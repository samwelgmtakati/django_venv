from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Count, Avg, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import connection, transaction, models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from collections import Counter
from django.contrib.auth import get_user_model
import json

from apps.accounts.models import User
from apps.jobs.models import Job, JobCategory, JobProposal, JobProposal
from apps.freelancer.models import Freelancer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import CustomUserCreationForm
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

User = get_user_model()

@csrf_protect
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect based on user type
                if user.is_client:
                    return redirect('client:dashboard')
                elif user.is_freelancer:
                    return redirect('freelancer:dashboard')
                else:
                    # Default redirect for users without a specific role
                    return redirect('dashboard:home')
            else:
                messages.error(request, 'Your account is inactive. Please contact support.')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            
    # If not POST or authentication failed, show the login form
    return render(request, 'registration/login.html')

def is_client(user):
    return hasattr(user, 'is_client') and user.is_client

def is_freelancer(user):
    return hasattr(user, 'is_freelancer') and user.is_freelancer

def register(request):
    """
    Handle user registration with client/freelancer account type selection.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Save the user with the selected role
                user = form.save(commit=False)
                user_type = form.cleaned_data.get('user_type')
                user.is_active = True  # Activate the user by default
                
                if user_type == 'client':
                    user.is_client = True
                    user.is_freelancer = False
                elif user_type == 'freelancer':
                    user.is_freelancer = True
                    user.is_client = False
                
                user.save()
                
                # Send success message
                messages.success(
                    request,
                    'Registration successful! Please log in with your credentials.'
                )
                
                # Redirect to login page
                return redirect('login')
                
            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error during registration: {str(e)}")
                
                # Add a user-friendly error message
                messages.error(
                    request,
                    'An error occurred during registration. Please try again.'
                )
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def admin_dashboard(request):
    """
    Admin dashboard view with admin-specific statistics and actions.
    """
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from datetime import timedelta
    from django.apps import apps
    from django.db.models import Count, Q
    
    User = get_user_model()
    context = {}
    
    # Get statistics
    now = timezone.now()
    last_week = now - timedelta(days=7)
    
    # Get all users with their counts and recent activity
    users = User.objects.all()
    
    # Get freelancers with additional data
    freelancers = User.objects.filter(
        is_freelancer=True
    ).select_related('freelancer').annotate(
        total_jobs=Count('assigned_jobs', distinct=True),
        completed_jobs=Count('assigned_jobs', filter=Q(assigned_jobs__status='completed'), distinct=True),
        active_jobs=Count('assigned_jobs', filter=Q(assigned_jobs__status='in_progress'), distinct=True)
    ).order_by('-date_joined')
    
    # Get clients with additional data
    clients = User.objects.filter(
        is_client=True
    ).select_related('profile').annotate(
        total_jobs_posted=Count('posted_jobs', distinct=True),
        active_jobs=Count('posted_jobs', filter=Q(posted_jobs__status='in_progress'), distinct=True),
        completed_jobs=Count('posted_jobs', filter=Q(posted_jobs__status='completed'), distinct=True)
    ).order_by('-date_joined')
    
    # User statistics
    context.update({
        'total_users': users.count(),
        'new_users_this_week': users.filter(date_joined__gte=last_week).count(),
        'clients_count': clients.count(),
        'freelancers_count': freelancers.count(),
        'freelancers': freelancers[:10],  # Show latest 10 freelancers
        'clients': clients[:10],          # Show latest 10 clients
        'freelancers_total_count': freelancers.count(),  # Total count for the dashboard cards
        'clients_total_count': clients.count(),          # Total count for the dashboard cards
    })
    
    # Initialize job-related statistics with default values
    job_stats = {
        'active_projects_count': 0,
        'completed_projects_count': 0,
        'total_jobs': 0,
    }
    
    # Try to get job data if available
    try:
        # First try to get Job model from jobs app
        try:
            Job = apps.get_model('jobs', 'Job')
            if hasattr(Job, 'objects'):
                job_stats.update({
                    'active_projects_count': Job.objects.filter(status='in_progress').count(),
                    'completed_projects_count': Job.objects.filter(status='completed').count(),
                    'total_jobs': Job.objects.count(),
                })
                
                # Add recent jobs to activity
                recent_activity = []
                recent_jobs = Job.objects.order_by('-created_at')[:5]
                for job in recent_jobs:
                    recent_activity.append({
                        'title': f'New job posted: {getattr(job, "title", "Untitled")}',
                        'description': f'Budget: TZS {getattr(job, "budget", "N/A")}',
                        'user': getattr(job, 'posted_by', None),
                        'timestamp': getattr(job, 'created_at', now),
                        'type': 'job_posted'
                    })
                context['recent_activity'] = recent_activity
                
        except LookupError:
            # If Job model doesn't exist in jobs app, try other possible model names
            try:
                # Try getting Project model if it exists
                Project = apps.get_model('projects', 'Project')
                if hasattr(Project, 'objects'):
                    job_stats.update({
                        'active_projects_count': Project.objects.filter(status='in_progress').count(),
                        'completed_projects_count': Project.objects.filter(status='completed').count(),
                        'total_jobs': Project.objects.count(),
                    })
                    
                    # Add recent projects to activity
                    recent_activity = []
                    recent_projects = Project.objects.order_by('-created_at')[:5]
                    for project in recent_projects:
                        recent_activity.append({
                            'title': f'New project: {getattr(project, "title", "Untitled")}',
                            'description': f'Status: {getattr(project, "status", "N/A")}',
                            'user': getattr(project, 'owner', None),
                            'timestamp': getattr(project, 'created_at', now),
                            'type': 'project_created'
                        })
                    context['recent_activity'] = recent_activity
                    
            except LookupError:
                # If neither Job nor Project model exists, use defaults (0)
                pass
                
    except Exception as e:
        # Log the error but don't crash the dashboard
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching job statistics: {str(e)}")
    
    context.update(job_stats)
    
    # Initialize financial statistics with default values
    financial_stats = {
        'total_revenue': 0,
        'weekly_revenue': 0,
    }
    
    # Try to get financial data if available
    try:
        # First try to get Order model from orders app
        try:
            Order = apps.get_model('orders', 'Order')
            if hasattr(Order, 'objects'):
                from django.db.models import Sum
                financial_stats.update({
                    'total_revenue': Order.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
                    'weekly_revenue': Order.objects.filter(
                        created_at__gte=last_week
                    ).aggregate(Sum('amount'))['amount__sum'] or 0,
                })
        except LookupError:
            # If Order model doesn't exist in orders app, try other possible model names
            try:
                # Try getting Transaction model if it exists
                Transaction = apps.get_model('payments', 'Transaction')
                if hasattr(Transaction, 'objects'):
                    from django.db.models import Sum
                    financial_stats.update({
                        'total_revenue': Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
                        'weekly_revenue': Transaction.objects.filter(
                            created_at__gte=last_week
                        ).aggregate(Sum('amount'))['amount__sum'] or 0,
                    })
            except LookupError:
                # If neither Order nor Transaction model exists, use defaults (0)
                pass
    except Exception as e:
        # Log the error but don't crash the dashboard
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching financial statistics: {str(e)}")
    
    context.update(financial_stats)
    
    # Add active page and admin URLs to context
    context.update({
        'active_page': 'admin_dashboard',
        'admin_urls': {
            'index': '/admin/',
            'user_add': '/admin/accounts/user/add/',
            'user_changelist': '/admin/accounts/user/',
            'userprofile_changelist': '/admin/accounts/userprofile/',
            'freelancer_changelist': '/admin/freelancer/freelancer/',
            'skill_changelist': '/admin/freelancer/skill/'
        },
        'INSTALLED_APPS': settings.INSTALLED_APPS
    })
    
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def dashboard_home(request):
    """
    Renders the appropriate dashboard based on user role.
    """
    # Redirect admin users to admin dashboard
    if request.user.is_admin:
        return redirect('dashboard:admin_dashboard')
        
    if request.user.is_client:
        return redirect('dashboard:client_dashboard')
    elif request.user.is_freelancer:
        return redirect('dashboard:freelancer_dashboard')
    
    # Default dashboard for users without a specific role
    profile_pic_url = None
    if hasattr(request.user, 'profile_picture'):
        try:
            if request.user.profile_picture:
                profile_pic_url = request.user.profile_picture.url
        except (ValueError, AttributeError):
            pass
    
    context = {
        'title': 'Dashboard',
        'active_page': 'dashboard',
        'profile_pic_url': profile_pic_url
    }
    return render(request, 'dashboard/home.html', context)

@login_required
@user_passes_test(is_client, login_url='dashboard:home')
def client_dashboard(request):
    """
    Client-specific dashboard view.
    """
    from apps.jobs.models import JobProposal
    
    # Get the client's jobs, ordered by creation date (newest first)
    jobs = Job.objects.filter(client=request.user).order_by('-created_at')
    
    # Count jobs by status
    active_jobs = jobs.filter(status='open').count()  # Changed from 'in_progress' to 'open'
    draft_jobs = jobs.filter(status='draft').count()
    completed_jobs = jobs.filter(status='completed').count()
    
    # Get recent proposals for the client's jobs
    recent_proposals = (
        JobProposal.objects
        .filter(job__in=jobs)
        .select_related('job', 'freelancer', 'freelancer__freelancer_profile')
        .order_by('-created_at')[:5]
    )
    
    # Prepare job data for the template
    jobs_data = []
    for job in jobs[:5]:  # Only get the 5 most recent jobs
        jobs_data.append({
            'id': job.id,
            'title': job.title,
            'slug': job.slug,  # Add slug field for URL generation
            'status': job.status,
            'created_at': job.created_at,
            'description': job.description,
            'deadline': job.deadline,
            'get_status_display': job.get_status_display(),
            'get_job_type_display': job.get_job_type_display() if hasattr(job, 'get_job_type_display') else 'N/A',
            'proposals_count': getattr(job, 'proposals_count', 0)
        })
    
    # Get recommended freelancers (top rated freelancers who haven't submitted proposals to the client's jobs)
    from django.db.models import Count, Avg, Case, When, IntegerField
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Get freelancers who have completed jobs
    recommended_freelancers = User.objects.filter(
        is_freelancer=True,
        freelancer_profile__isnull=False
    ).annotate(
        completed_jobs=Count(
            Case(
                When(assigned_jobs__status='completed', then=1),
                output_field=IntegerField(),
            )
        ),
        avg_rating=Avg('freelancer_reviews__rating')
    ).filter(
        completed_jobs__gt=0,  # Only include freelancers with completed jobs
        freelancer_profile__skills__isnull=False  # Only include freelancers with skills
    ).exclude(
        id__in=jobs.values('proposals__freelancer')  # Exclude those who already applied
    ).order_by(
        '-avg_rating',
        '-completed_jobs'
    )[:3]  # Limit to 3 recommendations
    
    # Prepare freelancer data for the template
    freelancers_data = []
    for freelancer in recommended_freelancers:
        freelancers_data.append({
            'id': freelancer.id,
            'full_name': freelancer.get_full_name() or freelancer.username,
            'title': getattr(freelancer.freelancer_profile, 'title', 'Freelancer'),
            'skills': list(freelancer.freelancer_profile.skills.all().values_list('name', flat=True)[:3]),
            'avg_rating': freelancer.avg_rating or 0,
            'completed_jobs': freelancer.completed_jobs,
            'profile_picture': freelancer.freelancer_profile.profile_picture.url if hasattr(freelancer.freelancer_profile, 'profile_picture') and freelancer.freelancer_profile.profile_picture else None
        })
    
    context = {
        'active_tab': 'dashboard',
        'jobs': jobs_data,  # Pass the prepared job data
        'total_jobs': jobs.count(),
        'active_jobs': active_jobs,
        'draft_jobs': draft_jobs,
        'completed_jobs': completed_jobs,
        'recent_proposals': recent_proposals,
        'recommended_freelancers': freelancers_data,
    }
    return render(request, 'dashboard/client_dashboard.html', context)

@login_required
@user_passes_test(is_freelancer, login_url='dashboard:home')
def freelancer_profile(request):
    """
    Freelancer profile view showing freelancer's information and statistics.
    """
    if not hasattr(request.user, 'is_freelancer') or not request.user.is_freelancer:
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('dashboard:home')
    
    # Get freelancer's completed jobs
    from apps.jobs.models import Job
    completed_jobs = Job.objects.filter(
        proposals__freelancer=request.user,
        status='completed'
    ).distinct()
    
    # Get freelancer's active jobs
    active_jobs = Job.objects.filter(
        proposals__freelancer=request.user,
        status__in=['in_progress', 'active']
    ).distinct()
    
    # Get freelancer's reviews
    from apps.reviews.models import Review
    reviews_received = Review.objects.filter(
        user_being_reviewed=request.user
    ).select_related('reviewer').order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews_received.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
    
    # Get freelancer's skills if they exist
    skills = []
    if hasattr(request.user, 'freelancer'):
        skills = request.user.freelancer.skills.all()
    
    context = {
        'active_tab': 'profile',
        'completed_jobs_count': completed_jobs.count(),
        'active_jobs_count': active_jobs.count(),
        'reviews_received': reviews_received,
        'avg_rating': avg_rating if avg_rating is not None else 0,
        'total_reviews': reviews_received.count(),
        'skills': skills,
    }
    return render(request, 'dashboard/freelancer_profile.html', context)

@login_required
@user_passes_test(is_freelancer, login_url='dashboard:home')
def freelancer_dashboard(request):
    """
    Freelancer-specific dashboard view with services and statistics.
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'is_freelancer') or not request.user.is_freelancer:
        messages.warning(request, 'You do not have permission to access the freelancer dashboard.')
        return redirect('home:home')
    
    # Import here to avoid circular imports
    from apps.services.models import Service
    from apps.jobs.models import JobProposal, Job
    from django.db.models import Count, Q
    
    # Get services data
    services = Service.objects.filter(
        freelancer=request.user,
        is_active=True
    ).order_by('-created_at')[:3]
    
    # Get proposals data
    proposals = JobProposal.objects.filter(
        freelancer=request.user
    ).select_related('job').order_by('-created_at')[:5]
    
    # Get jobs data
    active_jobs = Job.objects.filter(
        proposals__freelancer=request.user,
        status__in=['in_progress', 'active']
    ).distinct()
    
    completed_jobs = Job.objects.filter(
        proposals__freelancer=request.user,
        status='completed'
    ).distinct()
    
    # Get recommended jobs (jobs in the same categories as freelancer's skills)
    recommended_jobs = Job.objects.filter(
        status='published'  # Using 'published' status instead of is_active
    )
    
    # Add category filter if freelancer has skills
    if hasattr(request.user, 'freelancer') and request.user.freelancer.skills.exists():
        recommended_jobs = recommended_jobs.filter(
            category__in=request.user.freelancer.skills.all()
        )
    
    recommended_jobs = recommended_jobs.exclude(
        proposals__freelancer=request.user
    ).distinct()[:3]
    
    # Get freelancer's skills if they exist
    try:
        freelancer = request.user.freelancer
        skills = freelancer.skills.all() if hasattr(freelancer, 'skills') else []
    except Exception as e:
        skills = []
        print(f"Error getting freelancer skills: {e}")
    
    context = {
        'active_page': 'dashboard',
        'services': services,
        'services_count': services.count(),
        'total_services': Service.objects.filter(freelancer=request.user).count(),
        'total_proposals': JobProposal.objects.filter(freelancer=request.user).count(),
        'active_proposals': JobProposal.objects.filter(
            freelancer=request.user,
            status__in=['pending', 'accepted']
        ).count(),
        'active_jobs': active_jobs.count(),
        'completed_jobs': completed_jobs.count(),
        'proposals': proposals,
        'recommended_jobs': recommended_jobs,
        'skills': skills,  # Add skills to the context
    }
    return render(request, 'dashboard/freelancer_dashboard.html', context)

