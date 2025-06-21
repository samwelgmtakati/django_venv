from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.jobs.models import Order, OrderDelivery
from .models import OrderReview


@admin.register(OrderReview)
class OrderReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_order_id', 'get_reviewer', 'get_user_reviewed', 'rating_stars', 'created_at')
    list_filter = ('is_client_review', 'rating', 'created_at')
    search_fields = (
        'order__id',
        'reviewer__username',
        'reviewer__email',
        'user_being_reviewed__username',
        'user_being_reviewed__email',
        'comment'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('order', 'reviewer', 'user_being_reviewed', 'is_client_review')
        }),
        (_('Review Details'), {
            'fields': ('rating', 'comment')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_order_id(self, obj):
        return f"Order #{obj.order.id}"
    get_order_id.short_description = _('Order')
    get_order_id.admin_order_field = 'order__id'
    
    def get_reviewer(self, obj):
        return obj.reviewer.get_full_name() or obj.reviewer.username
    get_reviewer.short_description = _('Reviewer')
    get_reviewer.admin_order_field = 'reviewer__username'
    
    def get_user_reviewed(self, obj):
        return obj.user_being_reviewed.get_full_name() or obj.user_being_reviewed.username
    get_user_reviewed.short_description = _('User Reviewed')
    get_user_reviewed.admin_order_field = 'user_being_reviewed__username'
    
    def rating_stars(self, obj):
        return format_html(
            '<span style="color: #f39c12; font-size: 1.2em;">{}</span>',
            '★' * obj.rating + '☆' * (5 - obj.rating)
        )
    rating_stars.short_description = _('Rating')
    rating_stars.admin_order_field = 'rating'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "client", "freelancer", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("job__title", "client__username", "freelancer__username")

@admin.register(OrderDelivery)
class OrderDeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("order__id",)

