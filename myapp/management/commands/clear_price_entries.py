from django.core.management.base import BaseCommand
from core.models import PriceEntry

class Command(BaseCommand):
    help = 'Deletes all price entries from the database'

    def handle(self, *args, **options):
        count = PriceEntry.objects.count()
        self.stdout.write(self.style.WARNING(f'Deleting {count} price entries...'))
        
        PriceEntry.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('All price entries have been deleted.'))