def user_roles(request):
    """
    Context processor to add user role information to all templates.
    """
    if request.user.is_authenticated:
        return {
            'is_client': request.user.is_client,
            'is_freelancer': request.user.is_freelancer,
        }
    return {}

from django.shortcuts import render, redirect
from django.contrib import messages
from apps.jobs.models import Job, JobCategory
from django.utils.text import slugify
from django.utils import timezone

@login_required
@user_passes_test(is_client)
def post_job(request):
    """
    View for clients to post a new job
    """
    from apps.jobs.models import Job, JobCategory
    from datetime import date
    from django.http import JsonResponse, HttpResponseBadRequest
    from django.urls import reverse
    import json
    import logging
    import uuid
    
    # Set up logging
    logger = logging.getLogger(__name__)
    logger.info("post_job view called")
    
    # Get categories for the form
    categories = JobCategory.objects.all()
    
    # Handle GET requests - show the form
    if request.method != 'POST':
        context = {
            'categories': categories,
            'today': date.today(),
            'form_token': str(uuid.uuid4())  # Generate a new token for each form load
        }
        return render(request, 'dashboard/post_job.html', context)
    
    # Handle POST requests - process the form
    try:
        # Get form data based on content type
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        else:
            data = request.POST.dict()
        
        logger.info(f"Processing job submission. Data: {data}")
        
        # Check if this is a publish action
        is_publish = 'publish' in data or 'publish' in request.POST
        status = 'published' if is_publish else 'draft'
        logger.info(f"Setting job status to: {status}")
        
        # Check for existing similar job to prevent duplicates
        job_data = {
            'title': data.get('jobTitle'),
            'description': data.get('jobDescription'),
            'requirements': data.get('jobRequirements', ''),
            'client': request.user,
            'status': status,
            'budget': data.get('jobBudget') or None,
            'deadline': data.get('jobDeadline') or None,
            'published_at': timezone.now() if is_publish else None
        }
        
        # Set category if selected
        category_id = data.get('jobCategory')
        if category_id:
            logger.info(f"Setting category: {category_id}")
            job_data['category_id'] = category_id
        
        # Use get_or_create to prevent duplicates based on title and client
        job, created = Job.objects.get_or_create(
            title=job_data['title'],
            client=request.user,
            defaults=job_data
        )
        
        if not created:
            logger.warning(f"Duplicate job detected: {job.title} for user {request.user}")
            # Update existing job with new data
            for key, value in job_data.items():
                setattr(job, key, value)
            job.save()
        
        logger.info(f"Job {'created' if created else 'updated'} successfully with ID: {job.id}")
        
        # Prepare success response
        success_message = 'Job saved as draft successfully!' if status == 'draft' else 'Job published successfully!'
        response_data = {
            'success': True,
            'message': success_message,
            'redirect': reverse('dashboard:client_dashboard')
        }
        
        if request.content_type == 'application/json':
            return JsonResponse(response_data)
            
        messages.success(request, success_message)
        return redirect('dashboard:client_dashboard')
        
    except Exception as e:
        error_msg = f'Error saving job: {str(e)}'
        logger.error(error_msg, exc_info=True)
        
        if request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
            
        messages.error(request, error_msg)
        return render(request, 'dashboard/post_job.html', {
            'categories': categories,
            'today': date.today(),
            'form_data': data if 'data' in locals() else {}
        })

