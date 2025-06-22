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


def project_counts_processor(request):
    """
    Context processor that adds project counts to the template context.
    Only adds counts for authenticated clients.
    """
    from apps.jobs.models import Job
    
    context = {}
    
    if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'is_client') and request.user.is_client:
        jobs = Job.objects.filter(client=request.user)
        
        context.update({
            'total_projects': jobs.count(),
            'active_projects': jobs.filter(status__in=['open', 'in_progress']).count(),
            'completed_projects': jobs.filter(status='completed').count(),
            'draft_projects': jobs.filter(status='draft').count(),
        })
    
    return context
