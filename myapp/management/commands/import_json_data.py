import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import Commodity, PriceEntry, Location

class Command(BaseCommand):
    help = 'Imports price data from JSON files in the data folder'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing price entries before importing')
        parser.add_argument('--data-dir', type=str, default='../../data', help='Path to the data directory')

    def handle(self, *args, **options):
        data_dir = options['data_dir']

        # Check if we should clear existing data
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing price entries...'))
            PriceEntry.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing price entries cleared.'))

        # Check if the data directory exists
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f'Data directory not found: {data_dir}'))
            return

        # Get all JSON files in the data directory
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]

        if not json_files:
            self.stdout.write(self.style.ERROR(f'No JSON files found in {data_dir}'))
            return

        self.stdout.write(self.style.WARNING(f'Found {len(json_files)} JSON files'))

        # Process each JSON file
        total_entries = 0

        for json_file in json_files:
            file_path = os.path.join(data_dir, json_file)
            self.stdout.write(self.style.WARNING(f'Processing {json_file}...'))

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check if the data is a list or dictionary
                if isinstance(data, list):
                    entries = data
                elif isinstance(data, dict) and 'data' in data:
                    entries = data['data']
                else:
                    self.stdout.write(self.style.ERROR(f'Unexpected data format in {json_file}'))
                    continue

                file_entries = 0

                # Process each entry
                for entry in entries:
                    # Extract data from the entry based on the actual JSON structure
                    try:
                        commodity_name = entry.get('Commodity')
                        location_name = entry.get('Location')
                        date_str = entry.get('Date')
                        price = entry.get('Price')

                        # Skip if any required field is missing (except price can be null)
                        if not all([commodity_name, location_name, date_str]):
                            continue

                        # Handle null prices
                        if price is None:
                            # Skip entries with null prices
                            continue

                        # Parse the date
                        try:
                            # Try different date formats
                            for date_format in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%Y/%m/%d']:
                                try:
                                    date = datetime.strptime(date_str, date_format).date()
                                    break
                                except ValueError:
                                    continue
                            else:
                                # If none of the formats worked
                                self.stdout.write(self.style.WARNING(f'Could not parse date: {date_str}'))
                                continue
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'Error parsing date {date_str}: {str(e)}'))
                            continue

                        # Get or create the commodity
                        commodity, _ = Commodity.objects.get_or_create(name=commodity_name)

                        # Get or create the location
                        location, _ = Location.objects.get_or_create(name=location_name)

                        # Create the price entry
                        PriceEntry.objects.create(
                            commodity=commodity,
                            location=location,
                            date=date,
                            price=float(price)
                        )

                        file_entries += 1

                        # Show progress every 1000 entries
                        if file_entries % 1000 == 0:
                            self.stdout.write(self.style.WARNING(f'Processed {file_entries} entries from {json_file}'))

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing entry: {str(e)}'))
                        continue

                total_entries += file_entries
                self.stdout.write(self.style.SUCCESS(f'Successfully imported {file_entries} entries from {json_file}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {json_file}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported a total of {total_entries} price entries'))
