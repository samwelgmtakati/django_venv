import random
import sys
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.files import File
from faker import Faker
import requests
from io import BytesIO

# Add the project directory to the Python path
project_root = str(Path(__file__).resolve().parents[5])
if project_root not in sys.path:
    sys.path.append(project_root)

from apps.freelancer.models import Freelancer, Skill
from apps.accounts.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with sample data for development and testing'
    
    def add_arguments(self, parser):
        parser.add_argument('--freelancers', type=int, default=10, help='Number of freelancers to create')
        parser.add_argument('--clients', type=int, default=10, help='Number of clients to create')
        parser.add_argument('--skills', type=int, default=30, help='Number of skills to create')
    
    def create_skills(self, num_skills):
        """Create sample skills if they don't exist."""
        self.stdout.write('Checking/creating skills...')
        skills = []
        skill_names = [
            'Python', 'Django', 'JavaScript', 'React', 'Vue.js', 'Node.js', 
            'HTML', 'CSS', 'PostgreSQL', 'MongoDB', 'Docker', 'AWS', 
            'GraphQL', 'REST API', 'UI/UX Design', 'Mobile Development', 
            'iOS', 'Android', 'Flutter', 'React Native', 'Data Science',
            'Machine Learning', 'DevOps', 'Cybersecurity', 'Blockchain', 
            'Cloud Computing'
        ][:num_skills]
        
        for name in skill_names:
            skill, created = Skill.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower().replace(' ', '-')}
            )
            if created:
                skills.append(skill)
                self.stdout.write(f'Created skill: {name}')
            else:
                skills.append(skill)
        
        self.stdout.write(f'Total skills available: {len(skills)}')
        return skills
        
    def create_admin_user(self):
        """Create admin user if it doesn't exist."""
        if not User.objects.filter(username='admin').exists():
            with transaction.atomic():
                admin = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    is_admin=True,
                    is_staff=True,
                    is_superuser=True
                )
                if not hasattr(admin, 'profile'):
                    UserProfile.objects.create(user=admin)
                self.stdout.write(self.style.SUCCESS('Created admin user (username: admin, password: admin123)'))
        else:
            self.stdout.write('Admin user already exists')
    
    def create_freelancers(self, num_freelancers, skills):
        """Create freelancer users with profiles."""
        fake = Faker()
        existing_count = Freelancer.objects.count()
        
        if existing_count >= num_freelancers:
            self.stdout.write(f'Already have {existing_count} freelancers. No new freelancers created.')
            return
            
        new_freelancers_needed = num_freelancers - existing_count
        self.stdout.write(f'Creating {new_freelancers_needed} new freelancers...')
        
        for i in range(new_freelancers_needed):
            is_freelancer = True
            is_client = False
            
            try:
                with transaction.atomic():
                    # Create user with predictable username
                    user_num = Freelancer.objects.count() + 1
                    username = f"freelancer{user_num}"
                    email = f"{username}@example.com"
                    
                    # Create user with basic info and profile picture
                    user = User(
                        username=username,
                        email=email,
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        is_freelancer=True,
                        is_client=False
                    )
                    
                    # Set a default profile picture
                    try:
                        # Try to get a random avatar from a placeholder service
                        response = requests.get(f'https://i.pravatar.cc/300?img={random.randint(1, 70)}')
                        if response.status_code == 200:
                            # Create a file-like object from the response content
                            img_io = BytesIO(response.content)
                            img_io.name = f'{username}.jpg'
                            # Save the file to the user's profile_picture field
                            user.profile_picture.save(f'{username}.jpg', File(img_io), save=False)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Could not fetch profile picture: {str(e)}'))
                    
                    # Set password and save
                    user.set_password('password123')
                    user.save()
                    
                    # Create or update user profile
                    UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'bio': fake.paragraph(),
                            'location': f"{fake.city()}, {fake.country()}",
                            'website': fake.url()
                        }
                    )
                    
                    # Create freelancer profile
                    freelancer, created = Freelancer.objects.get_or_create(
                        user=user,
                        defaults={
                            'title': fake.job(),
                            'bio': '\n\n'.join(fake.paragraphs(nb=2)),
                            'hourly_rate': random.choice([20, 30, 40, 50, 60, 70, 80, 100, 120, 150]),
                            'experience_years': random.randint(1, 20),
                            'education': fake.sentence(),
                            'portfolio_website': fake.url(),
                            'is_available': random.choice([True, False] * 3 + [True])  # 75% chance of being available
                        }
                    )
                    
                    # Add random skills to freelancer if it's a new profile
                    if created and skills:
                        num_skills = random.randint(2, min(5, len(skills)))
                        freelancer_skills = random.sample(skills, num_skills)
                        freelancer.skills.set(freelancer_skills)
                    
                    self.stdout.write(self.style.SUCCESS(f'Created/updated freelancer: {user.username}'))
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating freelancer: {str(e)}'))
                continue
    
    def create_clients(self, num_clients):
        """Create client users."""
        fake = Faker()
        existing_count = User.objects.filter(is_client=True).count()
        
        if existing_count >= num_clients:
            self.stdout.write(f'Already have {existing_count} clients. No new clients created.')
            return
            
        new_clients_needed = num_clients - existing_count
        self.stdout.write(f'Creating {new_clients_needed} new clients...')
        
        for i in range(new_clients_needed):
            try:
                with transaction.atomic():
                    # Create user with predictable username
                    user_num = User.objects.filter(is_client=True).count() + 1
                    username = f"client{user_num}"
                    email = f"{username}@example.com"
                    
                    # Create user with basic info and profile picture
                    user = User(
                        username=username,
                        email=email,
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        is_freelancer=False,
                        is_client=True
                    )
                    
                    # Set a default profile picture
                    try:
                        # Try to get a random avatar from a placeholder service
                        response = requests.get(f'https://i.pravatar.cc/300?img={random.randint(1, 70)}')
                        if response.status_code == 200:
                            # Create a file-like object from the response content
                            img_io = BytesIO(response.content)
                            img_io.name = f'{username}.jpg'
                            # Save the file to the user's profile_picture field
                            user.profile_picture.save(f'{username}.jpg', File(img_io), save=False)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Could not fetch profile picture: {str(e)}'))
                    
                    # Set password and save
                    user.set_password('password123')
                    user.save()
                    
                    # Create or update user profile
                    UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'bio': fake.paragraph(),
                            'location': f"{fake.city()}, {fake.country()}",
                            'website': fake.url()
                        }
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f'Created client: {user.username}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating client: {str(e)}'))
                continue
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        try:
            # Create skills
            skills = self.create_skills(options['skills'])
            
            # Create admin user
            self.create_admin_user()
            
            # Create freelancers and clients
            self.create_freelancers(options['freelancers'], skills)
            self.create_clients(options['clients'])
            
            self.stdout.write(
                self.style.SUCCESS('\nSeed data created successfully!\n')
            )
            self.stdout.write(
                'You can log in with:\n'
                'Admin: username=admin, password=admin123\n'
                'Users: username=<username>, password=password123'
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            if hasattr(e, '__traceback__'):
                import traceback
                traceback.print_exc()
        
        self.stdout.write(
            'You can log in with:\n'
            'Admin: username=admin, password=admin123\n'
            'Users: username=<username>, password=password123'
        )
