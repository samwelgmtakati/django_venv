import os
import sys
import django
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_market.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.jobs.models import Order, Job, JobProposal

User = get_user_model()

def create_test_order():
    try:
        # Get or create test users
        client = User.objects.filter(is_client=True).first()
        freelancer = User.objects.filter(is_freelancer=True).first()
        
        if not client or not freelancer:
            print("Error: Need at least one client and one freelancer in the database.")
            return
        
        # Create a test job
        job = Job.objects.create(
            title="Test Job for Reviews",
            description="This is a test job for reviewing functionality.",
            budget=100.00,
            deadline=datetime.now() + timedelta(days=7),
            status='open',
            client=client
        )
        
        # Create a proposal
        proposal = JobProposal.objects.create(
            job=job,
            freelancer=freelancer,
            bid_amount=100.00,
            status='accepted',
            cover_letter="Test proposal for review testing",
            estimated_days=7  # Add the required estimated_days field
        )
        
        # Create a test order
        order = Order.objects.create(
            job=job,
            client=client,
            freelancer=freelancer,
            proposal=proposal,
            status=Order.STATUS_COMPLETED,
            amount=100.00,
            completed_at=datetime.now()
        )
        
        print(f"Successfully created test order: {order.id}")
        print(f"Client: {client}")
        print(f"Freelancer: {freelancer}")
        
        return order
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    create_test_order()
