from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_freelancers_list(request):
    """
    Admin view to list all freelancers
    """
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Get all freelancers with their stats
    freelancers = User.objects.filter(
        is_freelancer=True
    ).select_related('freelancer_profile').annotate(
        total_jobs=Count('assigned_jobs', distinct=True),
        completed_jobs=Count('assigned_jobs', filter=Q(assigned_jobs__status='completed'), distinct=True),
        active_jobs=Count('assigned_jobs', filter=Q(assigned_jobs__status='in_progress'), distinct=True)
    ).order_by('-date_joined')
    
    # Apply search if query exists
    if search_query:
        freelancers = freelancers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(freelancers, 20)  # Show 20 freelancers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_freelancers': freelancers.count(),
    }
    return render(request, 'dashboard/admin/freelancers_list.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_clients_list(request):
    """
    Admin view to list all clients
    """
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Get all clients with their stats
    clients = User.objects.filter(
        is_client=True
    ).select_related('profile').annotate(
        total_jobs_posted=Count('posted_jobs', distinct=True),
        active_jobs=Count('posted_jobs', filter=Q(posted_jobs__status='in_progress'), distinct=True),
        completed_jobs=Count('posted_jobs', filter=Q(posted_jobs__status='completed'), distinct=True)
    ).order_by('-date_joined')
    
    # Apply search if query exists
    if search_query:
        clients = clients.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(clients, 20)  # Show 20 clients per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_clients': clients.count(),
    }
    return render(request, 'dashboard/admin/clients_list.html', context)
