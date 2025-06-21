from django import template
from django.template.defaultfilters import filesizeformat
import os

register = template.Library()

@register.filter
def has_profile_picture(user):
    """
    Check if the user has a profile picture.
    Returns True if the user has a profile picture with an associated file.
    """
    if not user or not hasattr(user, 'profile_picture'):
        return False
    
    try:
        # Check if the file exists and has a name
        return bool(user.profile_picture and user.profile_picture.name)
    except (ValueError, AttributeError):
        return False
