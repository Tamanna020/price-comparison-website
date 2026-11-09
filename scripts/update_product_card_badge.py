with open('frontend/src/components/ProductCard.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

old_badge = """          {product.dataStatus === 'catalog_verified' && (
            <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs">
              Verified Spec
            </span>
          )}"""

new_badge = """          {product.dataStatus === 'catalog_verified' ? (
            <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs" title="Ingredients, net volume, and manufacturer packaging verified">
              Verified Spec
            </span>
          ) : product.dataStatus === 'partially_verified' ? (
            <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-amber-100 text-amber-800 border border-amber-300 shadow-2xs" title="Key specifications partially verified; packaging filing pending">
              Partially Verified Specs
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded-full text-[9px] font-medium bg-white/90 backdrop-blur-xs text-espresso-600 border border-espresso-200 shadow-2xs" title="Commercial product listing available">
              Product Info Available
            </span>
          )}"""

assert old_badge in text, "old_badge not found"
text = text.replace(old_badge, new_badge)

with open('frontend/src/components/ProductCard.tsx', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("ProductCard.tsx badge successfully updated.")
