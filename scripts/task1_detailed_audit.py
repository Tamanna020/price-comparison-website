import sqlite3
import json

conn = sqlite3.connect('data/pricewise.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, sku, title, brand, category, specs_json FROM products")
products = cur.fetchall()

print("=" * 80)
print("PHASE 11C DATA AUDIT: EXISTING DATABASE STATE")
print("=" * 80)
print(f"Total Products: {len(products)}")

electronic_count = 0
beauty_count = 0
test_count = 0

for p in products:
    cat = (p['category'] or '').lower()
    pid = p['id']
    if pid in (998, 999):
        test_count += 1
    elif cat in ('laptops', 'smartphones', 'audio', 'gaming', 'wearables', 'monitors', 'cameras', 'tvs'):
        electronic_count += 1
    else:
        beauty_count += 1

print(f"  Legacy Electronics (Phases 1-5): {electronic_count}")
print(f"  Core Beauty Products (Phases 6-11B): {beauty_count}")
print(f"  Test Fixture Products: {test_count}")

cur.execute("SELECT COUNT(*) FROM offers")
print(f"\nTotal Offers: {cur.fetchone()[0]}")

cur.execute("SELECT s.name, COUNT(o.id) FROM stores s LEFT JOIN offers o ON s.id = o.store_id GROUP BY s.name")
for r in cur.fetchall():
    print(f"  Store: {r[0]:25} Offers: {r[1]}")

cur.execute("SELECT data_status, data_source, COUNT(*) FROM price_history GROUP BY data_status, data_source")
print("\nPrice History Partitioning:")
for r in cur.fetchall():
    print(f"  Status: {str(r[0]):20} Source: {str(r[1]):20} Records: {r[2]}")

cur.execute("SELECT COUNT(*) FROM evidence_references")
print(f"\nTotal Evidence References: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM manual_verification_requests")
print(f"Total Manual Verification Requests: {cur.fetchone()[0]}")
