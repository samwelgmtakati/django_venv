import os
import mimetypes
from urllib.parse import quote

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, Http404, FileResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.db import transaction, models
from django.urls import reverse
from django.utils import timezone
from django.db.models import F

from .models import JobProposal, ProposalAttachment, Job, Notification
from .tasks import send_proposal_withdrawn_notification, send_attachment_deleted_notification
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db import transaction
from .models import JobProposal, Notification
from .forms import ProposalForm

class EditProposalView(LoginRequiredMixin, UpdateView):
    """
    View for freelancers to edit their pending proposals.
    """
    model = JobProposal
    form_class = ProposalForm
    template_name = 'jobs/proposal_edit.html'
    context_object_name = 'proposal'
    
    def get_queryset(self):
        # Only allow editing of pending proposals
        return JobProposal.objects.filter(
            freelancer=self.request.user.freelancer,
            status=JobProposal.STATUS_PENDING
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.object.job
        return context
    
    def form_valid(self, form):
        if form.instance.status != JobProposal.STATUS_PENDING:
            messages.error(
                self.request,
                'Only pending proposals can be edited.'
            )
            return self.form_invalid(form)
            
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Your proposal has been updated successfully.'
        )
        return response
    
    def get_success_url(self):
        return reverse_lazy(
            'jobs:proposal_detail',
            kwargs={
                'job_slug': self.object.job.slug,
                'pk': self.object.pk
            }
        )

@login_required
@require_http_methods(["POST"])
def withdraw_proposal(request, pk):
    """
    Allow freelancers to withdraw their proposal.
    
    This view handles both AJAX and regular form submissions. It updates the proposal status,
    creates notifications, and sends email alerts to the client.
    """
    proposal = get_object_or_404(
        JobProposal.objects.select_related('job', 'job__client', 'freelancer'),
        id=pk
    )
    
    # Check if the current user is the owner of the proposal
    if request.user != proposal.freelancer:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'message': 'You do not have permission to withdraw this proposal.'},
                status=403
            )
        messages.error(request, 'You do not have permission to withdraw this proposal.')
        return redirect('jobs:job_detail', slug=proposal.job.slug)
    
    # Check if the proposal can be withdrawn (only pending proposals can be withdrawn)
    if proposal.status != JobProposal.STATUS_PENDING:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'message': 'This proposal cannot be withdrawn as it is no longer pending.'},
                status=400
            )
        messages.error(request, 'This proposal cannot be withdrawn as it is no longer pending.')
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.id)
    
    # Get the reason for withdrawal if provided
    reason = request.POST.get('reason', '').strip()
    
    try:
        with transaction.atomic():
            # Update the proposal status
            proposal.status = JobProposal.STATUS_WITHDRAWN
            proposal.withdrawn_at = timezone.now()
            proposal.save(update_fields=['status', 'withdrawn_at', 'updated_at'])
            
            # Decrement the job's proposal count
            proposal.job.proposals_count = max(0, proposal.job.proposals_count - 1)
            proposal.job.save(update_fields=['proposals_count', 'updated_at'])
            
            # Create a notification for the client
            Notification.objects.create(
                recipient=proposal.job.client,
                actor=request.user,
                target=proposal.job,
                verb='withdrew the proposal for',
                description=f"{request.user.get_full_name()} has withdrawn their proposal for your job: {proposal.job.title}",
                notification_type='proposal_withdrawn',
                extra_data={'reason': reason} if reason else None
            )
            
            # Send email notification asynchronously
            send_proposal_withdrawn_notification.delay(proposal.id, reason)
            
            # Prepare success response
            success_message = 'Your proposal has been successfully withdrawn.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'redirect_url': reverse('jobs:job_detail', kwargs={'slug': proposal.job.slug})
                })
            
            messages.success(request, success_message)
            return redirect('jobs:job_detail', slug=proposal.job.slug)
            
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error withdrawing proposal {pk}: {str(e)}", exc_info=True)
        
        error_message = 'An error occurred while withdrawing the proposal. Please try again.'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'message': error_message},
                status=500
            )
        messages.error(request, error_message)
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.id)


@login_required
@require_http_methods(["POST"])
def delete_attachment(request, pk):
    """
    Handle deletion of a proposal attachment.
    Only the uploader can delete the attachment, and only if the proposal is still pending.
    """
    attachment = get_object_or_404(ProposalAttachment, pk=pk)
    proposal = attachment.proposal
    
    # Check if the current user is the uploader of the attachment
    if request.user != attachment.uploaded_by:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'message': 'You do not have permission to delete this attachment.'},
                status=403
            )
        messages.error(request, 'You do not have permission to delete this attachment.')
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.id)
    
    # Only allow deletion if the proposal is still pending
    if proposal.status != JobProposal.STATUS_PENDING:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'message': 'Attachments can only be deleted from pending proposals.'},
                status=400
            )
        messages.error(request, 'Attachments can only be deleted from pending proposals.')
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.id)
    
    try:
        with transaction.atomic():
            # Store attachment info for notification before deletion
            attachment_info = {
                'attachment_id': attachment.id,
                'filename': attachment.original_filename,
                'proposal_id': proposal.id,
                'job_title': proposal.job.title,
                'deleted_by_id': request.user.id
            }
            
            # Delete the file from storage
            attachment.file.delete(save=False)
            
            # Delete the attachment record
            attachment_id = attachment.id
            attachment.delete()
            
            # Send notification to the other party
            send_attachment_deleted_notification.delay(**attachment_info)
            
            # Create a notification for the uploader
            if request.user == proposal.freelancer:
                recipient = proposal.job.client
                verb = 'deleted an attachment from their proposal for'
            else:
                recipient = proposal.freelancer
                verb = 'deleted an attachment from your proposal for'
            
            Notification.objects.create(
                recipient=recipient,
                actor=request.user,
                target=proposal.job,
                verb=verb,
                description=f"{request.user.get_full_name()} {verb} '{proposal.job.title}'",
                data={
                    'attachment_id': attachment_id,
                    'filename': attachment_info['filename'],
                    'proposal_id': proposal.id,
                    'job_title': proposal.job.title,
                    'job_slug': proposal.job.slug
                }
            )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Attachment deleted successfully.',
                    'attachment_id': attachment_id
                })
            
            messages.success(request, 'Attachment deleted successfully.')
            return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.id)
            
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'message': f'An error occurred: {str(e)}'},
                status=500
            )
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.id)


@login_required
@require_http_methods(["POST"])
@csrf_exempt  # Only for demo - remove in production and use proper CSRF handling
def download_attachment(request, pk):
    """
    Download a proposal attachment.
    Only the job poster or the proposal owner can download attachments.
    """
    from .models import ProposalAttachment
    
    attachment = get_object_or_404(
        ProposalAttachment.objects.select_related('proposal__job', 'proposal__freelancer'),
        pk=pk
    )
    
    # Check permissions
    user = request.user
    proposal = attachment.proposal
    
    if not (user == proposal.freelancer or user == proposal.job.client or user.is_staff):
        messages.error(request, "You don't have permission to download this file.")
        return redirect('jobs:job_detail', slug=proposal.job.slug)
    
    # Track the download (you might want to log this)
    # attachment.downloads += 1
    # attachment.save(update_fields=['downloads'])
    
    # Serve the file for download
    response = FileResponse(attachment.file)
    response['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
    return response
