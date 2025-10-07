from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.models.data_models import RecommendedOrderFilters, GenerateRecommendationsRequest
from backend.core import data_manager
from backend.core.priority_calculator import PriorityCalculator
from backend.core.cycle_calculator import IntelligentCycleCalculator
from backend.core.recommendation_storage import get_recommendation_storage
from backend.config import OUTPUT_DIR, QUANTITY_PARAMS, NEW_CUSTOMER_PARAMS, MAX_DAYS_SINCE_PURCHASE
from backend.utils.http_cache import cached_response
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

router = APIRouter()

class TieredRecommendationSystem:
    """Optimized FMCG recommendation system with unified priority scoring - Exact match with legacy"""

    def __init__(self):
        self.data_manager = data_manager
        self.priority_calculator = PriorityCalculator()
        # Initialize shared cycle calculator to match legacy system
        self.cycle_calculator = IntelligentCycleCalculator()
    
    def process_recommendations(self, target_date: str, route_code: str = None) -> pd.DataFrame:
        """Generate recommendations using robust FMCG algorithms"""
        # Validate target_date is provided
        if not target_date:
            raise ValueError("target_date is required for deterministic recommendation generation")

        # Load data
        demand_df, customer_df, journey_customers = self._load_data(target_date, route_code)
        
        if demand_df.empty or not journey_customers:
            return pd.DataFrame()
        
        # Get van inventory and item names
        van_items = demand_df.set_index('ItemCode')['Predicted'].to_dict()
        item_names = demand_df.set_index('ItemCode')['ItemName'].to_dict()
        actual_route_code = demand_df['RouteCode'].iloc[0] if not demand_df.empty else route_code
        
        # Load actual quantities for target date
        actual_quantities = self._load_actual_quantities(target_date, route_code)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            customer_df, journey_customers, van_items, item_names, actual_route_code, target_date, actual_quantities
        )
        
        if recommendations.empty:
            return pd.DataFrame()
        
        # Save results
        output_dir = OUTPUT_DIR / 'recommendations'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"recommended_order_{target_date.replace('-', '')}.csv"
        recommendations.to_csv(output_file, index=False)
        
        return recommendations
    
    def _load_data(self, target_date: str, route_code: str = None):
        """Load and prepare data with route filtering"""
        try:
            # Convert route_code to int if provided and not 'All'
            route_filter = None
            if route_code and route_code != 'All':
                try:
                    route_filter = int(route_code)
                except (ValueError, TypeError):
                    route_filter = None
            
            # Load data from data manager
            demand_df = self.data_manager.get_demand_data(route_filter)
            customer_df = self.data_manager.get_customer_data(route_filter)
            journey_df = self.data_manager.get_journey_plan(route_filter)
            
            if demand_df.empty or customer_df.empty or journey_df.empty:
                print(f"Warning: One or more datasets are empty for route {route_code}")
            
            # Standardize codes (data should already be cleaned from data_manager)
            for df in [demand_df, customer_df, journey_df]:
                for col in ['CustomerCode', 'ItemCode', 'RouteCode']:
                    if col in df.columns:
                        df[col] = df[col].astype(str).str.strip()
            
            # Get data for target date
            target_dt = pd.to_datetime(target_date)
            daily_demand = demand_df[demand_df['TrxDate'] == target_dt]
            
            # Get journey plan customers for target date
            journey_customers = journey_df[
                journey_df['JourneyDate'] == target_dt
            ]['CustomerCode'].unique().tolist()
            
            # Filter historical data (configurable days from settings)
            cutoff_date = target_dt - timedelta(days=MAX_DAYS_SINCE_PURCHASE)
            customer_df = customer_df[
                (customer_df['TrxDate'] >= cutoff_date) & 
                (customer_df['TrxDate'] < target_dt)
            ]
            
            return daily_demand, customer_df, journey_customers
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame(), pd.DataFrame(), []
    
    def _load_actual_quantities(self, target_date: str, route_code: str = None):
        """Load actual quantities for comparison"""
        try:
            # Convert route_code to int if provided and not 'All'
            route_filter = None
            if route_code and route_code != 'All':
                try:
                    route_filter = int(route_code)
                except (ValueError, TypeError):
                    route_filter = None
            
            # Load customer data from data manager
            customer_df = self.data_manager.get_customer_data(route_filter)
            
            if customer_df.empty:
                return {}
            
            # Standardize codes
            for col in ['CustomerCode', 'ItemCode', 'RouteCode']:
                if col in customer_df.columns:
                    customer_df[col] = customer_df[col].astype(str).str.strip()
            
            # Filter for target date
            target_dt = pd.to_datetime(target_date)
            target_sales = customer_df[customer_df['TrxDate'] == target_dt]
            
            # Create lookup dictionary: (RouteCode, CustomerCode, ItemCode) -> TotalQuantity
            actual_dict = {}
            for _, row in target_sales.iterrows():
                key = (str(row['RouteCode']), str(row['CustomerCode']), str(row['ItemCode']))
                actual_dict[key] = row['TotalQuantity']
            
            return actual_dict
            
        except Exception:
            return {}
    
    def _generate_recommendations(self, customer_df, journey_customers,
                                 van_items, item_names, route_code, target_date, actual_quantities):
        """Generate tiered recommendations using unified priority system"""
        # Ensure target_date is provided for deterministic generation
        if not target_date:
            raise ValueError("target_date is required for deterministic recommendations")

        target_dt = pd.to_datetime(target_date)
        recommendations = []

        # OPTIMIZATION: Pre-compute all customer-item histories as nested dictionary for O(1) lookup
        customer_item_histories = {}
        for customer in journey_customers:
            cust_history = customer_df[customer_df['CustomerCode'] == customer]
            if not cust_history.empty:
                # Convert grouped items to dictionary for instant O(1) lookup
                customer_item_histories[customer] = {
                    'history': cust_history,
                    'items': {item_code: group for item_code, group in cust_history.groupby('ItemCode')}
                }
            else:
                customer_item_histories[customer] = None

        # Sort customers for consistent processing order
        for customer in sorted(journey_customers):
            # Get pre-computed customer data
            customer_data = customer_item_histories[customer]

            if customer_data is None:
                # New customer - recommend popular items
                recommendations.extend(
                    self._recommend_for_new_customer(customer, van_items, item_names, route_code, target_date, actual_quantities)
                )
                continue

            cust_history = customer_data['history']
            item_dict = customer_data['items']

            # Analyze each item (sorted for consistency)
            sorted_items = sorted(van_items.items())
            for item, van_qty in sorted_items:
                if van_qty <= 0:
                    continue

                # OPTIMIZATION: O(1) dictionary lookup for item history
                if item not in item_dict:
                    continue

                # Get item history from pre-computed dictionary (instant O(1) access)
                item_history = item_dict[item]

                # Calculate metrics using unified priority system (with target_dt for determinism)
                metrics = self._calculate_item_metrics(item_history, cust_history, target_dt, customer, item, customer_df)

                if not metrics:
                    continue

                # Skip if priority too low (legacy threshold)
                if metrics['priority'] < 15:
                    continue

                # Direct priority-to-quantity mapping (EXACTLY like legacy)
                priority = metrics['priority']
                avg_qty = metrics['avg_qty']

                # Direct quantity calculation based on priority and average
                recommended_qty = self._calculate_direct_quantity(priority, avg_qty, van_qty)
                tier = self.priority_calculator.get_tier(priority, 'balanced')

                if recommended_qty > 0:
                    # Get actual quantity for this combination
                    actual_key = (str(route_code), str(customer), str(item))
                    actual_qty = actual_quantities.get(actual_key, 0)

                    # Final validation and bounds checking (matching legacy exactly)
                    avg_qty_final = metrics['avg_qty']
                    cycle_days_final = metrics['cycle_days']
                    frequency_final = metrics['frequency']
                    days_since_final = metrics['days_since']

                    # Handle edge cases exactly like legacy
                    if np.isnan(avg_qty_final) or np.isinf(avg_qty_final) or avg_qty_final <= 0:
                        avg_qty_final = 1
                    if avg_qty_final > 1000:
                        avg_qty_final = 1000

                    if np.isnan(cycle_days_final) or np.isinf(cycle_days_final) or cycle_days_final <= 0:
                        cycle_days_final = 30.0
                    if cycle_days_final > 365:
                        cycle_days_final = 365.0

                    frequency_percent = min(100, frequency_final * 100)

                    recommendations.append({
                        'TrxDate': target_date,
                        'RouteCode': route_code,
                        'CustomerCode': customer,
                        'ItemCode': item,
                        'ItemName': item_names.get(item, ''),
                        'ActualQuantity': int(actual_qty) if actual_qty else 0,
                        'RecommendedQuantity': int(recommended_qty),
                        'Tier': tier,
                        'VanLoad': van_qty,
                        'PriorityScore': round(priority, 1),
                        'AvgQuantityPerVisit': int(round(avg_qty_final)),
                        'DaysSinceLastPurchase': int(days_since_final),
                        'PurchaseCycleDays': round(cycle_days_final, 1),
                        'FrequencyPercent': round(frequency_percent, 1)
                    })

        # Convert to DataFrame and sort by priority
        df = pd.DataFrame(recommendations)
        if not df.empty:
            df = df.sort_values(['CustomerCode', 'PriorityScore'], ascending=[True, False])
            
            # Apply van load constraints
            df = self._apply_van_load_constraints(df)
            
            # Reorder columns for clean output
            column_order = [
                'TrxDate', 'RouteCode', 'CustomerCode', 'ItemCode', 'ItemName',
                'ActualQuantity', 'RecommendedQuantity', 'Tier', 'VanLoad',
                'PriorityScore', 'AvgQuantityPerVisit', 'DaysSinceLastPurchase',
                'PurchaseCycleDays', 'FrequencyPercent'
            ]
            df = df[column_order]

        return df
    
    def _apply_van_load_constraints(self, df):
        """Ensure total recommended quantity per item doesn't exceed van load"""
        if df.empty:
            return df
        
        for item_code in df['ItemCode'].unique():
            item_mask = df['ItemCode'] == item_code
            item_data = df[item_mask].copy()
            
            van_load = item_data['VanLoad'].iloc[0]
            total_recommended = item_data['RecommendedQuantity'].sum()
            
            # If total exceeds van load, allocate by priority
            if total_recommended > van_load:
                item_data = item_data.sort_values('PriorityScore', ascending=False)
                
                remaining_load = van_load
                for idx in item_data.index:
                    if remaining_load <= 0:
                        df.loc[idx, 'RecommendedQuantity'] = 0
                    else:
                        original_qty = df.loc[idx, 'RecommendedQuantity']
                        allocated_qty = min(original_qty, remaining_load)
                        df.loc[idx, 'RecommendedQuantity'] = allocated_qty
                        remaining_load -= allocated_qty
        
        # Remove recommendations with 0 quantity
        df = df[df['RecommendedQuantity'] > 0].copy()
        
        return df
    
    def _calculate_item_metrics(self, item_history, cust_history, target_dt, customer_code, item_code, total_customers_history):
        """Calculate metrics for customer-item relationship using unified priority system"""
        if item_history is None or item_history.empty:
            return None

        # Essential metrics only (matching legacy)
        last_purchase = item_history['TrxDate'].max()
        days_since = (target_dt - last_purchase).days

        # Use time-weighted average from cycle calculator (EXACTLY like legacy)
        avg_qty, confidence = self.cycle_calculator.calculate_time_weighted_value(
            item_history, 'TotalQuantity', 'adaptive', target_dt
        )

        # Robust cycle calculation with data validation and fallbacks
        cycle_days, cycle_confidence = self._calculate_robust_cycle(item_history)

        # Basic metrics
        purchase_count = len(item_history)
        total_visits = cust_history['TrxDate'].nunique()
        frequency = purchase_count / max(total_visits, 1)

        # For max_qty (used in determine_tier)
        max_qty = item_history['TotalQuantity'].max()

        # Use unified priority calculator (no inventory_level - operational component removed)
        priority, priority_components = self.priority_calculator.calculate_priority(
            customer_code=customer_code,
            item_code=item_code,
            customer_history=cust_history,
            total_customers_history=total_customers_history,
            target_date=target_dt
        )

        return {
            'frequency': frequency,
            'avg_qty': avg_qty,
            'max_qty': max_qty,
            'days_since': days_since,
            'cycle_days': cycle_days,
            'priority': priority,
            'priority_components': priority_components,
            'purchase_count': purchase_count
        }
    
    
    def _calculate_direct_quantity(self, priority, avg_qty, van_qty):
        """
        Direct priority-to-quantity mapping - EXACTLY like legacy
        Uses priority score and historical average directly
        """
        # Priority-based multiplier (0.3 to 1.5 range)
        # Linear mapping: priority 15->0.3, priority 100->1.5
        priority_multiplier = 0.3 + (priority / 100.0) * 1.2

        # Base quantity from historical average
        base_qty = max(1, round(avg_qty))

        # Apply priority multiplier
        recommended_qty = base_qty * priority_multiplier

        # Ensure minimum of 1 and reasonable maximum
        recommended_qty = max(1, min(round(recommended_qty), van_qty))

        return int(recommended_qty)
    
    def _recommend_for_new_customer(self, customer, van_items, item_names, route_code, target_date, actual_quantities):
        """Generate recommendations for new customers using demand-based selection"""
        recommendations = []

        # Select popular items by demand (not alphabetical)
        items_count = QUANTITY_PARAMS['NEW_CUSTOMER_ITEMS_COUNT']
        popular_items = [item[0] for item in sorted(van_items.items(), key=lambda x: x[1], reverse=True)[:items_count]]

        for item in popular_items:
            if van_items[item] > 0:
                # Get actual quantity for this combination
                actual_key = (str(route_code), str(customer), str(item))
                actual_qty = actual_quantities.get(actual_key, 0)

                recommended_qty = min(QUANTITY_PARAMS['NEW_CUSTOMER_QTY'], van_items[item])

                recommendations.append({
                    'TrxDate': target_date,
                    'RouteCode': route_code,
                    'CustomerCode': customer,
                    'ItemCode': item,
                    'ItemName': item_names.get(item, ''),
                    'ActualQuantity': int(actual_qty) if actual_qty else 0,
                    'RecommendedQuantity': int(recommended_qty),
                    'Tier': NEW_CUSTOMER_PARAMS['TIER'],
                    'VanLoad': van_items[item],
                    'PriorityScore': NEW_CUSTOMER_PARAMS['PRIORITY_SCORE'],
                    'AvgQuantityPerVisit': NEW_CUSTOMER_PARAMS['AVG_QUANTITY'],
                    'DaysSinceLastPurchase': NEW_CUSTOMER_PARAMS['DAYS_SINCE_LAST'],
                    'PurchaseCycleDays': NEW_CUSTOMER_PARAMS['CYCLE_DAYS'],
                    'FrequencyPercent': NEW_CUSTOMER_PARAMS['FREQUENCY_PERCENT']
                })

        return recommendations

    def _calculate_robust_cycle(self, item_history):
        """Use the intelligent cycle calculator for consistency with legacy system"""
        return self.cycle_calculator.calculate_cycle(item_history)


