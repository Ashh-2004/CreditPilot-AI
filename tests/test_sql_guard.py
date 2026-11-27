"""
Tests for SQL Guard (AST parsing, sanitization, table allowlists, row limits).
"""

import pytest
from sql_guard import validate_and_sanitize_sql, enforce_row_limit, ALLOWED_TABLES


def test_valid_select_query():
    sql = "SELECT full_name, credit_score FROM borrowers WHERE credit_score > 650 ORDER BY credit_score DESC"
    is_safe, sanitized, err = validate_and_sanitize_sql(sql)
    assert is_safe is True
    assert "LIMIT 100" in sanitized
    assert err == ""


def test_valid_join_query():
    sql = """
    SELECT b.full_name, a.loan_amount, a.status
    FROM loan_applications a
    JOIN borrowers b ON a.borrower_id = b.borrower_id
    WHERE a.status = 'approved'
    """
    is_safe, sanitized, err = validate_and_sanitize_sql(sql)
    assert is_safe is True
    assert "LIMIT 100" in sanitized


def test_reject_dml_insert():
    sql = "INSERT INTO borrowers (full_name, email) VALUES ('Hacker', 'hacker@test.com')"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False
    assert "Invalid statement type" in msg or "Forbidden" in msg


def test_reject_dml_delete():
    sql = "DELETE FROM borrowers WHERE borrower_id = 1"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False


def test_reject_ddl_drop():
    sql = "DROP TABLE borrowers"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False


def test_reject_stacked_queries():
    sql = "SELECT * FROM loans; DROP TABLE borrowers;"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False
    assert "Multiple SQL statements detected" in msg


def test_reject_disallowed_tables():
    sql = "SELECT * FROM information_schema.tables"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False
    assert "Security Block" in msg


def test_reject_arbitrary_unlisted_table():
    sql = "SELECT * FROM secret_financial_records"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False
    assert "not permitted" in msg


def test_reject_password_hash_access():
    sql = "SELECT username, password_hash FROM users"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False
    assert "password_hash" in msg


def test_reject_wildcard_select_on_users():
    sql = "SELECT * FROM users"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False
    assert "Wildcard 'SELECT * FROM users' is blocked" in msg


def test_reject_file_outfile_operations():
    sql = "SELECT * FROM loans INTO OUTFILE '/tmp/dump.txt'"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False
    assert "INTO" in msg or "OUTFILE" in msg


def test_reject_dangerous_functions_sleep():
    sql = "SELECT full_name, SLEEP(5) FROM borrowers"
    is_safe, msg, detail = validate_and_sanitize_sql(sql)
    assert is_safe is False
    assert "Dangerous SQL function" in msg


def test_limit_clamping():
    sql_no_limit = "SELECT loan_id, outstanding_balance FROM loans"
    assert enforce_row_limit(sql_no_limit, max_rows=100) == "SELECT loan_id, outstanding_balance FROM loans LIMIT 100"

    sql_small_limit = "SELECT loan_id FROM loans LIMIT 25"
    assert enforce_row_limit(sql_small_limit, max_rows=100) == "SELECT loan_id FROM loans LIMIT 25"

    sql_large_limit = "SELECT loan_id FROM loans LIMIT 500"
    assert enforce_row_limit(sql_large_limit, max_rows=100) == "SELECT loan_id FROM loans LIMIT 100"
