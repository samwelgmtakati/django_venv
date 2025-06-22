from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.html import strip_tags

from .models import JobProposal, Notification, ProposalAttachment, Job


@shared_task(bind=True, max_retries=3)
def send_proposal_withdrawn_notification(self, proposal_id, reason=''):
    """
    Send notification to the client when a freelancer withdraws their proposal.
    
    Args:
        proposal_id: ID of the withdrawn proposal
        reason: Optional reason for withdrawal
    """
    try:
        # Get the proposal with related data
        proposal = JobProposal.objects.select_related('job', 'job__client', 'freelancer').get(id=proposal_id)
        
        # Recipient is the job owner (client)
        recipient = proposal.job.client
        
        # Create notification for the client
        notification = Notification.objects.create(
            recipient=recipient,
            actor=proposal.freelancer,
            target=proposal.job,
            verb='withdrew the proposal for',
            description=f"{proposal.freelancer.get_full_name()} has withdrawn their proposal for your job: {proposal.job.title}"
        )
        
        # Send email notification
        subject = f"Proposal Withdrawn: {proposal.freelancer.get_full_name()}"
        
        # Context for the email template
        context = {
            'client_name': recipient.get_full_name() or recipient.username,
            'freelancer_name': proposal.freelancer.get_full_name() or proposal.freelancer.username,
            'job_title': proposal.job.title,
            'job_url': settings.SITE_URL + reverse('jobs:job_detail', args=[proposal.job.slug]),
            'withdraw_reason': reason,
            'site_name': settings.SITE_NAME,
            'contact_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        # Render email content
        html_message = render_to_string('emails/proposal_withdrawn.html', context)
        plain_message = strip_tags(html_message)
        
        # Send the email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Notification sent to {recipient.email}"
    except JobProposal.DoesNotExist as e:
        # Retry if the proposal isn't found (might be a race condition)
        self.retry(countdown=60, exc=e)
    except Exception as e:
        # Log the error and retry
        self.retry(countdown=60, exc=e)


@shared_task
def send_proposal_submitted_notification(proposal_id):
    """
    Send notification to the client when a new proposal is submitted.
    """
    try:
        proposal = JobProposal.objects.select_related('job', 'job__client', 'freelancer').get(id=proposal_id)
        
        # Recipient is the job owner (client)
        recipient = proposal.job.client
        
        # Create notification for the client
        notification = Notification.objects.create(
            recipient=recipient,
            actor=proposal.freelancer,
            target=proposal.job,
            verb='submitted a proposal for',
            description=f"{proposal.freelancer.get_full_name()} has submitted a proposal for your job: {proposal.job.title}"
        )
        
        # Send email notification
        subject = f"New Proposal for {proposal.job.title}"
        
        # Context for the email template
        context = {
            'client_name': recipient.get_full_name() or recipient.username,
            'freelancer_name': proposal.freelancer.get_full_name() or proposal.freelancer.username,
            'job_title': proposal.job.title,
            'proposal_url': settings.SITE_URL + reverse('jobs:proposal_detail', kwargs={'job_slug': proposal.job.slug, 'pk': proposal.id}),
            'site_name': settings.SITE_NAME,
            'contact_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        # Render email content
        html_message = render_to_string('emails/new_proposal.html', context)
        plain_message = strip_tags(html_message)
        
        # Send the email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Notification sent to {recipient.email}"
    except JobProposal.DoesNotExist:
        return "Proposal not found"
    except Exception as e:
        return f"Error sending notification: {str(e)}"


@shared_task(bind=True, max_retries=3)
def send_attachment_deleted_notification(self, attachment_id, filename, proposal_id, job_title, deleted_by_id):
    """
    Send notification when an attachment is deleted from a proposal.
    
    Args:
        attachment_id: ID of the deleted attachment
        filename: Name of the deleted file
        proposal_id: ID of the proposal the attachment belonged to
        job_title: Title of the job
        deleted_by_id: ID of the user who deleted the attachment
    """
    try:
        from django.contrib.auth import get_user_model
        from .models import JobProposal, Notification
        
        User = get_user_model()
        
        # Get the proposal with related data
        proposal = JobProposal.objects.select_related('job', 'job__client', 'freelancer').get(id=proposal_id)
        deleted_by = User.objects.get(id=deleted_by_id)
        
        # Determine the recipient - the other party in the proposal
        if deleted_by == proposal.freelancer:
            recipient = proposal.job.client
            actor = proposal.freelancer
            verb = 'deleted an attachment from their proposal for'
        else:
            recipient = proposal.freelancer
            actor = proposal.job.client
            verb = 'deleted an attachment from the proposal for'
        
        # Create notification
        notification = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            target=proposal.job,
            verb=verb,
            description=f"{actor.get_full_name()} has deleted an attachment from the proposal for {job_title}",
            data={
                'attachment_id': attachment_id,
                'filename': filename,
                'deleted_by': {
                    'id': deleted_by.id,
                    'name': deleted_by.get_full_name() or deleted_by.username
                },
                'job': {
                    'id': proposal.job.id,
                    'title': job_title,
                    'slug': proposal.job.slug
                },
                'proposal_id': proposal_id
            }
        )
        
        # Prepare email context
        context = {
            'recipient_name': recipient.get_full_name() or recipient.username,
            'actor_name': actor.get_full_name() or actor.username,
            'job_title': job_title,
            'filename': filename,
            'proposal_url': f"{settings.SITE_URL}{reverse('jobs:proposal_detail', kwargs={'pk': proposal.id, 'job_slug': proposal.job.slug})}",
            'site_name': settings.SITE_NAME,
            'contact_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        # Render email content
        subject = f"Attachment Deleted: {filename}"
        html_message = render_to_string('emails/attachment_deleted.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Mark notification as sent
        notification.emailed = True
        notification.save(update_fields=['emailed'])
        
        return f"Notification sent to {recipient.email} about deleted attachment {filename}"
        
    except (JobProposal.DoesNotExist, User.DoesNotExist) as e:
        self.retry(countdown=60 * 5, exc=e)  # Retry after 5 minutes
        return f"Proposal or user not found. Retrying..."
    except Exception as e:
        self.retry(countdown=60 * 5, exc=e)  # Retry after 5 minutes
        return f"Error sending notification: {str(e)}"


@shared_task(bind=True, max_retries=3)
def send_new_attachment_notification(self, attachment_id, proposal_id):
    """
    Send notification when a new attachment is added to a proposal.
    
    Args:
        attachment_id: ID of the new attachment
        proposal_id: ID of the proposal the attachment was added to
    """
    try:
        # Get the attachment with related data
        attachment = ProposalAttachment.objects.select_related(
            'proposal', 
            'proposal__job', 
            'proposal__job__client', 
            'proposal__freelancer'
        ).get(id=attachment_id)
        
        proposal = attachment.proposal
        job = proposal.job
        
        # Determine who should be notified (the other party)
        if proposal.freelancer == attachment.uploaded_by:
            # If freelancer uploaded, notify client
            recipient = job.client
            actor = proposal.freelancer
            verb = 'added an attachment to their proposal for'
        else:
            # If client uploaded, notify freelancer
            recipient = proposal.freelancer
            actor = job.client
            verb = 'added an attachment to your proposal for'
        
        # Create notification
        notification = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            target=job,
            verb=verb,
            description=f"{actor.get_full_name()} has added a new attachment to the proposal for job: {job.title}",
            data={
                'attachment_id': str(attachment_id),
                'filename': attachment.filename,
                'proposal_id': str(proposal_id),
                'job_title': job.title,
                'uploaded_by': {
                    'id': str(attachment.uploaded_by.id),
                    'name': attachment.uploaded_by.get_full_name() or attachment.uploaded_by.username,
                    'is_client': attachment.uploaded_by.is_client
                }
            }
        )
        
        # Send email notification
        subject = f"New Attachment: {attachment.filename}"
        
        # Context for the email template
        context = {
            'recipient_name': recipient.get_full_name() or recipient.username,
            'actor_name': actor.get_full_name() or actor.username,
            'job_title': job.title,
            'filename': attachment.filename,
            'file_type': attachment.get_file_type_display(),
            'file_size': attachment.filesize_formatted(),
            'proposal_url': settings.SITE_URL + reverse('jobs:proposal_detail', kwargs={'job_slug': job.slug, 'pk': proposal_id}),
            'site_name': settings.SITE_NAME,
            'contact_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        # Render email content
        html_message = render_to_string('emails/new_attachment.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Mark notification as emailed
        notification.emailed = True
        notification.save(update_fields=['emailed'])
        
        return {
            'status': 'success',
            'notification_id': str(notification.id)
        }
        
    except Exception as e:
        # Log the error and retry
        self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes
        return f"Error sending notification: {str(e)}"
