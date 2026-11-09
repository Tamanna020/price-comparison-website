import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Tag,
  Heart,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  RotateCcw,
  Sun,
  Moon,
  Droplet,
  Flame,
  Cloud,
  Target,
  Sparkle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { matchSkinConcerns } from '../utils/api';
// import type { Product } from '../types';
import { PRODUCTS_DATA } from '../data/products';
import { ProductCard } from '../components/ProductCard';

const SKIN_CONCERNS = [
  { id: 'acne', label: 'Acne & Breakouts', icon: Flame, color: 'bg-rose-100 text-rose-700 border-rose-300', desc: 'Blemishes, blackheads, inflammatory acne' },
  { id: 'dryness', label: 'Dryness & Dehydration', icon: Droplet, color: 'bg-blue-100 text-blue-700 border-blue-300', desc: 'Tightness, flaking, compromised barrier' },
  { id: 'oily', label: 'Oily Skin & Excess Sebum', icon: Cloud, color: 'bg-amber-100 text-amber-700 border-amber-300', desc: 'Shine, enlarged pores, makeup slip' },
  { id: 'combination', label: 'Combination Skin', icon: Target, color: 'bg-purple-100 text-purple-700 border-purple-300', desc: 'Oily T-zone, normal/dry cheeks' },
  { id: 'pigmentation', label: 'Hyperpigmentation & Dark Spots', icon: Sparkle, color: 'bg-orange-100 text-orange-700 border-orange-300', desc: 'Post-acne marks, sun spots, uneven tone' },
  { id: 'sensitivity', label: 'Sensitivity & Redness', icon: Heart, color: 'bg-pink-100 text-pink-700 border-pink-300', desc: 'Reactive, stinging, easily irritated' },
  { id: 'dehydration', label: 'Dehydration', icon: Droplet, color: 'bg-cyan-100 text-cyan-700 border-cyan-300', desc: 'Lack of water (not oil), dull, tight' },
  { id: 'dullness', label: 'Dullness & Lack of Radiance', icon: Sun, color: 'bg-yellow-100 text-yellow-700 border-yellow-300', desc: 'Tired-looking, uneven texture, no glow' },
  { id: 'aging', label: 'Fine Lines & Firmness', icon: Moon, color: 'bg-indigo-100 text-indigo-700 border-indigo-300', desc: 'Loss of elasticity, fine lines, sagging' },
];

const SKIN_TYPES = [
  { id: 'oily', label: 'Oily', desc: 'Excess sebum, shine' },
  { id: 'dry', label: 'Dry', desc: 'Tight, flaky, needs lipids' },
  { id: 'combination', label: 'Combination', desc: 'Oily T-zone, dry cheeks' },
  { id: 'normal', label: 'Normal', desc: 'Balanced, few concerns' },
  { id: 'sensitive', label: 'Sensitive', desc: 'Reactive, easily irritated' },
  { id: 'unsure', label: 'Unsure', desc: 'Need gentle, safe formulas' },
];

const BUDGET_RANGES = [
  { id: 'all', label: 'Any Budget', range: null },
  { id: 'under-500', label: 'Under ₹500', range: [100, 500] },
  { id: '500-1000', label: '₹500 - ₹1,000', range: [500, 1000] },
  { id: '1000-2500', label: '₹1,000 - ₹2,500', range: [1000, 2500] },
  { id: 'above-2500', label: '₹2,500+ (Luxury)', range: [2500, 10000] },
];

