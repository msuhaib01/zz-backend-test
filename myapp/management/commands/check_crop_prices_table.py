from django.core.management.base import BaseCommand
from django.db import connections

class Command(BaseCommand):
    help = 'Checks the structure of the Crop_Prices table in the Azure SQL Database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking Crop_Prices table structure...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'Crop_Prices'
                """)
                columns = cursor.fetchall()
                if columns:
                    self.stdout.write(self.style.SUCCESS(f'Found {len(columns)} columns:'))
                    for col in columns:
                        max_length = col[2] if col[2] is not None else 'N/A'
                        self.stdout.write(f'  - {col[0]} ({col[1]}, max length: {max_length})')
                else:
                    self.stdout.write(self.style.WARNING('No columns found in the Crop_Prices table.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Query failed: {str(e)}'))
            
        self.stdout.write(self.style.SUCCESS('Checking sample data from Crop_Prices table...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("SELECT TOP 10 * FROM Crop_Prices")
                rows = cursor.fetchall()
                if rows:
                    self.stdout.write(self.style.SUCCESS(f'Found {len(rows)} rows:'))
                    for row in rows:
                        self.stdout.write(f'  - {row}')
                else:
                    self.stdout.write(self.style.WARNING('No data found in the Crop_Prices table.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Query failed: {str(e)}'))
            
        self.stdout.write(self.style.SUCCESS('Checking unique locations in Crop_Prices table...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("SELECT DISTINCT Location FROM Crop_Prices")
                locations = cursor.fetchall()
                if locations:
                    self.stdout.write(self.style.SUCCESS(f'Found {len(locations)} unique locations:'))
                    for loc in locations:
                        self.stdout.write(f'  - {loc[0]}')
                else:
                    self.stdout.write(self.style.WARNING('No locations found in the Crop_Prices table.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Query failed: {str(e)}'))
            
        self.stdout.write(self.style.SUCCESS('Checking unique commodities in Crop_Prices table...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("SELECT DISTINCT Commodity FROM Crop_Prices")
                commodities = cursor.fetchall()
                if commodities:
                    self.stdout.write(self.style.SUCCESS(f'Found {len(commodities)} unique commodities:'))
                    for com in commodities:
                        self.stdout.write(f'  - {com[0]}')
                else:
                    self.stdout.write(self.style.WARNING('No commodities found in the Crop_Prices table.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Query failed: {str(e)}'))
