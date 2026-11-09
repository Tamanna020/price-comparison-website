"""Audit frontend products.ts for field verification."""

with open('frontend/src/data/products.ts', 'r', encoding='utf-8') as f:
    text = f.read()

prod_blocks = text.split("id: 'prod-")
print(f"Total product blocks found: {len(prod_blocks) - 1}")

prods = []
for b in prod_blocks[1:]:
    lines = b.split('\n')
    pid = lines[0].split("'")[0]
    
    # Extract fields
    name = ''
    brand = ''
    category = ''
    quantity = ''
    official_url = ''
    data_source = ''
    data_status = ''
    evidence_type = ''
    
    for l in lines[:40]:
        l_str = l.strip()
        if l_str.startswith("name:"):
            name = l_str.split(":", 1)[1].strip().strip("',")
        elif l_str.startswith("brand:"):
            brand = l_str.split(":", 1)[1].strip().strip("',")
        elif l_str.startswith("category:"):
            category = l_str.split(":", 1)[1].strip().strip("',")
        elif l_str.startswith("quantity:"):
            quantity = l_str.split(":", 1)[1].strip().strip("',")
        elif l_str.startswith("officialUrl:"):
            official_url = l_str.split(":", 1)[1].strip().strip("',")
        elif l_str.startswith("dataSource:"):
            data_source = l_str.split(":", 1)[1].strip().strip("',")
        elif l_str.startswith("dataStatus:"):
            data_status = l_str.split(":", 1)[1].strip().strip("',")
        elif l_str.startswith("evidenceType:"):
            evidence_type = l_str.split(":", 1)[1].strip().strip("',")

    has_ingredients = 'keyIngredients:' in b
    has_how_to_use = 'howToUse:' in b
    has_description = 'description:' in b
    has_store_offers = 'storeOffers:' in b

    prods.append({
        'id': f"prod-{pid}",
        'name': name,
        'brand': brand,
        'category': category,
        'quantity': quantity,
        'has_ingredients': has_ingredients,
        'has_description': has_description,
        'has_how_to_use': has_how_to_use,
        'has_store_offers': has_store_offers,
        'official_url': official_url,
        'data_source': data_source,
        'data_status': data_status,
        'evidence_type': evidence_type,
    })

print(f"Parsed {len(prods)} products from frontend.")

# Summary statistics
with_official_url = [p for p in prods if p['official_url']]
with_data_source = [p for p in prods if p['data_source']]
with_data_status = [p for p in prods if p['data_status']]
missing_ingredients = [p for p in prods if not p['has_ingredients']]

print(f"Products with officialUrl: {len(with_official_url)} / {len(prods)}")
print(f"Products with dataSource: {len(with_data_source)} / {len(prods)}")
print(f"Products with dataStatus: {len(with_data_status)} / {len(prods)}")
print(f"Products missing ingredients in frontend: {len(missing_ingredients)} / {len(prods)}")

print("\nEarly products (prod-01 to prod-23) status:")
for p in prods[:23]:
    print(f"{p['id']}: brand={p['brand']}, name={p['name'][:30]}, url={'YES' if p['official_url'] else 'MISSING'}, status={p['data_status'] or 'UNSET'}")
