import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]

# Render injects this service's own hostname — trust it for both host checks
# and the Django admin's CSRF origin check.
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if _render_host:
    if _render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_render_host)
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'tenants',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Only relevant when the SPA runs on a different origin than the API during
# local dev (Vite's own port) — in production the built SPA is served by
# this same Django app via WhiteNoise, so requests are same-origin and this
# is unused there.
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173').split(',') if o.strip()
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database — this server holds ONLY tenant metadata (name, slug, domain,
# plan, status). It must never gain a foreign key into any tenant's own
# HR data; that boundary is the entire point of keeping this app separate.
# Same parsing guard as the main HRMSv2 app: a DATABASE_URL with no host
# (mangled quotes/whitespace, dropped scheme) would otherwise make
# psycopg2 silently fall back to a local Unix socket and fail unhelpfully.
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://hrms:hrms@localhost:5432/tenant_admin')
DATABASE_URL = DATABASE_URL.strip().strip('"').strip("'").strip()


def parse_db_url(url):
    from urllib.parse import urlparse
    from django.core.exceptions import ImproperlyConfigured
    result = urlparse(url)
    # A genuine unix-socket URL looks like 'postgresql://user@/dbname' — netloc
    # ends right at '@' with nothing after it. Checking only "does a database
    # name exist in the path" (as an earlier version of this guard did) is too
    # permissive: it also accepts a URL that's missing '@host' entirely (e.g.
    # a dropped hostname from a copy-paste error), silently treating a
    # malformed URL as a deliberate local-socket one.
    is_unix_socket = (
        result.scheme in ('postgresql', 'postgres') and result.netloc.endswith('@')
    )
    if not result.hostname and not is_unix_socket:
        raise ImproperlyConfigured(
            "DATABASE_URL has no host — psycopg2 would fall back to a local "
            "Unix socket and fail. Check the value for surrounding quotes, "
            "whitespace, a missing 'postgresql://' scheme, or special "
            f"characters in the password. Parsed scheme={result.scheme!r}, "
            f"host={result.hostname!r}."
        )
    cfg = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': result.path[1:],
        'USER': result.username or '',
        'PASSWORD': result.password or '',
        'HOST': result.hostname or '',
        'PORT': str(result.port) if result.port else '',
    }
    if result.hostname and result.hostname not in ('localhost', '127.0.0.1'):
        cfg['OPTIONS'] = {'sslmode': 'require'}
    return cfg


DATABASES = {
    'default': parse_db_url(DATABASE_URL)
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# The built React SPA (frontend/dist/) is served directly from the site root
# by WhiteNoise — unprefixed, since Vite's build already references
# /assets/... paths itself. Django's own STATIC_URL ('/static/') stays
# separate for the admin site's static files. See config/urls.py for the
# catch-all view that serves index.html for client-side routes.
WHITENOISE_ROOT = BASE_DIR / 'frontend' / 'dist'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Platform-operator login only — never a tenant's own HRMS login.
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- Automated tenant provisioning on Render (tenants/provisioning.py) ---
# Blank by default so this app still boots (e.g. locally) without them —
# provisioning.py checks these explicitly and fails a tenant fast with a clear
# error rather than half-provision something against a blank config.

# A Render API key (Account Settings → API Keys) and the workspace that owns
# every tenant service — the workspace id is the "tea-…"/"usr-…" id from
# `GET https://api.render.com/v1/owners`.
RENDER_API_KEY = os.environ.get('RENDER_API_KEY', '')
RENDER_OWNER_ID = os.environ.get('RENDER_OWNER_ID', '')
RENDER_API_BASE = os.environ.get('RENDER_API_BASE', 'https://api.render.com/v1').rstrip('/')

# Repo + branch every tenant's backend and frontend are built from. The Render
# workspace must already have access to this repo (GitHub app connected).
# Every push to this branch redeploys — and migrates — every tenant.
TENANT_REPO_URL = os.environ.get('TENANT_REPO_URL', '')
TENANT_REPO_BRANCH = os.environ.get('TENANT_REPO_BRANCH', 'main')

TENANT_RENDER_REGION = os.environ.get('TENANT_RENDER_REGION', 'singapore')
TENANT_BACKEND_PLAN = os.environ.get('TENANT_BACKEND_PLAN', 'starter')
# Tenant services are named <prefix>-<slug>-api / <prefix>-<slug>-web.
TENANT_SERVICE_PREFIX = os.environ.get('TENANT_SERVICE_PREFIX', 'hrms')

# Admin connection string to the shared Render Postgres instance that holds
# one database per tenant (distinct from this app's own DATABASE_URL above —
# that one holds only tenant-admin's metadata and must never be reused here).
# Use the instance's internal URL: tenant backends connect to the same host.
TENANT_APPS_DB_ADMIN_URL = os.environ.get('TENANT_APPS_DB_ADMIN_URL', '').strip().strip('"').strip("'").strip()

# If the instance's admin user may not CREATE ROLE, set this to true: each
# tenant still gets its own database, but owned by (and connecting as) the
# admin user — weaker isolation between tenants' databases.
TENANT_DB_SHARE_ADMIN_ROLE = os.environ.get('TENANT_DB_SHARE_ADMIN_ROLE', 'false').lower() == 'true'

# Names of env vars copied from THIS service's environment into every tenant
# backend — e.g. shared CLOUDINARY_* media storage or EMAIL_* SMTP settings.
TENANT_SHARED_ENV_KEYS = [
    k.strip() for k in os.environ.get('TENANT_SHARED_ENV_KEYS', '').split(',') if k.strip()
]

# Encrypts each tenant's generated admin password at rest (tenants/crypto.py,
# Fernet symmetric encryption — a URL-safe base64 32-byte key, generate with
# `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
# so TenantViewSet's reveal-password action can decrypt it again on demand,
# without ever storing the plaintext. Left blank by default so this app still
# boots without it — provisioning still succeeds either way (the one-time
# reveal right after creation still works), it just can't persist a
# revealable copy for later, and logs a warning when that happens.
TENANT_ADMIN_PASSWORD_ENCRYPTION_KEY = os.environ.get('TENANT_ADMIN_PASSWORD_ENCRYPTION_KEY', '')
