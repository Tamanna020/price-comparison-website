import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  RotateCcw,
  AlertTriangle,
  Info,
  Tag,
  ExternalLink,
  Search,
  ShieldCheck,
  Minus,
  Plus,
  HelpCircle,
} from 'lucide-react';
import type { AlternativeProduct, AlternativeFinderResponse } from '../utils/api';
import { findProductAlternatives } from '../utils/api';
import { PRODUCTS_DATA } from '../data/products';

interface AlternativesSectionProps {
  productId: number;
  productName: string;
  brand: string;
  price: number;
  originalPrice?: number;
  image: string;
  quantity: string;
  category: string;
  subcategory: string;
}

export const AlternativesSection: React.FC<AlternativesSectionProps> = ({
  productId,
  productName,
  brand,
  price,
  originalPrice,
  image,
  quantity,
  category,
  subcategory,
}) => {
  const [result, setResult] = useState<AlternativeFinderResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<'ai' | 'heuristic' | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [filters, setFilters] = useState({
    maxPriceRatio: 0.8,
    minSimilarity: 0.6,
  });

  const fetchAlternatives = async () => {
    setLoading(true);
    setError(null);
    const res = await findProductAlternatives(productId, {
      max_price_ratio: filters.maxPriceRatio,
      min_similarity: filters.minSimilarity,
    });
    if (res.success && res.data) {
      setResult(res.data);
      setSource(res.data.extraction_source === 'gemini_model' ? 'ai' : 'heuristic');
    } else {
      setError(res.error || 'Failed to find alternatives');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchAlternatives();
  }, [productId, filters.maxPriceRatio, filters.minSimilarity]);

  const displayedAlternatives = showAll
    ? result?.alternatives || []
    : (result?.alternatives || []).slice(0, 3);

  if (!result && !loading && !error) return null;

  const isAI = source === 'ai';
  const savingsCount = result?.alternatives.filter(
    (a) => a.price_difference && a.price_difference > 0
  ).length || 0;

  return (
    <section className="bg-white rounded-3xl border border-rose-200/90 p-6 sm:p-8 shadow-soft-lift space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-rose-100">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="text-[10px] font-bold tracking-widest uppercase text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
              Smart Dupe Finder
            </span>
            <span className="text-espresso-300">•</span>
            <span className="text-[11px] font-semibold text-espresso-600">
              {category.toUpperCase()} • {subcategory}
            </span>
          </div>
          <h3 className="font-editorial text-2xl sm:text-3xl font-bold text-espresso-900">
            Cheaper Alternatives & Formula Matches
          </h3>
        </div>

        {/* Source Badge & Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold">
            {isAI ? (
              <>
                <Sparkles className="w-3.5 h-3.5 text-rose-500" />
                <span className="text-rose-700 border-rose-200 bg-rose-50">AI Powered</span>
              </>
            ) : (
              <>
                <Search className="w-3.5 h-3.5 text-champagne-600" />
                <span className="text-champagne-800 border-champagne-300 bg-champagne-50">Heuristic Match</span>
              </>
            )}
          </div>
          <button
            onClick={fetchAlternatives}
            disabled={loading}
            className="px-3 py-1.5 rounded-xl border border-rose-200 bg-white hover:bg-rose-50/70 text-espresso-700 text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-2xs disabled:opacity-50"
            title="Re-search alternatives"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-rose-600' : ''}`} />
            <span>{loading ? 'Searching...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && !result && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-sm text-rose-700 flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading State */}
      {loading && !result && (
        <div className="space-y-3 animate-pulse">
          <div className="h-8 bg-rose-100 rounded-xl w-3/4" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-rose-50 rounded-2xl border border-rose-100" />
            ))}
          </div>
        </div>
      )}

      {result && (
        <>
          {/* Summary Banner */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-sage-50/70 to-rose-50/70 border border-sage-200 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs sm:text-sm">
            <div className="flex items-center space-x-3 text-espresso-800">
              <Sparkles className="w-5 h-5 text-rose-500 shrink-0" />
              <span>
                Found <strong>{result.alternatives.length}</strong> potential alternatives for{" "}
                <strong>{productName}</strong> ({brand})
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {savingsCount > 0 && (
                <span className="font-bold text-rose-700 bg-white/80 px-2.5 py-1 rounded-full border border-rose-200 text-[11px]">
                  {savingsCount} cheaper option{savingsCount !== 1 ? 's' : ''} found
                </span>
              )}
              <div className="px-2.5 py-1 rounded-full bg-ivory-100 text-espresso-600 border border-rose-100 text-[10px] font-bold">
                Max Price: ≤{Math.round(filters.maxPriceRatio * 100)}% of original
              </div>
              <div className="px-2.5 py-1 rounded-full bg-ivory-100 text-espresso-600 border border-rose-100 text-[10px] font-bold">
                Min Similarity: ≥{Math.round(filters.minSimilarity * 100)}%
              </div>
            </div>
          </div>

          {/* Filter Controls */}
          <div className="p-4 rounded-2xl bg-ivory-50 border border-rose-100 space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-espresso-700">
              <span>Search Filters</span>
              <HelpCircle className="w-4 h-4 text-espresso-400" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-espresso-400 mb-1">
                  Maximum Price Ratio
                </label>
                <select
                  value={filters.maxPriceRatio}
                  onChange={(e) => setFilters({ ...filters, maxPriceRatio: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-white border border-rose-200 rounded-xl text-xs text-espresso-800 focus:outline-hidden focus:border-rose-400"
                >
                  <option value={0.5}>50% (Half Price)</option>
                  <option value={0.6}>60%</option>
                  <option value={0.7}>70%</option>
                  <option value={0.8}>80% (Default)</option>
                  <option value={0.9}>90%</option>
                  <option value={1.0}>100% (Same Price)</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-espresso-400 mb-1">
                  Minimum Similarity Score
                </label>
                <select
                  value={filters.minSimilarity}
                  onChange={(e) => setFilters({ ...filters, minSimilarity: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-white border border-rose-200 rounded-xl text-xs text-espresso-800 focus:outline-hidden focus:border-rose-400"
                >
                  <option value={0.4}>40% (Broad Match)</option>
                  <option value={0.5}>50%</option>
                  <option value={0.6}>60% (Default)</option>
                  <option value={0.7}>70%</option>
                  <option value={0.8}>80% (Strict)</option>
                  <option value={0.9}>90% (Very Strict)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Original Product Reference Card */}
          <div className="p-4 rounded-2xl bg-white border border-rose-100 space-y-2">
            <div className="flex items-center space-x-2 text-xs font-bold text-espresso-900 uppercase tracking-wider">
              <Tag className="w-4 h-4 text-rose-500 shrink-0" />
              <span>Reference Product</span>
            </div>
            <div className="flex items-center space-x-4">
              <img
                src={image}
                alt={productName}
                className="w-16 h-16 rounded-xl object-cover border border-rose-200 shrink-0"
              />
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-espresso-900 truncate">{productName}</p>
                <p className="text-xs text-espresso-500">{brand}</p>
                <p className="text-xs text-espresso-400">{quantity}</p>
                <div className="flex items-baseline space-x-2 mt-1">
                  <span className="text-base font-extrabold font-sans text-espresso-950">
                    ₹{price.toLocaleString('en-IN')}
                  </span>
                  {originalPrice && originalPrice > price && (
                    <span className="text-xs font-sans text-espresso-400 line-through">
                      ₹{originalPrice.toLocaleString('en-IN')}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Alternatives Grid */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-editorial text-lg font-bold text-espresso-900">
                Alternative Products ({result.alternatives.length} found)
              </h4>
              {result.alternatives.length > 3 && (
                <button
                  onClick={() => setShowAll(!showAll)}
                  className="px-3 py-1.5 rounded-xl bg-white border border-rose-200 text-espresso-700 text-xs font-semibold flex items-center space-x-1.5 transition-all hover:bg-rose-50"
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>{showAll ? 'Show Less' : `Show All ${result.alternatives.length}`}</span>
                </button>
              )}
            </div>

            {result.alternatives.length === 0 ? (
              <div className="p-8 text-center bg-white/60 border border-rose-100 rounded-3xl text-espresso-600 text-sm space-y-2">
                <Search className="w-8 h-8 text-rose-400 mx-auto opacity-60" />
                <p className="font-semibold text-espresso-800">No alternatives found</p>
                <p className="text-xs text-espresso-500">
                  Try lowering the similarity threshold or increasing the max price ratio.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {displayedAlternatives.map((alt, idx) => (
                  <AlternativeCard
                    key={alt.alternative_product_id}
                    alt={alt}
                    index={idx}
                    referencePrice={price}
                  />
                ))}
              </div>
            )}

            {/* Price Verification Notice */}
            <div className="mt-6 pt-4 border-t border-rose-100">
              <div className="p-3.5 rounded-2xl bg-white border border-rose-100 text-[11px] text-espresso-600 flex items-start space-x-2">
                <Info className="w-4 h-4 text-sage-600 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-espresso-800">Price Verification:</strong>{' '}
                  <span className="text-rose-600 font-medium">✅ Verified</span> = Both prices from live retailer feeds.
                  <span className="text-amber-600 font-medium ml-2">⚠️ Unverified</span> = At least one price from demo/cached data.
                  Never assume products are identical solely based on shared ingredients.
                  Concentration, formulation, pH, and supporting ingredients critically affect performance.
                </div>
              </div>
            </div>

            {/* Data Attribution */}
            <div className="pt-4 border-t border-rose-100">
              <div className="p-3.5 rounded-2xl bg-white border border-rose-100 text-[11px] text-espresso-600 flex items-start space-x-2">
                <Info className="w-4 h-4 text-sage-600 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-espresso-800">Methodology:</strong>{' '}
                  {isAI
                    ? 'Gemini AI analyzes ingredient lists, formulation types, product categories, and price evidence to identify structurally similar alternatives. '
                    : 'Heuristic matching compares key ingredients, product type, category, and price using existing catalog data. '}
                  Similarity score reflects ingredient overlap and formulation alignment, not clinical equivalence.
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
};

// Alternative Card Component
interface AlternativeCardProps {
  alt: AlternativeProduct;
  index: number;
  referencePrice: number;
}

const AlternativeCard: React.FC<AlternativeCardProps> = ({ alt, index, referencePrice }) => {
  const isCheaper = alt.price_difference && alt.price_difference > 0;
  const isVerified = alt.price_verified;

  // Find product image from PRODUCTS_DATA
  const altProduct = PRODUCTS_DATA.find((p) => String(p.id) === String(alt.alternative_product_id));
  const image = altProduct?.image || 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=800&q=80';

  const similarityColor =
    alt.similarity_score >= 0.85
      ? 'bg-sage-100 text-sage-800 border-sage-300'
      : alt.similarity_score >= 0.7
      ? 'bg-champagne-100 text-champagne-800 border-champagne-300'
      : 'bg-amber-100 text-amber-800 border-amber-300';

  return (
    <div className="relative p-4 rounded-2xl border border-rose-100 bg-white shadow-2xs hover:shadow-soft-lift transition-all space-y-3">
      {/* Badge: Cheaper / Verified */}
      <div className="flex flex-wrap items-center gap-1.5">
        {isCheaper && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500 text-ivory flex items-center space-x-1">
            <Minus className="w-2.5 h-2.5" />
            <span>Save ₹{alt.price_difference?.toLocaleString('en-IN')} ({alt.price_difference_pct}%)</span>
          </span>
        )}
        {!isCheaper && alt.price_difference && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center space-x-1">
            <Plus className="w-2.5 h-2.5" />
            <span>₹{Math.abs(alt.price_difference).toLocaleString('en-IN')} more</span>
          </span>
        )}
        {isVerified && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sage-100 text-sage-800 border border-sage-300 flex items-center space-x-1">
            <ShieldCheck className="w-2.5 h-2.5" />
            <span>Price Verified</span>
          </span>
        )}
        {!isVerified && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center space-x-1">
            <AlertTriangle className="w-2.5 h-2.5" />
            <span>Price Unverified</span>
          </span>
        )}
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${similarityColor}`}>
          {Math.round(alt.similarity_score * 100)}% Similar
        </span>
      </div>

      {/* Product Info */}
      <div className="flex items-start space-x-3.5">
        <img
          src={image}
          alt={alt.alternative_product_name}
          className="w-20 h-20 rounded-xl object-cover border border-rose-200 shrink-0"
        />
        <div className="flex-1 min-w-0 space-y-1.5">
          <div className="flex items-center justify-between">
            <h4 className="font-editorial text-base font-bold text-espresso-900 truncate pr-2">
              {alt.alternative_product_name}
            </h4>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 uppercase tracking-wider">
              #{index + 1}
            </span>
          </div>
          <p className="text-xs text-espresso-500">{alt.alternative_brand}</p>
          <p className="text-[11px] text-espresso-400 italic">{alt.explanation}</p>

          {/* Matched Attributes */}
          {alt.matched_attributes && alt.matched_attributes.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {alt.matched_attributes.map((attr, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 rounded bg-sage-50 text-sage-700 text-[10px] border border-sage-100"
                >
                  ✓ {attr}
                </span>
              ))}
            </div>
          )}

          {/* Key Differences */}
          {alt.differences && alt.differences.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {alt.differences.map((diff, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 text-[10px] border border-rose-100"
                >
                  ≠ {diff}
                </span>
              ))}
            </div>
          )}

          {/* Price & Suitability */}
          <div className="pt-2 border-t border-rose-100 flex items-center justify-between">
            <div className="flex items-baseline space-x-2">
              <span className="text-base font-extrabold font-sans text-espresso-950">
                ₹{alt.alternative_price?.toLocaleString('en-IN')}
              </span>
              {alt.alternative_price && referencePrice > alt.alternative_price && (
                <span className="text-[10px] font-bold text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                  {Math.round(((referencePrice - alt.alternative_price!) / referencePrice) * 100)}% less
                </span>
              )}
            </div>
            <div className="text-right">
              <p className="text-[10px] font-semibold text-espresso-700">
                Suitability: <span className="text-espresso-900">{Math.round(alt.suitability_score * 100)}%</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* View Product Button */}
      <button
        className="w-full px-4 py-2.5 rounded-xl bg-espresso-800 hover:bg-espresso-950 text-ivory text-xs font-bold tracking-wide transition-colors shadow-xs flex items-center justify-center space-x-1"
      >
        <ExternalLink className="w-3.5 h-3.5" />
        <span>View on PriceWise</span>
      </button>
    </div>
  );
};

export default AlternativesSection;
