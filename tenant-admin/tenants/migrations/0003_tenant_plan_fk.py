from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    Tenant = apps.get_model('tenants', 'Tenant')
    Plan = apps.get_model('tenants', 'Plan')
    plan_by_slug = {p.slug: p for p in Plan.objects.all()}
    trial = plan_by_slug.get('trial')
    for t in Tenant.objects.all():
        # Old field held the choice key (e.g. 'TRIAL'); new Plan.slug is lowercase.
        t.plan_new = plan_by_slug.get((t.plan or '').lower(), trial)
        t.save(update_fields=['plan_new'])


def backwards(apps, schema_editor):
    Tenant = apps.get_model('tenants', 'Tenant')
    for t in Tenant.objects.all():
        t.plan = (t.plan_new.slug if t.plan_new else 'trial').upper()
        t.save(update_fields=['plan'])


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_module_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='plan_new',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='tenants', to='tenants.plan',
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name='tenant',
            name='plan',
        ),
        migrations.RenameField(
            model_name='tenant',
            old_name='plan_new',
            new_name='plan',
        ),
        migrations.AlterField(
            model_name='tenant',
            name='plan',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tenants', to='tenants.plan',
            ),
        ),
    ]
