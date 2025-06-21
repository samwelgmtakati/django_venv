from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.conf import settings

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Don't initialize reverse here as it might not be ready during app startup

    def __call__(self, request):
        # Skip middleware for static and media files
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)
            
        # Skip middleware for admin login page
        if request.path == reverse('admin:login') or request.path.startswith('/admin/login/'):
            return self.get_response(request)
            
        # Check admin access
        if request.path.startswith('/admin/'):
            if not request.user.is_authenticated:
                return redirect(f'{reverse("admin:login")}?next={request.path}')
            if not request.user.is_staff:
                return HttpResponseForbidden('You do not have permission to access this page.')
        
        return self.get_response(request)
