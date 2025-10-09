"""
Dynamic Supervision Session Manager
Handles real-time visit tracking and redistribution of unsold items
"""
import pandas as pd
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ItemRecommendation:
    """Represents a single item recommendation"""
    def __init__(self, item_code: str, item_name: str, recommended_quantity: int,
                 tier: str = 'CONSIDER', probability: float = 0.5, urgency_score: float = 0.5):
        self.item_code = item_code
        self.item_name = item_name
        self.recommended_quantity = recommended_quantity
        self.adjustment = 0  # For tracking redistributed quantities
        self.tier = tier
        self.probability = probability
        self.urgency_score = urgency_score

class CustomerRecommendations:
    """Represents recommendations for a single customer"""
    def __init__(self, customer_code: str):
        self.customer_code = customer_code
        self.items = {}  # {item_code: ItemRecommendation}
        self.visited = False
        self.actual_sales = {}  # {item_code: actual_quantity}

    def add_item(self, item_rec: ItemRecommendation):
        self.items[item_rec.item_code] = item_rec

    def get_total_recommended(self):
        return sum(item.recommended_quantity for item in self.items.values())

    def get_total_actual(self):
        return sum(self.actual_sales.values())

class DynamicSupervisionSession:
    """Manages dynamic supervision session with redistribution logic"""

    def __init__(self, route_code: str, date: str):
        self.route_code = route_code
        self.date = date
        self.session_id = f"{route_code}_{date}_{datetime.now().timestamp()}"

        # Session state
        self.customer_recommendations = {}  # {customer_code: CustomerRecommendations}
        self.van_inventory = {}  # {item_code: available_quantity}
        self.visited_customers = set()
        self.redistribution_log = []

        # Track adjustments for each customer-item combination
        self.adjustments = {}  # {customer_code: {item_code: adjustment_quantity}}

        logger.info(f"Created dynamic supervision session: {self.session_id}")

    def initialize_from_recommendations(self, recommendations_df: pd.DataFrame):
        """Initialize session from recommended order dataframe"""
        try:
            # Build customer recommendations
            for _, row in recommendations_df.iterrows():
                customer_code = str(row['CustomerCode'])

                if customer_code not in self.customer_recommendations:
                    self.customer_recommendations[customer_code] = CustomerRecommendations(customer_code)

                item_rec = ItemRecommendation(
                    item_code=str(row['ItemCode']),
                    item_name=str(row['ItemName']),
                    recommended_quantity=int(row['RecommendedQuantity']),
                    tier=str(row.get('Tier', 'CONSIDER')),
                    probability=float(row.get('ProbabilityPercent', 50)) / 100,
                    urgency_score=float(row.get('UrgencyScore', 0.5))
                )

                self.customer_recommendations[customer_code].add_item(item_rec)

                # Initialize van inventory
                item_code = str(row['ItemCode'])
                if item_code not in self.van_inventory:
                    self.van_inventory[item_code] = 0
                self.van_inventory[item_code] += int(row['RecommendedQuantity'])

            # Initialize adjustments tracking
            for customer_code in self.customer_recommendations:
                self.adjustments[customer_code] = {}

            logger.info(f"Initialized session with {len(self.customer_recommendations)} customers, "
                       f"{len(self.van_inventory)} items")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            return False

    def process_visit(self, customer_code: str, actual_sales: Dict[str, int]) -> Dict[str, Any]:
        """
        Process a customer visit and redistribute unsold items
        Returns redistribution recommendations
        """
        if customer_code not in self.customer_recommendations:
            return {"error": f"Customer {customer_code} not found in recommendations"}

        if customer_code in self.visited_customers:
            return {"error": f"Customer {customer_code} already visited"}

        # Mark as visited
        self.visited_customers.add(customer_code)
        customer_rec = self.customer_recommendations[customer_code]
        customer_rec.visited = True
        customer_rec.actual_sales = actual_sales

        # Calculate unsold items
        unsold_items = {}
        for item_code, item_rec in customer_rec.items.items():
            actual_qty = actual_sales.get(item_code, 0)
            recommended_qty = item_rec.recommended_quantity + self.adjustments[customer_code].get(item_code, 0)

            if actual_qty < recommended_qty:
                unsold_qty = recommended_qty - actual_qty
                unsold_items[item_code] = {
                    'quantity': unsold_qty,
                    'item_name': item_rec.item_name
                }

        # Redistribute unsold items
        redistribution_result = self._redistribute_items(unsold_items)

        # Log the visit
        self.redistribution_log.append({
            'customer_code': customer_code,
            'timestamp': datetime.now().isoformat(),
            'unsold_items': unsold_items,
            'redistribution': redistribution_result
        })

        return {
            'success': True,
            'customer_code': customer_code,
            'unsold_items': unsold_items,
            'redistribution': redistribution_result,
            'adjustments': self.adjustments  # Return all adjustments for frontend
        }

    def _redistribute_items(self, unsold_items: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Redistribute unsold items to remaining customers based on priority
        """
        if not unsold_items:
            return {
                'redistributed_count': 0,
                'details': [],
                'status': 'nothing_to_redistribute'
            }

        redistribution_details = []

        # Get unvisited customers
        unvisited_customers = [
            code for code in self.customer_recommendations
            if code not in self.visited_customers
        ]

        if not unvisited_customers:
            return {
                'redistributed_count': 0,
                'details': [],
                'status': 'no_remaining_customers',
                'message': 'No remaining customers to redistribute items to'
            }

        # Process each unsold item
        for item_code, item_info in unsold_items.items():
            remaining_qty = item_info['quantity']

            # Find eligible customers (those who have this item in recommendations)
            eligible_customers = []
            for customer_code in unvisited_customers:
                customer_rec = self.customer_recommendations[customer_code]
                if item_code in customer_rec.items:
                    item_rec = customer_rec.items[item_code]
                    eligible_customers.append({
                        'customer_code': customer_code,
                        'tier': item_rec.tier,
                        'probability': item_rec.probability,
                        'urgency_score': item_rec.urgency_score,
                        'current_recommended': item_rec.recommended_quantity,
                        'current_adjustment': self.adjustments[customer_code].get(item_code, 0)
                    })

            if not eligible_customers:
                continue

            # Sort by priority (tier, probability, urgency)
            tier_priority = {'MUST_STOCK': 4, 'SHOULD_STOCK': 3, 'CONSIDER': 2, 'MONITOR': 1}
            eligible_customers.sort(
                key=lambda x: (
                    tier_priority.get(x['tier'], 0),
                    x['probability'],
                    x['urgency_score']
                ),
                reverse=True
            )

            # Distribute to top eligible customers
            for customer in eligible_customers[:5]:  # Limit to top 5 customers
                if remaining_qty <= 0:
                    break

                # Calculate how much to redistribute
                # Don't overwhelm any single customer - max 50% increase
                max_increase = max(1, int(customer['current_recommended'] * 0.5))
                redistribute_qty = min(remaining_qty, max_increase)

                # Update adjustment
                customer_code = customer['customer_code']
                if item_code not in self.adjustments[customer_code]:
                    self.adjustments[customer_code][item_code] = 0
                self.adjustments[customer_code][item_code] += redistribute_qty

                redistribution_details.append({
                    'item_code': item_code,
                    'item_name': item_info['item_name'],
                    'customer_code': customer_code,
                    'quantity': redistribute_qty,
                    'tier': customer['tier'],
                    'probability': customer['probability']
                })

                remaining_qty -= redistribute_qty

        # Check if any items couldn't be redistributed
        items_not_redistributed = []
        for item_code, item_info in unsold_items.items():
            if not any(d['item_code'] == item_code for d in redistribution_details):
                items_not_redistributed.append(item_code)

        return {
            'redistributed_count': len(redistribution_details),
            'details': redistribution_details,
            'status': 'success' if not items_not_redistributed else 'partial',
            'items_not_redistributed': items_not_redistributed,
            'message': f'Redistributed {len(redistribution_details)} items successfully' +
                      (f', {len(items_not_redistributed)} items could not be redistributed' if items_not_redistributed else '')
        }

    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session summary"""
        total_customers = len(self.customer_recommendations)
        visited_count = len(self.visited_customers)

        # Calculate route-wide original recommended (from CSV file, never changes)
        route_total_recommended = 0
        for customer_code, customer_rec in self.customer_recommendations.items():
            for item_code, item_rec in customer_rec.items.items():
                route_total_recommended += item_rec.recommended_quantity

        # Calculate visited customers metrics (includes redistributions)
        visited_recommended = 0
        visited_actual = 0

        for customer_code in self.visited_customers:
            customer_rec = self.customer_recommendations[customer_code]
            for item_code, item_rec in customer_rec.items.items():
                recommended_with_adjustment = item_rec.recommended_quantity + self.adjustments[customer_code].get(item_code, 0)
                actual = customer_rec.actual_sales.get(item_code, 0)
                visited_recommended += recommended_with_adjustment
                visited_actual += actual

        performance_rate = (visited_actual / visited_recommended * 100) if visited_recommended > 0 else 0

        return {
            'session_id': self.session_id,
            'route_code': self.route_code,
            'date': self.date,
            'total_customers': total_customers,
            'visited_customers': visited_count,
            'remaining_customers': total_customers - visited_count,
            'performance_rate': round(performance_rate, 1),
            'total_recommended': route_total_recommended,
            'total_actual': visited_actual,
            'visited_recommended': visited_recommended,
            'redistribution_count': len(self.redistribution_log)
        }


# Global session storage (in production, use Redis or database)
active_sessions = {}

def get_or_create_session(route_code: str, date: str) -> DynamicSupervisionSession:
    """Get existing session or create new one"""
    session_key = f"{route_code}_{date}"

    if session_key not in active_sessions:
        active_sessions[session_key] = DynamicSupervisionSession(route_code, date)

    return active_sessions[session_key]

def clear_session(route_code: str, date: str):
    """Clear a session"""
    session_key = f"{route_code}_{date}"
    if session_key in active_sessions:
        del active_sessions[session_key]