import os
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from .utils import get_file_icon, get_file_type_display, format_file_size


class Notification(models.Model):
    """
    Model for storing notifications for users.
    """
    # Recipient of the notification
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_notifications',  # Changed from 'notifications' to 'job_notifications'
        help_text="The user who will receive this notification"
    )
    
    # Actor - the user who performed the action
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='actor_job_notifications',  # Changed from 'actor_notifications'
        null=True,
        blank=True,
        help_text="The user who triggered this notification"
    )
    
    # Verb - the action that was performed (e.g., 'commented', 'liked', 'shared')
    verb = models.CharField(max_length=255)
    
    # Target - the object that the action was performed on (optional)
    target_content_type = models.ForeignKey(
        ContentType,
        related_name='target_obj',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')
    
    # Additional data that might be needed
    data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Track if notification was sent via email
    emailed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'read_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.actor} {self.verb} for {self.recipient}"
    
    def mark_as_read(self):
        """Mark the notification as read."""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
    
    def mark_as_unread(self):
        """Mark the notification as unread."""
        if self.read_at:
            self.read_at = None
            self.save(update_fields=['read_at'])
    
    @property
    def is_read(self):
        """Check if the notification has been read."""
        return self.read_at is not None
    
    @classmethod
    def get_unread_count(cls, user):
        """Get the count of unread notifications for a user."""
        return cls.objects.filter(recipient=user, read_at__isnull=True).count()


class JobCategory(models.Model):
    """Category for jobs (e.g., Web Development, Design, Writing, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name_plural = 'Job Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Job(models.Model):
    """Model for job postings by clients"""
    
    JOB_TYPES = [
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly'),
    ]
    
    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique_for_date='created_at')
    description = models.TextField()
    requirements = models.TextField(help_text="Skills and requirements for this job")
    
    # Job Details
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='fixed')
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, related_name='jobs')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='intermediate')
    
    # Budget and Duration
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 1-3 months, 3-6 months, etc.")
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    
    # Relationships
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='posted_jobs',
        limit_choices_to={'is_client': True}
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_jobs',
        limit_choices_to={'is_freelancer': True}
    )
    
    # Metadata
    views = models.PositiveIntegerField(default=0)
    proposals_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['job_type']),
            models.Index(fields=['experience_level']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Job.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('jobs:job_detail', kwargs={'slug': self.slug})
    
    def increment_views(self):
        """Increment the view count for this job"""
        self.views += 1
        self.save(update_fields=['views'])
    
    def can_edit(self, user):
        """Check if the given user can edit this job"""
        return user == self.client or user.is_superuser


class JobProposal(models.Model):
    """Proposals submitted by freelancers for a job"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='proposals')
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='job_proposals',
        limit_choices_to={'is_freelancer': True}
    )
    cover_letter = models.TextField()
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['job', 'freelancer']
    
    def __str__(self):
        return f"{self.freelancer.get_full_name() or self.freelancer.username}'s proposal for {self.job.title}"
    
    def can_edit(self, user):
        """Check if the given user can edit this proposal"""
        return user == self.freelancer and self.status == 'pending'


# ----------------------
# (Order Management moved to apps.orders.models)
# ----------------------
# ----------------------
class OrderQuerySet(models.QuerySet):
    def with_review_info(self, user):
        """Annotate each order with review-related information."""
        from django.db.models import Case, When, Value, BooleanField, Q, Exists, OuterRef
        
        # Check if the current user has reviewed this order
        from apps.orders.models import OrderReview
        
        return self.annotate(
            can_review=Case(
                When(
                    Q(status=Order.STATUS_APPROVED) & 
                    ~Q(order_reviews__reviewer=user) &
                    (Q(client=user) | Q(freelancer=user)),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            ),
            has_reviewed=Exists(
                OrderReview.objects.filter(
                    order_id=OuterRef('pk'),
                    reviewer=user
                )
            )
        )


class OrderManager(models.Manager):
    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db)
    
    def with_review_info(self, user):
        return self.get_queryset().with_review_info(user)


