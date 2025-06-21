from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

# Create your models here.

class Skill(models.Model):
    """Model to store freelancer skills."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Freelancer(models.Model):
    """Model to store freelancer-specific information."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='freelancer_profile'
    )
    title = models.CharField(max_length=200, help_text='Professional title/headline')
    bio = models.TextField(blank=True, help_text='Tell us about yourself and your skills')
    skills = models.ManyToManyField(Skill, blank=True, related_name='freelancers')
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Your hourly rate in TZS'
    )
    experience_years = models.PositiveIntegerField(
        default=0,
        help_text='Years of professional experience'
    )
    education = models.TextField(blank=True, help_text='Your educational background')
    portfolio_website = models.URLField(blank=True)
    is_available = models.BooleanField(
        default=True,
        help_text='Available for new projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"
    
    class Meta:
        ordering = ['-created_at']

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_freelancer_profile(sender, instance, created, **kwargs):
    """
    Create a Freelancer profile when a user with is_freelancer=True is created.
    """
    if created and instance.is_freelancer:
        Freelancer.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_freelancer_profile(sender, instance, **kwargs):
    """
    Save the freelancer profile when the user is saved.
    """
    if hasattr(instance, 'freelancer_profile'):
        instance.freelancer_profile.save()
