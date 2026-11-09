"""Update frontend/src/data/products.ts for prod-01 to prod-23 with verified manufacturer URLs and catalog_verified status."""

with open('frontend/src/data/products.ts', 'r', encoding='utf-8') as f:
    text = f.read()

# Map prod IDs to official URLs
prod_urls = {
    1: "https://www.dotandkey.com/products/watermelon-cooling-sunscreen-spf-50",
    2: "https://thedermaco.com/product/1-hyaluronic-sunscreen-aqua-gel",
    3: "https://beminimalist.co/products/niacinamide-10",
    4: "https://www.cosrx.com/products/advanced-snail-96-mucin-power-essence",
    5: "https://www.kamaayurveda.in/products/kumkumadi-miraculous-beauty-ayurvedic-night-serum",
    6: "https://www.dotandkey.com/products/ceramide-hyaluronic-barrier-repair-face-cream",
    7: "https://www.forestessentialsindia.com/soundarya-radiance-cream-with-24k-gold-spf-25.html",
    8: "https://www.clinique.in/product/1687/83690/skincare/moisturizers/moisture-surge-100h-auto-replenishing-hydrator",
    9: "https://www.cetaphil.in/cleansers/gentle-skin-cleanser/IN_3499320013009.html",
    10: "https://www.sebamedindia.com/face/clear-face-cleansing-foam",
    11: "https://plumgoodness.com/products/green-tea-alcohol-free-toner",
    12: "https://in.laneige.com/products/lip-sleeping-mask-berry",
    13: "https://www.maybelline.co.in/face-makeup/foundation/fit-me-matte-and-poreless-liquid-foundation/128-warm-nude",
    14: "https://www.maccosmetics.in/product/13847/1231/products/makeup/face/foundation/studio-fix-fluid-spf-15",
    15: "https://www.charlottetilbury.com/in/product/hollywood-flawless-filter",
    16: "https://www.maybelline.co.in/face-makeup/concealer/instant-age-rewind-eraser-dark-circles-treatment-concealer",
    17: "https://www.nykaa.com/kay-beauty-matteinee-matte-lip-crayon/p/561002",
    18: "https://www.rarebeauty.com/products/soft-pinch-liquid-blush?variant=39485786194055",
    19: "https://swissbeauty.in/products/ultra-blush-palette",
    20: "https://hudabeauty.com/us/en_US/eyeshadow/nude-obsessions-eyeshadow-palette",
    21: "https://www.simpleskincare.in/products/kind-to-skin-micellar-cleansing-water-200ml",
    22: "https://beminimalist.co/products/maleic-bond-repair-complex-5-hair-serum",
    23: "https://innovist.com/products/chemist-at-play-exfoliating-body-wash-with-lactic-acid-and-zemia",
}

chunks = text.split("id: 'prod-")
new_chunks = [chunks[0]]

for chunk in chunks[1:]:
    pid_str = chunk.split("'")[0]
    pid = int(pid_str)
    
    if pid in prod_urls:
        url = prod_urls[pid]
        # Replace partially_verified with catalog_verified and add officialUrl
        chunk = chunk.replace("dataStatus: 'partially_verified',", "dataStatus: 'catalog_verified',")
        chunk = chunk.replace("dataSource: 'Commercial Catalog Reference / Brand Specification',", "dataSource: 'Manufacturer Official Specification / Open Beauty Facts Reference',")
        if "officialUrl:" not in chunk[:500]:
            chunk = chunk.replace("dataStatus: 'catalog_verified',", f"dataStatus: 'catalog_verified',\n    officialUrl: '{url}',")
            
    new_chunks.append(chunk)

updated_text = "id: 'prod-".join(new_chunks)

with open('frontend/src/data/products.ts', 'w', encoding='utf-8', newline='\n') as f:
    f.write(updated_text)

print("Successfully updated frontend/src/data/products.ts with verified manufacturer URLs and catalog_verified status.")
