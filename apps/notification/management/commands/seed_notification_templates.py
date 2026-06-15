from django.core.management.base import BaseCommand
from apps.notification.models import NotificationTemplate


TEMPLATES = [
    {
        'code': 'WORKFLOW_UPDATE',
        'channel': 'IN_APP',
        'name': 'Workflow Status Update (In-App)',
        'subject': 'Your {{ object_type }} request has been {{ action }}',
        'body_template': 'Your {{ object_type }} (ID: {{ object_id }}) has been {{ action }} by {{ actor }}. Current status: {{ status }}.',
    },
    {
        'code': 'WORKFLOW_UPDATE',
        'channel': 'EMAIL',
        'name': 'Workflow Status Update (Email)',
        'subject': '[HRMS] {{ object_type }} Request Update — {{ action }}',
        'body_template': (
            'Dear User,\n\n'
            'Your {{ object_type }} request (ID: {{ object_id }}) has been {{ action }} by {{ actor }}.\n'
            'Current status: {{ status }}.\n\n'
            'Please log in to the HRMS portal for more details.\n\n'
            'This is an automated notification. Please do not reply.'
        ),
    },
    {
        'code': 'LEAVE_APPROVED',
        'channel': 'IN_APP',
        'name': 'Leave Request Approved',
        'subject': 'Leave Request Approved',
        'body_template': 'Your {{ leave_type }} leave request from {{ start_date }} to {{ end_date }} has been approved.',
    },
    {
        'code': 'LEAVE_REJECTED',
        'channel': 'IN_APP',
        'name': 'Leave Request Rejected',
        'subject': 'Leave Request Rejected',
        'body_template': 'Your {{ leave_type }} leave request from {{ start_date }} to {{ end_date }} has been rejected. Reason: {{ notes }}.',
    },
    {
        'code': 'OFFER_EXTENDED',
        'channel': 'EMAIL',
        'name': 'Offer Letter Extended to Applicant',
        'subject': 'Job Offer — {{ position_title }} at {{ company_name }}',
        'body_template': (
            'Dear {{ applicant_name }},\n\n'
            'We are pleased to extend you an offer for the position of {{ position_title }}.\n'
            'Please log in to our applicant portal to review and respond to your offer.\n\n'
            'This offer expires on {{ expiry_date }}.\n\n'
            'Kind regards,\n{{ company_name }} HR Team'
        ),
    },
    {
        'code': 'ONBOARDING_STARTED',
        'channel': 'IN_APP',
        'name': 'Onboarding Case Started',
        'subject': 'Your onboarding has started',
        'body_template': 'Your onboarding process has been initiated. Please complete all required tasks before {{ target_start_date }}.',
    },
    {
        'code': 'REVIEW_REMINDER',
        'channel': 'IN_APP',
        'name': 'Performance Review Reminder',
        'subject': 'Reminder: {{ review_type }} Review due {{ due_date }}',
        'body_template': 'Reminder: Your {{ review_type }} for cycle {{ cycle }} is due on {{ due_date }}. Please complete it in time.',
    },
    {
        'code': 'TRAINING_ASSIGNMENT',
        'channel': 'IN_APP',
        'name': 'New Training Assignment',
        'subject': 'New training assigned: {{ course_title }}',
        'body_template': 'You have been assigned a new training: {{ course_title }}. Due date: {{ due_date }}.',
    },
]


class Command(BaseCommand):
    help = 'Seed initial NotificationTemplate records'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for tmpl_data in TEMPLATES:
            obj, was_created = NotificationTemplate.objects.update_or_create(
                code=tmpl_data['code'],
                channel=tmpl_data['channel'],
                defaults={
                    'name': tmpl_data['name'],
                    'subject': tmpl_data['subject'],
                    'body_template': tmpl_data['body_template'],
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: [{obj.channel}] {obj.code}'))
            else:
                updated += 1
                self.stdout.write(f'  Updated: [{obj.channel}] {obj.code}')

        self.stdout.write(
            self.style.SUCCESS(f'\nDone. Created: {created}, Updated: {updated}')
        )