@login_required
def find_work(request):
    """
    View to display all published jobs with filtering and pagination.
    """
    # Get all active jobs (both published and open) ordered by creation date (newest first)
    jobs = Job.objects.filter(
        status__in=['published', 'open']
    ).select_related('client', 'category').order_by('-created_at')
    
    # Get filter parameters
    category_id = request.GET.get('category')
    job_type = request.GET.get('job_type')
    experience = request.GET.get('experience')
    
    # Apply filters
    if category_id and category_id.isdigit():
        jobs = jobs.filter(category_id=category_id)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if experience:
        jobs = jobs.filter(experience_level=experience)
    
    # Pagination - 10 jobs per page
    paginator = Paginator(jobs, 10)
    page = request.GET.get('page')
    
    try:
        jobs_page = paginator.page(page)
    except PageNotAnInteger:
        jobs_page = paginator.page(1)
    except EmptyPage:
        jobs_page = paginator.page(paginator.num_pages)
    
    context = {
        'jobs': jobs_page,
        'categories': JobCategory.objects.all(),
        'job_types': dict(Job.JOB_TYPES),
        'experience_levels': dict(Job.EXPERIENCE_LEVELS),
        'selected_category': category_id,
        'selected_job_type': job_type,
        'selected_experience': experience,
    }
    
    return render(request, 'dashboard/find_work.html', context)

