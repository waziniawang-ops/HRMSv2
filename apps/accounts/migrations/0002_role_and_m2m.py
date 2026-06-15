"""
Migration: introduce dynamic RBAC
  1. Create auth_role table
  2. Add auth_user_roles M2M junction table
  3. Data-seed all 15 system roles
  4. For every existing user, add their primary `role` field value to the M2M set
"""
from django.conf import settings
from django.db import migrations, models


ROLES_SEED = [
    ('SYSTEM_ADMIN',    'System Admin'),
    ('HR_ADMIN',        'HR Admin'),
    ('HR_MAKER',        'HR Maker'),
    ('HR_CHECKER',      'HR Checker'),
    ('HIRING_MANAGER',  'Hiring Manager'),
    ('INTERVIEWER',     'Interviewer'),
    ('RECRUITER',       'Recruiter'),
    ('FINANCE_CHECKER', 'Finance Checker'),
    ('TALENT_COMMITTEE','Talent Committee'),
    ('HR_PERFORMANCE',  'HR Performance Officer'),
    ('LD_OFFICER',      'L&D Officer'),
    ('LD_CHECKER',      'L&D Checker'),
    ('MANAGER',         'Manager'),
    ('EMPLOYEE',        'Employee'),
    ('APPLICANT',       'Applicant'),
]


def seed_roles_and_assign(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    CustomUser = apps.get_model('accounts', 'CustomUser')

    role_map = {}
    for code, display_name in ROLES_SEED:
        role_obj, _ = Role.objects.get_or_create(
            code=code,
            defaults={'display_name': display_name},
        )
        role_map[code] = role_obj

    for user in CustomUser.objects.all():
        if user.role and user.role in role_map:
            user.roles.add(role_map[user.role])


def unseed_roles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.filter(code__in=[r[0] for r in ROLES_SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=30, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'auth_role',
                'ordering': ['code'],
            },
        ),
        migrations.AddField(
            model_name='customuser',
            name='roles',
            field=models.ManyToManyField(
                blank=True,
                db_table='auth_user_roles',
                help_text='All system roles assigned to this user',
                related_name='users',
                to='accounts.role',
            ),
        ),
        migrations.RunPython(seed_roles_and_assign, unseed_roles),
    ]
