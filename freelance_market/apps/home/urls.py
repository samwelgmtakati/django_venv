from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    # Home page
    path('', views.home_page, name='home_page'),
    
    # About page
    path('about/', views.about, name='about'),
    
    # Contact page
    path('contact/', views.contact, name='contact'),
    
    # Terms of Service
    path('terms/', views.terms, name='terms'),
    
    # Privacy Policy
    path('privacy/', views.privacy, name='privacy'),
    
    # FAQ
    path('faq/', views.faq, name='faq'),
    
    # How it works
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    
    # For clients
    path('for-clients/', views.for_clients, name='for_clients'),
    
    # For freelancers
    path('for-freelancers/', views.for_freelancers, name='for_freelancers'),
    
    path('testimonials/', views.testimonials, name='testimonials'),
    
    # Blog (if you plan to add a blog later)
    # path('blog/', include('blog.urls')),
]