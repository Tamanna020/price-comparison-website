with open('frontend/src/pages/ProductDetailPage.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

target = """              {/* Price Box */}"""
replacement = """              {product.dataSource && (
                <div className="flex items-center space-x-2 text-xs text-emerald-800 bg-emerald-50/90 border border-emerald-200/90 px-3 py-1.5 rounded-xl">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>
                    <strong className="font-semibold">Verified Product Specification:</strong> {product.dataSource}
                  </span>
                </div>
              )}

              {/* Price Box */}"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open('frontend/src/pages/ProductDetailPage.tsx', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(text)
    print("SUCCESS: Added Verified Product Specification badge to ProductDetailPage.tsx")
else:
    print("FAILED: Target not found")