@login_required
def client_profile(request):
    """
    Client profile view showing client's information and statistics.
    """
    if not hasattr(request.user, 'is_client') or not request.user.is_client:
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('dashboard:home')
    
    # Get client's posted jobs using the correct related_name
    posted_jobs = request.user.posted_jobs.all().order_by('-created_at')
    active_jobs = posted_jobs.filter(status='published')
    completed_jobs = posted_jobs.filter(status='completed')
    
    # Get client's reviews
    from apps.reviews.models import Review
    reviews_received = Review.objects.filter(
        user_being_reviewed=request.user
    ).select_related('reviewer').order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews_received.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
    
    context = {
        'active_tab': 'profile',
        'posted_jobs_count': posted_jobs.count(),
        'active_jobs_count': active_jobs.count(),
        'completed_jobs_count': completed_jobs.count(),
        'recent_jobs': posted_jobs[:5],
        'reviews_received': reviews_received,
        'avg_rating': avg_rating if avg_rating is not None else 0,
        'total_reviews': reviews_received.count(),
    }
    return render(request, 'dashboard/client_profile.html', context)

@login_required
def custom_logout(request):
    """
    Logout view that handles both GET and POST requests.
    """
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('home:home_page')
    # For GET requests, redirect to home
    return redirect('home:home_page')

