import uuid
from django.db import migrations, models
import django.db.models.deletion


MODULES = [
    # (code, name, category, description)
    ('core_hr', 'Core HR', 'CORE', 'Employees, org units, positions, grades'),
    ('workforce', 'Workforce & Leave', 'CORE', 'Leave, overtime, transfers, shift rosters'),
    ('attendance', 'Attendance', 'CORE', 'Face/geo check-in, attendance records'),
    ('ess', 'Employee Self-Service', 'CORE', 'Employee-facing portal and dashboard'),
    ('recruitment', 'Recruitment', 'TALENT', 'Requisitions, postings, applications, offers'),
    ('onboarding', 'Onboarding', 'TALENT', 'New-hire onboarding cases and checklists'),
    ('offboarding', 'Offboarding', 'TALENT', 'Exit process and separation cases'),
    ('succession', 'Succession Planning', 'TALENT', 'Succession plans and talent pools'),
    ('performance', 'Performance Management', 'TALENT', 'Review cycles, goals, outcomes'),
    ('learning', 'Learning & Development', 'TALENT', 'Courses, assignments, skill gaps'),
    ('skills', 'Skills Management', 'TALENT', 'Skills inventory and matrices'),
    ('payroll', 'Payroll', 'FINANCE', 'Payroll runs, payslips, GL postings'),
    ('compensation', 'Compensation', 'FINANCE', 'Salary bands and compensation reviews'),
    ('benefits', 'Benefits', 'FINANCE', 'Benefits enrollment and administration'),
    ('claims', 'Claims', 'FINANCE', 'Expense and medical claims'),
    ('service_desk', 'Service Desk', 'OPERATIONS', 'HR case/ticket management'),
    ('employee_relations', 'Employee Relations', 'OPERATIONS', 'Grievances and disciplinary cases'),
    ('hse', 'Health, Safety & Environment', 'OPERATIONS', 'Incidents, inspections, compliance'),
    ('engagement', 'Engagement', 'OPERATIONS', 'Surveys and engagement tracking'),
]

# (slug, name, description, monthly_price, seat_limit, module_codes)
PLANS = [
    (
        'trial', 'Trial', '14-day evaluation, core modules only.',
        '0.00', 10,
        ['core_hr', 'workforce', 'attendance', 'ess'],
    ),
    (
        'starter', 'Starter', 'Small teams getting started with core HR and hiring.',
        '299.00', 50,
        ['core_hr', 'workforce', 'attendance', 'ess', 'recruitment', 'onboarding', 'learning'],
    ),
    (
        'pro', 'Pro', 'Growing companies needing the full talent lifecycle.',
        '799.00', 200,
        [
            'core_hr', 'workforce', 'attendance', 'ess', 'recruitment', 'onboarding',
            'offboarding', 'learning', 'performance', 'succession', 'skills',
            'service_desk', 'claims',
        ],
    ),
    (
        'enterprise', 'Enterprise', 'Full platform, custom pricing.',
        None, None,
        [code for code, *_ in MODULES],
    ),
]


def seed(apps, schema_editor):
    Module = apps.get_model('tenants', 'Module')
    Plan = apps.get_model('tenants', 'Plan')

    module_by_code = {}
    for code, name, category, description in MODULES:
        module_by_code[code] = Module.objects.create(
            id=uuid.uuid4(), code=code, name=name, category=category, description=description,
        )

    for slug, name, description, price, seat_limit, module_codes in PLANS:
        plan = Plan.objects.create(
            id=uuid.uuid4(), slug=slug, name=name, description=description,
            monthly_price=price, seat_limit=seat_limit,
        )
        plan.modules.set(module_by_code[c] for c in module_codes)


def unseed(apps, schema_editor):
    apps.get_model('tenants', 'Plan').objects.all().delete()
    apps.get_model('tenants', 'Module').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.SlugField(help_text='Matches the HRMSv2 app label, e.g. "payroll"', max_length=50, unique=True)),
                ('name', models.CharField(help_text='Display name, e.g. "Payroll"', max_length=100)),
                ('category', models.CharField(choices=[('CORE', 'Core'), ('TALENT', 'Talent'), ('FINANCE', 'Finance & Rewards'), ('OPERATIONS', 'Operations')], default='CORE', max_length=20)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('is_active', models.BooleanField(default=True, help_text='Inactive modules are hidden from the plan editor, not deleted.')),
            ],
            options={
                'db_table': 'module',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='e.g. "Professional"', max_length=100)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('monthly_price', models.DecimalField(blank=True, decimal_places=2, help_text='Leave blank for custom/quote-based pricing (typical for Enterprise).', max_digits=10, null=True)),
                ('seat_limit', models.PositiveIntegerField(blank=True, help_text='Leave blank for unlimited seats.', null=True)),
                ('is_active', models.BooleanField(default=True, help_text="Inactive plans stay assigned to any tenant already on them, but can't be picked for new ones.")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('modules', models.ManyToManyField(blank=True, related_name='plans', to='tenants.module')),
            ],
            options={
                'db_table': 'plan',
                'ordering': ['monthly_price', 'name'],
            },
        ),
        migrations.RunPython(seed, unseed),
    ]
