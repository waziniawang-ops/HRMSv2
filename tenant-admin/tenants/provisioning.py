"""
Automated per-tenant provisioning on Render.

Triggered from TenantViewSet (tenants/api.py) in a background thread — a new
tenant takes several minutes (two builds plus migrations), far too slow for
one HTTP request, and this app deliberately has no Celery/Redis of its own.

provision_tenant() runs these steps in order, each raising ProvisioningError
on failure so the caller can record it and best-effort tear down whatever was
already created in that run:

  1. create_tenant_database   - new role + database on the shared tenant
                                Postgres instance (NOT a new instance per tenant).
  2. create_backend_service   - new Render web service built from this repo,
                                with the tenant's env vars (ENABLED_MODULES,
                                SEAT_LIMIT, OAUTH_*, ...). Its pre-deploy
                                command, provision_tenant.sh, runs migrations
                                and seeds the tenant's first admin account.
  3. create_frontend_site     - new Render static site built from this repo's
                                frontend/ with VITE_API_URL and VITE_ORG_NAME.
                                Every tenant keeps the Visionaries look.
  4. Push the frontend's URL back into the backend's env (CORS, OAuth
     redirect) and redeploy it — Render only reports a service's URL once
     the service exists, so neither URL can be known before both are created.
  5. Wait for both deploys to go live, then drop the one-time admin password
     from the backend's env so it never sits there after the first seed.

deprovision_tenant() is the counterpart, triggered from TenantViewSet.destroy():
it deletes both Render services and the database before removing the tracking
row, so "Delete Tenant" can't silently leave orphaned billed infrastructure.

Every push to TENANT_REPO_BRANCH redeploys every tenant (autoDeploy), and each
deploy's pre-deploy command migrates that tenant's own database.
"""
import logging
import os
import re
import secrets
import time
from urllib.parse import urlparse

import psycopg2
import requests
from django.conf import settings
from django.utils import timezone as dj_timezone

from .crypto import encrypt_secret, decrypt_secret, EncryptionNotConfigured

logger = logging.getLogger(__name__)

_REQUIRED_SETTINGS = (
    'RENDER_API_KEY', 'RENDER_OWNER_ID', 'TENANT_REPO_URL', 'TENANT_APPS_DB_ADMIN_URL',
)

_SAFE_IDENTIFIER_RE = re.compile(r'^[a-z][a-z0-9_]{0,62}$')

_DEPLOY_POLL_SECONDS = 15
_DEPLOY_TIMEOUT_SECONDS = 30 * 60
_DEPLOY_LIVE = 'live'
_DEPLOY_FAILED = {'build_failed', 'update_failed', 'pre_deploy_failed', 'canceled', 'deactivated'}

BACKEND_BUILD_COMMAND = 'pip install -r requirements.txt && python manage.py collectstatic --no-input'
BACKEND_START_COMMAND = 'gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2'
BACKEND_PRE_DEPLOY_COMMAND = './provision_tenant.sh'
FRONTEND_BUILD_COMMAND = 'cd frontend && npm ci && npm run build'
FRONTEND_PUBLISH_PATH = 'frontend/dist'


class ProvisioningError(Exception):
    """Raised at any step of provision_tenant(); message becomes tenant.provisioning_error."""


def _require_config():
    missing = [name for name in _REQUIRED_SETTINGS if not getattr(settings, name, '')]
    if missing:
        raise ProvisioningError('Provisioning is not fully configured — missing: ' + ', '.join(missing))


def _log_step(tenant, message, reset=False):
    """Appends a timestamped line to tenant.provisioning_log and saves it
    immediately, so an operator watching the tenant (the frontend polls every
    3s while PROVISIONING/DEPROVISIONING) sees real progress. reset=True
    starts a fresh log for a new run. Never raises — a logging hiccup must not
    fail the step it describes."""
    line = f'[{dj_timezone.now().strftime("%H:%M:%S")}] {message}'
    try:
        tenant.provisioning_log = line if reset else (tenant.provisioning_log or '') + '\n' + line
        tenant.save(update_fields=['provisioning_log'])
    except Exception:
        logger.exception('Failed to write provisioning_log for tenant %s', tenant.id)


