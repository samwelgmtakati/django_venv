import os
import mimetypes
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Get an instance of a logger
logger = logging.getLogger(__name__)
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.db.models import Q, Count, F, Case, When, Value, IntegerField
from django.utils import timezone
from django.http import JsonResponse, HttpResponse, Http404, FileResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import PermissionDenied, ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .tasks import send_proposal_submitted_notification, send_new_attachment_notification
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect, Http404
from django.db.models import Q, Count, Sum, Case, When, Value, IntegerField
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Import Notification model from notifications app
from apps.notifications.models import Notification
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

from .models import Job, JobCategory, JobProposal, ProposalAttachment
from .forms import ProposalAttachmentForm
from .forms import JobForm, JobFilterForm, JobCategoryForm, ProposalForm
from .serializers import (
    JobSerializer, JobDetailSerializer, JobProposalSerializer,
    JobCategorySerializer, UserSerializer
)
from .permissions import (
    IsOwnerOrReadOnly, IsJobOwner, IsProposalOwner,
    IsClient, IsFreelancer
)

class ClientRequiredMixin(UserPassesTestMixin):
    """Verify that the current user is a client."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_client

class JobOwnerMixin(ClientRequiredMixin):
    """Verify that the current user is the owner of the job."""
    def test_func(self):
        if not super().test_func():
            return False
        job = self.get_object()
        return job.client == self.request.user or self.request.user.is_superuser

class JobListView(LoginRequiredMixin, ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10
    
    def get_queryset(self):
        # Check if this is the freelancer browse view
        is_freelancer_view = getattr(self, 'is_freelancer_view', False) or \
                           self.request.path == reverse('jobs:browse_jobs') or \
                           (hasattr(self, 'kwargs') and self.kwargs.get('is_freelancer_view', False))
        
        # If this is a freelancer viewing jobs, show all published jobs
        if is_freelancer_view and hasattr(self.request.user, 'freelancer'):
            queryset = Job.objects.filter(status='published').order_by('-created_at')
        else:
            # Default: show only the current user's jobs
            queryset = Job.objects.filter(client=self.request.user).order_by('-created_at')
        
        # Handle search
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(requirements__icontains=search_query)
            )
        
        # Handle filters from URL parameters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        job_type = self.request.GET.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)
            
        experience_level = self.request.GET.get('experience_level')
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)
            
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter form for freelancer view
        context['filter_form'] = JobFilterForm(self.request.GET or None)
        
        # Add search query for the template
        context['search_query'] = self.request.GET.get('search', '')
        
        # Add filter parameters for the template
        context['selected_category'] = self.request.GET.get('category')
        context['selected_job_type'] = self.request.GET.get('job_type')
        context['selected_experience'] = self.request.GET.get('experience_level')
        
        return context
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = JobFilterForm(self.request.GET or None)
        context['active_tab'] = 'all'
        return context

class JobDetailView(LoginRequiredMixin, DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        # Allow any authenticated user to view job details
        return Job.objects.all()
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.get_object()
        user = self.request.user
        
        # Add additional context
        context['is_owner'] = job.client == user
        context['can_edit'] = job.can_edit(user)
        
        # Add proposals if user is the job poster
        if context['is_owner']:
            context['proposals'] = job.proposals.select_related('freelancer').all()
        
        # Check if current user has already applied
        if user.is_authenticated and user.is_freelancer:
            context['has_applied'] = job.proposals.filter(freelancer=user).exists()
            
        return context

class JobCreateView(LoginRequiredMixin, ClientRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def form_valid(self, form):
        form.instance.client = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Job created successfully.')
        return response
    
    def get_success_url(self):
        return reverse('jobs:job_detail', kwargs={'slug': self.object.slug})

class JobUpdateView(LoginRequiredMixin, JobOwnerMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_update.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context
    
    def post(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"POST data: {request.POST}")
        
        self.object = self.get_object()
        logger.info(f"Current job status: {self.object.status}")
        
        form = self.get_form()
        logger.info(f"Form is valid: {form.is_valid()}")
        logger.info(f"Form errors: {form.errors if not form.is_valid() else 'None'}")
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_valid(self, form):
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if this is a publish action
        is_publish = 'publish' in self.request.POST
        logger.info(f"Is publish action: {is_publish}")
        
        if is_publish:
            form.instance.status = 'open'
            message = 'Job published successfully and is now visible to freelancers.'
            logger.info("Setting job status to 'open'")
        else:
            message = 'Job updated successfully.'
        
        # Save the job
        self.object = form.save()
        logger.info(f"Job saved with status: {self.object.status}")
        
        # Set success message
        messages.success(self.request, message)
        logger.info(f"Success message set: {message}")
        
        # Redirect to dashboard home
        logger.info("Redirecting to client dashboard")
        return redirect('client_dashboard')
        
    def get_success_url(self):
        # Fallback URL in case form_valid doesn't redirect
        return reverse('dashboard:client_dashboard')

class JobDeleteView(JobOwnerMixin, DeleteView):
    model = Job
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    http_method_names = ['post']  # Only allow POST requests
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse('dashboard:my_projects')  # Updated to use the correct URL name
        self.object.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Project deleted successfully.',
                'redirect': success_url
            })
            
        messages.success(request, 'Project deleted successfully.')
        return redirect(success_url)
    
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class JobCategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all job categories"""
    model = JobCategory
    template_name = 'jobs/category_list.html'
    context_object_name = 'categories'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return JobCategory.objects.all().order_by('name')


class JobCategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new job category"""
    model = JobCategory
    form_class = JobCategoryForm
    template_name = 'jobs/category_form.html'
    success_url = reverse_lazy('jobs:category_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully.')
        return super().form_valid(form)


class JobCategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing job category"""
    model = JobCategory
    form_class = JobCategoryForm
    template_name = 'jobs/category_form.html'
    success_url = reverse_lazy('jobs:category_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully.')
        return super().form_valid(form)


class JobCategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a job category"""
    model = JobCategory
    template_name = 'jobs/category_confirm_delete.html'
    success_url = reverse_lazy('jobs:category_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Category deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ProposalListView(LoginRequiredMixin, ListView):
    """List all proposals for a specific job"""
    model = JobProposal
    template_name = 'jobs/proposal_list.html'
    context_object_name = 'proposals'
    paginate_by = 10
    
    def get_queryset(self):
        job_slug = self.kwargs.get('job_slug')
        self.job = get_object_or_404(Job, slug=job_slug)
        
        # Only job owner can view proposals
        if self.job.client != self.request.user and not self.request.user.is_superuser:
            raise Http404("You don't have permission to view these proposals.")
            
        return JobProposal.objects.filter(job=self.job).select_related('freelancer', 'job')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.job
        context['can_accept_proposals'] = (
            self.job.status == 'published' and 
            not self.job.freelancer and
            self.job.client == self.request.user
        )
        return context


class ProposalDetailView(LoginRequiredMixin, DetailView):
    """View details of a specific proposal"""
    model = JobProposal
    template_name = 'jobs/proposal_detail_new.html'  # Updated template
    context_object_name = 'proposal'
    
    def get_queryset(self):
        # Get the job_slug from URL kwargs
        job_slug = self.kwargs.get('job_slug')
        
        # Only the job owner, proposal owner, or admin can view the proposal
        qs = JobProposal.objects.select_related('job', 'freelancer', 'freelancer__profile')\
                              .prefetch_related('attachments')\
                              .filter(job__slug=job_slug)
        
        if not self.request.user.is_superuser:
            qs = qs.filter(
                Q(job__client=self.request.user) |  # Job owner
                Q(freelancer=self.request.user)     # Proposal owner
            )
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proposal = self.get_object()
        job = proposal.job
        context['job'] = job
        
        # Add job_slug to context for URL reversing
        context['job_slug'] = self.kwargs.get('job_slug')
        
        # User type and permissions
        is_client = self.request.user == job.client
        is_freelancer = self.request.user == proposal.freelancer
        
        # Add similar proposals for client view
        if is_client and proposal.status == 'pending':
            context['similar_proposals'] = JobProposal.objects\
                .filter(job=job, status='pending')\
                .exclude(id=proposal.id)\
                .select_related('freelancer', 'freelancer__profile')\
                .order_by('created_at')[:5]
        
        # Calculate total attachment size
        total_size = sum(attachment.file.size for attachment in proposal.attachments.all())
        context['total_attachment_size'] = total_size
        
        # Add permissions
        context.update({
            'can_accept': (
                is_client and 
                proposal.status == 'pending' and
                not job.freelancer  # No freelancer assigned yet
            ),
            'can_reject': is_client and proposal.status == 'pending',
            'can_withdraw': is_freelancer and proposal.status == 'pending',
            'can_message': is_client or is_freelancer,
            'is_client': is_client,
            'is_freelancer': is_freelancer,
        })
        
        return context


@login_required
@require_http_methods(["POST"])
def accept_proposal(request, job_slug, pk):
    """
    Accept a job proposal and assign the freelancer to the job.
    Rejects all other proposals for this job.
    """
    proposal = get_object_or_404(
        JobProposal.objects.select_related('job', 'freelancer'),
        pk=pk,
        job__slug=job_slug,
        job__client=request.user
    )
    
    # Check if the job is still available
    if proposal.job.status != 'published':
        messages.error(request, 'This job is no longer accepting proposals.')
        return redirect('jobs:job_detail', slug=job_slug)
    
    # Check if the proposal is still pending
    if proposal.status != 'pending':
        messages.warning(request, 'This proposal has already been processed.')
        return redirect('jobs:proposal_detail', job_slug=job_slug, pk=pk)
    
    try:
        with transaction.atomic():
            # Update the proposal status
            proposal.status = 'accepted'
            proposal.responded_at = timezone.now()
            proposal.save(update_fields=['status', 'responded_at', 'updated_at'])
            
            # Update the job status and assign the freelancer
            job = proposal.job
            job.status = 'in_progress'
            job.freelancer = proposal.freelancer
            job.updated_at = timezone.now()
            job.save(update_fields=['status', 'freelancer', 'updated_at'])
            
            # Reject all other proposals for this job
            JobProposal.objects.filter(
                job=job,
                status='pending'
            ).exclude(
                pk=proposal.pk
            ).update(
                status='rejected',
                responded_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            # Create a notification for the freelancer
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=proposal.freelancer,
                title='Proposal Accepted',
                message=f'Your proposal for "{job.title}" has been accepted!',
                url=reverse('jobs:proposal_detail', kwargs={'job_slug': job.slug, 'pk': proposal.pk})
            )
            
            # Send email notification
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = f'Your Proposal for "{job.title}" Has Been Accepted!'
            message = f'''
            Hello {proposal.freelancer.get_full_name() or proposal.freelancer.username},
            
            Great news! Your proposal for "{job.title}" has been accepted by the client.
            
            Project Details:
            - Job: {job.title}
            - Budget: ${proposal.bid_amount}
            - Estimated Duration: {proposal.estimated_days} days
            
            You can now start working on the project. Please communicate with the client through the platform's messaging system.
            
            View your proposal: {request.build_absolute_uri(reverse('jobs:proposal_detail', kwargs={'job_slug': job.slug, 'pk': proposal.pk}))}
            
            Best regards,
            {settings.SITE_NAME} Team
            '''
            
            send_mail(
                subject=subject,
                message=message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[proposal.freelancer.email],
                fail_silently=True
            )
            
            messages.success(
                request,
                f'Proposal accepted! {proposal.freelancer.get_full_name()} has been assigned to this job.'
            )
            
    except Exception as e:
        logger.error(f'Error accepting proposal: {str(e)}')
        messages.error(
            request,
            'An error occurred while processing your request. Please try again.'
        )
        return redirect('jobs:proposal_detail', job_slug=job_slug, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        # Update the proposal status to withdrawn
        proposal.status = 'withdrawn'
        proposal.withdrawn_at = timezone.now()
        proposal.withdraw_reason = reason
        proposal.save(update_fields=['status', 'withdrawn_at', 'withdraw_reason'])
        
        # Decrement the job's proposal count
        Job.objects.filter(pk=proposal.job_id).update(proposal_count=F('proposal_count') - 1)
        
        # Send notification to the job client
        send_proposal_withdrawn_notification.delay(
            proposal_id=proposal.id,
            reason=reason
        )
        
        messages.success(request, 'Your proposal has been withdrawn successfully.')
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Proposal withdrawn successfully.',
                'redirect_url': reverse('jobs:job_detail', kwargs={'slug': proposal.job.slug})
            })
            
        return redirect('jobs:job_detail', slug=proposal.job.slug)
    
    return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.pk)


@login_required
@require_http_methods(["POST"])
def upload_proposal_attachment(request, proposal_id):
    """
    Handle file uploads for a proposal.
    """
    proposal = get_object_or_404(JobProposal, pk=proposal_id)
    
    # Check permissions - only the proposal owner can upload attachments
    if proposal.freelancer != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'error': 'You do not have permission to add attachments to this proposal.'}, 
                status=403
            )
        raise PermissionDenied("You don't have permission to add attachments to this proposal.")
    
    # Check if proposal is still editable
    if proposal.status != 'pending':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'error': 'You can only add attachments to pending proposals.'}, 
                status=400
            )
        messages.error(request, 'You can only add attachments to pending proposals.')
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.pk)
    
    if 'file' not in request.FILES:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No file was uploaded.'}, status=400)
        messages.error(request, 'No file was uploaded.')
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.pk)
    
    # Get the uploaded file
    uploaded_file = request.FILES['file']
    
    # Validate file size (limit to 20MB)
    max_size = 20 * 1024 * 1024  # 20MB
    if uploaded_file.size > max_size:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'error': 'File size exceeds the maximum limit of 20MB.'}, 
                status=400
            )
        messages.error(request, 'File size exceeds the maximum limit of 20MB.')
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.pk)
    
    # Validate file type
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif', 'application/pdf',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain', 'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'
    ]
    
    # Get the file's content type
    content_type = None
    try:
        # Try to get content type from the file itself
        if hasattr(uploaded_file, 'content_type') and uploaded_file.content_type:
            content_type = uploaded_file.content_type
        else:
            # Fall back to mimetypes
            content_type = mimetypes.guess_type(uploaded_file.name)[0]
    except Exception:
        content_type = None
    
    if content_type not in allowed_types:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'error': 'File type not allowed. Please upload a valid document, image, or archive.'}, 
                status=400
            )
        messages.error(request, 'File type not allowed. Please upload a valid document, image, or archive.')
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.pk)
    
    try:
        with transaction.atomic():
            # Create the attachment
            attachment = ProposalAttachment(
                proposal=proposal,
                uploaded_by=request.user,
                original_filename=uploaded_file.name,
                file=uploaded_file,
                file_size=uploaded_file.size,
                content_type=content_type or 'application/octet-stream'
            )
            attachment.save()
            
            # Update the proposal's updated_at timestamp
            JobProposal.objects.filter(pk=proposal.pk).update(updated_at=timezone.now())
            
            # Send notification to the job client about the new attachment
            send_new_attachment_notification.delay(
                attachment_id=attachment.id,
                uploaded_by_id=request.user.id
            )
            
            # Prepare the response data
            response_data = {
                'id': attachment.id,
                'name': attachment.original_filename,
                'size': attachment.file_size,
                'url': attachment.file.url,
                'download_url': reverse('jobs:download_attachment', kwargs={'pk': attachment.id}),
                'is_image': attachment.file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')),
                'preview_url': attachment.file.url if attachment.file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else None,
                'uploaded_at': attachment.uploaded_at.isoformat(),
                'content_type': content_type
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'File uploaded successfully.',
                    'attachment': response_data
                })
            
            messages.success(request, 'File uploaded successfully.')
            return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.pk)
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'error': f'An error occurred while uploading the file: {str(e)}'}, 
                status=500
            )
        messages.error(request, f'An error occurred while uploading the file: {str(e)}')
        return redirect('jobs:proposal_detail', job_slug=proposal.job.slug, pk=proposal.pk)


@login_required
@require_http_methods(["POST"])
def reject_proposal(request, job_slug, pk):
    """
    Reject a job proposal with an optional message.
    """
    proposal = get_object_or_404(
        JobProposal.objects.select_related('job', 'freelancer'),
        pk=pk,
        job__slug=job_slug,
        job__client=request.user
    )
    
    # Check if the proposal is still pending
    if proposal.status != 'pending':
        messages.warning(request, 'This proposal has already been processed.')
        return redirect('jobs:proposal_detail', job_slug=job_slug, pk=pk)
    
    try:
        with transaction.atomic():
            # Update the proposal status
            proposal.status = 'rejected'
            proposal.responded_at = timezone.now()
            proposal.save(update_fields=['status', 'responded_at', 'updated_at'])
            
            # Create a notification for the freelancer
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=proposal.freelancer,
                title='Proposal Not Selected',
                message=f'Your proposal for "{proposal.job.title}" was not selected.',
                url=reverse('jobs:proposal_detail', kwargs={'job_slug': job_slug, 'pk': proposal.pk})
            )
            
            # Send email notification
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = f'Update on Your Proposal for "{proposal.job.title}"'
            message = f'''
            Hello {proposal.freelancer.get_full_name() or proposal.freelancer.username},
            
            We regret to inform you that your proposal for "{proposal.job.title}" was not selected by the client.
            
            Don't be discouraged! There are many other opportunities available. Keep an eye on new job postings that match your skills.
            
            View your proposal: {request.build_absolute_uri(reverse('jobs:proposal_detail', kwargs={'job_slug': job_slug, 'pk': proposal.pk}))}
            
            Best regards,
            {settings.SITE_NAME} Team
            '''
            
            send_mail(
                subject=subject,
                message=message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[proposal.freelancer.email],
                fail_silently=True
            )
            
            messages.success(
                request,
                f'Proposal from {proposal.freelancer.get_full_name()} has been rejected.'
            )
            
    except Exception as e:
        logger.error(f'Error rejecting proposal: {str(e)}')
        messages.error(
            request,
            'An error occurred while processing your request. Please try again.'
        )
    
    return redirect('jobs:proposal_detail', job_slug=job_slug, pk=pk)


@login_required
@require_http_methods(["POST"])
def update_job_status(request, slug):
    job = get_object_or_404(Job, slug=slug)
    
    if request.method == 'POST' and request.user == job.client:
        new_status = request.POST.get('status')
        if new_status in dict(Job.STATUS_CHOICES).keys():
            job.status = new_status
            if new_status == 'published' and not job.published_at:
                job.published_at = timezone.now()
            job.save()
            messages.success(request, f'Job status updated to {job.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    # Redirect back to the previous page or job detail
    return redirect(request.META.get('HTTP_REFERER', 'jobs:job_detail'))


@login_required
def job_publish(request, slug):
    """
    Publish a draft job.
    """
    job = get_object_or_404(Job, slug=slug, client=request.user)
    
    if job.status != 'draft':
        messages.warning(request, 'Only draft jobs can be published.')
        return redirect('dashboard:my_projects')
    
    # Update job status to open
    job.status = 'open'
    job.published_at = timezone.now()
    job.save()
    
    messages.success(request, 'Job has been published successfully and is now visible to freelancers!')
    return redirect('dashboard:my_projects')


@login_required
def job_dashboard(request):
    """Client's job dashboard with comprehensive statistics and recent activity."""
    if not request.user.is_client:
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    # Calculate statistics
    jobs = Job.objects.filter(client=request.user)
    proposals = JobProposal.objects.filter(job__client=request.user)
    
    # Job status counts
    job_status_counts = jobs.values('status').annotate(count=Count('id'))
    status_counts = {item['status']: item['count'] for item in job_status_counts}
    
    # Calculate total spent (sum of all accepted proposal amounts)
    total_spent = proposals.filter(status='accepted').aggregate(
        total=Sum('bid_amount')
    )['total'] or 0
    
    # Get count of hired freelancers (unique freelancers with accepted proposals)
    hired_freelancers = proposals.filter(status='accepted').values('freelancer').distinct().count()
    
    # Prepare stats for the dashboard
    stats = {
        'total_jobs': jobs.count(),
        'active_jobs': status_counts.get('published', 0),
        'draft_jobs': status_counts.get('draft', 0),
        'closed_jobs': status_counts.get('closed', 0),
        'archived_jobs': status_counts.get('archived', 0),
        'total_proposals': proposals.count(),
        'pending_proposals': proposals.filter(status='pending').count(),
        'accepted_proposals': proposals.filter(status='accepted').count(),
        'rejected_proposals': proposals.filter(status='rejected').count(),
        'hired_freelancers': hired_freelancers,
        'total_spent': total_spent,
    }
    
    # Get recent jobs with proposal counts
    recent_jobs = jobs.select_related('category').prefetch_related('proposals').order_by('-created_at')[:5]
    
    # Generate recent activity
    recent_activity = []
    
    # Add job creation activity
    for job in recent_jobs:
        recent_activity.append({
            'title': f'Job Created: {job.title}',
            'description': f'You created a new job posting',
            'time': job.created_at,
            'job': job,
            'icon': 'plus-circle-fill',
            'type': 'job_created'
        })
    
    # Add proposal activity
    recent_proposals = proposals.select_related('job', 'freelancer').order_by('-submitted_at')[:3]
    for proposal in recent_proposals:
        recent_activity.append({
            'title': f'New Proposal from {proposal.freelancer.get_full_name() or proposal.freelancer.username}',
            'description': f'For job: {proposal.job.title}',
            'time': proposal.submitted_at,
            'job': proposal.job,
            'icon': 'envelope',
            'type': 'proposal_received'
        })
    
    # Sort all activities by time (newest first)
    recent_activity.sort(key=lambda x: x['time'], reverse=True)
    recent_activity = recent_activity[:10]  # Limit to 10 most recent activities
    
    # Get job categories for filter
    categories = JobCategory.objects.annotate(
        job_count=Count('job', filter=Q(job__client=request.user))
    ).filter(job_count__gt=0).order_by('-job_count')[:10]
    
    context = {
        'stats': stats,
        'recent_jobs': recent_jobs,
        'recent_activity': recent_activity,
        'categories': categories,
        'active_tab': 'dashboard',
    }
    
    return render(request, 'jobs/job_dashboard.html', context)


