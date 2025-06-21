from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates an admin user'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',  # Change this in production!
                is_admin=True,
                is_staff=True
            )
            self.stdout.write(self.style.SUCCESS('Successfully created admin user'))
        else:
            self.stdout.write('Admin user already exists')
