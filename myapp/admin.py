from django.contrib import admin

# Register your models here.
from .models import Commodity, PriceEntry, User, PhoneVerification, Location

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class PriceEntryAdmin(admin.ModelAdmin):
    list_display = ('commodity', 'location', 'date', 'price')
    list_filter = ('commodity', 'location', 'date')
    search_fields = ('commodity__name', 'location__name')
    date_hierarchy = 'date'
    autocomplete_fields = ['commodity', 'location']

class CommodityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Commodity, CommodityAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(PriceEntry, PriceEntryAdmin)
admin.site.register(User)
admin.site.register(PhoneVerification)