# --- Render API ---------------------------------------------------------------

def _render(method, path, json=None, allow_404=False):
    """One Render REST API call. Retries on rate limiting; raises
    ProvisioningError with Render's own message on any other failure."""
    url = f'{settings.RENDER_API_BASE}{path}'
    headers = {
        'Authorization': f'Bearer {settings.RENDER_API_KEY}',
        'Accept': 'application/json',
    }
    for attempt in range(4):
        try:
            resp = requests.request(method, url, headers=headers, json=json, timeout=30)
        except requests.RequestException as e:
            raise ProvisioningError(f'Render API {method} {path} failed: {e}') from e
        if resp.status_code == 429 and attempt < 3:
            time.sleep(int(resp.headers.get('Retry-After', '5') or 5))
            continue
        break
    if allow_404 and resp.status_code == 404:
        return None
    if resp.status_code >= 400:
        raise ProvisioningError(f'Render API {method} {path} returned HTTP {resp.status_code}: {resp.text[:300]}')
    return resp.json() if resp.content else None


def _service_name(tenant, suffix):
    return f'{settings.TENANT_SERVICE_PREFIX}-{tenant.slug}-{suffix}'


def _env_list(env):
    return [{'key': k, 'value': v} for k, v in env.items()]


def _set_env_vars(service_id, env):
    """Replaces the service's whole env var set. Takes effect on the next deploy."""
    _render('PUT', f'/services/{service_id}/env-vars', json=_env_list(env))


def _recent_deploys(service_id):
    items = _render('GET', f'/services/{service_id}/deploys?limit=20') or []
    # List endpoints wrap each row as {"deploy": {...}, "cursor": "..."}.
    return [item.get('deploy', item) for item in items]


def _trigger_deploy(service_id):
    """Starts a deploy and returns its id. If another deploy is still running,
    Render queues the new one and answers with an empty body, so the queued
    deploy's id is found by waiting for a deploy that wasn't there before."""
    before = {d['id'] for d in _recent_deploys(service_id)}
    data = _render('POST', f'/services/{service_id}/deploys', json={'clearCache': 'do_not_clear'})
    if data and data.get('id'):
        return data['id']
    deadline = time.monotonic() + _DEPLOY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        new = [d for d in _recent_deploys(service_id) if d['id'] not in before]
        if new:
            return max(new, key=lambda d: d.get('createdAt', ''))['id']
        time.sleep(_DEPLOY_POLL_SECONDS)
    raise ProvisioningError(f'Deploy queued on {service_id} never started within {_DEPLOY_TIMEOUT_SECONDS // 60} minutes.')


def _wait_for_deploy(tenant, service_id, deploy_id, label):
    deadline = time.monotonic() + _DEPLOY_TIMEOUT_SECONDS
    last_status = None
    while time.monotonic() < deadline:
        deploy = _render('GET', f'/services/{service_id}/deploys/{deploy_id}')
        status = deploy.get('status')
        if status != last_status:
            _log_step(tenant, f'{label} deploy: {status}')
            last_status = status
        if status == _DEPLOY_LIVE:
            return
        if status in _DEPLOY_FAILED:
            raise ProvisioningError(
                f'{label} deploy {deploy_id} ended with status {status} — see the service\'s logs in the Render dashboard.'
            )
        time.sleep(_DEPLOY_POLL_SECONDS)
    raise ProvisioningError(f'{label} deploy {deploy_id} did not go live within {_DEPLOY_TIMEOUT_SECONDS // 60} minutes.')


def delete_service(service_id):
    if service_id:
        _render('DELETE', f'/services/{service_id}', allow_404=True)


# --- Database -----------------------------------------------------------------

def _db_name(tenant):
    # The tenant_ prefix keeps tenant databases from ever colliding with
    # another database on the same instance (e.g. the flagship's own "hrms").
    name = f'tenant_{tenant.slug.replace("-", "_")}'
    if not _SAFE_IDENTIFIER_RE.match(name):
        raise ProvisioningError(
            f'Tenant slug {tenant.slug!r} is not safe to use as a database/role name '
            '(must be short, lowercase letters/digits/hyphens).'
        )
    return name