export const SkinConcernMatcherPage: React.FC = () => {
  const { user, openAuthModal } = useAuth();
  const navigate = useNavigate();

  const [selectedConcerns, setSelectedConcerns] = useState<string[]>([]);
  const [skinType, setSkinType] = useState<string>('unsure');
  const [budgetRange, setBudgetRange] = useState<string>('all');
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<'ai' | 'heuristic' | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const toggleConcern = useCallback((concernId: string) => {
    setSelectedConcerns((prev) =>
      prev.includes(concernId)
        ? prev.filter((c) => c !== concernId)
        : [...prev, concernId]
    );
  }, []);

  const handleSearch = async () => {
    if (selectedConcerns.length === 0) {
      setError('Please select at least one skin concern');
      return;
    }

    if (!user) {
      openAuthModal('login');
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);

    const budget = BUDGET_RANGES.find((b) => b.id === budgetRange);
    
    const res = await matchSkinConcerns(selectedConcerns, skinType, (budget?.range as [number, number] | undefined) || undefined);

    if (res.success && res.data) {
      setMatches(res.data.matches);
      setSource(res.data.matches.length > 0 && res.data.has_live_data ? 'ai' : 'heuristic');
    } else {
      setError(res.error || 'Failed to find matches');
      setMatches([]);
    }
    setLoading(false);
  };

  const handleProductClick = (productId: number) => {
    const product = PRODUCTS_DATA.find((p) => String(p.id) === String(productId));
    if (product) {
      navigate(`/product/${product.slug || product.id}`);
    }
  };

  const clearAll = () => {
    setSelectedConcerns([]);
    setSkinType('unsure');
    setBudgetRange('all');
    setMatches([]);
    setHasSearched(false);
    setError(null);
  };

  const hasActiveFilters = selectedConcerns.length > 0 || skinType !== 'unsure' || budgetRange !== 'all';

  return (
    <div className="min-h-screen bg-ivory">
      {/* Header */}
      <header className="border-b border-rose-100 bg-white/60 backdrop-blur-xs sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          <nav className="flex items-center space-x-2 text-xs text-espresso-500">
            <button
              onClick={() => navigate('/')}
              className="hover:text-rose-600 transition-colors flex items-center space-x-1"
            >
              <span>←</span>
              <span>Discovery</span>
            </button>
            <span>/</span>
            <span className="font-semibold text-espresso-800">Skin Concern Matcher</span>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 space-y-10">
        {/* Page Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-2">
            <span className="text-[10px] font-bold tracking-widest uppercase text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
              AI-Powered Discovery
            </span>
            <span className="text-espresso-300">•</span>
            <span className="text-[10px] font-semibold text-espresso-600">Phase 8E Live</span>
          </div>
          <h1 className="font-editorial text-4xl sm:text-5xl font-bold text-espresso-950 tracking-tight">
            Find Products for Your Skin Concerns
          </h1>
          <p className="text-lg text-espresso-600 max-w-2xl mx-auto leading-relaxed">
            Select your skin concerns, type, and budget. Our ingredient intelligence engine matches products
            with actives that address your specific needs — powered by Gemini AI with heuristic fallback.
          </p>
        </div>

        {/* Disclaimer */}
        <div className="p-4 sm:p-5 rounded-2xl bg-amber-500/10 border border-amber-300/60 text-espresso-800 text-xs sm:text-sm flex items-start space-x-3 mx-auto max-w-3xl">
          <ShieldCheck className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block text-espresso-900 mb-0.5">Cosmetic Guidance Notice</span>
            <p className="text-xs text-espresso-700 leading-relaxed">
              Product recommendations are for cosmetic discovery only and do not constitute dermatological
              or medical diagnosis. Consult a board-certified dermatologist for medical skin conditions.
            </p>
          </div>
        </div>

        {/* Filter Panel */}
        <div className="bg-white rounded-3xl border border-rose-200/90 p-6 sm:p-8 shadow-soft-lift space-y-8">
          {/* Skin Concerns */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-editorial font-bold text-espresso-900 flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-rose-500" />
                <span>1. Select Your Skin Concerns</span>
              </h2>
              {selectedConcerns.length > 0 && (
                <button
                  onClick={() => setSelectedConcerns([])}
                  className="text-xs font-bold text-rose-600 hover:text-rose-700 underline"
                >
                  Clear All
                </button>
              )}
            </div>
            <p className="text-xs text-espresso-500 mb-4">
              Choose one or more concerns to prioritize in matching. Products are ranked by ingredient relevance.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {SKIN_CONCERNS.map((concern) => {
                const active = selectedConcerns.includes(concern.id);
                const Icon = concern.icon;
                return (
                  <button
                    key={concern.id}
                    type="button"
                    onClick={() => toggleConcern(concern.id)}
                    className={`relative p-4 rounded-2xl border transition-all text-left ${
                      active
                        ? `border-2 ${concern.color.replace('bg-', 'bg-').replace('text-', 'text-').replace('border-', 'border-')} shadow-xs`
                        : 'border-rose-100 hover:border-rose-300 bg-white/60'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${concern.color} shrink-0`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className={`font-semibold text-sm ${active ? 'text-espresso-900' : 'text-espresso-800'}`}>
                            {concern.label}
                          </p>
                          {active && (
                            <ShieldCheck className="w-4 h-4 text-sage-600 shrink-0" />
                          )}
                        </div>
                        <p className="text-[11px] text-espresso-500 mt-0.5 leading-normal">{concern.desc}</p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          {/* Skin Type */}
          <section>
            <h2 className="text-base font-editorial font-bold text-espresso-900 mb-4 flex items-center space-x-2">
              <Sun className="w-4 h-4 text-champagne-600" />
              <span>2. Your Skin Type (Optional)</span>
            </h2>
            <p className="text-xs text-espresso-500 mb-4">
              Helps refine matches for your skin's baseline behavior.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
              {SKIN_TYPES.map((type) => (
                <button
                  key={type.id}
                  type="button"
                  onClick={() => setSkinType(type.id)}
                  className={`text-left p-3 rounded-2xl border transition-all ${
                    skinType === type.id
                      ? 'border-rose-400 bg-rose-50/70 shadow-xs'
                      : 'border-rose-100 hover:border-rose-200 bg-white/60'
                  }`}
                >
                  <p className={`font-semibold text-sm ${skinType === type.id ? 'text-rose-700' : 'text-espresso-800'}`}>
                    {type.label}
                  </p>
                  <p className="text-[11px] text-espresso-500 mt-0.5">{type.desc}</p>
                </button>
              ))}
            </div>
          </section>

          {/* Budget Range */}
          <section>
            <h2 className="text-base font-editorial font-bold text-espresso-900 mb-4 flex items-center space-x-2">
              <Tag className="w-4 h-4 text-rose-500" />
              <span>3. Budget Range (Optional)</span>
            </h2>
            <div className="flex flex-wrap gap-2">
              {BUDGET_RANGES.map((range) => (
                <button
                  key={range.id}
                  type="button"
                  onClick={() => setBudgetRange(range.id)}
                  className={`px-4 py-2 rounded-xl text-xs font-medium transition-all border ${
                    budgetRange === range.id
                      ? 'bg-rose-500 text-ivory border-rose-500 shadow-xs'
                      : 'bg-white border-rose-200 text-espresso-700 hover:border-rose-300'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </section>

          {/* Search Action */}
          <div className="pt-4 border-t border-rose-100 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2 text-xs text-espresso-500">
              <span className="font-semibold text-espresso-700">Active:</span>
              {selectedConcerns.map((c) => {
                const concern = SKIN_CONCERNS.find((sc) => sc.id === c);
                return concern ? (
                  <span key={c} className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${concern.color}`}>
                    {concern.label}
                  </span>
                ) : null;
              })}
              {skinType !== 'unsure' && (
                <span className="px-2 py-0.5 rounded-full bg-champagne-50 text-champagne-800 border border-champagne-300">
                  Skin: {SKIN_TYPES.find((t) => t.id === skinType)?.label}
                </span>
              )}
              {budgetRange !== 'all' && (
                <span className="px-2 py-0.5 rounded-full bg-ivory-200 text-espresso-800 border border-rose-200">
                  {BUDGET_RANGES.find((b) => b.id === budgetRange)?.label}
                </span>
              )}
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={clearAll}
                disabled={!hasActiveFilters}
                className="px-4 py-2.5 rounded-xl bg-white border border-rose-200 text-espresso-600 text-xs font-semibold hover:bg-rose-50 hover:border-rose-300 transition-all disabled:opacity-50 flex items-center space-x-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Clear All</span>
              </button>
              <button
                onClick={handleSearch}
                disabled={selectedConcerns.length === 0 || loading}
                className="px-6 py-2.5 rounded-xl bg-rose-500 hover:bg-rose-600 text-ivory text-xs font-semibold shadow-md hover:shadow-lg transition-all flex items-center space-x-2 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                <span>{loading ? 'Matching...' : 'Find My Matches'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-sm text-rose-800 flex items-center space-x-2 animate-shake">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Results */}
        {hasSearched && !loading && (
          <section className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-editorial text-2xl font-bold text-espresso-900">
                  Your Personalized Matches
                </h2>
                <p className="text-xs text-espresso-500 mt-0.5">
                  {matches.length} product{matches.length !== 1 ? 's' : ''} found
                  {source && (
                    <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      source === 'ai' ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-champagne-50 text-champagne-800 border border-champagne-300'
                    }">
                      {source === 'ai' ? '🧠 AI Ranked' : '⚡ Heuristic Ranked'}
                    </span>
                  )}
                </p>
              </div>
              {matches.length > 0 && (
                <div className="flex items-center space-x-2 text-xs text-espresso-500">
                  <span className="font-semibold text-espresso-700">Sort by:</span>
                  <span className="px-2 py-0.5 rounded-full bg-sage-100 text-sage-700 font-bold">Suitability Score</span>
                </div>
              )}
            </div>

            {matches.length === 0 ? (
              <div className="p-12 text-center bg-white/60 border border-rose-100 rounded-3xl text-espresso-600 text-sm space-y-4">
                <Target className="w-12 h-12 text-rose-400 mx-auto opacity-60" />
                <h3 className="font-editorial text-2xl font-bold text-espresso-800">No matches found</h3>
                <p className="text-xs text-espresso-500 leading-relaxed max-w-md mx-auto">
                  We couldn't find products matching your specific combination of concerns and filters.
                  Try selecting fewer concerns, broadening your budget, or changing your skin type.
                </p>
                <button
                  onClick={clearAll}
                  className="mt-2 px-5 py-2.5 rounded-xl bg-espresso-800 text-ivory text-xs font-semibold hover:bg-espresso-900 transition-colors shadow-xs"
                >
                  Reset & Try Again
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 sm:gap-7">
                {matches.map((match: any) => (
                  <ProductCard
                    key={match.product_id}
                    product={{
                      id: `match-${match.product_id}`,
                      slug: `match-${match.product_id}`,
                      name: match.product_name,
                      brand: match.brand,
                      category: match.category as any,
                      subcategory: 'Serum' as any,
                      quantity: 'Standard',
                      price: match.price || 0,
                      image: 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=800&q=80',
                      description: match.explanation,
                      skinType: '',
                      keyIngredients: match.matched_ingredients || [],
                      howToUse: {
                        routine: 'AM & PM',
                        stepNumber: 1,
                        instructions: 'Apply as directed.',
                      },
                      storeOffers: [],
                    } as any}
                    isWishlisted={false}
                    onToggleWishlist={() => {}}
                    onViewProduct={() => handleProductClick(match.product_id)}
                    onComparePrices={() => handleProductClick(match.product_id)}
                  />
                ))}
              </div>
            )}

            {/* Educational Note */}
            {matches.length > 0 && (
              <div className="p-5 rounded-2xl bg-white border border-rose-100 text-[11px] text-espresso-600 flex items-start space-x-3">
                <HelpCircle className="w-4 h-4 text-sage-600 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-espresso-800 block mb-1">How Matching Works</strong>
                  <p className="leading-relaxed">
                    Products are scored by <strong>ingredient relevance</strong> to your concerns. We analyze key actives
                    (niacinamide for acne, hyaluronic acid for dehydration, vitamin C for pigmentation, etc.) and rank
                    products where these ingredients appear prominently.
                    <strong>Suitability Score</strong> combines ingredient match strength, category relevance, and price fit.
                    Not a medical recommendation — consult a dermatologist for persistent conditions.
                  </p>
                </div>
              </div>
            )}
          </section>
        )}

        {/* Empty State */}
        {!hasSearched && !loading && (
          <div className="text-center py-20">
            <Sparkles className="w-16 h-16 text-rose-400 mx-auto mb-4 opacity-60" />
            <h3 className="font-editorial text-3xl font-bold text-espresso-800 mb-2">
              Ready to Find Your Matches
            </h3>
            <p className="text-lg text-espresso-600 max-w-xl mx-auto mb-8 leading-relaxed">
              Select your skin concerns above, optionally add your skin type and budget, then click
              "Find My Matches" to see personalized product recommendations powered by ingredient intelligence.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-espresso-500">
              <span className="font-semibold text-espresso-700">Popular combinations:</span>
              <button className="px-3 py-1.5 rounded-xl bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100" onClick={() => { setSelectedConcerns(['acne', 'oily']); setSkinType('oily'); }}>
                Acne + Oily Skin
              </button>
              <button className="px-3 py-1.5 rounded-xl bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100" onClick={() => { setSelectedConcerns(['dryness', 'dehydration']); setSkinType('dry'); }}>
                Dryness + Dehydration
              </button>
              <button className="px-3 py-1.5 rounded-xl bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100" onClick={() => { setSelectedConcerns(['pigmentation', 'dullness']); setSkinType('combination'); }}>
                Pigmentation + Dullness
              </button>
              <button className="px-3 py-1.5 rounded-xl bg-pink-50 text-pink-700 border border-pink-200 hover:bg-pink-100" onClick={() => { setSelectedConcerns(['sensitivity', 'redness']); setSkinType('sensitive'); }}>
                Sensitivity + Redness
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default SkinConcernMatcherPage;
