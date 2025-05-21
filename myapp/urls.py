from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.home, name='home'),
    path('commodities/', views.list_commodities, name='list_commodities'),
    path('commodities/<int:commodity_id>/history/', views.commodity_history, name='commodity_history'),

    # New API endpoints that match the crop_prices app
    path('api/crop-prices/locations/', api_views.get_locations, name='get_locations'),
    path('api/crop-prices/commodities/', api_views.get_commodities, name='get_commodities'),
    path('api/crop-prices/price-history/', api_views.get_price_history, name='get_price_history'),
    path('api/crop-prices/forecast/', api_views.get_forecast, name='get_forecast'),
    path('api/crop-prices/compare-commodities/', api_views.compare_commodities, name='compare_commodities'),
    path('api/crop-prices/compare-locations/', api_views.compare_locations, name='compare_locations'),
    path('api/crop-prices/model-predict/', api_views.model_predict, name='model_predict'),
    path('api/aims-table/', api_views.get_aims_table_data, name='get_aims_table_data'),
]
