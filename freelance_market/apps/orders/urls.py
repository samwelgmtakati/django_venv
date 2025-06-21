from django.urls import path
from . import views

app_name = 'orders'

from .views import (
    OrderListView, OrderDetailView, OrderDeliverView, 
    approve_order, OrderReviewCreateView, RequestRevisionView,
    start_order, PaymentActionView
)

urlpatterns = [
    # Order management
    path("", OrderListView.as_view(), name="list"),
    path("<int:pk>/", OrderDetailView.as_view(), name="detail"),
    
    # Order actions
    path("<int:pk>/deliver/", OrderDeliverView.as_view(), name="deliver"),
    path("<int:pk>/start/", start_order, name="start"),
    path("<int:pk>/approve/", approve_order, name="approve"),
    path("<int:pk>/review/", OrderReviewCreateView.as_view(), name="review"),
    path("<int:pk>/request-revision/", RequestRevisionView.as_view(), name="request_revision"),
    
    # Payment actions
    path(
        "<int:pk>/payment/<str:action>/",
        PaymentActionView.as_view(),
        name="payment_action"
    ),
]