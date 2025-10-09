"""
Supervision Storage Manager
Handles saving and retrieving supervision sessions from YaumiAIML database
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from backend.database import get_database_manager
from backend.logging_config import get_logger
from backend.exceptions import DatabaseException

logger = get_logger(__name__)


class SupervisionStorage:
    """Manages storage and retrieval of supervision sessions in database"""

    def __init__(self):
        self.db_manager = get_database_manager()
        self.route_table = "[YaumiAIML].[dbo].[tbl_supervision_route_summary]"
        self.customer_table = "[YaumiAIML].[dbo].[tbl_supervision_customer_summary]"
        self.item_table = "[YaumiAIML].[dbo].[tbl_supervision_item_details]"

    def save_supervision_session(
        self,
        session_data: Dict[str, Any],
        customer_summaries: List[Dict[str, Any]],
        item_details: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Save complete supervision session (route + customers + items)

        Args:
            session_data: Route-level summary data
            customer_summaries: List of customer summary records
            item_details: List of item detail records

        Returns:
            Result dictionary with success status
        """
        logger.info(f"Starting save: {len(customer_summaries)} customers, {len(item_details)} items")
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # 1. Upsert Route Summary
                route_merge = f"""
                    MERGE INTO {self.route_table} AS target
                        USING (SELECT ? AS session_id) AS source
                        ON target.session_id = source.session_id
                        WHEN MATCHED THEN
                            UPDATE SET
                                total_customers_visited = ?,
                                customer_completion_rate = ?,
                                total_skus_recommended = ?,
                                total_skus_sold = ?,
                                sku_coverage_rate = ?,
                                total_qty_recommended = ?,
                                total_qty_actual = ?,
                                qty_fulfillment_rate = ?,
                                redistribution_count = ?,
                                redistribution_qty = ?,
                                route_performance_score = ?,
                                llm_performance_analysis = ?,
                                session_status = ?
                        WHEN NOT MATCHED THEN
                            INSERT (
                                session_id, route_code, supervision_date,
                                total_customers_planned, total_customers_visited, customer_completion_rate,
                                total_skus_recommended, total_skus_sold, sku_coverage_rate,
                                total_qty_recommended, total_qty_actual, qty_fulfillment_rate,
                                redistribution_count, redistribution_qty,
                                route_performance_score, llm_performance_analysis, session_status
                            )
                            VALUES (
                                ?, ?, ?,
                                ?, ?, ?,
                                ?, ?, ?,
                                ?, ?, ?,
                                ?, ?,
                                ?, ?, ?
                            );
                """

                cursor.execute(route_merge, (
                    # MATCHED params
                    session_data['session_id'],
                    session_data['total_customers_visited'],
                    session_data['customer_completion_rate'],
                    session_data['total_skus_recommended'],
                    session_data['total_skus_sold'],
                    session_data['sku_coverage_rate'],
                    session_data['total_qty_recommended'],
                    session_data['total_qty_actual'],
                    session_data['qty_fulfillment_rate'],
                    session_data['redistribution_count'],
                    session_data['redistribution_qty'],
                    session_data['route_performance_score'],
                    session_data.get('llm_performance_analysis'),
                    session_data.get('session_status', 'active'),
                    # NOT MATCHED params
                    session_data['session_id'],
                    session_data['route_code'],
                    session_data['supervision_date'],
                    session_data['total_customers_planned'],
                    session_data['total_customers_visited'],
                    session_data['customer_completion_rate'],
                    session_data['total_skus_recommended'],
                    session_data['total_skus_sold'],
                    session_data['sku_coverage_rate'],
                    session_data['total_qty_recommended'],
                    session_data['total_qty_actual'],
                    session_data['qty_fulfillment_rate'],
                    session_data['redistribution_count'],
                    session_data['redistribution_qty'],
                    session_data['route_performance_score'],
                    session_data.get('llm_performance_analysis'),
                    session_data.get('session_status', 'active')
                ))
                logger.info(f"Route summary saved")

                # 2. Upsert Customer Summaries
                customer_merge = f"""
                    MERGE INTO {self.customer_table} AS target
                    USING (SELECT ? AS session_id, ? AS customer_code) AS source
                    ON target.session_id = source.session_id
                       AND target.customer_code = source.customer_code
                    WHEN MATCHED THEN
                        UPDATE SET
                            visit_sequence = ?,
                            visit_timestamp = ?,
                            total_skus_recommended = ?,
                            total_skus_sold = ?,
                            sku_coverage_rate = ?,
                            total_qty_recommended = ?,
                            total_qty_actual = ?,
                            qty_fulfillment_rate = ?,
                            customer_performance_score = ?,
                            llm_performance_analysis = ?,
                            record_saved_at = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (
                            session_id, customer_code,
                            visit_sequence, visit_timestamp,
                            total_skus_recommended, total_skus_sold, sku_coverage_rate,
                            total_qty_recommended, total_qty_actual, qty_fulfillment_rate,
                            customer_performance_score, llm_performance_analysis
                        )
                        VALUES (
                            ?, ?,
                            ?, ?,
                            ?, ?, ?,
                            ?, ?, ?,
                            ?, ?
                        );
                """

                for customer in customer_summaries:
                    cursor.execute(customer_merge, (
                    # MATCHED params
                    customer['session_id'],
                    customer['customer_code'],
                    customer['visit_sequence'],
                    customer['visit_timestamp'],
                    customer['total_skus_recommended'],
                    customer['total_skus_sold'],
                    customer['sku_coverage_rate'],
                    customer['total_qty_recommended'],
                    customer['total_qty_actual'],
                    customer['qty_fulfillment_rate'],
                    customer['customer_performance_score'],
                    customer.get('llm_performance_analysis'),
                    # NOT MATCHED params
                    customer['session_id'],
                    customer['customer_code'],
                    customer['visit_sequence'],
                    customer['visit_timestamp'],
                    customer['total_skus_recommended'],
                    customer['total_skus_sold'],
                    customer['sku_coverage_rate'],
                    customer['total_qty_recommended'],
                    customer['total_qty_actual'],
                    customer['qty_fulfillment_rate'],
                    customer['customer_performance_score'],
                    customer.get('llm_performance_analysis')
                ))
                logger.info(f"Customer summaries saved: {len(customer_summaries)} records")

                # 3. Upsert Item Details
                item_merge = f"""
                    MERGE INTO {self.item_table} AS target
                    USING (SELECT ? AS session_id, ? AS customer_code, ? AS item_code) AS source
                    ON target.session_id = source.session_id
                       AND target.customer_code = source.customer_code
                       AND target.item_code = source.item_code
                    WHEN MATCHED THEN
                        UPDATE SET
                            adjusted_recommended_qty = ?,
                            recommendation_adjustment = ?,
                            final_actual_qty = ?,
                            actual_adjustment = ?,
                            was_manually_edited = ?,
                            was_item_sold = ?,
                            record_saved_at = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (
                            session_id, customer_code, item_code, item_name,
                            original_recommended_qty, adjusted_recommended_qty, recommendation_adjustment,
                            original_actual_qty, final_actual_qty, actual_adjustment,
                            was_manually_edited, was_item_sold,
                            recommendation_tier, priority_score, van_inventory_qty,
                            days_since_last_purchase, purchase_cycle_days, purchase_frequency_pct,
                            visit_timestamp
                        )
                        VALUES (
                            ?, ?, ?, ?,
                            ?, ?, ?,
                            ?, ?, ?,
                            ?, ?,
                            ?, ?, ?,
                            ?, ?, ?,
                            ?
                        );
                """

                for item in item_details:
                    cursor.execute(item_merge, (
                        # MATCHED params
                        item['session_id'],
                        item['customer_code'],
                        item['item_code'],
                        item['adjusted_recommended_qty'],
                        item['recommendation_adjustment'],
                        item['final_actual_qty'],
                        item['actual_adjustment'],
                        item['was_manually_edited'],
                        item['was_item_sold'],
                        # NOT MATCHED params
                        item['session_id'],
                        item['customer_code'],
                        item['item_code'],
                        item['item_name'],
                        item['original_recommended_qty'],
                        item['adjusted_recommended_qty'],
                        item['recommendation_adjustment'],
                        item['original_actual_qty'],
                        item['final_actual_qty'],
                        item['actual_adjustment'],
                        item['was_manually_edited'],
                        item['was_item_sold'],
                        item['recommendation_tier'],
                        item['priority_score'],
                        item['van_inventory_qty'],
                        item['days_since_last_purchase'],
                        item['purchase_cycle_days'],
                        item['purchase_frequency_pct'],
                        item['visit_timestamp']
                    ))
                logger.info(f"Item details saved: {len(item_details)} records")

                logger.info(f"Committing transaction...")
                conn.commit()
                logger.info(f"Transaction committed successfully")

                logger.info(
                    f"Saved supervision session: {session_data['session_id']} - "
                    f"{len(customer_summaries)} customers, {len(item_details)} items"
                )

                return {
                    'success': True,
                    'message': 'Supervision session saved successfully',
                    'session_id': session_data['session_id'],
                    'customers_saved': len(customer_summaries),
                    'items_saved': len(item_details)
                }

        except Exception as e:
            logger.error(f"Failed to save supervision session: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Database error: {str(e)}'
            }

    def load_supervision_session(self, session_id: str) -> Dict[str, Any]:
        """
        Load complete supervision session

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with route, customers, and items data
        """
        try:
            # Load route summary
            route_query = f"""
                SELECT * FROM {self.route_table}
                WHERE session_id = ?
            """
            route_df = self.db_manager.execute_query(route_query, (session_id,))

            if route_df.empty:
                return {'exists': False}

            # Load customer summaries
            customer_query = f"""
                SELECT * FROM {self.customer_table}
                WHERE session_id = ?
                ORDER BY visit_sequence
            """
            customer_df = self.db_manager.execute_query(customer_query, (session_id,))

            # Load item details
            item_query = f"""
                SELECT * FROM {self.item_table}
                WHERE session_id = ?
                ORDER BY customer_code, item_code
            """
            item_df = self.db_manager.execute_query(item_query, (session_id,))

            return {
                'exists': True,
                'route_summary': route_df.to_dict('records')[0] if not route_df.empty else None,
                'customer_summaries': customer_df.to_dict('records'),
                'item_details': item_df.to_dict('records')
            }

        except Exception as e:
            logger.error(f"Failed to load supervision session: {e}", exc_info=True)
            return {'exists': False, 'error': str(e)}

    def check_session_exists(self, route_code: str, date: str) -> Optional[str]:
        """
        Check if supervision session exists for route and date

        Returns:
            session_id if exists, None otherwise
        """
        try:
            query = f"""
                SELECT session_id FROM {self.route_table}
                WHERE route_code = ? AND supervision_date = ?
            """
            result = self.db_manager.execute_query(query, (route_code, date))

            if not result.empty:
                return result.iloc[0]['session_id']

            return None

        except Exception as e:
            logger.error(f"Failed to check session existence: {e}")
            return None


# Singleton instance
_supervision_storage = SupervisionStorage()


def get_supervision_storage() -> SupervisionStorage:
    """Get singleton supervision storage instance"""
    return _supervision_storage
