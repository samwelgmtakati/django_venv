import os
import django
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_market.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.jobs.models import Job, JobProposal, Order
from apps.orders.models import OrderReview

User = get_user_model()

def create_test_review():
    try:
        print("Starting to create test review...")
        
        # Get or create test users
        client = User.objects.filter(is_client=True).first()
        freelancer = User.objects.filter(is_freelancer=True).first()
        
        if not client or not freelancer:
            print("Error: Need at least one client and one freelancer in the database.")
            return
            
        print(f"Found client: {client}")
        print(f"Found freelancer: {freelancer}")
        
        # Find an existing order that doesn't have a review yet
        orders_without_review = Order.objects.filter(
            status=Order.STATUS_COMPLETED
        ).exclude(
            id__in=OrderReview.objects.values_list('order_id', flat=True)
        ).order_by('id')
        
        if orders_without_review.exists():
            order = orders_without_review.first()
            print(f"Found order without review: {order.id} (Client: {order.client}, Freelancer: {order.freelancer})")
        else:
            print("No orders without reviews found. Looking for any completed order...")
            # If no orders without reviews, try to find any completed order
            completed_orders = Order.objects.filter(status=Order.STATUS_COMPLETED).order_by('id')
            if completed_orders.exists():
                order = completed_orders.first()
                print(f"Found completed order: {order.id} (may already have a review)")
            else:
                print("No completed orders found. Please complete an order first.")
                return
        
        # Check if this order already has a review
        if hasattr(order, 'review'):
            print(f"Order {order.id} already has a review (ID: {order.review.id}). Using existing review.")
            review = order.review
        else:
            # Create a new review
            review = OrderReview.objects.create(
                order=order,
                client=order.client,
                freelancer=order.freelancer,
                rating=5,
                comment="Test review created by the system.",
                is_client_review=True
            )
            print(f"Created new review for order {order.id}")
        print(f"Created test review: {review.id}")
        
        # Verify the review was created correctly
        print("\nReview details:")
        print(f"Order: {review.order}")
        print(f"Client: {review.client}")
        print(f"Freelancer: {review.freelancer}")
        print(f"Rating: {review.rating}/5")
        print(f"Comment: {review.comment}")
        print(f"Is client review: {review.is_client_review}")
        
        return review
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_review()
