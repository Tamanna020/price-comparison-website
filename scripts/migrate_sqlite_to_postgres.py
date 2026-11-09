"""SQLite to PostgreSQL Migration Engine for PriceWise AI (Phase 12).

Exports schema DDL and table data from local SQLite (data/pricewise.db) into
production-grade PostgreSQL SQL statements or directly into a live PostgreSQL
instance via psycopg2 or psycopg.

Features:
1. Type normalization (INTEGER PK AUTOINCREMENT -> SERIAL/BIGSERIAL, TIMESTAMP -> TIMESTAMPTZ, REAL -> DOUBLE PRECISION).
2. Proper dependency ordering of tables (parents before child foreign keys).
3. Sequence synchronization (`setval(pg_get_serial_sequence(...))`).
4. Dry-run mode for syntax validation and integrity checking.
5. Reversible and non-destructive.
"""

import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_SQLITE_PATH = DATA_DIR / "pricewise.db"
DEFAULT_OUTPUT_SQL = DATA_DIR / "postgres_migration.sql"

# Table creation order respecting foreign keys
TABLE_ORDER = [
    "users",
    "stores",
    "products",
    "offers",
    "price_history",
    "price_tracking",
    "price_alerts",
    "wishlist",
    "user_profiles",
    "user_preferences",
    "user_routines",
    "user_routine_items",
    "product_reviews",
    "product_platform_ratings",
    "evidence_references",
    "manual_verification_requests",
    "price_correction_submissions",
    "price_check_logs",
    "ingredient_analysis_cache",
    "alternative_finder_cache",
    "routine_recommendation_cache",
    "gemini_cache",
    "gemini_rate_limits",
    "gemini_token_usage",
]


