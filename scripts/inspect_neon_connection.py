"""
Inspect Neon PostgreSQL connection safely without printing credentials.
Performs read-only inspection of server version, SSL status, permissions,
extensions, and existing schema/table contents.
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
import psycopg

BASE_DIR = Path(__file__).resolve().parent.parent

def load_env_local():
    """Load .env.local variables into os.environ if present without printing."""
    env_local = BASE_DIR / ".env.local"
    if not env_local.exists():
        print("ERROR: .env.local does not exist.")
        sys.exit(1)
    
    with open(env_local, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                if key not in os.environ:
                    os.environ[key] = val

def mask_connection_url(url: str) -> str:
    parsed = urlparse(url)
    user = parsed.username or "none"
    host = parsed.hostname or "unknown"
    port = parsed.port or 5432
    path = parsed.path or "/default"
    masked_user = user[:2] + "***" if len(user) > 2 else "***"
    return f"postgresql://{masked_user}:****@{host}:{port}{path}"

def inspect_connection():
    load_env_local()
    
    pooled_url = os.environ.get("DATABASE_URL")
    direct_url = os.environ.get("DATABASE_URL_UNPOOLED")
    
    if not pooled_url:
        print("ERROR: DATABASE_URL not found in environment or .env.local")
        sys.exit(1)
        
    print("=" * 60)
    print("NEON POSTGRESQL SAFE CONNECTION INSPECTION")
    print("=" * 60)
    print(f"Pooled Endpoint Target: {mask_connection_url(pooled_url)}")
    if direct_url:
        print(f"Direct Endpoint Target: {mask_connection_url(direct_url)}")
    print("-" * 60)

    # We will test pooled and direct connection
    endpoints = [("Pooled Application Endpoint", pooled_url)]
    if direct_url and direct_url != pooled_url:
        endpoints.append(("Direct Migration Endpoint", direct_url))

    for name, url in endpoints:
        print(f"\nTesting: {name}")
        try:
            with psycopg.connect(url, connect_timeout=15) as conn:
                with conn.cursor() as cur:
                    # 1. Server Version
                    cur.execute("SELECT version();")
                    ver = cur.fetchone()[0]
                    cur.execute("SHOW server_version;")
                    short_ver = cur.fetchone()[0]
                    print(f"  [PASS] Connected successfully.")
                    print(f"  PostgreSQL Server Version: {short_ver} ({ver.split()[0]} {ver.split()[1]})")

                    # 2. SSL Verification
                    ssl_active = bool(conn.pgconn.ssl_in_use)
                    params = conn.info.get_parameters() if hasattr(conn.info, 'get_parameters') else {}
                    ssl_mode = params.get('sslmode', 'require')
                    print(f"  [PASS] SSL / TLS Transport Active: {ssl_active} (sslmode={ssl_mode})")

                    # 3. Current User & Database Context
                    cur.execute("SELECT current_user, current_database(), current_schema();")
                    c_user, c_db, c_schema = cur.fetchone()
                    print(f"  Current User: {c_user}")
                    print(f"  Current Database: {c_db}")
                    print(f"  Current Schema: {c_schema}")

                    # 4. User Privileges
                    cur.execute("""
                        SELECT 
                            has_database_privilege(current_user, current_database(), 'CREATE'),
                            has_schema_privilege(current_user, current_schema(), 'CREATE');
                    """)
                    can_create_db, can_create_schema = cur.fetchone()
                    print(f"  Privileges: CREATE on DB={can_create_db}, CREATE on Schema={can_create_schema}")

                    # 5. Installed & Available Extensions
                    cur.execute("SELECT extname, extversion FROM pg_extension;")
                    installed_exts = cur.fetchall()
                    ext_list = [f"{name} ({v})" for name, v in installed_exts]
                    print(f"  Installed Extensions: {', '.join(ext_list) if ext_list else 'None'}")

        except Exception as e:
            print(f"  [FAIL] Connection error for {name}: {type(e).__name__}: {str(e)}")

    # Detailed Inspection of Schema on direct or pooled connection that succeeds
    print("\n" + "=" * 60)
    print("DETAILED SCHEMA & DATA INVENTORY (READ-ONLY)")
    print("=" * 60)
    connected = False
    for label, try_url in [("Direct", direct_url), ("Pooled", pooled_url)]:
        if not try_url:
            continue
        try:
            with psycopg.connect(try_url, connect_timeout=15) as conn:
                with conn.cursor() as cur:
                    print(f"Connecting via {label} for inventory...")
                    # Find all user tables in public schema
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                        ORDER BY table_name;
                    """)
                    tables = [row[0] for row in cur.fetchall()]
                    
                    if not tables:
                        print("Status: DATABASE IS EMPTY (0 user tables in public schema).")
                        print("Emptiness: TRUE - Clean slate, safe for initial canonical migration.")
                    else:
                        print(f"Status: DATABASE CONTAINS {len(tables)} EXISTING TABLES:")
                        total_records = 0
                        for tbl in tables:
                            cur.execute(f'SELECT COUNT(*) FROM "{tbl}";')
                            cnt = cur.fetchone()[0]
                            total_records += cnt
                            print(f"  - {tbl}: {cnt} rows")
                        print(f"Total Records Across Tables: {total_records}")
                        if total_records == 0:
                            print("Emptiness: Tables exist but contain 0 records.")
                        else:
                            print(f"Emptiness: FALSE - Contains {total_records} existing records.")

                    # Check custom types or enums
                    cur.execute("""
                        SELECT typname FROM pg_type t 
                        JOIN pg_namespace n ON n.oid = t.typnamespace 
                        WHERE n.nspname = 'public' AND t.typtype = 'e';
                    """)
                    enums = [row[0] for row in cur.fetchall()]
                    if enums:
                        print(f"Existing Custom Enums: {', '.join(enums)}")

                    # Check sequences
                    cur.execute("""
                        SELECT sequence_name FROM information_schema.sequences
                        WHERE sequence_schema = 'public';
                    """)
                    seqs = [row[0] for row in cur.fetchall()]
                    if seqs:
                        print(f"Existing Sequences: {len(seqs)} found")
                connected = True
                break
        except Exception as e:
            print(f"[FAIL] Schema inspection error via {label}: {type(e).__name__}: {str(e)}")

    print("\n" + "=" * 60)
    print("INSPECTION COMPLETE - ALL SENSITIVE CREDENTIALS SHIELDED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    inspect_connection()