class SubmitProposalView(LoginRequiredMixin, CreateView):
    """View for freelancers to submit proposals for jobs"""
    model = JobProposal
    form_class = ProposalForm
    template_name = 'jobs/proposal_submit.html'
    
    def dispatch(self, request, *args, **kwargs):
        logger.debug(f'Dispatching proposal submission request for job: {kwargs.get("slug")}')
        try:
            self.job = get_object_or_404(Job, slug=kwargs.get('slug'), status__in=['published', 'open'])
            logger.debug(f'Found job: {self.job.title} (ID: {self.job.id})')
            
            # Check if user is a freelancer
            if not request.user.is_freelancer:
                logger.warning(f'Non-freelancer user {request.user} attempted to submit a proposal')
                messages.error(request, 'Only freelancers can submit proposals.')
                return redirect('jobs:job_detail', slug=self.job.slug)
                
            # Check if user has already submitted a proposal
            if JobProposal.objects.filter(job=self.job, freelancer=request.user).exists():
                logger.warning(f'User {request.user} already has a proposal for job {self.job.id}')
                messages.warning(request, 'You have already submitted a proposal for this job.')
                return redirect('jobs:job_detail', slug=self.job.slug)
                
            logger.debug('Proceeding with proposal form')
            return super().dispatch(request, *args, **kwargs)
            
        except Exception as e:
            logger.error(f'Error in proposal submission dispatch: {str(e)}', exc_info=True)
            raise
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['job'] = self.job
        kwargs['freelancer'] = self.request.user
        return kwargs
        
    def get_context_data(self, **kwargs):
        logger.debug('Building template context for proposal submission')
        try:
            context = super().get_context_data(**kwargs)
            context['job'] = self.job
            context['active_page'] = 'find_work'  # Set the active page for the sidebar
            
            # Add dashboard context variables
            context['is_client'] = self.request.user.is_client
            context['is_freelancer'] = self.request.user.is_freelancer
            context['is_admin'] = self.request.user.is_superuser
            
            # Add proposal form specific context
            context['max_file_size'] = 10  # MB
            context['max_files'] = 5
            context['allowed_file_types'] = ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
            
            # Set min and max bid amounts based on job type
            if self.job.job_type == 'fixed':
                context['min_bid'] = 5  # Minimum bid amount
                context['max_bid'] = 100000  # Maximum bid amount
            else:
                context['min_bid'] = 3  # Minimum hourly rate
                context['max_bid'] = 1000  # Maximum hourly rate
                
            # Add user profile context
            if hasattr(self.request.user, 'profile'):
                context['user_profile'] = self.request.user.profile
            
            logger.debug(f'Context data: {context.keys()}')
            return context
            
        except Exception as e:
            logger.error(f'Error in get_context_data: {str(e)}', exc_info=True)
            raise
            
    def get_template_names(self):
        template_name = 'jobs/proposal_submit.html'
        logger.debug(f'Looking for template: {template_name}')
        
        # Log all template directories being searched
        from django.template.loader import get_template
        from django.template import engines
        
        for engine in engines.all():
            try:
                template = engine.get_template(template_name)
                logger.debug(f'Found template at: {template.origin}')
            except Exception as e:
                logger.debug(f'Template not found in {engine}: {str(e)}')
        
        return [template_name]
        
    def get(self, request, *args, **kwargs):
        logger.debug('Entering GET method of SubmitProposalView')
        try:
            # Get the response from the parent class
            response = super().get(request, *args, **kwargs)
            logger.debug(f'Response status code: {response.status_code}')
            logger.debug(f'Response content type: {response.get("Content-Type")}')
            
            # Force template rendering by accessing the rendered content
            if hasattr(response, 'render'):
                response.render()
                
            return response
            
        except Exception as e:
            logger.error(f'Error in GET method: {str(e)}', exc_info=True)
            raise
    
    def form_valid(self, form):
        """Handle form validation and file uploads"""
        form.instance.job = self.job
        form.instance.freelancer = self.request.user
        
        # Use transaction to ensure data consistency
        with transaction.atomic():
            # Save the proposal first
            self.object = form.save()
            
            # Handle file uploads
            files = self.request.FILES.getlist('attachments')
            if files:
                for file in files:
                    attachment = ProposalAttachment(
                        proposal=self.object,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        file_type=file.content_type
                    )
                    attachment.save()
            
            # Update job's proposal count
            self.job.proposals_count = F('proposals_count') + 1
            self.job.save(update_fields=['proposals_count', 'updated_at'])
            
            # Send notification to the client
            send_proposal_submitted_notification.delay(self.object.id)
            
            # Create a notification for the client
            Notification.objects.create(
                user=self.job.client,
                title='New Proposal Received',
                message=f"{self.request.user.get_full_name()} has submitted a proposal for your job: {self.job.title}",
                notification_type='proposal_submitted',
                url=reverse('jobs:proposal_detail', kwargs={'job_slug': self.job.slug, 'pk': self.object.pk})
            )
        
        messages.success(self.request, 'Your proposal has been submitted successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirect to the freelancer's proposals list instead of the proposal detail
        messages.success(self.request, 'Your proposal has been submitted successfully!')
        return reverse('dashboard:freelancer_proposals')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.job
        
        # Add job budget information for client-side validation
        if self.job.job_type == 'fixed':
            context['min_bid'] = 1
            context['max_bid'] = self.job.budget * 2 if self.job.budget else 10000
        else:
            # For hourly jobs, use hourly rate range
            context['min_bid'] = self.job.min_hourly_rate or 1
            context['max_bid'] = (self.job.max_hourly_rate or 100) * 2
            
        # Add file upload limits
        context['max_file_size'] = 10  # MB
        context['max_files'] = 5
        context['allowed_file_types'] = [
            '.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.jpg', '.jpeg', '.png'
        ]
        
        return context


class JobListAPIView(generics.ListCreateAPIView):
    """
    API view to list all jobs or create a new job.
    """
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Optionally filter jobs by status, client, or freelancer.
        """
        queryset = Job.objects.all()
        
        # Filter by status if provided
        status = self.request.query_params.get('status', None)
        if status is not None:
            queryset = queryset.filter(status=status)
            
        # Filter by client if provided
        client_id = self.request.query_params.get('client', None)
        if client_id is not None:
            queryset = queryset.filter(client_id=client_id)
            
        # Filter by freelancer if provided
        freelancer_id = self.request.query_params.get('freelancer', None)
        if freelancer_id is not None:
            queryset = queryset.filter(freelancer_id=freelancer_id)
            
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """
        Set the client to the current user when creating a job.
        """
        serializer.save(client=self.request.user)


class JobDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update or delete a job instance.
    """
    queryset = Job.objects.all()
    serializer_class = JobDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """
        Use different serializers for different HTTP methods.
        """
        if self.request.method == 'GET':
            return JobDetailSerializer
        return JobSerializer
    
    def perform_update(self, serializer):
        """
        Add custom update logic here if needed.
        """
        instance = self.get_object()
        if instance.status == 'completed' and 'status' in serializer.validated_data:
            if serializer.validated_data['status'] != 'completed':
                # Don't allow changing status from completed to something else
                serializer.validated_data['status'] = 'completed'
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """
        Custom delete to handle related objects.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class JobProposalViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows job proposals to be viewed or edited.
    """
    serializer_class = JobProposalSerializer
    permission_classes = [permissions.IsAuthenticated, IsProposalOwner]
    
    def get_queryset(self):
        """
        Filter proposals based on the current user's role.
        Clients see proposals for their jobs, freelancers see their own proposals.
        """
        queryset = JobProposal.objects.select_related('job', 'freelancer')
        
        # If user is a client, return proposals for their jobs
        if self.request.user.is_client:
            return queryset.filter(job__client=self.request.user)
        
        # If user is a freelancer, return their own proposals
        if self.request.user.is_freelancer:
            return queryset.filter(freelancer=self.request.user)
        
        # Superusers see all proposals
        if self.request.user.is_superuser:
            return queryset
            
        return queryset.none()
    
    def perform_create(self, serializer):
        """Set the freelancer to the current user when creating a proposal."""
        serializer.save(freelancer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Custom action to accept a proposal."""
        proposal = self.get_object()
        
        # Check permissions
        if proposal.job.client != request.user:
            return Response(
                {"detail": "You don't have permission to accept this proposal."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if the proposal is in a valid state
        if proposal.status != 'submitted':
            return Response(
                {"detail": "This proposal cannot be accepted in its current state."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Update the proposal status
            proposal.status = 'accepted'
            proposal.accepted_at = timezone.now()
            proposal.save()
            
            # Update the job status and assign the freelancer
            job = proposal.job
            job.status = 'in_progress'
            job.freelancer = proposal.freelancer
            job.save()
            
            # Reject all other proposals for this job
            JobProposal.objects.filter(
                job=job,
                status='submitted'
            ).exclude(
                id=proposal.id
            ).update(
                status='rejected',
                rejected_at=timezone.now()
            )
            
            return Response(
                {"detail": "Proposal accepted successfully."},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Custom action to reject a proposal."""
        proposal = self.get_object()
        
        # Check permissions
        if proposal.job.client != request.user:
            return Response(
                {"detail": "You don't have permission to reject this proposal."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if the proposal is in a valid state
        if proposal.status != 'submitted':
            return Response(
                {"detail": "This proposal cannot be rejected in its current state."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the proposal status
        proposal.status = 'rejected'
        proposal.rejected_at = timezone.now()
        proposal.save()
        
        return Response(
            {"detail": "Proposal rejected successfully."},
            status=status.HTTP_200_OK
        )


class JobCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows job categories to be viewed or edited.
    """
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'slug'
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
