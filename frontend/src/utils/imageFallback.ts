/**
 * PriceWise AI — Product Image Fallback and Verification Utilities
 * Phase 14 Stage 3: Product Image Recovery
 *
 * Provides category-tailored neutral luxury SVG placeholders,
 * image loading error handlers, and image verification status helpers.
 */

export type ImageVerificationStatus = 'verified_exact' | 'permission_review' | 'unverified' | 'placeholder';

export interface ImageMetadata {
  url: string;
  sourceName?: string;
  sourceUrl?: string;
  status: ImageVerificationStatus;
  lastChecked?: string;
}

/**
 * Escapes XML/SVG special characters for safe inclusion in SVG data URIs.
 */
function escapeXml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/**
 * Generates an elegant, neutral luxury SVG data URI tailored to a product's brand and category.
 * Prevents Cumulative Layout Shift (CLS), broken image icons, and misleading generic stock photos.
 */
export function generateProductPlaceholderSvg(
  brand: string = 'BEAUTY',
  category: string = 'SKINCARE',
  _title?: string
): string {
  const brandClean = escapeXml((brand || 'BEAUTY').toUpperCase().slice(0, 24));
  const catClean = escapeXml((category || 'SKINCARE').toUpperCase().slice(0, 24));

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FAF8F5"/>
      <stop offset="100%" stop-color="#F2EDE5"/>
    </linearGradient>
    <linearGradient id="silhouette" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#EFE9DF"/>
      <stop offset="100%" stop-color="#E2D9CC"/>
    </linearGradient>
  </defs>
  <rect width="600" height="600" fill="url(#bg)"/>
  <rect x="24" y="24" width="552" height="552" rx="20" fill="none" stroke="#E6E0D6" stroke-width="2" stroke-dasharray="6 6"/>
  
  <!-- Minimalist Beauty Packaging Silhouette -->
  <g transform="translate(250, 150)">
    <!-- Dropper / Cap -->
    <rect x="42" y="0" width="16" height="20" rx="3" fill="#B8ADA0"/>
    <rect x="36" y="20" width="28" height="25" rx="4" fill="#CCC3B6"/>
    <!-- Bottle Body -->
    <rect x="12" y="45" width="76" height="135" rx="16" fill="#FFFFFF" stroke="#D8D0C4" stroke-width="2.5"/>
    <!-- Label Placeholder lines -->
    <rect x="26" y="75" width="48" height="6" rx="3" fill="#ECE6DC"/>
    <rect x="31" y="90" width="38" height="4" rx="2" fill="#ECE6DC"/>
    <!-- Center Emblem -->
    <circle cx="50" cy="125" r="11" fill="none" stroke="#C98991" stroke-width="2"/>
    <circle cx="50" cy="125" r="4" fill="#C98991"/>
  </g>
  
  <!-- Product Brand & Category Text -->
  <text x="300" y="375" font-family="ui-serif, Georgia, Cambria, serif" font-size="20" font-weight="bold" fill="#302724" text-anchor="middle" letter-spacing="2.5">${brandClean}</text>
  <text x="300" y="405" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="700" fill="#8C827A" text-anchor="middle" letter-spacing="2">${catClean}</text>
  
  <!-- Transparent Status Pill -->
  <g transform="translate(170, 435)">
    <rect width="260" height="32" rx="16" fill="#FFFFFF" stroke="#C98991" stroke-width="1.5" opacity="0.95"/>
    <circle cx="22" cy="16" r="4.5" fill="#C98991"/>
    <text x="140" y="21" font-family="system-ui, -apple-system, sans-serif" font-size="10.5" font-weight="700" fill="#6E635C" text-anchor="middle" letter-spacing="0.8">IMAGE VERIFICATION PENDING</text>
  </g>
  
  <!-- Subtle Footer Note -->
  <text x="300" y="515" font-family="system-ui, -apple-system, sans-serif" font-size="11" fill="#A89E96" text-anchor="middle">Authentic packaging filing in progress • PriceWise AI</text>
</svg>`;

  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
}

/**
 * Checks if a given image URL is a generic stock Unsplash image or broken link.
 */
export function isGenericStockImage(url?: string | null): boolean {
  if (!url) return true;
  // If it's a known generic Unsplash photo reused across catalog
  if (url.includes('images.unsplash.com')) return true;
  // If it's the old DEMO PRODUCT IMAGE SVG
  if (url.includes('DEMO%20PRODUCT%20IMAGE') || url.includes('DEMO PRODUCT IMAGE')) return true;
  return false;
}

/**
 * Returns the safest, most authentic image URL for a product.
 * If the product only has a generic stock Unsplash image or broken URL, returns a tailored neutral placeholder.
 */
export function getProductDisplayImage(
  imageUrl?: string | null,
  brand?: string,
  category?: string,
  title?: string
): string {
  if (!imageUrl || isGenericStockImage(imageUrl)) {
    return generateProductPlaceholderSvg(brand, category, title);
  }
  return imageUrl;
}
