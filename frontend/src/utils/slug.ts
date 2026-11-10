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

import { PRODUCTS_DATA } from '../data/products';

/**
 * Safely resolves a product ID (e.g. "prod-01", "prod-23", slug, or numeric ID) 
 * into its explicit verified PostgreSQL database ID (dbId).
 * Guaranteed to NEVER resolve to legacy electronics records (IDs 1-11).
 * Default fallback is 12 (Dot & Key Sunscreen, first verified beauty product).
 */
export const toNumericProductId = (id: string | number | undefined | null, fallback = 12): number => {
  if (id == null) return fallback;
  if (typeof id === 'number') {
    if (!isNaN(id) && id >= 12) return id;
    const foundByNum = PRODUCTS_DATA.find((p) => p.dbId === id);
    if (foundByNum && foundByNum.dbId && foundByNum.dbId >= 12) return foundByNum.dbId;
    return fallback;
  }

  const idStr = id.toString().trim();

  // 1. Direct integer check for valid beauty database IDs (>= 12)
  const parsedDirect = parseInt(idStr, 10);
  if (!isNaN(parsedDirect) && idStr === parsedDirect.toString() && parsedDirect >= 12) {
    return parsedDirect;
  }

  // 2. Direct lookup by exact id or slug in catalog
  const product = PRODUCTS_DATA.find(
    (p) => p.id.toLowerCase() === idStr.toLowerCase() || (p.slug && p.slug.toLowerCase() === idStr.toLowerCase())
  );
  if (product && product.dbId && product.dbId >= 12) {
    return product.dbId;
  }

  // 3. Normalized ID lookup (e.g. "prod-1" -> "prod-01")
  const numPart = idStr.replace(/^prod-?/i, '');
  const parsedNum = parseInt(numPart, 10);
  if (!isNaN(parsedNum)) {
    const formattedId = `prod-${parsedNum < 10 ? '0' + parsedNum : parsedNum}`;
    const match = PRODUCTS_DATA.find((p) => p.id === formattedId);
    if (match && match.dbId && match.dbId >= 12) {
      return match.dbId;
    }
  }

  return fallback;
};

/**
 * Normalizes a product ID into standard frontend string format (e.g. "prod-01").
 */
export const toFrontendProductId = (id: string | number | undefined | null): string => {
  if (typeof id === 'string' && id.startsWith('prod-')) return id;
  const num = toNumericProductId(id);
  const found = PRODUCTS_DATA.find((p) => p.dbId === num);
  if (found) return found.id;
  return `prod-${num < 10 ? '0' + num : num}`;
};


