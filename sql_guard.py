"""
SQL Guard: AST-based validation, sanitization, and security enforcement
for the Natural Language AI Query Assistant in LoanSense AI.

Enforces:
1. Single statement execution (disallowing semicolon chaining/stacked queries).
2. Strict read-only SELECT statement types.
3. Strict table allowlist matching loaniq_db schema.
4. Protection of sensitive columns (e.g. users.password_hash).
5. Elimination of destructive DDL/DML, file I/O, and dangerous SQL functions.
6. Enforced row limits (clamping to max 100 rows).
"""

import re
from typing import Tuple, Set, Optional
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Function
from sqlparse.tokens import Keyword, DML, DDL, Punctuation, Whitespace


ALLOWED_TABLES: Set[str] = {
    "users",
    "borrowers",
    "loan_applications",
    "loans",
    "payments",
    "emi_schedule",
    "collateral",
}

FORBIDDEN_KEYWORDS: Set[str] = {
    "insert", "update", "delete", "drop", "truncate", "alter",
    "create", "replace", "grant", "revoke", "rename", "call",
    "exec", "execute", "set", "show", "describe", "use",
    "load", "outfile", "dumpfile", "information_schema", "mysql",
    "performance_schema", "sys", "into"
}

FORBIDDEN_FUNCTIONS: Set[str] = {
    "sleep", "benchmark", "load_file", "system_user", "session_user",
    "user", "version", "database", "schema"
}

PROHIBITED_COLUMNS_BY_TABLE: dict[str, Set[str]] = {
    "users": {"password_hash"}
}

MAX_ALLOWED_ROWS: int = 100


def _extract_table_names(tokens) -> Set[str]:
    """Recursively traverses SQL tokens to extract table names following FROM or JOIN."""
    tables = set()
    from_seen = False

    for token in tokens:
        if token.is_whitespace:
            continue

        if token.ttype is Keyword and token.value.upper() in ("FROM", "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN"):
            from_seen = True
            continue

        if from_seen:
            if isinstance(token, IdentifierList):
                for identifier in token.get_identifiers():
                    name = identifier.get_real_name()
                    if name:
                        tables.add(name.lower().strip("`'\""))
                from_seen = False
            elif isinstance(token, Identifier):
                name = token.get_real_name()
                if name:
                    tables.add(name.lower().strip("`'\""))
                from_seen = False
            elif token.ttype is Keyword or isinstance(token, Where):
                from_seen = False

        if hasattr(token, "tokens"):
            tables.update(_extract_table_names(token.tokens))

    return tables


def _check_forbidden_constructs(sql: str) -> Optional[str]:
    """Checks raw SQL for forbidden functions, keywords, or constructs."""
    clean_sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    clean_sql = re.sub(r'/\*.*?\*/', '', clean_sql, flags=re.DOTALL)
    lower_sql = clean_sql.lower()

    # Reject INTO OUTFILE / DUMPFILE
    if re.search(r"\binto\s+(outfile|dumpfile)\b", lower_sql):
        return "File output operations ('INTO OUTFILE / DUMPFILE') are strictly forbidden."

    # Check forbidden functions
    for fn in FORBIDDEN_FUNCTIONS:
        if re.search(rf"\b{fn}\s*\(", lower_sql):
            return f"Dangerous SQL function '{fn}()' is strictly prohibited."

    # Check forbidden keywords
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", lower_sql):
            # Allow 'into' only if it's not present or matched above; keyword set has 'into'
            if kw == "into":
                return "The 'INTO' clause is not allowed in read-only queries."
            return f"Forbidden keyword or command detected: '{kw.upper()}'."

    # Check sensitive columns in users table
    if "users" in lower_sql and "password_hash" in lower_sql:
        return "Access to sensitive credentials ('password_hash') is forbidden."

    if "users" in lower_sql and re.search(r"select\s+\*\s+from\s+users", lower_sql):
        return "Wildcard 'SELECT * FROM users' is blocked to protect sensitive credentials."

    return None


def enforce_row_limit(sql: str, max_rows: int = MAX_ALLOWED_ROWS) -> str:
    """
    Enforces a strict row limit on the query:
    - If a LIMIT exists and exceeds max_rows, clamps it to max_rows.
    - If no LIMIT exists, appends LIMIT max_rows.
    """
    clean_sql = sql.strip().rstrip(";")
    limit_match = re.search(r"\blimit\s+(\d+)(\s*,\s*(\d+))?(\s+offset\s+(\d+))?\s*$", clean_sql, flags=re.IGNORECASE)

    if limit_match:
        # If LIMIT N format
        if limit_match.group(1) and not limit_match.group(3):
            current_limit = int(limit_match.group(1))
            if current_limit > max_rows:
                # Replace with max_rows
                clean_sql = clean_sql[:limit_match.start()] + f"LIMIT {max_rows}"
            return clean_sql
        # If LIMIT offset, count format
        elif limit_match.group(3):
            offset = int(limit_match.group(1))
            count = int(limit_match.group(3))
            if count > max_rows:
                clean_sql = clean_sql[:limit_match.start()] + f"LIMIT {offset}, {max_rows}"
            return clean_sql

    return f"{clean_sql} LIMIT {max_rows}"


def validate_and_sanitize_sql(sql: str) -> Tuple[bool, str, str]:
    """
    Validates that a SQL query is a safe, single-statement read-only SELECT,
    checks table allowlists and forbidden functions, and applies a row limit.

    Returns:
        (is_valid: bool, sanitized_sql_or_error_msg: str, error_detail: str)
    """
    if not sql or not sql.strip():
        return False, "Query cannot be empty.", "Empty input"

    # Remove comments
    clean_sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    clean_sql = re.sub(r'/\*.*?\*/', '', clean_sql, flags=re.DOTALL).strip()

    # 1. Parse statement AST
    try:
        parsed_statements = sqlparse.parse(clean_sql)
    except Exception as e:
        return False, f"Failed to parse SQL query: {e}", "Parse Error"

    if not parsed_statements:
        return False, "Query cannot be empty.", "Empty parsed statement"

    # Enforce exactly one statement (reject stacked queries / semicolons)
    non_empty_stmts = [s for s in parsed_statements if str(s).strip().strip(";")]
    if len(non_empty_stmts) != 1:
        return False, "Multiple SQL statements detected. Only a single query may be executed.", "Stacked Query Detected"

    stmt = non_empty_stmts[0]

    # 2. Enforce statement type is strictly SELECT
    stmt_type = stmt.get_type()
    if stmt_type != "SELECT":
        return False, f"Invalid statement type '{stmt_type}'. Only read-only SELECT queries are allowed.", "Non-SELECT statement"

    # 3. Check for forbidden keywords, functions, or columns
    error_msg = _check_forbidden_constructs(clean_sql)
    if error_msg:
        return False, f"Security Block: {error_msg}", "Forbidden Keyword or Construct"

    # 4. Enforce Table Allowlist
    tables = _extract_table_names(stmt.tokens)
    if tables:
        disallowed_tables = tables - ALLOWED_TABLES
        if disallowed_tables:
            return False, f"Security Block: Access to table(s) {sorted(list(disallowed_tables))} is not permitted.", "Disallowed Table"

    # 5. Enforce Row Limits
    sanitized_sql = enforce_row_limit(clean_sql, max_rows=MAX_ALLOWED_ROWS)

    return True, sanitized_sql, ""
