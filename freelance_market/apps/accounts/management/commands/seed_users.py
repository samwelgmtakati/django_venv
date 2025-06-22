from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates freelancers and clients with specific username patterns'

    def add_arguments(self, parser):
        parser.add_argument('--freelancers', type=int, default=10,
                          help='Number of freelancers to create (default: 10)')
        parser.add_argument('--clients', type=int, default=5,
                          help='Number of clients to create (default: 5)')

    def handle(self, *args, **options):
        fake = Faker()
        freelancer_count = options['freelancers']
        client_count = options['clients']
        
        # Common first and last names for more realistic data
        first_names = [fake.unique.first_name() for _ in range(100)]
        last_names = [fake.unique.last_name() for _ in range(100)]
        
        with transaction.atomic():
            # Create freelancers
            created_freelancers = 0
            for i in range(1, freelancer_count + 1):
                username = f'freelancer{i}'
                email = f'{username}@example.com'
                
                # Skip if user with this username or email already exists
                if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                    self.stdout.write(self.style.WARNING(f'Skipping duplicate freelancer: {username}'))
                    continue
                
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='password123',
                        first_name=random.choice(first_names),
                        last_name=random.choice(last_names),
                        is_freelancer=True,
                        is_active=True
                    )
                    created_freelancers += 1
                    
                    # Create profile for the user
                    self.create_user_profile(user, fake)
                    
                    self.stdout.write(self.style.SUCCESS(f'Created freelancer: {username} (password: password123)'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating freelancer {username}: {e}'))
            
            # Create clients
            created_clients = 0
            for i in range(1, client_count + 1):
                username = f'client{i}'
                email = f'{username}@example.com'
                
                # Skip if user with this username or email already exists
                if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                    self.stdout.write(self.style.WARNING(f'Skipping duplicate client: {username}'))
                    continue
                
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='password123',
                        first_name=random.choice(first_names),
                        last_name=random.choice(last_names),
                        is_client=True,
                        is_active=True
                    )
                    created_clients += 1
                    
                    # Create profile for the user
                    self.create_user_profile(user, fake)
                    
                    self.stdout.write(self.style.SUCCESS(f'Created client: {username} (password: password123)'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating client {username}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {created_freelancers} freelancers and {created_clients} clients\n'
            'All users have the password: password123'
        ))
    
    def create_user_profile(self, user, fake):
        """Create a user profile with realistic fake data."""
        from apps.accounts.models import UserProfile
        
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.bio = fake.paragraph(nb_sentences=3)
        profile.location = fake.city() + ', ' + fake.country()
        profile.website = fake.url()
        
        # Add phone number to user
        user.phone_number = f"+1{fake.msisdn()[:10]}"
        user.save()
        
        profile.save()
        return profile
