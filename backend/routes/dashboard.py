from fastapi import APIRouter, HTTPException
import pandas as pd
import logging
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core import data_manager
from backend.models.data_models import DashboardFilters, HistoricalAverages, FilterOptions
from backend.utils.data_processor import filter_dashboard_data, aggregate_by_period, get_filter_options

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/filter-options", response_model=FilterOptions)
async def get_filter_options_endpoint():
    """Get available filter options"""
    if not data_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Data not loaded yet")
    
    dashboard_data = data_manager.get_demand_data()
    options = get_filter_options(dashboard_data)
    return FilterOptions(**options)

@router.post("/dashboard-data")
async def get_dashboard_data(filters: DashboardFilters):
    """Get filtered and aggregated dashboard data with item breakdown support"""
    if not data_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Data not loaded yet")

    dashboard_data = data_manager.get_demand_data()

    try:
        # Filter data
        filtered_df = filter_dashboard_data(dashboard_data, filters.dict())

        # Aggregate by period
        aggregated_df = aggregate_by_period(filtered_df, filters.period)

        if aggregated_df.empty:
            return {"chart_data": [], "table_data": []}

        # Determine filter selections
        multiple_items_selected = len(filters.item_codes) > 1 or 'All' in filters.item_codes
        multiple_routes_selected = len(filters.route_codes) > 1 or 'All' in filters.route_codes
        single_route_selected = len(filters.route_codes) == 1 and 'All' not in filters.route_codes

        # Store original item-level data for breakdown
        item_level_df = aggregated_df.copy()

        # Prepare chart data with item breakdown
        chart_data = []

        if multiple_items_selected:
            # Multiple items selected - need item breakdown
            # Always group by date first
            group_cols = ['TrxDate']

            # Include RouteCode in grouping based on route selection
            if single_route_selected:
                # Single specific route - include in grouping
                group_cols.append('RouteCode')
            elif multiple_routes_selected and 'All' not in filters.route_codes:
                # Multiple specific routes - include in grouping to keep them separate
                group_cols.append('RouteCode')
            # If 'All' routes selected, don't include RouteCode in grouping (aggregate across all)

            # Add period-specific columns
            if filters.period == 'Weekly':
                group_cols.extend(['ISOYear', 'ISOWeek'])
            elif filters.period == 'Monthly':
                group_cols.extend(['ISOYear', 'Month'])

            # Keep only existing columns
            group_cols = [col for col in group_cols if col in item_level_df.columns]

            # Create aggregated view for table
            agg_dict = {
                'TotalQuantity': 'sum',
                'Predicted': 'sum'
            }

            aggregated_for_table = item_level_df.groupby(group_cols).agg(agg_dict).reset_index()

            # For chart data, get top items by volume for each date/route combination
            # Group by same columns used for aggregation to ensure consistency
            chart_group_cols = ['TrxDate']
            if 'RouteCode' in group_cols:
                chart_group_cols.append('RouteCode')

            for group_keys, date_items in item_level_df.groupby(chart_group_cols):
                if 'RouteCode' in chart_group_cols:
                    if isinstance(group_keys, tuple):
                        date, route_code = group_keys
                    else:
                        date = group_keys
                        route_code = date_items['RouteCode'].iloc[0]
                    route_display = str(int(route_code))
                else:
                    date = group_keys if not isinstance(group_keys, tuple) else group_keys[0]
                    route_display = 'All Routes'

                # Sort by total volume
                date_items = date_items.sort_values('TotalQuantity', ascending=False)

                # Get top 10 items
                top_items = date_items.head(10)

                # Calculate "Others"
                others_actual = date_items.iloc[10:]['TotalQuantity'].sum() if len(date_items) > 10 else 0
                others_predicted = date_items.iloc[10:]['Predicted'].sum() if len(date_items) > 10 else 0

                # Build breakdown for this date
                items_breakdown = []
                for _, item_row in top_items.iterrows():
                    items_breakdown.append({
                        'itemCode': item_row['ItemCode'],
                        'itemName': item_row.get('ItemName', ''),
                        'actual': int(item_row['TotalQuantity']),
                        'predicted': int(item_row['Predicted'])
                    })

                if others_actual > 0:
                    items_breakdown.append({
                        'itemCode': 'Others',
                        'itemName': 'Others',
                        'actual': int(others_actual),
                        'predicted': int(others_predicted)
                    })

                chart_data.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "route": route_display,
                    "item": "Multiple Items",
                    "actual": int(date_items['TotalQuantity'].sum()),
                    "predicted": int(date_items['Predicted'].sum()),
                    "routeCode": route_display,
                    "itemCode": "Multiple",
                    "itemBreakdown": items_breakdown
                })

            # For table, use aggregated data and include full item breakdown
            table_data_list = []
            for _, agg_row in aggregated_for_table.iterrows():
                date = agg_row['TrxDate']
                route_code = agg_row.get('RouteCode', 'Multiple')

                # Get all items for this date/route combination
                if 'RouteCode' in group_cols:
                    items_for_row = item_level_df[
                        (item_level_df['TrxDate'] == date) &
                        (item_level_df['RouteCode'] == route_code)
                    ]
                else:
                    items_for_row = item_level_df[item_level_df['TrxDate'] == date]

                # Build full item breakdown for table expansion
                full_breakdown = []
                for _, item_row in items_for_row.iterrows():
                    full_breakdown.append({
                        'itemCode': item_row['ItemCode'],
                        'itemName': item_row.get('ItemName', ''),
                        'actual': int(item_row['TotalQuantity']),
                        'predicted': int(item_row['Predicted'])
                    })

                table_data_list.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "route": str(int(route_code)) if isinstance(route_code, (int, float)) else route_code,
                    "item": f"{len(full_breakdown)} Items",
                    "actual": int(agg_row['TotalQuantity']),
                    "predicted": int(agg_row['Predicted']),
                    "routeCode": str(int(route_code)) if isinstance(route_code, (int, float)) else route_code,
                    "itemCode": "Multiple",
                    "itemBreakdown": full_breakdown
                })

            # Use the aggregated table data
            table_data = table_data_list

        else:
            # Single item selected - need to handle route aggregation
            # Determine grouping based on route selection
            single_item_group_cols = ['TrxDate', 'ItemCode']

            if single_route_selected:
                # Single route - include in grouping
                single_item_group_cols.append('RouteCode')
            elif multiple_routes_selected and 'All' not in filters.route_codes:
                # Multiple specific routes - include in grouping to show separate rows
                single_item_group_cols.append('RouteCode')
            # If 'All' routes, aggregate across all routes

            # Add period columns
            if filters.period == 'Weekly':
                single_item_group_cols.extend(['ISOYear', 'ISOWeek'])
            elif filters.period == 'Monthly':
                single_item_group_cols.extend(['ISOYear', 'Month'])

            # Keep only existing columns
            single_item_group_cols = [col for col in single_item_group_cols if col in aggregated_df.columns]

            # Aggregate data
            agg_dict = {
                'TotalQuantity': 'sum',
                'Predicted': 'sum'
            }
            if 'ItemName' in aggregated_df.columns:
                agg_dict['ItemName'] = 'first'

            single_item_aggregated = aggregated_df.groupby(single_item_group_cols).agg(agg_dict).reset_index()

            # Build chart and table data
            chart_data = []
            table_data = []

            for _, row in single_item_aggregated.iterrows():
                item_display = f"{row['ItemCode']} - {row.get('ItemName', '')}"

                # Determine route display
                if 'RouteCode' in row.index:
                    route_display = str(int(row['RouteCode']))
                else:
                    route_display = 'All Routes'

                data_point = {
                    "date": row['TrxDate'].strftime('%Y-%m-%d'),
                    "route": route_display,
                    "item": item_display,
                    "actual": int(row['TotalQuantity']),
                    "predicted": int(row['Predicted']),
                    "routeCode": route_display,
                    "itemCode": row['ItemCode']
                }
                chart_data.append(data_point)
                table_data.append(data_point)

        return {
            "chart_data": chart_data,
            "table_data": table_data
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def calculate_calendar_daily_averages_from_data(filtered_data, target_date):
    """Calculate ISO calendar-based daily averages from already filtered data"""
    if filtered_data.empty:
        return {"last_1_week": 0.0, "last_1_month": 0.0, "last_3_months": 0.0, "last_6_months": 0.0, "last_1_year": 0.0}

    filtered_data = filtered_data.copy()
    filtered_data['TrxDate'] = pd.to_datetime(filtered_data['TrxDate'])
    target_date = pd.to_datetime(target_date)

    # Use ISO calendar for consistent daily calculations
    filtered_data['ISOYear'] = filtered_data['TrxDate'].dt.isocalendar().year
    filtered_data['ISOWeek'] = filtered_data['TrxDate'].dt.isocalendar().week
    filtered_data['ISODay'] = filtered_data['TrxDate'].dt.isocalendar().day

    # Aggregate to daily level first
    daily = filtered_data.groupby(['ISOYear', 'ISOWeek', 'ISODay', 'TrxDate']).agg({
        'TotalQuantity': 'sum'
    }).reset_index()

    # Filter historical data before target date
    historical = daily[daily['TrxDate'] < target_date]

    averages = {}
    # ISO-based periods: use exact ISO week boundaries
    target_iso_year = target_date.isocalendar().year
    target_iso_week = target_date.isocalendar().week

    periods = {
        "last_1_week": 1,    # last 1 ISO week
        "last_1_month": 4,   # last 4 ISO weeks (approx 1 month)
        "last_3_months": 13, # last 13 ISO weeks (approx 3 months)
        "last_6_months": 26, # last 26 ISO weeks (approx 6 months)
        "last_1_year": 52    # last 52 ISO weeks (1 year)
    }

    for period_name, weeks in periods.items():
        # Calculate start ISO week
        start_week_num = (target_iso_year * 52 + target_iso_week) - weeks
        start_year = start_week_num // 52
        start_week = start_week_num % 52
        if start_week == 0:
            start_year -= 1
            start_week = 52

        # Filter period data
        period_data = historical[
            ((historical['ISOYear'] > start_year) |
             ((historical['ISOYear'] == start_year) & (historical['ISOWeek'] >= start_week)))
        ]
        averages[period_name] = float(period_data['TotalQuantity'].mean() if len(period_data) > 0 else 0)

    return averages

def calculate_calendar_weekly_averages_from_data(filtered_data, target_date):
    """Calculate weekly averages from already filtered data"""
    if filtered_data.empty:
        return {"last_1_week": 0.0, "last_3_weeks": 0.0, "last_6_weeks": 0.0, "last_1_year": 0.0}

    filtered_data = filtered_data.copy()
    filtered_data['TrxDate'] = pd.to_datetime(filtered_data['TrxDate'])
    target_date = pd.to_datetime(target_date)

    filtered_data['Year'] = filtered_data['TrxDate'].dt.isocalendar().year
    filtered_data['Week'] = filtered_data['TrxDate'].dt.isocalendar().week

    # Aggregate to weekly
    weekly = filtered_data.groupby(['Year', 'Week']).agg({
        'TotalQuantity': 'sum'
    }).reset_index()

    # Get target week
    target_year = target_date.isocalendar().year
    target_week = target_date.isocalendar().week
    target_week_num = target_year * 52 + target_week

    # Filter historical weeks
    weekly['WeekNum'] = weekly['Year'] * 52 + weekly['Week']
    historical = weekly[weekly['WeekNum'] < target_week_num]

    averages = {}
    periods = {"last_1_week": 1, "last_3_weeks": 3, "last_6_weeks": 6, "last_1_year": 52}

    for period_name, weeks in periods.items():
        start_week_num = target_week_num - weeks
        period_data = historical[historical['WeekNum'] >= start_week_num]
        averages[period_name] = float(period_data['TotalQuantity'].mean() if len(period_data) > 0 else 0)

    return averages

def calculate_calendar_monthly_averages_from_data(filtered_data, target_date):
    """Calculate monthly averages from already filtered data"""
    if filtered_data.empty:
        return {"last_1_month": 0.0, "last_3_months": 0.0, "last_6_months": 0.0, "last_1_year": 0.0}

    filtered_data = filtered_data.copy()
    filtered_data['TrxDate'] = pd.to_datetime(filtered_data['TrxDate'])
    target_date = pd.to_datetime(target_date)

    # Use ISO calendar for consistent monthly calculations
    filtered_data['ISOYear'] = filtered_data['TrxDate'].dt.isocalendar().year
    filtered_data['Month'] = filtered_data['TrxDate'].dt.month

    # Aggregate to monthly (using ISO year for consistency)
    monthly = filtered_data.groupby(['ISOYear', 'Month']).agg({
        'TotalQuantity': 'sum'
    }).reset_index()

    # Get target month (using ISO year)
    target_iso_year = target_date.isocalendar().year
    target_month = target_date.month
    target_month_num = target_iso_year * 12 + target_month

    # Filter historical months
    monthly['MonthNum'] = monthly['ISOYear'] * 12 + monthly['Month']
    historical = monthly[monthly['MonthNum'] < target_month_num]

    averages = {}
    periods = {"last_1_month": 1, "last_3_months": 3, "last_6_months": 6, "last_1_year": 12}

    for period_name, months in periods.items():
        start_month_num = target_month_num - months
        period_data = historical[historical['MonthNum'] >= start_month_num]
        averages[period_name] = float(period_data['TotalQuantity'].mean() if len(period_data) > 0 else 0)

    return averages

@router.post("/historical-averages")
async def get_historical_averages(filters: dict):
    """Get historical averages for popup"""
    if not data_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Data not loaded yet")

    dashboard_data = data_manager.get_demand_data()

    try:
        # Get parameters from filters
        route_code = filters.get('route_code', None)    # Single route code (for backward compatibility)
        route_codes = filters.get('route_codes', None)  # List of route codes for multiple routes
        item_codes = filters.get('item_codes', None)    # List of item codes for multiple items
        item_code = filters.get('item_code', None)      # Single item code
        target_date = filters.get('date', dashboard_data['TrxDate'].max())
        period = filters.get('period', 'Daily')

        # Filter data by route(s)
        filtered_data = dashboard_data.copy()

        if route_codes and len(route_codes) > 0:
            # Multiple routes
            route_codes_int = [int(rc) for rc in route_codes]
            filtered_data = filtered_data[filtered_data['RouteCode'].isin(route_codes_int)]
        elif route_code:
            # Single route (backward compatibility)
            filtered_data = filtered_data[filtered_data['RouteCode'] == int(route_code)]

        # Filter by items
        if item_codes and len(item_codes) > 0:
            # Multiple specific items selected
            filtered_data = filtered_data[filtered_data['ItemCode'].isin(item_codes)]
        elif item_code and item_code != 'All' and item_code != 'Multiple':
            # Single specific item selected
            filtered_data = filtered_data[filtered_data['ItemCode'] == item_code]
        # else: All items (no filtering)

        # Calculate period-specific averages using the filtered data
        if period == 'Daily':
            averages_data = calculate_calendar_daily_averages_from_data(filtered_data, target_date)
        elif period == 'Weekly':
            averages_data = calculate_calendar_weekly_averages_from_data(filtered_data, target_date)
        elif period == 'Monthly':
            averages_data = calculate_calendar_monthly_averages_from_data(filtered_data, target_date)
        else:
            raise ValueError(f"Invalid period: {period}")

        return HistoricalAverages(period=period, data=averages_data)

    except ValueError as e:
        logger.error(f"Invalid input for historical averages: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating historical averages: {str(e)}", exc_info=True)
        # Return empty data instead of error for better UX
        empty_data = {}
        if period == 'Daily':
            empty_data = {"last_1_week": 0.0, "last_1_month": 0.0, "last_3_months": 0.0, "last_6_months": 0.0, "last_1_year": 0.0}
        elif period == 'Weekly':
            empty_data = {"last_1_week": 0.0, "last_3_weeks": 0.0, "last_6_weeks": 0.0, "last_1_year": 0.0}
        elif period == 'Monthly':
            empty_data = {"last_1_month": 0.0, "last_3_months": 0.0, "last_6_months": 0.0, "last_1_year": 0.0}
        return HistoricalAverages(period=period, data=empty_data)