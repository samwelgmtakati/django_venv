from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Max
from django.core.paginator import Paginator

from .models import Thread, Message
from .forms import MessageForm, NewThreadForm
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def inbox(request):
    """Display all message threads for the current user."""
    # Get all threads where the current user is a participant
    user_threads = Thread.objects.filter(
        participants=request.user
    ).annotate(
        last_message=Max('messages__sent_at')
    ).order_by('-last_message')
    
    # Get unread counts for each thread
    for thread in user_threads:
        thread.unread_count = Message.objects.filter(
            thread=thread,
            recipient=request.user,
            read_at__isnull=True
        ).count()
    
    context = {
        'threads': user_threads
    }
    return render(request, 'messages/inbox.html', context)

@login_required
def thread_detail(request, thread_id):
    """Display a single message thread."""
    thread = get_object_or_404(Thread, id=thread_id, participants=request.user)
    
    # Mark messages as read when viewing the thread
    Message.objects.filter(
        thread=thread,
        recipient=request.user,
        read_at__isnull=True
    ).update(read_at=timezone.now())
    
    # Get all messages in the thread
    message_list = thread.messages.all().select_related('sender')
    
    # Handle message form submission
    if request.method == 'POST':
        form = MessageForm(request.POST, thread=thread, sender=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.thread = thread
            message.sender = request.user
            # Set recipient as the other participant in the thread
            other_participants = thread.participants.exclude(id=request.user.id)
            if other_participants.exists():
                message.recipient = other_participants.first()
            message.save()
            return redirect('messages:thread_detail', thread_id=thread.id)
    else:
        form = MessageForm(thread=thread, sender=request.user)
    
    context = {
        'thread': thread,
        'messages': message_list,
        'form': form,
    }
    return render(request, 'messages/thread_detail.html', context)

@login_required
def new_thread(request, recipient_id=None):
    """Start a new message thread with another user."""
    recipient = None
    job_id = request.GET.get('job')
    proposal_id = request.GET.get('proposal')
    
    # Get recipient if ID is provided
    if recipient_id:
        recipient = get_object_or_404(User, id=recipient_id)
    
    # Initialize form with sender and context
    form_kwargs = {'sender': request.user}
    
    # Add job or proposal context if provided
    if job_id:
        from apps.jobs.models import Job
        job = get_object_or_404(Job, id=job_id)
        form_kwargs['job'] = job
        if not recipient:
            recipient = job.client
    elif proposal_id:
        from apps.proposals.models import Proposal
        proposal = get_object_or_404(Proposal, id=proposal_id)
        form_kwargs['proposal'] = proposal
        if not recipient:
            recipient = proposal.freelancer
    elif recipient:
        form_kwargs['recipient'] = recipient
    
    if request.method == 'POST':
        form = NewThreadForm(request.POST, **form_kwargs)
        
        if form.is_valid():
            thread = form.save()

            return redirect('messages:thread_detail', thread_id=thread.id)
    else:
        # Set initial subject if we have a recipient
        initial = {}
        if recipient:
            initial['subject'] = f"Re: {recipient.get_full_name() or recipient.username}"
        
        # If we have job or proposal, include their titles in the subject
        if 'job' in form_kwargs and form_kwargs['job']:
            initial['subject'] = f"Re: {form_kwargs['job'].title}"
        elif 'proposal' in form_kwargs and form_kwargs['proposal']:
            initial['subject'] = f"Re: {form_kwargs['proposal'].job.title} - Proposal"
            
        form = NewThreadForm(initial=initial, **form_kwargs)
    
    # Get all users except the current user for the recipient dropdown
    users = User.objects.exclude(pk=request.user.pk).select_related('profile')
    
    context = {
        'form': form,
        'recipient': recipient,
        'users': users,
        'job': form_kwargs.get('job'),
        'proposal': form_kwargs.get('proposal'),
    }
    return render(request, 'messages/new_thread.html', context)

@login_required
def mark_thread_read(request, thread_id):
    """Mark a thread as read for the current user."""
    thread = get_object_or_404(Thread, id=thread_id, participants=request.user)
    
    # Mark all unread messages in this thread as read for the current user
    thread.messages.filter(recipient=request.user, read_at__isnull=True).update(read_at=timezone.now())
    
    # Redirect back to the thread detail page
    return redirect('messages:thread_detail', thread_id=thread.id)


@login_required
def reply_to_thread(request, thread_id):
    """Reply to a message thread."""
    thread = get_object_or_404(Thread, id=thread_id, participants=request.user)
    
    # Get the other participant(s) in the thread
    other_participants = thread.participants.exclude(id=request.user.id)
    recipient = other_participants.first()  # For 1:1 messages, there should be only one other participant
    
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES, thread=thread, sender=request.user, recipient=recipient)
        
        if form.is_valid():
            try:
                message = form.save()

                return redirect('messages:thread_detail', thread_id=thread.id)
            except Exception as e:
                messages.error(request, _('An error occurred while sending your reply. Please try again.'))
                logger.exception("Error sending reply")
    else:
        form = MessageForm(thread=thread, sender=request.user, recipient=recipient)
    
    context = {
        'thread': thread,
        'form': form,
    }
    return render(request, 'messages/thread_detail.html', context)


@login_required
def delete_thread(request, thread_id):
    """Delete a message thread."""
    thread = get_object_or_404(Thread, id=thread_id, participants=request.user)
    
    if request.method == 'POST':
        thread.delete()

        return redirect('messages:inbox')
    
    context = {'thread': thread}
    return render(request, 'messages/confirm_delete_thread.html', context)
