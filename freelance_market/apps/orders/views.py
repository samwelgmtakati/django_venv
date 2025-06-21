import os
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

from apps.jobs.models import Order, OrderDelivery
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
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    paginate_by = 1  # Show one order per page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object if hasattr(self, 'object') else None
        
        # Get the filtered queryset we stored in get_queryset
        queryset = getattr(self, 'filtered_queryset', Order.objects.none())
        
        # If no order is found, set up empty context
        if not order:
            context.update({
                'order': None,
                'active_page': 'orders',
                'can_deliver': False,
                'can_approve': False,
                'can_request_revision': False,
                'can_review': False,
                'has_reviewed': False,
                'reviews': [],
                'deliveries': [],
                'pagination': {
                    'has_previous': False,
                    'has_next': False,
                    'previous_order_id': None,
                    'next_order_id': None,
                    'current_index': 0,
                    'total_orders': 0
                },
                'STATUS_APPROVED': Order.STATUS_APPROVED,
                'STATUS_CANCELLED': Order.STATUS_CANCELLED,
                'STATUS_DELIVERED': Order.STATUS_DELIVERED,
                'STATUS_IN_PROGRESS': Order.STATUS_IN_PROGRESS,
                'STATUS_REVISION_REQUESTED': Order.STATUS_REVISION_REQUESTED,
            })
            return context
            
        # Get all orders for pagination
        user = self.request.user
        client_orders = Order.objects.filter(client=user)
        freelancer_orders = Order.objects.filter(freelancer=user)
        all_orders = (client_orders | freelancer_orders).distinct().order_by('-created_at')
        
        # Get current order index and total count
        order_list = list(all_orders.values_list('id', flat=True))
        current_index = order_list.index(order.id) if order.id in order_list else 0
        total_orders = len(order_list)
        
        # Get previous and next order IDs
        prev_order_id = order_list[current_index - 1] if current_index > 0 else None
        next_order_id = order_list[current_index + 1] if current_index < total_orders - 1 else None
        
        # Add pagination context
        pagination = {
            'has_previous': current_index > 0,
            'has_next': current_index < total_orders - 1,
            'previous_order_id': prev_order_id,
            'next_order_id': next_order_id,
            'current_index': current_index + 1,
            'total_orders': total_orders,
        }
        
        # Get reviews and deliveries
        from apps.reviews.models import Review
        reviews = Review.objects.filter(order=order).select_related('reviewer').order_by('-created_at')
        has_reviewed = reviews.filter(reviewer=self.request.user).exists()
        
        # Check permissions
        can_deliver = (
            order.freelancer == self.request.user and 
            order.status in [Order.STATUS_IN_PROGRESS, Order.STATUS_REVISION_REQUESTED]
        )
        
        can_approve = (
            order.client == self.request.user and 
            order.status == Order.STATUS_DELIVERED
        )
        
        can_request_revision = (
            order.client == self.request.user and 
            order.status == Order.STATUS_DELIVERED
        )
        
        can_review = (
            order.status == Order.STATUS_APPROVED and 
            not has_reviewed
        )
        
        # Update context
        context.update({
            'active_page': 'orders',
            'order': order,
            'can_deliver': can_deliver,
            'can_approve': can_approve,
            'can_request_revision': can_request_revision,
            'can_review': can_review,
            'has_reviewed': has_reviewed,
            'reviews': reviews,
            'deliveries': order.deliveries.all().order_by('-uploaded_at'),
            'pagination': pagination,
            'STATUS_APPROVED': Order.STATUS_APPROVED,
            'STATUS_CANCELLED': Order.STATUS_CANCELLED,
            'STATUS_DELIVERED': Order.STATUS_DELIVERED,
            'STATUS_IN_PROGRESS': Order.STATUS_IN_PROGRESS,
            'STATUS_REVISION_REQUESTED': Order.STATUS_REVISION_REQUESTED,
        })
        return context

    def get_queryset(self):
        user = self.request.user
        print(f"Getting orders for user: {user}")  # Debug print
        
        # First get all orders where user is either client or freelancer
        client_orders = Order.objects.filter(client=user)
        freelancer_orders = Order.objects.filter(freelancer=user)
        queryset = (client_orders | freelancer_orders).distinct()
        
        print(f"Found {queryset.count()} total orders")  # Debug print
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.exclude(status__in=[Order.STATUS_APPROVED, Order.STATUS_CANCELLED])
        elif status == 'completed':
            queryset = queryset.filter(status=Order.STATUS_APPROVED)
        elif status == 'cancelled':
            queryset = queryset.filter(status=Order.STATUS_CANCELLED)
        
        # Order by creation date, newest first
        queryset = queryset.order_by('-created_at')
        
        # Store the filtered queryset for later use
        self.filtered_queryset = queryset
        
        print(f"After filtering: {queryset.count()} orders")  # Debug print
        
        # Handle order_id parameter for direct navigation
        order_id = self.request.GET.get('order_id')
        if order_id:
            try:
                # Try to get the specific order if ID is provided
                order = queryset.get(id=order_id)
                return order
            except (Order.DoesNotExist, ValueError):
                pass
        
        # If no orders exist, return an empty queryset
        if not queryset.exists():
            return queryset.none()
                
        # Get the page number from the request
        page = self.request.GET.get('page', 1)
        paginator = Paginator(queryset, self.paginate_by)
        
        try:
            page_obj = paginator.page(page)
            if page_obj.object_list.exists():
                return page_obj.object_list[0]
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)
            if page_obj.object_list.exists():
                return page_obj.object_list[0]
        
        # Return first order if pagination fails
        return queryset.first()
    
    def get(self, request, *args, **kwargs):
        try:
            print("OrderListView: GET request received")  # Debug print
            response = super().get(request, *args, **kwargs)
            print(f"Rendering template: {self.template_name}")  # Debug print
            print(f"Context data: {self.get_context_data()}")  # Debug print
            return response
        except Exception as e:
            print(f"Error in OrderListView: {str(e)}")  # Debug print
            raise


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        user = self.request.user
        
        # Attach request to order for can_be_reviewed property
        order._request = self.request
        
        # Add delivery history
        context['deliveries'] = order.deliveries.all().order_by('-uploaded_at')
        
        # Get all reviews for this order
        from apps.reviews.models import Review
        reviews = Review.objects.filter(order=order).select_related('reviewer').order_by('-created_at')
        
        # Check if current user has already reviewed
        has_reviewed = reviews.filter(reviewer=user).exists()
        
        # Add review section context
        show_review_section = order.status in [Order.STATUS_APPROVED, Order.STATUS_COMPLETED]
        can_leave_review = (
            order.status in [Order.STATUS_APPROVED, Order.STATUS_COMPLETED] and 
            not has_reviewed and
            user in [order.client, order.freelancer]
        )
        
        context.update({
            'debug_info': {
                'template_name': self.template_name,
                'order_status': order.status,
                'order_status_display': order.get_status_display(),
                'user_roles': {
                    'is_client': user == order.client,
                    'is_freelancer': user == order.freelancer,
                }
            },
            'reviews': reviews,
            'has_reviewed': has_reviewed,
            'can_review': can_leave_review,
            'show_review_section': show_review_section,
            'review_exists': reviews.exists(),
        })
        
        # Add permissions
        context.update({
            'can_start': (
                user == order.client and 
                order.status == Order.STATUS_INITIATED
            ),
            'can_deliver': (
                user == order.freelancer and 
                order.status in [Order.STATUS_IN_PROGRESS, Order.STATUS_REVISION_REQUESTED]
            ),
            'can_approve': (
                user == order.client and 
                order.status == Order.STATUS_DELIVERED
            ),
            'can_request_revision': (
                user == order.client and 
                order.status == Order.STATUS_DELIVERED and
                order.revision_count < order.max_revisions
            ),
            'can_be_reviewed': order.can_be_reviewed,
            'is_client': user == order.client,
            'is_freelancer': user == order.freelancer,
        })
        
        # Add payment info
        context['payment_actions'] = {
            'can_pay': (
                order.payment_status == Order.PAYMENT_PENDING and
                self.request.user == order.client
            ),
            'can_refund': (
                order.payment_status == Order.PAYMENT_PAID and
                self.request.user == order.client
            )
        }
        
        return context
        
    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()
        if request.user not in {order.client, order.freelancer} and not request.user.is_staff:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class OrderDeliverView(LoginRequiredMixin, FormView):
    form_class = OrderDeliveryForm
    template_name = "orders/delivery_form.html"  # This should be in apps/orders/templates/orders/
    
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
    """Client leaves rating & comment after order is approved."""
    form_class = OrderReviewForm
    template_name = "orders/review_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs["pk"])
        if request.user != self.order.client or self.order.status != Order.STATUS_APPROVED or hasattr(self.order, 'review'):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        review = form.save(commit=False)
        review.order = self.order
        review.client = self.order.client
        review.freelancer = self.order.freelancer
        review.save()
        return redirect("orders:detail", pk=self.order.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context

