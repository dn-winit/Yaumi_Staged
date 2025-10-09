"""
Recommendation Storage Manager
Handles saving and retrieving daily recommendations from YaumiAIML database
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
from backend.database import get_database_manager
from backend.logging_config import get_logger
from backend.exceptions import DatabaseException

logger = get_logger(__name__)


class RecommendationStorage:
    """Manages storage and retrieval of daily recommendations in database"""

    def __init__(self):
        self.db_manager = get_database_manager()
        self.table_name = "[YaumiAIML].[dbo].[tbl_recommended_orders]"

    def save_recommendations(self, recommendations_df: pd.DataFrame, date: str, route_code: str) -> Dict[str, Any]:
        """
        Save daily recommendations to database with bulk insert
        Note: Recommendations are immutable (one-time per date). Cron job checks existence before calling.

        Args:
            recommendations_df: DataFrame with recommendation data
            date: Target date (YYYY-MM-DD)
            route_code: Route code

        Returns:
            Result dictionary with success status and details
        """
        try:
            if recommendations_df.empty:
                return {
                    'success': False,
                    'message': 'No recommendations to save',
                    'records_saved': 0
                }

            # Prepare bulk insert query
            insert_query = f"""
                INSERT INTO {self.table_name} (
                    trx_date, route_code, customer_code, item_code, item_name,
                    actual_quantity, recommended_quantity, tier, van_load, priority_score,
                    avg_quantity_per_visit, days_since_last_purchase,
                    purchase_cycle_days, frequency_percent,
                    generated_at, generated_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Prepare data for bulk insert
            generated_at = datetime.now()
            records = []

            for _, row in recommendations_df.iterrows():
                records.append((
                    row['TrxDate'],
                    str(row['RouteCode']),
                    str(row['CustomerCode']),
                    str(row['ItemCode']),
                    str(row['ItemName']),
                    int(row.get('ActualQuantity', 0)),
                    int(row['RecommendedQuantity']),
                    str(row['Tier']),
                    int(row['VanLoad']),
                    float(row['PriorityScore']),
                    int(row['AvgQuantityPerVisit']),
                    int(row['DaysSinceLastPurchase']),
                    float(row['PurchaseCycleDays']),
                    float(row['FrequencyPercent']),
                    generated_at,
                    'SYSTEM_CRON'
                ))

            # Execute bulk insert
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(insert_query, records)
                conn.commit()

            logger.info(f"Saved {len(records)} recommendations to database for {date}, route {route_code}")

            return {
                'success': True,
                'message': f'Successfully saved {len(records)} recommendations',
                'records_saved': len(records),
                'date': date,
                'route_code': route_code,
                'generated_at': generated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to save recommendations: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Database error: {str(e)}',
                'records_saved': 0
            }

    def get_recommendations(self, date: str, route_code: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve recommendations from database for a specific date

        Args:
            date: Target date (YYYY-MM-DD)
            route_code: Optional route filter

        Returns:
            DataFrame with recommendations or empty DataFrame if not found
        """
        try:
            # Convert date string to proper format for SQL Server
            from datetime import datetime
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()

            query = f"""
                SELECT
                    trx_date AS TrxDate,
                    route_code AS RouteCode,
                    customer_code AS CustomerCode,
                    item_code AS ItemCode,
                    item_name AS ItemName,
                    actual_quantity AS ActualQuantity,
                    recommended_quantity AS RecommendedQuantity,
                    tier AS Tier,
                    van_load AS VanLoad,
                    priority_score AS PriorityScore,
                    avg_quantity_per_visit AS AvgQuantityPerVisit,
                    days_since_last_purchase AS DaysSinceLastPurchase,
                    purchase_cycle_days AS PurchaseCycleDays,
                    frequency_percent AS FrequencyPercent,
                    generated_at
                FROM {self.table_name}
                WHERE CAST(trx_date AS DATE) = ?
                  {"AND route_code = ?" if route_code else ""}
                ORDER BY customer_code, priority_score DESC
            """

            params = (date_obj,) if not route_code else (date_obj, str(route_code))
            df = self.db_manager.execute_query(query, params)

            if not df.empty:
                logger.info(f"Retrieved {len(df)} recommendations from database for {date}")
            else:
                logger.info(f"No recommendations found in database for {date}")

            return df

        except Exception as e:
            logger.error(f"Failed to retrieve recommendations: {e}", exc_info=True)
            return pd.DataFrame()

    def check_exists(self, date: str, route_code: Optional[str] = None) -> bool:
        """
        Check if recommendations exist for a date

        Args:
            date: Target date (YYYY-MM-DD)
            route_code: Optional route filter

        Returns:
            True if recommendations exist, False otherwise
        """
        try:
            # Convert date string to proper format
            from datetime import datetime
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()

            query = f"""
                SELECT COUNT(*) as count
                FROM {self.table_name}
                WHERE CAST(trx_date AS DATE) = ?
                  {"AND route_code = ?" if route_code else ""}
            """

            params = (date_obj,) if not route_code else (date_obj, str(route_code))
            result = self.db_manager.execute_query(query, params)

            if not result.empty:
                count = result.iloc[0]['count']
                return count > 0

            return False

        except Exception as e:
            logger.error(f"Failed to check recommendations existence: {e}")
            return False

    def get_generation_info(self, date: str) -> Dict[str, Any]:
        """
        Get information about when recommendations were generated

        Args:
            date: Target date (YYYY-MM-DD)

        Returns:
            Dictionary with generation metadata
        """
        try:
            # Convert date string to proper format
            from datetime import datetime
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()

            query = f"""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT route_code) as routes_count,
                    COUNT(DISTINCT customer_code) as customers_count,
                    COUNT(DISTINCT item_code) as items_count,
                    MIN(generated_at) as first_generated,
                    MAX(generated_at) as last_generated,
                    MAX(generated_by) as generated_by
                FROM {self.table_name}
                WHERE CAST(trx_date AS DATE) = ?
            """

            result = self.db_manager.execute_query(query, (date_obj,))

            if not result.empty and result.iloc[0]['total_records'] > 0:
                row = result.iloc[0]
                return {
                    'exists': True,
                    'date': date,
                    'total_records': int(row['total_records']),
                    'routes_count': int(row['routes_count']),
                    'customers_count': int(row['customers_count']),
                    'items_count': int(row['items_count']),
                    'generated_at': str(row['last_generated']),
                    'generated_by': str(row['generated_by'])
                }

            return {'exists': False, 'date': date}

        except Exception as e:
            logger.error(f"Failed to get generation info: {e}")
            return {'exists': False, 'date': date, 'error': str(e)}


# Singleton instance
_storage = RecommendationStorage()


def get_recommendation_storage() -> RecommendationStorage:
    """Get singleton recommendation storage instance"""
    return _storage
