import os
import re
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from core.models import Commodity, PriceEntry, Location

class Command(BaseCommand):
    help = 'Imports sample data from the frontend AppContext.js file'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before importing')
        parser.add_argument('--file', type=str, default='../../Zameen-Zarien/context/AppContext.js', help='Path to AppContext.js file')
        parser.add_argument('--days', type=int, default=7, help='Number of days of price history to generate')
        parser.add_argument('--debug', action='store_true', help='Print debug information')

    def handle(self, *args, **options):
        # Check if we should clear existing data
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            PriceEntry.objects.all().delete()
            Location.objects.all().delete()
            Commodity.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        # Get the path to the AppContext.js file
        file_path = options['file']
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract commodities data
        commodities_match = re.search(r'const\s+sampleCommodities\s*=\s*\[(.*?)\];', content, re.DOTALL)
        if not commodities_match:
            self.stdout.write(self.style.ERROR('Could not find sampleCommodities in the file'))
            return

        commodities_data = commodities_match.group(1)
        commodity_items = re.findall(r'\{\s*id:\s*(\d+),\s*name:\s*"([^"]+)",\s*name_ur:\s*"([^"]+)"\s*\}', commodities_data)

        # Extract locations data
        locations_match = re.search(r'const\s+sampleLocations\s*=\s*\[(.*?)\];', content, re.DOTALL)
        if not locations_match:
            self.stdout.write(self.style.ERROR('Could not find sampleLocations in the file'))
            return

        locations_data = locations_match.group(1)
        location_items = re.findall(r'\{\s*id:\s*(\d+),\s*name:\s*"([^"]+)",\s*name_ur:\s*"([^"]+)"\s*\}', locations_data)

        # Create commodities
        created_commodities = []
        for commodity_id, name, name_ur in commodity_items:
            commodity, created = Commodity.objects.get_or_create(name=name)
            created_commodities.append(commodity)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created commodity: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Commodity already exists: {name}'))

        # Create locations
        created_locations = []
        for location_id, name, name_ur in location_items:
            location, created = Location.objects.get_or_create(name=name)
            created_locations.append(location)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created location: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Location already exists: {name}'))

        # Generate price data for the last 90 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)

        # Count existing entries to avoid duplicates
        existing_count = PriceEntry.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).count()

        if existing_count > 0:
            self.stdout.write(self.style.WARNING(f'Found {existing_count} existing price entries. Skipping price data generation.'))
            self.stdout.write(self.style.SUCCESS('If you want to regenerate price data, use the --clear option.'))
            return

        # Generate price entries
        entries_created = 0

        for commodity in created_commodities:
            # Set a base price for each commodity
            base_price = random.uniform(50, 500)

            # Generate prices for each day with some random variation
            current_date = start_date
            while current_date <= end_date:
                for location in created_locations:
                    # Add some randomness to the price (±10%)
                    price_variation = random.uniform(-0.1, 0.1)
                    price = base_price * (1 + price_variation)

                    # Create the price entry
                    PriceEntry.objects.create(
                        commodity=commodity,
                        date=current_date,
                        price=round(price, 2),
                        location=location
                    )
                    entries_created += 1

                # Move to the next day
                current_date += timedelta(days=1)

                # Slightly adjust the base price to simulate market trends (±2%)
                trend_variation = random.uniform(-0.02, 0.02)
                base_price = base_price * (1 + trend_variation)

        self.stdout.write(self.style.SUCCESS(f'Successfully created {entries_created} price entries'))