def _parse_admin_db_url(url):
    result = urlparse(url)
    if not result.hostname:
        raise ProvisioningError('TENANT_APPS_DB_ADMIN_URL has no host.')
    return {
        'host': result.hostname,
        'port': result.port or 5432,
        'user': result.username or '',
        'password': result.password or '',
        'dbname': result.path.lstrip('/') or 'postgres',
    }


def _admin_connection(dbname=None):
    admin = _parse_admin_db_url(settings.TENANT_APPS_DB_ADMIN_URL)
    return psycopg2.connect(
        host=admin['host'], port=admin['port'], user=admin['user'],
        password=admin['password'], dbname=dbname or admin['dbname'], sslmode='require',
    )


def assert_database_absent(tenant):
    """Refuses to provision over an existing database. Called before
    provision_tenant marks the database as created, so a collision can never
    lead rollback into dropping a database this run didn't create."""
    name = _db_name(tenant)
    conn = _admin_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (name,))
            exists = cur.fetchone() is not None
    finally:
        conn.close()
    if exists:
        raise ProvisioningError(
            f'Database "{name}" already exists on the tenant Postgres instance — '
            'drop it manually if it is a leftover from a failed attempt, then retry.'
        )


def create_tenant_database(tenant):
    """Creates a dedicated database (and, unless TENANT_DB_SHARE_ADMIN_ROLE is
    set, a dedicated login role that owns it) on the shared tenant Postgres
    instance. Returns the tenant's own DATABASE_URL.

    Never drops an existing database first — callers check
    assert_database_absent() beforehand, so a mistyped slug or misconfigured
    admin URL can't destroy data."""
    name = _db_name(tenant)
    admin = _parse_admin_db_url(settings.TENANT_APPS_DB_ADMIN_URL)
    share_admin_role = settings.TENANT_DB_SHARE_ADMIN_ROLE

    conn = _admin_connection()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            if share_admin_role:
                db_user, db_password = admin['user'], admin['password']
                cur.execute(f'CREATE DATABASE "{name}"')
            else:
                db_user, db_password = name, secrets.token_urlsafe(24)
                try:
                    cur.execute(f'CREATE ROLE "{name}" LOGIN PASSWORD %s', (db_password,))
                except psycopg2.errors.InsufficientPrivilege as e:
                    raise ProvisioningError(
                        'The tenant Postgres admin user may not create roles. Set '
                        'TENANT_DB_SHARE_ADMIN_ROLE=true to give each tenant its own database '
                        'owned by the admin user instead.'
                    ) from e
                # The admin user must be a member of the new role to make it the owner.
                cur.execute(f'GRANT "{name}" TO "{admin["user"]}"')
                cur.execute(f'CREATE DATABASE "{name}" OWNER "{name}"')
    except ProvisioningError:
        raise
    except Exception as e:
        raise ProvisioningError(f'Database creation failed: {e}') from e
    finally:
        conn.close()

    if not share_admin_role:
        # PG15+ no longer grants CREATE on the public schema to everyone, and
        # owning the database doesn't make the role the schema's owner.
        conn = _admin_connection(dbname=name)
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(f'GRANT ALL ON SCHEMA public TO "{name}"')
        except Exception as e:
            raise ProvisioningError(f'Granting schema privileges failed: {e}') from e
        finally:
            conn.close()

    return f'postgresql://{db_user}:{db_password}@{admin["host"]}:{admin["port"]}/{name}'


def delete_tenant_database(tenant):
    """Counterpart to create_tenant_database. Raises on a real failure — used
    both for best-effort rollback (caller catches and logs) and deliberate
    teardown via deprovision_tenant (caller lets it propagate)."""
    name = _db_name(tenant)
    conn = _admin_connection()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            # WITH (FORCE) (PG13+) disconnects the tenant backend's lingering
            # sessions, which may outlive its service deletion by a moment.
            cur.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            if not settings.TENANT_DB_SHARE_ADMIN_ROLE:
                cur.execute(f'DROP ROLE IF EXISTS "{name}"')
    finally:
        conn.close()


