from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.jobs.models import JobProposal, Order


@receiver(post_save, sender=JobProposal)
def create_order_when_proposal_accepted(sender, instance: JobProposal, created: bool, **kwargs):
    """Automatically create an Order once a proposal gets accepted."""
    # We only care when the proposal has already existed and its status is now 'accepted'
    if instance.status != 'accepted':
        return

    # Guard against duplicate orders
    if hasattr(instance, 'order') and instance.order:
        return

    Order.objects.create(
        job=instance.job,
        proposal=instance,
        client=instance.job.client,
        freelancer=instance.freelancer,
        status=Order.STATUS_INITIATED,
        created_at=timezone.now(),
    )
