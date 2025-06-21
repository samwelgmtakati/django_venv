from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def home_page(request):
    """
    Render the main landing page.
    """
    context = {
        'title': 'Home - Freelance Market',
        'meta_description': 'Find the perfect freelance services for your business or start offering your skills today.',
    }
    return render(request, 'home/index.html', context)

def about(request):
    """Render the about page."""
    context = {
        'title': 'About Us - Freelance Market',
        'meta_description': 'Learn about our mission, values, and the team behind Freelance Market.',
    }
    return render(request, 'home/about.html', context)

@require_http_methods(['GET', 'POST'])
def contact(request):
    """Handle contact form submissions."""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Send email
        html_message = render_to_string('emails/contact_form.html', {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
        })
        
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                f"New Contact Form: {subject}",
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('home:contact')
        except Exception as e:
            messages.error(request, 'There was an error sending your message. Please try again later.')
    
    context = {
        'title': 'Contact Us - Freelance Market',
        'meta_description': 'Get in touch with our team for any questions or support.',
    }
    return render(request, 'home/contact.html', context)

def terms(request):
    """Render the terms of service page."""
    context = {
        'title': 'Terms of Service - Freelance Market',
        'meta_description': 'Read our terms of service and user agreement.',
    }
    return render(request, 'home/terms.html', context)

def privacy(request):
    """Render the privacy policy page."""
    context = {
        'title': 'Privacy Policy - Freelance Market',
        'meta_description': 'Learn how we protect your privacy and handle your data.',
    }
    return render(request, 'home/privacy.html', context)

def faq(request):
    """Render the FAQ page."""
    faqs = [
        {
            'question': 'How do I hire a freelancer?',
            'answer': 'Simply post a job, review proposals, and award the project to your preferred freelancer.'
        },
        {
            'question': 'How do I get paid as a freelancer?',
            'answer': 'Set up your payment method in your account settings and withdraw your earnings easily.'
        },
        # Add more FAQs as needed
    ]
    
    context = {
        'title': 'Frequently Asked Questions - Freelance Market',
        'meta_description': 'Find answers to common questions about our platform.',
        'faqs': faqs,
    }
    return render(request, 'home/faq.html', context)

def how_it_works(request):
    """Render the how it works page."""
    steps = [
        {
            'title': 'Create an Account',
            'description': 'Sign up as a client or freelancer in just a few minutes.',
            'icon': 'person-plus'
        },
        {
            'title': 'Post or Find Work',
            'description': 'Post your project or browse available jobs and services.',
            'icon': 'search'
        },
        {
            'title': 'Collaborate & Pay Securely',
            'description': 'Work together using our platform and pay securely upon completion.',
            'icon': 'shield-check'
        }
    ]
    
    context = {
        'title': 'How It Works - Freelance Market',
        'meta_description': 'Learn how to get started with Freelance Market.',
        'steps': steps,
    }
    return render(request, 'home/how_it_works.html', context)

def for_clients(request):
    """Render the page for clients."""
    benefits = [
        'Access to top freelance talent',
        'Secure payment system',
        '24/7 customer support',
        'Easy project management tools'
    ]
    
    context = {
        'title': 'For Clients - Freelance Market',
        'meta_description': 'Find and hire top freelance talent for your projects.',
        'benefits': benefits,
    }
    return render(request, 'home/for_clients.html', context)

def for_freelancers(request):
    """Render the page for freelancers."""
    benefits = [
        'Find work that matches your skills',
        'Get paid securely and on time',
        'Build your portfolio',
        'Work with clients worldwide'
    ]
    
    context = {
        'title': 'For Freelancers - Freelance Market',
        'meta_description': 'Find freelance jobs and grow your career.',
        'benefits': benefits,
    }
    return render(request, 'home/for_freelancers.html', context)

def testimonials(request):
    context = {
        'title': 'Testimonials - Freelance Market',
        'meta_description': 'Read success stories from freelancers and businesses using our platform',
    }
    return render(request, 'home/testimonials.html', context)