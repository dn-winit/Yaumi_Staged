"""
Centralized data manager with dynamic paths
Loads all data on startup and provides it to all services
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

from backend.config import (
    DATABASE_CONFIG,
    get_sql_query_path,
    get_cache_file_path,
    get_data_file_path
)
from backend.database import get_database_manager
from backend.logging_config import get_logger
from backend.exceptions import DatabaseException, DataNotLoadedException

logger = get_logger(__name__)

class DataManager:
    """
    Singleton data manager that loads all data on startup
    and keeps it in memory for fast access
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.demand_data = pd.DataFrame()
            self.customer_data = pd.DataFrame()
            self.journey_plan = pd.DataFrame()
            self.merged_demand = pd.DataFrame()
            self.last_refresh = None
            self.is_loaded = False
            self._initialized = True

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize all data on server startup
        This is called once when the server starts
        """
        logger.info("="*60)
        logger.info("INITIALIZING DATA MANAGER")
        logger.info("="*60)

        result = {
            'success': False,
            'data': {},
            'errors': []
        }

        try:
            # Initialize database manager
            db_manager = get_database_manager()
            if not db_manager.is_connected:
                db_manager.initialize(DATABASE_CONFIG)

            # Load each data type
            logger.info("Fetching data from SQL Server...")

            # 1. Load demand data
            logger.info("1. Loading demand data...")
            self.demand_data = self._fetch_sql_data('demand_data')
            if not self.demand_data.empty:
                self.demand_data['TrxDate'] = pd.to_datetime(self.demand_data['TrxDate'])
                result['data']['demand_rows'] = len(self.demand_data)
                logger.info(f"   ✓ Loaded {len(self.demand_data)} demand records")
            else:
                result['errors'].append("Failed to load demand data")

            # 2. Load recent demand data
            logger.info("2. Loading recent demand data...")
            recent_demand = self._fetch_sql_data('recent_demand')
            if not recent_demand.empty:
                recent_demand['TrxDate'] = pd.to_datetime(recent_demand['TrxDate'])
                result['data']['recent_demand_rows'] = len(recent_demand)
                logger.info(f"   ✓ Loaded {len(recent_demand)} recent demand records")

            # 3. Merge demand data
            logger.info("3. Merging demand data...")
            self.merged_demand = self._merge_demand_data(self.demand_data, recent_demand)
            result['data']['merged_demand_rows'] = len(self.merged_demand)
            logger.info(f"   ✓ Merged total: {len(self.merged_demand)} records")

            # 4. Load customer data
            logger.info("4. Loading customer data...")
            self.customer_data = self._fetch_sql_data('customer_data')
            if not self.customer_data.empty:
                self.customer_data['TrxDate'] = pd.to_datetime(self.customer_data['TrxDate'])
                result['data']['customer_rows'] = len(self.customer_data)
                logger.info(f"   ✓ Loaded {len(self.customer_data)} customer records")
            else:
                result['errors'].append("Failed to load customer data")

            # 5. Load journey plan
            logger.info("5. Loading journey plan...")
            self.journey_plan = self._fetch_sql_data('journey_plan')
            if not self.journey_plan.empty:
                self.journey_plan['JourneyDate'] = pd.to_datetime(self.journey_plan['JourneyDate'])
                result['data']['journey_rows'] = len(self.journey_plan)
                logger.info(f"   ✓ Loaded {len(self.journey_plan)} journey records")
            else:
                result['errors'].append("Failed to load journey plan")

            # Save to cache
            logger.info("6. Caching data to disk...")
            self._save_cache()

            # Set metadata
            self.last_refresh = datetime.now()
            self.is_loaded = True

            # Add summary to result
            if not self.merged_demand.empty:
                result['data']['date_range'] = {
                    'start': str(self.merged_demand['TrxDate'].min()),
                    'end': str(self.merged_demand['TrxDate'].max())
                }
                result['data']['unique_customers'] = len(self.customer_data['CustomerCode'].unique()) if not self.customer_data.empty else 0
                result['data']['unique_items'] = len(self.merged_demand['ItemCode'].unique()) if not self.merged_demand.empty else 0
                result['data']['routes'] = list(self.merged_demand['RouteCode'].unique()) if not self.merged_demand.empty else []

            result['success'] = len(result['errors']) == 0
            result['last_refresh'] = self.last_refresh.isoformat()

            logger.info("="*60)
            logger.info(f"DATA INITIALIZATION {'SUCCESSFUL' if result['success'] else 'COMPLETED WITH ERRORS'}")
            logger.info(f"Total records loaded: {sum(v for k, v in result['data'].items() if 'rows' in k)}")
            logger.info("="*60)

        except DatabaseException as e:
            logger.error(f"Database error during initialization: {e}", exc_info=True)
            result['errors'].append(str(e))
        except Exception as e:
            logger.error(f"Data initialization failed: {e}", exc_info=True)
            result['errors'].append(str(e))

        return result

    def _fetch_sql_data(self, query_name: str) -> pd.DataFrame:
        """Fetch data from SQL Server using DatabaseManager"""
        query_path = get_sql_query_path(query_name)
        cache_file = get_cache_file_path(f'{query_name}.csv')

        try:
            # Try to read SQL query and execute
            if query_path.exists():
                db_manager = get_database_manager()
                df = db_manager.execute_query_from_file(str(query_path))

                # Save to cache
                if not df.empty:
                    df.to_csv(cache_file, index=False)
                    logger.debug(f"Cached {query_name} data: {len(df)} rows")

                return df
            else:
                logger.warning(f"SQL query file not found: {query_path}")

        except DatabaseException as e:
            logger.warning(f"SQL fetch failed for {query_name}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fetching {query_name}: {e}")

        # Try to load from cache
        if cache_file.exists():
            logger.info(f"Loading {query_name} from cache: {cache_file}")
            return pd.read_csv(cache_file)

        # Try to load from data directory
        data_file = get_data_file_path(f'{query_name}.csv')
        if data_file.exists():
            logger.info(f"Loading {query_name} from data: {data_file}")
            return pd.read_csv(data_file)

        return pd.DataFrame()

    def _merge_demand_data(self, demand_df: pd.DataFrame, recent_df: pd.DataFrame) -> pd.DataFrame:
        """Merge historical and recent demand data"""
        if demand_df.empty:
            return recent_df

        if recent_df.empty:
            return demand_df

        # Common columns
        common_columns = [
            'TrxDate', 'WarehouseCode', 'WarehouseName', 'RouteCode',
            'ItemCode', 'ItemName', 'CategoryName', 'TotalQuantity',
            'AvgUnitPrice', 'SalesValue', 'Predicted'
        ]

        # Select common columns and merge
        merged = pd.concat([
            demand_df[common_columns],
            recent_df[common_columns]
        ], ignore_index=True)

        # Sort by date
        merged = merged.sort_values('TrxDate').reset_index(drop=True)

        return merged

    def _save_cache(self):
        """Save all data to cache files using dynamic paths"""
        try:
            self.merged_demand.to_csv(get_cache_file_path('merged_demand.csv'), index=False)
            self.customer_data.to_csv(get_cache_file_path('customer_data.csv'), index=False)
            self.journey_plan.to_csv(get_cache_file_path('journey_plan.csv'), index=False)
            logger.info("   ✓ Data cached successfully")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def get_demand_data(self, route_filter: Optional[int] = None) -> pd.DataFrame:
        """Get demand data, optionally filtered by route"""
        if not self.is_loaded:
            return pd.DataFrame()

        df = self.merged_demand.copy()
        if route_filter:
            # Convert route_filter to string for comparison
            df = df[df['RouteCode'] == str(route_filter)]
        return df

    def get_customer_data(self, route_filter: Optional[int] = None) -> pd.DataFrame:
        """Get customer data, optionally filtered by route"""
        if not self.is_loaded:
            return pd.DataFrame()

        df = self.customer_data.copy()
        if route_filter:
            # Convert route_filter to string for comparison
            df = df[df['RouteCode'] == str(route_filter)]
        return df

    def get_journey_plan(self, route_filter: Optional[int] = None, date: Optional[str] = None) -> pd.DataFrame:
        """Get journey plan, optionally filtered"""
        if not self.is_loaded:
            return pd.DataFrame()

        df = self.journey_plan.copy()

        if route_filter:
            # Convert route_filter to string for comparison
            df = df[df['RouteCode'] == str(route_filter)]

        if date:
            target_date = pd.to_datetime(date)
            df = df[df['JourneyDate'] == target_date]

        return df

    def get_summary(self) -> Dict[str, Any]:
        """Get data summary"""
        if not self.is_loaded:
            return {'loaded': False}

        return {
            'loaded': True,
            'last_refresh': self.last_refresh.isoformat() if self.last_refresh else None,
            'demand_records': len(self.merged_demand),
            'customer_records': len(self.customer_data),
            'journey_records': len(self.journey_plan),
            'date_range': {
                'start': str(self.merged_demand['TrxDate'].min()) if not self.merged_demand.empty else None,
                'end': str(self.merged_demand['TrxDate'].max()) if not self.merged_demand.empty else None
            },
            'routes': list(self.merged_demand['RouteCode'].unique()) if not self.merged_demand.empty else [],
            'unique_customers': len(self.customer_data['CustomerCode'].unique()) if not self.customer_data.empty else 0,
            'unique_items': len(self.merged_demand['ItemCode'].unique()) if not self.merged_demand.empty else 0
        }

# Create singleton instance
data_manager = DataManager()