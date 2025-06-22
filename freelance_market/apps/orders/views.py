import os
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, FormView, UpdateView, View
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseForbidden, JsonResponse, Http404, HttpResponseRedirect
from django.forms import ValidationError
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging

from apps.jobs.models import Order, OrderDelivery
from apps.reviews.models import Review
from .forms import OrderDeliveryForm, OrderReviewForm, OrderRevisionForm


@login_required
@require_http_methods(["POST"])
def start_order(request, pk):
    """Mark order as in progress (client confirms start of work)."""
    order = get_object_or_404(Order, pk=pk)
    
    if request.user != order.client:
        return HttpResponseForbidden("Only the client can start the order")
        
    try:
        order.mark_in_progress()
        messages.success(request, "Order marked as in progress. The freelancer can now start working.")
    except ValueError as e:
        messages.error(request, str(e))
        
    return redirect("orders:detail", pk=order.pk)


@login_required
@require_http_methods(["POST"])
def approve_order(request, pk):
    """Client approves delivered order marking it as approved."""
    order = get_object_or_404(Order, pk=pk)
    if request.user != order.client or order.status != Order.STATUS_DELIVERED:
        return HttpResponseForbidden()
    order.mark_approved()
    messages.success(request, "Order approved successfully!")
    return redirect("orders:detail", pk=order.pk)


