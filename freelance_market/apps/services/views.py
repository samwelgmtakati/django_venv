from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Service

class FreelancerServiceMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure only the service owner can modify it"""
    def test_func(self):
        service = self.get_object()
        return self.request.user == service.freelancer

class FreelancerServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'services/service_list.html'  # This is correct as it's in the root templates/services/ directory
    context_object_name = 'services'
    
    def get_queryset(self):
        return Service.objects.filter(freelancer=self.request.user)

class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    fields = ['title', 'description', 'price', 'delivery_time', 'service_type', 'is_active']
    template_name = 'services/service_form.html'
    
    def form_valid(self, form):
        form.instance.freelancer = self.request.user
        messages.success(self.request, 'Service created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('dashboard:freelancer_dashboard')

class ServiceUpdateView(FreelancerServiceMixin, UpdateView):
    model = Service
    fields = ['title', 'description', 'price', 'delivery_time', 'service_type', 'is_active']
    template_name = 'services/service_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Service updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('dashboard:freelancer_dashboard')

class ServiceDeleteView(FreelancerServiceMixin, DeleteView):
    model = Service
    template_name = 'services/service_confirm_delete.html'
    
    def get_success_url(self):
        messages.success(self.request, 'Service deleted successfully!')
        return reverse_lazy('dashboard:freelancer_dashboard')
