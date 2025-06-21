from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Thread(models.Model):
    """A conversation thread between two or more users."""
    subject = models.CharField(
        _('subject'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('Subject of the conversation')
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='threads',
        verbose_name=_('participants'),
        help_text=_('Users participating in this conversation')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When the conversation was started')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('When the last message was sent')
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this conversation is active')
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('thread')
        verbose_name_plural = _('threads')

    def __str__(self):
        if self.subject:
            return self.subject
        participants = self.participants.all()[:3]
        usernames = [user.get_short_name() or user.username for user in participants]
        if self.participants.count() > 3:
            usernames.append('...')
        return ', '.join(usernames)
    
    def get_absolute_url(self):
        return reverse('messages:thread_detail', args=[str(self.id)])
    
    def get_other_participant(self, user):
        """Get the other participant in a 1:1 conversation."""
        if self.participants.count() == 2:
            return self.participants.exclude(id=user.id).first()
        return None
    
    def mark_read_for_user(self, user):
        """Mark all messages in this thread as read for a user."""
        self.messages.filter(recipient=user, read_at__isnull=True).update(
            read_at=timezone.now()
        )


class Message(models.Model):
    """A single message in a conversation thread."""
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('thread'),
        help_text=_('The conversation this message belongs to')
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('sender'),
        help_text=_('User who sent the message')
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='received_messages',
        verbose_name=_('recipient'),
        null=True,
        blank=True,
        help_text=_('Intended recipient of the message')
    )
    body = models.TextField(
        _('message'),
        help_text=_('The message content')
    )
    sent_at = models.DateTimeField(
        _('sent at'),
        auto_now_add=True,
        help_text=_('When the message was sent')
    )
    read_at = models.DateTimeField(
        _('read at'),
        null=True,
        blank=True,
        help_text=_('When the message was read by the recipient')
    )
    parent_msg = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('parent message'),
        help_text=_('The message this is a reply to')
    )

    class Meta:
        ordering = ['sent_at']
        verbose_name = _('message')
        verbose_name_plural = _('messages')

    def __str__(self):
        return f"{self.sender} to {self.recipient}: {self.body[:50]}"
    
    @property
    def is_read(self):
        return self.read_at is not None
    
    def mark_as_read(self):
        """Mark this message as read."""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
    
    def get_absolute_url(self):
        return f"{self.thread.get_absolute_url()}#message-{self.id}"
