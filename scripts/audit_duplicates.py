"""Audit catalogue duplicates and inconsistencies."""

import sqlite3
from collections import Counter

conn = sqlite3.connect('data/pricewise.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Product title duplicates
cur.execute("SELECT title, count(*) as c FROM products GROUP BY lower(trim(title)) HAVING c > 1")
dup_titles = cur.fetchall()
print("Duplicate product titles in DB:", [dict(r) for r in dup_titles])

# 2. Brand spelling variations
cur.execute("SELECT DISTINCT brand FROM products")
all_brands = [r['brand'] for r in cur.fetchall()]
print(f"Total distinct brands in DB: {len(all_brands)}")
print("Brands in DB:", sorted(all_brands))

# 3. Duplicate offers for the same product and store
cur.execute("SELECT product_id, store_id, count(*) as c FROM offers GROUP BY product_id, store_id HAVING c > 1")
dup_offers = cur.fetchall()
print(f"Duplicate offers in DB (same product & store): {len(dup_offers)}")
if dup_offers:
    for d in dup_offers:
        print("  Duplicate offer:", dict(d))

# 4. Check frontend brands
with open('frontend/src/data/products.ts', 'r', encoding='utf-8') as f:
    text = f.read()

import re
frontend_brands = set(re.findall(r"brand:\s*'([^']+)'", text))
print(f"Total distinct brands in frontend: {len(frontend_brands)}")
print("Frontend brands:", sorted(frontend_brands))

# Compare brand names
db_brand_set = set(all_brands)
print("\nBrands in frontend but not DB:", sorted(frontend_brands - db_brand_set))
print("Brands in DB but not frontend:", sorted(db_brand_set - frontend_brands))
