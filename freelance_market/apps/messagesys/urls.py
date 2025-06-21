from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from . import views
from . import views_debug

app_name = 'messages'

urlpatterns = [
    # Inbox - List of all message threads
    path('', login_required(views.inbox), name='inbox'),
    
    # View a specific thread
    path('thread/<int:thread_id>/', login_required(views.thread_detail), name='thread_detail'),
    
    # Start a new message thread
    path('new/', login_required(views.new_thread), name='new_thread'),
    path('new/<int:recipient_id>/', login_required(views.new_thread), name='new_thread_with_recipient'),
    
    # Delete a thread
    path('thread/<int:thread_id>/delete/', login_required(views.delete_thread), name='delete_thread'),
    
    # Mark thread as read
    path('thread/<int:thread_id>/mark-read/', login_required(views.mark_thread_read), name='mark_thread_read'),
    
    # Reply to a thread
    path('thread/<int:thread_id>/reply/', login_required(views.reply_to_thread), name='reply_to_thread'),
    
    # Debug URLs (remove in production)
    path('debug/csrf/', ensure_csrf_cookie(views_debug.debug_csrf), name='debug_csrf'),
    path('debug/post/', views_debug.debug_post, name='debug_post'),
]