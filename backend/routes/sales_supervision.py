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

router = APIRouter()
logger = logging.getLogger(__name__)

# Import settings for dynamic paths
from backend.config import OUTPUT_DIR

# Output directories - using dynamic paths from settings
RECOMMENDATIONS_DIR = OUTPUT_DIR / 'recommendations'
SUPERVISION_DIR = OUTPUT_DIR / 'supervision'
SUPERVISION_DIR.mkdir(parents=True, exist_ok=True)

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
        
        # Check if recommended order exists for this date
        recommended_order_data = []
        customer_scores = {}
        
        # Convert date to format used in recommended order files (YYYYMMDD)
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
            file_date = parsed_date.strftime('%Y%m%d')
        except ValueError:
            # Try other date formats
            try:
                parsed_date = datetime.strptime(target_date, '%m/%d/%Y')
                file_date = parsed_date.strftime('%Y%m%d')
            except:
                file_date = target_date.replace('-', '')
        
        # Check for recommended order file
        recommended_file = RECOMMENDATIONS_DIR / f"recommended_order_{file_date}.csv"
        
        if recommended_file.exists():
            # Load recommended order data
            rec_df = pd.read_csv(recommended_file)
            
            # Filter by route
            rec_filtered = rec_df[rec_df['RouteCode'].astype(str) == str(route_code)]
            
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


@router.post("/generate-recommendations-for-date")
async def generate_recommendations_for_supervision(filters: SalesSupervisionFilters):
    """Generate recommendations for a specific date if not already generated"""
    try:
        target_date = filters.date
        # Convert 'All' to None for the recommendation system
        route_code = None if filters.route_code == 'All' else filters.route_code
        
        # Parse and validate date
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
            formatted_date = parsed_date.strftime('%Y-%m-%d')
            file_date = parsed_date.strftime('%Y%m%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")
        
        # Check if file already exists
        backend_output_file = RECOMMENDATIONS_DIR / f"recommended_order_{file_date}.csv"
        logger.info(f"Checking for existing file at: {backend_output_file}")
        
        if backend_output_file.exists():
            logger.info(f"File already exists for {formatted_date}")
            return {
                "message": f"Recommendations already exist for {formatted_date}",
                "generated": False,
                "date": formatted_date
            }
        
        # Check if data manager is loaded
        if not data_manager.is_loaded:
            raise HTTPException(status_code=503, detail="Data not loaded yet. Please wait for data initialization.")
        
        # Generate recommendations using TieredRecommendationSystem
        logger.info(f"Starting recommendation generation for date: {formatted_date}, route: {route_code}")
        system = TieredRecommendationSystem()
        logger.info(f"TieredRecommendationSystem created, data_manager.is_loaded: {system.data_manager.is_loaded}")
        
        results = system.process_recommendations(formatted_date, route_code)
        logger.info(f"Process recommendations returned {len(results) if not results.empty else 0} results")
        
        if results.empty:
            return {
                "message": f"No recommendations could be generated for {formatted_date}",
                "generated": False,
                "date": formatted_date
            }
        
        logger.info(f"Successfully generated {len(results)} recommendations for {formatted_date}")
        
        return {
            "message": f"Generated {len(results)} recommendations for {formatted_date}",
            "generated": True,
            "date": formatted_date,
            "recommendations_count": len(results)
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


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

        # Parse date for file lookup
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
            file_date = parsed_date.strftime('%Y%m%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")

        # Load recommendations from file
        recommended_file = RECOMMENDATIONS_DIR / f"recommended_order_{file_date}.csv"

        if not recommended_file.exists():
            # Generate recommendations if not exists
            logger.info(f"Recommendations not found, generating for {target_date}")
            system = TieredRecommendationSystem()
            results = system.process_recommendations(target_date, route_code)

            if results.empty:
                raise HTTPException(status_code=404, detail=f"No recommendations could be generated for {target_date}")

        # Load the recommendations
        rec_df = pd.read_csv(recommended_file)

        # Filter by route if specific route requested
        if route_code != 'All':
            rec_df = rec_df[rec_df['RouteCode'].astype(str) == str(route_code)]

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

        # Parse date for file lookup
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
            file_date = parsed_date.strftime('%Y%m%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")

        # Load recommendations from file
        recommended_file = RECOMMENDATIONS_DIR / f"recommended_order_{file_date}.csv"

        if not recommended_file.exists():
            raise HTTPException(status_code=404, detail="Recommended order data not found for this date")

        # Load the recommendations
        rec_df = pd.read_csv(recommended_file)

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

        # Parse date for file lookup
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
            file_date = parsed_date.strftime('%Y%m%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")

        recommended_file = RECOMMENDATIONS_DIR / f"recommended_order_{file_date}.csv"
        if not recommended_file.exists():
            raise HTTPException(status_code=404, detail="Recommended order data not found for this date")

        # Load and filter recommendations
        rec_df = pd.read_csv(recommended_file)
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
            file_date = parsed_date.strftime('%Y%m%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

        recommended_file = RECOMMENDATIONS_DIR / f"recommended_order_{file_date}.csv"
        if recommended_file.exists():
            route_data = pd.read_csv(recommended_file)
            # Filter by route if specified
            if route_code != 'All':
                route_data = route_data[route_data['RouteCode'].astype(str) == str(route_code)]
        else:
            route_data = pd.DataFrame()

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