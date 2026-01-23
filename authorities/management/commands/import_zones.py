"""
Management command to import authority zones from GeoJSON
Usage: python manage.py import_zones <geojson_file> --authority <authority_id>
"""
from django.core.management.base import BaseCommand, CommandError
from authorities.models import Authority, AuthorityZone
import json


class Command(BaseCommand):
    help = 'Import authority zones from a GeoJSON file'

    def add_arguments(self, parser):
        parser.add_argument('geojson_file', type=str, help='Path to GeoJSON file')
        parser.add_argument('--authority', type=int, help='Authority ID to assign zones to')
        parser.add_argument('--authority-name', type=str, help='Authority name (will create if not exists)')

    def handle(self, *args, **options):
        geojson_file = options['geojson_file']
        authority_id = options.get('authority')
        authority_name = options.get('authority_name')

        # Get or create authority
        if authority_id:
            try:
                authority = Authority.objects.get(id=authority_id)
            except Authority.DoesNotExist:
                raise CommandError(f'Authority with ID {authority_id} does not exist')
        elif authority_name:
            authority, created = Authority.objects.get_or_create(
                name=authority_name,
                defaults={'contact_email': f'{authority_name.lower().replace(" ", "")}@example.com'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created authority: {authority.name}'))
        else:
            raise CommandError('Must provide either --authority or --authority-name')

        # Read GeoJSON file
        try:
            with open(geojson_file, 'r') as f:
                geojson_data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'File not found: {geojson_file}')
        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in file: {geojson_file}')

        # Process features
        if geojson_data.get('type') == 'FeatureCollection':
            features = geojson_data.get('features', [])
        elif geojson_data.get('type') == 'Feature':
            features = [geojson_data]
        else:
            raise CommandError('GeoJSON must be a Feature or FeatureCollection')

        created_count = 0
        for feature in features:
            geometry = feature.get('geometry')
            properties = feature.get('properties', {})
            
            if not geometry:
                self.stdout.write(self.style.WARNING('Skipping feature without geometry'))
                continue

            zone_name = properties.get('name', f'Zone {created_count + 1}')
            
            # Create zone
            zone, created = AuthorityZone.objects.get_or_create(
                authority=authority,
                name=zone_name,
                defaults={'polygon_geojson': json.dumps(geometry)}
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created zone: {zone_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Zone already exists: {zone_name}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {created_count} zones for {authority.name}'))
