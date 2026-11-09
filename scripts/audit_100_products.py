"""Audit all 100 beauty products across SQLite and Frontend.
Inspects:
- Product name / title
- Brand
- Category
- Product size / quantity
- Formulation / productType
- Ingredients (full INCI vs key actives)
- Product description
- Skin concerns
- Manufacturer URL
- Source reference
- Evidence reference
- Data status
"""

import json
import sqlite3
import re

def audit_database():
    conn = sqlite3.connect('data/pricewise.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, sku, title, brand, category, description, specs_json, image_url
        FROM products
        WHERE category NOT IN ('Smartphones', 'Laptops', 'Audio', 'Wearables', 'Gaming', 'Monitors', 'Cameras', 'TVs')
        ORDER BY id
    """)
    rows = cur.fetchall()
    print(f"Total beauty products in SQLite: {len(rows)}")

    db_products = []
    for r in rows:
        specs = json.loads(r['specs_json'] or '{}')
        specs_lower = {k.lower(): v for k, v in specs.items()}
        
        # Check ingredients
        ingredients_field = None
        for k in specs_lower:
            if 'ingredient' in k:
                ingredients_field = specs_lower[k]
                break

        # Check volume
        volume_field = None
        for k in ('volume', 'size', 'net quantity', 'net_quantity'):
            if k in specs_lower:
                volume_field = specs_lower[k]
                break

        # Check source & url
        source_field = specs_lower.get('source')
        evidence_field = specs_lower.get('evidence')
        url_field = specs_lower.get('product url', specs_lower.get('official url'))
        data_status = specs_lower.get('data status', specs_lower.get('data_status', 'demo'))
        concerns = specs_lower.get('skin concerns', specs_lower.get('concerns'))
        formulation = specs_lower.get('product type', specs_lower.get('formulation'))

        db_products.append({
            'db_id': r['id'],
            'title': r['title'],
            'brand': r['brand'],
            'category': r['category'],
            'description': r['description'],
            'volume': volume_field,
            'formulation': formulation,
            'ingredients': ingredients_field,
            'concerns': concerns,
            'source': source_field,
            'evidence': evidence_field,
            'url': url_field,
            'data_status': data_status,
        })
    return db_products

if __name__ == '__main__':
    db_prods = audit_database()
    print(f"Audited {len(db_prods)} database beauty products.")
    
    # Analyze completeness
    missing_ingredients = [p for p in db_prods if not p['ingredients']]
    missing_volume = [p for p in db_prods if not p['volume']]
    missing_source = [p for p in db_prods if not p['source']]
    missing_url = [p for p in db_prods if not p['url']]
    
    print(f"Missing ingredients: {len(missing_ingredients)}")
    print(f"Missing volume: {len(missing_volume)}")
    print(f"Missing source: {len(missing_source)}")
    print(f"Missing URL: {len(missing_url)}")

    # Sample of early products (IDs 1-23)
    early = [p for p in db_prods if p['db_id'] <= 32]
    print(f"Early products count: {len(early)}")
    for p in early[:5]:
        print("Early:", p['db_id'], p['brand'], p['title'], "Source:", p['source'], "URL:", p['url'])
