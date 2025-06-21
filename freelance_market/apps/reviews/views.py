from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from .models import Review
from .forms import ReviewForm
from apps.jobs.models import Order

class CreateReviewView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_review.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_order()
        if order is not None:  # Only add to context if not a redirect
            context['order'] = order
        return context
    
    def get_order(self, check_reviewed=True):
        order = get_object_or_404(
            Order.objects.select_related('client', 'freelancer'),
            pk=self.kwargs['order_pk'],
            status__in=['completed', 'approved']  # Allow both completed and approved orders
        )
        
        # Check if user is allowed to review this order
        user = self.request.user
        if user not in [order.client, order.freelancer]:
            raise Http404("You are not authorized to review this order.")
            
        # Check if review already exists
        if check_reviewed and Review.objects.filter(order=order, reviewer=user).exists():
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.info(self.request, _('You have already reviewed this order.'))
            return redirect('orders:detail', pk=order.pk)
            
        return order
        
    def get(self, request, *args, **kwargs):
        # Get order without checking for existing review to avoid redirect loop
        order = self.get_order(check_reviewed=False)
        if order is None:
            return super().get(request, *args, **kwargs)
            
        # Check if review exists and redirect if needed
        if Review.objects.filter(order=order, reviewer=request.user).exists():
            from django.contrib import messages
            messages.info(self.request, _('You have already reviewed this order.'))
            return redirect('orders:detail', pk=order.pk)
            
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        order = self.get_order()
        is_client = self.request.user == order.client
        
        review = form.save(commit=False)
        review.order = order
        review.reviewer = self.request.user
        review.user_being_reviewed = order.freelancer if is_client else order.client
        review.is_client_review = is_client
        review.save()
        
        messages.success(self.request, _('Thank you for your review!'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('orders:detail', kwargs={'pk': self.kwargs['order_pk']})