# --- Tenant configuration -----------------------------------------------------

def _enabled_module_codes(tenant):
    """The plan's Module.codes — the backend's ENABLED_MODULES, read by the main
    app's ModuleGateMiddleware / IsModuleEnabled."""
    return sorted(tenant.plan.modules.values_list('code', flat=True))


def _seat_limit_env_value(tenant):
    """The plan's seat_limit as a plain integer string, or '' for unlimited —
    enforced by the main app's UserCreateSerializer."""
    return str(tenant.plan.seat_limit) if tenant.plan.seat_limit is not None else ''


def _oauth_env_values(tenant, backend_url):
    """OAUTH_* values for this tenant's backend. If the stored client secret
    can't be decrypted, SSO just won't work for this tenant rather than
    blocking module/seat-limit updates too."""
    if not tenant.oauth_enabled:
        return {'OAUTH_ENABLED': 'false'}
    client_secret = ''
    if tenant.oauth_client_secret_encrypted:
        try:
            client_secret = decrypt_secret(tenant.oauth_client_secret_encrypted)
        except Exception:
            logger.warning('Could not decrypt oauth_client_secret for tenant %s — SSO will not work until it is re-saved.', tenant.id)
    return {
        'OAUTH_ENABLED': 'true',
        'OAUTH_ISSUER': tenant.oauth_issuer,
        'OAUTH_CLIENT_ID': tenant.oauth_client_id,
        'OAUTH_CLIENT_SECRET': client_secret,
        'OAUTH_REDIRECT_URI': f'{backend_url}/api/v1/auth/oauth/callback/' if backend_url else '',
        'OAUTH_BUTTON_LABEL': tenant.oauth_button_label,
    }


def _shared_env():
    """Env vars copied verbatim from this app's own environment into every
    tenant backend (TENANT_SHARED_ENV_KEYS) — e.g. CLOUDINARY_* or EMAIL_*."""
    return {key: os.environ[key] for key in settings.TENANT_SHARED_ENV_KEYS if os.environ.get(key)}


def _backend_env(tenant, db_url, django_secret_key, backend_url='', frontend_url='', admin_password=None):
    env = {
        **_shared_env(),
        'PYTHON_VERSION': '3.11',
        'DJANGO_SETTINGS_MODULE': 'config.settings.production',
        'DEBUG': 'false',
        'DATABASE_URL': db_url,
        'SECRET_KEY': django_secret_key,
        # Tenants get no Redis or Celery worker — see config.settings.base.
        'USE_REDIS_CACHE': 'false',
        'CORS_ALLOWED_ORIGINS': frontend_url,
        'FRONTEND_URL': frontend_url,
        'ENABLED_MODULES': ','.join(_enabled_module_codes(tenant)),
        'SEAT_LIMIT': _seat_limit_env_value(tenant),
        # Read by provision_tenant.sh, which only ever creates this user if it
        # doesn't exist yet.
        'DJANGO_SUPERUSER_USERNAME': tenant.admin_email,
        'DJANGO_SUPERUSER_EMAIL': tenant.admin_email,
        'DJANGO_SUPERUSER_FIRST_NAME': tenant.admin_first_name,
        'DJANGO_SUPERUSER_LAST_NAME': tenant.admin_last_name,
        **_oauth_env_values(tenant, backend_url),
    }
    if tenant.domain:
        env['ALLOWED_HOSTS'] = tenant.domain
    if admin_password:
        env['DJANGO_SUPERUSER_PASSWORD'] = admin_password
    return env


