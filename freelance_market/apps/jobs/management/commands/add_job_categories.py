from django.core.management.base import BaseCommand
from apps.jobs.models import JobCategory

class Command(BaseCommand):
    help = 'Adds default job categories to the database'

    def handle(self, *args, **options):
        categories = [
            'Web Development',
            'Mobile Development',
            'Graphic Design',
            'Content Writing',
            'Digital Marketing',
            'Video & Animation',
            'Music & Audio',
            'Programming & Tech',
            'Business',
            'Lifestyle',
            'Data Science & Analytics',
            'Photography',
            'Social Media Management',
            'Translation',
            'Legal',
            'Accounting & Consulting',
            'Customer Service',
            'Sales & Marketing',
            'Writing & Translation',
            'Admin Support',
            'Engineering & Architecture',
            'IT & Networking',
            'Game Development',
            'AI Services',
            'Blockchain & Cryptocurrency'
        ]

        created_count = 0
        for category_name in categories:
            category, created = JobCategory.objects.get_or_create(name=category_name)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {category_name}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} new categories. Total categories: {JobCategory.objects.count()}'))
