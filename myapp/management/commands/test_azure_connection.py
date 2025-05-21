import pyodbc
from django.core.management.base import BaseCommand
from django.db import connections

class Command(BaseCommand):
    help = 'Tests the connection to the Azure SQL Database'

    def handle(self, *args, **options):
        connection_string = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:zz-backend.database.windows.net,1433;Database=zz-database;Uid=wahaj110;Pwd=WaqeyB2013;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

        self.stdout.write(self.style.SUCCESS('Testing direct connection using pyodbc...'))
        try:
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            row = cursor.fetchone()
            self.stdout.write(self.style.SUCCESS(f'Direct connection successful! SQL Server version: {row[0]}'))
            cursor.close()
            conn.close()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Direct connection failed: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Testing connection using Django...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("SELECT @@VERSION")
                row = cursor.fetchone()
                self.stdout.write(self.style.SUCCESS(f'Django connection successful! SQL Server version: {row[0]}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Django connection failed: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Testing query for locations...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("SELECT TOP 10 Location FROM Crop_Prices GROUP BY Location ORDER BY Location")
                rows = cursor.fetchall()
                if rows:
                    self.stdout.write(self.style.SUCCESS(f'Found {len(rows)} locations:'))
                    for row in rows:
                        self.stdout.write(f'  - {row[0]}')
                else:
                    self.stdout.write(self.style.WARNING('No locations found in the database.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Location query failed: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Testing query for commodities...'))
        try:
            with connections['azure_sql'].cursor() as cursor:
                cursor.execute("SELECT TOP 10 Commodity FROM Crop_Prices")
                rows = cursor.fetchall()
                if rows:
                    self.stdout.write(self.style.SUCCESS(f'Found {len(rows)} commodities:'))
                    for row in rows:
                        self.stdout.write(f'  - {row[0]}')
                else:
                    self.stdout.write(self.style.WARNING('No commodities found in the database.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Commodity query failed: {str(e)}'))
