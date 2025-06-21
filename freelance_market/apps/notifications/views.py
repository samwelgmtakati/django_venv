from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, View
from django.utils import timezone

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """View for listing all notifications for the current user."""
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user, 
            is_read=False
        ).count()
        return context


class UnreadNotificationListView(NotificationListView):
    """View for listing only unread notifications."""
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            is_read=False
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_only'] = True
        return context


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """View for displaying a single notification."""
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Mark as read when viewed
        if not self.object.is_read:
            self.object.mark_as_read()
        return response


class MarkNotificationReadView(LoginRequiredMixin, View):
    """View for marking a single notification as read."""
    
    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(
            Notification,
            pk=kwargs['pk'],
            user=request.user
        )
        if not notification.is_read:
            notification.mark_as_read()
            messages.success(request, 'Notification marked as read.')
        
        next_url = request.META.get('HTTP_REFERER', reverse('notifications:list'))
        return redirect(next_url)


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """View for marking all notifications as read."""
    
    def post(self, request, *args, **kwargs):
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        if updated > 0:
            messages.success(request, f'Marked {updated} notifications as read.')
        else:
            messages.info(request, 'No unread notifications to mark as read.')
        
        next_url = request.META.get('HTTP_REFERER', reverse('notifications:list'))
        return redirect(next_url)