# API Endpoints - Modified to accept both date and route parameters
@router.get("/filter-options")
async def get_recommended_order_filter_options(
    date: Optional[str] = Query(None, description="Date for recommendations (YYYY-MM-DD)"),
    route_code: Optional[str] = Query(None, description="Route code to filter by"),
    customer_code: Optional[str] = Query(None, description="Customer code to filter items")
):
    """Get filter options strictly from recommendations stored in DB for the given date.
    - routes: all routes present for the date
    - customers: only when a specific route is provided (date+route)
    - items: from date+route (and optionally customer)
    No fallback to files or master data to avoid confusing, stale, or broad lists.
    """
    try:
        routes: list = []
        customers: list = []
        items: list = []

        rec_df = pd.DataFrame()
        normalized_date: Optional[str] = None

        # Normalize provided date
        if date:
            try:
                normalized_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                try:
                    normalized_date = datetime.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
                except ValueError:
                    normalized_date = None
        else:
            # Date is required to scope filter options to a single day of recommendations
            return cached_response({"routes": [], "items": [], "customers": []}, cache_type="filter_options")

        # Read recommendations for the exact date (and optional route)
        if normalized_date:
            try:
                storage = get_recommendation_storage()
                route_for_db = None if not route_code or route_code == 'All' else str(route_code)
                rec_df = storage.get_recommendations(normalized_date, route_for_db)
            except Exception:
                rec_df = pd.DataFrame()

        if not rec_df.empty:
            # Ensure string types and trimmed
            for col in ['RouteCode', 'CustomerCode', 'ItemCode', 'ItemName']:
                if col in rec_df.columns:
                    rec_df[col] = rec_df[col].astype(str).str.strip()

            # Build route list from recs (deduped)
            routes = [{"code": rc, "name": rc} for rc in sorted(rec_df['RouteCode'].astype(str).unique())]

            # Apply route filter if given
            if route_code and route_code != 'All':
                rec_df = rec_df[rec_df['RouteCode'].astype(str) == str(route_code)]

            # Customers strictly from recs; require route filter to avoid over-broad lists
            if route_code and route_code != 'All':
                customers = [{"code": cc, "name": cc} for cc in sorted(rec_df['CustomerCode'].astype(str).unique())]
            else:
                customers = []

            # Items from recs, optionally filtered by customer
            rec_items = rec_df
            if customer_code and customer_code != 'All':
                rec_items = rec_items[rec_items['CustomerCode'].astype(str) == str(customer_code)]
            if not rec_items.empty:
                items_data = rec_items[['ItemCode', 'ItemName']].drop_duplicates()
                items = [{"code": str(row['ItemCode']), "name": f"{row['ItemCode']} - {row['ItemName']}"}
                        for _, row in items_data.iterrows()]
                items = sorted(items, key=lambda x: x['code'])
            elif not (route_code and route_code != 'All'):
                # Without route/customer context, avoid presenting broad item lists
                items = []
        else:
            # No valid date or no recommendations found for date/route
            routes = []
            customers = []
            items = []

        return cached_response({"routes": routes, "items": items, "customers": customers}, cache_type="filter_options")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load filter options: {str(e)}")