class Order(models.Model):
    """Represents an agreed contract created once a proposal is accepted."""

    # Order status constants
    STATUS_INITIATED = 'initiated'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DELIVERED = 'delivered'
    STATUS_APPROVED = 'approved'
    STATUS_REVISION_REQUESTED = 'revision_requested'
    STATUS_CANCELLED = 'cancelled'
    STATUS_DISPUTED = 'disputed'
    STATUS_COMPLETED = 'completed'  # Added for review purposes

    STATUS_CHOICES = [
        (STATUS_INITIATED, 'Initiated'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_COMPLETED, 'Completed'),  # Added for review purposes
        (STATUS_REVISION_REQUESTED, 'Revision Requested'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_DISPUTED, 'In Dispute'),
    ]

    # Payment status constants
    PAYMENT_PENDING = 'pending'
    PAYMENT_PAID = 'paid'
    PAYMENT_REFUNDED = 'refunded'
    PAYMENT_DISPUTED = 'disputed'

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, 'Payment Pending'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_REFUNDED, 'Payment Refunded'),
        (PAYMENT_DISPUTED, 'Payment Disputed'),
    ]

    # Core relationships
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='orders')
    proposal = models.OneToOneField('JobProposal', on_delete=models.CASCADE, related_name='order')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_orders')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='freelancer_orders')

    # Status tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_INITIATED)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING)
    
    # Financials
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    
    # Custom manager
    objects = OrderManager()
    
    # Revision tracking
    revision_count = models.PositiveIntegerField(default=0)
    max_revisions = models.PositiveIntegerField(default=3)  # Default max revisions
    last_revision_requested_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    requirements = models.JSONField(default=dict, blank=True)  # Store order requirements checklist
    metadata = models.JSONField(default=dict, blank=True)  # For additional data

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['client']),
            models.Index(fields=['freelancer']),
            models.Index(fields=['deadline']),
        ]

    def __str__(self):
        return f"Order #{self.pk} - {self.job.title}"

    # Status transition methods
    def mark_in_progress(self, save=True):
        """Mark order as in progress."""
        if self.status != self.STATUS_INITIATED:
            raise ValueError(f"Cannot mark as in progress from status {self.status}")
            
        self.status = self.STATUS_IN_PROGRESS
        self.started_at = timezone.now()
        
        if save:
            self.save(update_fields=['status', 'started_at', 'updated_at'])
        return True

    def mark_in_progress(self, save=True):
        """Mark order as in progress."""
        if self.status != self.STATUS_INITIATED:
            raise ValueError(f"Cannot mark as in_progress from status {self.status}")
            
        self.status = self.STATUS_IN_PROGRESS
        self.started_at = timezone.now()
        
        if save:
            self.save(update_fields=['status', 'started_at', 'updated_at'])
        return True

    def mark_delivered(self, message='', save=True):
        """Mark order as delivered with optional message."""
        if self.status not in [self.STATUS_IN_PROGRESS, self.STATUS_REVISION_REQUESTED]:
            raise ValueError(f"Cannot mark as delivered from status {self.status}")
            
        self.status = self.STATUS_DELIVERED
        self.delivered_at = timezone.now()
        
        if save:
            self.save(update_fields=['status', 'delivered_at', 'updated_at'])
        return True

    def request_revision(self, message='', save=True):
        """Request a revision from the freelancer."""
        if self.status != self.STATUS_DELIVERED:
            raise ValueError(f"Cannot request revision from status {self.status}")
            
        if self.revision_count >= self.max_revisions:
            raise ValueError("Maximum number of revisions reached")
            
        self.status = self.STATUS_REVISION_REQUESTED
        self.revision_count += 1
        self.last_revision_requested_at = timezone.now()
        
        if save:
            self.save(update_fields=[
                'status', 
                'revision_count', 
                'last_revision_requested_at', 
                'updated_at'
            ])
        return True

    def mark_approved(self, save=True):
        """Mark order as approved by client."""
        if self.status != self.STATUS_DELIVERED:
            raise ValueError("Only delivered orders can be approved")
            
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        
        # Mark as completed if payment is already made
        if self.payment_status == self.PAYMENT_PAID:
            self.mark_completed(save=False)
        
        if save:
            self.save()
            
        return True

    def cancel(self, reason='', save=True):
        """Cancel the order."""
        if self.status in [self.STATUS_APPROVED, self.STATUS_CANCELLED]:
            raise ValueError(f"Cannot cancel order in status {self.status}")
            
        self.status = self.STATUS_CANCELLED
        self.completed_at = timezone.now()
        

    # Utility methods
    @property
    def is_active(self):
        """Check if the order is currently active."""
        return self.status in [self.STATUS_IN_PROGRESS, self.STATUS_DELIVERED, self.STATUS_REVISION_REQUESTED]

    @property
    def is_completed(self):
        """Check if the order is completed."""
        return self.status in [self.STATUS_APPROVED, self.STATUS_CANCELLED]

    @property
    def days_remaining(self):
        """Calculate days remaining until deadline."""
        if not self.deadline:
            return None
        delta = self.deadline - timezone.now()
        return max(0, delta.days)

    def get_absolute_url(self):
        """Get the absolute URL for this order."""
        from django.urls import reverse
        return reverse('orders:detail', kwargs={'pk': self.pk})
        
    def get_status_badge_class(self):
        """Return the appropriate Bootstrap badge class for the current status."""
        status_classes = {
            self.STATUS_INITIATED: 'bg-secondary',
            self.STATUS_IN_PROGRESS: 'bg-primary',
            self.STATUS_DELIVERED: 'bg-info text-dark',
            self.STATUS_APPROVED: 'bg-success',
            self.STATUS_REVISION_REQUESTED: 'bg-warning text-dark',
            self.STATUS_CANCELLED: 'bg-danger',
            self.STATUS_DISPUTED: 'bg-danger',
        }
        return status_classes.get(self.status, 'bg-secondary')
        
    def get_payment_status_badge_class(self):
        """Return the appropriate Bootstrap badge class for the payment status."""
        status_classes = {
            self.PAYMENT_PENDING: 'bg-secondary',
            self.PAYMENT_PAID: 'bg-success',
            self.PAYMENT_REFUNDED: 'bg-danger',
            self.PAYMENT_DISPUTED: 'bg-warning text-dark',
        }
        return status_classes.get(self.payment_status, 'bg-secondary')
        
    def get_latest_delivery(self):
        """Get the most recent delivery for this order."""
        return self.deliveries.order_by('-uploaded_at').first()
        
    @property
    def is_overdue(self):
        """Check if the order is past its deadline."""
        if not self.deadline:
            return False
        return timezone.now() > self.deadline and self.status not in [
            self.STATUS_APPROVED,
            self.STATUS_CANCELLED
        ]
        
    def can_request_revision(self, user):
        """Check if the given user can request a revision."""
        return (
            user == self.client and
            self.status == self.STATUS_DELIVERED and
            self.revision_count < self.max_revisions
        )
        
    def can_approve(self, user):
        """Check if the given user can approve this order."""
        return user == self.client and self.status == self.STATUS_DELIVERED
        
    def can_deliver(self, user):
        """Check if the given user can deliver work for this order."""
        return (
            user == self.freelancer and 
            self.status in [self.STATUS_IN_PROGRESS, self.STATUS_REVISION_REQUESTED]
        )
        
    # Review-related methods
    def can_be_reviewed_by(self, user):
        """Check if the order can be reviewed by the given user."""
        # Allow reviews for both approved and completed orders
        if self.status not in [self.STATUS_APPROVED, self.STATUS_COMPLETED]:
            return False
            
        # Client can leave a review if they haven't already
        if user == self.client:
            return not hasattr(self, 'review')
        # Freelancer can leave a review if they haven't already
        elif user == self.freelancer:
            return not hasattr(self, 'freelancer_review')
        return False
        
    @property
    def can_be_reviewed(self):
        """Check if the order can be reviewed by the current user."""
        from django.contrib.auth import get_user
        from django.utils.functional import SimpleLazyObject
        
        # If we don't have a request context, we can't determine the user
        if not hasattr(self, '_request'):
            return False
            
        user = get_user(self._request)
        if not user.is_authenticated:
            return False
            
        return self.can_be_reviewed_by(user)
        
    def get_review_from(self, user):
        """Get the review left by a specific user."""
        from apps.orders.models import OrderReview
        try:
            return OrderReview.objects.get(order=self, reviewer=user)
        except OrderReview.DoesNotExist:
            return None
            
    def get_reviews(self):
        """Get all reviews for this order."""
        from apps.orders.models import OrderReview
        return OrderReview.objects.filter(order=self)
        
    def get_average_rating(self):
        """Calculate the average rating from all reviews."""
        from django.db.models import Avg
        from apps.orders.models import OrderReview
        
        result = OrderReview.objects.filter(order=self).aggregate(Avg('rating'))
        return result['rating__avg'] or 0
        
    def mark_completed(self, save=True):
        """Mark the order as completed."""
        if self.status not in [self.STATUS_APPROVED, self.STATUS_DELIVERED, self.STATUS_IN_PROGRESS]:
            raise ValueError(f"Cannot complete order from status: {self.status}")
            
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        
        # If not already set, set approved_at to now for backward compatibility
        if not self.approved_at:
            self.approved_at = timezone.now()
        
        if save:
            self.save(update_fields=[
                'status', 
                'completed_at', 
                'approved_at',
                'updated_at'
            ])
            
        return True


