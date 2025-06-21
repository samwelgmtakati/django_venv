import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_market.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.jobs.models import Order
from apps.orders.models import OrderReview

def test_order_review():
    # Get the first available users and order for testing
    User = get_user_model()
    
    try:
        # Get or create test users
        client = User.objects.filter(is_client=True).first()
        freelancer = User.objects.filter(is_freelancer=True).first()
        
        if not client or not freelancer:
            print("Error: Need at least one client and one freelancer in the database.")
            return
        
        # Get a completed order
        order = Order.objects.filter(
            status=Order.STATUS_COMPLETED,
            client=client,
            freelancer=freelancer
        ).first()
        
        if not order:
            print("Error: No completed order found between the client and freelancer.")
            return
        
        # Create a review
        review = OrderReview.objects.create(
            order=order,
            client=client,
            freelancer=freelancer,
            rating=5,
            comment="Great work! Very professional.",
            is_client_review=True
        )
        
        print(f"Successfully created review: {review}")
        print(f"Client: {review.client}")
        print(f"Freelancer: {review.freelancer}")
        print(f"Rating: {review.rating}/5")
        print(f"Comment: {review.comment}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_order_review()
