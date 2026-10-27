from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0006_tenant_deprovisioning_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='admin_password_encrypted',
            field=models.TextField(
                blank=True,
                help_text=(
                    "The admin user's generated login password, Fernet-encrypted "
                    '(tenants/crypto.py) — set once by provisioning, decrypted on '
                    "demand via TenantViewSet's reveal-password action. Never "
                    'exposed in plaintext through the normal serializer.'
                ),
            ),
        ),
    ]
