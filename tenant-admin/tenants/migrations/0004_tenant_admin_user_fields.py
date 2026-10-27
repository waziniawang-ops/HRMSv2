from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_tenant_plan_fk'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tenant',
            old_name='contact_email',
            new_name='admin_email',
        ),
        migrations.AlterField(
            model_name='tenant',
            name='admin_email',
            field=models.EmailField(blank=True, help_text="Login email for the tenant's admin user once provisioned", max_length=254),
        ),
        migrations.AddField(
            model_name='tenant',
            name='admin_first_name',
            field=models.CharField(blank=True, help_text="Tenant's primary admin user", max_length=100),
        ),
        migrations.AddField(
            model_name='tenant',
            name='admin_last_name',
            field=models.CharField(blank=True, help_text="Tenant's primary admin user", max_length=100),
        ),
        migrations.AddField(
            model_name='tenant',
            name='admin_phone',
            field=models.CharField(blank=True, help_text='Optional — for onboarding contact', max_length=30),
        ),
    ]
