from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Count, Q

class ReviewQuerySet(models.QuerySet):
    def verified(self):
        return self.filter(is_verified=True)
    
    def for_user(self, user):
        return self.filter(user_being_reviewed=user)
    
    def with_ratings(self):
        return self.annotate(
            avg_rating=Avg('rating'),
            total_ratings=Count('id')
        )

class Review(models.Model):
    RATING_CHOICES = [
        (1, _('1 - Poor')),
        (2, _('2 - Fair')),
        (3, _('3 - Average')),
        (4, _('4 - Good')),
        (5, _('5 - Excellent')),
    ]
    
    # Core fields
    order = models.ForeignKey(
        'jobs.Order', 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name=_('order')
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='reviews_given',
        verbose_name=_('reviewer')
    )
    user_being_reviewed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='reviews_received',
        verbose_name=_('user being reviewed')
    )
    
    # Main rating and comment
    rating = models.PositiveSmallIntegerField(
        _('overall rating'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text=_('Overall rating (optional if detailed ratings are provided)')
    )
    comment = models.TextField(_('comment'), blank=True, null=True)
    
    # Detailed ratings
    communication_rating = models.PositiveSmallIntegerField(
        _('communication'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    quality_rating = models.PositiveSmallIntegerField(
        _('quality of work'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    deadline_rating = models.PositiveSmallIntegerField(
        _('meeting deadlines'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    professionalism_rating = models.PositiveSmallIntegerField(
        _('professionalism'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Response and interaction
    response = models.TextField(_('response'), blank=True, null=True)
    response_date = models.DateTimeField(_('response date'), blank=True, null=True)
    
    # Status and metadata
    is_client_review = models.BooleanField(
        _('is client review'),
        default=False,
        help_text=_('True if client is reviewing freelancer')
    )
    is_verified = models.BooleanField(
        _('is verified'),
        default=False,
        help_text=_('Mark if the review has been verified by admin')
    )
    was_edited = models.BooleanField(_('was edited'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Engagement metrics
    helpful_count = models.PositiveIntegerField(_('helpful count'), default=0)
    
    objects = ReviewQuerySet.as_manager()
    
    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        unique_together = ('order', 'reviewer')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_being_reviewed', 'is_verified']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return _("Review for {user} by {reviewer} - {rating} stars").format(
            user=self.user_being_reviewed,
            reviewer=self.reviewer,
            rating=self.rating
        )
    
    def save(self, *args, **kwargs):
        if self.pk:
            self.was_edited = True
        super().save(*args, **kwargs)
    
    @property
    def has_detailed_ratings(self):
        return all([
            self.communication_rating,
            self.quality_rating,
            self.deadline_rating,
            self.professionalism_rating
        ])
    
    def get_average_rating(self):
        if self.has_detailed_ratings:
            ratings = [
                self.communication_rating,
                self.quality_rating,
                self.deadline_rating,
                self.professionalism_rating
            ]
            return sum(ratings) / len(ratings)
        return self.rating
    
    def add_response(self, response_text):
        self.response = response_text
        self.response_date = timezone.now()
        self.save(update_fields=['response', 'response_date'])
    
    def mark_helpful(self, user):
        from .models import ReviewHelpfulVote
        vote, created = ReviewHelpfulVote.objects.get_or_create(
            review=self,
            user=user,
            defaults={'is_helpful': True}
        )
        if created:
            self.helpful_count += 1
            self.save(update_fields=['helpful_count'])
        return created


class ReviewHelpfulVote(models.Model):
    """Tracks which users found which reviews helpful."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpful_votes',
        verbose_name=_('review')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='helpful_votes',
        verbose_name=_('user')
    )
    is_helpful = models.BooleanField(_('is helpful'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        unique_together = ('review', 'user')
        verbose_name = _('helpful vote')
        verbose_name_plural = _('helpful votes')
    
    def __str__(self):
        return f"{'Helpful' if self.is_helpful else 'Not helpful'} vote by {self.user}"


def update_user_rating(user):
    """Update the user's average rating based on all their reviews."""
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Avg
    
    # Get the user's profile model based on user type
    try:
        if hasattr(user, 'freelancer'):
            profile = user.freelancer
        elif hasattr(user, 'client'):
            profile = user.client
        else:
            return None
            
        # Calculate average rating
        result = Review.objects.filter(
            user_being_reviewed=user,
            is_verified=True
        ).aggregate(avg_rating=Avg('rating'))
        
        if result['avg_rating'] is not None:
            profile.average_rating = round(result['avg_rating'], 1)
            profile.save(update_fields=['average_rating'])
            return profile.average_rating
            
    except Exception as e:
        # Log error but don't break the flow
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating user rating for {user}: {str(e)}")
    
    return None
