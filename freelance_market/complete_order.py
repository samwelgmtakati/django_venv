import os
import django
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_market.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.jobs.models import Order

def complete_order(order_id=None):
    """Mark an order as completed."""
    try:
        # If no order_id is provided, find the most recent order that can be completed
        if order_id is None:
            order = Order.objects.exclude(status=Order.STATUS_COMPLETED).order_by('-id').first()
            if order is None:
                print("No incomplete orders found.")
                return
        else:
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                print(f"Order with ID {order_id} does not exist.")
                return
        
        # Update the order status to completed
        order.status = Order.STATUS_COMPLETED
        order.completed_at = datetime.now()
        order.save(update_fields=['status', 'completed_at', 'updated_at'])
        
        print(f"Order {order.id} has been marked as completed.")
        print(f"Client: {order.client}")
        print(f"Freelancer: {order.freelancer}")
        print(f"Amount: {order.amount} TZS")
        
        return order
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        order_id = int(sys.argv[1])
        complete_order(order_id)
    else:
        complete_order()
