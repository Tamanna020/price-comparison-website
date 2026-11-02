import type { Product } from '../types';

/**
 * Generate a URL-friendly, deterministic slug from product brand and title.
 * e.g., "Dot & Key Watermelon Cooling Sunscreen SPF 50+" -> "dot-key-watermelon-cooling-sunscreen-spf-50"
 */
export const generateProductSlug = (product: { name: string; brand?: string; id: string }): string => {
  const brandPart = product.brand ? `${product.brand}-` : '';
  const base = `${brandPart}${product.name}`.toLowerCase();
  const slug = base
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)+/g, '');
  return slug || product.id;
};

/**
 * Resolves a product by slug, ID, or title slug.
 * Returns undefined if no product matches (for clean 404 state handling).
 */
export const findProductBySlugOrId = (products: Product[], slugOrId: string): Product | undefined => {
  if (!slugOrId) return undefined;
  const target = slugOrId.trim().toLowerCase();

  return products.find((p) => {
    // 1. Exact ID match (e.g. "prod-01")
    if (p.id.toLowerCase() === target) return true;

    // 2. Explicit slug match
    if (p.slug && p.slug.toLowerCase() === target) return true;

    // 3. Computed slug match (brand + name)
    const computed = generateProductSlug(p);
    if (computed === target) return true;

    // 4. Name-only slug match (e.g. "watermelon-cooling-sunscreen-spf-50-pa")
    const nameOnly = p.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)+/g, '');
    if (nameOnly === target) return true;

    return false;
  });
};