def create_backend_service(tenant, env):
    """Creates the tenant's backend web service. Render starts its first
    deploy immediately. Returns (service_id, url, deploy_id)."""
    data = _render('POST', '/services', json={
        'type': 'web_service',
        'name': _service_name(tenant, 'api'),
        'ownerId': settings.RENDER_OWNER_ID,
        'repo': settings.TENANT_REPO_URL,
        'branch': settings.TENANT_REPO_BRANCH,
        'autoDeploy': 'yes',
        'envVars': _env_list(env),
        'serviceDetails': {
            'runtime': 'python',
            'plan': settings.TENANT_BACKEND_PLAN,
            'region': settings.TENANT_RENDER_REGION,
            'numInstances': 1,
            'healthCheckPath': '/healthz/',
            'preDeployCommand': BACKEND_PRE_DEPLOY_COMMAND,
            'envSpecificDetails': {
                'buildCommand': BACKEND_BUILD_COMMAND,
                'startCommand': BACKEND_START_COMMAND,
            },
        },
    })
    service = data['service']
    return service['id'], service['serviceDetails']['url'], data.get('deployId')


def create_frontend_site(tenant, backend_url):
    """Creates the tenant's static site, built from this repo's frontend/
    with the tenant's API URL and organisation name. Returns
    (service_id, url, deploy_id)."""
    data = _render('POST', '/services', json={
        'type': 'static_site',
        'name': _service_name(tenant, 'web'),
        'ownerId': settings.RENDER_OWNER_ID,
        'repo': settings.TENANT_REPO_URL,
        'branch': settings.TENANT_REPO_BRANCH,
        'autoDeploy': 'yes',
        'envVars': _env_list({
            'NODE_VERSION': '20',
            'VITE_API_URL': f'{backend_url}/api/v1',
            'VITE_ORG_NAME': tenant.name,
            'VITE_SHOW_DEMO_CREDENTIALS': 'false',
        }),
        'serviceDetails': {
            'buildCommand': FRONTEND_BUILD_COMMAND,
            'publishPath': FRONTEND_PUBLISH_PATH,
            'pullRequestPreviewsEnabled': 'no',
        },
    })
    service = data['service']
    # SPA routing: every client-side route serves index.html.
    _render('POST', f'/services/{service["id"]}/routes', json={
        'type': 'rewrite', 'source': '/*', 'destination': '/index.html',
    })
    return service['id'], service['serviceDetails']['url'], data.get('deployId')


def _rollback(tenant, db_created):
    """Best-effort teardown of whatever this run created, so a failed attempt
    doesn't leave orphaned billed resources. Each step is wrapped separately
    so one cleanup failure doesn't hide the others."""
    for label, field in (('backend service', 'render_backend_service_id'), ('frontend site', 'render_frontend_service_id')):
        service_id = getattr(tenant, field)
        if not service_id:
            continue
        _log_step(tenant, f'Rolling back: deleting {label}…')
        try:
            delete_service(service_id)
            setattr(tenant, field, '')
            tenant.save(update_fields=[field])
            _log_step(tenant, f'Rollback: {label} deleted.')
        except Exception:
            logger.exception('Cleanup: failed to delete %s for tenant %s', label, tenant.id)
            _log_step(tenant, f'Rollback: failed to delete {label} — may need manual cleanup in Render.')
    if db_created:
        _log_step(tenant, 'Rolling back: deleting tenant database…')
        try:
            delete_tenant_database(tenant)
            _log_step(tenant, 'Rollback: database deleted.')
        except Exception:
            logger.exception('Cleanup: failed to delete database for tenant %s', tenant.id)
            _log_step(tenant, 'Rollback: failed to delete database — may need manual cleanup.')


# --- Entry points (run in background threads by tenants/api.py) ---------------

