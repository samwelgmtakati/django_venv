from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import PaymentMethod, Transaction, WithdrawalRequest, Invoice


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)
    ordering = ('name',)


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('transaction_link', 'amount', 'status', 'created_at')
    fields = ('transaction_link', 'amount', 'status', 'created_at')
    
    def transaction_link(self, obj):
        url = reverse('admin:payments_transaction_change', args=[obj.id])
        return mark_safe(f'<a href="{url}">{obj.reference}</a>')
    transaction_link.short_description = 'Transaction'
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user_email', 'amount_currency', 'transaction_type', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('reference', 'user__email', 'description')
    readonly_fields = ('created_at', 'updated_at', 'processed_at')
    list_select_related = ('user',)
    date_hierarchy = 'created_at'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def amount_currency(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_currency.short_description = 'Amount'
    amount_currency.admin_order_field = 'amount'


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user_email', 'amount_currency', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('reference', 'user__email', 'account_number', 'account_name')
    readonly_fields = ('created_at', 'updated_at', 'processed_at')
    list_select_related = ('user', 'payment_method')
    date_hierarchy = 'created_at'
    actions = ['approve_selected', 'reject_selected', 'mark_as_processed']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def amount_currency(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_currency.short_description = 'Amount'
    amount_currency.admin_order_field = 'amount'
    
    def approve_selected(self, request, queryset):
        updated = queryset.filter(status=WithdrawalRequest.STATUS_PENDING).update(
            status=WithdrawalRequest.STATUS_APPROVED,
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated} withdrawal requests approved.")
    approve_selected.short_description = "Approve selected withdrawal requests"
    
    def reject_selected(self, request, queryset):
        updated = queryset.filter(status=WithdrawalRequest.STATUS_PENDING).update(
            status=WithdrawalRequest.STATUS_REJECTED,
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated} withdrawal requests rejected.")
    reject_selected.short_description = "Reject selected withdrawal requests"
    
    def mark_as_processed(self, request, queryset):
        updated = queryset.filter(status=WithdrawalRequest.STATUS_APPROVED).update(
            status=WithdrawalRequest.STATUS_PROCESSED,
            processed_by=request.user,
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated} withdrawal requests marked as processed.")
    mark_as_processed.short_description = "Mark selected as processed"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user_email', 'amount_currency', 'status', 'due_date', 'paid_date')
    list_filter = ('status', 'due_date')
    search_fields = ('invoice_number', 'user__email', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'paid_date')
    list_select_related = ('user', 'transaction')
    date_hierarchy = 'created_at'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def amount_currency(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_currency.short_description = 'Amount'
    amount_currency.admin_order_field = 'amount'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'transaction')
