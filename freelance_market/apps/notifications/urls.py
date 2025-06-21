from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', login_required(views.NotificationListView.as_view()), name='list'),
    path('unread/', login_required(views.UnreadNotificationListView.as_view()), name='unread'),
    path('<int:pk>/', login_required(views.NotificationDetailView.as_view()), name='detail'),
    path('<int:pk>/mark-read/', login_required(views.MarkNotificationReadView.as_view()), name='mark_read'),
    path('mark-all-read/', login_required(views.MarkAllNotificationsReadView.as_view()), name='mark_all_read'),
]