def provision_tenant(tenant_id, result_registry):
    """`result_registry` is the short-lived in-memory dict (tenants/api.py)
    this writes the one-time generated admin password into on success."""
    from .models import Tenant

    # provisioning_status is already PROVISIONING — set synchronously by
    # TenantViewSet.perform_create before this thread starts.
    tenant = Tenant.objects.select_related('plan').get(id=tenant_id)

    db_created = False
    _log_step(tenant, 'Starting provisioning…', reset=True)
    try:
        _require_config()
        if not tenant.admin_email:
            raise ProvisioningError('admin_email is required to provision a tenant (used to seed the first login).')

        admin_password = secrets.token_urlsafe(16)
        django_secret_key = secrets.token_urlsafe(50)

        _log_step(tenant, 'Creating tenant database…')
        assert_database_absent(tenant)
        # Set BEFORE the attempt: a failure partway through may still have
        # created the database, and rollback must know to remove it.
        db_created = True
        db_url = create_tenant_database(tenant)
        _log_step(tenant, f'Database created ({_db_name(tenant)}).')

        _log_step(tenant, 'Creating backend service…')
        backend_id, backend_url, backend_first_deploy_id = create_backend_service(
            tenant, _backend_env(tenant, db_url, django_secret_key, admin_password=admin_password),
        )
        tenant.render_backend_service_id = backend_id
        tenant.save(update_fields=['render_backend_service_id'])
        _log_step(tenant, f'Backend service created: {backend_url}')

        _log_step(tenant, 'Creating frontend static site…')
        frontend_id, frontend_url, frontend_deploy_id = create_frontend_site(tenant, backend_url)
        tenant.render_frontend_service_id = frontend_id
        tenant.save(update_fields=['render_frontend_service_id'])
        _log_step(tenant, f'Frontend static site created: {frontend_url}')

        # The first deploy builds, migrates and seeds the admin account. Let it
        # finish before redeploying, so the two deploys don't overlap.
        if backend_first_deploy_id:
            _log_step(tenant, 'Building and migrating the backend (this takes a few minutes)…')
            _wait_for_deploy(tenant, backend_id, backend_first_deploy_id, 'Backend (first)')

        _log_step(tenant, 'Pointing the backend at its frontend (CORS, SSO redirect) and redeploying…')
        _set_env_vars(backend_id, _backend_env(
            tenant, db_url, django_secret_key, backend_url, frontend_url, admin_password=admin_password,
        ))
        backend_deploy_id = _trigger_deploy(backend_id)
        _wait_for_deploy(tenant, backend_id, backend_deploy_id, 'Backend')
        if frontend_deploy_id:
            _wait_for_deploy(tenant, frontend_id, frontend_deploy_id, 'Frontend')

        # The admin account now exists; the plaintext password has no reason
        # to stay in the service's env. Takes effect without a redeploy.
        _set_env_vars(backend_id, _backend_env(tenant, db_url, django_secret_key, backend_url, frontend_url))

        _log_step(tenant, 'Provisioning complete.')
        tenant.provisioning_status = Tenant.PROVISIONING_ACTIVE
        tenant.backend_url = backend_url
        tenant.frontend_url = frontend_url
        tenant.provisioning_error = ''
        tenant.provisioned_at = dj_timezone.now()
        try:
            tenant.admin_password_encrypted = encrypt_secret(admin_password)
            tenant.backend_db_url_encrypted = encrypt_secret(db_url)
            tenant.backend_secret_key_encrypted = encrypt_secret(django_secret_key)
        except EncryptionNotConfigured:
            # Provisioning itself still succeeded; without the key this tenant's
            # password can't be revealed later and plan changes can't be synced.
            logger.warning(
                'TENANT_ADMIN_PASSWORD_ENCRYPTION_KEY not set — admin password and '
                'backend secrets for tenant %s will not be revealable/resyncable later.', tenant_id,
            )
        tenant.save(update_fields=[
            'provisioning_status', 'backend_url', 'frontend_url', 'provisioning_error',
            'provisioned_at', 'admin_password_encrypted',
            'backend_db_url_encrypted', 'backend_secret_key_encrypted',
        ])

        result_registry[tenant_id] = {'initial_admin_password': admin_password}
    except Exception as e:
        logger.exception('Provisioning failed for tenant %s', tenant_id)
        _log_step(tenant, f'Provisioning failed: {e}')
        _rollback(tenant, db_created)
        tenant.provisioning_status = Tenant.PROVISIONING_FAILED
        tenant.provisioning_error = str(e)
        tenant.save(update_fields=['provisioning_status', 'provisioning_error'])


