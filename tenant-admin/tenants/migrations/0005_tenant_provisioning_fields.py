from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_tenant_admin_user_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='provisioning_status',
            field=models.CharField(
                choices=[
                    ('NOT_PROVISIONED', 'Not provisioned'),
                    ('PROVISIONING', 'Provisioning…'),
                    ('ACTIVE', 'Provisioned'),
                    ('FAILED', 'Provisioning failed'),
                ],
                default='NOT_PROVISIONED',
                help_text='Set by the automated provisioning flow — not editable by hand.',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='tenant',
            name='provisioning_error',
            field=models.TextField(blank=True, help_text='Set when provisioning_status is FAILED.'),
        ),
        migrations.AddField(
            model_name='tenant',
            name='backend_url',
            field=models.URLField(blank=True, help_text="This tenant's own backend API, once provisioned."),
        ),
        migrations.AddField(
            model_name='tenant',
            name='frontend_url',
            field=models.URLField(blank=True, help_text="This tenant's own frontend app, once provisioned."),
        ),
        migrations.AddField(
            model_name='tenant',
            name='provisioned_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
