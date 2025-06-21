from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


class Notification(models.Model):
    """
    Model for storing user notifications.
    """
    NOTIFICATION_TYPES = [
        ('proposal_accepted', 'Proposal Accepted'),
        ('proposal_rejected', 'Proposal Rejected'),
        ('message_received', 'New Message'),
        ('job_update', 'Job Update'),
        ('payment_received', 'Payment Received'),
        ('system', 'System Notification'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    url = models.URLField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
            return True
        return False
    
    def get_absolute_url(self):
        """Get the URL for this notification."""
        return self.url or reverse('notifications:list')
        
    def get_badge_type(self):
        """Return the appropriate badge type based on notification type."""
        badge_types = {
            'proposal_accepted': 'success',
            'proposal_rejected': 'danger',
            'message_received': 'info',
            'job_update': 'warning',
            'payment_received': 'success',
            'system': 'secondary',
        }
        return badge_types.get(self.notification_type, 'secondary')
    
    def get_icon(self):
        """Return the appropriate icon based on notification type."""
        icons = {
            'proposal_accepted': 'check-circle-fill',
            'proposal_rejected': 'x-circle-fill',
            'message_received': 'envelope-fill',
            'job_update': 'info-circle-fill',
            'payment_received': 'currency-dollar',
            'system': 'bell-fill',
        }
        return icons.get(self.notification_type, 'bell-fill')
