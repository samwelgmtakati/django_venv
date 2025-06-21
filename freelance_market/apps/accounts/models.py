from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom user model that extends the default User model."""
    email = models.EmailField(_('email address'), unique=True)
    is_freelancer = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)  # Admin flag
    
    # User details
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return self.username
        
    # is_staff is managed by Django's auth system, but we'll make it return is_admin
    # to maintain compatibility with Django's admin site
    @property
    def is_staff(self):
        """Override is_staff to allow admin users to access the admin site."""
        return self.is_admin
        
    @is_staff.setter
    def is_staff(self, value):
        """Allow Django to set is_staff, but map it to is_admin."""
        self.is_admin = value

class UserProfile(models.Model):
    """Profile model that extends the User model with additional information."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved."""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # In case the profile wasn't created by the create signal
        UserProfile.objects.create(user=instance)
