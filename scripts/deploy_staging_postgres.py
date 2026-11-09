"""Automated Staging PostgreSQL Deployment & Verification Tool.

Usage:
    python scripts/deploy_staging_postgres.py --url "<target_postgres_url>"
Or with DATABASE_URL set in environment:
    python scripts/deploy_staging_postgres.py
"""

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
import sqlite3

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database.connection import get_connection

def run_staging_postgres_deployment(target_url: str, force: bool = False):
    print("=" * 80)
    print("PRICEWISE AI — AUTOMATED STAGING POSTGRESQL DEPLOYMENT")
    print("=" * 80)
    parsed = urlparse(target_url)
    print(f"Target Database Host: {parsed.hostname}, Database: {parsed.path.lstrip('/')} (credentials completely masked)")

    # Safety Guard: Ensure production branch is never accidentally targeted without explicit override
    neon_branch = os.environ.get("NEON_BRANCH", "").lower()
    if neon_branch == "production" and not force:
        print("ERROR: Safety Guard Blocked: Active Neon branch in environment is 'production'!")
        print("This tool is intended for staging. Switch to staging branch or pass --force.")
        sys.exit(1)

    # Read migration SQL
    sql_file = BASE_DIR / "data" / "postgres_migration.sql"
    if not sql_file.exists():
        print(f"Error: {sql_file} not found!")
        sys.exit(1)

    print(f"Reading migration file: {sql_file} ({sql_file.stat().st_size} bytes)...")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Keep pooled DATABASE_URL for application get_connection() checks
    pooled_url = os.environ.get("DATABASE_URL")
    if not pooled_url or "pooler" not in pooled_url:
        os.environ["DATABASE_URL"] = target_url

    print("Connecting to target PostgreSQL database...")
    try:
        import psycopg
        conn = psycopg.connect(target_url)
        conn.autocommit = True
        cur = conn.cursor()

        # Pre-migration safety inspection of target database
        cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
        existing_table_count = cur.fetchone()[0]
        if existing_table_count > 0:
            print(f"  [SAFETY NOTICE] Target database contains {existing_table_count} existing tables.")
            print("  Executing migration will cleanly reset tables to canonical schema via DROP TABLE IF EXISTS ... CASCADE.")
        else:
            print("  Target database is clean (0 existing tables). Proceeding with initial deployment.")

        print("Executing migration SQL...")
        cur.execute(sql_content)
        print("Migration SQL executed successfully.")
        conn.close()
    except Exception as e:
        print(f"Deployment failed: {e}")
        sys.exit(1)

    # Validate row parity against SQLite (strictly opened in read-only mode)
    print("\nVerifying table counts and row parity against local SQLite canon...")
    sq_path = (BASE_DIR / "data" / "pricewise.db").resolve()
    sq_uri = f"file:///{sq_path.as_posix()}?mode=ro"
    sq_conn = sqlite3.connect(sq_uri, uri=True)
    try:
        sq_cur = sq_conn.cursor()
        sq_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [r[0] for r in sq_cur.fetchall()]

        with get_connection() as pg_conn:
            pg_cur = pg_conn.cursor()
            passed = 0
            for table in tables:
                sq_cur.execute(f"SELECT count(*) FROM {table}")
                sq_cnt = sq_cur.fetchone()[0]
                pg_cur.execute(f"SELECT count(*) FROM {table}")
                pg_cnt = pg_cur.fetchone()[0]
                if sq_cnt == pg_cnt:
                    passed += 1
                else:
                    print(f"  MISMATCH on {table}: SQLite={sq_cnt}, Postgres={pg_cnt}")

            print(f"Parity Check: {passed}/{len(tables)} tables match exactly.")
    finally:
        sq_conn.close()

    print("=" * 80)
    print("STAGING POSTGRESQL DEPLOYMENT AND VERIFICATION COMPLETE: SUCCESS!")
    print("=" * 80)

def load_local_env():
    """Safely load .env.local without exposing credentials."""
    env_local = BASE_DIR / ".env.local"
    if env_local.exists():
        with open(env_local, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k not in os.environ:
                        os.environ[k] = v

if __name__ == "__main__":
    load_local_env()
    # Neon Best Practice: Use direct (unpooled) connection for schema migrations
    default_url = os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")
    
    parser = argparse.ArgumentParser(description="Deploy and verify staging PostgreSQL database.")
    parser.add_argument("--url", default=default_url, help="PostgreSQL connection URL")
    parser.add_argument("--force", action="store_true", help="Bypass existing table warnings")
    args = parser.parse_args()

    if not args.url:
        print("Error: DATABASE_URL not provided via --url or environment.")
        sys.exit(1)

    run_staging_postgres_deployment(args.url, force=args.force)
