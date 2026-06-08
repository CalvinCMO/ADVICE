"""
apps/accounts/management/commands/create_superuser_from_env.py
Creates a superuser from environment variables for automated deployments.
Run: python manage.py create_superuser_from_env
"""

import os

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create a superuser from SUPERUSER_EMAIL, SUPERUSER_PASSWORD, and SUPERUSER_USERNAME env vars'

    def handle(self, *args, **options):
        from apps.accounts.models import User

        email = os.environ.get('SUPERUSER_EMAIL')
        password = os.environ.get('SUPERUSER_PASSWORD')
        username = os.environ.get('SUPERUSER_USERNAME', '')

        if not email:
            raise CommandError('SUPERUSER_EMAIL environment variable is not set.')
        if not password:
            raise CommandError('SUPERUSER_PASSWORD environment variable is not set.')

        # Derive first/last name from SUPERUSER_USERNAME or fall back to sensible defaults
        if username:
            parts = username.strip().split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''
        else:
            first_name = 'Super'
            last_name = 'Admin'

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser with email "{email}" already exists. Skipping.')
            )
            return

        User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        self.stdout.write(
            self.style.SUCCESS(f'✅ Superuser "{email}" created successfully.')
        )
