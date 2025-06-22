from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, UpdateView, ListView, View
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse, HttpResponseForbidden
from django.db.models import Avg, Count, Q
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import Review, ReviewHelpfulVote
from .forms import ReviewForm, ReviewResponseForm, ReviewHelpfulVoteForm
from apps.jobs.models import Order
from apps.accounts.models import User

class CreateReviewView(LoginRequiredMixin, CreateView):
    """View for creating a new review for an order."""
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_review.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_order()
        if order is not None:  # Only add to context if not a redirect
            context['order'] = order
            context['is_client'] = self.request.user == order.client
        return context
    
    def get_order(self, check_reviewed=True):
        order = get_object_or_404(
            Order.objects.select_related('client', 'freelancer'),
            pk=self.kwargs['order_pk'],
            status__in=[Order.STATUS_COMPLETED, Order.STATUS_APPROVED]
        )
        
        # Check if user is allowed to review this order
        user = self.request.user
        if user not in [order.client, order.freelancer]:
            raise Http404(_("You are not authorized to review this order."))
            
        # Check if review already exists
        if check_reviewed and Review.objects.filter(order=order, reviewer=user).exists():
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
            messages.info(self.request, _('You have already reviewed this order.'))
            return redirect('orders:detail', pk=order.pk)
            
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        order = self.get_order()
        if order is None:  # If get_order() returned None due to a redirect
            return redirect(self.get_success_url())
            
        # Create the review object but don't save it yet
        review = form.save(commit=False)
        review.order = order
        review.reviewer = self.request.user
        review.user_being_reviewed = order.freelancer if self.request.user == order.client else order.client
        
        # Set review type based on user flags
        if review.user_being_reviewed.is_freelancer:
            review.review_type = 'freelancer'
        elif review.user_being_reviewed.is_client:
            review.review_type = 'client'
        
        # Calculate average of all ratings if detailed ratings are provided
        if all([review.communication_rating, review.quality_rating, 
                review.deadline_rating, review.professionalism_rating]):
            ratings = [
                int(review.communication_rating),
                int(review.quality_rating),
                int(review.deadline_rating),
                int(review.professionalism_rating)
            ]
            review.rating = round(sum(ratings) / len(ratings))
        
        # Save the review
        review.save()
        
        # Send notification to the user being reviewed
        if review.review_type == 'freelancer':
            notification_message = f"You have received a new review from {order.client.get_full_name() or order.client.username}"
            notification_recipient = order.freelancer
        else:
            notification_message = f"You have received a new review from {order.freelancer.get_full_name() or order.freelancer.username}"
            notification_recipient = order.client
        
        # Create notification
        from apps.notifications.models import Notification
        notification = Notification.objects.create(
            recipient=notification_recipient,
            sender=self.request.user,
            notification_type='new_review',
            message=notification_message,
            target_url=reverse('reviews:user_reviews', kwargs={'username': notification_recipient.username})
        )
        
        # Update user's average rating
        from .models import update_user_rating
        update_user_rating(review.user_being_reviewed)
        
        messages.success(self.request, _('Thank you for your detailed review!'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('orders:detail', kwargs={'pk': self.kwargs['order_pk']})


class UpdateReviewView(LoginRequiredMixin, UpdateView):
    """View for updating an existing review."""
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/update_review.html'
    
    def get_queryset(self):
        return Review.objects.filter(reviewer=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.object.order
        context['is_client'] = self.request.user == self.object.order.client
        return context
    
    def form_valid(self, form):
        review = form.save(commit=False)
        review.was_edited = True
        
        # Set review type based on user flags
        if review.user_being_reviewed.is_freelancer:
            review.review_type = 'freelancer'
        elif review.user_being_reviewed.is_client:
            review.review_type = 'client'
        
        # Calculate average of all ratings if detailed ratings are provided
        if all([review.communication_rating, review.quality_rating, 
                review.deadline_rating, review.professionalism_rating]):
            ratings = [
                int(review.communication_rating),
                int(review.quality_rating),
                int(review.deadline_rating),
                int(review.professionalism_rating)
            ]
            review.rating = round(sum(ratings) / len(ratings))
        
        # Save the review
        review.save()
        
        # Only send notification if the review content or ratings changed
        if form.has_changed():
            if review.review_type == 'freelancer':
                notification_message = f"Your review from {review.order.client.get_full_name() or review.order.client.username} has been updated"
                notification_recipient = review.order.freelancer
            else:
                notification_message = f"Your review from {review.order.freelancer.get_full_name() or review.order.freelancer.username} has been updated"
                notification_recipient = review.order.client
                
            # Create notification
            from apps.notifications.models import Notification
            Notification.objects.create(
                recipient=notification_recipient,
                sender=self.request.user,
                notification_type='updated_review',
                message=notification_message,
                target_url=reverse('reviews:user_reviews', kwargs={'username': notification_recipient.username})
            )
        
        # Update user's average rating
        if review.user_being_reviewed:
            from .models import update_user_rating
            update_user_rating(review.user_being_reviewed)
        
        messages.success(self.request, _('Your review has been updated.'))
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirect to the user's reviews page after successful submission
        return reverse_lazy('reviews:user_reviews', kwargs={'username': self.request.user.username})


class ReviewResponseView(LoginRequiredMixin, View):
    """View for responding to a review."""
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        
        # Only the reviewed user can respond to the review
        if review.user_being_reviewed != request.user:
            return HttpResponseForbidden(_("You are not authorized to respond to this review."))
        
        form = ReviewResponseForm(request.POST, instance=review)
        if form.is_valid():
            response = form.save(commit=False)
            response.save()
            
            # Send notification to the reviewer
            from apps.notifications.models import Notification
            Notification.objects.create(
                recipient=review.reviewer,
                sender=request.user,
                notification_type='review_response',
                message=f"{request.user.get_full_name() or request.user.username} has responded to your review",
                target_url=reverse('reviews:user_reviews', kwargs={'username': review.reviewer.username}) + f'#review-{review.id}'
            )
            
            messages.success(request, _('Your response has been submitted.'))
        else:
            messages.error(request, _('There was an error with your response.'))
        
        # Redirect back to the user's reviews page
        return redirect('reviews:user_reviews', username=request.user.username)


@method_decorator(require_http_methods(["POST"]), name='dispatch')
class ReviewHelpfulVoteView(LoginRequiredMixin, View):
    """View for marking a review as helpful."""
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        
        # User can't vote on their own review
        if review.reviewer == request.user:
            return JsonResponse({
                'success': False,
                'message': _('You cannot vote on your own review.')
            }, status=400)
        
        form = ReviewHelpfulVoteForm(request.POST, user=request.user, review=review)
        
        if form.is_valid():
            # Check if user already voted
            existing_vote = ReviewHelpfulVote.objects.filter(
                user=request.user,
                review=review
            ).first()
            
            if existing_vote:
                # Toggle helpful status
                existing_vote.is_helpful = not existing_vote.is_helpful
                existing_vote.save()
                
                # Update helpful count
                review.helpful_count = ReviewHelpfulVote.objects.filter(
                    review=review, 
                    is_helpful=True
                ).count()
                review.save(update_fields=['helpful_count'])
                
                return JsonResponse({
                    'success': True,
                    'helpful': existing_vote.is_helpful,
                    'helpful_count': review.helpful_count
                })
            else:
                # Create new vote
                form.save()
                return JsonResponse({
                    'success': True,
                    'helpful': True,
                    'helpful_count': review.helpful_count + 1
                })
        
        return JsonResponse({
            'success': False,
            'message': _('Invalid request.')
        }, status=400)


class UserReviewsView(ListView):
    """View for displaying all reviews for a user."""
    model = Review
    template_name = 'reviews/user_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        username = self.kwargs.get('username')
        self.user = get_object_or_404(User, username=username)
        
        queryset = Review.objects.filter(
            user_being_reviewed=self.user,
            is_verified=True
        ).select_related(
            'reviewer',
            'order',
            'order__job'
        ).order_by('-created_at')
        
        # Filter by rating if provided
        rating = self.request.GET.get('rating')
        if rating and rating.isdigit():
            rating = int(rating)
            if 1 <= rating <= 5:
                queryset = queryset.filter(rating=rating)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_user'] = self.user
        
        # Get rating statistics
        stats = Review.objects.filter(
            user_being_reviewed=self.user,
            is_verified=True
        ).aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id'),
            five_star=Count('id', filter=Q(rating=5)),
            four_star=Count('id', filter=Q(rating=4)),
            three_star=Count('id', filter=Q(rating=3)),
            two_star=Count('id', filter=Q(rating=2)),
            one_star=Count('id', filter=Q(rating=1))
        )
        
        # Calculate percentages
        total = stats['total_reviews'] or 1  # Avoid division by zero
        for i in range(1, 6):
            count = stats.get(f'{i}_star', 0)
            stats[f'{i}_star_pct'] = round((count / total) * 100) if total else 0
        
        context.update({
            'stats': stats,
            'active_filter': self.request.GET.get('rating', 'all'),
            'is_freelancer': hasattr(self.user, 'freelancer'),
            'is_client': hasattr(self.user, 'client'),
        })
        
        return context