@login_required
def my_projects(request):
    """
    View showing all projects for the current client
    """
    if not hasattr(request.user, 'is_client') or not request.user.is_client:
        return redirect('dashboard:home')
    
    # Get all jobs posted by the current user
    projects = Job.objects.filter(client=request.user).order_by('-created_at')
    
    # Count projects by status
    active_count = projects.filter(status='in_progress').count()
    completed_count = projects.filter(status='completed').count()
    draft_count = projects.filter(status='draft').count()
    total_spent = sum(p.budget for p in projects.filter(status='completed') if p.budget)
    
    context = {
        'active_page': 'my_projects',
        'page_title': 'My Projects',
        'projects': projects,
        'active_count': active_count,
        'completed_count': completed_count,
        'draft_count': draft_count,
        'total_spent': total_spent,
    }
    return render(request, 'dashboard/client/projects/list.html', context)

@login_required
def active_projects(request):
    """
    View showing active projects for the current client
    """
    if not hasattr(request.user, 'is_client') or not request.user.is_client:
        return redirect('dashboard:home')
    
    # Get active projects (in progress)
    projects = Job.objects.filter(
        client=request.user,
        status='in_progress'
    ).order_by('-created_at')
    
    # Count projects by status
    active_count = projects.count()
    completed_count = Job.objects.filter(client=request.user, status='completed').count()
    draft_count = Job.objects.filter(client=request.user, status='draft').count()
    total_spent = sum(p.budget for p in Job.objects.filter(client=request.user, status='completed') if p.budget)
    
    context = {
        'active_page': 'active_projects',
        'page_title': 'Active Projects',
        'projects': projects,
        'active_count': active_count,
        'completed_count': completed_count,
        'draft_count': draft_count,
        'total_spent': total_spent,
    }
    return render(request, 'dashboard/client/projects/list.html', context)

