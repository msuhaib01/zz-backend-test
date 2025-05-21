import pyodbc
from datetime import datetime
from django.conf import settings

# Azure SQL Database connection string
CONNECTION_STRING = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:zz-backend.database.windows.net,1433;Database=zz-database;Uid=wahaj110;Pwd=WaqeyB2013;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

def get_connection():
    """
    Get a connection to the Azure SQL Database
    """
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"Error connecting to Azure SQL Database: {str(e)}")
        return None

def get_locations():
    """
    Get all unique locations from the Azure SQL Database
    """
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Location FROM Crop_Prices ORDER BY Location")
        locations = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return locations
    except Exception as e:
        print(f"Error getting locations: {str(e)}")
        if conn:
            conn.close()
        return []

def get_commodities():
    """
    Get all unique commodities from the Azure SQL Database
    """
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Commodity FROM Crop_Prices ORDER BY Commodity")
        commodities = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return commodities
    except Exception as e:
        print(f"Error getting commodities: {str(e)}")
        if conn:
            conn.close()
        return []

def get_price_history(commodity, location, start_date=None, end_date=None):
    """
    Get price history for a specific commodity and location
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # Build the query
        query = "SELECT Date, Price FROM Crop_Prices WHERE Commodity = ? AND Location = ?"
        params = [commodity, location]

        # Add date filters if provided
        if start_date:
            query += " AND Date >= ?"
            params.append(start_date)
            print(f"Added start_date filter: {start_date}")

        if end_date:
            query += " AND Date <= ?"
            params.append(end_date)
            print(f"Added end_date filter: {end_date}")

        query += " ORDER BY Date"

        print(f"Executing SQL query: {query}")
        print(f"With parameters: {params}")

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Format the results
        data = [{'date': row[0].strftime('%Y-%m-%d'), 'price': float(row[1]) if row[1] is not None else None} for row in rows]

        # Calculate statistics
        prices = [item['price'] for item in data if item['price'] is not None]
        stats = {}

        if prices:
            stats = {
                'average': round(sum(prices) / len(prices), 2),
                'highest': round(max(prices), 2),
                'lowest': round(min(prices), 2),
                'current': round(prices[-1], 2) if prices else None,
            }
        else:
            stats = {
                'average': None,
                'highest': None,
                'lowest': None,
                'current': None,
            }

        cursor.close()
        conn.close()

        return {
            'commodity': commodity,
            'location': location,
            'data': data,
            'stats': stats
        }
    except Exception as e:
        print(f"Error getting price history: {str(e)}")
        if conn:
            conn.close()
        return None

def compare_commodities(commodities, location, start_date=None, end_date=None):
    """
    Compare prices of multiple commodities at a specific location
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        results = {}

        for commodity in commodities:
            # Build the query
            query = "SELECT Date, Price FROM Crop_Prices WHERE Commodity = ? AND Location = ?"
            params = [commodity, location]

            # Add date filters if provided
            if start_date:
                query += " AND Date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND Date <= ?"
                params.append(end_date)

            query += " ORDER BY Date"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Format the results
            data = [{'date': row[0].strftime('%Y-%m-%d'), 'price': float(row[1]) if row[1] is not None else None} for row in rows]
            results[commodity] = data

        cursor.close()
        conn.close()

        return {
            'location': location,
            'data': results
        }
    except Exception as e:
        print(f"Error comparing commodities: {str(e)}")
        if conn:
            conn.close()
        return None

def compare_locations(commodity, locations, start_date=None, end_date=None):
    """
    Compare prices of a commodity across multiple locations
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        results = {}

        for location in locations:
            # Build the query
            query = "SELECT Date, Price FROM Crop_Prices WHERE Commodity = ? AND Location = ?"
            params = [commodity, location]

            # Add date filters if provided
            if start_date:
                query += " AND Date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND Date <= ?"
                params.append(end_date)

            query += " ORDER BY Date"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Format the results
            data = [{'date': row[0].strftime('%Y-%m-%d'), 'price': float(row[1]) if row[1] is not None else None} for row in rows]
            results[location] = data

        cursor.close()
        conn.close()

        return {
            'commodity': commodity,
            'data': results
        }
    except Exception as e:
        print(f"Error comparing locations: {str(e)}")
        if conn:
            conn.close()
        return None

def get_latest_price(commodity, location, reference_date=None):
    """
    Get the latest price for a specific commodity and location before the reference date.
    If reference_date is None, returns the absolute latest price.
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # Build the query to get the most recent price
        if reference_date:
            query = """
                SELECT TOP 1 Date, Price
                FROM Crop_Prices
                WHERE Commodity = ? AND Location = ? AND Price IS NOT NULL AND Date < ?
                ORDER BY Date DESC
            """
            params = [commodity, location, reference_date]
            print(f"Executing SQL query for latest price before {reference_date}: {query}")
        else:
            query = """
                SELECT TOP 1 Date, Price
                FROM Crop_Prices
                WHERE Commodity = ? AND Location = ? AND Price IS NOT NULL
                ORDER BY Date DESC
            """
            params = [commodity, location]
            print(f"Executing SQL query for absolute latest price: {query}")

        print(f"With parameters: {params}")

        cursor.execute(query, params)
        row = cursor.fetchone()

        if row:
            latest_price = {
                'date': row[0].strftime('%Y-%m-%d'),
                'price': float(row[1]) if row[1] is not None else None
            }
            print(f"Found latest price: {latest_price['price']} on {latest_price['date']}")
        else:
            latest_price = None
            print(f"No price data found for {commodity} in {location}")

        cursor.close()
        conn.close()

        return latest_price
    except Exception as e:
        print(f"Error getting latest price: {str(e)}")
        if conn:
            conn.close()
        return None
