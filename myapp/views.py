import datetime
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Commodity, PriceEntry

def home(request):
    return JsonResponse({'message': 'Hello world'})

def list_commodities(request):
    """
    Return a simple JSON list of commodities
    and their latest price (if available).
    """
    commodity_list = []
    commodities = Commodity.objects.all()
    
    for commodity in commodities:
        # get the latest price entry if it exists
        latest_price_entry = PriceEntry.objects.filter(commodity=commodity).order_by('-date').first()
        commodity_list.append({
            'id': commodity.id,
            'name': commodity.name,
            'latest_price': f"{latest_price_entry.price}" if latest_price_entry else None,
            'latest_price_date': f"{latest_price_entry.date}" if latest_price_entry else None,
        })

    return JsonResponse(commodity_list, safe=False)

def commodity_history(request, commodity_id):
    """
    Returns a JSON list of historical price entries for a given commodity.
    Optionally filters by start_date and end_date (YYYY-MM-DD).
    Example usage: /commodities/1/history/?start_date=2024-01-01&end_date=2025-01-01
    """
    # 1) Validate and retrieve the commodity
    commodity = get_object_or_404(Commodity, pk=commodity_id)

    # 2) Parse optional date filters
    start_date_str = request.GET.get('start_date', None)
    end_date_str = request.GET.get('end_date', None)

    # 3) Build a query for PriceEntry
    entries = PriceEntry.objects.filter(commodity=commodity).order_by('date')

    # 4) Filter by optional start_date
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            entries = entries.filter(date__gte=start_date)
        except ValueError:
            # If there's an error parsing the date, we could ignore or return error
            pass

    # 5) Filter by optional end_date
    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
            entries = entries.filter(date__lte=end_date)
        except ValueError:
            pass

    # 6) Prepare JSON-serializable data
    history_data = []
    for entry in entries:
        history_data.append({
            "date": str(entry.date),
            "price": float(entry.price),  # convert Decimal to float for JSON
        })

    # 7) Construct and return response
    return JsonResponse({
        "commodity_id": commodity.id,
        "commodity_name": commodity.name,
        "count": len(history_data),
        "data": history_data
    })