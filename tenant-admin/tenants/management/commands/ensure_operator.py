import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Creates the platform-operator superuser from OPERATOR_USERNAME / '
        'OPERATOR_EMAIL / OPERATOR_PASSWORD if it does not exist yet. Never '
        'changes an existing user, so it is safe as part of every deploy.'
    )

    def handle(self, *args, **options):
        username = os.environ.get('OPERATOR_USERNAME', '')
        password = os.environ.get('OPERATOR_PASSWORD', '')
        if not username or not password:
            self.stdout.write('OPERATOR_USERNAME/OPERATOR_PASSWORD not set — skipping operator seed.')
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Operator already exists: {username}')
            return
        User.objects.create_superuser(username, os.environ.get('OPERATOR_EMAIL', ''), password)
        self.stdout.write(f'Operator created: {username}')
