with open('frontend/src/types/index.ts', 'r', encoding='utf-8') as f:
    text = f.read()

target = """export interface Product {
  id: string;
  slug?: string; // Canonical URL-friendly slug (e.g. 'watermelon-cooling-sunscreen-spf-50')
  name: string;
  brand: string;
  brandTier: 'Luxury' | 'Premium' | 'Affordable' | 'Drugstore';
  category: ProductCategory;
  subcategory: Subcategory;
  quantity: string; // e.g. "50 ml", "30 ml", "3.8 g" """

target_clean = """export interface Product {
  id: string;
  slug?: string; // Canonical URL-friendly slug (e.g. 'watermelon-cooling-sunscreen-spf-50')
  name: string;
  brand: string;
  brandTier: 'Luxury' | 'Premium' | 'Affordable' | 'Drugstore';
  category: ProductCategory;
  subcategory: Subcategory;
  quantity: string;"""

replacement = """export interface Product {
  id: string;
  dbId?: number; // Corresponding SQLite database product id
  slug?: string; // Canonical URL-friendly slug (e.g. 'watermelon-cooling-sunscreen-spf-50')
  name: string;
  brand: string;
  brandTier: 'Luxury' | 'Premium' | 'Affordable' | 'Drugstore';
  category: ProductCategory;
  subcategory: Subcategory;
  quantity: string;
  dataSource?: string;
  dataStatus?: 'catalog_verified' | 'demo' | 'verified_retailer';
  evidenceType?: string;
  officialUrl?: string;"""

c_norm = text.replace('\r\n', '\n')
t_norm = target_clean.replace('\r\n', '\n')
r_norm = replacement.replace('\r\n', '\n')

if t_norm in c_norm:
    c_norm = c_norm.replace(t_norm, r_norm, 1)
    with open('frontend/src/types/index.ts', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(c_norm.replace('\n', '\r\n'))
    print("SUCCESS: Updated frontend/src/types/index.ts")
else:
    print("FAILED: Target not found")
