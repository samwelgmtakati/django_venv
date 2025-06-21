from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()

class PaymentMethod(models.Model):
    """Stores user's payment methods"""
    AZAMPESA = 'azampesa'
    MPESA = 'mpesa'  # Changed from MTN to MPESA
    TIGOPESA = 'tigopesa'
    HALOPESA = 'halopesa'
    BANK = 'bank'
    
    PAYMENT_METHOD_CHOICES = [
        (AZAMPESA, 'AzamPesa'),
        (MPESA, 'MPESA'),  # Updated display name
        (TIGOPESA, 'Tigo Pesa'),
        (HALOPESA, 'HaloPesa'),
        (BANK, 'Bank Transfer'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods', null=True, blank=True)
    name = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='azampesa')
    account_number = models.CharField(max_length=50, blank=True, default='')
    account_name = models.CharField(max_length=100, blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    branch_code = models.CharField(max_length=20, blank=True, null=True)
    swift_code = models.CharField(max_length=20, blank=True, null=True)
    iban = models.CharField(max_length=50, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_name_display()} - {self.account_number}"
    
    class Meta:
        ordering = ['-is_primary', '-created_at']
        unique_together = ['user', 'name', 'account_number']
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def save(self, *args, **kwargs):
        # Ensure only one primary payment method per user
        if self.is_primary:
            PaymentMethod.objects.filter(
                user=self.user, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """Tracks all financial transactions in the system"""
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]
    
    TYPE_DEPOSIT = 'deposit'
    TYPE_WITHDRAWAL = 'withdrawal'
    TYPE_PAYMENT = 'payment'
    TYPE_REFUND = 'refund'
    
    TYPE_CHOICES = [
        (TYPE_DEPOSIT, 'Deposit'),
        (TYPE_WITHDRAWAL, 'Withdrawal'),
        (TYPE_PAYMENT, 'Payment'),
        (TYPE_REFUND, 'Refund'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='TZS')
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    reference = models.CharField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.currency} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"TXN-{timezone.now().strftime('%Y%m%d')}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)
    
    def mark_as_completed(self, save=True):
        self.status = self.STATUS_COMPLETED
        self.processed_at = timezone.now()
        if save:
            self.save()
    
    def mark_as_failed(self, save=True):
        self.status = self.STATUS_FAILED
        self.processed_at = timezone.now()
        if save:
            self.save()


class WithdrawalRequest(models.Model):
    """Tracks withdrawal requests from freelancers"""
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_PROCESSED = 'processed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_PROCESSED, 'Processed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('10000.00'))])
    currency = models.CharField(max_length=3, default='TZS')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reference = models.CharField(max_length=100, unique=True, blank=True)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_withdrawals')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Withdrawal Request'
        verbose_name_plural = 'Withdrawal Requests'
    
    def __str__(self):
        return f"Withdrawal - {self.amount} {self.currency} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"WDR-{timezone.now().strftime('%Y%m%d')}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)
    
    def approve(self, user):
        self.status = self.STATUS_APPROVED
        self.processed_by = user
        self.processed_at = timezone.now()
        self.save()
    
    def reject(self, user, reason=''):
        self.status = self.STATUS_REJECTED
        self.processed_by = user
        self.processed_at = timezone.now()
        self.notes = f"{self.notes}\nRejection Reason: {reason}" if self.notes else f"Rejection Reason: {reason}"
        self.save()
    
    def mark_as_processed(self, user):
        self.status = self.STATUS_PROCESSED
        self.processed_by = user
        self.processed_at = timezone.now()
        self.save()


class Invoice(models.Model):
    """Stores invoice information for payments"""
    STATUS_PAID = 'paid'
    STATUS_PENDING = 'pending'
    STATUS_OVERDUE = 'overdue'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PAID, 'Paid'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='invoices')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='TZS')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"INV-{self.invoice_number} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m')}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)
    
    def mark_as_paid(self, transaction=None):
        self.status = self.STATUS_PAID
        self.paid_date = timezone.now().date()
        if transaction:
            self.transaction = transaction
        self.save()
    
    def is_overdue(self):
        return self.status == self.STATUS_PENDING and timezone.now().date() > self.due_date


# Signal handlers and other utility functions would go here
