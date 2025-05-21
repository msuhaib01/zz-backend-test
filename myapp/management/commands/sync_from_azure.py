from django.core.management.base import BaseCommand
from django.db import connections
from core.models import Commodity, Location, PriceEntry
from datetime import datetime

class Command(BaseCommand):
    help = 'Syncs data from Azure SQL Database to local models'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1000, help='Limit the number of records to sync')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before syncing')

    def handle(self, *args, **options):
        limit = options['limit']
        clear = options['clear']
        
        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            PriceEntry.objects.all().delete()
            Commodity.objects.all().delete()
            Location.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))
        
        # Step 1: Sync locations
        self.stdout.write(self.style.SUCCESS('Syncing locations...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("SELECT DISTINCT Location FROM Crop_Prices")
                locations = cursor.fetchall()
                
                for loc in locations:
                    location_name = loc[0]
                    Location.objects.get_or_create(name=location_name)
                
                self.stdout.write(self.style.SUCCESS(f'Synced {len(locations)} locations.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to sync locations: {str(e)}'))
            return
        
        # Step 2: Sync commodities
        self.stdout.write(self.style.SUCCESS('Syncing commodities...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("SELECT DISTINCT Commodity FROM Crop_Prices")
                commodities = cursor.fetchall()
                
                for com in commodities:
                    commodity_name = com[0]
                    Commodity.objects.get_or_create(name=commodity_name)
                
                self.stdout.write(self.style.SUCCESS(f'Synced {len(commodities)} commodities.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to sync commodities: {str(e)}'))
            return
        
        # Step 3: Sync price entries
        self.stdout.write(self.style.SUCCESS(f'Syncing price entries (limit: {limit})...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute(f"""
                    SELECT TOP {limit} Location, Date, Commodity, Price 
                    FROM Crop_Prices 
                    WHERE Price IS NOT NULL
                    ORDER BY Date DESC
                """)
                entries = cursor.fetchall()
                
                count = 0
                skipped = 0
                
                for entry in entries:
                    location_name, date, commodity_name, price = entry
                    
                    try:
                        location = Location.objects.get(name=location_name)
                        commodity = Commodity.objects.get(name=commodity_name)
                        
                        # Check if entry already exists
                        existing = PriceEntry.objects.filter(
                            location=location,
                            commodity=commodity,
                            date=date
                        ).exists()
                        
                        if not existing:
                            PriceEntry.objects.create(
                                location=location,
                                commodity=commodity,
                                date=date,
                                price=price
                            )
                            count += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Skipped entry: {entry} - {str(e)}'))
                        skipped += 1
                
                self.stdout.write(self.style.SUCCESS(f'Synced {count} price entries, skipped {skipped}.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to sync price entries: {str(e)}'))
            return
        
        self.stdout.write(self.style.SUCCESS('Sync completed successfully.'))
