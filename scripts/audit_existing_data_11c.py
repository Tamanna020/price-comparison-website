import sqlite3

conn = sqlite3.connect('data/pricewise.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [r[0] for r in cur.fetchall()]
print(f"Total Tables: {len(tables)}")

for t in sorted(tables):
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cur.fetchone()[0]
    print(f"  {t:32}: {cnt} rows")

print("\n--- PRODUCTS SCHEMA & SPECS_JSON INSPECTION ---")
cur.execute("PRAGMA table_info(products);")
cols = [r['name'] for r in cur.fetchall()]
print("Products columns:", cols)

cur.execute("SELECT id, sku, title, brand, category, specs_json FROM products LIMIT 5;")
for r in cur.fetchall():
    print(f"\nProduct ID {r['id']}: {r['title']} ({r['brand']})")
    print(f"  Category: {r['category']}")
    print(f"  Specs JSON snippet: {str(r['specs_json'])[:150]}")

import json

cur.execute("SELECT id, title, brand, category, specs_json FROM products;")
rows = cur.fetchall()

missing_brand = 0
missing_size = 0
missing_ingredients = 0
missing_concerns = 0
missing_desc = 0
duplicate_titles = {}

for r in rows:
    title = (r['title'] or '').strip()
    brand = (r['brand'] or '').strip()
    desc = (r['description'] or '').strip()
    if not brand:
        missing_brand += 1
    if not desc:
        missing_desc += 1
    
    duplicate_titles[title.lower()] = duplicate_titles.get(title.lower(), 0) + 1

    specs = {}
    if r['specs_json']:
        try:
            specs = json.loads(r['specs_json'])
        except Exception:
            pass

    size = specs.get('size_volume') or specs.get('size') or specs.get('volume') or specs.get('net_content')
    if not size:
        missing_size += 1

    ingredients = specs.get('ingredients') or specs.get('key_ingredients') or specs.get('active_ingredients')
    if not ingredients:
        missing_ingredients += 1

    concerns = specs.get('skin_concerns') or specs.get('concerns') or specs.get('target_concerns')
    if not concerns:
        missing_concerns += 1

print("\n--- AUDIT SUMMARY ON 34 PRODUCTS ---")
print(f"Total Products: {len(rows)}")
print(f"Missing Brand: {missing_brand}")
print(f"Missing Description: {missing_desc}")
print(f"Missing Size/Volume in specs_json: {missing_size}")
print(f"Missing Ingredients in specs_json: {missing_ingredients}")
print(f"Missing Skin Concerns in specs_json: {missing_concerns}")

dups = {k: v for k, v in duplicate_titles.items() if v > 1}
print(f"Duplicate Product Titles: {len(dups)} duplicates found ({dups})")


print("\n--- PRODUCT TITLES & BRAND DISTRIBUTION ---")
cur.execute("SELECT brand, COUNT(*) FROM products GROUP BY brand ORDER BY COUNT(*) DESC;")
for r in cur.fetchall():
    print(f"  {r[0]:25}: {r[1]}")

print("\n--- OFFERS AUDIT ---")
cur.execute("""
    SELECT 
        COUNT(*) as total_offers,
        SUM(CASE WHEN offer_url IS NULL OR offer_url = '' THEN 1 ELSE 0 END) as missing_url,
        SUM(CASE WHEN current_price IS NULL OR current_price <= 0 THEN 1 ELSE 0 END) as invalid_price,
        SUM(CASE WHEN original_price IS NULL OR original_price <= 0 THEN 1 ELSE 0 END) as invalid_mrp
    FROM offers
""")
o_stats = dict(cur.fetchone())
for k, v in o_stats.items():
    print(f"  {k:25}: {v}")

print("\n--- REVIEWS & EVIDENCE STATS ---")
cur.execute("SELECT COUNT(*) FROM reviews")
print(f"  Total Reviews: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM evidence_references")
print(f"  Total Evidence References: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM manual_verification_requests")
print(f"  Total Manual Verification Requests: {cur.fetchone()[0]}")