def deprovision_tenant(tenant_id):
    """Deletes the tenant's Render services and database, then the tracking
    row. Unlike _rollback, errors surface: on failure the row is kept and
    marked DEPROVISION_FAILED so an operator can see what happened and retry."""
    from .models import Tenant

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return

    _log_step(tenant, 'Starting deprovisioning…', reset=True)
    try:
        if tenant.render_backend_service_id or tenant.render_frontend_service_id:
            _require_config()
        _log_step(tenant, 'Deleting Render services…')
        delete_service(tenant.render_backend_service_id)
        delete_service(tenant.render_frontend_service_id)
        _log_step(tenant, 'Render services deleted.')

        if tenant.provisioned_at or tenant.backend_db_url_encrypted:
            _log_step(tenant, 'Deleting tenant database…')
            delete_tenant_database(tenant)
            _log_step(tenant, 'Database deleted.')

        _log_step(tenant, 'Deprovisioning complete — removing tracking record.')
        tenant.delete()
    except Exception as e:
        logger.exception('Deprovisioning failed for tenant %s', tenant_id)
        _log_step(tenant, f'Deprovisioning failed: {e}')
        tenant.provisioning_status = Tenant.PROVISIONING_DEPROVISION_FAILED
        tenant.provisioning_error = f'Failed to delete tenant resources: {e}'
        tenant.save(update_fields=['provisioning_status', 'provisioning_error'])


def sync_backend_config(tenant):
    """Re-pushes an ACTIVE tenant's config (ENABLED_MODULES, SEAT_LIMIT,
    OAUTH_*, ...) and redeploys its backend, reusing the SAME db_url and
    secret_key stored at provisioning time — a new SECRET_KEY would sign out
    every user of that tenant."""
    if tenant.provisioning_status != tenant.PROVISIONING_ACTIVE:
        return
    if not (tenant.backend_db_url_encrypted and tenant.backend_secret_key_encrypted and tenant.render_backend_service_id):
        logger.warning('Cannot sync backend config for tenant %s — missing stored secrets or service id.', tenant.id)
        return
    _require_config()
    _log_step(tenant, 'Syncing backend configuration (plan/module/seat-limit/SSO change)…', reset=True)
    env = _backend_env(
        tenant,
        decrypt_secret(tenant.backend_db_url_encrypted),
        decrypt_secret(tenant.backend_secret_key_encrypted),
        tenant.backend_url, tenant.frontend_url,
    )
    _set_env_vars(tenant.render_backend_service_id, env)
    deploy_id = _trigger_deploy(tenant.render_backend_service_id)
    _wait_for_deploy(tenant, tenant.render_backend_service_id, deploy_id, 'Backend')
    _log_step(tenant, 'Backend configuration synced.')


def sync_tenant_modules(tenant_id):
    """Background-thread wrapper for sync_backend_config. Logs its own errors —
    a failed resync leaves the tenant running on its previous config, which is
    not the same failure class as a provisioning error."""
    from .models import Tenant
    try:
        tenant = Tenant.objects.select_related('plan').get(id=tenant_id)
    except Tenant.DoesNotExist:
        return
    try:
        sync_backend_config(tenant)
    except Exception as e:
        logger.exception('Failed to sync backend config for tenant %s', tenant_id)
        _log_step(tenant, f'Sync failed: {e}')


def set_tenant_suspended(tenant_id, suspended):
    """Suspends (or resumes) both of the tenant's Render services, so a
    SUSPENDED tenant's users really are locked out and the services stop
    running. The database is left untouched."""
    from .models import Tenant
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return
    verb = 'suspend' if suspended else 'resume'
    _log_step(tenant, f'{verb.capitalize()}ing Render services…', reset=True)
    try:
        _require_config()
        for service_id in (tenant.render_backend_service_id, tenant.render_frontend_service_id):
            if service_id:
                _render('POST', f'/services/{service_id}/{verb}')
        _log_step(tenant, f'Render services {verb}ed.')
    except Exception as e:
        logger.exception('Failed to %s tenant %s', verb, tenant_id)
        _log_step(tenant, f'Failed to {verb} Render services: {e}')
