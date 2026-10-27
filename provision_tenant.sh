#!/usr/bin/env bash
# Render pre-deploy command for tenant backends created by tenant-admin
# (tenant-admin/tenants/provisioning.py). Runs before every deploy of a
# tenant, so it must be safe to repeat:
#   1. apply migrations — every push to the tracked branch upgrades all tenants;
#   2. create the tenant's first admin account, ONLY if it doesn't exist yet.
#      It never resets an existing user's password, and provisioning removes
#      DJANGO_SUPERUSER_PASSWORD from the service once the first deploy is live.
# Demo data (seed_users / demo_seed.py) is never written to a tenant.
set -euo pipefail

python manage.py migrate --no-input
echo "Migrations complete."

python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from django.contrib.auth import get_user_model

username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
User = get_user_model()

if not username:
    print("No DJANGO_SUPERUSER_USERNAME set — skipping admin seed.")
elif User.objects.filter(username=username).exists():
    print(f"Admin user already exists: {username}")
elif not password:
    print("DJANGO_SUPERUSER_PASSWORD not set — cannot create the admin user.")
else:
    user = User(
        username=username,
        email=os.environ.get("DJANGO_SUPERUSER_EMAIL", username),
        first_name=os.environ.get("DJANGO_SUPERUSER_FIRST_NAME", ""),
        last_name=os.environ.get("DJANGO_SUPERUSER_LAST_NAME", ""),
        is_staff=True,
        is_superuser=True,
        role=User.ROLE_SYSTEM_ADMIN,
        user_type=User.USER_TYPE_INTERNAL,
    )
    user.set_password(password)
    user.save()
    print(f"Admin user created: {username}")
PY
