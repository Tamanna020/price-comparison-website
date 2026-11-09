import sqlite3
import os

db_path = 'data/pricewise.db'
if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}!")
    for root, dirs, files in os.walk('.'):
        for f in files:
            if f.endswith('.db'):
                print(f"Found alternative: {os.path.join(root, f)}")
else:
    print(f"Database found at {db_path} ({os.path.getsize(db_path)} bytes)")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cur.fetchall()]
    print(f"\nTotal tables found: {len(tables)}")
    print("-" * 50)
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM `{t}`;")
            count = cur.fetchone()[0]
            print(f"{t:<35} | {count:>6} records")
        except Exception as e:
            print(f"{t:<35} | ERROR: {e}")
    conn.close()

