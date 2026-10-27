"""Generic OpenID Connect SSO login for this tenant's backend.

One tenant = one Django process = at most one OIDC provider, configured
statically via OAUTH_* settings (pushed by tenant-admin's provisioning.py
from Tenant.oauth_* fields — see tenant-admin/tenants/provisioning.py) — so
unlike a multi-tenant OIDC library, this never needs per-request provider
lookup, just this one deployment's fixed issuer/client_id/secret.

Hand-rolled rather than pulling in a full OIDC framework
(mozilla-django-oidc, authlib) because:
  - mozilla-django-oidc wants OIDC_OP_*_ENDPOINT settings fixed at Django
    startup. This deployment only has an issuer URL and needs
    `.well-known/openid-configuration` discovery — fetching that lazily
    (cached, on first login attempt) is safer than a startup-time network
    call that could fail Django's boot if the IdP happens to be briefly
    unreachable at that exact moment.
  - The one part that must NOT be hand-rolled — verifying the ID token's
    signature against the IdP's real JWKS — isn't: that's PyJWT's
    PyJWKClient, already a transitive dependency via
    djangorestframework-simplejwt. Hand-rolling JWT signature/claims
    verification is exactly the kind of thing that quietly grows an
    algorithm-confusion or expiry-bypass bug; using the vetted library for
    that specific step is the point of this trade-off, not a contradiction
    of it.

CSRF/replay protection (the OAuth `state` parameter) is deliberately
stateless — a signed, self-contained token via django.core.signing, not
something stored server-side and looked up on callback. This app's
SESSION_ENGINE is cache-backed (Redis), and tenant deployments have no
Redis provisioned at all (see config.settings.base's REDIS_URL comment) —
`request.session` would fail outright there. Signing embeds the nonce in
the state value itself, verified by re-checking the signature (and
expiry) on callback rather than a lookup, so this needs no session, cache,
or database at all and works identically whether or not Redis exists.
"""
import secrets
import time
from urllib.parse import urlencode

import jwt
import requests
from django.conf import settings
from django.core import signing

STATE_MAX_AGE = 600  # seconds an authorization code round-trip has to complete in
DISCOVERY_CACHE_TTL = 3600  # seconds — an IdP's endpoints don't rotate often
_discovery_cache = {}  # issuer -> (fetched_at, discovery_doc)
_jwks_client_cache = {}  # jwks_uri -> jwt.PyJWKClient


def make_state_and_nonce():
    """nonce goes to the IdP as OIDC's own `nonce` param (and comes back
    inside the ID token's claims, verified by exact match); state is a
    signed envelope around that same nonce, returned verbatim by the IdP on
    the callback redirect and unsigned there — see module docstring for why
    this replaces server-side session storage."""
    nonce = secrets.token_urlsafe(24)
    state = signing.dumps({'nonce': nonce})
    return state, nonce


def validate_state(state):
    """Returns the embedded nonce if `state` has a valid signature and
    hasn't expired; raises signing.BadSignature (which covers both a bad
    signature and django.core.signing.SignatureExpired, its subclass) if
    the callback is forged, tampered with, or simply too old."""
    data = signing.loads(state, max_age=STATE_MAX_AGE)
    return data['nonce']


class OAuthConfigError(Exception):
    """OAuth is disabled, or enabled but missing required settings."""


class OAuthLoginError(Exception):
    """Any failure during the login/callback flow — the view catches this
    and redirects to the frontend with an error indicator rather than
    letting it surface as a raw 500."""


def require_config():
    if not settings.OAUTH_ENABLED:
        raise OAuthConfigError('OAuth SSO is not enabled for this tenant.')
    missing = [
        name for name in ('OAUTH_ISSUER', 'OAUTH_CLIENT_ID', 'OAUTH_CLIENT_SECRET', 'OAUTH_REDIRECT_URI')
        if not getattr(settings, name, '')
    ]
    if missing:
        raise OAuthConfigError('OAuth is enabled but misconfigured — missing: ' + ', '.join(missing))


def get_discovery_document():
    issuer = settings.OAUTH_ISSUER
    cached = _discovery_cache.get(issuer)
    if cached and time.time() - cached[0] < DISCOVERY_CACHE_TTL:
        return cached[1]
    resp = requests.get(f'{issuer}/.well-known/openid-configuration', timeout=10)
    resp.raise_for_status()
    doc = resp.json()
    _discovery_cache[issuer] = (time.time(), doc)
    return doc


def _jwks_client(jwks_uri):
    client = _jwks_client_cache.get(jwks_uri)
    if client is None:
        client = jwt.PyJWKClient(jwks_uri)
        _jwks_client_cache[jwks_uri] = client
    return client


def build_authorization_url(state, nonce):
    require_config()
    doc = get_discovery_document()
    params = {
        'client_id': settings.OAUTH_CLIENT_ID,
        'redirect_uri': settings.OAUTH_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'nonce': nonce,
    }
    return f"{doc['authorization_endpoint']}?{urlencode(params)}"


def exchange_code_for_claims(code, expected_nonce):
    """Exchanges an authorization code for tokens, verifies the ID token
    (signature via the IdP's real JWKS, issuer, audience, expiry) and its
    nonce (replay protection), and returns the decoded claims dict."""
    require_config()
    doc = get_discovery_document()

    try:
        token_resp = requests.post(doc['token_endpoint'], data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.OAUTH_REDIRECT_URI,
            'client_id': settings.OAUTH_CLIENT_ID,
            'client_secret': settings.OAUTH_CLIENT_SECRET,
        }, timeout=10)
        token_resp.raise_for_status()
    except requests.RequestException as e:
        raise OAuthLoginError(f'Failed to exchange authorization code: {e}') from e

    id_token = token_resp.json().get('id_token')
    if not id_token:
        raise OAuthLoginError('IdP token response did not include an id_token.')

    try:
        signing_key = _jwks_client(doc['jwks_uri']).get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token, signing_key.key,
            algorithms=['RS256'],  # what Entra ID/Google/Okta/Auth0 all sign with; never 'none' or an HMAC alg
            audience=settings.OAUTH_CLIENT_ID,
            issuer=settings.OAUTH_ISSUER,
        )
    except jwt.PyJWTError as e:
        raise OAuthLoginError(f'ID token validation failed: {e}') from e

    if claims.get('nonce') != expected_nonce:
        raise OAuthLoginError('ID token nonce did not match the login attempt — possible replay.')

    return claims