@login_required
def completed_projects(request):
    """
    View showing completed projects for the current client
    """
    if not hasattr(request.user, 'is_client') or not request.user.is_client:
        return redirect('dashboard:home')
    
    # Get completed projects
    projects = Job.objects.filter(
        client=request.user,
        status='completed'
    ).order_by('-created_at')
    
    # Count projects by status
    active_count = Job.objects.filter(client=request.user, status='in_progress').count()
    completed_count = projects.count()
    draft_count = Job.objects.filter(client=request.user, status='draft').count()
    total_spent = sum(p.budget for p in projects if p.budget)
    
    context = {
        'active_page': 'completed_projects',
        'page_title': 'Completed Projects',
        'projects': projects,
        'active_count': active_count,
        'completed_count': completed_count,
        'draft_count': draft_count,
        'total_spent': total_spent,
    }
    return render(request, 'dashboard/client/projects/list.html', context)

@login_required
def draft_projects(request):
    """
    View showing draft projects for the current client
    """
    if not hasattr(request.user, 'is_client') or not request.user.is_client:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:home')
    
    # Get draft jobs for the current client
    jobs = Job.objects.filter(
        client=request.user,
        status='draft'
    ).order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(jobs, 10)  # Show 10 jobs per page
    
    try:
        jobs = paginator.page(page)
    except PageNotAnInteger:
        jobs = paginator.page(1)
    except EmptyPage:
        jobs = paginator.page(paginator.num_pages)
    
    context = {
        'jobs': jobs,
        'active_page': 'draft_projects',
        'title': 'Draft Projects'
    }
    return render(request, 'dashboard/client/project_list.html', context)


