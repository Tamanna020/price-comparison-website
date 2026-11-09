with open('frontend/src/pages/ProductDetailPage.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Add Info to lucide-react import
old_import = """  CheckCircle2,
  Star,"""
new_import = """  CheckCircle2,
  Info,
  Star,"""
assert old_import in text, "old_import not found"
text = text.replace(old_import, new_import)

# Update banner
old_banner = """              {product.dataSource && (
                <div className="flex items-center space-x-2 text-xs text-emerald-800 bg-emerald-50/90 border border-emerald-200/90 px-3 py-1.5 rounded-xl">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>
                    <strong className="font-semibold">Verified Product Specification:</strong> {product.dataSource}
                  </span>
                </div>
              )}"""

new_banner = """              {product.dataSource ? (
                <div className={`flex items-center space-x-2 text-xs px-3 py-1.5 rounded-xl border ${
                  product.dataStatus === 'catalog_verified'
                    ? 'text-emerald-800 bg-emerald-50/90 border-emerald-200/90'
                    : 'text-amber-800 bg-amber-50/90 border-amber-200/90'
                }`}>
                  <CheckCircle2 className={`w-3.5 h-3.5 shrink-0 ${
                    product.dataStatus === 'catalog_verified' ? 'text-emerald-600' : 'text-amber-600'
                  }`} />
                  <span>
                    <strong className="font-semibold">
                      {product.dataStatus === 'catalog_verified'
                        ? 'Verified Product Specification:'
                        : 'Partially Verified Specifications:'}
                    </strong>{' '}
                    {product.dataSource}
                  </span>
                </div>
              ) : (
                <div className="flex items-center space-x-2 text-xs text-espresso-700 bg-espresso-50/80 border border-espresso-200 px-3 py-1.5 rounded-xl">
                  <Info className="w-3.5 h-3.5 text-espresso-500 shrink-0" />
                  <span>
                    <strong className="font-semibold">Product Information Available:</strong> Commercial catalog listing. Packaging filing reference pending verification.
                  </span>
                </div>
              )}"""

assert old_banner in text, "old_banner not found"
text = text.replace(old_banner, new_banner)

with open('frontend/src/pages/ProductDetailPage.tsx', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("ProductDetailPage.tsx updated successfully.")