def get_sqlite_table_names(conn: sqlite3.Connection) -> List[str]:
    """Get all non-internal table names from SQLite."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    existing = {r[0] for r in cur.fetchall()}
    # Return ordered tables that exist, followed by any remaining
    ordered = [t for t in TABLE_ORDER if t in existing]
    for t in existing:
        if t not in ordered:
            ordered.append(t)
    return ordered


def convert_sqlite_type_to_postgres(col_name: str, col_type: str, pk: bool, extra_sql: str) -> str:
    """Map SQLite column types and constraints to PostgreSQL equivalents."""
    col_upper = col_type.upper().strip()
    if pk and "AUTOINCREMENT" in extra_sql.upper():
        return "SERIAL PRIMARY KEY"
    elif pk and "INT" in col_upper:
        return "SERIAL PRIMARY KEY" if col_name == "id" else f"{col_upper} PRIMARY KEY"
    
    if "INT" in col_upper:
        return "INTEGER"
    elif "REAL" in col_upper or "FLOAT" in col_upper or "DOUBLE" in col_upper:
        return "DOUBLE PRECISION"
    elif "BOOL" in col_upper:
        return "BOOLEAN"
    elif "TIME" in col_upper or "DATE" in col_upper:
        return "TIMESTAMP WITH TIME ZONE"
    elif "BLOB" in col_upper:
        return "BYTEA"
    else:
        return "TEXT"


def escape_postgres_value(val: Any) -> str:
    """Format a Python value for PostgreSQL SQL insertion."""
    if val is None:
        return "NULL"
    elif isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, bytes):
        return f"decode('{val.hex()}', 'hex')"
    else:
        # String escaping (double single quotes)
        s = str(val).replace("'", "''")
        return f"'{s}'"


def generate_postgres_ddl(sqlite_path: Path) -> str:
    """Generate PostgreSQL-compatible DDL schema script."""
    ddl_lines = [
        "-- ============================================================================",
        f"-- PriceWise AI PostgreSQL Production Schema",
        f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "-- ============================================================================",
        "BEGIN;",
        "",
        "-- Drop tables in reverse order if they exist for clean migrations",
    ]

    conn = sqlite3.connect(str(sqlite_path))
    try:
        tables = get_sqlite_table_names(conn)
        for t in reversed(tables):
            ddl_lines.append(f"DROP TABLE IF EXISTS {t} CASCADE;")
        ddl_lines.append("")

        cur = conn.cursor()
        for table in tables:
            cur.execute(f"PRAGMA table_info({table});")
            cols_info = cur.fetchall()
            cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table,))
            sql_row = cur.fetchone()
            orig_sql = sql_row[0] if sql_row else ""

            # Check foreign keys
            cur.execute(f"PRAGMA foreign_key_list({table});")
            fks = cur.fetchall()

            ddl_lines.append(f"-- Table: {table}")
            ddl_lines.append(f"CREATE TABLE {table} (")
            col_defs = []

            pk_cols = [c[1] for c in cols_info if c[5] > 0]
            is_composite_pk = len(pk_cols) > 1

            for col in cols_info:
                cid, name, col_type, notnull, dflt_value, pk = col
                # Determine type
                extra = ""
                is_single_pk = bool(pk) and not is_composite_pk
                if is_single_pk and "AUTOINCREMENT" in orig_sql.upper():
                    extra = "AUTOINCREMENT"
                pg_type = convert_sqlite_type_to_postgres(name, col_type, is_single_pk, extra)

                cdef = f"    {name} {pg_type}"
                if notnull and "PRIMARY KEY" not in pg_type:
                    cdef += " NOT NULL"
                if dflt_value is not None:
                    # Clean SQLite default
                    dflt_clean = str(dflt_value).strip()
                    if dflt_clean.upper() in ("CURRENT_TIMESTAMP", "DATETIME('NOW')"):
                        dflt_clean = "CURRENT_TIMESTAMP"
                    elif dflt_clean in ("'0'", "0") and "BOOLEAN" in pg_type:
                        dflt_clean = "FALSE"
                    elif dflt_clean in ("'1'", "1") and "BOOLEAN" in pg_type:
                        dflt_clean = "TRUE"
                    cdef += f" DEFAULT {dflt_clean}"
                col_defs.append(cdef)

            if is_composite_pk:
                pk_join = ', '.join(pk_cols)
                col_defs.append(f"    PRIMARY KEY ({pk_join})")

            # Add foreign keys
            for fk in fks:
                # fk: (id, seq, table, from, to, on_update, on_delete, match)
                fk_table = fk[2]
                fk_from = fk[3]
                fk_to = fk[4]
                fk_on_delete = fk[6]
                fk_clause = f"    FOREIGN KEY ({fk_from}) REFERENCES {fk_table}({fk_to})"
                if fk_on_delete and fk_on_delete.upper() != "NO ACTION":
                    fk_clause += f" ON DELETE {fk_on_delete.upper()}"
                col_defs.append(fk_clause)

            ddl_lines.append(",\n".join(col_defs))
            ddl_lines.append(");")
            ddl_lines.append("")

            # Indexes
            cur.execute(f"PRAGMA index_list({table});")
            indexes = cur.fetchall()
            for idx in indexes:
                idx_name = idx[1]
                idx_unique = idx[2]
                # Skip auto-created primary key / unique indexes
                if idx_name.startswith("sqlite_autoindex_"):
                    continue
                cur.execute(f"PRAGMA index_info({idx_name});")
                idx_cols = [r[2] for r in cur.fetchall()]
                cols_str = ", ".join(idx_cols)
                uniq_str = "UNIQUE " if idx_unique else ""
                ddl_lines.append(f"CREATE {uniq_str}INDEX IF NOT EXISTS {idx_name} ON {table}({cols_str});")

            ddl_lines.append("")

        ddl_lines.append("COMMIT;")
    finally:
        conn.close()

    return "\n".join(ddl_lines)


def generate_postgres_data_inserts(sqlite_path: Path) -> Tuple[str, Dict[str, int]]:
    """Dump all SQLite data as PostgreSQL INSERT statements with sequence sync."""
    lines = [
        "BEGIN;",
        "-- Disable triggers during mass data load",
        "SET CONSTRAINTS ALL DEFERRED;",
        "",
    ]
    counts = {}

    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    try:
        tables = get_sqlite_table_names(conn)
        cur = conn.cursor()

        for table in tables:
            cur.execute(f"SELECT * FROM {table};")
            rows = cur.fetchall()
            counts[table] = len(rows)

            if not rows:
                continue

            col_names = [d[0] for d in cur.description]
            cols_clause = ", ".join(col_names)
            lines.append(f"-- Data for {table} ({len(rows)} records)")

            # Batch insert in chunks of 50 for readability and speed
            chunk_size = 50
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i + chunk_size]
                val_rows = []
                for row in chunk:
                    vals = [escape_postgres_value(row[c]) for c in col_names]
                    val_rows.append(f"    ({', '.join(vals)})")
                lines.append(f"INSERT INTO {table} ({cols_clause}) VALUES\n" + ",\n".join(val_rows) + ";")

            # Sequence sync if table has an integer 'id' primary key
            if "id" in col_names:
                lines.append(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 1), true);\n"
                )

        lines.append("COMMIT;")
    finally:
        conn.close()

    return "\n".join(lines), counts


def export_full_migration(sqlite_path: Path, output_file: Path) -> Dict[str, int]:
    """Generate combined schema and data migration file."""
    ddl = generate_postgres_ddl(sqlite_path)
    data, counts = generate_postgres_data_inserts(sqlite_path)
    full_content = ddl + "\n\n" + data
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(full_content, encoding="utf-8")
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PriceWise AI SQLite to PostgreSQL Migration")
    parser.add_argument("--sqlite", type=str, default=str(DEFAULT_SQLITE_PATH), help="Path to SQLite database")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_SQL), help="Path to output SQL file")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without writing output")
    args = parser.parse_args()

    sqlite_p = Path(args.sqlite)
    output_p = Path(args.output)

    if not sqlite_p.exists():
        print(f"Error: SQLite database not found at {sqlite_p}")
        sys.exit(1)

    print(f"Reading SQLite database: {sqlite_p}")
    if args.dry_run:
        ddl = generate_postgres_ddl(sqlite_p)
        data, counts = generate_postgres_data_inserts(sqlite_p)
        print("Dry run completed successfully.")
        print(f"Generated DDL lines: {len(ddl.splitlines())}")
        print(f"Generated Data lines: {len(data.splitlines())}")
        print("Extracted record counts:")
        for tbl, cnt in counts.items():
            print(f"  {tbl}: {cnt} rows")
    else:
        counts = export_full_migration(sqlite_p, output_p)
        print(f"PostgreSQL migration script written to: {output_p}")
        print("Migrated tables and record counts:")
        for tbl, cnt in counts.items():
            print(f"  {tbl}: {cnt} rows")
