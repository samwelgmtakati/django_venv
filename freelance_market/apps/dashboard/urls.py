from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

# Import views directly from their modules
from .views.views import (
    dashboard_home, register, client_dashboard, client_profile, freelancer_dashboard,
    freelancer_profile, post_job, my_projects, active_projects, completed_projects, 
    draft_projects, client_proposals, accept_proposal, reject_proposal, 
    freelancer_proposals, find_work, api_proposal_detail, admin_dashboard, custom_logout
)

# Import skills-related views
from .views_skills import (
    freelancer_skills, add_skill, edit_skill, delete_skill
)

# Import other admin views
from .views.admin_views import (
    admin_freelancers_list, admin_clients_list
)

# Import job_views
from .views.job_views import job_detail

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home (redirects based on user role)
    path('', login_required(dashboard_home), name='home'),
    
    # Admin dashboard and management
    path('admin-dashboard/', login_required(admin_dashboard), name='admin_dashboard'),
    path('admin/freelancers/', login_required(admin_freelancers_list), name='admin_freelancers_list'),
    path('admin/clients/', login_required(admin_clients_list), name='admin_clients_list'),
    
    # Registration - using the full path to avoid conflicts
    path('register/', register, name='register'),
    
    # Client dashboard
    path('client/', login_required(client_dashboard), name='client_dashboard'),
    path('client/profile/', login_required(client_profile), name='client_profile'),
    
    # Freelancer dashboard
    path('freelancer/', login_required(freelancer_dashboard), name='freelancer_dashboard'),
    path('freelancer/profile/', login_required(freelancer_profile), name='freelancer_profile'),
    
    # Skills management
    path('skills/', login_required(freelancer_skills), name='freelancer_skills'),
    path('skills/add/', login_required(add_skill), name='add_skill'),
    path('skills/<int:skill_id>/edit/', login_required(edit_skill), name='edit_skill'),
    path('skills/<int:skill_id>/delete/', login_required(delete_skill), name='delete_skill'),

    path('jobs/post/', post_job, name='post_job'),
    
    # Client project management
    path('projects/', my_projects, name='my_projects'),
    path('projects/active/', active_projects, name='active_projects'),
    path('projects/completed/', completed_projects, name='completed_projects'),
    path('projects/drafts/', draft_projects, name='draft_projects'),
    path('proposals/', client_proposals, name='client_proposals'),
    path('proposals/<int:proposal_id>/accept/', accept_proposal, name='accept_proposal'),
    path('proposals/<int:proposal_id>/reject/', reject_proposal, name='reject_proposal'),
    
    # Freelancer proposals
    path('freelancer/proposals/', freelancer_proposals, name='freelancer_proposals'),
    
    # Job details
    path('jobs/<slug:slug>/', job_detail, name='job_detail'),
    
    # API endpoints
    path('api/proposals/<int:proposal_id>/', api_proposal_detail, name='api_proposal_detail'),
    
    path('find-work/', find_work, name='find_work'),

    # Include auth URLs with custom templates
    path('', include([
        path('login/', auth_views.LoginView.as_view(
            template_name='registration/login.html',
            redirect_authenticated_user=True
        ), name='login'),
        # Logout
        path('logout/', custom_logout, name='logout'),
        
        path('password_change/', auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change.html'
        ), name='password_change'),
        path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html'
        ), name='password_change_done'),
        path('password_reset/', auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt'
        ), name='password_reset'),
        path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ), name='password_reset_done'),
        path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html'
        ), name='password_reset_confirm'),
        path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ), name='password_reset_complete'),
    ])),
]
