from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    DetailView, UpdateView, DeleteView, 
    TemplateView, CreateView, ListView, View
)
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_http_methods
from django.forms import modelformset_factory
from django.db.models import Count, Avg, Q
from .models import Freelancer, Skill
from apps.reviews.models import Review
from .forms import FreelancerForm, SkillForm

class SkillMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to check if user has a freelancer profile."""
    def test_func(self):
        return hasattr(self.request.user, 'freelancer_profile')
    
    def handle_no_permission(self):
        messages.info(self.request, 'Please create your freelancer profile first.')
        return redirect('freelancer:create_profile')
    
    def get_freelancer(self):
        return self.request.user.freelancer_profile


class FreelancerProfileView(SkillMixin, DetailView):
    """View for freelancer's own profile."""
    model = Freelancer
    template_name = 'freelancer/profile.html'
    context_object_name = 'freelancer'
    
    def get_object(self, queryset=None):
        try:
            return self.request.user.freelancer_profile
        except Freelancer.DoesNotExist:
            # Redirect to create profile if it doesn't exist
            return None
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            messages.info(request, 'Please create your freelancer profile first.')
            return redirect('freelancer:create_profile')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Freelancer Profile'
        return context

class FreelancerCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new freelancer profile."""
    model = Freelancer
    form_class = FreelancerForm
    template_name = 'freelancer/form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user already has a freelancer profile
        if hasattr(request.user, 'freelancer_profile'):
            return redirect('freelancer:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        self.request.user.is_freelancer = True
        self.request.user.save()
        messages.success(self.request, 'Your freelancer profile has been created!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Freelancer Profile'
        context['submit_text'] = 'Create Profile'
        return context
    
    def get_success_url(self):
        return reverse('freelancer:profile')

class FreelancerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating freelancer profile."""
    model = Freelancer
    form_class = FreelancerForm
    template_name = 'freelancer/form.html'
    
    def get_object(self, queryset=None):
        try:
            return self.request.user.freelancer_profile
        except Freelancer.DoesNotExist:
            raise Http404("You don't have a freelancer profile. Please create one first.")
    
    def test_func(self):
        # Only the profile owner can update it
        freelancer = self.get_object()
        return self.request.user == freelancer.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Profile'
        context['submit_text'] = 'Update Profile'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('freelancer:profile')

class FreelancerDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for deleting freelancer profile."""
    model = Freelancer
    template_name = 'freelancer/confirm_delete.html'
    success_url = reverse_lazy('dashboard:home')
    
    def get_object(self, queryset=None):
        try:
            return self.request.user.freelancer_profile
        except Freelancer.DoesNotExist:
            raise Http404("You don't have a freelancer profile.")
    
    def test_func(self):
        # Only the profile owner can delete it
        freelancer = self.get_object()
        return self.request.user == freelancer.user
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        self.request.user.is_freelancer = False
        self.request.user.save()
        messages.success(request, 'Your freelancer profile has been deleted.')
        return response

class PublicProfileView(DetailView):
    """Public view of a freelancer's profile."""
    model = Freelancer
    template_name = 'freelancer/public_profile.html'
    context_object_name = 'freelancer'
    slug_field = 'user__username'
    slug_url_kwarg = 'username'
    
    def get_queryset(self):
        return Freelancer.objects.filter(user__is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        freelancer = self.object
        
        # Get reviews for this freelancer
        from apps.reviews.models import Review
        reviews = Review.objects.filter(
            user_being_reviewed=freelancer.user,
            is_client_review=False  # Only get reviews from clients
        ).select_related('reviewer').order_by('-created_at')
        
        # Calculate average rating
        avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        # Count reviews by rating
        rating_counts = {}
        for i in range(5, 0, -1):
            rating_counts[i] = reviews.filter(rating=i).count()
        
        context.update({
            'title': f"{freelancer.user.get_full_name() or freelancer.user.username}'s Profile",
            'reviews': reviews[:5],  # Show only 5 most recent reviews
            'total_reviews': reviews.count(),
            'avg_rating': round(avg_rating, 1) if avg_rating else 0,
            'rating_counts': rating_counts,
            'rating_percentage': round((avg_rating / 5) * 100) if avg_rating else 0,
        })
        return context

@login_required
@require_POST
def toggle_availability(request):
    # Toggle freelancer's availability status via AJAX.
    if not request.user.is_authenticated or not hasattr(request.user, 'freelancer_profile'):
        return JsonResponse({'error': 'Authentication required'}, status=403)
    
    if request.method == 'POST':
        freelancer = request.user.freelancer_profile
        freelancer.is_available = not freelancer.is_available
        freelancer.save()
        return JsonResponse({
            'status': 'success',
            'is_available': freelancer.is_available
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)


class SkillListView(SkillMixin, ListView):
    """View for listing and managing freelancer skills."""
    model = Skill
    template_name = 'freelancer/skills.html'
    context_object_name = 'skills'
    
    def get_queryset(self):
        return self.get_freelancer().skills.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Skills'
        context['available_skills'] = Skill.objects.exclude(
            id__in=self.get_queryset().values_list('id', flat=True)
        )
        return context


class SkillAddView(SkillMixin, View):
    """View for adding a skill to freelancer's profile."""
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
            
        skill_id = request.POST.get('skill_id')
        if not skill_id:
            messages.error(request, 'No skill selected')
            return redirect('freelancer:skills')
            
        try:
            skill = Skill.objects.get(id=skill_id)
            freelancer = self.get_freelancer()
            if not freelancer.skills.filter(id=skill.id).exists():
                freelancer.skills.add(skill)
                messages.success(request, f'Added skill: {skill.name}')
            else:
                messages.info(request, f'You already have the skill: {skill.name}')
        except (Skill.DoesNotExist, ValueError):
            messages.error(request, 'Invalid skill selected')
            
        return redirect('freelancer:skills')


class SkillDeleteView(SkillMixin, View):
    """View for removing a skill from freelancer's profile."""
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
            
        skill_id = request.POST.get('skill_id')
        if not skill_id:
            messages.error(request, 'No skill selected')
            return redirect('freelancer:skills')
            
        try:
            skill = Skill.objects.get(id=skill_id)
            freelancer = self.get_freelancer()
            if freelancer.skills.filter(id=skill.id).exists():
                freelancer.skills.remove(skill)
                messages.success(request, f'Removed skill: {skill.name}')
            else:
                messages.warning(request, 'Skill not found in your profile')
        except (Skill.DoesNotExist, ValueError):
            messages.error(request, 'Invalid skill selected')
        return redirect('freelancer:skills')


class SkillCreateView(SkillMixin, CreateView):
    """View for creating a new skill and adding it to freelancer's profile."""
    model = Skill
    form_class = SkillForm
    template_name = 'freelancer/skill_form.html'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Check if skill with this name already exists (case-insensitive)
        name = form.cleaned_data.get('name')
        existing_skill = Skill.objects.filter(name__iexact=name).first()
        
        if existing_skill:
            # If skill exists, add it to the freelancer's skills if not already added
            freelancer = self.get_freelancer()
            if not freelancer.skills.filter(id=existing_skill.id).exists():
                freelancer.skills.add(existing_skill)
                messages.success(self.request, f'Added existing skill: {existing_skill.name}')
            else:
                messages.info(self.request, f'You already have the skill: {existing_skill.name}')
            return redirect('freelancer:skills')
        
        # If skill doesn't exist, create it and add to freelancer's skills
        self.object = form.save()
        self.get_freelancer().skills.add(self.object)
        messages.success(self.request, f'Added new skill: {self.object.name}')
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse('freelancer:skills')
