from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify

class Service(models.Model):
    FREELANCER = 'freelancer'
    AGENCY = 'agency'
    SERVICE_TYPES = [
        (FREELANCER, 'Freelancer Service'),
        (AGENCY, 'Agency Service'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time = models.PositiveIntegerField(help_text='Delivery time in days')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default=FREELANCER)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
    
    def __str__(self):
        return f"{self.title} by {self.freelancer.username}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.freelancer.username}")
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('services:service_detail', kwargs={'slug': self.slug})
