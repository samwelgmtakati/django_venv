from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils import timezone

from apps.messagesys.models import Thread, Message, ThreadParticipant

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a test message and sends a notification'
    
    def handle(self, *args, **options):
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
                'is_staff': False,
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test user: {user.email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing test user: {user.email}'))
        
        # Create a test thread
        thread = Thread.objects.create(subject='Test Message Thread')
        
        # Add the test user as a participant
        ThreadParticipant.objects.create(
            thread=thread,
            user=user,
            last_read=timezone.now()
        )
        
        # Create a test message
        message = Message.objects.create(
            thread=thread,
            sender=user,
            recipient=user,
            subject='Test Message',
            body='This is a test message to verify the notification system is working correctly.',
            sent_at=timezone.now()
        )
        
        self.stdout.write(self.style.SUCCESS('Created test message'))
        
        # Now run the notification command
        self.stdout.write('\nSending test notification...\n')
        
        from django.core.management import call_command
        call_command('send_message_notifications', '--dry-run')
        
        self.stdout.write('\nTo actually send the notification, run:')
        self.stdout.write(self.style.SUCCESS('python manage.py send_message_notifications'))
