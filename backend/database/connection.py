"""
Database connection manager with connection pooling and retry logic
"""

import pyodbc
import pandas as pd
from typing import Optional, Dict, Any, List
import time
from contextlib import contextmanager
from queue import Queue, Empty
import threading

from backend.logging_config import get_logger
from backend.exceptions import DatabaseException
from backend.constants.config_constants import (
    DATABASE_CONNECTION_TIMEOUT,
    DATABASE_RETRY_ATTEMPTS,
    DATABASE_RETRY_DELAY
)

logger = get_logger(__name__)


class ConnectionPool:
    """
    Thread-safe connection pool for database connections
    Maintains a pool of reusable connections to improve performance
    """

    def __init__(self, connection_string: str, pool_size: int = 5, max_overflow: int = 10):
        """
        Initialize connection pool

        Args:
            connection_string: Database connection string
            pool_size: Number of connections to maintain in pool
            max_overflow: Maximum additional connections beyond pool_size
        """
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._pool: Queue = Queue(maxsize=pool_size + max_overflow)
        self._current_size = 0
        self._lock = threading.Lock()

        # Pre-create pool connections
        for _ in range(pool_size):
            try:
                conn = self._create_connection()
                self._pool.put(conn)
                self._current_size += 1
            except Exception as e:
                logger.warning(f"Failed to pre-create pool connection: {e}")

        logger.info(f"Connection pool initialized: {self._current_size}/{pool_size} connections created")

    def _create_connection(self) -> pyodbc.Connection:
        """Create a new database connection"""
        return pyodbc.connect(self.connection_string)

    def get_connection(self, timeout: float = 5.0) -> pyodbc.Connection:
        """
        Get a connection from the pool

        Args:
            timeout: Maximum time to wait for a connection (seconds)

        Returns:
            Database connection

        Raises:
            DatabaseException: If no connection available within timeout
        """
        try:
            # Try to get existing connection from pool
            conn = self._pool.get(timeout=timeout)

            # Validate connection is still alive
            try:
                conn.cursor().execute("SELECT 1")
                return conn
            except Exception:
                # Connection is dead, create a new one
                logger.debug("Stale connection detected, creating new connection")
                conn.close()
                return self._create_connection()

        except Empty:
            # Pool is empty, try to create new connection if under limit
            with self._lock:
                if self._current_size < (self.pool_size + self.max_overflow):
                    try:
                        conn = self._create_connection()
                        self._current_size += 1
                        logger.debug(f"Created new connection (total: {self._current_size})")
                        return conn
                    except Exception as e:
                        raise DatabaseException(f"Failed to create new connection: {e}")
                else:
                    raise DatabaseException(
                        f"Connection pool exhausted (max: {self.pool_size + self.max_overflow})"
                    )

    def return_connection(self, conn: pyodbc.Connection) -> None:
        """
        Return a connection to the pool

        Args:
            conn: Database connection to return
        """
        try:
            # Only return if connection is still valid
            if conn and not conn.closed:
                self._pool.put_nowait(conn)
            else:
                # Connection is closed, decrement count
                with self._lock:
                    self._current_size -= 1
        except Exception as e:
            logger.warning(f"Failed to return connection to pool: {e}")
            try:
                conn.close()
            except:
                pass
            with self._lock:
                self._current_size -= 1

    def close_all(self) -> None:
        """Close all connections in the pool"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing pooled connection: {e}")

        self._current_size = 0
        logger.info("All pool connections closed")


class DatabaseManager:
    """
    Manages database connections with connection pooling and retry logic
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
            self._pool: Optional[ConnectionPool] = None
            self._initialized = True

    def initialize(self, db_config: Dict[str, str], pool_size: int = 5) -> None:
        """
        Initialize database connection with connection pooling

        Args:
            db_config: Database configuration dictionary
            pool_size: Number of connections to maintain in pool
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

            # Initialize connection pool
            self._pool = ConnectionPool(self.connection_string, pool_size=pool_size)

            # Test connection
            self._test_connection()
            self.is_connected = True

            logger.info(
                f"Database initialized successfully with connection pool: {db_config['SERVER']}/{db_config['DATABASE']}",
                extra={
                    'server': db_config['SERVER'],
                    'database': db_config['DATABASE'],
                    'pool_size': pool_size
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
        Get database connection from pool with automatic cleanup

        Yields:
            pyodbc.Connection

        Raises:
            DatabaseException: If connection fails
        """
        if not self._pool:
            raise DatabaseException("Database not initialized. Call initialize() first.")

        connection = None
        try:
            # Get connection from pool
            connection = self._pool.get_connection()
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}", exc_info=True)
            raise DatabaseException(f"Failed to get database connection: {str(e)}")
        finally:
            # Return connection to pool (not closing it)
            if connection:
                try:
                    self._pool.return_connection(connection)
                except Exception as e:
                    logger.warning(f"Error returning connection to pool: {e}")

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
            pool_info = {}
            if self._pool:
                pool_info = {
                    'pool_size': self._pool.pool_size,
                    'current_connections': self._pool._current_size
                }

            return {
                'status': 'healthy',
                'connected': True,
                'message': 'Database connection successful',
                **pool_info
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'message': str(e)
            }

    def close_pool(self) -> None:
        """Close all connections in the pool"""
        if self._pool:
            self._pool.close_all()
            logger.info("Database connection pool closed")


# Singleton instance
_database_manager = DatabaseManager()


def get_database_manager() -> DatabaseManager:
    """Get the singleton database manager instance"""
    return _database_manager
