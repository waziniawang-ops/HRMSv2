import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Plan-gateable modules — must match tenant-admin/tenants/models.py's Module.code
# catalog exactly. Each tenant is a fully separate Render deployment with no live
# connection to tenant-admin, so the catalog is duplicated here rather than
# looked up. Apps not in this set (accounts, audit, documents, notification,
# reporting, workflow) are cross-cutting infrastructure and are never gated.
GATEABLE_MODULES = frozenset({
    'attendance', 'core_hr', 'ess', 'workforce',
    'benefits', 'claims', 'compensation', 'payroll',
    'employee_relations', 'engagement', 'hse', 'service_desk',
    'learning', 'offboarding', 'onboarding', 'performance', 'recruitment', 'skills', 'succession',
})

# Set by tenant-admin's provisioning to this tenant's plan's module codes
# (comma-separated). Empty means "no gating at all", not "nothing enabled" —
# the flagship deployment and local/dev never set it, so a missing env var can
# never lock a tenant out of their own app.
ENABLED_MODULES = frozenset(
    m.strip() for m in os.environ.get('ENABLED_MODULES', '').split(',') if m.strip()
)

# Set by tenant-admin's provisioning to the plan's seat_limit. Unset/blank means
# unlimited. Enforced in apps.accounts.serializers.UserCreateSerializer.
_seat_limit_raw = os.environ.get('SEAT_LIMIT', '').strip()
SEAT_LIMIT = int(_seat_limit_raw) if _seat_limit_raw.isdigit() else None

# This deployment's own frontend URL — where the OAuth callback sends the browser.
FRONTEND_URL = os.environ.get('FRONTEND_URL', '').strip()

# Generic OpenID Connect SSO, configured per tenant in tenant-admin and pushed
# here as env vars. Unset means SSO is simply not offered (see apps.accounts.oauth).
OAUTH_ENABLED = os.environ.get('OAUTH_ENABLED', '').strip().lower() == 'true'
OAUTH_ISSUER = os.environ.get('OAUTH_ISSUER', '').strip().rstrip('/')
OAUTH_CLIENT_ID = os.environ.get('OAUTH_CLIENT_ID', '').strip()
OAUTH_CLIENT_SECRET = os.environ.get('OAUTH_CLIENT_SECRET', '').strip()
OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', '').strip()
OAUTH_BUTTON_LABEL = os.environ.get('OAUTH_BUTTON_LABEL', '').strip() or 'Sign in with SSO'

# Render automatically injects this — no manual env var needed
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    'cloudinary_storage',
    'cloudinary',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.audit',
    'apps.workflow',
    'apps.core_hr',
    'apps.recruitment',
    'apps.onboarding',
    'apps.workforce',
    'apps.succession',
    'apps.performance',
    'apps.learning',
    'apps.notification',
    'apps.reporting',
    'apps.attendance',
    # New modules
    'apps.payroll',
    'apps.compensation',
    'apps.benefits',
    'apps.ess',
    'apps.service_desk',
    'apps.employee_relations',
    'apps.documents',
    'apps.offboarding',
    'apps.engagement',
    'apps.hse',
    'apps.claims',
    'apps.skills',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

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
    'apps.audit.middleware.AuditMiddleware',
    'apps.accounts.middleware.ModuleGateMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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
ASGI_APPLICATION = 'config.asgi.application'

# Database
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://hrms:hrms@localhost:5432/hrms')

def parse_db_url(url):
    from urllib.parse import urlparse
    result = urlparse(url)
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

# Cache
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Tenant deployments created by tenant-admin get no Redis of their own — they
# set USE_REDIS_CACHE=false and fall back to an in-process cache with
# database-backed sessions (only the Django admin uses sessions; the API is JWT).
if os.environ.get('USE_REDIS_CACHE', 'true').lower() == 'true':
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

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

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'apps.accounts.permissions.IsModuleEnabled',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# OpenAPI docs
SPECTACULAR_SETTINGS = {
    'TITLE': 'ERP HRMS API',
    'DESCRIPTION': 'Human Resource Management System - Full Enterprise API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@hrms.local')

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if os.environ.get('CORS_ALLOWED_ORIGINS') else []

# Cloudinary
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
}

# Audit
AUDIT_IMMUTABLE_MODE = os.environ.get('AUDIT_IMMUTABLE_MODE', 'true').lower() == 'true'

# Document upload
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_DOCUMENT_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]
