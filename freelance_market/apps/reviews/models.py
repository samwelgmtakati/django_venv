from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Review(models.Model):
    RATING_CHOICES = [
        (1, _('1 - Poor')),
        (2, _('2 - Fair')),
        (3, _('3 - Average')),
        (4, _('4 - Good')),
        (5, _('5 - Excellent')),
    ]

    order = models.ForeignKey(
        'jobs.Order', 
        on_delete=models.CASCADE, 
        related_name='job_reviews',
        verbose_name=_('order')
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='freelance_reviews_given',
        verbose_name=_('reviewer')
    )
    user_being_reviewed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='freelance_reviews_received',
        verbose_name=_('user being reviewed')
    )
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(_('comment'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    is_client_review = models.BooleanField(
        _('is client review'),
        default=False,
        help_text=_('True if client is reviewing freelancer')
    )

    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        unique_together = ('order', 'reviewer')
        ordering = ['-created_at']

    def __str__(self):
        return _("Review for {user} by {reviewer} - {rating} stars").format(
            user=self.user_being_reviewed,
            reviewer=self.reviewer,
            rating=self.rating
        )
