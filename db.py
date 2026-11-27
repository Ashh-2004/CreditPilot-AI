"""
Database connectivity and reliability module for LoanSense AI.
Provides pooled MySQL connections, robust resource cleanup, and transaction helpers.
Preserves existing fetch_all, execute, and get_conn signatures while adding safe insert handling
and read-only query execution with timeout and row limits.
"""

import logging
from typing import Any, List, Optional
import mysql.connector
from mysql.connector import Error as MySQLError
from mysql.connector.pooling import MySQLConnectionPool
import config

logger = logging.getLogger(__name__)

# Module-level connection pool singleton
_pool: Optional[MySQLConnectionPool] = None


def get_connection_pool(pool_name: str = "loaniq_pool", pool_size: int = 5) -> Optional[MySQLConnectionPool]:
    """
    Returns the singleton MySQLConnectionPool instance.
    Lazily initializes the pool on first call using centralized config.
    Falls back gracefully if the database service is currently unavailable.
    """
    global _pool
    if _pool is None:
        try:
            cfg = config.get_db_config()
            _pool = MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                **cfg
            )
            logger.info("Initialized MySQL connection pool '%s' (size=%d)", pool_name, pool_size)
        except MySQLError as err:
            logger.warning(
                "Could not initialize MySQL connection pool (%s). Direct connections will be used: %s",
                config.get_masked_db_config(),
                err,
            )
            _pool = None
    return _pool


def get_conn():
    """
    Acquires and returns a MySQL database connection.
    Attempts to pull from the connection pool first; falls back to a direct connection
    if pooling is uninitialized or exhausted.
    """
    pool = get_connection_pool()
    if pool is not None:
        try:
            return pool.get_connection()
        except MySQLError as err:
            logger.warning("Failed to obtain pooled connection, falling back to direct connection: %s", err)

    db_config = config.get_db_config()
    try:
        return mysql.connector.connect(**db_config)
    except MySQLError as err:
        logger.error(
            "Failed to connect to MySQL at %s:%s (database: %s). Error: %s",
            db_config["host"],
            db_config["port"],
            db_config["database"],
            err,
        )
        raise


def fetch_all(query: str, params: tuple = ()) -> List[dict]:
    """
    Executes a SELECT query and returns all matching records as a list of dictionaries.
    Guarantees that both the cursor and connection are closed safely in all cases.
    """
    conn = get_conn()
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


def execute(query: str, params: tuple = ()) -> None:
    """
    Executes a DML query (INSERT, UPDATE, DELETE) and commits changes.
    Guarantees that both the cursor and connection are closed safely in all cases.
    """
    conn = get_conn()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


def execute_insert(query: str, params: tuple = ()) -> int:
    """
    Executes an INSERT query, commits the transaction, and returns the generated AUTO_INCREMENT ID.
    Eliminates race conditions caused by secondary SELECT queries.
    """
    conn = get_conn()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        last_id = cur.lastrowid
        return last_id
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


def fetch_all_read_only(
    query: str,
    params: tuple = (),
    timeout_seconds: int = 10,
    max_rows: int = 100
) -> List[dict]:
    """
    Executes a read-only SELECT query with enforced query timeouts and row limits.
    Enforces transaction read-only context where supported.
    Guarantees resource cleanup.
    """
    if config.DB_READONLY_USER:
        conn = mysql.connector.connect(**config.get_readonly_db_config())
    else:
        conn = get_conn()
    cur = None
    try:
        cur = conn.cursor(dictionary=True)

        # Set read-only transaction and execution timeout if supported
        try:
            cur.execute("SET SESSION TRANSACTION READ ONLY")
        except Exception:
            pass

        try:
            # MySQL 5.7.8+ statement execution timeout in milliseconds
            cur.execute(f"SET SESSION max_execution_time = {timeout_seconds * 1000}")
        except Exception:
            pass

        cur.execute(query, params)
        if max_rows > 0:
            return cur.fetchmany(max_rows)
        return cur.fetchall()
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass
