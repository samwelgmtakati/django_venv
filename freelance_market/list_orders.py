import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_market.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.jobs.models import Order, JobProposal
from apps.orders.models import OrderReview

def list_orders_and_proposals():
    print("=== Orders ===")
    orders = Order.objects.all().order_by('-id')[:10]  # Get last 10 orders
    for order in orders:
        print(f"ID: {order.id}, Status: {order.status}, Client: {order.client}, Freelancer: {order.freelancer}, Proposal: {order.proposal_id}")
    
    print("\n=== Proposals ===")
    proposals = JobProposal.objects.all().order_by('-id')[:10]  # Get last 10 proposals
    for proposal in proposals:
        print(f"ID: {proposal.id}, Job: {proposal.job_id}, Freelancer: {proposal.freelancer}, Status: {proposal.status}")
    
    print("\n=== Reviews ===")
    reviews = OrderReview.objects.all().order_by('-id')[:10]  # Get last 10 reviews
    for review in reviews:
        print(f"ID: {review.id}, Order: {review.order_id}, Client: {review.client}, Freelancer: {review.freelancer}, Rating: {review.rating}")

if __name__ == "__main__":
    list_orders_and_proposals()
