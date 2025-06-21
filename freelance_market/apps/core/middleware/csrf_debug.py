"""
CSRF Debug Middleware

This middleware helps debug CSRF issues by logging relevant information
about CSRF validation failures.
"""
import logging
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware, RejectRequest, REASON_NO_CSRF_COOKIE, REASON_CSRF_TOKEN_MISSING, REASON_CSRF_TOKEN_INCORRECT

logger = logging.getLogger(__name__)

class CsrfDebugMiddleware(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Log the CSRF failure
        logger.warning(
            "CSRF verification failed: %s",
            reason,
            extra={
                'status_code': 403,
                'request': request,
                'user': str(request.user)
            }
        )
        
        # Log request details that might be helpful for debugging
        logger.debug("CSRF Debug - Request details:")
        logger.debug(f"  Method: {request.method}")
        logger.debug(f"  Path: {request.path}")
        logger.debug(f"  User: {request.user}")
        logger.debug(f"  Is Authenticated: {request.user.is_authenticated}")
        logger.debug(f"  CSRF Cookie: {request.COOKIES.get(settings.CSRF_COOKIE_NAME, 'Not set')}")
        logger.debug(f"  POST data: {request.POST}")
        logger.debug(f"  Headers: {dict(request.headers)}")
        
        # Call the original _reject method
        return super()._reject(request, reason)
