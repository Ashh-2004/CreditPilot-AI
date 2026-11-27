"""
Tests for SQL schema file syntax validation.
"""

from pathlib import Path


def test_create_tables_sql_syntax():
    """Verify that Create tables.sql does not contain illegal characters and parses properly."""
    schema_path = Path(__file__).resolve().parent.parent / "Create tables.sql"
    assert schema_path.exists(), "Create tables.sql must exist"

    content = schema_path.read_text(encoding="utf-8")
    assert r"\, " not in content and r"\," not in content, "Found stray backslash syntax error in Create tables.sql"
    assert "CREATE DATABASE loaniq_db;" in content
    assert "CREATE TABLE users" in content
    assert "CREATE TABLE borrowers" in content
    assert "CREATE TABLE loan_applications" in content
    assert "CREATE TABLE loans" in content
    assert "CREATE TABLE payments" in content
    assert "CREATE TABLE emi_schedule" in content
    assert "CREATE TABLE collateral" in content
