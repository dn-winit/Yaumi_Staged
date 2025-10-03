import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import io

def parse_dashboard_csv(file_content: bytes) -> pd.DataFrame:
    """Parse dashboard CSV content into DataFrame"""
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        df['TrxDate'] = pd.to_datetime(df['TrxDate'])
        return df
    except Exception as e:
        raise ValueError(f"Error parsing CSV: {str(e)}")

def parse_forecast_csv(file_content: bytes) -> pd.DataFrame:
    """Parse forecast CSV content into DataFrame"""
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        df['TrxDate'] = pd.to_datetime(df['TrxDate'])
        return df
    except Exception as e:
        raise ValueError(f"Error parsing CSV: {str(e)}")

def filter_dashboard_data(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply filters to dashboard data - supports multi-select for routes and items"""
    filtered_df = df.copy()

    # Filter by routes - support multi-select
    route_codes = filters.get('route_codes', [])
    if route_codes and 'All' not in route_codes:
        # Convert to int for comparison since RouteCode is stored as int
        route_codes_int = [int(rc) for rc in route_codes]
        filtered_df = filtered_df[filtered_df['RouteCode'].isin(route_codes_int)]

    # Filter by items - support multi-select
    item_codes = filters.get('item_codes', ['All'])
    if item_codes and 'All' not in item_codes:
        filtered_df = filtered_df[filtered_df['ItemCode'].isin(item_codes)]

    # Filter by date range
    start_date = pd.to_datetime(filters['start_date'])
    end_date = pd.to_datetime(filters['end_date'])
    filtered_df = filtered_df[(filtered_df['TrxDate'] >= start_date) & (filtered_df['TrxDate'] <= end_date)]

    return filtered_df

def aggregate_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Aggregate data by ISO calendar period (Daily, Weekly, Monthly)"""
    if period == 'Daily':
        return df
    
    df_copy = df.copy()
    df_copy['TrxDate'] = pd.to_datetime(df_copy['TrxDate'])
    
    # Initialize group_cols to avoid undefined variable error
    group_cols = []
    
    if period == 'Weekly':
        # Use ISO calendar weeks
        df_copy['ISOYear'] = df_copy['TrxDate'].dt.isocalendar().year
        df_copy['ISOWeek'] = df_copy['TrxDate'].dt.isocalendar().week
        
        # Create period identifier - use Monday of the ISO week as period date
        df_copy['Period'] = df_copy['TrxDate'] - pd.to_timedelta(df_copy['TrxDate'].dt.dayofweek, unit='d')
        group_cols = ['Period', 'ISOYear', 'ISOWeek', 'RouteCode', 'ItemCode', 'ItemName']
        
    elif period == 'Monthly':
        # Use ISO calendar year with regular months
        df_copy['ISOYear'] = df_copy['TrxDate'].dt.isocalendar().year
        df_copy['Month'] = df_copy['TrxDate'].dt.month
        
        # Create period identifier - use first day of month
        df_copy['Period'] = df_copy['TrxDate'].dt.to_period('M').dt.to_timestamp()
        group_cols = ['Period', 'ISOYear', 'Month', 'RouteCode', 'ItemCode', 'ItemName']
    else:
        # Fallback for unknown period types
        return df
    
    # Group and aggregate - remove old average columns since we calculate dynamically
    agg_dict = {
        'TotalQuantity': 'sum',
        'Predicted': 'sum',
        'SalesValue': 'sum',
        'WarehouseName': 'first',
        'CategoryName': 'first',
        'AvgUnitPrice': 'mean'
    }
    
    aggregated = df_copy.groupby(group_cols).agg(agg_dict).reset_index()
    aggregated['TrxDate'] = aggregated['Period']
    
    return aggregated

def get_filter_options(df: pd.DataFrame) -> Dict[str, List[Dict]]:
    """Extract unique filter options from dataframe"""
    routes = df['RouteCode'].drop_duplicates().tolist()
    routes = [{'code': str(route), 'name': str(route)} for route in routes]
    
    items = df[['ItemCode', 'ItemName']].drop_duplicates().to_dict('records')
    items = [{'code': i['ItemCode'], 'name': f"{i['ItemCode']} - {i['ItemName']}"} for i in items]
    
    return {
        'routes': routes,
        'items': items
    }