from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from . import views
from . import admin_views
from . import views_skills

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home (redirects based on user role)
    path('', login_required(views.dashboard_home), name='home'),
    
    # Admin dashboard and management
    path('admin-dashboard/', login_required(views.admin_dashboard), name='admin_dashboard'),
    path('admin/freelancers/', login_required(admin_views.admin_freelancers_list), name='admin_freelancers_list'),
    path('admin/clients/', login_required(admin_views.admin_clients_list), name='admin_clients_list'),
    
    # Registration - using the full path to avoid conflicts
    path('register/', views.register, name='register'),
    
    # Client dashboard
    path('client/', login_required(views.client_dashboard), name='client_dashboard'),
    path('client/profile/', login_required(views.client_profile), name='client_profile'),
    
    # Freelancer dashboard
    path('freelancer/', login_required(views.freelancer_dashboard), name='freelancer_dashboard'),
    
    # Skills management
    path('skills/', login_required(views_skills.freelancer_skills), name='freelancer_skills'),
    path('skills/add/', login_required(views_skills.add_skill), name='add_skill'),
    path('skills/<int:skill_id>/edit/', login_required(views_skills.edit_skill), name='edit_skill'),
    path('skills/<int:skill_id>/delete/', login_required(views_skills.delete_skill), name='delete_skill'),

    path('jobs/post/', views.post_job, name='post_job'),
    
    # Client project management
    path('projects/', views.my_projects, name='my_projects'),
    path('projects/active/', views.active_projects, name='active_projects'),
    path('projects/completed/', views.completed_projects, name='completed_projects'),
    path('projects/drafts/', views.draft_projects, name='draft_projects'),
    path('proposals/', views.client_proposals, name='client_proposals'),
    path('proposals/<int:proposal_id>/accept/', views.accept_proposal, name='accept_proposal'),
    path('proposals/<int:proposal_id>/reject/', views.reject_proposal, name='reject_proposal'),
    
    # Freelancer proposals
    path('freelancer/proposals/', views.freelancer_proposals, name='freelancer_proposals'),
    
    # API endpoints
    path('api/proposals/<int:proposal_id>/', views.api_proposal_detail, name='api_proposal_detail'),
    
    path('find-work/', views.find_work, name='find_work'),

    # Include auth URLs with custom templates
    path('', include([
        path('login/', auth_views.LoginView.as_view(
            template_name='registration/login.html',
            redirect_authenticated_user=True
        ), name='login'),
        # Replace the existing logout URL pattern with:
        path('logout/', views.custom_logout, name='logout'),
        
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
