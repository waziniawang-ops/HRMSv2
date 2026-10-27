"""Encrypt-at-rest for tenant secrets tenant-admin needs to recover later:
the admin login password (Tenant.admin_password_encrypted, revealed on
demand via TenantViewSet.reveal_password) and the deployed backend's own
DATABASE_URL/SECRET_KEY (Tenant.backend_db_url_encrypted /
backend_secret_key_encrypted, decrypted by provisioning.sync_backend_config
to safely rebuild that backend service's config — e.g. after a plan change —
without regenerating SECRET_KEY, which would invalidate every active
session/JWT for that tenant).

Fernet (symmetric, authenticated encryption) rather than a hash — these all
need to be recovered in plaintext later, not just verified, so this is a
genuinely different problem from how user passwords are hashed everywhere
else in this codebase.
"""
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

__all__ = ['encrypt_secret', 'decrypt_secret', 'EncryptionNotConfigured', 'InvalidToken']


class EncryptionNotConfigured(Exception):
    """Raised when TENANT_ADMIN_PASSWORD_ENCRYPTION_KEY isn't set."""


def _fernet():
    key = settings.TENANT_ADMIN_PASSWORD_ENCRYPTION_KEY
    if not key:
        raise EncryptionNotConfigured('TENANT_ADMIN_PASSWORD_ENCRYPTION_KEY is not set.')
    return Fernet(key.encode())


def encrypt_secret(plaintext):
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext):
    return _fernet().decrypt(ciphertext.encode()).decode()
