"""
Import corporator data from CSV into Authority model.

Usage:
  python manage.py import_corporators --csv gwmc_corporators_clean.csv
  python manage.py import_corporators --csv gwmc_corporators_clean.csv --authority-name "GWMC"
"""

import csv
from django.core.management.base import BaseCommand, CommandError
from authorities.models import Authority


class Command(BaseCommand):
    help = 'Import corporator data from CSV file into Authority model'

    def add_arguments(self, parser):
        parser.add_argument('--csv', type=str, required=True, help='Path to CSV file')
        parser.add_argument('--authority-name', type=str, default='GWMC', help='Base name for authorities (default: GWMC)')
        parser.add_argument('--overwrite', action='store_true', help='Overwrite existing authorities with same name')

    def handle(self, *args, **options):
        csv_file = options['csv']
        authority_base_name = options['authority_name']
        overwrite = options['overwrite']

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                corporators = list(reader)
        except FileNotFoundError:
            raise CommandError(f'CSV file not found: {csv_file}')
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {e}')

        if not corporators:
            raise CommandError('CSV file is empty or has no valid data')

        self.stdout.write(f'Found {len(corporators)} corporators in CSV file')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for i, corp in enumerate(corporators, start=1):
            name = corp.get('name', '').strip()
            ward = corp.get('ward', '').strip()
            phone = corp.get('phone', '').strip()
            email = corp.get('email', '').strip()
            address = corp.get('address', '').strip()
            other_info = corp.get('other_info', '').strip()

            if not name:
                self.stdout.write(self.style.WARNING(f'[{i}/{len(corporators)}] Skipping row {i}: No name found'))
                skipped_count += 1
                continue

            # Create authority name: "GWMC - Ward X - Corporator Name" or just "Ward X - Corporator Name"
            if ward:
                authority_name = f"{authority_base_name} - Ward {ward} - {name}"
            else:
                authority_name = f"{authority_base_name} - {name}"

            # Create description from available info
            description_parts = []
            if ward:
                description_parts.append(f"Ward: {ward}")
            if other_info:
                description_parts.append(other_info)
            description = " | ".join(description_parts) if description_parts else f"Corporator for {authority_base_name}"

            # Create contact email if not provided
            if not email:
                # Generate a placeholder email
                email = f"ward{ward}@{authority_base_name.lower()}.gov.in" if ward else f"{name.lower().replace(' ', '.')}@{authority_base_name.lower()}.gov.in"

            # Check if authority already exists
            existing = Authority.objects.filter(name=authority_name).first()

            if existing:
                if overwrite:
                    # Update existing
                    existing.contact_email = email
                    existing.contact_phone = phone
                    existing.description = description
                    existing.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'[{i}/{len(corporators)}] Updated: {authority_name}'))
                else:
                    skipped_count += 1
                    self.stdout.write(self.style.WARNING(f'[{i}/{len(corporators)}] Skipped (exists): {authority_name}'))
            else:
                # Create new
                authority = Authority.objects.create(
                    name=authority_name,
                    contact_email=email,
                    contact_phone=phone,
                    description=description
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'[{i}/{len(corporators)}] Created: {authority_name}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Import Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Updated: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Skipped: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Total: {len(corporators)}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