@router.post("/generate-recommendations")
async def generate_recommendations(request: GenerateRecommendationsRequest):
    """Generate recommendations for a specific date and optionally route code"""
    try:
        # Check if data manager is loaded
        if not data_manager.is_loaded:
            raise HTTPException(status_code=503, detail="Data not loaded yet. Please wait for data initialization.")
        
        target_date = request.date
        route_code = request.route_code  # Optional route code parameter
        force_regenerate = getattr(request, 'force_regenerate', False)  # Optional force regenerate flag
        
        # Validate and normalize date format - handle both YYYY-MM-DD and MM/DD/YYYY
        try:
            # Try YYYY-MM-DD format first
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
            target_date = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            try:
                # Try MM/DD/YYYY format (frontend format)
                parsed_date = datetime.strptime(target_date, '%m/%d/%Y')
                target_date = parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY format.")
        
        # Use the working recommendation system
        system = TieredRecommendationSystem()
        results = system.process_recommendations(target_date, route_code)
        
        if results.empty:
            error_msg = f"No recommendations could be generated for date {target_date}"
            if route_code:
                error_msg += f" and route {route_code}"
            error_msg += ". Check if data exists for this date and route combination."
            raise HTTPException(status_code=404, detail=error_msg)
        
        return {
            "message": f"Generated {len(results)} recommendations for {target_date}" + (f" (Route: {route_code})" if route_code else ""),
            "recommendations_count": len(results),
            "date": target_date,
            "route_code": route_code
        }
    except HTTPException as e:
        # Preserve intended status (e.g., 404)
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.post("/pre-generate-daily")
async def pre_generate_daily_recommendations(
    date: str = Query(..., description="Target date (YYYY-MM-DD)"),
    route_code: str = Query(default="1004", description="Route code (default: 1004)")
):
    """
    Pre-generate recommendations for a specific date and save to database

    **Use Case:** Called by cron job nightly (3 AM Gulf/Asia time)

    **Benefits:**
    - Users get instant responses (< 1 second)
    - No waiting time during business hours
    - Consistent data throughout the day

    **Cron Schedule:** Run daily at 3:00 AM local time
    - For UAE/Saudi (UTC+4): 11:00 PM UTC previous day
    - For Pakistan/India (UTC+5): 10:00 PM UTC previous day

    **Example:** curl -X POST "https://yaumi-live.onrender.com/api/v1/recommended-order/pre-generate-daily?date=2025-10-08"
    """
    try:
        # Check if data manager is loaded
        if not data_manager.is_loaded:
            raise HTTPException(
                status_code=503,
                detail="Data not loaded yet. Please wait for data initialization."
            )

        # Validate date format
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
            target_date = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD format (e.g., 2025-10-08)"
            )

        storage = get_recommendation_storage()

        # Check if already exists
        exists = storage.check_exists(target_date, route_code)
        if exists:
            info = storage.get_generation_info(target_date)
            return {
                "success": True,
                "message": f"Recommendations already exist for {target_date}",
                "action": "skipped",
                "date": target_date,
                "route_code": route_code,
                "existing_records": info.get('total_records', 0),
                "generated_at": info.get('generated_at')
            }

        # Generate recommendations
        print(f"[CRON] Starting recommendation generation for {target_date}, route {route_code}")
        start_time = datetime.now()

        system = TieredRecommendationSystem()
        recommendations_df = system.process_recommendations(target_date, route_code)

        if recommendations_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data available to generate recommendations for {target_date}"
            )

        # Save to database
        save_result = storage.save_recommendations(recommendations_df, target_date, route_code)

        generation_time = (datetime.now() - start_time).total_seconds()

        if save_result['success']:
            print(f"[CRON] Successfully saved {save_result['records_saved']} recommendations for {target_date}")
            return {
                "success": True,
                "message": f"Successfully generated and saved recommendations for {target_date}",
                "action": "generated",
                "date": target_date,
                "route_code": route_code,
                "records_saved": save_result['records_saved'],
                "generation_time_seconds": round(generation_time, 2),
                "generated_at": save_result['generated_at']
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save recommendations: {save_result['message']}"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CRON] Error during pre-generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Pre-generation failed: {str(e)}"
        )


