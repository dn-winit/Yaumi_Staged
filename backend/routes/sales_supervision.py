from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from datetime import datetime
import pandas as pd
import os
import sys
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core import data_manager
from backend.models.data_models import SalesSupervisionFilters
from backend.routes.recommended_order import TieredRecommendationSystem
from backend.core.dynamic_supervisor import get_or_create_session, clear_session
from backend.core.llm_analyzer import llm_analyzer
from backend.core.recommendation_storage import get_recommendation_storage

router = APIRouter()
logger = logging.getLogger(__name__)

# All recommendations are now stored in database (tbl_recommended_orders)
# No CSV files or local directories needed

def calculate_item_accuracy(actual_qty: int, recommended_qty: int) -> float:
    """
    Calculate item accuracy score with perfect zone (75-120% of recommended).
    Perfect zone = 100%, Outside zone = Linear penalty
    """
    if recommended_qty == 0:
        return 100.0 if actual_qty == 0 else 0.0

    if actual_qty == 0:
        return 0.0

    achievement_pct = (actual_qty / recommended_qty) * 100

    # Perfect zone: 75-120%
    if 75 <= achievement_pct <= 120:
        return 100.0

    # Below 75%: Linear penalty from 0% to 75%
    elif achievement_pct < 75:
        return max(0, (achievement_pct / 75) * 100)

    # Above 120%: Linear penalty from 120% to 200%
    else:
        if achievement_pct >= 200:
            return 0.0
        return max(0, 100 - ((achievement_pct - 120) / 80 * 100))

