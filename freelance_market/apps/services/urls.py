from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.FreelancerServiceListView.as_view(), name='service_list'),
    path('new/', views.ServiceCreateView.as_view(), name='service_create'),
    path('<int:pk>/edit/', views.ServiceUpdateView.as_view(), name='service_edit'),
    path('<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),
]