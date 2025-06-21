from django.shortcuts import render
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.http import HttpResponse
import os

def debug_template_loading(request, template_path):
    """Debug view to check template loading"""
    context = {
        'template_path': template_path,
        'template_dirs': [],
        'template_found': False,
        'template_absolute_path': None,
        'template_content': None,
        'template_exists': False,
    }
    
    # Try to get the template
    try:
        template = get_template(template_path)
        context['template_found'] = True
        context['template_absolute_path'] = template.origin.name if hasattr(template, 'origin') else 'Not available'
        context['template_exists'] = os.path.exists(context['template_absolute_path'])
        
        # Try to read template content
        try:
            with open(context['template_absolute_path'], 'r') as f:
                context['template_content'] = f.read()
        except Exception as e:
            context['template_content'] = f"Error reading template: {str(e)}"
    except TemplateDoesNotExist as e:
        context['error'] = f"Template not found: {str(e)}"
    except Exception as e:
        context['error'] = f"Error loading template: {str(e)}"
    
    # Get template directories
    from django.template.engine import Engine
    engine = Engine.get_default()
    context['template_dirs'] = [str(d) for d in engine.dirs]
    
    # Check if template exists in any of the template dirs
    for template_dir in context['template_dirs']:
        full_path = os.path.join(template_dir, template_path)
        if os.path.exists(full_path):
            context['template_exists_in_dirs'] = full_path
            break
    
    return render(request, 'debug/template_debug.html', context)
