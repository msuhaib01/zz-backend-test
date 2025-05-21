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

    def handle(self, *args, **options):
        days = options['days']
        
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
        self.stdout.write(self.style.WARNING(f'Reading file: {file_path}'))
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
        
        # Join lines 11 to 302 as requested
        content = ''.join(content[10:302])
        
        # Extract commodities data
        commodities_data = []
        locations_data = []
        
        # Look for patterns like { id: 1, name: "Apple (Ammre)", name_ur: "سیب (عمری)" }
        commodity_pattern = r'\{\s*id:\s*(\d+),\s*name:\s*"([^"]+)",\s*name_ur:\s*"([^"]+)"\s*\}'
        
        # Find all commodities
        if 'sampleCommodities' in content:
            commodities_section = content.split('sampleCommodities')[1].split('];')[0]
            commodities_data = re.findall(commodity_pattern, commodities_section)
            self.stdout.write(self.style.WARNING(f'Found {len(commodities_data)} commodities'))
        
        # Find all locations
        if 'sampleLocations' in content:
            locations_section = content.split('sampleLocations')[1].split('];')[0]
            locations_data = re.findall(commodity_pattern, locations_section)
            self.stdout.write(self.style.WARNING(f'Found {len(locations_data)} locations'))
        
        if not commodities_data:
            self.stdout.write(self.style.ERROR('No commodities found in the file'))
            return
            
        if not locations_data:
            self.stdout.write(self.style.ERROR('No locations found in the file'))
            return

        # Create commodities
        created_commodities = []
        for commodity_id, name, name_ur in commodities_data:
            commodity, created = Commodity.objects.get_or_create(name=name)
            created_commodities.append(commodity)

        self.stdout.write(self.style.SUCCESS(f'Created {len(created_commodities)} commodities'))

        # Create locations
        created_locations = []
        for location_id, name, name_ur in locations_data:
            location, created = Location.objects.get_or_create(name=name)
            created_locations.append(location)
                
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_locations)} locations'))

        # Generate price data for the specified number of days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Generate price entries
        entries_created = 0
        total_entries = len(created_commodities) * len(created_locations) * (days + 1)
        
        self.stdout.write(self.style.WARNING(f'Generating {total_entries} price entries for {days+1} days...'))
        
        # Create a progress counter
        progress_step = max(1, total_entries // 10)  # Show progress 10 times
        
        for commodity in created_commodities:
            # Set a base price for each commodity
            base_price = random.uniform(50, 500)
            
            # Generate prices for each day with some random variation
            current_date = start_date
            day_count = 0
            
            while current_date <= end_date and day_count <= days:
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
                    
                    # Show progress
                    if entries_created % progress_step == 0:
                        percent = int((entries_created / total_entries) * 100)
                        self.stdout.write(self.style.WARNING(f'Progress: {percent}% ({entries_created}/{total_entries})'))
                
                # Move to the next day
                current_date += timedelta(days=1)
                day_count += 1
                
                # Slightly adjust the base price to simulate market trends (±2%)
                trend_variation = random.uniform(-0.02, 0.02)
                base_price = base_price * (1 + trend_variation)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {entries_created} price entries'))
