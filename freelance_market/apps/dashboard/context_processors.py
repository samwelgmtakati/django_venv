def profile_picture_processor(request):
    """
    Context processor that adds the user's profile picture URL to the template context.
    Handles cases where the profile picture might not be set.
    Also includes debug information if in development.
    """
    from django.conf import settings
    
    context = {
        'debug': settings.DEBUG,
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        context['has_profile_picture'] = False
        if hasattr(request.user, 'profile_picture'):
            try:
                if request.user.profile_picture:
                    context['profile_picture_url'] = request.user.profile_picture.url
                    context['has_profile_picture'] = True
            except (ValueError, AttributeError):
                pass
    return context
