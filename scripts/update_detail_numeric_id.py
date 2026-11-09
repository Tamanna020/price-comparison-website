with open('frontend/src/pages/ProductDetailPage.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

target = "const numericProductId = toNumericProductId(product.id);"
replacement = "const numericProductId = product.dbId || toNumericProductId(product.id);"

if target in text:
    text = text.replace(target, replacement, 1)
    with open('frontend/src/pages/ProductDetailPage.tsx', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(text)
    print("SUCCESS: Updated numericProductId in ProductDetailPage.tsx")
else:
    print("FAILED: Target not found")
