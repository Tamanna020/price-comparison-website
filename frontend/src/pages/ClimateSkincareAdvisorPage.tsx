import React, { useState, useEffect } from 'react';
import {
  CloudSun,
  Droplets,
  Thermometer,
  ShieldAlert,
  Sparkles,
  Info,
  CheckCircle2,
  Wind,
  Sun,
  CloudRain,
  Building2,
  Compass,
  RefreshCw,
} from 'lucide-react';
import {
  fetchClimateRecommendations,
  type ClimateSkincareResponse,
} from '../utils/api';

const CLIMATE_OPTIONS = [
  {
    code: 'hot_humid',
    name: 'Hot & Humid',
    subtitle: 'Coastal / Tropical',
    cities: 'Mumbai, Chennai, Kolkata, Goa',
    icon: CloudSun,
  },
  {
    code: 'hot_dry',
    name: 'Hot & Arid',
    subtitle: 'Desert & Summer Plains',
    cities: 'Delhi (May-June), Rajasthan, Ahmedabad',
    icon: Sun,
  },
  {
    code: 'monsoon',
    name: 'Monsoon Humidity',
    subtitle: 'Pan-India Rains',
    cities: 'July to September across India',
    icon: CloudRain,
  },
  {
    code: 'winter_dry',
    name: 'Winter Dryness',
    subtitle: 'Cold Winds & High TEWL',
    cities: 'Delhi, Punjab, UP, Kashmir (Nov-Feb)',
    icon: Wind,
  },
  {
    code: 'ac_indoor',
    name: 'AC Indoor Work',
    subtitle: 'Artificial Dehydration',
    cities: 'Corporate IT Hubs & Office Desks',
    icon: Building2,
  },
  {
    code: 'temperate_seasonal',
    name: 'Temperate / Plateau',
    subtitle: 'Mild Transitions',
    cities: 'Bangalore, Pune, Shillong',
    icon: Compass,
  },
];

export const ClimateSkincareAdvisorPage: React.FC = () => {
  const [selectedClimate, setSelectedClimate] = useState<string>('hot_humid');
  const [selectedSkinType, setSelectedSkinType] = useState<string>('Combination');
  const [selectedConcerns, setSelectedConcerns] = useState<string[]>(['Oiliness & Pores']);
  const [recommendationData, setRecommendationData] = useState<ClimateSkincareResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const skinTypeOptions = ['Oily', 'Dry', 'Combination', 'Sensitive', 'Normal'];
  const concernOptions = [
    'Oiliness & Pores',
    'Acne & Blemishes',
    'Dehydration & Tightness',
    'Hyperpigmentation & Dullness',
    'Barrier Repair',
  ];

  const toggleConcern = (concern: string) => {
    setSelectedConcerns((prev) =>
      prev.includes(concern) ? prev.filter((c) => c !== concern) : [...prev, concern]
    );
  };

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      const res = await fetchClimateRecommendations(
        selectedClimate,
        selectedSkinType,
        selectedConcerns
      );
      if (res.success && res.data) {
        setRecommendationData(res.data);
      }
      setIsLoading(false);
    }
    load();
  }, [selectedClimate, selectedSkinType, selectedConcerns]);

  const profile = recommendationData?.climate_profile;

  return (
    <div className="min-h-screen bg-ivory text-espresso-900 pb-20">
      {/* Header Banner */}
      <section className="bg-gradient-to-b from-rose-100/60 via-ivory to-ivory border-b border-rose-200/50 pt-10 pb-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-rose-200/60 border border-rose-300/60 text-espresso-800 text-xs font-semibold uppercase tracking-wider mb-3">
            <CloudSun className="w-3.5 h-3.5 text-rose-600" />
            <span>Phase 10 Skincare Intelligence • Indian Weather Adaptations</span>
          </div>
          <h1 className="font-editorial text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-espresso-900">
            Climate-Aware <span className="italic font-normal text-rose-600">Skincare Advisor</span>
          </h1>
          <p className="mt-2 text-espresso-600 text-sm sm:text-base max-w-3xl">
            Indian micro-climates dramatically alter skin barrier lipid fluidization, trans-epidermal water loss (TEWL), and fungal acne vulnerability. Select your current weather reality for targeted texture and active recommendations.
          </p>
        </div>
      </section>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 space-y-8">
        {/* Climate Selector Carousel / Grid */}
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-espresso-500 mb-3">
            1. Select Your Current Regional Climate Condition
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {CLIMATE_OPTIONS.map((item) => {
              const Icon = item.icon;
              const isSelected = selectedClimate === item.code;
              return (
                <button
                  key={item.code}
                  onClick={() => setSelectedClimate(item.code)}
                  className={`p-3.5 rounded-2xl text-left border transition-all flex flex-col justify-between ${
                    isSelected
                      ? 'bg-rose-500 text-white border-rose-600 shadow-soft-lift scale-[1.02]'
                      : 'bg-white text-espresso-800 border-rose-200/70 hover:border-rose-400'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <Icon className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-rose-500'}`} />
                    {isSelected && <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded-full font-bold">Active</span>}
                  </div>
                  <div>
                    <h3 className="font-serif font-bold text-sm leading-tight">{item.name}</h3>
                    <p className={`text-[10px] mt-0.5 leading-tight ${isSelected ? 'text-rose-100' : 'text-espresso-500'}`}>
                      {item.subtitle}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* User Skin Context Filters */}
        <div className="bg-white rounded-2xl border border-rose-200/70 p-5 shadow-soft-lift flex flex-col md:flex-row gap-6 justify-between items-start md:items-center">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-espresso-500 mb-2">
              Skin Type
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {skinTypeOptions.map((st) => (
                <button
                  key={st}
                  onClick={() => setSelectedSkinType(st)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    selectedSkinType === st
                      ? 'bg-espresso-900 text-white border-espresso-900'
                      : 'bg-ivory text-espresso-700 border-rose-200/80 hover:border-rose-400'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-espresso-500 mb-2">
              Primary Skin Concerns
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {concernOptions.map((concern) => {
                const isSelected = selectedConcerns.includes(concern);
                return (
                  <button
                    key={concern}
                    onClick={() => toggleConcern(concern)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      isSelected
                        ? 'bg-rose-600 text-white border-rose-600'
                        : 'bg-ivory text-espresso-700 border-rose-200/80 hover:border-rose-400'
                    }`}
                  >
                    {concern}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Climate Strategy & Guidance Panels */}
        {isLoading ? (
          <div className="p-12 text-center text-espresso-500 bg-white rounded-2xl border border-rose-100">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-rose-500 mb-2" />
            <p className="text-sm">Calculating regional climate adaptations...</p>
          </div>
        ) : profile ? (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Detailed Strategy Cards */}
            <div className="lg:col-span-2 space-y-6">
              {/* Climate Overview Card */}
              <div className="bg-white rounded-2xl border border-rose-200/80 p-6 shadow-soft-lift">
                <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-rose-100">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-rose-500">
                      Regional Profile
                    </span>
                    <h2 className="font-serif font-bold text-2xl text-espresso-900 mt-0.5">
                      {profile.name}
                    </h2>
                    <p className="text-xs text-espresso-500 mt-0.5">{profile.regions}</p>
                  </div>

                  <div className="flex items-center space-x-3 text-xs">
                    <span className="px-3 py-1.5 rounded-xl bg-ivory border border-rose-200 flex items-center space-x-1 font-medium">
                      <Thermometer className="w-3.5 h-3.5 text-rose-500" />
                      <span>{profile.temperature_range}</span>
                    </span>
                    <span className="px-3 py-1.5 rounded-xl bg-ivory border border-rose-200 flex items-center space-x-1 font-medium">
                      <Droplets className="w-3.5 h-3.5 text-blue-500" />
                      <span>{profile.humidity_level}</span>
                    </span>
                  </div>
                </div>

                <div className="mt-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-espresso-500 mb-1">
                    Real-World Skin Impact
                  </h3>
                  <p className="text-sm text-espresso-700 leading-relaxed">{profile.skin_impact}</p>
                </div>

                {/* 4 Formulation Strategy Pillars */}
                <div className="grid sm:grid-cols-2 gap-4 mt-6 pt-4 border-t border-rose-100">
                  <div className="p-3.5 rounded-xl bg-ivory/60 border border-rose-100">
                    <span className="text-xs font-bold text-espresso-900 block mb-1">
                      🫧 Cleanser Strategy
                    </span>
                    <p className="text-xs text-espresso-600">{profile.cleanser_guidance}</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-ivory/60 border border-rose-100">
                    <span className="text-xs font-bold text-espresso-900 block mb-1">
                      🧴 Moisturizer Vehicle
                    </span>
                    <p className="text-xs text-espresso-600">{profile.moisturizer_guidance}</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-ivory/60 border border-rose-100">
                    <span className="text-xs font-bold text-espresso-900 block mb-1">
                      ☀️ Sunscreen Vehicle
                    </span>
                    <p className="text-xs text-espresso-600">{profile.sunscreen_guidance}</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-ivory/60 border border-rose-100">
                    <span className="text-xs font-bold text-espresso-900 block mb-1">
                      💄 Makeup Base Advice
                    </span>
                    <p className="text-xs text-espresso-600">{profile.makeup_base_guidance}</p>
                  </div>
                </div>
              </div>

              {/* Actives Recommendations */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="bg-emerald-50/60 rounded-2xl border border-emerald-200 p-5 shadow-xs">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-900 flex items-center space-x-1.5 mb-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Hero Actives for this Climate</span>
                  </span>
                  <ul className="space-y-1.5 text-xs text-emerald-800">
                    {profile.recommended_actives.map((act, i) => (
                      <li key={i} className="flex items-center space-x-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        <span>{act}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-amber-50/60 rounded-2xl border border-amber-200 p-5 shadow-xs">
                  <span className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center space-x-1.5 mb-2">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                    <span>Formulations to Avoid / Limit</span>
                  </span>
                  <ul className="space-y-1.5 text-xs text-amber-800">
                    {profile.avoid_or_caution.map((av, i) => (
                      <li key={i} className="flex items-center space-x-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                        <span>{av}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Right 1 Col: Matched Catalog Products */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-serif font-bold text-base text-espresso-900 flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-rose-500" />
                  <span>Catalog Product Matches</span>
                </h3>
                <span className="text-[10px] uppercase font-bold text-rose-600 bg-rose-100 px-2 py-0.5 rounded-full">
                  Verified Matches
                </span>
              </div>

              {recommendationData.matched_catalog_products.length > 0 ? (
                <div className="space-y-3">
                  {recommendationData.matched_catalog_products.map((prod) => (
                    <div
                      key={prod.id}
                      className="bg-white rounded-2xl border border-rose-200/70 p-4 shadow-soft-lift flex items-start space-x-3.5 hover:border-rose-400 transition-colors"
                    >
                      {prod.image_url ? (
                        <img
                          src={prod.image_url}
                          alt={prod.title}
                          className="w-16 h-16 rounded-xl object-cover shrink-0 border border-rose-100"
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-xl bg-rose-50 flex items-center justify-center shrink-0 text-rose-400 font-serif font-bold">
                          {prod.brand.slice(0, 2)}
                        </div>
                      )}

                      <div className="flex-1 min-w-0">
                        <span className="text-[10px] font-bold text-rose-500 uppercase tracking-wider block">
                          {prod.brand}
                        </span>
                        <h4 className="font-serif font-bold text-xs text-espresso-900 truncate">
                          {prod.title}
                        </h4>
                        <p className="text-[11px] text-espresso-600 line-clamp-2 mt-1">
                          {prod.climate_rationale}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-espresso-500 bg-white rounded-2xl border border-rose-100">
                  No direct product matches found for selected criteria.
                </div>
              )}
            </div>
          </div>
        ) : null}

        {/* Mandatory Medical Disclaimer Banner */}
        <div className="p-4 rounded-xl bg-ivory border border-rose-200/80 text-xs text-espresso-600 flex items-start space-x-3">
          <Info className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
          <p>
            <strong>PriceWise AI Cosmetic Guidance Notice:</strong> Climate recommendations and texture guidance are educational cosmetic suggestions based on published dermatological literature. They do not constitute medical diagnoses or prescriptions. If irritation, burning, or redness occurs, discontinue use immediately.
          </p>
        </div>
      </main>
    </div>
  );
};
