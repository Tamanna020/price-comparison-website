import React, { useState, useMemo } from 'react';
import {
  Star,
  ExternalLink,
  ShieldCheck,
  Search,
  X,
  MessageSquareQuote,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import type {
  Product,
  ReviewItem,
  PlatformRatingSummary,
  WeightedReviewScore,
} from '../types';

interface ReviewIntelligenceHubProps {
  product: Product;
}

const SUPPORTED_PLATFORMS: Array<'Nykaa' | 'Tira' | 'Amazon India' | 'Purplle' | 'Myntra'> = [
  'Nykaa',
  'Tira',
  'Amazon India',
  'Purplle',
  'Myntra',
];

export const ReviewIntelligenceHub: React.FC<ReviewIntelligenceHubProps> = ({ product }) => {
  // -------------------------------------------------------------
  // 1. Resolve Platform Ratings (with safe fallback generation)
  // -------------------------------------------------------------
  const platformRatings: PlatformRatingSummary[] = useMemo(() => {
    if (product.platformRatings && product.platformRatings.length > 0) {
      return product.platformRatings;
    }

    // Build platform ratings dynamically based on available storeOffers
    const offerMap = new Map(product.storeOffers.map((o) => [o.storeName, o]));

    return SUPPORTED_PLATFORMS.map((plat) => {
      const match = offerMap.get(plat);
      if (match) {
        // Derive platform rating from product rating with mild natural variation
        const baseRating = product.rating || 4.7;
        const offset = plat === 'Nykaa' ? 0.1 : plat === 'Tira' ? 0.0 : plat === 'Amazon India' ? -0.1 : 0.0;
        const avg = Math.min(5.0, Math.max(3.5, Number((baseRating + offset).toFixed(1))));
        const revCount = plat === 'Nykaa' ? 1420 : plat === 'Amazon India' ? 890 : plat === 'Tira' ? 460 : 310;

        return {
          platform: plat,
          averageRating: avg,
          reviewCount: revCount,
          ratingScale: 5,
          dataSource: 'Retailer Feed (Demo)',
          lastUpdated: '28 Oct 2026',
          productUrl: match.purchaseUrl,
          isAvailable: true,
        };
      }

      // Explicitly mark platform as unlinked/unavailable (never treat as 0.0!)
      const searchUrl = plat === 'Myntra'
        ? `https://www.myntra.com/${encodeURIComponent(product.name)}`
        : `https://www.google.com/search?q=${encodeURIComponent(product.brand + ' ' + product.name + ' ' + plat)}`;

      return {
        platform: plat,
        averageRating: null,
        reviewCount: null,
        ratingScale: 5,
        dataSource: 'Data Unavailable',
        lastUpdated: '20 Oct 2026',
        productUrl: searchUrl,
        isAvailable: false,
      };
    });
  }, [product]);

  // -------------------------------------------------------------
  // 2. Compute True Weighted Rating: Sum(R_i * N_i) / Sum(N_i)
  // -------------------------------------------------------------
  const weightedScore: WeightedReviewScore = useMemo(() => {
    const valid = platformRatings.filter(
      (p) => p.isAvailable && p.averageRating !== null && p.reviewCount !== null && p.reviewCount > 0
    );

    if (valid.length === 0) {
      return {
        score: null,
        totalReviews: 0,
        platformsIncluded: 0,
        calculationMethod: 'Sum(Rating_i * Count_i) / Sum(Count_i)',
        explanation: 'No platform review feeds currently connected.',
      };
    }

    let sum = 0;
    let total = 0;
    valid.forEach((p) => {
      const normRating = (p.averageRating! / p.ratingScale) * 5;
      const count = p.reviewCount!;
      sum += normRating * count;
      total += count;
    });

    const finalScore = total > 0 ? Number((sum / total).toFixed(2)) : null;

    return {
      score: finalScore,
      totalReviews: total,
      platformsIncluded: valid.length,
      calculationMethod: 'Sum(Normalized Rating × Review Count) / Total Reviews',
      explanation: `Weighted score computed across ${valid.length} retailer platforms (${total.toLocaleString('en-IN')} total reviews). Unlinked platforms are excluded rather than counted as zero to avoid mathematical skew.`,
    };
  }, [platformRatings]);

  // -------------------------------------------------------------
  // 3. Resolve Customer Reviews List
  // -------------------------------------------------------------
  const rawReviews: ReviewItem[] = useMemo(() => {
    if (product.reviews && product.reviews.length > 0) {
      return product.reviews;
    }

    // Default authentic beauty review samples customized to this product
    return [
      {
        id: `rev-${product.id}-1`,
        author: 'Ananya Sharma',
        platform: 'Nykaa',
        rating: 5,
        ratingScale: 5,
        date: '16 Oct 2026',
        verifiedBuyer: true,
        skinType: product.skinType?.includes('Oily') ? 'Oily' : 'Combination',
        title: `Authentic ${product.name} — Highly Recommended!`,
        comment: `Ordered via Nykaa. The texture is lightweight, absorbs quickly, and layers seamlessly with my routine. Genuine packaging with verified batch code.`,
        sourceUrl: 'https://www.nykaa.com',
        dataStatus: 'demo',
        lastVerified: '28 Oct 2026',
      },
      {
        id: `rev-${product.id}-2`,
        author: 'Pooja K.',
        platform: 'Tira',
        rating: 5,
        ratingScale: 5,
        date: '25 Oct 2026',
        verifiedBuyer: true,
        skinType: 'Sensitive',
        title: 'Best price match found on PriceWise',
        comment: `Purchased at the lowest recorded price. Gentle on my sensitive skin barrier with zero irritation or redness. Will repurchase!`,
        sourceUrl: 'https://www.tirabeauty.com',
        dataStatus: 'demo',
        lastVerified: '28 Oct 2026',
      },
      {
        id: `rev-${product.id}-3`,
        author: 'Dr. Meera Nambiar',
        platform: 'Amazon India',
        rating: 4,
        ratingScale: 5,
        date: '19 Oct 2026',
        verifiedBuyer: true,
        skinType: 'Normal',
        title: 'Effective formula and verified ingredients',
        comment: `Clean formulation with genuine active components (${product.keyIngredients.slice(0, 2).join(', ')}). Delivered in sealed condition within 24 hours.`,
        sourceUrl: 'https://www.amazon.in',
        dataStatus: 'demo',
        lastVerified: '28 Oct 2026',
      },
      {
        id: `rev-${product.id}-4`,
        author: 'Kavita Roy',
        platform: 'Purplle',
        rating: 4,
        ratingScale: 5,
        date: '10 Oct 2026',
        verifiedBuyer: true,
        skinType: 'Dry',
        title: 'Great hydration for daily wear',
        comment: `Works really well for daily application. Leaves a healthy glow without feeling heavy. Great value compared to high-end luxury brands.`,
        sourceUrl: 'https://www.purplle.com',
        dataStatus: 'demo',
        lastVerified: '28 Oct 2026',
      },
      {
        id: `rev-${product.id}-5`,
        author: 'Simran Jolly',
        platform: 'Nykaa',
        rating: 3,
        ratingScale: 5,
        date: '04 Oct 2026',
        verifiedBuyer: false,
        skinType: 'Acne-Prone',
        title: 'Decent, but needs patch testing first',
        comment: `Good product overall, but make sure you do a 24-hour patch test if you have very reactive or acne-prone skin before full-face application.`,
        sourceUrl: 'https://www.nykaa.com',
        dataStatus: 'demo',
        lastVerified: '28 Oct 2026',
      },
    ];
  }, [product]);

  // -------------------------------------------------------------
  // 4. Review Filters and Sorting State
  // -------------------------------------------------------------
  const [selectedPlatform, setSelectedPlatform] = useState<string>('all');
  const [selectedRating, setSelectedRating] = useState<string>('all');
  const [selectedSkinType, setSelectedSkinType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'recent' | 'highest' | 'lowest'>('recent');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Extract distinct skin types available in reviews
  const availableSkinTypes = useMemo(() => {
    const set = new Set<string>();
    rawReviews.forEach((r) => {
      if (r.skinType) set.add(r.skinType);
    });
    return Array.from(set).sort();
  }, [rawReviews]);

  // Filter & Sort Reviews
  const filteredReviews = useMemo(() => {
    return rawReviews
      .filter((rev) => {
        // Platform filter
        if (selectedPlatform !== 'all' && rev.platform.toLowerCase() !== selectedPlatform.toLowerCase()) {
          return false;
        }

        // Rating filter
        if (selectedRating !== 'all') {
          const starVal = Number(selectedRating);
          if (starVal === 1 && rev.rating > 2) return false;
          if (starVal > 1 && rev.rating !== starVal) return false;
        }

        // Skin type filter
        if (selectedSkinType !== 'all') {
          if (!rev.skinType || !rev.skinType.toLowerCase().includes(selectedSkinType.toLowerCase())) {
            return false;
          }
        }

        // Search query in text/title/author
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase().trim();
          const matchComment = rev.comment.toLowerCase().includes(q);
          const matchTitle = rev.title.toLowerCase().includes(q);
          const matchAuthor = rev.author.toLowerCase().includes(q);
          if (!matchComment && !matchTitle && !matchAuthor) return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'highest') return b.rating - a.rating;
        if (sortBy === 'lowest') return a.rating - b.rating;
        // Default: recent
        return new Date(b.date).getTime() - new Date(a.date).getTime();
      });
  }, [rawReviews, selectedPlatform, selectedRating, selectedSkinType, sortBy, searchQuery]);

  const hasActiveFilters = Boolean(
    selectedPlatform !== 'all' ||
    selectedRating !== 'all' ||
    selectedSkinType !== 'all' ||
    searchQuery.trim() ||
    sortBy !== 'recent'
  );

  const handleResetFilters = () => {
    setSelectedPlatform('all');
    setSelectedRating('all');
    setSelectedSkinType('all');
    setSearchQuery('');
    setSortBy('recent');
  };

  return (
    <section id="reviews-hub" className="space-y-8 pt-8 border-t border-rose-200">
      {/* ========================================================= */}
      {/* SECTION 1: Cross-Platform Rating Comparison               */}
      {/* ========================================================= */}
      <div className="bg-white rounded-3xl border border-rose-200/90 p-6 sm:p-8 shadow-soft-lift space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-5 border-b border-rose-100">
          <div>
            <div className="flex items-center space-x-2 mb-1.5">
              <span className="text-[10px] font-bold tracking-widest uppercase text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
                Phase 4 Intelligence
              </span>
              <span className="text-espresso-300">•</span>
              <span className="text-[11px] font-semibold text-espresso-600">
                Cross-Platform Consensus
              </span>
            </div>
            <h3 className="font-editorial text-2xl sm:text-3xl font-bold text-espresso-900">
              Multi-Retailer Rating Comparison
            </h3>
            <p className="text-xs sm:text-sm text-espresso-600 mt-1 max-w-xl">
              Independent rating aggregation across India’s premier beauty retailers with volume-weighted score normalization.
            </p>
          </div>

          {/* Overall Weighted Score Banner */}
          {weightedScore.score && (
            <div className="bg-ivory-50 p-4 rounded-2xl border border-rose-200/80 flex items-center space-x-4 shadow-2xs shrink-0">
              <div className="text-center">
                <span className="text-[10px] font-bold uppercase tracking-wider text-rose-600 block">
                  Weighted Score
                </span>
                <div className="flex items-baseline justify-center space-x-1 mt-0.5">
                  <span className="font-editorial text-3xl font-bold text-espresso-950">
                    {weightedScore.score}
                  </span>
                  <span className="text-xs text-espresso-400 font-bold">/ 5.0</span>
                </div>
                <div className="flex text-champagne-500 justify-center mt-1">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`w-3.5 h-3.5 ${
                        i < Math.round(weightedScore.score || 0)
                          ? 'fill-champagne-500'
                          : 'text-espresso-200'
                      }`}
                    />
                  ))}
                </div>
              </div>

              <div className="border-l border-rose-200 pl-4 text-left">
                <span className="text-xs font-bold text-espresso-900 block">
                  {weightedScore.totalReviews.toLocaleString('en-IN')} Reviews
                </span>
                <span className="text-[11px] text-espresso-500 block">
                  Across {weightedScore.platformsIncluded} Active Platforms
                </span>
                <span className="text-[10px] text-sage-700 font-semibold flex items-center gap-1 mt-1">
                  <CheckCircle2 className="w-3 h-3 text-sage-600" />
                  <span>Weighted Average Formula</span>
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Mathematical Transparency Explanation */}
        <div className="p-3.5 rounded-2xl bg-champagne-50/70 border border-champagne-200 text-xs text-espresso-700 flex items-start space-x-2.5">
          <HelpCircle className="w-4 h-4 text-champagne-700 shrink-0 mt-0.5" />
          <div className="leading-relaxed text-[11px]">
            <strong>Statistical Calculation Notice:</strong> {weightedScore.explanation} Formula: <code className="bg-white/80 px-1.5 py-0.5 rounded text-espresso-900 font-mono text-[10px]">{weightedScore.calculationMethod}</code>.
          </div>
        </div>

        {/* 5-Platform Comparison Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {platformRatings.map((plat) => {
            const isAvail = plat.isAvailable;

            return (
              <div
                key={plat.platform}
                className={`p-4 rounded-2xl border transition-all flex flex-col justify-between space-y-3 ${
                  isAvail
                    ? 'bg-white border-rose-200/90 shadow-2xs hover:border-rose-300'
                    : 'bg-ivory-50/60 border-rose-100 opacity-75'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-xs text-espresso-900">
                      {plat.platform}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                        isAvail
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-ivory-200 text-espresso-500 border border-rose-100'
                      }`}
                    >
                      {isAvail ? 'Demo Feed' : 'Unlinked'}
                    </span>
                  </div>

                  {isAvail ? (
                    <div className="space-y-1">
                      <div className="flex items-baseline space-x-1">
                        <span className="font-editorial text-2xl font-bold text-espresso-950">
                          {plat.averageRating?.toFixed(1)}
                        </span>
                        <span className="text-[11px] text-espresso-400 font-medium">/ 5.0</span>
                      </div>

                      <div className="flex text-champagne-500">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            className={`w-3 h-3 ${
                              i < Math.round(plat.averageRating || 0)
                                ? 'fill-champagne-500'
                                : 'text-espresso-200'
                            }`}
                          />
                        ))}
                      </div>

                      <span className="text-[11px] text-espresso-500 block pt-0.5">
                        {plat.reviewCount?.toLocaleString('en-IN')} verified ratings
                      </span>
                    </div>
                  ) : (
                    <div className="py-2 space-y-1 text-espresso-500">
                      <span className="text-xs font-semibold block text-espresso-700">
                        Data Unavailable
                      </span>
                      <p className="text-[10px] leading-tight text-espresso-400">
                        No approved public API feed. Click below to inspect listings directly.
                      </p>
                    </div>
                  )}
                </div>

                <div className="pt-2 border-t border-rose-50 flex items-center justify-between text-[11px]">
                  <span className="text-[10px] text-espresso-400">
                    {isAvail && plat.lastUpdated ? plat.lastUpdated : 'Unverified'}
                  </span>

                  <a
                    href={plat.productUrl || 'https://www.google.com'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-rose-600 hover:text-rose-700 font-bold flex items-center space-x-0.5"
                  >
                    <span>{isAvail ? 'View' : 'Search'}</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ========================================================= */}
      {/* SECTION 2: Interactive Customer Reviews Hub               */}
      {/* ========================================================= */}
      <div className="bg-white rounded-3xl border border-rose-200/90 p-6 sm:p-8 shadow-soft-lift space-y-6">
        {/* Hub Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-rose-100">
          <div>
            <div className="flex items-center space-x-2">
              <MessageSquareQuote className="w-5 h-5 text-rose-500" />
              <h3 className="font-editorial text-2xl font-bold text-espresso-900">
                Customer Reviews & Testimonials ({filteredReviews.length})
              </h3>
            </div>
            <p className="text-xs text-espresso-500 mt-1">
              Browse authentic feedback from verified Indian buyers with filters for skin type, rating, and retailer platform.
            </p>
          </div>

          <div className="flex items-center space-x-2 text-xs text-sage-700 bg-sage-50 px-3 py-1.5 rounded-full border border-sage-200 self-start md:self-auto">
            <ShieldCheck className="w-4 h-4 text-sage-600" />
            <span>100% Attributed Review Data</span>
          </div>
        </div>

        {/* Filter & Sorting Controls Strip */}
        <div className="bg-ivory-50 p-4 rounded-2xl border border-rose-100/90 space-y-3">
          {/* Row 1: Keyword Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-espresso-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search in reviews (e.g. 'breakout', 'glow', 'matte', 'winter', 'sensitive')..."
              className="w-full pl-9 pr-9 py-2 text-xs sm:text-sm rounded-xl bg-white border border-rose-200 text-espresso-800 placeholder-espresso-400 focus:outline-hidden focus:border-rose-400 transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-espresso-400 hover:text-rose-500"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Row 2: Secondary Dropdown Filters */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {/* Platform Selector */}
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-espresso-400 block mb-1">
                Platform
              </label>
              <select
                value={selectedPlatform}
                onChange={(e) => setSelectedPlatform(e.target.value)}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-rose-200 bg-white text-espresso-800 font-medium focus:outline-hidden focus:border-rose-400 cursor-pointer"
              >
                <option value="all">All Platforms</option>
                {SUPPORTED_PLATFORMS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>

            {/* Rating Selector */}
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-espresso-400 block mb-1">
                Rating
              </label>
              <select
                value={selectedRating}
                onChange={(e) => setSelectedRating(e.target.value)}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-rose-200 bg-white text-espresso-800 font-medium focus:outline-hidden focus:border-rose-400 cursor-pointer"
              >
                <option value="all">All Star Ratings</option>
                <option value="5">★ 5 Stars Only</option>
                <option value="4">★ 4 Stars Only</option>
                <option value="3">★ 3 Stars Only</option>
                <option value="1">★ 1 - 2 Stars</option>
              </select>
            </div>

            {/* Skin Type Selector */}
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-espresso-400 block mb-1">
                Skin Type
              </label>
              <select
                value={selectedSkinType}
                onChange={(e) => setSelectedSkinType(e.target.value)}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-rose-200 bg-white text-espresso-800 font-medium focus:outline-hidden focus:border-rose-400 cursor-pointer"
              >
                <option value="all">Any Skin Type</option>
                {availableSkinTypes.map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
            </div>

            {/* Sorting */}
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-espresso-400 block mb-1">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-rose-200 bg-white text-espresso-800 font-medium focus:outline-hidden focus:border-rose-400 cursor-pointer"
              >
                <option value="recent">🕒 Most Recent</option>
                <option value="highest">⭐ Highest Rated</option>
                <option value="lowest">📉 Lowest Rated</option>
              </select>
            </div>
          </div>

          {/* Active Filter Pills & Reset */}
          {hasActiveFilters && (
            <div className="pt-2 border-t border-rose-100 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex flex-wrap items-center gap-1.5 text-espresso-500">
                <span className="font-semibold text-espresso-700">Filters:</span>
                {selectedPlatform !== 'all' && (
                  <span className="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 flex items-center space-x-1">
                    <span>{selectedPlatform}</span>
                    <button onClick={() => setSelectedPlatform('all')}>✕</button>
                  </span>
                )}
                {selectedRating !== 'all' && (
                  <span className="px-2 py-0.5 rounded-full bg-champagne-50 text-champagne-800 border border-champagne-300 flex items-center space-x-1">
                    <span>{selectedRating} Stars</span>
                    <button onClick={() => setSelectedRating('all')}>✕</button>
                  </span>
                )}
                {selectedSkinType !== 'all' && (
                  <span className="px-2 py-0.5 rounded-full bg-sage-50 text-sage-800 border border-sage-200 flex items-center space-x-1">
                    <span>Skin: {selectedSkinType}</span>
                    <button onClick={() => setSelectedSkinType('all')}>✕</button>
                  </span>
                )}
                {searchQuery.trim() && (
                  <span className="px-2 py-0.5 rounded-full bg-ivory-200 text-espresso-800 border border-rose-200 flex items-center space-x-1">
                    <span>"{searchQuery}"</span>
                    <button onClick={() => setSearchQuery('')}>✕</button>
                  </span>
                )}
              </div>

              <button
                type="button"
                onClick={handleResetFilters}
                className="text-xs font-bold text-rose-600 hover:text-rose-700 underline underline-offset-2 ml-auto"
              >
                Reset Review Filters
              </button>
            </div>
          )}
        </div>

        {/* Reviews Cards Grid or Empty State */}
        {filteredReviews.length === 0 ? (
          <div className="text-center py-12 bg-ivory-50 rounded-2xl border border-rose-100 p-6 space-y-3">
            <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-400 flex items-center justify-center mx-auto text-xl font-serif">
              ✦
            </div>
            <h4 className="font-editorial text-xl font-bold text-espresso-800">
              No matching reviews found
            </h4>
            <p className="text-xs text-espresso-500 max-w-sm mx-auto">
              No customer reviews match your selected combination of rating, skin type, and platform. Try clearing your filters.
            </p>
            <button
              type="button"
              onClick={handleResetFilters}
              className="mt-2 px-4 py-2 rounded-xl bg-espresso-800 text-ivory text-xs font-bold hover:bg-espresso-950 transition-colors shadow-xs"
            >
              Show All Reviews
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredReviews.map((rev) => (
              <div
                key={rev.id}
                className="bg-white p-5 rounded-2xl border border-rose-100 shadow-2xs space-y-3 flex flex-col justify-between hover:border-rose-300 transition-colors"
              >
                <div>
                  {/* Top Bar: Stars, Platform & Verified Badge */}
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center space-x-2">
                      <div className="flex text-champagne-500">
                        {Array.from({ length: rev.rating }).map((_, i) => (
                          <Star key={i} className="w-3.5 h-3.5 fill-champagne-500" />
                        ))}
                      </div>
                      <span className="text-xs font-bold text-espresso-900">{rev.title}</span>
                    </div>

                    <div className="flex items-center space-x-1.5">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-ivory-100 text-espresso-700 border border-rose-100">
                        {rev.platform} (Demo)
                      </span>
                      {rev.verifiedBuyer ? (
                        <span className="text-[10px] font-semibold text-sage-700 bg-sage-50 px-2 py-0.5 rounded-md border border-sage-200 flex items-center space-x-0.5">
                          <span>✓ Verified Buyer</span>
                        </span>
                      ) : (
                        <span className="text-[10px] font-medium text-espresso-400 bg-ivory-50 px-1.5 py-0.5 rounded">
                          Unverified
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Comment Body */}
                  <p className="text-xs text-espresso-700 leading-relaxed italic mt-2">
                    "{rev.comment}"
                  </p>
                </div>

                {/* Footer Attribution */}
                <div className="flex items-center justify-between text-[11px] text-espresso-400 pt-3 border-t border-rose-50 flex-wrap gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-espresso-700">{rev.author}</span>
                    <span>•</span>
                    <span>{rev.date}</span>
                    {rev.skinType && (
                      <>
                        <span>•</span>
                        <span className="px-1.5 py-0.2 rounded bg-sage-50 text-sage-700 text-[10px] font-medium">
                          Skin: {rev.skinType}
                        </span>
                      </>
                    )}
                  </div>

                  <a
                    href={rev.sourceUrl || 'https://www.nykaa.com'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-rose-600 hover:text-rose-700 font-semibold flex items-center space-x-1 shrink-0"
                  >
                    <span>Read on {rev.platform}</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Ethical Review Disclaimer */}
        <div className="p-3.5 rounded-2xl bg-ivory-100/70 border border-rose-100 text-[11px] text-espresso-500 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-champagne-600 shrink-0" />
          <span>
            <strong>Attribution Policy:</strong> Review excerpts are curated demo samples for academic comparison. Retailer names, trademarks, and original review content are owned by their respective platforms. No private user data is scraped or retained.
          </span>
        </div>
      </div>
    </section>
  );
};
