with open('frontend/src/components/ProductCard.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

target = """        {/* Top Floating Badges */}
        <div className="absolute top-3 left-3 flex flex-col gap-1 items-start">
          {product.dealTag && ("""

replacement = """        {/* Top Floating Badges */}
        <div className="absolute top-3 left-3 flex flex-col gap-1 items-start">
          {product.dataStatus === 'catalog_verified' && (
            <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs">
              Verified Spec
            </span>
          )}
          {product.dealTag && ("""

if target in text:
    text = text.replace(target, replacement, 1)
    with open('frontend/src/components/ProductCard.tsx', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(text)
    print("SUCCESS: Added Verified Spec badge to ProductCard.tsx")
else:
    print("FAILED: Target not found")