class OrderDelivery(models.Model):
    """File(s) or message delivered by freelancer for an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deliveries')
    file = models.FileField(upload_to='order_deliveries/%Y/%m/%d/', blank=True, null=True)
    message = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Delivery for order #{self.order_id} on {self.uploaded_at:%Y-%m-%d}"  

class ProposalAttachment(models.Model):
    """
    Model for storing files attached to job proposals.
    """
    proposal = models.ForeignKey(
        JobProposal,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='proposal_attachments/%Y/%m/%d/',
        max_length=255,
        help_text="Upload a file related to your proposal"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes",
        default=0
    )
    file_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(
        blank=True,
        help_text="Optional description for the file"
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Proposal Attachment'
        verbose_name_plural = 'Proposal Attachments'

    def __str__(self):
        return f"{self.original_filename or 'Untitled'} - {self.proposal}"
    
    def save(self, *args, **kwargs):
        """
        Save the file with additional metadata.
        """
        if not self.original_filename and hasattr(self.file, 'name'):
            self.original_filename = os.path.basename(self.file.name)
        
        if self.file:
            if hasattr(self.file, 'size') and self.file.size:
                self.file_size = self.file.size
            
            name, ext = os.path.splitext(self.file.name)
            self.file_type = ext.lower().lstrip('.')
            
        super().save(*args, **kwargs)
    
    @property
    def filename(self):
        """Return the original filename."""
        return self.original_filename or os.path.basename(self.file.name)
    
    @property
    def filesize_formatted(self):
        """Return file size in human readable format."""
        return format_file_size(self.file_size)
    
    @property
    def extension(self):
        """Return the file extension in lowercase without the dot."""
        _, ext = os.path.splitext(self.filename)
        return ext.lower().lstrip('.')
    
    @property
    def get_file_icon(self):
        """Get the appropriate icon class for this file type."""
        return get_file_icon(self.filename)
    
    @property
    def get_file_type_display(self):
        """Get a human-readable description of the file type."""
        return get_file_type_display(self.filename)
    
    @property
    def is_image(self):
        """Check if the file is an image."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        return self.extension in image_extensions
    
    @property
    def is_document(self):
        """Check if the file is a document."""
        doc_extensions = {'.pdf', '.doc', '.docx', '.odt', '.rtf', '.txt'}
        return self.extension in doc_extensions
    
    @property
    def is_spreadsheet(self):
        """Check if the file is a spreadsheet."""
        ss_extensions = {'.xls', '.xlsx', '.ods', '.csv'}
        return self.extension in ss_extensions
    
    @property
    def is_presentation(self):
        """Check if the file is a presentation."""
        pres_extensions = {'.ppt', '.pptx', '.odp'}
        return self.extension in pres_extensions
    
    @property
    def is_archive(self):
        """Check if the file is an archive."""
        archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz'}
        return self.extension in archive_extensions
    
    @property
    def preview_url(self):
        """
        Return a URL for previewing the file if it's an image,
        otherwise return None.
        """
        if self.is_image and hasattr(self.file, 'url'):
            return self.file.url
        return None
    
    @classmethod
    def get_allowed_extensions(cls):
        """Return a list of allowed file extensions."""
        return sorted([ext for ext in FileValidator.ALLOWED_EXTENSIONS])