class OrderListView(LoginRequiredMixin, ListView):
    """
    View for listing all orders for the current user with filtering and pagination.
    """
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Get the list of orders for the current user with optional status filtering.
        """
        user = self.request.user
        queryset = Order.objects.filter(
            Q(client=user) | Q(freelancer=user)
        ).distinct()
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.exclude(
                status__in=[Order.STATUS_APPROVED, Order.STATUS_CANCELLED, Order.STATUS_COMPLETED]
            )
        elif status == 'completed':
            queryset = queryset.filter(status=Order.STATUS_APPROVED) | \
                      queryset.filter(status=Order.STATUS_COMPLETED)
        elif status == 'cancelled':
            queryset = queryset.filter(status=Order.STATUS_CANCELLED)
        
        return queryset.select_related('job', 'client', 'freelancer')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get base queryset for the current user
        base_queryset = Order.objects.filter(
            Q(client=user) | Q(freelancer=user)
        ).distinct()
        
        # Add statistics to context
        context.update({
            'active_page': 'orders',
            'active_orders_count': base_queryset.filter(
                status__in=[
                    Order.STATUS_IN_PROGRESS,
                    Order.STATUS_DELIVERED,
                    Order.STATUS_REVISION_REQUESTED
                ]
            ).count(),
            'completed_orders_count': base_queryset.filter(
                status=Order.STATUS_APPROVED
            ).count(),
            'total_spent': base_queryset.filter(
                client=user,
                status=Order.STATUS_APPROVED
            ).aggregate(total=models.Sum('amount')).get('total__sum') or 0,
        })
        
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying details of a specific order.
    """
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    
    def get_queryset(self):
        """
        Only allow the client or freelancer to view the order.
        """
        user = self.request.user
        return Order.objects.filter(
            Q(client=user) | Q(freelancer=user)
        ).select_related('job', 'client', 'freelancer')

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the template.
        """
        context = super().get_context_data(**kwargs)
        order = self.object
        user = self.request.user
        
        # Get reviews with user info
        reviews = order.reviews.select_related('reviewer').order_by('-created_at')
        
        # Check if current user has reviewed
        user_has_reviewed = False
        if user.is_authenticated:
            user_has_reviewed = reviews.filter(reviewer=user).exists()
        
        # Check permissions
        can_deliver = (
            order.freelancer == user and 
            order.status in [Order.STATUS_IN_PROGRESS, Order.STATUS_REVISION_REQUESTED]
        )
        
        can_approve = (
            order.client == user and 
            order.status == Order.STATUS_DELIVERED
        )
        
        can_request_revision = (
            order.client == user and 
            order.status == Order.STATUS_DELIVERED
        )
        
        can_review = (
            order.status in [Order.STATUS_APPROVED, Order.STATUS_COMPLETED] and 
            not user_has_reviewed and
            user in [order.client, order.freelancer]
        )
        
        # Add to context
        context.update({
            'can_deliver': can_deliver,
            'can_approve': can_approve,
            'can_request_revision': can_request_revision,
            'can_review': can_review,
            'user_has_reviewed': user_has_reviewed,
            'reviews': reviews,
            'deliveries': order.deliveries.all().order_by('-uploaded_at'),
            'active_page': 'orders',
            'can_be_reviewed': order.status in [Order.STATUS_APPROVED, Order.STATUS_COMPLETED],
            'is_client': user == order.client,
            'is_freelancer': user == order.freelancer,
            'payment_actions': {
                'can_pay': (
                    order.payment_status == Order.PAYMENT_PENDING and
                    user == order.client
                ),
                'can_refund': (
                    order.payment_status == Order.PAYMENT_PAID and
                    user == order.client
                )
            }
        })
        
        return context
        
    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()
        if request.user not in {order.client, order.freelancer} and not request.user.is_staff:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class OrderDeliverView(LoginRequiredMixin, FormView):
    form_class = OrderDeliveryForm
    template_name = "orders/delivery_form.html"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.order = get_object_or_404(Order, pk=kwargs["pk"])
        
    def dispatch(self, request, *args, **kwargs):
        # Check permissions
        if request.user != self.order.freelancer:
            return HttpResponseForbidden("You are not authorized to deliver this order.")
        if self.order.status not in [Order.STATUS_IN_PROGRESS, Order.STATUS_REVISION_REQUESTED]:
            return HttpResponseForbidden("Cannot deliver order in current status")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.order
        return kwargs
        
    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def form_valid(self, form):
        delivery = form.save(commit=False)
        delivery.order = self.order
        delivery.is_revision = self.order.status == Order.STATUS_REVISION_REQUESTED
        delivery.save()
        
        # Mark as delivered if not already
        if self.order.status != Order.STATUS_DELIVERED:
            self.order.mark_delivered()
            
        messages.success(self.request, "Work delivered successfully!")
        return redirect("orders:detail", pk=self.order.pk)

    def get_context_data(self, **kwargs):
        # Get the form first to ensure it's properly initialized
        form = self.get_form()
        
        # Update context with form and other data
        context = super().get_context_data(**kwargs)
        context.update({
            'order': self.order,
            'is_revision': self.order.status == Order.STATUS_REVISION_REQUESTED,
            'form': form,
            'debug': True  # Ensure debug is always available in template
        })
        
        # Debug information
        print("\nDEBUG - OrderDeliverView - Context:")
        print(f"- Order ID: {self.order.id}")
        print(f"- Order Status: {self.order.status} ({self.order.get_status_display()})")
        print(f"- Form in context: {'form' in context}")
        if 'form' in context:
            print(f"- Form fields: {list(context['form'].fields.keys())}")
            print(f"- Form visible fields: {[f.name for f in context['form'].visible_fields()]}")
            print(f"- Form hidden fields: {[f.name for f in context['form'].hidden_fields()]}")
        else:
            print("- No form in context")
            
        # Print template debug info
        print("\nTemplate debug info:")
        print(f"- Template name: {self.template_name}")
        print(f"- Template exists: {os.path.exists(os.path.join(settings.BASE_DIR, 'templates', self.template_name)) if hasattr(settings, 'BASE_DIR') else 'Cannot verify'}")
        
        # Print form field details
        if 'form' in context:
            print("\nForm field details:")
            for name, field in context['form'].fields.items():
                print(f"- {name}: {field.__class__.__name__} (required={field.required}, label='{field.label}')")
        
        return context


class RequestRevisionView(LoginRequiredMixin, FormView):
    """View for clients to request revisions on delivered work."""
    form_class = OrderRevisionForm
    template_name = "orders/request_revision.html"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs["pk"])
        if request.user != self.order.client:
            return HttpResponseForbidden()
        if self.order.status != Order.STATUS_DELIVERED:
            return HttpResponseForbidden("Can only request revision on delivered orders")
        if self.order.revision_count >= self.order.max_revisions:
            return HttpResponseForbidden("Maximum number of revisions reached")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            self.order.request_revision(
                message=form.cleaned_data.get('message', '')
            )
            messages.success(self.request, "Revision requested successfully!")
            # TODO: Send notification to freelancer
            return redirect("orders:detail", pk=self.order.pk)
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context


class PaymentActionView(LoginRequiredMixin, View):
    """Handle payment actions (hold, release, refund)."""
    
    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'])
        action = request.POST.get('action')
        
        # Verify permissions
        if request.user != order.client:
            return JsonResponse({"error": "Permission denied"}, status=403)
        
        try:
            if action == "pay":
                if order.payment_status != Order.PAYMENT_PENDING:
                    raise ValidationError("Cannot process payment in current status")
                order.mark_as_paid()
                message = "Payment processed successfully"
                
            elif action == "refund":
                if order.payment_status != Order.PAYMENT_PAID:
                    raise ValidationError("Cannot refund payment in current status")
                order.payment_status = Order.PAYMENT_REFUNDED
                order.save(update_fields=['payment_status', 'updated_at'])
                message = "Payment refunded to client"
                
            else:
                return JsonResponse({"error": "Invalid action"}, status=400)
                
            return JsonResponse({"status": "success", "message": message})
            
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Payment action failed: {str(e)}", exc_info=True)
            return JsonResponse({"error": "An error occurred"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class OrderReviewCreateView(LoginRequiredMixin, FormView):
    """View for leaving a review after order is approved.
    
    Both clients and freelancers can leave reviews for each other.
    """
    form_class = OrderReviewForm
    template_name = "orders/review_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs["pk"])
        self.user = request.user
        
        # Check if user is part of this order
        if self.user not in [self.order.client, self.order.freelancer]:
            return HttpResponseForbidden("Only participants of this order can leave a review.")
        
        # Check if order is approved
        if self.order.status != Order.STATUS_APPROVED:
            return HttpResponseForbidden(
                f"Reviews can only be left for approved orders. Current status: {self.order.get_status_display()}"
            )
        
        # Check if user has already reviewed this order
        existing_review = Review.objects.filter(
            order=self.order,
            reviewer=self.user
        ).first()
        
        if existing_review:
            return HttpResponseForbidden("You have already submitted a review for this order.")
            
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        kwargs['order'] = self.order
        return kwargs

    def form_valid(self, form):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Form is valid, processing review submission...")
        
        # Debug form data
        logger.info(f"Form data: {form.cleaned_data}")
        
        # Check again for existing review to prevent race conditions
        if Review.objects.filter(order=self.order, reviewer=self.user).exists():
            logger.warning(f"User {self.user} already has a review for order {self.order.id}")
            messages.warning(self.request, "You have already submitted a review for this order.")
            return redirect("orders:detail", pk=self.order.pk)
            
        try:
            review = form.save(commit=False)
            review.order = self.order
            review.reviewer = self.user
            
            # Set the user being reviewed (the other party in the order)
            if self.user == self.order.client:
                review.user_being_reviewed = self.order.freelancer
                review.is_client_review = True
                logger.info(f"Client review from {self.user} for freelancer {self.order.freelancer}")
            else:
                review.user_being_reviewed = self.order.client
                review.is_client_review = False
                logger.info(f"Freelancer review from {self.user} for client {self.order.client}")
            
            # Save the review
            review.save()
            logger.info(f"Review saved with ID {review.id}")
            
            # Update the user's rating
            from apps.reviews.models import update_user_rating
            update_user_rating(review.user_being_reviewed)
            logger.info(f"Updated rating for user {review.user_being_reviewed}")
            
            messages.success(self.request, "Thank you for your review!")
            
            # Ensure we're redirecting to the order detail page
            redirect_url = reverse("orders:detail", kwargs={"pk": self.order.pk})
            logger.info(f"Redirecting to {redirect_url}")
            return redirect(redirect_url)
            
        except Exception as e:
            logger.error(f"Error saving review: {str(e)}", exc_info=True)
            messages.error(self.request, f"An error occurred: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        logger = logging.getLogger(__name__)
        logger.warning("Form is invalid")
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        
        # Add information about who is being reviewed
        if self.user == self.order.client:
            context["reviewing_freelancer"] = True
            context["user_being_reviewed"] = self.order.freelancer
        else:
            context["reviewing_freelancer"] = False
            context["user_being_reviewed"] = self.order.client
            
        return context

