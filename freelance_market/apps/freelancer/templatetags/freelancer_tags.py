from django import template
from django.contrib.auth import get_user_model

register = template.Library()

@register.filter(name='has_freelancer_profile')
def has_freelancer_profile(user):
    """Check if the user has a freelancer profile."""
    if not user.is_authenticated:
        return False
    return hasattr(user, 'freelancer_profile')

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get a value from a dictionary using a key.
    Usage: {{ my_dict|get_item:key }}
    """
    if not dictionary:
        return None
    return dictionary.get(key, '')