def calculate_customer_score(customer_data: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate customer score with two components: Coverage and Accuracy.
    Returns dict with score, coverage, and accuracy percentages.
    """
    if customer_data.empty:
        return {'score': 0.0, 'coverage': 0.0, 'accuracy': 0.0}

    total_items = len(customer_data)
    items_sold = len(customer_data[customer_data['ActualQuantity'] > 0])

    # Coverage: percentage of items sold
    coverage_score = (items_sold / total_items) * 100

    # Accuracy: average accuracy of all items
    accuracy_scores = []
    for _, item_row in customer_data.iterrows():
        item_accuracy = calculate_item_accuracy(
            item_row['ActualQuantity'],
            item_row['RecommendedQuantity']
        )
        accuracy_scores.append(item_accuracy)

    accuracy_score = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0

    # Final score: Coverage (40%) + Accuracy (60%)
    final_score = (coverage_score * 0.4) + (accuracy_score * 0.6)

    return {
        'score': round(final_score, 1),
        'coverage': round(coverage_score, 1),
        'accuracy': round(accuracy_score, 1)
    }

@router.get("/filter-options")
async def get_sales_supervision_filter_options():
    """Get filter options for sales supervision"""
    try:
        if not data_manager.is_loaded:
            raise HTTPException(status_code=503, detail="Data not loaded yet")
        
        # Get data from data manager
        demand_df = data_manager.get_demand_data()
        journey_df = data_manager.get_journey_plan()
        
        # Get unique routes
        routes = sorted(demand_df['RouteCode'].unique().tolist())
        route_options = [{"code": str(route), "name": str(route)} for route in routes]
        
        # Get unique dates from journey plan (these are the valid supervision dates)
        dates = []
        if not journey_df.empty:
            dates = journey_df['JourneyDate'].dt.strftime('%Y-%m-%d').unique().tolist()
            dates.sort()
        
        return {
            "routes": route_options,
            "dates": dates
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load filter options: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-sales-data")
async def get_sales_supervision_data(filters: SalesSupervisionFilters):
    """Get sales supervision data for a specific route and date"""
    try:
        route_code = filters.route_code
        target_date = filters.date
        
        # Validate inputs
        if not route_code or not target_date:
            raise HTTPException(status_code=400, detail="Route code and date are required")
        
        # Check if data manager is loaded
        if not data_manager.is_loaded:
            raise HTTPException(status_code=503, detail="Data not loaded yet. Please wait for data initialization.")
        
        # Load demand data from data manager
        demand_df = data_manager.get_demand_data()
        
        # Convert TrxDate to datetime if not already
        demand_df['TrxDate'] = pd.to_datetime(demand_df['TrxDate'])
        
        # Parse target date
        try:
            target_date_parsed = pd.to_datetime(target_date)
        except:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")
        
        # Filter demand data by route and date
        demand_filtered = demand_df[
            (demand_df['RouteCode'].astype(str) == str(route_code)) & 
            (demand_df['TrxDate'].dt.date == target_date_parsed.date())
        ]
        
        # Prepare demand section data
        demand_items = []
        if not demand_filtered.empty:
            # The merged demand data has columns: TotalQuantity, AvgUnitPrice, Predicted
            # Group by item to get aggregated demand
            demand_grouped = demand_filtered.groupby(['ItemCode', 'ItemName']).agg({
                'Predicted': 'sum',  # Use Predicted as allocated quantity
                'TotalQuantity': 'sum',  # Actual quantity
                'AvgUnitPrice': 'mean'  # Average price
            }).reset_index()
            
            for _, row in demand_grouped.iterrows():
                demand_items.append({
                    "itemCode": str(row['ItemCode']),
                    "itemName": str(row['ItemName']),
                    "allocatedQuantity": float(row['Predicted']),  # Predicted as allocated
                    "totalQuantity": float(row['TotalQuantity']),  # Actual quantity
                    "avgPrice": round(float(row['AvgUnitPrice']), 2) if pd.notna(row['AvgUnitPrice']) else 0
                })
        
        # Check if recommended order exists in database for this date
        recommended_order_data = []
        customer_scores = {}

        # Get recommendations from database
        storage = get_recommendation_storage()
        rec_df = storage.get_recommendations(target_date, str(route_code))

        if not rec_df.empty:
            # Recommendations exist in database
            rec_filtered = rec_df

            if not rec_filtered.empty:
                # Group by customer
                customers = rec_filtered['CustomerCode'].unique()
                
                for customer in customers:
                    customer_data = rec_filtered[rec_filtered['CustomerCode'] == customer]
                    
                    # Calculate performance score with new algorithm
                    total_recommended = customer_data['RecommendedQuantity'].sum()
                    total_actual = customer_data['ActualQuantity'].sum()

                    # Get score breakdown (score, coverage, accuracy)
                    score_data = calculate_customer_score(customer_data)

                    customer_scores[str(customer)] = score_data['score']

                    # Prepare customer items
                    items = []
                    for _, item_row in customer_data.iterrows():
                        item_actual = int(item_row['ActualQuantity'])
                        item_recommended = int(item_row['RecommendedQuantity'])

                        # Calculate item accuracy
                        item_accuracy = calculate_item_accuracy(item_actual, item_recommended)

                        # Handle both old and new recommendation formats
                        prob_percent = 0.0
                        urgency_score = 0.0

                        if 'PriorityScore' in item_row:
                            priority_score = float(item_row['PriorityScore'])
                            prob_percent = priority_score
                            urgency_score = priority_score
                        else:
                            prob_percent = float(item_row.get('ProbabilityPercent', 0))
                            urgency_score = float(item_row.get('UrgencyScore', 0))

                        items.append({
                            "itemCode": str(item_row['ItemCode']),
                            "itemName": str(item_row['ItemName']),
                            "actualQuantity": item_actual,
                            "recommendedQuantity": item_recommended,
                            "accuracy": round(item_accuracy, 1),
                            "tier": str(item_row['Tier']),
                            "probabilityPercent": prob_percent,
                            "urgencyScore": urgency_score
                        })

                    recommended_order_data.append({
                        "customerCode": str(customer),
                        "customerName": f"Customer {customer}",
                        "score": score_data['score'],
                        "coverage": score_data['coverage'],
                        "accuracy": score_data['accuracy'],
                        "items": items,
                        "totalItems": len(items),
                        "totalRecommendedQty": int(total_recommended),
                        "totalActualQty": int(total_actual)
                    })
                
                # Sort customers by score (highest first)
                recommended_order_data = sorted(recommended_order_data, key=lambda x: x['score'], reverse=True)
        
        return {
            "route": str(route_code),
            "date": target_date,
            "demandSection": {
                "items": demand_items,
                "totalItems": len(demand_items),
                "totalAllocatedQty": sum(item['allocatedQuantity'] for item in demand_items),
                "totalQty": sum(item['totalQuantity'] for item in demand_items)
            },
            "recommendedOrderSection": {
                "hasData": len(recommended_order_data) > 0,
                "customers": recommended_order_data,
                "totalCustomers": len(recommended_order_data),
                "avgScore": round(sum(c['score'] for c in recommended_order_data) / len(recommended_order_data), 1) if recommended_order_data else 0,
                "scoreType": "performance"  # Indicates this is actual vs recommended performance
            }
        }

    except HTTPException:
        raise  # Re-raise HTTPExceptions with original status codes
    except Exception as e:
        logger.error(f"Unexpected error in get_sales_supervision_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sales supervision data: {str(e)}")


# Removed: /generate-recommendations-for-date endpoint
# Now uses unified /api/v1/recommended-order/get-recommendations-data endpoint
# Frontend calls getRecommendedOrderData() which auto-generates if needed


@router.post("/initialize-session")
async def initialize_dynamic_session(filters: SalesSupervisionFilters):
    """Initialize or reinitialize a dynamic supervision session"""
    try:
        route_code = filters.route_code
        target_date = filters.date

        if not route_code or not target_date:
            raise HTTPException(status_code=400, detail="Route code and date are required")

        # Clear any existing session for this route/date
        clear_session(route_code, target_date)

        # Create new session
        session = get_or_create_session(route_code, target_date)

        # Parse date
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")

        # Load recommendations from database
        storage = get_recommendation_storage()
        rec_df = storage.get_recommendations(target_date, str(route_code) if route_code != 'All' else None)

        if rec_df.empty:
            # Generate recommendations if not exists in database
            logger.info(f"Recommendations not found in database, generating for {target_date}")
            system = TieredRecommendationSystem()
            results = system.process_recommendations(target_date, route_code if route_code != 'All' else None)

            if results.empty:
                raise HTTPException(status_code=404, detail=f"No recommendations could be generated for {target_date}")

            # Save to database
            save_result = storage.save_recommendations(results, target_date, str(route_code) if route_code != 'All' else '1004')
            if not save_result['success']:
                logger.warning(f"Failed to save recommendations to database: {save_result['message']}")

            # Use the generated results
            rec_df = results

        if rec_df.empty:
            raise HTTPException(status_code=404, detail=f"No recommendations found for route {route_code} on {target_date}")

        # Initialize session with recommendations
        success = session.initialize_from_recommendations(rec_df)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to initialize supervision session")

        # Get session summary
        summary = session.get_session_summary()

        return {
            "success": True,
            "message": f"Session initialized for route {route_code} on {target_date}",
            "session": summary
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to initialize session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize session: {str(e)}")


@router.post("/process-visit")
async def process_customer_visit(request: Dict[str, Any] = Body(...)):
    """Process a customer visit and get redistribution recommendations"""
    try:
        route_code = request.get('route_code')
        target_date = request.get('date')
        customer_code = request.get('customer_code')
        actual_sales = request.get('actual_sales', {})

        if not all([route_code, target_date, customer_code]):
            raise HTTPException(status_code=400, detail="Missing required parameters")

        # Get active session
        session = get_or_create_session(route_code, target_date)

        # Process the visit
        result = session.process_visit(customer_code, actual_sales)

        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])

        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to process visit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process visit: {str(e)}")


@router.post("/get-session-summary")
async def get_session_summary(filters: SalesSupervisionFilters):
    """Get current session summary"""
    try:
        route_code = filters.route_code
        target_date = filters.date

        if not route_code or not target_date:
            raise HTTPException(status_code=400, detail="Route code and date are required")

        # Get active session
        session = get_or_create_session(route_code, target_date)

        # Return summary
        return session.get_session_summary()

    except Exception as e:
        logger.error(f"Failed to get session summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session summary: {str(e)}")


@router.post("/analyze-customer")
async def analyze_customer_performance(request: Dict[str, Any] = Body(...)):
    """Generate advanced analysis for individual customer performance"""
    try:
        customer_code = request.get('customer_code')
        route_code = request.get('route_code')
        date = request.get('date')

        if not all([customer_code, route_code, date]):
            raise HTTPException(status_code=400, detail="Missing required parameters")

        # Parse date
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")

        # Load recommendations from database
        storage = get_recommendation_storage()
        rec_df = storage.get_recommendations(date, str(route_code))

        if rec_df.empty:
            raise HTTPException(status_code=404, detail="Recommended order data not found for this date and route")

        # Filter by route and customer
        customer_rec_data = rec_df[
            (rec_df['RouteCode'].astype(str) == str(route_code)) &
            (rec_df['CustomerCode'].astype(str) == str(customer_code))
        ]

        if customer_rec_data.empty:
            raise HTTPException(status_code=404, detail="No data found for this customer")

        # Calculate performance score with new algorithm
        score_data = calculate_customer_score(customer_rec_data)

        # Format current visit items
        current_items = []
        for _, item_row in customer_rec_data.iterrows():
            current_items.append({
                'itemCode': str(item_row['ItemCode']),
                'itemName': str(item_row['ItemName']),
                'recommendedQuantity': int(item_row['RecommendedQuantity']),
                'actualQuantity': int(item_row['ActualQuantity'])
            })

        # Calculate SKUs sold
        skus_sold = len(customer_rec_data[customer_rec_data['ActualQuantity'] > 0])

        # Generate advanced analysis - returns structured JSON
        analysis_json = llm_analyzer.analyze_customer_performance(
            customer_code=customer_code,
            route_code=route_code,
            date=date,
            customer_data=customer_rec_data,
            current_items=current_items,
            performance_score=score_data['score'],
            coverage=score_data['coverage'],
            accuracy=score_data['accuracy']
        )

        # Return merged response with analysis and metrics
        return {
            **analysis_json,
            "performance_score": score_data['score'],
            "coverage": score_data['coverage'],
            "accuracy": score_data['accuracy'],
            "total_items": len(current_items),
            "skus_sold": skus_sold,
            "total_recommended": int(customer_rec_data['RecommendedQuantity'].sum()),
            "total_actual": int(customer_rec_data['ActualQuantity'].sum())
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to analyze customer performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")


@router.post("/analyze-customer-with-updates")
async def analyze_customer_performance_with_updates(request: Dict[str, Any] = Body(...)):
    """Generate advanced analysis for customer with updated actual quantities"""
    try:
        customer_code = request.get('customer_code')
        route_code = request.get('route_code')
        date = request.get('date')
        actual_quantities = request.get('actual_quantities', {})

        if not all([customer_code, route_code, date]):
            raise HTTPException(status_code=400, detail="Missing required parameters")

        # Parse date
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")

        # Load recommendations from database
        storage = get_recommendation_storage()
        rec_df = storage.get_recommendations(date, str(route_code))

        if rec_df.empty:
            raise HTTPException(status_code=404, detail="Recommended order data not found for this date and route")
        customer_rec_data = rec_df[
            (rec_df['RouteCode'].astype(str) == str(route_code)) &
            (rec_df['CustomerCode'].astype(str) == str(customer_code))
        ].copy()

        if customer_rec_data.empty:
            raise HTTPException(status_code=404, detail="No data found for this customer")

        # Update actual quantities with frontend edits (simulating real-time visit updates)
        for idx, item_row in customer_rec_data.iterrows():
            item_code = str(item_row['ItemCode'])
            if item_code in actual_quantities:
                customer_rec_data.at[idx, 'ActualQuantity'] = actual_quantities[item_code]

        # Calculate performance score with updated data
        score_data = calculate_customer_score(customer_rec_data)

        # Calculate SKUs sold
        skus_sold = len(customer_rec_data[customer_rec_data['ActualQuantity'] > 0])

        # Format current visit items with updated quantities
        current_items = []
        for _, item_row in customer_rec_data.iterrows():
            current_items.append({
                'itemCode': str(item_row['ItemCode']),
                'itemName': str(item_row['ItemName']),
                'recommendedQuantity': int(item_row['RecommendedQuantity']),
                'actualQuantity': int(item_row['ActualQuantity'])
            })

        # Generate advanced analysis - returns structured JSON
        analysis_json = llm_analyzer.analyze_customer_performance(
            customer_code=customer_code,
            route_code=route_code,
            date=date,
            customer_data=customer_rec_data,
            current_items=current_items,
            performance_score=score_data['score'],
            coverage=score_data['coverage'],
            accuracy=score_data['accuracy']
        )

        # Return merged response with analysis and metrics
        return {
            **analysis_json,
            "performance_score": score_data['score'],
            "coverage": score_data['coverage'],
            "accuracy": score_data['accuracy'],
            "total_items": len(current_items),
            "skus_sold": skus_sold,
            "total_recommended": int(customer_rec_data['RecommendedQuantity'].sum()),
            "total_actual": int(customer_rec_data['ActualQuantity'].sum())
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to analyze customer performance with updates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")


@router.post("/analyze-route-with-visited-data")
async def analyze_route_performance_with_visited_data(request: Dict[str, Any] = Body(...)):
    """Generate advanced analysis for route performance using real visited customer data"""
    try:
        route_code = request.get('route_code')
        date = request.get('date')
        all_customers = request.get('all_customers', [])
        visited_customers_data = request.get('visited_customers_data', [])

        if not all([route_code, date]):
            raise HTTPException(status_code=400, detail="Missing required parameters")

        # Calculate route metrics using real visited customer data
        total_customers = len(all_customers)
        visited_customers = len(visited_customers_data)
        coverage_percentage = (visited_customers / total_customers * 100) if total_customers > 0 else 0.0

        # Calculate weighted average score of visited customers
        if visited_customers > 0:
            total_score = sum(customer.get('score', 0) for customer in visited_customers_data)
            weighted_average_score = total_score / visited_customers
        else:
            weighted_average_score = 0.0

        overall_metrics = {
            'totalCustomers': total_customers,
            'visitedCustomers': visited_customers,
            'coveragePercentage': coverage_percentage,
            'weightedAverageScore': weighted_average_score,
            'averageScore': weighted_average_score  # For compatibility
        }

        # Load the full recommended order for pre-context
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

        # Load recommendations from database
        storage = get_recommendation_storage()
        route_data = storage.get_recommendations(date, str(route_code) if route_code != 'All' else None)

        # Generate advanced analysis - returns structured JSON
        analysis_json = llm_analyzer.analyze_route_performance(
            route_code=route_code,
            date=date,
            route_data=route_data,  # Full planning context
            visited_customers=visited_customers_data,  # Actual visited data
            coverage_metrics=overall_metrics
        )

        # Return merged response with analysis and metrics
        return {
            **analysis_json,
            "date": date,
            "metrics": overall_metrics
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to analyze route performance with visited data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate route analysis: {str(e)}")


@router.get("/analysis-health")
async def check_analysis_health():
    """Check analysis service health"""
    try:
        health_status = llm_analyzer.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Failed to check analysis health: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/save-supervision-state")
async def save_supervision_state(request: Request):
    """
    Save complete supervision session state to database

    Frontend sends:
    - route_code, date
    - visited_customers: [{customer_code, visit_sequence, llm_analysis}]
    - actual_quantities: {customer_code: {item_code: quantity}}
    - adjustments: {customer_code: {item_code: adjustment_amount}}
    - route_llm_analysis: string

    Backend fetches full data from tbl_recommended_orders and builds complete payload
    """
    try:
        from backend.core.supervision_storage import get_supervision_storage
        from datetime import datetime

        data = await request.json()

        route_code = data.get('route_code')
        date_str = data.get('date')
        visited_customers = data.get('visited_customers', [])  # [{customer_code, visit_sequence, llm_analysis}]
        actual_quantities = data.get('actual_quantities', {})  # {customer_code: {item_code: qty}}
        adjustments = data.get('adjustments', {})  # {customer_code: {item_code: adjustment}}
        route_llm_analysis = data.get('route_llm_analysis', '')

        if not route_code or not date_str:
            raise HTTPException(status_code=400, detail="Missing route_code or date")

        if not visited_customers:
            raise HTTPException(status_code=400, detail="No visited customers to save")

        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Get full recommendation data from database
        rec_storage = get_recommendation_storage()
        rec_df = rec_storage.get_recommendations(date_str, str(route_code))

        if rec_df.empty:
            raise HTTPException(status_code=404, detail="No recommendations found for this route and date")

        # Get journey plan to count total planned customers
        journey_df = data_manager.get_journey_plan()
        journey_filtered = journey_df[
            (journey_df['RouteCode'].astype(str) == str(route_code)) &
            (journey_df['TrxDate'].dt.date == target_date.date())
        ]
        total_customers_planned = len(journey_filtered['CustomerCode'].unique()) if not journey_filtered.empty else 0

        # Generate unique session ID with microseconds and random suffix
        import uuid
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')  # Include microseconds
        random_suffix = uuid.uuid4().hex[:8]
        session_id = f"{route_code}_{date_str}_{timestamp}_{random_suffix}"

        # Build customer summaries and item details
        customer_summaries = []
        item_details = []

        visited_customer_codes = [vc['customer_code'] for vc in visited_customers]
        visit_sequence_map = {vc['customer_code']: vc['visit_sequence'] for vc in visited_customers}
        llm_analysis_map = {vc['customer_code']: vc.get('llm_analysis', '') for vc in visited_customers}

        route_total_skus_recommended = 0
        route_total_skus_sold = 0
        route_total_qty_recommended = 0
        route_total_qty_actual = 0
        route_redistribution_count = 0
        route_redistribution_qty = 0
        customer_scores = []

        # Pre-group DataFrame by customer for efficient lookup (N+1 optimization)
        customer_groups = rec_df.groupby('CustomerCode')

        # Validation: Check if any visited customers don't exist in recommendations
        invalid_customers = []
        for customer_code in visited_customer_codes:
            if customer_code not in customer_groups.groups:
                invalid_customers.append(customer_code)

        if invalid_customers:
            logger.warning(f"Visited customers not found in recommendations: {invalid_customers}")
            # Continue saving for valid customers only
            visited_customer_codes = [c for c in visited_customer_codes if c not in invalid_customers]

        for customer_code in visited_customer_codes:
            customer_data = customer_groups.get_group(customer_code)

            if customer_data.empty:
                continue

            customer_actuals = actual_quantities.get(customer_code, {})
            customer_adjustments = adjustments.get(customer_code, {})

            cust_total_skus_recommended = len(customer_data)
            cust_total_skus_sold = 0
            cust_total_qty_recommended = 0
            cust_total_qty_actual = 0

            visit_timestamp = datetime.now()

            # Process each item
            for _, item_row in customer_data.iterrows():
                item_code = str(item_row['ItemCode'])

                original_recommended_qty = int(item_row['RecommendedQuantity'])
                original_actual_qty = int(item_row.get('ActualQuantity', 0))

                # Get adjustment (from redistribution)
                adjustment = customer_adjustments.get(item_code, 0)
                adjusted_recommended_qty = original_recommended_qty + adjustment

                # Get final actual quantity (manual edit or original)
                final_actual_qty = customer_actuals.get(item_code, original_actual_qty)
                actual_adjustment = final_actual_qty - original_actual_qty

                was_manually_edited = item_code in customer_actuals
                was_item_sold = final_actual_qty > 0

                if was_item_sold:
                    cust_total_skus_sold += 1

                cust_total_qty_recommended += adjusted_recommended_qty
                cust_total_qty_actual += final_actual_qty

                # Track redistribution
                if adjustment != 0:
                    route_redistribution_count += 1
                    route_redistribution_qty += abs(adjustment)

                # Build item detail record
                item_details.append({
                    'session_id': session_id,
                    'customer_code': customer_code,
                    'item_code': item_code,
                    'item_name': str(item_row['ItemName']),
                    'original_recommended_qty': original_recommended_qty,
                    'adjusted_recommended_qty': adjusted_recommended_qty,
                    'recommendation_adjustment': adjustment,
                    'original_actual_qty': original_actual_qty,
                    'final_actual_qty': final_actual_qty,
                    'actual_adjustment': actual_adjustment,
                    'was_manually_edited': was_manually_edited,
                    'was_item_sold': was_item_sold,
                    'recommendation_tier': str(item_row.get('Tier', 'Unknown')),
                    'priority_score': float(item_row.get('PriorityScore', 0)),
                    'van_inventory_qty': int(item_row.get('VanLoad', 0)),
                    'days_since_last_purchase': int(item_row.get('DaysSinceLastPurchase', 0)),
                    'purchase_cycle_days': float(item_row.get('PurchaseCycleDays', 0)),
                    'purchase_frequency_pct': float(item_row.get('FrequencyPercent', 0)),
                    'visit_timestamp': visit_timestamp
                })

            # Calculate customer score
            cust_sku_coverage_rate = (cust_total_skus_sold / cust_total_skus_recommended * 100) if cust_total_skus_recommended > 0 else 0
            cust_qty_fulfillment_rate = (cust_total_qty_actual / cust_total_qty_recommended * 100) if cust_total_qty_recommended > 0 else 0
            cust_performance_score = (cust_sku_coverage_rate * 0.4) + (cust_qty_fulfillment_rate * 0.6)

            customer_scores.append(cust_performance_score)
            route_total_skus_recommended += cust_total_skus_recommended
            route_total_skus_sold += cust_total_skus_sold
            route_total_qty_recommended += cust_total_qty_recommended
            route_total_qty_actual += cust_total_qty_actual

            # Build customer summary
            customer_summaries.append({
                'session_id': session_id,
                'customer_code': customer_code,
                'visit_sequence': visit_sequence_map.get(customer_code, 0),
                'visit_timestamp': visit_timestamp,
                'total_skus_recommended': cust_total_skus_recommended,
                'total_skus_sold': cust_total_skus_sold,
                'sku_coverage_rate': round(cust_sku_coverage_rate, 2),
                'total_qty_recommended': cust_total_qty_recommended,
                'total_qty_actual': cust_total_qty_actual,
                'qty_fulfillment_rate': round(cust_qty_fulfillment_rate, 2),
                'customer_performance_score': round(cust_performance_score, 2),
                'llm_performance_analysis': llm_analysis_map.get(customer_code, '')
            })

        # Calculate route-level metrics
        total_customers_visited = len(visited_customers)
        customer_completion_rate = (total_customers_visited / total_customers_planned * 100) if total_customers_planned > 0 else 0
        sku_coverage_rate = (route_total_skus_sold / route_total_skus_recommended * 100) if route_total_skus_recommended > 0 else 0
        qty_fulfillment_rate = (route_total_qty_actual / route_total_qty_recommended * 100) if route_total_qty_recommended > 0 else 0
        route_performance_score = sum(customer_scores) / len(customer_scores) if customer_scores else 0

        # Build route session data
        session_data = {
            'session_id': session_id,
            'route_code': str(route_code),
            'supervision_date': date_str,
            'total_customers_planned': total_customers_planned,
            'total_customers_visited': total_customers_visited,
            'customer_completion_rate': round(customer_completion_rate, 2),
            'total_skus_recommended': route_total_skus_recommended,
            'total_skus_sold': route_total_skus_sold,
            'sku_coverage_rate': round(sku_coverage_rate, 2),
            'total_qty_recommended': route_total_qty_recommended,
            'total_qty_actual': route_total_qty_actual,
            'qty_fulfillment_rate': round(qty_fulfillment_rate, 2),
            'redistribution_count': route_redistribution_count,
            'redistribution_qty': route_redistribution_qty,
            'route_performance_score': round(route_performance_score, 2),
            'llm_performance_analysis': route_llm_analysis,
            'session_status': 'active'
        }

        # Save to database
        storage = get_supervision_storage()
        result = storage.save_supervision_session(
            session_data=session_data,
            customer_summaries=customer_summaries,
            item_details=item_details
        )

        if result['success']:
            logger.info(
                f"Supervision state saved: {result['session_id']} - "
                f"{result['customers_saved']} customers, {result['items_saved']} items"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save supervision state: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save supervision state: {str(e)}")


@router.post("/load-supervision-state")
async def load_supervision_state(request: Request):
    """
    Load saved supervision session state from database
    Returns data formatted for frontend consumption (ready to display in read-only mode)

    Frontend sends: { route_code, date }
    Backend returns: {
        exists: bool,
        mode: 'historical' | 'not_found',
        visited_customers: [customer_code],
        actual_quantities: {customer_code: {item_code: qty}},
        adjustments: {customer_code: {item_code: adjustment}},
        route_analysis: {...},
        customer_analyses: {customer_code: {...}},
        session_summary: {...}
    }
    """
    try:
        from backend.core.supervision_storage import get_supervision_storage

        data = await request.json()
        route_code = data.get('route_code')
        date = data.get('date')

        if not route_code or not date:
            raise HTTPException(status_code=400, detail="Missing route_code or date")

        storage = get_supervision_storage()

        # Check if session exists
        session_id = storage.check_session_exists(route_code, date)

        if not session_id:
            return {
                'exists': False,
                'mode': 'live',
                'message': 'No saved session found. Live mode enabled.'
            }

        # Load the saved session
        result = storage.load_supervision_session(session_id)

        if not result.get('exists'):
            return {
                'exists': False,
                'mode': 'live',
                'message': 'Session data not found. Live mode enabled.'
            }

        # Transform data for frontend consumption
        route_summary = result['route_summary']
        customer_summaries = result['customer_summaries']
        item_details = result['item_details']

        # Build visited customers list (sorted by visit sequence)
        visited_customers = [
            c['customer_code'] for c in
            sorted(customer_summaries, key=lambda x: x['visit_sequence'])
        ]

        # Build actual quantities map: {customer_code: {item_code: final_actual_qty}}
        actual_quantities = {}
        for item in item_details:
            customer_code = item['customer_code']
            item_code = item['item_code']
            final_qty = item['final_actual_qty']

            if customer_code not in actual_quantities:
                actual_quantities[customer_code] = {}
            actual_quantities[customer_code][item_code] = final_qty

        # Build adjustments map: {customer_code: {item_code: recommendation_adjustment}}
        adjustments = {}
        for item in item_details:
            customer_code = item['customer_code']
            item_code = item['item_code']
            adjustment = item['recommendation_adjustment']

            if adjustment != 0:  # Only include non-zero adjustments
                if customer_code not in adjustments:
                    adjustments[customer_code] = {}
                adjustments[customer_code][item_code] = adjustment

        # Build customer analyses map: {customer_code: llm_analysis_text}
        customer_analyses = {
            c['customer_code']: c['llm_performance_analysis']
            for c in customer_summaries
            if c.get('llm_performance_analysis')
        }

        # Build visit sequence map: {customer_code: sequence_number}
        visit_sequences = {
            c['customer_code']: c['visit_sequence']
            for c in customer_summaries
        }

        logger.info(f"Loaded saved supervision session: {session_id} ({len(visited_customers)} customers)")

        return {
            'exists': True,
            'mode': 'historical',
            'session_id': session_id,
            'visited_customers': visited_customers,
            'actual_quantities': actual_quantities,
            'adjustments': adjustments,
            'visit_sequences': visit_sequences,
            'route_analysis': route_summary.get('llm_performance_analysis', ''),
            'customer_analyses': customer_analyses,
            'session_summary': {
                'route_code': route_summary['route_code'],
                'date': route_summary['supervision_date'],
                'total_customers_planned': route_summary['total_customers_planned'],
                'total_customers_visited': route_summary['total_customers_visited'],
                'customer_completion_rate': route_summary['customer_completion_rate'],
                'total_skus_recommended': route_summary['total_skus_recommended'],
                'total_skus_sold': route_summary['total_skus_sold'],
                'sku_coverage_rate': route_summary['sku_coverage_rate'],
                'total_qty_recommended': route_summary['total_qty_recommended'],
                'total_qty_actual': route_summary['total_qty_actual'],
                'qty_fulfillment_rate': route_summary['qty_fulfillment_rate'],
                'redistribution_count': route_summary['redistribution_count'],
                'redistribution_qty': route_summary['redistribution_qty'],
                'route_performance_score': route_summary['route_performance_score'],
                'session_status': route_summary['session_status']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load supervision state: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load supervision state: {str(e)}")


@router.get("/check-supervision-exists")
async def check_supervision_exists(route_code: str, date: str):
    """
    Check if supervision session exists for given route and date

    Returns:
    - session_id if exists
    - None if not found
    """
    try:
        from backend.core.supervision_storage import get_supervision_storage

        storage = get_supervision_storage()
        session_id = storage.check_session_exists(route_code, date)

        return {
            'exists': session_id is not None,
            'session_id': session_id
        }

    except Exception as e:
        logger.error(f"Failed to check supervision existence: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check supervision: {str(e)}")


@router.get("/llm-cache-stats")
async def get_llm_cache_stats():
    """
    Get LLM cache and rate limiter statistics

    Returns performance metrics including:
    - Cache hit/miss rates
    - Cost savings from caching
    - Rate limiter status
    - Total cached responses
    """
    try:
        from backend.core.llm_cache import get_llm_cache, get_rate_limiter

        cache = get_llm_cache()
        rate_limiter = get_rate_limiter()

        # Get statistics
        cache_stats = cache.get_stats()
        rate_limit_stats = rate_limiter.get_stats()

        # Calculate additional metrics
        total_requests = cache_stats['total_requests']
        if total_requests > 0:
            avg_cost_saved_per_request = cache_stats['total_cost_saved_usd'] / total_requests
        else:
            avg_cost_saved_per_request = 0

        return {
            'cache': {
                **cache_stats,
                'avg_cost_saved_per_request_usd': round(avg_cost_saved_per_request, 6)
            },
            'rate_limiter': rate_limit_stats,
            'status': 'healthy',
            'message': 'LLM cache and rate limiter operational'
        }

    except Exception as e:
        logger.error(f"Failed to get LLM cache stats: {e}")
        return {
            'cache': None,
            'rate_limiter': None,
            'status': 'error',
            'message': str(e)
        }