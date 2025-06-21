from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for the Notification model."""
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'read_at')
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'title', 'message', 'notification_type', 'url')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )
