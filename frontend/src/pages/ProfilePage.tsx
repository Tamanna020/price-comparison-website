import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles,
  User,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  Save,
  CheckCircle2,
  Sliders,
  DollarSign,
  Heart,
  Palette,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import type { UserProfile, RecommendedProduct } from '../types';
import {
  getUserProfile,
  updateUserProfile,
  resetUserProfile,
  getPersonalizedRecommendations,
} from '../utils/api';

const SKIN_TYPES = [
  { id: 'oily', label: 'Oily', desc: 'Excess sebum, shine, prone to enlarged pores' },
  { id: 'dry', label: 'Dry', desc: 'Tightness, flaky areas, needs barrier hydration' },
  { id: 'combination', label: 'Combination', desc: 'Oily T-zone (forehead, nose) with normal/dry cheeks' },
  { id: 'normal', label: 'Normal', desc: 'Well-balanced sebum & moisture levels' },
  { id: 'sensitive', label: 'Sensitive', desc: 'Easily irritated, reactive to strong actives & fragrances' },
  { id: 'unsure', label: 'Unsure', desc: 'Need gentle, universally tolerated formulas' },
];

const SKIN_CONCERNS = [
  { id: 'acne', label: 'Acne & Breakouts' },
  { id: 'pigmentation', label: 'Hyperpigmentation & Dark Spots' },
  { id: 'dullness', label: 'Dullness & Uneven Tone' },
  { id: 'dryness', label: 'Dryness & Dehydration' },
  { id: 'barrier_repair', label: 'Compromised Skin Barrier' },
  { id: 'pores', label: 'Enlarged Pores & Texture' },
  { id: 'aging', label: 'Fine Lines & Firmness' },
  { id: 'sun_damage', label: 'Sun Damage & Tan' },
  { id: 'redness', label: 'Redness & Irritation' },
];

const COMMON_BRANDS = [
  'Minimalist',
  'The Derma Co',
  'Plum',
  'Dot & Key',
  'Cetaphil',
  'Neutrogena',
  'L\'Oréal Paris',
  'Maybelline',
  'Forest Essentials',
  'Kama Ayurveda',
  'Huda Beauty',
  'Nykaa Cosmetics',
];

const INGREDIENTS_AVOID = [
  { id: 'fragrance', label: 'Synthetic Fragrance / Parfum' },
  { id: 'essential_oils', label: 'Essential Oils' },
  { id: 'drying_alcohols', label: 'Drying Alcohols (Alcohol Denat)' },
  { id: 'parabens', label: 'Parabens' },
  { id: 'sulfates', label: 'Sulfates (SLS / SLES)' },
  { id: 'retinoids', label: 'Retinoids (Pregnancy / Nursing)' },
  { id: 'comedogenic_oils', label: 'Heavy Comedogenic Oils' },
];

export const ProfilePage: React.FC = () => {
  const { user, openAuthModal } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Profile fields
  const [skinType, setSkinType] = useState<UserProfile['skin_type']>('unsure');
  const [skinConcerns, setSkinConcerns] = useState<string[]>([]);
  const [preferredBrands, setPreferredBrands] = useState<string[]>([]);
  const [preferredCategories, setPreferredCategories] = useState<string[]>(['skincare']);
  const [budgetMin, setBudgetMin] = useState<number>(300);
  const [budgetMax, setBudgetMax] = useState<number>(2500);
  const [makeupFinish, setMakeupFinish] = useState<'matte' | 'dewy' | 'natural' | 'any'>('any');
  const [makeupCoverage, setMakeupCoverage] = useState<'light' | 'medium' | 'full' | 'any'>('any');
  const [undertone, setUndertone] = useState<'warm' | 'cool' | 'neutral' | 'olive' | 'unsure'>('unsure');
  const [ingredientAvoidances, setIngredientAvoidances] = useState<string[]>([]);
  const [disclaimer, setDisclaimer] = useState<string>('');

  // Recommendations
  const [recommendations, setRecommendations] = useState<RecommendedProduct[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    const res = await getUserProfile();
    if (res.profile) {
      const p = res.profile;
      setSkinType(p.skin_type || 'unsure');
      setSkinConcerns(p.skin_concerns || []);
      setPreferredBrands(p.preferred_brands || []);
      setPreferredCategories(p.preferred_categories || ['skincare']);
      setBudgetMin(p.budget_min ?? 300);
      setBudgetMax(p.budget_max ?? 2500);
      setMakeupFinish(p.makeup_preferences?.finish_preference || 'any');
      setMakeupCoverage(p.makeup_preferences?.coverage_preference || 'any');
      setUndertone(p.makeup_preferences?.undertone || 'unsure');
      setIngredientAvoidances(p.ingredient_avoidances || []);
    }
    if (res.disclaimer) {
      setDisclaimer(res.disclaimer);
    }
    setLoading(false);
  }, []);

  const loadRecommendations = useCallback(async () => {
    if (!user) return;
    setLoadingRecs(true);
    const recRes = await getPersonalizedRecommendations(6);
    setRecommendations(recRes.recommendations || []);
    setLoadingRecs(false);
  }, [user]);

  useEffect(() => {
    if (user) {
      loadProfile();
      loadRecommendations();
    } else {
      setLoading(false);
    }
  }, [user, loadProfile, loadRecommendations]);

  const toggleConcern = (concernId: string) => {
    setSkinConcerns((prev) =>
      prev.includes(concernId) ? prev.filter((c) => c !== concernId) : [...prev, concernId]
    );
  };

  const toggleBrand = (brand: string) => {
    setPreferredBrands((prev) =>
      prev.includes(brand) ? prev.filter((b) => b !== brand) : [...prev, brand]
    );
  };

  const toggleAvoidance = (ingId: string) => {
    setIngredientAvoidances((prev) =>
      prev.includes(ingId) ? prev.filter((i) => i !== ingId) : [...prev, ingId]
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    const res = await updateUserProfile({
      skin_type: skinType,
      skin_concerns: skinConcerns,
      preferred_brands: preferredBrands,
      preferred_categories: preferredCategories,
      budget_min: budgetMin,
      budget_max: budgetMax,
      makeup_preferences: {
        finish_preference: makeupFinish,
        coverage_preference: makeupCoverage,
        undertone: undertone,
      },
      ingredient_avoidances: ingredientAvoidances,
    });

    if (res.success) {
      setMessage({ type: 'success', text: 'Beauty profile successfully updated!' });
      loadRecommendations();
    } else {
      setMessage({ type: 'error', text: res.error || 'Failed to update profile' });
    }
    setSaving(false);
  };

  const handleReset = async () => {
    if (!window.confirm('Reset all beauty profile preferences to default?')) return;
    setSaving(true);
    const res = await resetUserProfile();
    if (res.success) {
      setMessage({ type: 'success', text: 'Profile preferences reset to defaults.' });
      loadProfile();
      loadRecommendations();
    }
    setSaving(false);
  };

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/80 border border-rose-200/80 rounded-3xl p-10 sm:p-14 shadow-soft-lift glass-panel max-w-xl mx-auto"
        >
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-rose-200 to-rose-400 mx-auto flex items-center justify-center text-ivory mb-5 shadow-xs">
            <User className="w-8 h-8" />
          </div>
          <h2 className="font-editorial text-3xl font-bold text-espresso-900 mb-2">
            Personalized Beauty Profile
          </h2>
          <p className="text-sm text-espresso-600 mb-8 leading-relaxed">
            Create your bespoke skin profile to unlock catalog recommendations matched to your skin type, concerns, active ingredient safety, and INR budget preferences.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => openAuthModal('login')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-rose-500 hover:bg-rose-600 text-ivory text-sm font-semibold shadow-md transition-all"
            >
              Sign In to Your Profile
            </button>
            <button
              onClick={() => openAuthModal('register')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white border border-rose-200 hover:border-rose-400 text-espresso-700 text-sm font-semibold transition-all"
            >
              Create Free Account
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-rose-100 rounded-full w-64 mx-auto" />
          <div className="h-4 bg-rose-50 rounded-full w-96 mx-auto" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 space-y-10">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-rose-100/80 pb-6">
        <div>
          <div className="flex items-center space-x-2 text-rose-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" />
            <span>Curated Intelligence</span>
          </div>
          <h1 className="font-editorial text-3xl sm:text-4xl font-bold text-espresso-900">
            Beauty Profile & Preferences
          </h1>
          <p className="text-sm text-espresso-600 mt-1">
            Logged in as <span className="font-semibold text-espresso-800">{user.name}</span> ({user.email})
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleReset}
            disabled={saving}
            className="px-4 py-2 text-xs font-medium text-espresso-600 hover:text-rose-600 bg-white border border-rose-200 rounded-xl hover:border-rose-300 transition-all flex items-center space-x-1.5 shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2.5 text-xs font-semibold text-ivory bg-rose-500 hover:bg-rose-600 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center space-x-2 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save Preferences'}</span>
          </button>
        </div>
      </div>

      {/* Status Alert */}
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-4 rounded-2xl border text-sm flex items-center space-x-3 ${
            message.type === 'success'
              ? 'bg-sage-50 border-sage-200 text-sage-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-sage-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          )}
          <span>{message.text}</span>
        </motion.div>
      )}

      {/* Non-medical Cosmetic Disclaimer Banner */}
      <div className="p-4 sm:p-5 rounded-2xl bg-amber-500/10 border border-amber-300/60 text-espresso-800 text-xs sm:text-sm flex items-start space-x-3">
        <ShieldCheck className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block text-espresso-900 mb-0.5">
            Cosmetic Guidance Notice
          </span>
          <p className="text-xs text-espresso-700 leading-relaxed">
            {disclaimer ||
              'Profile recommendations and routine suggestions are for cosmetic and skincare discovery purposes only and do not constitute dermatological or medical diagnosis. Please consult a board-certified dermatologist for medical skin conditions or persistent irritation.'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Settings (Left 2 Columns) */}
        <div className="lg:col-span-2 space-y-8">
          {/* Skin Type */}
          <section className="bg-white/80 border border-rose-100 rounded-3xl p-6 sm:p-8 shadow-xs glass-panel">
            <h2 className="text-base font-editorial font-bold text-espresso-900 mb-1 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-rose-400" />
              <span>1. Your Primary Skin Type</span>
            </h2>
            <p className="text-xs text-espresso-500 mb-4">
              Select the option that best reflects your bare skin a few hours after cleansing.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {SKIN_TYPES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setSkinType(t.id as UserProfile['skin_type'])}
                  className={`text-left p-3.5 rounded-2xl border transition-all ${
                    skinType === t.id
                      ? 'border-rose-400 bg-rose-50/70 shadow-xs'
                      : 'border-rose-100 hover:border-rose-200 bg-white/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-espresso-900">{t.label}</span>
                    {skinType === t.id && (
                      <span className="w-2 h-2 rounded-full bg-rose-500" />
                    )}
                  </div>
                  <p className="text-[11px] text-espresso-500 mt-1 leading-normal">{t.desc}</p>
                </button>
              ))}
            </div>
          </section>

          {/* Skin Concerns */}
          <section className="bg-white/80 border border-rose-100 rounded-3xl p-6 sm:p-8 shadow-xs glass-panel">
            <h2 className="text-base font-editorial font-bold text-espresso-900 mb-1 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-rose-400" />
              <span>2. Skin Concerns to Address</span>
            </h2>
            <p className="text-xs text-espresso-500 mb-4">
              Select multiple targets to prioritize in your product matching.
            </p>
            <div className="flex flex-wrap gap-2">
              {SKIN_CONCERNS.map((c) => {
                const active = skinConcerns.includes(c.id);
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => toggleConcern(c.id)}
                    className={`px-3.5 py-2 rounded-xl text-xs font-medium transition-all border ${
                      active
                        ? 'bg-rose-500 text-ivory border-rose-500 shadow-xs'
                        : 'bg-white border-rose-200/80 text-espresso-700 hover:border-rose-300'
                    }`}
                  >
                    {c.label}
                  </button>
                );
              })}
            </div>
          </section>

          {/* Ingredients to Avoid */}
          <section className="bg-white/80 border border-rose-100 rounded-3xl p-6 sm:p-8 shadow-xs glass-panel">
            <h2 className="text-base font-editorial font-bold text-espresso-900 mb-1 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-rose-400" />
              <span>3. Ingredient Sensitivities & Avoidances</span>
            </h2>
            <p className="text-xs text-espresso-500 mb-4">
              We will flag or filter catalog matches containing these ingredients.
            </p>
            <div className="flex flex-wrap gap-2">
              {INGREDIENTS_AVOID.map((ing) => {
                const active = ingredientAvoidances.includes(ing.id);
                return (
                  <button
                    key={ing.id}
                    type="button"
                    onClick={() => toggleAvoidance(ing.id)}
                    className={`px-3.5 py-2 rounded-xl text-xs font-medium transition-all border ${
                      active
                        ? 'bg-amber-600 text-ivory border-amber-600 shadow-xs'
                        : 'bg-white border-rose-200/80 text-espresso-700 hover:border-rose-300'
                    }`}
                  >
                    {ing.label}
                  </button>
                );
              })}
            </div>
          </section>

          {/* Makeup Preferences */}
          <section className="bg-white/80 border border-rose-100 rounded-3xl p-6 sm:p-8 shadow-xs glass-panel">
            <h2 className="text-base font-editorial font-bold text-espresso-900 mb-1 flex items-center space-x-2">
              <Palette className="w-4 h-4 text-rose-500" />
              <span>4. Makeup & Complexion Preferences</span>
            </h2>
            <p className="text-xs text-espresso-500 mb-4">
              Tailor finish, coverage, and undertone recommendations.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-espresso-700 mb-1.5">
                  Finish
                </label>
                <select
                  value={makeupFinish}
                  onChange={(e) => setMakeupFinish(e.target.value as 'matte' | 'dewy' | 'natural' | 'any')}
                  className="w-full p-2.5 bg-white border border-rose-200 rounded-xl text-xs text-espresso-800 focus:outline-hidden focus:border-rose-400"
                >
                  <option value="any">Any / Versatile</option>
                  <option value="matte">Velvet Matte</option>
                  <option value="dewy">Dewy / Luminous</option>
                  <option value="natural">Natural Satin</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-espresso-700 mb-1.5">
                  Coverage
                </label>
                <select
                  value={makeupCoverage}
                  onChange={(e) => setMakeupCoverage(e.target.value as 'light' | 'medium' | 'full' | 'any')}
                  className="w-full p-2.5 bg-white border border-rose-200 rounded-xl text-xs text-espresso-800 focus:outline-hidden focus:border-rose-400"
                >
                  <option value="any">Any Coverage</option>
                  <option value="light">Sheer / Skin Tint</option>
                  <option value="medium">Medium Buildable</option>
                  <option value="full">Full Coverage</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-espresso-700 mb-1.5">
                  Undertone
                </label>
                <select
                  value={undertone}
                  onChange={(e) => setUndertone(e.target.value as 'warm' | 'cool' | 'neutral' | 'olive' | 'unsure')}
                  className="w-full p-2.5 bg-white border border-rose-200 rounded-xl text-xs text-espresso-800 focus:outline-hidden focus:border-rose-400"
                >
                  <option value="unsure">Unsure / Flexible</option>
                  <option value="warm">Warm (Golden / Peachy)</option>
                  <option value="cool">Cool (Rosy / Blue)</option>
                  <option value="neutral">Neutral Balanced</option>
                  <option value="olive">Olive Undertone</option>
                </select>
              </div>
            </div>
          </section>
        </div>

        {/* Sidebar Controls (Right 1 Column) */}
        <div className="space-y-8">
          {/* Budget Range (INR) */}
          <section className="bg-white/80 border border-rose-100 rounded-3xl p-6 shadow-xs glass-panel">
            <h2 className="text-base font-editorial font-bold text-espresso-900 mb-1 flex items-center space-x-2">
              <DollarSign className="w-4 h-4 text-rose-500" />
              <span>Target Budget (INR)</span>
            </h2>
            <p className="text-xs text-espresso-500 mb-4">
              Set your target spending range for discovery suggestions.
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-xs text-espresso-600 mb-1">
                  Minimum Price: <span className="font-semibold text-espresso-900">₹{budgetMin}</span>
                </label>
                <input
                  type="range"
                  min="100"
                  max="2000"
                  step="50"
                  value={budgetMin}
                  onChange={(e) => setBudgetMin(Number(e.target.value))}
                  className="w-full accent-rose-500 cursor-pointer"
                />
              </div>
              <div>
                <label className="block text-xs text-espresso-600 mb-1">
                  Maximum Price: <span className="font-semibold text-espresso-900">₹{budgetMax}</span>
                </label>
                <input
                  type="range"
                  min="500"
                  max="10000"
                  step="100"
                  value={budgetMax}
                  onChange={(e) => setBudgetMax(Number(e.target.value))}
                  className="w-full accent-rose-500 cursor-pointer"
                />
              </div>
              <div className="p-3 bg-rose-50/50 rounded-xl border border-rose-100 text-center">
                <span className="text-xs text-espresso-700">
                  Target Range: <strong className="text-rose-600">₹{budgetMin} – ₹{budgetMax}</strong>
                </span>
              </div>
            </div>
          </section>

          {/* Preferred Brands */}
          <section className="bg-white/80 border border-rose-100 rounded-3xl p-6 shadow-xs glass-panel">
            <h2 className="text-base font-editorial font-bold text-espresso-900 mb-1 flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-rose-500" />
              <span>Favorite Brands</span>
            </h2>
            <p className="text-xs text-espresso-500 mb-4">
              Selected brands receive higher recommendation weights.
            </p>
            <div className="flex flex-wrap gap-1.5">
              {COMMON_BRANDS.map((b) => {
                const active = preferredBrands.includes(b);
                return (
                  <button
                    key={b}
                    type="button"
                    onClick={() => toggleBrand(b)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all border ${
                      active
                        ? 'bg-rose-500 text-ivory border-rose-500'
                        : 'bg-white border-rose-200 text-espresso-700 hover:border-rose-300'
                    }`}
                  >
                    {b}
                  </button>
                );
              })}
            </div>
          </section>
        </div>
      </div>

      {/* Dynamic Catalog Recommendations Preview */}
      <section className="pt-8 border-t border-rose-100">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center space-x-2 text-rose-500 text-xs font-semibold uppercase tracking-wider mb-1">
              <Heart className="w-4 h-4" />
              <span>Personalized For You</span>
            </div>
            <h2 className="font-editorial text-2xl font-bold text-espresso-900">
              Matched From Our Indian Catalog
            </h2>
            <p className="text-xs text-espresso-500 mt-0.5">
              Scored based on your skin type, primary concerns, and budget in ₹ INR.
            </p>
          </div>
        </div>

        {loadingRecs ? (
          <div className="text-center py-12 text-espresso-500 text-xs">
            Calculating personalized matches...
          </div>
        ) : recommendations.length === 0 ? (
          <div className="p-8 text-center bg-white/60 border border-rose-100 rounded-3xl text-espresso-600 text-sm">
            Save your skin preferences above to see personalized product matches.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.map((rec) => (
              <div
                key={rec.id}
                className="bg-white border border-rose-100 rounded-3xl p-5 shadow-xs hover:shadow-soft-lift transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-espresso-500 mb-2">
                    <span className="font-semibold text-rose-600">{rec.brand}</span>
                    <span className="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 font-bold text-[10px]">
                      {rec.recommendation_score}% Match
                    </span>
                  </div>
                  <h3 className="font-editorial text-base font-bold text-espresso-900 mb-1 line-clamp-1">
                    {rec.name}
                  </h3>
                  <p className="text-xs font-semibold text-espresso-800 mb-3">
                    ₹{rec.price}{' '}
                    {rec.original_price && rec.original_price > rec.price && (
                      <span className="text-xs text-espresso-400 line-through font-normal ml-1">
                        ₹{rec.original_price}
                      </span>
                    )}
                  </p>
                  <div className="space-y-1">
                    {rec.matched_reasons.map((r, i) => (
                      <p key={i} className="text-[11px] text-sage-700 flex items-center space-x-1">
                        <span className="w-1 h-1 rounded-full bg-sage-500" />
                        <span>{r}</span>
                      </p>
                    ))}
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-rose-50 flex items-center justify-between">
                  <a
                    href={`/product/${rec.id}`}
                    className="text-xs font-semibold text-rose-600 hover:text-rose-700 flex items-center space-x-1"
                  >
                    <span>View Live Comparison</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