@login_required
@login_required
def client_proposals(request):
    """
    View showing all proposals for the current client's jobs
    """
    if not hasattr(request.user, 'is_client') or not request.user.is_client:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:home')
    
    # Get all proposals for the client's jobs
    proposals = JobProposal.objects.filter(
        job__client=request.user
    ).select_related('job', 'freelancer__profile').order_by('-created_at')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        proposals = proposals.filter(status=status_filter)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(proposals, 10)  # Show 10 proposals per page
    
    try:
        proposals = paginator.page(page)
    except PageNotAnInteger:
        proposals = paginator.page(1)
    except EmptyPage:
        proposals = paginator.page(paginator.num_pages)
    
    context = {
        'proposals': proposals,
        'active_page': 'client_proposals',
        'title': 'Job Proposals',
        'status_filter': status_filter,
        'status_choices': dict(JobProposal.STATUS_CHOICES)
    }
    return render(request, 'dashboard/client/proposal_list.html', context)


@require_http_methods(["POST"])
@login_required
def accept_proposal(request, proposal_id):
    """
    View to accept a job proposal
    """
    proposal = get_object_or_404(
        JobProposal.objects.select_related('job', 'freelancer'),
        id=proposal_id,
        job__client=request.user,
        status='pending'  # Only pending proposals can be accepted
    )
    
    with transaction.atomic():
        # Update the proposal status
        proposal.status = 'accepted'
        proposal.save(update_fields=['status', 'updated_at'])
        
        # Update the job status to 'in_progress' and assign the freelancer
        job = proposal.job
        job.status = 'in_progress'
        job.freelancer = proposal.freelancer
        job.save(update_fields=['status', 'freelancer', 'updated_at'])
        
        # Create a notification for the freelancer
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=proposal.freelancer,
            title='Proposal Accepted',
            message=f'Your proposal for "{proposal.job.title}" has been accepted!',
            notification_type='proposal_accepted'
        )
        
        # Reject all other pending proposals for this job
        JobProposal.objects.filter(
            job=proposal.job,
            status='pending'
        ).exclude(
            id=proposal.id
        ).update(
            status='rejected'
        )
        
        messages.success(request, f'Proposal from {proposal.freelancer.get_full_name() or proposal.freelancer.username} has been accepted.')
    
    # Redirect back to the proposals list
    return redirect('dashboard:client_proposals')


