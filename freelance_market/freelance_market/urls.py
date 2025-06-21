from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from apps.dashboard import views as dashboard_views
from apps.jobs.views_debug import debug_template_loading

urlpatterns = [
    path('', include(('apps.home.urls', 'home'), namespace='home')),
    path('admin/', admin.site.urls),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('freelancer/', include('apps.freelancer.urls', namespace='freelancer')),
    
    # Debug URLs
    path('debug/template/<path:template_path>/', debug_template_loading, name='debug_template'),
    
    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
        next_page='dashboard:home'
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home:home_page'), name='logout'),
    path('accounts/register/', dashboard_views.register, name='register'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html'
    ), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html'
    ), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # App URLs
    path('client/', include('apps.client.urls', namespace='client')),
    path('jobs/', include('apps.jobs.urls', namespace='jobs')),
    path('services/', include('apps.services.urls', namespace='services')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
    path('messages/', include('apps.messagesys.urls', namespace='messages')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
