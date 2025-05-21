from django.core.management.base import BaseCommand
from django.db import connections

class Command(BaseCommand):
    help = 'Lists all tables in the Azure SQL Database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Listing tables in Azure SQL Database...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_type = 'BASE TABLE'
                """)
                rows = cursor.fetchall()
                if rows:
                    self.stdout.write(self.style.SUCCESS(f'Found {len(rows)} tables:'))
                    for row in rows:
                        self.stdout.write(f'  - {row[0]}')
                else:
                    self.stdout.write(self.style.WARNING('No tables found in the database.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Query failed: {str(e)}'))
            
        # Try to list columns for a few common table names
        possible_tables = ['Location', 'Locations', 'Commodity', 'Commodities', 'PriceEntry', 'PriceEntries', 'Price']
        for table in possible_tables:
            try:
                with connections['azure_sql'].cursor() as cursor:
                    cursor.execute(f"""
                        SELECT COLUMN_NAME, DATA_TYPE 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_NAME = '{table}'
                    """)
                    columns = cursor.fetchall()
                    if columns:
                        self.stdout.write(self.style.SUCCESS(f'Columns in {table}:'))
                        for col in columns:
                            self.stdout.write(f'  - {col[0]} ({col[1]})')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to get columns for {table}: {str(e)}'))
