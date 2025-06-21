from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Thread, Message


class MessageInline(admin.StackedInline):
    model = Message
    extra = 0
    fields = ('sender', 'recipient', 'body', 'sent_at', 'read_at')
    readonly_fields = ('sent_at',)
    show_change_link = True


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'participants_list', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('subject', 'participants__username', 'participants__email')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]
    date_hierarchy = 'created_at'
    
    def participants_list(self, obj):
        return ", ".join([p.get_full_name() or p.username for p in obj.participants.all()])
    participants_list.short_description = _('Participants')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'sender', 'recipient', 'sent_at', 'is_read')
    list_filter = ('sent_at', 'read_at', 'sender', 'recipient')
    search_fields = ('body', 'sender__username', 'recipient__username')
    readonly_fields = ('sent_at',)
    date_hierarchy = 'sent_at'
    
    def is_read(self, obj):
        return obj.read_at is not None
    is_read.boolean = True
    is_read.short_description = _('Read')
