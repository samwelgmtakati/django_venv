from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='get_range')
def get_range(value):
    """Return a range of numbers from 0 to the given value."""
    return range(int(value))

@register.filter(name='subtract')
def subtract(value, arg):
    """Subtract the argument from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return value - arg
        except Exception:
            return ''
