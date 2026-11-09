import sqlite3
import json

def test_database_integrity():
    print("=== PriceWise AI: Database Integrity & Table Statistics ===")
    conn = sqlite3.connect("data/pricewise.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. PRAGMA integrity_check
    cur.execute("PRAGMA integrity_check;")
    integrity = cur.fetchall()
    print(f"PRAGMA integrity_check: {[dict(r) for r in integrity]}")
    assert len(integrity) == 1 and integrity[0][0] == "ok", "Database integrity check failed!"
    print("  ✓ SQLite PRAGMA integrity_check: OK")

    # 2. PRAGMA foreign_key_check
    cur.execute("PRAGMA foreign_key_check;")
    fk_violations = cur.fetchall()
    if fk_violations:
        print(f"  ⚠ Foreign key violations found: {len(fk_violations)}")
        for v in fk_violations:
            print("    ", dict(v))
    else:
        print("  ✓ SQLite PRAGMA foreign_key_check: 0 violations")

    # 3. Table counts
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [r[0] for r in cur.fetchall()]
    print(f"\nTotal Tables: {len(tables)}")
    
    table_counts = {}
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cur.fetchone()[0]
        table_counts[t] = cnt
        print(f"  - {t:<30}: {cnt:>5} rows")

    # Verify critical tables exist and have data
    assert table_counts.get("products", 0) >= 34, "Products table missing or incomplete"
    assert table_counts.get("offers", 0) >= 97, "Offers table missing or incomplete"
    assert table_counts.get("price_history", 0) >= 900, "Price history table missing or incomplete"
    assert table_counts.get("users", 0) >= 1, "Users table missing or empty"

    conn.close()
    print("\n✓ Database integrity verified successfully!")
    return table_counts

if __name__ == "__main__":
    test_database_integrity()

