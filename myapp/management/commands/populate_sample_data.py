import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from core.models import Commodity, PriceEntry, Location

class Command(BaseCommand):
    help = 'Populates the database with sample commodity and price data'

    def handle(self, *args, **options):
        # Sample commodities
        commodities = [
            "Apple (Ammre)",
            "Apple (Golden)",
            "Banana",
            "Carrot",
            "Cauliflower",
            "Cucumber",
            "Garlic",
            "Ginger",
            "Grapes",
            "Lemon",
            "Mango",
            "Onion",
            "Orange",
            "Potato",
            "Tomato",
            "Wheat",
            "Rice",
            "Corn",
            "Sugarcane",
            "Cotton"
        ]

        # Sample locations
        locations = [
            "Lahore",
            "Karachi",
            "Islamabad",
            "Faisalabad",
            "Multan",
            "Peshawar",
            "Quetta",
            "Sialkot",
            "Gujranwala",
            "Rawalpindi"
        ]

        # Create locations
        created_locations = []
        for location_name in locations:
            location, created = Location.objects.get_or_create(name=location_name)
            created_locations.append(location)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created location: {location_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Location already exists: {location_name}'))

        # Create commodities
        created_commodities = []
        for commodity_name in commodities:
            commodity, created = Commodity.objects.get_or_create(name=commodity_name)
            created_commodities.append(commodity)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created commodity: {commodity_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Commodity already exists: {commodity_name}'))

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
            self.stdout.write(self.style.SUCCESS('If you want to regenerate price data, delete existing entries first.'))
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
