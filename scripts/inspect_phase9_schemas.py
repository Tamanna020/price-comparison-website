import sqlite3

def inspect_schemas():
    conn = sqlite3.connect("data/pricewise.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    tables = ["price_history", "price_alerts", "price_tracking", "offers", "evidence_references", "stores"]
    for t in tables:
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,))
        row = cur.fetchone()
        print(f"=== {t} ===")
        print(row["sql"] if row else "NOT FOUND")
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"Count: {cur.fetchone()[0]}")
        print()

    # Check sample price_history
    print("=== SAMPLE PRICE_HISTORY (3 rows) ===")
    cur.execute("SELECT * FROM price_history LIMIT 3")
    for r in cur.fetchall():
        print(dict(r))

    # Check sample price_alerts / price_tracking
    print("\n=== SAMPLE PRICE_TRACKING (3 rows) ===")
    cur.execute("SELECT * FROM price_tracking LIMIT 3")
    for r in cur.fetchall():
        print(dict(r))

    print("\n=== SAMPLE PRICE_ALERTS (3 rows) ===")
    cur.execute("SELECT * FROM price_alerts LIMIT 3")
    for r in cur.fetchall():
        print(dict(r))

    conn.close()

if __name__ == "__main__":
    inspect_schemas()

