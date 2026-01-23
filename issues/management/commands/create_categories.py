"""
Management command to create initial issue categories
"""
from django.core.management.base import BaseCommand
from issues.models import IssueCategory


class Command(BaseCommand):
    help = 'Create initial issue categories'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Road Issues', 'icon': '🛣️', 'description': 'Potholes, road damage, traffic issues'},
            {'name': 'Street Lights', 'icon': '💡', 'description': 'Broken or non-functional street lights'},
            {'name': 'Garbage', 'icon': '🗑️', 'description': 'Garbage collection issues, overflowing bins'},
            {'name': 'Water Supply', 'icon': '💧', 'description': 'Water supply problems, leaks, quality issues'},
            {'name': 'Sewage', 'icon': '🚰', 'description': 'Sewage problems, drainage issues'},
            {'name': 'Parks & Recreation', 'icon': '🌳', 'description': 'Park maintenance, playground equipment'},
            {'name': 'Public Safety', 'icon': '🚨', 'description': 'Safety concerns, crime, emergencies'},
            {'name': 'Other', 'icon': '📋', 'description': 'Other civic issues'},
        ]
        
        created_count = 0
        for cat_data in categories:
            category, created = IssueCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'description': cat_data['description']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {category.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} categories'))
