"""
Priority Calculation System
Calculates unified priority scores for inventory recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

try:
    from .cycle_calculator import IntelligentCycleCalculator
except ImportError:
    from cycle_calculator import IntelligentCycleCalculator


class PriorityCalculator:
    """
    Calculates priority scores (0-100) for customer-item combinations
    Uses weighted components to determine stocking priority
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Component weights for priority calculation
        self.weights = {
            'purchase_pattern': 0.45,
            'timing_need': 0.35,
            'customer_value': 0.20
        }

        # Initialize cycle calculator
        self.cycle_calculator = IntelligentCycleCalculator()

        # Cache for market benchmark calculations
        self._market_benchmark_cache = None
        self._market_benchmark_date = None

    def calculate_priority(self,
                          customer_code: str,
                          item_code: str,
                          customer_history: pd.DataFrame,
                          total_customers_history: pd.DataFrame,
                          target_date: pd.Timestamp = None) -> Tuple[float, Dict[str, float]]:
        """
        Calculate priority score for a customer-item combination

        Args:
            customer_code: Customer identifier
            item_code: Item identifier
            customer_history: Historical purchase data for this customer
            total_customers_history: Market data for benchmarking

        Returns:
            Tuple of (priority_score, component_breakdown)
        """
        try:
            # Get item-specific history for this customer
            item_history = customer_history[
                customer_history['ItemCode'] == item_code
            ].copy()

            # Calculate components
            purchase_pattern = self._calculate_purchase_pattern(
                customer_history, item_history
            )

            timing_need = self._calculate_timing_need(item_history, target_date)

            customer_value = self._calculate_customer_value(
                customer_history, item_history, total_customers_history, target_date
            )

            # Calculate weighted final priority
            priority = (
                self.weights['purchase_pattern'] * purchase_pattern +
                self.weights['timing_need'] * timing_need +
                self.weights['customer_value'] * customer_value
            )

            # Normalize to 0-100 scale and round to avoid floating-point variations
            priority = max(0, min(100, priority * 100))
            priority = round(priority, 2)  # Round to 2 decimal places for determinism

            components = {
                'purchase_pattern': purchase_pattern,
                'timing_need': timing_need,
                'customer_value': customer_value,
                'final_priority': priority
            }

            return priority, components

        except Exception as e:
            self.logger.error(f"Error calculating priority: {e}")
            return 0.0, {}

    def _calculate_purchase_pattern(self,
                                   customer_history: pd.DataFrame,
                                   item_history: pd.DataFrame) -> float:
        """
        Calculate how consistently customer buys this item
        Components: purchase rate (70%) + consistency (30%)
        """
        if customer_history.empty:
            return 0.0

        # Purchase rate: How often bought when visited
        visit_dates = customer_history['TrxDate'].unique()
        purchase_dates = item_history['TrxDate'].unique() if not item_history.empty else []

        if len(visit_dates) == 0:
            return 0.0

        purchase_rate = len(purchase_dates) / len(visit_dates)

        # Consistency: How regular are the purchase intervals
        consistency = 1.0  # Default to perfect if insufficient data

        if len(purchase_dates) >= 3:
            # Calculate intervals between purchases
            dates_sorted = pd.to_datetime(item_history['TrxDate']).sort_values()
            intervals = [(dates_sorted.iloc[i+1] - dates_sorted.iloc[i]).days
                        for i in range(len(dates_sorted)-1)]

            if intervals:
                mean_interval = np.mean(intervals)
                std_interval = np.std(intervals)
                # Coefficient of variation (lower = more consistent)
                if mean_interval > 0:
                    cv = std_interval / mean_interval
                    consistency = max(0, 1 - cv)  # Convert to 0-1 where 1 is most consistent

        # Weighted combination
        score = (0.7 * purchase_rate) + (0.3 * consistency)
        score = min(1.0, score)

        # Round to avoid floating-point variations
        return round(score, 4)

    def _calculate_timing_need(self, item_history: pd.DataFrame, target_date: pd.Timestamp = None) -> float:
        """
        Calculate replenishment timing score based on purchase patterns
        """
        return self.cycle_calculator.calculate_timing_need(item_history, None, target_date)

    def _calculate_customer_value(self,
                                 customer_history: pd.DataFrame,
                                 item_history: pd.DataFrame,
                                 total_customers_history: pd.DataFrame,
                                 target_date: pd.Timestamp = None) -> float:
        """
        Calculate customer value score based on size, importance, activity and growth
        """
        if customer_history.empty:
            return 0.0

        # Calculate value components
        weighted_size = self._calculate_dynamic_customer_size(
            customer_history, total_customers_history, target_date
        )

        recent_importance = self._calculate_recent_item_importance(
            item_history, customer_history, target_date
        )

        activity_score = self.cycle_calculator.calculate_activity_score(customer_history, target_date)

        growth_trend = self._calculate_customer_growth_value(customer_history)

        # Dynamic weighting based on data quality
        weights = self._calculate_dynamic_weights(customer_history, item_history)

        # Weighted combination
        score = (
            weights['size'] * weighted_size +
            weights['importance'] * recent_importance +
            weights['activity'] * activity_score +
            weights['growth'] * growth_trend
        )
        score = min(1.0, score)

        # Round to avoid floating-point variations
        return round(score, 4)

    def _calculate_dynamic_customer_size(self,
                                        customer_history: pd.DataFrame,
                                        total_customers_history: pd.DataFrame,
                                        target_date: pd.Timestamp = None) -> float:
        """
        Calculate customer size relative to market benchmark
        """
        # Get time-weighted customer value using target date for consistency
        weighted_customer_total, confidence = self.cycle_calculator.calculate_time_weighted_value(
            customer_history, 'TotalQuantity', 'adaptive', target_date
        )

        if weighted_customer_total <= 0:
            return 0.0

        # Get market benchmark for comparison
        weighted_avg_size = self._get_market_benchmark(total_customers_history, target_date)

        if weighted_avg_size is None:
            weighted_avg_size = weighted_customer_total  # Fallback

        # Calculate relative size ratio
        ratio = weighted_customer_total / max(weighted_avg_size, 1)

        # Apply activity-based cap
        activity = self.cycle_calculator.calculate_activity_score(customer_history, target_date)
        cap = 2.0 + activity

        return min(ratio, cap) / cap

    def _get_market_benchmark(self, total_customers_history: pd.DataFrame, target_date: pd.Timestamp = None) -> float:
        """
        Get market benchmark for customer size comparison
        """
        # Use target_date for deterministic caching
        if target_date is None:
            raise ValueError("target_date is required for deterministic market benchmark calculations")
        cache_date = target_date.date()
        if self._market_benchmark_cache is not None and self._market_benchmark_date == cache_date:
            return self._market_benchmark_cache

        # Calculate benchmark
        if not total_customers_history.empty:
            # Use top customers for benchmark
            top_customers = total_customers_history.groupby('CustomerCode')['TotalQuantity'].sum()
            top_customers = top_customers.nlargest(100)

            # Calculate average of top customers
            weighted_avg_size = top_customers.mean()

            # Cache the result
            self._market_benchmark_cache = weighted_avg_size
            self._market_benchmark_date = cache_date

            return weighted_avg_size

        return None

    def _calculate_recent_item_importance(self,
                                         item_history: pd.DataFrame,
                                         customer_history: pd.DataFrame,
                                         target_date: pd.Timestamp = None) -> float:
        """
        Calculate item importance based on recent purchase patterns
        """
        if item_history.empty or customer_history.empty:
            return 0.0

        # Use target_date for deterministic calculations
        if target_date is None:
            raise ValueError("target_date is required for deterministic importance calculations")
        reference_time = target_date

        # Calculate recency window
        purchase_gaps = self.cycle_calculator._extract_purchase_gaps(customer_history)
        if purchase_gaps:
            avg_gap = np.mean(purchase_gaps)
            recency_window = min(90, max(30, avg_gap * 10))
        else:
            recency_window = 60

        cutoff_date = reference_time - pd.Timedelta(days=recency_window)

        # Get recent data
        recent_customer = customer_history[customer_history['TrxDate'] > cutoff_date]
        recent_item = item_history[item_history['TrxDate'] > cutoff_date]

        # Calculate recent importance
        if not recent_customer.empty:
            recent_customer_total = recent_customer['TotalQuantity'].sum()
            recent_item_total = recent_item['TotalQuantity'].sum()
            recent_importance = recent_item_total / max(recent_customer_total, 1)
        else:
            # Fallback to historical with decay
            historical_importance = (
                item_history['TotalQuantity'].sum() /
                max(customer_history['TotalQuantity'].sum(), 1)
            )
            # Apply decay for historical data
            days_since_last = (reference_time - customer_history['TrxDate'].max()).days
            decay_factor = np.exp(-days_since_last / 90)
            recent_importance = historical_importance * decay_factor

        # Get importance trend
        trend = self.cycle_calculator.calculate_importance_trend(item_history, customer_history, reference_time)

        # Apply trend adjustment
        if trend > 0:
            importance_with_trend = recent_importance * (1 + trend * 0.3)
        elif trend < 0:
            importance_with_trend = recent_importance * (1 + trend * 0.2)
        else:
            importance_with_trend = recent_importance

        return min(1.0, importance_with_trend)

    def _calculate_customer_growth_value(self, customer_history: pd.DataFrame) -> float:
        """
        Calculate value based on customer growth patterns
        """
        # Get growth trend
        growth_trend = self.cycle_calculator.calculate_growth_trend(customer_history)

        # Convert trend to value score
        if growth_trend >= 0:
            return 0.5 + (growth_trend * 0.5)
        else:
            return 0.5 + (growth_trend * 0.5)

    def _calculate_dynamic_weights(self,
                                  customer_history: pd.DataFrame,
                                  item_history: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate component weights based on available data
        """
        # Base weights
        weights = {
            'size': 0.50,
            'importance': 0.25,
            'activity': 0.15,
            'growth': 0.10
        }

        # Adjust based on data availability
        customer_count = len(customer_history)
        item_count = len(item_history)

        if customer_count < 5:
            weights['growth'] = 0.05
            weights['activity'] = 0.20

        if item_count == 0:
            weights['importance'] = 0.0
            weights['size'] = 0.60
            weights['activity'] = 0.25
            weights['growth'] = 0.15

        elif item_count < 3:
            weights['importance'] = 0.15
            weights['size'] = 0.55

        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}

        return weights

    def get_tier(self, priority: float, strategy: str = 'balanced') -> str:
        """
        Map priority score to tier based on strategy

        Args:
            priority: Priority score (0-100)
            strategy: One of 'conservative', 'aggressive', 'balanced'

        Returns:
            Tier name
        """
        thresholds = {
            'conservative': {
                'MUST_STOCK': 85,
                'SHOULD_STOCK': 65,
                'CONSIDER': 45,
                'MONITOR': 25
            },
            'aggressive': {
                'MUST_STOCK': 65,
                'SHOULD_STOCK': 45,
                'CONSIDER': 25,
                'MONITOR': 10
            },
            'balanced': {
                'MUST_STOCK': 75,
                'SHOULD_STOCK': 55,
                'CONSIDER': 35,
                'MONITOR': 15
            }
        }

        strategy_thresholds = thresholds.get(strategy, thresholds['balanced'])

        if priority >= strategy_thresholds['MUST_STOCK']:
            return 'MUST_STOCK'
        elif priority >= strategy_thresholds['SHOULD_STOCK']:
            return 'SHOULD_STOCK'
        elif priority >= strategy_thresholds['CONSIDER']:
            return 'CONSIDER'
        elif priority >= strategy_thresholds['MONITOR']:
            return 'MONITOR'
        else:
            return 'EXCLUDE'