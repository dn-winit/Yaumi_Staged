from fastapi import APIRouter, HTTPException
import pandas as pd
import logging
import os
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core import data_manager
from backend.models.data_models import ForecastFilters, FilterOptions
from backend.utils.data_processor import get_filter_options, aggregate_by_period

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/forecast-filter-options", response_model=FilterOptions)
async def get_forecast_filter_options():
    """Get filter options for forecast data - only future dates"""
    if not data_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Data not loaded yet")

    demand_data = data_manager.get_demand_data()

    # Filter to only future dates starting from tomorrow
    tomorrow = datetime.now().date() + timedelta(days=1)
    demand_data['TrxDate'] = pd.to_datetime(demand_data['TrxDate'])
    future_data = demand_data[demand_data['TrxDate'].dt.date >= tomorrow]

    options = get_filter_options(future_data)
    return FilterOptions(**options)

@router.post("/forecast-data")
async def get_forecast_data(filters: ForecastFilters):
    """Get filtered forecast data - supports multi-select routes and items"""
    if not data_manager.is_loaded:
        raise HTTPException(status_code=503, detail="Data not loaded yet")

    data_source = data_manager.get_demand_data()

    try:
        # Filter to show only future dates (starting from tomorrow)
        tomorrow = datetime.now().date() + timedelta(days=1)
        filtered_df = data_source.copy()
        filtered_df['TrxDate'] = pd.to_datetime(filtered_df['TrxDate'])
        filtered_df = filtered_df[filtered_df['TrxDate'].dt.date >= tomorrow]

        # Ensure Predicted column exists
        if 'Predicted_Quantity' in filtered_df.columns and 'Predicted' not in filtered_df.columns:
            filtered_df['Predicted'] = filtered_df['Predicted_Quantity']

        # Filter by routes
        route_codes = filters.route_codes
        if route_codes and 'All' not in route_codes:
            route_codes_int = [int(rc) for rc in route_codes]
            filtered_df = filtered_df[filtered_df['RouteCode'].isin(route_codes_int)]

        # Filter by items
        item_codes = filters.item_codes
        if item_codes and 'All' not in item_codes:
            filtered_df = filtered_df[filtered_df['ItemCode'].isin(item_codes)]

        if filtered_df.empty:
            return {"chart_data": [], "table_data": []}

        # Aggregate by period
        aggregated_df = aggregate_by_period(filtered_df, filters.period)

        # Determine filter selections
        multiple_items_selected = len(filters.item_codes) > 1 or 'All' in filters.item_codes
        multiple_routes_selected = len(filters.route_codes) > 1 or 'All' in filters.route_codes
        single_route_selected = len(filters.route_codes) == 1 and 'All' not in filters.route_codes

        # Store original item-level data for breakdown
        item_level_df = aggregated_df.copy()

        chart_data = []

        if multiple_items_selected:
            # Multiple items selected - need item breakdown
            group_cols = ['TrxDate']

            # Include RouteCode in grouping based on route selection
            if single_route_selected:
                group_cols.append('RouteCode')
            elif multiple_routes_selected and 'All' not in filters.route_codes:
                group_cols.append('RouteCode')

            # Add period-specific columns
            if filters.period == 'Weekly':
                group_cols.extend(['ISOYear', 'ISOWeek'])
            elif filters.period == 'Monthly':
                group_cols.extend(['ISOYear', 'Month'])

            group_cols = [col for col in group_cols if col in item_level_df.columns]

            # Create aggregated view for table
            agg_dict = {'Predicted': 'sum'}
            aggregated_for_table = item_level_df.groupby(group_cols).agg(agg_dict).reset_index()

            # For chart data, get top items by volume for each date/route combination
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

                # Sort by predicted volume
                date_items = date_items.sort_values('Predicted', ascending=False)

                # Get top 10 items
                top_items = date_items.head(10)

                # Calculate "Others"
                others_predicted = date_items.iloc[10:]['Predicted'].sum() if len(date_items) > 10 else 0

                # Build breakdown for this date
                items_breakdown = []
                for _, item_row in top_items.iterrows():
                    items_breakdown.append({
                        'itemCode': item_row['ItemCode'],
                        'itemName': item_row.get('ItemName', ''),
                        'actual': 0,  # No actual for forecast
                        'predicted': int(item_row['Predicted'])
                    })

                if others_predicted > 0:
                    items_breakdown.append({
                        'itemCode': 'Others',
                        'itemName': 'Others',
                        'actual': 0,
                        'predicted': int(others_predicted)
                    })

                chart_data.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "route": route_display,
                    "item": "Multiple Items",
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
                        'actual': 0,
                        'predicted': int(item_row['Predicted'])
                    })

                table_data_list.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "route": str(int(route_code)) if isinstance(route_code, (int, float)) else route_code,
                    "item": f"{len(full_breakdown)} Items",
                    "predicted": int(agg_row['Predicted']),
                    "routeCode": str(int(route_code)) if isinstance(route_code, (int, float)) else route_code,
                    "itemCode": "Multiple",
                    "itemBreakdown": full_breakdown
                })

            table_data = table_data_list

        else:
            # Single item selected - handle route aggregation
            single_item_group_cols = ['TrxDate', 'ItemCode']

            if single_route_selected:
                single_item_group_cols.append('RouteCode')
            elif multiple_routes_selected and 'All' not in filters.route_codes:
                single_item_group_cols.append('RouteCode')

            # Add period columns
            if filters.period == 'Weekly':
                single_item_group_cols.extend(['ISOYear', 'ISOWeek'])
            elif filters.period == 'Monthly':
                single_item_group_cols.extend(['ISOYear', 'Month'])

            single_item_group_cols = [col for col in single_item_group_cols if col in aggregated_df.columns]

            # Aggregate data
            agg_dict = {'Predicted': 'sum'}
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
        logger.error(f"Error in get_forecast_data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))