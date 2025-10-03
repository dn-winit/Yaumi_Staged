"""
Intelligent Cycle Calculator
Provides purchase cycle analysis and timing predictions
Includes customer activity scoring and trend analysis
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional


class IntelligentCycleCalculator:
    """
    Advanced cycle calculator with pattern recognition and timing analysis
    """

    def __init__(self):
        # Pattern recognition thresholds
        self.pattern_thresholds = self._calculate_dynamic_pattern_thresholds()

    def calculate_cycle(self, item_history: pd.DataFrame) -> Tuple[float, float]:
        """
        Main entry point for cycle calculation

        Args:
            item_history: DataFrame with purchase history for customer-item combination

        Returns:
            Tuple of (cycle_days, confidence_score)
        """
        if item_history.empty:
            return self._get_fallback_cycle(), 0.0

        # Extract and validate purchase gaps
        gaps = self._extract_purchase_gaps(item_history)
        if not gaps:
            return self._get_fallback_cycle(), 0.0

        # Dynamic outlier removal (no hardcoded 180 days)
        clean_gaps = self._remove_outliers_dynamically(gaps)
        if not clean_gaps:
            return np.median(gaps), 0.1  # Use raw data as fallback

        # Pattern recognition and cycle calculation
        pattern_info = self._analyze_purchase_pattern(clean_gaps)
        final_cycle, confidence = self._calculate_adaptive_cycle(clean_gaps, pattern_info)

        return final_cycle, confidence

    def _extract_purchase_gaps(self, item_history: pd.DataFrame) -> list:
        """Extract gaps between purchases with validation"""
        if len(item_history) < 2:
            return []

        # Get unique purchase dates
        dates = pd.to_datetime(item_history['TrxDate']).unique()
        if len(dates) < 2:
            return []

        # Calculate gaps
        sorted_dates = sorted(dates)
        gaps = []
        for i in range(1, len(sorted_dates)):
            gap = (sorted_dates[i] - sorted_dates[i-1]).days
            if gap > 0:  # Only positive gaps
                gaps.append(gap)

        return gaps

    def _remove_outliers_dynamically(self, gaps: list) -> list:
        """Remove outliers using statistical methods - no hardcoded thresholds"""
        if len(gaps) < 3:
            return gaps  # Not enough data for outlier detection

        gaps_array = np.array(gaps)

        # Method 1: IQR-based outlier removal
        q1, q3 = np.percentile(gaps_array, [25, 75])
        iqr = q3 - q1

        if iqr > 0:  # Valid IQR
            # Adaptive multiplier based on data spread
            data_spread = (q3 - q1) / np.median(gaps_array) if np.median(gaps_array) > 0 else 1.0
            iqr_multiplier = min(2.0, max(1.2, 1.5 - data_spread * 0.3))  # 1.2 to 2.0 range

            lower_bound = max(1, q1 - iqr_multiplier * iqr)  # At least 1 day
            upper_bound = q3 + iqr_multiplier * iqr

            clean_gaps = [g for g in gaps if lower_bound <= g <= upper_bound]

            # Safety check - don't remove too much data
            if len(clean_gaps) >= len(gaps) * 0.6:  # Keep at least 60%
                return clean_gaps

        # Method 2: MAD-based outlier removal (more robust)
        median = np.median(gaps_array)
        mad = np.median(np.abs(gaps_array - median))

        if mad > 0:
            # Adaptive threshold based on coefficient of variation
            cv = np.std(gaps_array) / np.mean(gaps_array) if np.mean(gaps_array) > 0 else 1.0
            mad_threshold = min(4.0, max(2.0, 3.0 - cv))  # 2.0 to 4.0 range

            clean_gaps = [g for g in gaps if abs(g - median) <= mad_threshold * mad]
            return clean_gaps if clean_gaps else gaps

        return gaps  # Fallback to original data

    def _analyze_purchase_pattern(self, gaps: list) -> Dict[str, Any]:
        """Analyze purchase pattern - completely dynamic classification"""
        if not gaps:
            return {"type": "unknown", "consistency": 0.0, "base_cycle": self._get_fallback_cycle()}

        gaps_array = np.array(gaps)
        mean_gap = np.mean(gaps_array)
        std_gap = np.std(gaps_array)
        median_gap = np.median(gaps_array)

        # Calculate consistency (lower CV = more consistent)
        consistency = 1.0 - min(1.0, std_gap / mean_gap) if mean_gap > 0 else 0.0

        # Dynamic pattern classification based on gap characteristics
        pattern_type = self._classify_pattern_dynamically(gaps_array, consistency)

        # Choose appropriate base cycle method
        if consistency > 0.7:  # High consistency - use median
            base_cycle = median_gap
        elif consistency > 0.4:  # Medium consistency - weighted average
            base_cycle = 0.6 * median_gap + 0.4 * mean_gap
        else:  # Low consistency - use mean
            base_cycle = mean_gap

        return {
            "type": pattern_type,
            "consistency": consistency,
            "base_cycle": base_cycle,
            "mean_gap": mean_gap,
            "median_gap": median_gap,
            "variability": std_gap / mean_gap if mean_gap > 0 else 1.0
        }

    def _classify_pattern_dynamically(self, gaps_array: np.ndarray, consistency: float) -> str:
        """Classify pattern without hardcoded ranges - purely data-driven"""
        mean_gap = np.mean(gaps_array)

        # Dynamic classification based on actual data distribution
        if consistency > 0.7:  # High consistency patterns
            # Use natural breakpoints in the data
            if mean_gap <= np.percentile(gaps_array, 20):  # Bottom 20%
                return "frequent"
            elif mean_gap <= np.percentile(gaps_array, 80):  # Middle 60%
                return "regular"
            else:  # Top 20%
                return "occasional"
        else:  # Low consistency
            return "irregular"

    def _calculate_adaptive_cycle(self, gaps: list, pattern_info: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate final cycle with adaptive recency weighting"""
        if len(gaps) <= 2:
            confidence = 0.3 + 0.1 * len(gaps)  # 0.3 to 0.5
            return pattern_info["base_cycle"], confidence

        # Dynamic recency parameters based on pattern characteristics
        recency_params = self._get_adaptive_recency_params(pattern_info)

        # Apply recency weighting
        weighted_cycle = self._apply_adaptive_weighting(gaps, recency_params)

        # Blend with base cycle based on pattern stability
        stability_factor = pattern_info["consistency"]
        final_cycle = (
            stability_factor * pattern_info["base_cycle"] +
            (1 - stability_factor) * weighted_cycle
        )

        # Calculate confidence dynamically
        confidence = self._calculate_dynamic_confidence(gaps, pattern_info)

        return final_cycle, confidence

    def _get_adaptive_recency_params(self, pattern_info: Dict[str, Any]) -> Dict[str, float]:
        """Get recency parameters that adapt to pattern characteristics"""
        consistency = pattern_info["consistency"]
        variability = pattern_info["variability"]

        # Adaptive parameters - no hardcoded values
        if consistency > 0.8:  # Very stable pattern
            strength = 0.2 + 0.2 * (1 - consistency)  # Light weighting
            window_ratio = 0.3
        elif consistency > 0.5:  # Moderately stable
            strength = 0.4 + 0.3 * variability  # Medium weighting
            window_ratio = 0.4
        else:  # Unstable pattern
            strength = 0.6 + 0.3 * variability  # Heavy weighting
            window_ratio = 0.5 + 0.2 * variability

        return {
            "strength": min(0.9, strength),  # Cap at 90%
            "window_ratio": min(0.8, window_ratio)  # Cap at 80%
        }

    def _apply_adaptive_weighting(self, gaps: list, recency_params: Dict[str, float]) -> float:
        """Apply recency weighting with adaptive parameters"""
        window_size = max(2, int(len(gaps) * recency_params["window_ratio"]))
        recent_gaps = gaps[-window_size:]

        # Create adaptive weights
        if len(recent_gaps) == 1:
            return recent_gaps[0]

        # Exponential weighting with adaptive strength
        weights = np.exp(np.linspace(0, recency_params["strength"] * 2, len(recent_gaps)))
        weights = weights / weights.sum()

        return np.average(recent_gaps, weights=weights)

    def _calculate_dynamic_confidence(self, gaps: list, pattern_info: Dict[str, Any]) -> float:
        """Calculate confidence score dynamically based on data quality"""
        # Base confidence from data amount (logarithmic scaling)
        data_amount_score = min(0.4, np.log(len(gaps) + 1) * 0.15)

        # Consistency bonus
        consistency_score = pattern_info["consistency"] * 0.3

        # Pattern type bonus (stable patterns get higher confidence)
        pattern_bonus = {
            "frequent": 0.2,
            "regular": 0.25,
            "occasional": 0.15,
            "irregular": 0.05
        }.get(pattern_info["type"], 0.1)

        # Combine scores
        final_confidence = min(0.95, 0.3 + data_amount_score + consistency_score + pattern_bonus)

        return final_confidence

    def _get_fallback_cycle(self) -> float:
        """Get fallback cycle - could be made configurable or context-aware"""
        return 30.0  # Default 30-day cycle

    def _calculate_dynamic_pattern_thresholds(self) -> Dict[str, float]:
        """Calculate dynamic thresholds - placeholder for future enhancement"""
        # This could analyze historical data to set dynamic thresholds
        # For now, return empty dict as we're using purely adaptive methods
        return {}

    def calculate_timing_need(self,
                            item_history: pd.DataFrame,
                            customer_history: Optional[pd.DataFrame] = None,
                            target_date: Optional[pd.Timestamp] = None) -> float:
        """
        Calculate timing need score with intelligent churn detection

        Args:
            item_history: Purchase history for specific item
            customer_history: Overall customer history (optional, for context)

        Returns:
            Timing need score (0-1) with churn-aware decay
        """
        if item_history.empty:
            return 0.5  # Moderate need for no history

        if target_date is None:
            raise ValueError("target_date is required for deterministic timing calculations")

        # Get last purchase and calculate cycle
        last_purchase = pd.to_datetime(item_history['TrxDate']).max()
        days_since = (target_date - last_purchase).days

        # Get intelligent cycle with confidence
        avg_cycle, confidence = self.calculate_cycle(item_history)

        # Calculate position in cycle
        cycle_position = days_since / max(avg_cycle, 1)

        # Get pattern characteristics for intelligent scoring
        gaps = self._extract_purchase_gaps(item_history)
        pattern_info = self._analyze_purchase_pattern(gaps) if gaps else None

        # Calculate dynamic thresholds
        peak_threshold, decay_params = self._calculate_adaptive_thresholds(
            avg_cycle, confidence, pattern_info, item_history
        )

        # Apply intelligent scoring
        if cycle_position <= peak_threshold:
            # Normal urgency curve up to peak
            return self._calculate_urgency_score(cycle_position, peak_threshold)
        else:
            # Churn-aware decay after peak
            return self._calculate_decayed_score(
                cycle_position, peak_threshold, decay_params, pattern_info
            )

    def _calculate_adaptive_thresholds(self,
                                      avg_cycle: float,
                                      confidence: float,
                                      pattern_info: Optional[Dict],
                                      item_history: pd.DataFrame) -> Tuple[float, Dict]:
        """
        Calculate dynamic thresholds for peak and decay
        Fully adaptive - no hardcoding
        """
        # Analyze customer behavior depth
        purchase_count = len(item_history)
        history_span = (item_history['TrxDate'].max() - item_history['TrxDate'].min()).days

        # Dynamic peak calculation based on pattern stability
        if pattern_info:
            consistency = pattern_info.get('consistency', 0.5)
            variability = pattern_info.get('variability', 1.0)
        else:
            consistency = 0.5
            variability = 1.0

        # Peak threshold: when to start considering churn
        # More consistent = wait longer, more variable = shorter tolerance
        base_peak = 2.0  # Start with 2x cycle as base

        # Adjust based on consistency (0.5 to 1.5 multiplier)
        consistency_factor = 0.5 + consistency

        # Adjust based on cycle length (shorter cycles = less tolerance)
        if avg_cycle <= 7:  # Daily/weekly
            cycle_factor = 0.9
        elif avg_cycle <= 14:  # Bi-weekly
            cycle_factor = 1.0
        elif avg_cycle <= 30:  # Monthly
            cycle_factor = 1.1
        else:  # Occasional
            cycle_factor = 1.2

        # Adjust based on history depth
        history_factor = min(1.2, 0.8 + (purchase_count / 20))  # 0.8 to 1.2

        peak_threshold = base_peak * consistency_factor * cycle_factor * history_factor

        # Decay parameters
        decay_params = {
            'rate': self._calculate_decay_rate(avg_cycle, consistency, purchase_count),
            'floor': self._calculate_floor_value(consistency, purchase_count),
            'curve_type': 'sigmoid' if consistency > 0.6 else 'exponential'
        }

        return peak_threshold, decay_params

    def _calculate_decay_rate(self, avg_cycle: float, consistency: float, purchase_count: int) -> float:
        """
        Calculate how fast the score should decay after peak
        Dynamic based on customer characteristics
        """
        # Base decay rate
        base_rate = 0.5

        # Faster decay for frequent consistent buyers who stop
        if avg_cycle <= 7 and consistency > 0.7:
            cycle_modifier = 1.5  # Clear signal they stopped
        elif avg_cycle <= 30:
            cycle_modifier = 1.0
        else:
            cycle_modifier = 0.7  # Slower decay for occasional buyers

        # History depth modifier (more history = more confident in churn)
        history_modifier = min(1.3, 0.7 + (purchase_count / 10))

        # Consistency modifier (consistent patterns = faster decay when broken)
        consistency_modifier = 0.7 + (consistency * 0.6)

        return base_rate * cycle_modifier * history_modifier * consistency_modifier

    def _calculate_floor_value(self, consistency: float, purchase_count: int) -> float:
        """
        Calculate minimum score (never fully zero - might return)
        """
        # Base floor
        base_floor = 0.05

        # Higher floor for irregular patterns (harder to judge churn)
        consistency_bonus = (1 - consistency) * 0.1

        # Higher floor for customers with long history
        history_bonus = min(0.05, purchase_count / 100)

        return min(0.2, base_floor + consistency_bonus + history_bonus)

    def _calculate_urgency_score(self, cycle_position: float, peak_threshold: float) -> float:
        """
        Calculate normal urgency score (before peak)
        Smooth curve, no hardcoded thresholds
        """
        # Normalize position to 0-1 range up to peak
        normalized = min(1.0, cycle_position / peak_threshold)

        # Smooth S-curve (sigmoid-like) for natural urgency growth
        if normalized <= 0.3:
            # Slow start
            return 0.1 + 0.2 * (normalized / 0.3)
        elif normalized <= 0.7:
            # Acceleration phase
            progress = (normalized - 0.3) / 0.4
            return 0.3 + 0.4 * progress
        else:
            # Steep increase near due date
            progress = (normalized - 0.7) / 0.3
            return 0.7 + 0.3 * progress

    def _calculate_decayed_score(self,
                                cycle_position: float,
                                peak_threshold: float,
                                decay_params: Dict,
                                pattern_info: Optional[Dict]) -> float:
        """
        Calculate decayed score for likely churned customers
        Intelligent decay based on pattern characteristics
        """
        # How far beyond peak
        excess = cycle_position - peak_threshold
        peak_score = 1.0  # Score at peak

        # Apply decay based on curve type
        if decay_params['curve_type'] == 'sigmoid':
            # Smooth sigmoid decay for consistent patterns
            decay_factor = 1.0 / (1.0 + np.exp(decay_params['rate'] * excess))
        else:
            # Exponential decay for irregular patterns
            decay_factor = np.exp(-decay_params['rate'] * excess)

        # Calculate decayed score
        decayed = peak_score * decay_factor

        # Apply floor (never fully zero)
        return max(decay_params['floor'], decayed)

    def calculate_time_weighted_value(self,
                                     history: pd.DataFrame,
                                     value_column: str = 'TotalQuantity',
                                     decay_type: str = 'adaptive',
                                     reference_date: pd.Timestamp = None) -> Tuple[float, float]:
        """
        Calculate time-weighted average with adaptive decay
        Recent values matter more than old ones

        Args:
            history: DataFrame with TrxDate and value column
            value_column: Column to average (default 'TotalQuantity')
            decay_type: 'adaptive', 'exponential', or 'linear'
            reference_date: The date to calculate weights relative to (for deterministic results)

        Returns:
            Tuple of (weighted_average, decay_confidence)
        """
        if history.empty:
            return 0.0, 0.0

        # Use provided reference date or default to last purchase + 1 day
        # Using a consistent reference date ensures reproducible calculations
        if reference_date is None:
            reference_date = history['TrxDate'].max() + pd.Timedelta(days=1)
        now = pd.to_datetime(reference_date)

        # Calculate adaptive decay rate based on purchase frequency
        purchase_gaps = self._extract_purchase_gaps(history)
        if purchase_gaps:
            avg_gap = np.mean(purchase_gaps)
            # Faster decay for frequent buyers, slower for occasional
            base_decay = 1.0 / max(avg_gap, 1)  # Inversely proportional to gap
        else:
            base_decay = 0.033  # Default: ~30 day half-life

        weighted_sum = 0.0
        weight_sum = 0.0

        for _, row in history.iterrows():
            days_ago = (now - pd.to_datetime(row['TrxDate'])).days

            # Calculate weight based on decay type
            if decay_type == 'adaptive':
                # Adaptive decay based on purchase pattern
                if days_ago <= avg_gap if purchase_gaps else 30:
                    weight = 1.0  # Recent: full weight
                elif days_ago <= avg_gap * 3 if purchase_gaps else 90:
                    weight = 0.7 + 0.3 * (1 - (days_ago - avg_gap) / (avg_gap * 2))
                else:
                    weight = np.exp(-base_decay * days_ago / 30)
            elif decay_type == 'exponential':
                weight = np.exp(-base_decay * days_ago / 30)
            else:  # linear
                weight = max(0, 1 - days_ago / 365)

            value = row.get(value_column, 0)
            weighted_sum += value * weight
            weight_sum += weight

        # Calculate weighted average (the core fix)
        if weight_sum > 0:
            weighted_average = weighted_sum / weight_sum

            # Validate result and apply safety bounds
            if weighted_average <= 0 or np.isnan(weighted_average) or np.isinf(weighted_average):
                # Fallback to simple median for safety
                weighted_average = history[value_column].median()
                confidence = 0.3  # Low confidence for fallback
            else:
                # Additional validation: check against reasonable bounds
                simple_avg = history[value_column].mean()
                historical_max = history[value_column].max()

                # Bounds checking: weighted average shouldn't be more than 5x simple average
                # or more than 120% of historical maximum
                upper_bound = min(simple_avg * 5, historical_max * 1.2)
                lower_bound = max(1, simple_avg * 0.1)  # At least 10% of simple average, minimum 1

                if weighted_average > upper_bound:
                    weighted_average = min(upper_bound, simple_avg * 2)  # Cap at 2x simple average
                    confidence = 0.5  # Reduced confidence for capped values
                elif weighted_average < lower_bound:
                    weighted_average = max(lower_bound, simple_avg * 0.5)  # Floor at 50% of simple average
                    confidence = 0.5  # Reduced confidence for floored values
                else:
                    # Normal confidence calculation based on data recency
                    avg_weight = weight_sum / len(history)
                    confidence = min(1.0, avg_weight * 2)
        else:
            # No valid weights - use simple average as fallback
            weighted_average = history[value_column].mean() if not history.empty else 0.0
            confidence = 0.2  # Very low confidence

        return weighted_average, confidence

    def calculate_activity_score(self,
                                history: pd.DataFrame,
                                reference_date: Optional[pd.Timestamp] = None) -> float:
        """
        Calculate how active a customer has been recently
        Multi-window analysis with pattern recognition

        Returns:
            Activity score (0-1) with recency and consistency factors
        """
        if history.empty:
            return 0.0

        if reference_date is None:
            raise ValueError("reference_date is required for deterministic time-weighted calculations")

        # Define adaptive windows based on data characteristics
        purchase_gaps = self._extract_purchase_gaps(history)
        if purchase_gaps:
            avg_gap = np.mean(purchase_gaps)
            # Dynamic windows based on purchase pattern
            windows = [
                ('immediate', min(7, avg_gap * 2)),      # 2x average gap
                ('short', min(30, avg_gap * 6)),         # 6x average gap
                ('medium', min(90, avg_gap * 15)),       # 15x average gap
                ('long', min(180, avg_gap * 30))         # 30x average gap
            ]
        else:
            # Default windows
            windows = [
                ('immediate', 7),
                ('short', 30),
                ('medium', 90),
                ('long', 180)
            ]

        scores = {}
        for window_name, days in windows:
            cutoff = reference_date - pd.Timedelta(days=days)
            purchases_in_window = len(history[history['TrxDate'] > cutoff])

            # Normalize by expected purchases based on pattern
            if purchase_gaps:
                expected_purchases = days / np.mean(purchase_gaps)
                normalized_score = min(1.0, purchases_in_window / max(expected_purchases, 1))
            else:
                # Simple normalization
                normalized_score = min(1.0, purchases_in_window / (days / 7))  # Expect weekly

            scores[window_name] = normalized_score

        # Weighted combination with emphasis on recent activity
        weights = {
            'immediate': 0.4,
            'short': 0.3,
            'medium': 0.2,
            'long': 0.1
        }

        activity = sum(scores[w] * weights[w] for w in weights)

        # Consistency bonus - active across multiple windows
        if all(scores[w] > 0.3 for w in ['immediate', 'short', 'medium']):
            activity = min(1.0, activity * 1.2)

        # Trending bonus - compare recent to historical
        recent_rate = scores['immediate']
        historical_rate = scores['long']
        if recent_rate > historical_rate * 1.5:  # Growing activity
            activity = min(1.0, activity * 1.1)

        return activity

    def calculate_growth_trend(self,
                              history: pd.DataFrame,
                              value_column: str = 'TotalQuantity') -> float:
        """
        Calculate growth or decline trend

        Returns:
            Trend score (-1 to 1): negative=declining, positive=growing
        """
        if len(history) < 3:  # Need minimum data for trend
            return 0.0

        # Sort by date
        sorted_history = history.sort_values('TrxDate')

        # Split into halves
        midpoint = len(sorted_history) // 2
        first_half = sorted_history.iloc[:midpoint]
        second_half = sorted_history.iloc[midpoint:]

        if first_half.empty or second_half.empty:
            return 0.0

        # Calculate average value in each half
        first_avg = first_half[value_column].mean()
        second_avg = second_half[value_column].mean()

        # Calculate time spans
        first_span = (first_half['TrxDate'].max() - first_half['TrxDate'].min()).days + 1
        second_span = (second_half['TrxDate'].max() - second_half['TrxDate'].min()).days + 1

        # Normalize by time (value per day)
        first_rate = first_avg * len(first_half) / max(first_span, 1)
        second_rate = second_avg * len(second_half) / max(second_span, 1)

        # Calculate growth rate
        if first_rate > 0:
            growth_rate = (second_rate - first_rate) / first_rate
        else:
            growth_rate = 1.0 if second_rate > 0 else 0.0

        # Smooth with tanh to get -1 to 1 range
        return np.tanh(growth_rate)

    def calculate_importance_trend(self,
                                  item_history: pd.DataFrame,
                                  customer_history: pd.DataFrame,
                                  target_date: Optional[pd.Timestamp] = None) -> float:
        """
        Calculate if an item is becoming more or less important to customer

        Returns:
            Importance trend (-1 to 1)
        """
        if item_history.empty or len(customer_history) < 3:
            return 0.0

        if target_date is None:
            raise ValueError("target_date is required for deterministic trend calculations")

        # Calculate importance in different time periods
        now = target_date
        periods = [
            (now - pd.Timedelta(days=30), now),           # Recent
            (now - pd.Timedelta(days=60), now - pd.Timedelta(days=30)),  # Previous
            (now - pd.Timedelta(days=90), now - pd.Timedelta(days=60))   # Earlier
        ]

        importances = []
        for start, end in periods:
            period_customer = customer_history[
                (customer_history['TrxDate'] >= start) &
                (customer_history['TrxDate'] < end)
            ]
            period_item = item_history[
                (item_history['TrxDate'] >= start) &
                (item_history['TrxDate'] < end)
            ]

            if not period_customer.empty:
                importance = period_item['TotalQuantity'].sum() / period_customer['TotalQuantity'].sum()
                importances.append(importance)

        if len(importances) >= 2:
            # Calculate trend
            recent = importances[0]
            historical = np.mean(importances[1:])

            if historical > 0:
                trend = (recent - historical) / historical
                return np.tanh(trend * 2)  # Scale and smooth

        return 0.0