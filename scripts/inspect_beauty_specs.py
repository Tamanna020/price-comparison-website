import sqlite3
import json

conn = sqlite3.connect('data/pricewise.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT id, title, brand, category, specs_json FROM products WHERE id >= 12 AND id <= 32 LIMIT 3')
for r in cur.fetchall():
    print(f"ID {r['id']}: {r['title']} [{r['brand']}]")
    specs = json.loads(r['specs_json'])
    for k, v in specs.items():
        print(f"   {k}: {str(v)[:80]}")
    print('---')
