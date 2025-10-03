"""
Database connection manager with connection pooling and retry logic
"""

import pyodbc
import pandas as pd
from typing import Optional, Dict, Any
import time
from contextlib import contextmanager

from backend.logging_config import get_logger
from backend.exceptions import DatabaseException
from backend.constants.config_constants import (
    DATABASE_CONNECTION_TIMEOUT,
    DATABASE_RETRY_ATTEMPTS,
    DATABASE_RETRY_DELAY
)

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages database connections with retry logic and connection pooling
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.connection_string: Optional[str] = None
            self.is_connected = False
            self._initialized = True

    def initialize(self, db_config: Dict[str, str]) -> None:
        """
        Initialize database connection

        Args:
            db_config: Database configuration dictionary
        """
        try:
            self.connection_string = (
                f"DRIVER={db_config['DRIVER']};"
                f"SERVER={db_config['SERVER']};"
                f"DATABASE={db_config['DATABASE']};"
                f"UID={db_config['UID']};"
                f"PWD={db_config['PWD']};"
                f"Timeout={DATABASE_CONNECTION_TIMEOUT};"
            )

            # Test connection
            self._test_connection()
            self.is_connected = True

            logger.info(
                f"Database initialized successfully: {db_config['SERVER']}/{db_config['DATABASE']}",
                extra={
                    'server': db_config['SERVER'],
                    'database': db_config['DATABASE'],
                }
            )

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            self.is_connected = False
            raise DatabaseException(f"Database initialization failed: {str(e)}")

    def _test_connection(self) -> None:
        """Test database connection"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()

    @contextmanager
    def get_connection(self):
        """
        Get database connection with automatic cleanup

        Yields:
            pyodbc.Connection

        Raises:
            DatabaseException: If connection fails
        """
        if not self.connection_string:
            raise DatabaseException("Database not initialized. Call initialize() first.")

        connection = None
        try:
            connection = pyodbc.connect(self.connection_string)
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}", exc_info=True)
            raise DatabaseException(f"Failed to connect to database: {str(e)}")
        finally:
            if connection:
                try:
                    connection.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        retry: bool = True
    ) -> pd.DataFrame:
        """
        Execute SQL query with retry logic

        Args:
            query: SQL query string
            params: Query parameters
            retry: Whether to retry on failure

        Returns:
            DataFrame with query results

        Raises:
            DatabaseException: If query execution fails
        """
        attempts = DATABASE_RETRY_ATTEMPTS if retry else 1

        for attempt in range(1, attempts + 1):
            try:
                with self.get_connection() as connection:
                    if params:
                        df = pd.read_sql(query, connection, params=params)
                    else:
                        df = pd.read_sql(query, connection)

                    logger.debug(
                        f"Query executed successfully: {len(df)} rows returned",
                        extra={'rows': len(df), 'attempt': attempt}
                    )

                    return df

            except Exception as e:
                logger.warning(
                    f"Query execution failed (attempt {attempt}/{attempts}): {e}",
                    extra={'attempt': attempt, 'max_attempts': attempts}
                )

                if attempt < attempts:
                    time.sleep(DATABASE_RETRY_DELAY * attempt)  # Exponential backoff
                else:
                    raise DatabaseException(
                        f"Query execution failed after {attempts} attempts: {str(e)}",
                        details={'query': query[:100], 'attempts': attempts}
                    )

        return pd.DataFrame()

    def execute_query_from_file(self, query_file_path: str, retry: bool = True) -> pd.DataFrame:
        """
        Execute SQL query from file

        Args:
            query_file_path: Path to SQL file
            retry: Whether to retry on failure

        Returns:
            DataFrame with query results

        Raises:
            DatabaseException: If file read or query execution fails
        """
        try:
            with open(query_file_path, 'r', encoding='utf-8') as f:
                query = f.read()

            return self.execute_query(query, retry=retry)

        except FileNotFoundError:
            raise DatabaseException(f"SQL file not found: {query_file_path}")
        except Exception as e:
            raise DatabaseException(f"Failed to execute query from file: {str(e)}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check database health

        Returns:
            Health status dictionary
        """
        try:
            self._test_connection()
            return {
                'status': 'healthy',
                'connected': True,
                'message': 'Database connection successful'
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'message': str(e)
            }


# Singleton instance
_database_manager = DatabaseManager()


def get_database_manager() -> DatabaseManager:
    """Get the singleton database manager instance"""
    return _database_manager
