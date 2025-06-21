from django import template
from django.db.models import Q
from ..models import Message

register = template.Library()

@register.simple_tag(takes_context=True)
def unread_messages_count(context):
    """
    Returns the count of unread messages for the current user.
    Usage: {% unread_messages_count as count %}
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return 0
    
    return Message.objects.filter(
        recipient=request.user,
        read_at__isnull=True
    ).count()

@register.inclusion_tag('messages/nav_message_count.html', takes_context=True)
def nav_message_count(context):
    """
    Renders the message count badge for the navigation bar.
    Usage: {% nav_message_count %}
    """
    request = context.get('request')
    count = 0
    
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        count = Message.objects.filter(
            recipient=request.user,
            read_at__isnull=True
        ).count()
    
    return {'unread_count': count}
