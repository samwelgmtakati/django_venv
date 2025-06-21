from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserProfile(models.Model):
    """
    Extends the custom User model with additional user information.
    Note: This model is being kept for backward compatibility but should be phased out
    in favor of the custom User model in the accounts app.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='dashboard_profile'
    )
    bio = models.TextField(max_length=500, blank=True, help_text='A short bio about yourself.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username}\'s Profile'

    @property
    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'.strip() or self.user.username

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        # Add db_table to make it clear this is from the dashboard app
        db_table = 'dashboard_userprofile'

# Signal to create a profile when a new user signs up
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    This signal is kept for backward compatibility but is not strictly necessary
    since we're using a custom User model with these fields directly.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
    elif hasattr(instance, 'dashboard_profile'):
        instance.dashboard_profile.save()
