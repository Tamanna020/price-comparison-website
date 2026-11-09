import psycopg
from pathlib import Path
import sys

db_url = "postgresql://pricewise:pricewise_staging_pass@127.0.0.1:5433/pricewise_staging"
sql_file = Path("data/postgres_migration.sql")

if not sql_file.exists():
    print(f"Error: {sql_file} not found.")
    sys.exit(1)

print(f"Reading SQL migration script: {sql_file}")
sql_content = sql_file.read_text(encoding="utf-8")

conn = psycopg.connect(db_url, autocommit=True)
cur = conn.cursor()

try:
    print("Executing migration on PostgreSQL 16...")
    cur.execute(sql_content)
    print("MIGRATION EXECUTED SUCCESSFULLY!")
except Exception as e:
    print(f"MIGRATION FAILED: {e}")
finally:
    conn.close()
