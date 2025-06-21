from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

from .models import Notification


@receiver(post_save, sender=Notification)
def send_notification_email(sender, instance, created, **kwargs):
    """
    Send an email notification when a new notification is created.
    """
    if created and instance.user.email:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        subject = f"{settings.SITE_NAME} - {instance.title}"
        
        # Render HTML email template
        html_message = render_to_string('notifications/email/notification.html', {
            'notification': instance,
            'site_name': settings.SITE_NAME,
            'protocol': 'https' if settings.USE_HTTPS else 'http',
        })
        
        # Render plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
            html_message=html_message,
            fail_silently=True
        )
