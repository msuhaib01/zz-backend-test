import datetime
import numpy as np
import os
import json
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Commodity, PriceEntry, Location
from . import azure_data
from . import model_prediction

@api_view(['GET'])
def get_locations(request):
    """
    Get all unique locations from the Azure SQL Database
    """
    try:
        # Get all locations from Azure SQL Database
        locations = azure_data.get_locations()
        return Response({'locations': locations})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_commodities(request):
    """
    Get all unique commodities from the Azure SQL Database
    """
    try:
        # Get all commodities from Azure SQL Database
        commodities = azure_data.get_commodities()
        return Response({'commodities': commodities})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_price_history(request):
    """
    Get price history for a specific commodity and location from Azure SQL Database
    """
    commodity_name = request.GET.get('commodity')
    location_name = request.GET.get('location')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not commodity_name or not location_name:
        return Response({'error': 'Commodity and location are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Convert string dates to datetime objects if provided
        start_date_obj = None
        end_date_obj = None

        if start_date:
            try:
                start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                print(f"Parsed start_date: {start_date} -> {start_date_obj}")
            except ValueError as e:
                print(f"Error parsing start_date '{start_date}': {str(e)}")
                pass

        if end_date:
            try:
                end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                print(f"Parsed end_date: {end_date} -> {end_date_obj}")
            except ValueError as e:
                print(f"Error parsing end_date '{end_date}': {str(e)}")
                pass

        print(f"Fetching price history for {commodity_name} in {location_name} from {start_date_obj} to {end_date_obj}")

        # Get price history from Azure SQL Database
        result = azure_data.get_price_history(
            commodity=commodity_name,
            location=location_name,
            start_date=start_date_obj,
            end_date=end_date_obj
        )

        if not result:
            return Response({'error': 'No data found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_forecast(request):
    """
    Get price forecast for a specific commodity and location using the trained model
    """
    commodity_name = request.GET.get('commodity')
    location_name = request.GET.get('location')
    days = int(request.GET.get('days', 7))
    use_model = request.GET.get('use_model', 'true').lower() == 'true'

    if not commodity_name or not location_name:
        return Response({'error': 'Commodity and location are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if use_model:
            # Use the trained model for prediction
            result = model_prediction.predict_prices(
                commodity=commodity_name,
                location=location_name,
                days=days
            )

            if result:
                # Add additional information for the frontend
                result['message'] = f"AI model prediction for {commodity_name} in {location_name}"
                return Response(result)

        # If model is disabled or prediction failed, use simple linear prediction
        # Try to get data from Azure SQL Database
        result = azure_data.get_price_history(
            commodity=commodity_name,
            location=location_name
        )

        if not result or not result.get('data'):
            # If no historical data, use the model anyway
            result = model_prediction.predict_prices(
                commodity=commodity_name,
                location=location_name,
                days=days
            )

            if result:
                result['message'] = f"AI model prediction for {commodity_name} in {location_name} (no historical data)"
                return Response(result)
            else:
                return Response({'error': f'No data found for {commodity_name} in {location_name}'}, status=status.HTTP_404_NOT_FOUND)

        # Use the data from Azure SQL Database
        dates = [datetime.datetime.strptime(item['date'], '%Y-%m-%d').date() for item in result['data']]
        prices = [float(item['price']) for item in result['data']]

        if len(prices) < 2:
            # If not enough data points, use the model anyway
            result = model_prediction.predict_prices(
                commodity=commodity_name,
                location=location_name,
                days=days
            )

            if result:
                result['message'] = f"AI model prediction for {commodity_name} in {location_name} (insufficient historical data)"
                return Response(result)
            else:
                return Response({'error': 'Not enough data points for forecast'}, status=status.HTTP_404_NOT_FOUND)

        # Calculate average daily change
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        avg_change = sum(changes) / len(changes)

        # Get the last date and price
        last_date = dates[-1]
        last_price = prices[-1]

        # Generate forecast
        forecast_data = []
        for i in range(1, days + 1):
            forecast_date = last_date + datetime.timedelta(days=i)
            forecast_price = last_price + (avg_change * i)

            # Add some randomness for confidence interval
            confidence_low = round(forecast_price * 0.95, 2)
            confidence_high = round(forecast_price * 1.05, 2)

            forecast_data.append({
                'date': forecast_date.strftime('%Y-%m-%d'),
                'price': round(forecast_price, 2),
                'confidence': [confidence_low, confidence_high]
            })

        return Response({
            'commodity': commodity_name,
            'location': location_name,
            'forecast': forecast_data,
            'using_model': False,
            'message': f"Linear prediction for {commodity_name} in {location_name} based on historical data"
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def compare_commodities(request):
    """
    Compare prices of multiple commodities at a specific location from Azure SQL Database
    """
    commodity_names = request.GET.getlist('commodities[]')
    location_name = request.GET.get('location')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not commodity_names or not location_name:
        return Response({'error': 'Commodities and location are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Convert string dates to datetime objects if provided
        start_date_obj = None
        end_date_obj = None

        if start_date:
            try:
                start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                pass

        if end_date:
            try:
                end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                pass

        # Get comparison data from Azure SQL Database
        result = azure_data.compare_commodities(
            commodities=commodity_names,
            location=location_name,
            start_date=start_date_obj,
            end_date=end_date_obj
        )

        if not result:
            return Response({'error': 'No data found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def compare_locations(request):
    """
    Compare prices of a commodity across multiple locations from Azure SQL Database
    """
    commodity_name = request.GET.get('commodity')
    location_names = request.GET.getlist('locations[]')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not commodity_name or not location_names:
        return Response({'error': 'Commodity and locations are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Convert string dates to datetime objects if provided
        start_date_obj = None
        end_date_obj = None

        if start_date:
            try:
                start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                pass

        if end_date:
            try:
                end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                pass

        # Get comparison data from Azure SQL Database
        result = azure_data.compare_locations(
            commodity=commodity_name,
            locations=location_names,
            start_date=start_date_obj,
            end_date=end_date_obj
        )

        if not result:
            return Response({'error': 'No data found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def model_predict(request):
    """
    Get price prediction using the trained model for a specific commodity and location.
    Can accept either days parameter or start_date and end_date parameters.
    """
    commodity_name = request.GET.get('commodity')
    location_name = request.GET.get('location')
    days = int(request.GET.get('days', 7))
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not commodity_name or not location_name:
        return Response({'error': 'Commodity and location are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Convert string dates to datetime objects if provided
    start_date_obj = None
    end_date_obj = None

    if start_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            print(f"Parsed start_date: {start_date} -> {start_date_obj}")
        except ValueError as e:
            print(f"Error parsing start_date '{start_date}': {str(e)}")
            return Response({'error': f'Invalid start_date format: {start_date}'}, status=status.HTTP_400_BAD_REQUEST)

    if end_date:
        try:
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            print(f"Parsed end_date: {end_date} -> {end_date_obj}")
        except ValueError as e:
            print(f"Error parsing end_date '{end_date}': {str(e)}")
            return Response({'error': f'Invalid end_date format: {end_date}'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if start_date_obj and end_date_obj:
            print(f"Attempting model prediction for {commodity_name} in {location_name} from {start_date_obj} to {end_date_obj}")

            # Use the trained model for prediction with date range
            result = model_prediction.predict_prices(
                commodity=commodity_name,
                location=location_name,
                days=days,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
        else:
            print(f"Attempting model prediction for {commodity_name} in {location_name} for {days} days")

            # Use the trained model for prediction with days
            result = model_prediction.predict_prices(
                commodity=commodity_name,
                location=location_name,
                days=days
            )

        if not result:
            print("Model prediction failed, using fallback prediction")
            # If model prediction fails, use fallback prediction
            if start_date_obj and end_date_obj:
                result = model_prediction.fallback_prediction(
                    commodity=commodity_name,
                    location=location_name,
                    days=days,
                    start_date=start_date_obj,
                    end_date=end_date_obj
                )
            else:
                result = model_prediction.fallback_prediction(
                    commodity=commodity_name,
                    location=location_name,
                    days=days
                )

            if not result:
                print("Fallback prediction also failed, returning simple forecast")
                # If fallback also fails, create a simple forecast
                current_date = datetime.datetime.now().date()
                forecast_data = []

                if start_date_obj and end_date_obj:
                    # Generate a list of dates in the range
                    date_list = []
                    current = start_date_obj
                    while current <= end_date_obj:
                        date_list.append(current)
                        current += datetime.timedelta(days=1)
                else:
                    # Use the default behavior (next 'days' days)
                    date_list = [current_date + datetime.timedelta(days=i) for i in range(1, days + 1)]

                # Generate predictions for each date
                for forecast_date in date_list:
                    forecast_data.append({
                        'date': forecast_date.strftime('%Y-%m-%d'),
                        'price': 100.0,  # Default price
                        'confidence': [95.0, 105.0]  # Default confidence interval
                    })

                result = {
                    'commodity': commodity_name,
                    'location': location_name,
                    'forecast': forecast_data,
                    'using_model': False,
                    'message': f"Simple forecast for {commodity_name} in {location_name} (prediction failed)"
                }

        # Add additional information for the frontend
        if 'message' not in result:
            result['message'] = f"AI model prediction for {commodity_name} in {location_name}"

        print(f"Returning prediction result: {result['message']}")
        return Response(result)
    except Exception as e:
        print(f"Error in model_predict: {str(e)}")

        # Create a simple forecast as a last resort
        try:
            current_date = datetime.datetime.now().date()
            forecast_data = []

            if start_date_obj and end_date_obj:
                # Generate a list of dates in the range
                date_list = []
                current = start_date_obj
                while current <= end_date_obj:
                    date_list.append(current)
                    current += datetime.timedelta(days=1)
            else:
                # Use the default behavior (next 'days' days)
                date_list = [current_date + datetime.timedelta(days=i) for i in range(1, days + 1)]

            # Generate predictions for each date
            for forecast_date in date_list:
                forecast_data.append({
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'price': 100.0,  # Default price
                    'confidence': [95.0, 105.0]  # Default confidence interval
                })

            result = {
                'commodity': commodity_name,
                'location': location_name,
                'forecast': forecast_data,
                'using_model': False,
                'message': f"Emergency forecast for {commodity_name} in {location_name} (error occurred)"
            }

            return Response(result)
        except:
            # If even the simple forecast fails, return an error
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_aims_table_data(request):
    """
    Serve the latest scraped AIMS table data as JSON.
    """
    json_path = os.path.join(settings.BASE_DIR, 'aims_data.json')
    if not os.path.exists(json_path):
        return Response({'error': 'AIMS data not found. Please run the scraper.'}, status=404)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return Response({'data': data})
