"""
Test PostgreSQL 18.6 compatibility safely using transaction ROLLBACK.
Verifies DDL parsing, constraints, sequences, and JSON types without persisting any changes.
Database remains 100% empty after this test.
"""
import os
import sys
from pathlib import Path
import psycopg

BASE_DIR = Path(__file__).resolve().parent.parent

def test_compatibility():
    env_local = BASE_DIR / ".env.local"
    if not env_local.exists():
        print("ERROR: .env.local not found")
        sys.exit(1)

    with open(env_local, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'").strip('"')

    direct_url = os.environ.get("DATABASE_URL_UNPOOLED")
    sql_file = BASE_DIR / "data" / "postgres_migration.sql"

    print("=" * 60)
    print("POSTGRESQL 18.6 SYNTAX & DDL COMPATIBILITY CHECK (ROLLBACK MODE)")
    print("=" * 60)
    print(f"Reading migration SQL: {sql_file.name} ({sql_file.stat().st_size} bytes)")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    # We will test in a transaction and explicitly ROLLBACK
    print("Connecting to Neon Staging Direct endpoint...")
    with psycopg.connect(direct_url, connect_timeout=15) as conn:
        print("Starting transaction...")
        with conn.cursor() as cur:
            try:
                # Execute full migration script inside transaction
                print("Executing full migration SQL inside uncommitted transaction...")
                cur.execute(sql)
                print("  [PASS] Full DDL, constraints, sequences, and data compiled successfully in PG 18.6!")

                # Verify table count inside transaction
                cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
                tbl_count = cur.fetchone()[0]
                print(f"  [PASS] Tables visible inside transaction: {tbl_count}")

            finally:
                # Explicit rollback guarantees clean slate
                print("Rolling back transaction to preserve empty database...")
                conn.rollback()
                print("  [PASS] Transaction rolled back cleanly.")

        # Confirm post-rollback emptiness
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
            clean_count = cur.fetchone()[0]
            print(f"Post-rollback table count in public schema: {clean_count}")
            assert clean_count == 0, "Error: database was not left clean!"
            print("  [CONFIRMED] Staging database remains 100% EMPTY.")

    print("=" * 60)
    print("POSTGRESQL 18.6 COMPATIBILITY TEST RESULT: SUCCESS")
    print("=" * 60)

if __name__ == "__main__":
    test_compatibility()
