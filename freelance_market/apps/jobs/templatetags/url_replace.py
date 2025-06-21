from django import template

register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    """
    Replace or add a URL parameter.
    
    Usage in template:
    {% load url_replace %}
    <a href="?{% url_replace request 'page' 1 %}">First page</a>
    """
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()
