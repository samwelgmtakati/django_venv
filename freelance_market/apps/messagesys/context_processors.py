from .models import Message

def unread_messages_count(request):
    """
    Adds the count of unread messages to the template context.
    Only adds the count if the user is authenticated.
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return {
            'unread_messages_count': Message.objects.filter(
                recipient=request.user,
                read_at__isnull=True
            ).count()
        }
    return {'unread_messages_count': 0}
