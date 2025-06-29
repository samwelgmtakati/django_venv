from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'reviews'

urlpatterns = [
    path('order/<int:order_pk>/create/', views.CreateReviewView.as_view(), name='create'),
    path('user/<str:username>/', views.UserReviewsView.as_view(), name='user_reviews'),
]