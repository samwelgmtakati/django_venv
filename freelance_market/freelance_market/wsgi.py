"""
WSGI config for freelance_market project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_market.settings')
# Set production environment if not set
os.environ.setdefault('DJANGO_ENV', 'production')

# This application object is used by any WSGI server configured to use this file.
application = get_wsgi_application()

# Apply WSGI middleware here if needed
# from whitenoise import WhiteNoise
# application = WhiteNoise(application, root=os.path.join(BASE_DIR, 'staticfiles'))
