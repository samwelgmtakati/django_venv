"""
Debug views for troubleshooting CSRF and other issues.
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from django.conf import settings

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
@ensure_csrf_cookie
def debug_csrf(request):
    """Debug view to check CSRF token and cookies."""
    response_data = {
        'success': True,
        'csrftoken': get_token(request),
        'cookies': dict(request.COOKIES),
        'meta': {k: str(v) for k, v in request.META.items() if k.startswith('HTTP_') or k.startswith('CSRF_')},
        'settings': {
            'CSRF_COOKIE_NAME': settings.CSRF_COOKIE_NAME,
            'CSRF_COOKIE_SECURE': settings.CSRF_COOKIE_SECURE,
            'CSRF_COOKIE_HTTPONLY': settings.CSRF_COOKIE_HTTPONLY,
            'CSRF_COOKIE_SAMESITE': getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Lax'),
            'CSRF_HEADER_NAME': settings.CSRF_HEADER_NAME,
            'CSRF_USE_SESSIONS': settings.CSRF_USE_SESSIONS,
            'CORS_ALLOW_ALL_ORIGINS': getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False),
            'CORS_ALLOW_CREDENTIALS': getattr(settings, 'CORS_ALLOW_CREDENTIALS', False),
        },
    }
    return JsonResponse(response_data)

@require_http_methods(["POST"])
@csrf_exempt
def debug_post(request):
    """Debug view to test POST requests and CSRF."""
    return JsonResponse({
        'success': True,
        'method': request.method,
        'POST': dict(request.POST),
        'FILES': {k: str(v) for k, v in request.FILES.items()},
        'cookies': dict(request.COOKIES),
        'meta': {k: str(v) for k, v in request.META.items() if k.startswith('HTTP_') or k.startswith('CSRF_')},
    })
