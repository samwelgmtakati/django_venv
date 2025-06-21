from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from apps.freelancer.models import Skill, Freelancer
from django.urls import reverse

@login_required
def freelancer_skills(request):
    """View for managing freelancer skills"""
    if not hasattr(request.user, 'freelancer_profile'):
        messages.error(request, 'Freelancer profile not found.')
        return redirect('dashboard:freelancer_dashboard')
    
    freelancer = request.user.freelancer_profile
    skills = freelancer.skills.all()
    
    context = {
        'skills': skills,
        'freelancer': freelancer,
    }
    return render(request, 'dashboard/includes/skills_list.html', context)

@login_required
@require_POST
def add_skill(request):
    """Add a new skill to the freelancer's profile"""
    if not hasattr(request.user, 'freelancer_profile'):
        return JsonResponse({'success': False, 'error': 'Freelancer profile not found.'}, status=400)
    
    skill_name = request.POST.get('name', '').strip()
    if not skill_name:
        return JsonResponse({'success': False, 'error': 'Skill name is required.'}, status=400)
    
    # Get or create the skill
    skill, created = Skill.objects.get_or_create(
        name__iexact=skill_name,
        defaults={'name': skill_name}
    )
    
    # Add skill to freelancer if not already added
    freelancer = request.user.freelancer_profile
    if skill not in freelancer.skills.all():
        freelancer.skills.add(skill)
        
        # Return the new skill HTML
        skill_html = f"""
        <div class="skill-item skill-expert" data-skill-id="{skill.id}">
            <div class="skill-header">
                <div class="skill-title-wrapper">
                    <div class="skill-icon">
                        <i class="bi bi-code-slash"></i>
                    </div>
                    <h6 class="skill-title">{skill.name}</h6>
                </div>
                <div class="skill-actions">
                    <button class="btn btn-sm btn-outline-primary edit-skill" data-skill-id="{skill.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-skill" data-skill-id="{skill.id}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
            <div class="skill-meta">
                <div class="skill-progress-wrapper">
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" style="width: 90%" 
                             aria-valuenow="90" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
                <span class="skill-percentage">90%</span>
            </div>
        </div>
        """
        return JsonResponse({
            'success': True,
            'skill_id': skill.id,
            'skill_html': skill_html
        })
    
    return JsonResponse({'success': False, 'error': 'Skill already exists.'}, status=400)

@login_required
def edit_skill(request, skill_id):
    """Edit a skill in the freelancer's profile"""
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
        
    if not hasattr(request.user, 'freelancer_profile'):
        return JsonResponse({'success': False, 'error': 'Freelancer profile not found.'}, status=400)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        skill_name = request.POST.get('name', '').strip()
        if not skill_name:
            return JsonResponse({'success': False, 'error': 'Skill name cannot be empty'}, status=400)
            
        # Get or create the skill
        skill, created = Skill.objects.get_or_create(
            name__iexact=skill_name,
            defaults={'name': skill_name}
        )
        
        # If the skill already exists (not created) but with different case, update it
        if not created and skill.name != skill_name:
            skill.name = skill_name
            skill.save()
        
        freelancer = request.user.freelancer_profile
        old_skill = get_object_or_404(Skill, id=skill_id)
        
        # Check if the old skill is actually assigned to the freelancer
        if not freelancer.skills.filter(id=skill_id).exists():
            return JsonResponse({'success': False, 'error': 'Skill not found in your profile.'}, status=404)
        
        # If the skill is different, update it
        if old_skill.id != skill.id:
            # Remove the old skill
            freelancer.skills.remove(old_skill)
            # Add the new skill if not already present
            if not freelancer.skills.filter(id=skill.id).exists():
                freelancer.skills.add(skill)
        
        return JsonResponse({
            'success': True,
            'message': 'Skill updated successfully',
            'skill': {
                'id': skill.id,
                'name': skill.name
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def delete_skill(request, skill_id):
    """Remove a skill from the freelancer's profile"""
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
        
    if not hasattr(request.user, 'freelancer_profile'):
        return JsonResponse({'success': False, 'error': 'Freelancer profile not found.'}, status=400)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        skill = Skill.objects.get(id=skill_id)
        freelancer = request.user.freelancer_profile
        
        # Check if the skill is actually assigned to the freelancer
        if not freelancer.skills.filter(id=skill_id).exists():
            return JsonResponse({'success': False, 'error': 'Skill not found in your profile.'}, status=404)
            
        freelancer.skills.remove(skill)
        return JsonResponse({'success': True, 'message': 'Skill removed successfully'})
        
    except (ValueError, Skill.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Skill not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': 'An error occurred while removing the skill.'}, status=500)
