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

/**
 * Safely parses a product ID (e.g. "prod-1", "prod-01", "1", 1) into a clean integer for backend APIs.
 * Returns a fallback (default 1) if unparseable.
 */
export const toNumericProductId = (id: string | number | undefined | null, fallback = 1): number => {
  if (id == null) return fallback;
  if (typeof id === 'number') return isNaN(id) ? fallback : id;
  const cleaned = id.toString().replace(/^prod-?/i, '').trim();
  const parsed = parseInt(cleaned, 10);
  return isNaN(parsed) ? fallback : parsed;
};

/**
 * Normalizes a product ID into standard frontend string format (e.g. "prod-1").
 */
export const toFrontendProductId = (id: string | number | undefined | null): string => {
  if (typeof id === 'string' && id.startsWith('prod-')) return id;
  const num = toNumericProductId(id);
  return `prod-${num}`;
};


