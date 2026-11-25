"""
Tests for database connection pooling, safe inserts, and resource cleanups in db.py.
"""

from unittest.mock import MagicMock, patch
import pytest
import db


def test_get_connection_pool_structure():
    """Verify that get_connection_pool returns a MySQLConnectionPool or None gracefully."""
    pool = db.get_connection_pool(pool_name="test_pool", pool_size=2)
    # When MySQL is offline, it gracefully returns None without crashing
    assert pool is None or hasattr(pool, "get_connection")


def test_execute_insert_returns_lastrowid():
    """Verify execute_insert returns cur.lastrowid and commits."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.lastrowid = 42
    mock_conn.cursor.return_value = mock_cur

    with patch("db.get_conn", return_value=mock_conn):
        last_id = db.execute_insert("INSERT INTO borrowers (full_name) VALUES (%s)", ("Test Borrower",))
        assert last_id == 42
        mock_cur.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()


def test_fetch_all_cleans_up_on_exception():
    """Verify fetch_all closes both cursor and connection even if an exception occurs."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.execute.side_effect = RuntimeError("Simulated query failure")
    mock_conn.cursor.return_value = mock_cur

    with patch("db.get_conn", return_value=mock_conn):
        with pytest.raises(RuntimeError):
            db.fetch_all("SELECT * FROM non_existent_table")

        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()


def test_execute_cleans_up_on_exception():
    """Verify execute closes both cursor and connection even if an exception occurs."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.execute.side_effect = RuntimeError("Simulated execution failure")
    mock_conn.cursor.return_value = mock_cur

    with patch("db.get_conn", return_value=mock_conn):
        with pytest.raises(RuntimeError):
            db.execute("UPDATE loans SET status = %s", ("defaulted",))

        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()
