from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0005_tenant_provisioning_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenant',
            name='provisioning_status',
            field=models.CharField(
                choices=[
                    ('NOT_PROVISIONED', 'Not provisioned'),
                    ('PROVISIONING', 'Provisioning…'),
                    ('ACTIVE', 'Provisioned'),
                    ('FAILED', 'Provisioning failed'),
                    ('DEPROVISIONING', 'Deleting Azure resources…'),
                    ('DEPROVISION_FAILED', 'Failed to delete Azure resources'),
                ],
                default='NOT_PROVISIONED',
                help_text='Set by the automated provisioning flow — not editable by hand.',
                max_length=20,
            ),
        ),
    ]