@router.post("/get-recommendations-data")
async def get_recommended_order_data(filters: RecommendedOrderFilters):
    """
    Get recommended order data with multi-select filtering
    Fetches from database for instant response, generates on-demand if not found
    """
    try:
        # Check if data manager is loaded
        if not data_manager.is_loaded:
            raise HTTPException(status_code=503, detail="Data not loaded yet. Please wait for data initialization.")

        # Normalize date (support YYYY-MM-DD and MM/DD/YYYY like other endpoints)
        target_date = filters.date
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
            target_date = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            try:
                parsed_date = datetime.strptime(target_date, '%m/%d/%Y')
                target_date = parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY format.")

        storage = get_recommendation_storage()

        # Try to fetch from database first (FAST - instant response)
        # If a single route is selected (and not 'All'), fetch by route in SQL to reduce payload
        route_codes = filters.route_codes
        single_route = None
        if route_codes and 'All' not in route_codes and len(route_codes) == 1:
            single_route = str(route_codes[0])

        recommendations_df = storage.get_recommendations(target_date, single_route)
        data_source = "database"

        if recommendations_df.empty:
            # Not in database - generate on demand (SLOW - first time only)
            print(f"[INFO] No recommendations in database for {target_date}, generating...")

            try:
                system = TieredRecommendationSystem()
                recommendations_df = system.process_recommendations(target_date, None)

                if recommendations_df.empty:
                    raise HTTPException(status_code=404, detail=f"No data available for {target_date}")

                print(f"Generated {len(recommendations_df)} recommendations for {target_date}")

                # Save to database for next time – persist per route for correct delete/replace behavior
                total_saved = 0
                for rc in sorted(recommendations_df['RouteCode'].astype(str).unique()):
                    df_route = recommendations_df[recommendations_df['RouteCode'].astype(str) == rc]
                    save_result = storage.save_recommendations(df_route, target_date, rc)
                    if save_result['success']:
                        total_saved += save_result['records_saved']
                if total_saved > 0:
                    print(f"[INFO] Saved {total_saved} recommendations to database")

                data_source = "generated"

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to generate recommendations for {target_date}: {str(e)}")
        else:
            print(f"[INFO] Loaded {len(recommendations_df)} recommendations from database for {target_date}")
            data_source = "database"

        # Apply filters
        filtered_df = recommendations_df.copy()

        # Filter by routes (multi-select)
        route_codes = filters.route_codes
        if route_codes and 'All' not in route_codes:
            filtered_df = filtered_df[filtered_df['RouteCode'].astype(str).isin([str(rc) for rc in route_codes])]

        # Filter by customers (multi-select)
        customer_codes = filters.customer_codes
        if customer_codes and 'All' not in customer_codes:
            filtered_df = filtered_df[filtered_df['CustomerCode'].astype(str).isin([str(cc) for cc in customer_codes])]

        # Filter by items (multi-select)
        item_codes = filters.item_codes
        if item_codes and 'All' not in item_codes:
            filtered_df = filtered_df[filtered_df['ItemCode'].astype(str).isin([str(ic) for ic in item_codes])]

        if filtered_df.empty:
            return {
                "chart_data": [],
                "table_data": [],
                "status": data_source,
                "message": f"No data matches the selected filters for {target_date}"
            }

        # Determine aggregation strategy
        multiple_customers = len(filters.customer_codes) > 1 or 'All' in filters.customer_codes
        multiple_items = len(filters.item_codes) > 1 or 'All' in filters.item_codes

        # Convert function for individual items
        def convert_item_to_api_format(df_row):
            if 'PriorityScore' in df_row:
                priority_score = float(df_row['PriorityScore'])
                return {
                    "trxDate": str(df_row['TrxDate']),
                    "routeCode": str(df_row['RouteCode']),
                    "customerCode": str(df_row.get('CustomerCode', '')),
                    "itemCode": str(df_row['ItemCode']),
                    "itemName": str(df_row['ItemName']),
                    "actualQuantity": int(df_row['ActualQuantity']),
                    "recommendedQuantity": int(df_row['RecommendedQuantity']),
                    "tier": str(df_row['Tier']),
                    "vanLoad": int(df_row['VanLoad']),
                    "priorityScore": priority_score,
                    "probabilityPercent": priority_score,
                    "urgencyScore": priority_score,
                    "avgQuantityPerVisit": int(df_row['AvgQuantityPerVisit']),
                    "daysSinceLastPurchase": int(df_row['DaysSinceLastPurchase']),
                    "purchaseCycleDays": int(df_row['PurchaseCycleDays']),
                    "frequencyPercent": float(df_row['FrequencyPercent'])
                }
            else:
                return {
                    "trxDate": str(df_row['TrxDate']),
                    "routeCode": str(df_row['RouteCode']),
                    "customerCode": str(df_row.get('CustomerCode', '')),
                    "itemCode": str(df_row['ItemCode']),
                    "itemName": str(df_row['ItemName']),
                    "actualQuantity": int(df_row['ActualQuantity']),
                    "recommendedQuantity": int(df_row['RecommendedQuantity']),
                    "tier": str(df_row['Tier']),
                    "vanLoad": int(df_row['VanLoad']),
                    "probabilityPercent": float(df_row.get('ProbabilityPercent', 0)),
                    "avgQuantityPerVisit": int(df_row['AvgQuantityPerVisit']),
                    "daysSinceLastPurchase": int(df_row['DaysSinceLastPurchase']),
                    "purchaseCycleDays": int(df_row['PurchaseCycleDays']),
                    "frequencyPercent": float(df_row['FrequencyPercent']),
                    "urgencyScore": float(df_row.get('UrgencyScore', 0))
                }

        # Build chart and table data
        chart_data = []
        table_data = []

        if multiple_customers:
            # Customer-based aggregation with item breakdown
            for customer_code in sorted(filtered_df['CustomerCode'].unique()):
                customer_items = filtered_df[filtered_df['CustomerCode'] == customer_code]

                # Build customer breakdown (all items for this customer)
                customer_breakdown = []
                for _, item_row in customer_items.iterrows():
                    customer_breakdown.append(convert_item_to_api_format(item_row))

                # Create aggregated customer row
                customer_summary = {
                    "trxDate": str(customer_items['TrxDate'].iloc[0]),
                    "routeCode": str(customer_items['RouteCode'].iloc[0]),
                    "customerCode": str(customer_code),
                    "itemCode": "Multiple",
                    "itemName": f"{len(customer_items)} Items",
                    "actualQuantity": int(customer_items['ActualQuantity'].sum()),
                    "recommendedQuantity": int(customer_items['RecommendedQuantity'].sum()),
                    "tier": "MULTIPLE",
                    "vanLoad": 0,
                    "priorityScore": 0,
                    "probabilityPercent": 0,
                    "urgencyScore": 0,
                    "avgQuantityPerVisit": 0,
                    "daysSinceLastPurchase": 0,
                    "purchaseCycleDays": 0,
                    "frequencyPercent": 0,
                    "customerBreakdown": customer_breakdown
                }

                table_data.append(customer_summary)

            # For chart, use all individual items
            chart_data = [convert_item_to_api_format(row) for _, row in filtered_df.iterrows()]

        else:
            # Single customer - show all items directly (no aggregation needed)
            for _, row in filtered_df.iterrows():
                item_data = convert_item_to_api_format(row)
                table_data.append(item_data)
                chart_data.append(item_data)

        # Create status message
        if data_source == "loaded":
            status_message = f"Recommended order loaded successfully for {target_date}"
        else:
            status_message = f"Recommended order generated successfully for {target_date}"

        return {
            "chart_data": chart_data,
            "table_data": table_data,
            "status": data_source,
            "message": status_message
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommended order data: {str(e)}")


