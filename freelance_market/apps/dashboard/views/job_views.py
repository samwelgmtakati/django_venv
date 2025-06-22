from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from apps.jobs.models import Job

@login_required
def job_detail(request, slug):
    """
    View for displaying job details in the dashboard.
    """
    job = get_object_or_404(Job, slug=slug, status='published')
    context = {
        'job': job,
        'title': f'{job.title} - Job Details'
    }
    return render(request, 'dashboard/job_detail.html', context)
