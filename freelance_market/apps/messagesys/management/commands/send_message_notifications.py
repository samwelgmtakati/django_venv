from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.sites.models import Site

from apps.accounts.models import User
from apps.messagesys.models import ThreadParticipant, Message

import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sends email notifications for unread messages'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually sending emails',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all users with unread messages who haven't been notified recently
        users = User.objects.filter(
            received_messages__read_at__isnull=True
        ).distinct()
        
        if not users.exists():
            self.stdout.write(self.style.SUCCESS('No users with unread messages found.'))
            return
        
        site = Site.objects.get_current()
        email_count = 0
        
        for user in users:
            # Skip if user has disabled email notifications
            if hasattr(user, 'notification_settings') and not user.notification_settings.email_message_received:
                continue
                
            # Get unread messages grouped by thread
            unread_threads = ThreadParticipant.objects.filter(
                user=user,
                thread__messages__read_at__isnull=True,
                thread__messages__recipient=user,
                is_muted=False
            ).distinct().select_related('thread')
            
            if not unread_threads.exists():
                continue
                
            # Prepare context for email
            context = {
                'user': user,
                'site': site,
                'unread_threads': [],
                'total_unread': 0
            }
            
            # Get message details for each thread
            for participant in unread_threads:
                thread = participant.thread
                unread_messages = thread.messages.filter(
                    recipient=user,
                    read_at__isnull=True
                ).select_related('sender').order_by('sent_at')
                
                if not unread_messages.exists():
                    continue
                    
                context['unread_threads'].append({
                    'thread': thread,
                    'messages': unread_messages,
                    'count': unread_messages.count()
                })
                context['total_unread'] += unread_messages.count()
            
            if not context['unread_threads']:
                continue
                
            # Skip if the user has been notified recently (e.g., in the last hour)
            last_notification = getattr(user, 'last_message_notification', None)
            if last_notification and (timezone.now() - last_notification).total_seconds() < 3600:
                continue
                
            # Render email content
            subject = f"You have {context['total_unread']} unread message{'' if context['total_unread'] == 1 else 's'}"
            text_content = render_to_string('emails/message_notification.txt', context)
            html_content = render_to_string('emails/message_notification.html', context)
            
            # Send email
            if not dry_run:
                try:
                    send_mail(
                        subject=subject,
                        message=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_content,
                        fail_silently=False,
                    )
                    email_count += 1
                    
                    # Update last notification time
                    user.last_message_notification = timezone.now()
                    user.save(update_fields=['last_message_notification'])
                    
                    self.stdout.write(self.style.SUCCESS(f'Sent notification to {user.email}'))
                except Exception as e:
                    logger.error(f'Error sending notification to {user.email}: {str(e)}')
                    self.stdout.write(self.style.ERROR(f'Error sending to {user.email}: {str(e)}'))
            else:
                self.stdout.write(f'[DRY RUN] Would send notification to {user.email}')
                
        self.stdout.write(self.style.SUCCESS(f'Successfully sent {email_count} email notifications.'))
