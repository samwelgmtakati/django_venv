from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class OrderReview(models.Model):
    """Rating & review left by users after an order is completed."""
    RATING_CHOICES = [
        (1, _('1 - Poor')),
        (2, _('2 - Fair')),
        (3, _('3 - Average')),
        (4, _('4 - Good')),
        (5, _('5 - Excellent')),
    ]
    
    order = models.OneToOneField(
        'jobs.Order',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name=_('order'),
        db_column='order_id'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_reviews',
        verbose_name=_('client'),
        db_column='client_id'
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='freelancer_reviews',
        verbose_name=_('freelancer'),
        db_column='freelancer_id'
    )
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(_('comment'), blank=True)
    is_client_review = models.BooleanField(
        _('is client review'),
        default=False,
        help_text=_('True if this is a client reviewing a freelancer')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('order review')
        verbose_name_plural = _('order reviews')
        unique_together = ('order', 'client')

    def __str__(self):
        return _('%(rating)s/5 review by %(client)s for %(freelancer)s') % {
            'rating': self.rating,
            'client': self.client.get_short_name() or self.client.username,
            'freelancer': self.freelancer.get_short_name() or self.freelancer.username
        }
        
    def save(self, *args, **kwargs):
        # Ensure client and freelancer are set correctly
        if not self.pk:  # Only on creation
            if not self.client_id:
                self.client = self.order.client
            if not self.freelancer_id:
                self.freelancer = self.order.freelancer
            
            # Set is_client_review based on who is leaving the review
            if hasattr(self, 'order') and hasattr(self.order, 'client'):
                self.is_client_review = (self.client_id == self.order.client_id)
        
        super().save(*args, **kwargs)


class OrderQuerySet(models.QuerySet):
    def with_review_info(self, user):
        """Annotate each order with review-related information."""
        from django.db.models import Case, When, Value, BooleanField, Q
        
        return self.annotate(
            can_review=Case(
                When(
                    Q(status=Order.STATUS_COMPLETED) & 
                    ~Q(review__isnull=False) &
                    (Q(client=user) | Q(freelancer=user)),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            ),
            has_reviewed=Case(
                When(review__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        )


class OrderManager(models.Manager):
    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db)
    
    def with_review_info(self, user):
        return self.get_queryset().with_review_info(user)
