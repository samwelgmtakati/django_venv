from django.urls import path
from . import views

app_name = 'freelancer'

urlpatterns = [
    # Profile management
    path('profile/', views.FreelancerProfileView.as_view(), name='profile'),
    path('profile/create/', views.FreelancerCreateView.as_view(), name='create_profile'),
    path('profile/edit/', views.FreelancerUpdateView.as_view(), name='edit_profile'),
    path('profile/delete/', views.FreelancerDeleteView.as_view(), name='delete_profile'),
    
    # Skills management
    path('skills/', views.SkillListView.as_view(), name='skills'),
    path('skills/add/', views.SkillAddView.as_view(), name='add_skill'),
    path('skills/remove/', views.SkillDeleteView.as_view(), name='remove_skill'),
    path('skills/create/', views.SkillCreateView.as_view(), name='create_skill'),
    
    # Public profile
    path('<str:username>/', views.PublicProfileView.as_view(), name='public_profile'),
    
    # AJAX endpoints
    path('api/toggle-availability/', views.toggle_availability, name='toggle_availability'),
]