from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from . import views
from .views_proposals import withdraw_proposal, download_attachment, delete_attachment, EditProposalView

app_name = 'jobs'

urlpatterns = [
    # Job Dashboard
    path('', login_required(views.job_dashboard), name='job_dashboard'),
    
    # Job CRUD
    path('list/', views.JobListView.as_view(), name='job_list'),
    path('create/', views.JobCreateView.as_view(), name='job_create'),
    
    # Job browsing for freelancers
    path('browse/', views.JobListView.as_view(
        template_name='jobs/freelancer/job_list.html',
        extra_context={'is_freelancer_view': True}
    ), name='browse_jobs'),
    
    # Status Views - Placed before the slug patterns to avoid conflicts
    path('active/', views.JobListView.as_view(extra_context={'status': 'published'}), name='active_jobs'),
    path('completed/', views.JobListView.as_view(extra_context={'status': 'completed'}), name='completed_jobs'),
    path('drafts/', views.JobListView.as_view(extra_context={'status': 'draft'}), name='draft_jobs'),
    path('archived/', views.JobListView.as_view(extra_context={'status': 'archived'}), name='archived_jobs'),
    
    # Job detail and actions - Keep slug patterns after the status views
    path('<slug:slug>/', views.JobDetailView.as_view(), name='job_detail'),
    path('<slug:slug>/modal/', views.JobDetailModalView.as_view(), name='job_detail_modal'),
    path('<slug:slug>/update/', views.JobUpdateView.as_view(), name='job_update'),
    path('<slug:slug>/delete/', login_required(views.JobDeleteView.as_view()), name='job_delete'),
    path('<slug:slug>/publish/', login_required(views.job_publish), name='job_publish'),
    path('<slug:slug>/status/', views.update_job_status, name='update_job_status'),
    
    # Job Categories
    path('categories/', login_required(views.JobCategoryListView.as_view()), name='category_list'),
    path('categories/create/', login_required(views.JobCategoryCreateView.as_view()), name='category_create'),
    path('categories/<int:pk>/update/', login_required(views.JobCategoryUpdateView.as_view()), name='category_update'),
    path('categories/<int:pk>/delete/', login_required(views.JobCategoryDeleteView.as_view()), name='category_delete'),
    
    # Proposals
    path('<slug:slug>/propose/', login_required(views.SubmitProposalView.as_view()), name='submit_proposal'),
    path('<slug:job_slug>/proposals/', login_required(views.ProposalListView.as_view()), name='proposal_list'),
    path('<slug:job_slug>/proposals/<int:pk>/', login_required(views.ProposalDetailView.as_view()), name='proposal_detail'),
    path('<slug:job_slug>/proposals/<int:pk>/edit/', login_required(EditProposalView.as_view()), name='edit_proposal'),
    path('<slug:job_slug>/proposals/<int:pk>/accept/', login_required(views.accept_proposal), name='accept_proposal'),
    path('<slug:job_slug>/proposals/<int:pk>/reject/', login_required(views.reject_proposal), name='reject_proposal'),
    path('proposals/<int:pk>/withdraw/', login_required(withdraw_proposal), name='withdraw_proposal'),
    path('proposals/<int:proposal_id>/attachments/upload/', login_required(views.upload_proposal_attachment), name='upload_proposal_attachment'),
    path('attachments/<int:pk>/download/', login_required(csrf_exempt(download_attachment)), name='download_attachment'),
    path('attachments/<int:pk>/delete/', login_required(delete_attachment), name='delete_attachment'),
    
    # API Endpoints
    path('api/jobs/', include([
        path('', views.JobListAPIView.as_view(), name='api_job_list'),
        path('<int:pk>/', views.JobDetailAPIView.as_view(), name='api_job_detail'),
    ])),
]

# Removed duplicate status URLs and moved them to the main urlpatterns