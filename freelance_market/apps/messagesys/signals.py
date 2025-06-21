from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Message, Thread, ThreadParticipant

User = get_user_model()

@receiver(post_save, sender=Message)
def update_thread_modified(sender, instance, created, **kwargs):
    """Update the thread's modified timestamp when a new message is added"""
    if created and instance.thread:
        instance.thread.save()  # This will update the updated_at field

@receiver(post_save, sender=ThreadParticipant)
def update_thread_participant(sender, instance, created, **kwargs):
    """Update the thread's modified timestamp when a participant is added or modified"""
    if instance.thread:
        instance.thread.save()

@receiver(post_delete, sender=Message)
def update_thread_on_message_delete(sender, instance, **kwargs):
    """Update the thread's modified timestamp when a message is deleted"""
    if instance.thread:
        instance.thread.save()

@receiver(post_save, sender=Message)
def mark_messages_as_read_on_send(sender, instance, created, **kwargs):
    """
    Mark messages as read when a user sends a message in a thread they're participating in
    and update the last_message_notification timestamp
    """
    if created and instance.thread and instance.sender:
        # Mark all messages in this thread as read for the sender
        ThreadParticipant.objects.filter(
            thread=instance.thread,
            user=instance.sender
        ).update(last_read=timezone.now())
        
        # Update the recipient's last_message_notification timestamp
        if instance.recipient != instance.sender:
            User.objects.filter(id=instance.recipient_id).update(
                last_message_notification=timezone.now()
            )

@receiver(m2m_changed, sender=Thread.participants.through)
def update_thread_participants(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Handle thread participant changes and update notification timestamps
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Update the thread's updated_at timestamp
        if isinstance(instance, Thread):
            instance.save(update_fields=['updated_at'])
        elif isinstance(instance, User):
            # If a user was added to multiple threads
            for thread_id in pk_set or []:
                Thread.objects.filter(id=thread_id).update(updated_at=timezone.now())
                
        # Update notification timestamps for added participants
        if action == 'post_add' and pk_set:
            from .models import ThreadParticipant
            now = timezone.now()
            
            # Get the user who performed the action (if any)
            user_pk = getattr(instance, '_current_user_pk', None)
            
            # Update last_message_notification for all added participants
            User.objects.filter(id__in=pk_set).update(last_message_notification=now)
            
            # Create ThreadParticipant records if they don't exist
            if isinstance(instance, Thread):
                for user_id in pk_set:
                    ThreadParticipant.objects.get_or_create(
                        thread=instance,
                        user_id=user_id,
                        defaults={'last_read': now if user_pk == user_id else None}
                    )