@require_http_methods(["POST"])
@login_required
def reject_proposal(request, proposal_id):
    """
    View to reject a job proposal
    """
    proposal = get_object_or_404(
        JobProposal.objects.select_related('job', 'freelancer'),
        id=proposal_id,
        job__client=request.user,
        status='pending'  # Only pending proposals can be rejected
    )
    
    rejection_reason = request.POST.get('rejection_reason', '')
    
    # Update the proposal status
    proposal.status = 'rejected'
    proposal.save(update_fields=['status', 'updated_at'])
    
    # Create a notification for the freelancer
    from apps.notifications.models import Notification
    Notification.objects.create(
        user=proposal.freelancer,
        title='Proposal Rejected',
        message=f'Your proposal for "{proposal.job.title}" has been rejected.' + (f' Reason: {rejection_reason}' if rejection_reason else ''),
        notification_type='proposal_rejected'
    )
    
    messages.success(request, f'Proposal from {proposal.freelancer.get_full_name() or proposal.freelancer.username} has been rejected.')
    
    # Redirect back to the proposals list
    return redirect('dashboard:client_proposals')


@login_required
def freelancer_proposals(request):
    """
    View showing all proposals submitted by the current freelancer
    """
    if not hasattr(request.user, 'is_freelancer') or not request.user.is_freelancer:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:home')
    
    # Get all proposals for the current freelancer
    proposals = JobProposal.objects.filter(
        freelancer=request.user
    ).select_related('job', 'job__client__profile').order_by('-created_at')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        proposals = proposals.filter(status=status_filter)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(proposals, 10)  # Show 10 proposals per page
    
    try:
        proposals = paginator.page(page)
    except PageNotAnInteger:
        proposals = paginator.page(1)
    except EmptyPage:
        proposals = paginator.page(paginator.num_pages)
    
    context = {
        'proposals': proposals,
        'active_page': 'freelancer_proposals',
        'title': 'My Proposals',
        'status_filter': status_filter,
        'status_choices': dict(JobProposal.STATUS_CHOICES)
    }
    return render(request, 'dashboard/freelancer/proposal_list.html', context)


@login_required
def api_proposal_detail(request, proposal_id):
    """
    API endpoint to get proposal details for the modal
    """
    proposal = get_object_or_404(
        JobProposal.objects.select_related('job', 'freelancer__profile'),
        id=proposal_id,
        job__client=request.user  # Only the client can view this
    )
    
    # Prepare proposal details for JSON response
    data = {
        'id': proposal.id,
        'job_title': proposal.job.title,
        'job_id': proposal.job.id,
        'freelancer_name': proposal.freelancer.get_full_name() or proposal.freelancer.username,
        'freelancer_avatar': proposal.freelancer.avatar.url if hasattr(proposal.freelancer, 'avatar') and proposal.freelancer.avatar else None,
        'cover_letter': proposal.cover_letter,
        'bid_amount': str(proposal.bid_amount),
        'estimated_days': proposal.estimated_days,
        'status': proposal.get_status_display(),
        'submitted_at': proposal.created_at.strftime('%B %d, %Y at %I:%M %p'),
        'attachments': [
            {
                'filename': attachment.filename(),
                'url': attachment.file.url,
                'size': attachment.filesize_formatted(),
                'icon': attachment.get_file_icon(),
                'type': attachment.get_file_type_display()
            } for attachment in proposal.attachments.all()
        ]
    }
    
    return JsonResponse(data)