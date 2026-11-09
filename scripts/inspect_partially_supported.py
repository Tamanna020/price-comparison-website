import sqlite3, json

conn = sqlite3.connect('data/pricewise.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('''
    SELECT id, title, brand, category, specs_json 
    FROM products 
    WHERE id BETWEEN 12 AND 32 AND id NOT IN (21, 23, 24)
    ORDER BY id
''')
rows = cur.fetchall()
print(f"Count of products to review: {len(rows)}")
for r in rows:
    specs = json.loads(r['specs_json'] or '{}')
    print(f"ID {r['id']}: {r['brand']} | {r['title']} | Category: {r['category']}")
    print(f"   Net Quantity: {specs.get('Net Quantity') or specs.get('volume') or specs.get('size')}")
    print(f"   Key Ingredients: {specs.get('Key Ingredients') or specs.get('ingredients')}")
