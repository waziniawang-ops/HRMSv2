from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser

PASSWORD = 'Demo1234!'

USERS = [
    # (username, role, user_type, first_name, last_name, is_staff, is_superuser)
    ('sysadmin',    'SYSTEM_ADMIN',     'INTERNAL', 'Syed',    'Admin',        True,  True),
    ('hr_norziah',  'HR_ADMIN',         'INTERNAL', 'Norziah', 'Kamal',        False, False),
    ('hr_fatimah',  'HR_MAKER',         'INTERNAL', 'Fatimah', 'Hassan',       False, False),
    ('hr_ahmad',    'HR_CHECKER',       'INTERNAL', 'Ahmad',   'Razali',       False, False),
    ('rec_shafiq',  'RECRUITER',        'INTERNAL', 'Shafiq',  'Idris',        False, False),
    ('mgr_dinesh',  'HIRING_MANAGER',   'INTERNAL', 'Dinesh',  'Raj',          False, False),
    ('int_liwei',   'INTERVIEWER',      'INTERNAL', 'Li',      'Wei',          False, False),
    ('fin_rajan',   'FINANCE_CHECKER',  'INTERNAL', 'Rajan',   'Subramaniam',  False, False),
    ('talent_siti', 'TALENT_COMMITTEE', 'INTERNAL', 'Siti',    'Rohani',       False, False),
    ('perf_azlan',  'HR_PERFORMANCE',   'INTERNAL', 'Azlan',   'Yusof',        False, False),
    ('ld_nurul',    'LD_OFFICER',       'INTERNAL', 'Nurul',   'Aina',         False, False),
    ('ldc_hassan',  'LD_CHECKER',       'INTERNAL', 'Hassan',  'Osman',        False, False),
    ('emp_ali',     'EMPLOYEE',         'INTERNAL', 'Ali',     'bin Hamid',    False, False),
]

LABELS = {
    'sysadmin':    'Sys Admin',
    'hr_norziah':  'HR Admin',
    'hr_fatimah':  'HR Maker',
    'hr_ahmad':    'HR Checker',
    'rec_shafiq':  'Recruiter',
    'mgr_dinesh':  'Hiring Mgr',
    'int_liwei':   'Interviewer',
    'fin_rajan':   'Finance',
    'talent_siti': 'Talent Cmt',
    'perf_azlan':  'HR Perf',
    'ld_nurul':    'LD Officer',
    'ldc_hassan':  'LD Checker',
    'emp_ali':     'Employee',
}


class Command(BaseCommand):
    help = 'Create all demo users with Demo1234! password (safe to re-run)'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('  HRMSv2 — Seed Demo Users')
        self.stdout.write('=' * 50)

        created_count = 0
        updated_count = 0

        for username, role, user_type, fname, lname, is_staff, is_superuser in USERS:
            user, created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@hrms.demo',
                    'first_name': fname,
                    'last_name': lname,
                    'role': role,
                    'user_type': user_type,
                    'is_staff': is_staff,
                    'is_superuser': is_superuser,
                },
            )
            # Always reset password and role in case of re-run
            user.set_password(PASSWORD)
            user.role = role
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()

            if created:
                created_count += 1
                status = 'created'
            else:
                updated_count += 1
                status = 'updated'

            self.stdout.write(f'  [{status}] {username:<15} — {LABELS[username]}')

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(
            f'  Done: {created_count} created, {updated_count} updated'
        ))
        self.stdout.write(f'  Password for all accounts: {PASSWORD}')
        self.stdout.write('=' * 50 + '\n')
