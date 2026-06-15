from django.core.management.base import BaseCommand
from apps.workflow.models import WorkflowRule


WORKFLOW_RULES = [

    # ─────────────────────────────────────────────────────────────────────────
    # CORE HR
    # ─────────────────────────────────────────────────────────────────────────
    {
        'workflow_code': 'ORG_UNIT_APPROVAL',
        'module_code': 'core_hr',
        'applies_to': 'OrgUnit',
        'description': (
            'Org Unit Creation / Restructure — any change to the organisational '
            'hierarchy requires HR Checker verification then HR Admin sign-off.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER', 'sla_hours': 24},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'POSITION_APPROVAL',
        'module_code': 'core_hr',
        'applies_to': 'Position',
        'description': (
            'New Position / Headcount Approval — positions must be reviewed by '
            'HR Checker before HR Admin approves the headcount budget.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER', 'sla_hours': 24},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'JOB_GRADE_APPROVAL',
        'module_code': 'core_hr',
        'applies_to': 'JobGrade',
        'description': (
            'Job Grade / Salary Band Change — compensation band adjustments require '
            'HR Checker review, Finance Checker cost validation, then HR Admin approval.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER',     'sla_hours': 24},
            {'step': 2, 'role': 'FINANCE_CHECKER', 'sla_hours': 48},
            {'step': 3, 'role': 'HR_ADMIN',        'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'EMPLOYEE_RECORD_APPROVAL',
        'module_code': 'core_hr',
        'applies_to': 'Employee',
        'description': (
            'Employee Record Amendment — new hire records or contract amendments '
            'require HR Checker then HR Admin endorsement before activation.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER', 'sla_hours': 24},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'JOB_APPROVAL',
        'module_code': 'core_hr',
        'applies_to': 'Job',
        'description': (
            'Job Definition Approval — new job family or job title changes must be '
            'verified by HR Checker and confirmed by HR Admin.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER', 'sla_hours': 24},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # RECRUITMENT
    # ─────────────────────────────────────────────────────────────────────────
    {
        'workflow_code': 'RECRUITMENT_REQUISITION_APPROVAL',
        'module_code': 'recruitment',
        'applies_to': 'JobRequisition',
        'description': (
            'Job Requisition Approval — hiring request raised by Recruiter / HR Maker '
            'is reviewed by Hiring Manager for business need, then HR Admin for '
            'headcount budget sign-off.'
        ),
        'steps': [
            {'step': 1, 'role': 'HIRING_MANAGER', 'sla_hours': 24},
            {'step': 2, 'role': 'HR_ADMIN',        'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'JOB_POSTING_APPROVAL',
        'module_code': 'recruitment',
        'applies_to': 'JobPosting',
        'description': (
            'Job Posting Publication Approval — job adverts must be reviewed by '
            'HR Checker for accuracy and compliance before going live.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER', 'sla_hours': 24},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'APPLICANT_SHORTLIST_APPROVAL',
        'module_code': 'recruitment',
        'applies_to': 'Application',
        'description': (
            'Candidate Shortlist Approval — Hiring Manager reviews and endorses the '
            'shortlisted candidates before interview invitations are sent.'
        ),
        'steps': [
            {'step': 1, 'role': 'HIRING_MANAGER', 'sla_hours': 48},
        ],
        'segregation_of_duties': False,
        'maker_cannot_approve': False,
    },
    {
        'workflow_code': 'INTERVIEW_SCHEDULE_APPROVAL',
        'module_code': 'recruitment',
        'applies_to': 'Interview',
        'description': (
            'Interview Panel Approval — interview schedule and panel composition '
            'is confirmed by the Hiring Manager prior to dispatch.'
        ),
        'steps': [
            {'step': 1, 'role': 'HIRING_MANAGER', 'sla_hours': 24},
        ],
        'segregation_of_duties': False,
        'maker_cannot_approve': False,
    },
    {
        'workflow_code': 'OFFER_APPROVAL',
        'module_code': 'recruitment',
        'applies_to': 'Offer',
        'description': (
            'Offer Letter Approval — compensation offers require HR Checker review, '
            'Finance Checker cost validation, then HR Admin final sign-off before '
            'the letter is released to the candidate.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER',     'sla_hours': 24},
            {'step': 2, 'role': 'FINANCE_CHECKER', 'sla_hours': 48},
            {'step': 3, 'role': 'HR_ADMIN',        'sla_hours': 24},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # ONBOARDING
    # ─────────────────────────────────────────────────────────────────────────
    {
        'workflow_code': 'ONBOARDING_CASE_APPROVAL',
        'module_code': 'onboarding',
        'applies_to': 'OnboardingCase',
        'description': (
            'Onboarding Package Approval — the onboarding task plan and documentation '
            'checklist for a new hire is reviewed by HR Checker then endorsed by '
            'HR Admin before tasks are assigned.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER', 'sla_hours': 24},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # WORKFORCE
    # ─────────────────────────────────────────────────────────────────────────
    {
        'workflow_code': 'LEAVE_REQUEST_APPROVAL',
        'module_code': 'workforce',
        'applies_to': 'LeaveRequest',
        'description': (
            'Leave Request Approval — employee leave requests are first endorsed '
            'by their direct Manager for operational cover, then acknowledged by '
            'HR Checker for records compliance.'
        ),
        'steps': [
            {'step': 1, 'role': 'MANAGER',   'sla_hours': 24},
            {'step': 2, 'role': 'HR_CHECKER', 'sla_hours': 24},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'LEAVE_TYPE_APPROVAL',
        'module_code': 'workforce',
        'applies_to': 'LeaveType',
        'description': (
            'Leave Type / Policy Approval — new or amended leave entitlement policies '
            'require HR Checker review and HR Admin sign-off before they take effect.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER', 'sla_hours': 24},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'OVERTIME_APPROVAL',
        'module_code': 'workforce',
        'applies_to': 'OvertimeRequest',
        'description': (
            'Overtime Request Approval — overtime must be approved by the employee\'s '
            'Manager within 12 hours, followed by HR Checker for payroll processing.'
        ),
        'steps': [
            {'step': 1, 'role': 'MANAGER',   'sla_hours': 12},
            {'step': 2, 'role': 'HR_CHECKER', 'sla_hours': 24},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'TRANSFER_APPROVAL',
        'module_code': 'workforce',
        'applies_to': 'Transfer',
        'description': (
            'Transfer / Internal Promotion Approval — position changes and inter-'
            'department transfers require HR Checker review of grading implications '
            'then HR Admin sign-off on the effective date and compensation.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER', 'sla_hours': 48},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 72},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # SUCCESSION
    # ─────────────────────────────────────────────────────────────────────────
    {
        'workflow_code': 'SUCCESSION_PLAN_APPROVAL',
        'module_code': 'succession',
        'applies_to': 'SuccessionPlan',
        'description': (
            'Succession Plan Approval — critical role succession plans are reviewed '
            'by HR Checker for completeness, endorsed by the Talent Committee for '
            'strategic fit, then finalised by HR Admin.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER',      'sla_hours': 48},
            {'step': 2, 'role': 'TALENT_COMMITTEE', 'sla_hours': 72},
            {'step': 3, 'role': 'HR_ADMIN',         'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'TALENT_POOL_NOMINATION',
        'module_code': 'succession',
        'applies_to': 'TalentPool',
        'description': (
            'Talent Pool Nomination Approval — employees nominated for a talent pool '
            'must be endorsed by their Manager and ratified by the Talent Committee.'
        ),
        'steps': [
            {'step': 1, 'role': 'MANAGER',          'sla_hours': 48},
            {'step': 2, 'role': 'TALENT_COMMITTEE',  'sla_hours': 72},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'TALENT_PROFILE_REVIEW',
        'module_code': 'succession',
        'applies_to': 'TalentProfile',
        'description': (
            'Talent Profile Review and Endorsement — individual talent assessments '
            'are quality-checked by HR Checker then ratified by the Talent Committee '
            'before being visible in succession planning reports.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER',      'sla_hours': 48},
            {'step': 2, 'role': 'TALENT_COMMITTEE', 'sla_hours': 72},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # PERFORMANCE
    # ─────────────────────────────────────────────────────────────────────────
    {
        'workflow_code': 'PERFORMANCE_CYCLE_APPROVAL',
        'module_code': 'performance',
        'applies_to': 'PerformanceCycle',
        'description': (
            'Performance Cycle Setup Approval — annual or mid-year cycle configuration '
            '(timelines, forms, weights) is reviewed by HR Performance Officer then '
            'activated by HR Admin.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_PERFORMANCE', 'sla_hours': 48},
            {'step': 2, 'role': 'HR_ADMIN',        'sla_hours': 72},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'GOAL_PLAN_APPROVAL',
        'module_code': 'performance',
        'applies_to': 'GoalPlan',
        'description': (
            'Goal Plan / KPI Approval — employee KPIs and OKRs are agreed with the '
            'Manager for alignment to department targets, then acknowledged by HR '
            'Performance for calibration.'
        ),
        'steps': [
            {'step': 1, 'role': 'MANAGER',        'sla_hours': 48},
            {'step': 2, 'role': 'HR_PERFORMANCE',  'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'PERFORMANCE_REVIEW_APPROVAL',
        'module_code': 'performance',
        'applies_to': 'ReviewForm',
        'description': (
            'Performance Review Submission — completed review forms are endorsed by '
            'the reviewing Manager then counter-signed by HR Performance before '
            'being locked for calibration.'
        ),
        'steps': [
            {'step': 1, 'role': 'MANAGER',        'sla_hours': 72},
            {'step': 2, 'role': 'HR_PERFORMANCE',  'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'PERFORMANCE_OUTCOME_APPROVAL',
        'module_code': 'performance',
        'applies_to': 'FinalOutcome',
        'description': (
            'Final Performance Outcome / Rating Approval — calibrated ratings and '
            'increment recommendations flow through HR Performance → HR Checker → '
            'HR Admin before the outcome letter is issued.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_PERFORMANCE', 'sla_hours': 48},
            {'step': 2, 'role': 'HR_CHECKER',      'sla_hours': 24},
            {'step': 3, 'role': 'HR_ADMIN',        'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # LEARNING & DEVELOPMENT
    # ─────────────────────────────────────────────────────────────────────────
    {
        'workflow_code': 'COURSE_PUBLICATION_APPROVAL',
        'module_code': 'learning',
        'applies_to': 'Course',
        'description': (
            'Course Publication Approval — new e-learning or instructor-led courses '
            'are quality-reviewed by the L&D Checker then approved for publication '
            'by HR Admin.'
        ),
        'steps': [
            {'step': 1, 'role': 'LD_CHECKER', 'sla_hours': 48},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 72},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'TRAINING_ASSIGNMENT_APPROVAL',
        'module_code': 'learning',
        'applies_to': 'TrainingRequest',
        'description': (
            'External Training / Budget Approval — nominations for external programmes '
            'or conferences are endorsed by the employee\'s Manager for business '
            'relevance, then approved by the L&D Checker for budget allocation.'
        ),
        'steps': [
            {'step': 1, 'role': 'MANAGER',   'sla_hours': 48},
            {'step': 2, 'role': 'LD_CHECKER', 'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
    {
        'workflow_code': 'SKILL_GAP_PLAN_APPROVAL',
        'module_code': 'learning',
        'applies_to': 'SkillGap',
        'description': (
            'Skill Gap Development Plan Approval — individual development plans '
            'addressing identified skill gaps are reviewed by the L&D Officer then '
            'endorsed by HR Admin for resource allocation.'
        ),
        'steps': [
            {'step': 1, 'role': 'LD_OFFICER', 'sla_hours': 72},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 72},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # ATTENDANCE
    # ─────────────────────────────────────────────────────────────────────────
    {
        'workflow_code': 'ATTENDANCE_CORRECTION_APPROVAL',
        'module_code': 'attendance',
        'applies_to': 'AttendanceRecord',
        'description': (
            'Manual Attendance Correction Approval — any manual override of a '
            'check-in / check-out record must be verified by HR Checker and '
            'confirmed by HR Admin to maintain audit integrity.'
        ),
        'steps': [
            {'step': 1, 'role': 'HR_CHECKER', 'sla_hours': 24},
            {'step': 2, 'role': 'HR_ADMIN',   'sla_hours': 48},
        ],
        'segregation_of_duties': True,
        'maker_cannot_approve': True,
    },
]


class Command(BaseCommand):
    help = 'Seed WorkflowRule records for all system modules (idempotent)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete ALL existing workflow rules before seeding (useful for demos)',
        )

    def handle(self, *args, **options):
        if options['reset']:
            count, _ = WorkflowRule.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'  Deleted {count} existing rules.'))

        created = updated = 0

        for rule_data in WORKFLOW_RULES:
            obj, was_created = WorkflowRule.objects.update_or_create(
                workflow_code=rule_data['workflow_code'],
                defaults={
                    'module_code':            rule_data['module_code'],
                    'applies_to':             rule_data['applies_to'],
                    'description':            rule_data['description'],
                    'steps':                  rule_data['steps'],
                    'segregation_of_duties':  rule_data['segregation_of_duties'],
                    'maker_cannot_approve':   rule_data['maker_cannot_approve'],
                    'audit_required':         True,
                    'is_active':              True,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  [+] {obj.workflow_code:<45} ({obj.module_code})')
                )
            else:
                updated += 1
                self.stdout.write(
                    f'  [~] {obj.workflow_code:<45} ({obj.module_code})'
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done — {created} created, {updated} updated. '
            f'Total rules: {WorkflowRule.objects.count()}'
        ))
