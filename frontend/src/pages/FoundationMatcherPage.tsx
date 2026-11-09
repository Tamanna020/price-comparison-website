import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Info,
  CheckCircle2,
  RefreshCw,
  Palette,
} from 'lucide-react';
import {
  matchFoundationShade,
  type FoundationMatchResponse,
} from '../utils/api';

const SKIN_DEPTHS = [
  { id: 'fair', label: 'Fair', hex: '#F9E4D4', desc: 'Porcelain, very fair (MAC NC10-15)' },
  { id: 'light', label: 'Light', hex: '#EED0B5', desc: 'Light beige, soft wheat (MAC NC20)' },
  { id: 'light_medium', label: 'Light-Medium', hex: '#E1BC9B', desc: 'Warm wheatish, golden light (MAC NC25-30)' },
  { id: 'medium', label: 'Medium', hex: '#CCA17A', desc: 'Classic Indian wheatish (MAC NC35-40)' },
  { id: 'tan', label: 'Tan', hex: '#B5855A', desc: 'Rich honey, golden caramel (MAC NC42-45)' },
  { id: 'deep', label: 'Deep', hex: '#8F5E3B', desc: 'Warm espresso, bronze caramel (MAC NC47-50)' },
  { id: 'rich_deep', label: 'Rich-Deep', hex: '#5E3821', desc: 'Deep cocoa, espresso (MAC NC55+)' },
];

const UNDERTONES = [
  {
    id: 'warm',
    label: 'Warm (Golden / Yellow)',
    desc: 'Veins appear greenish; gold jewelry flatters; tans easily in sun.',
    accent: '#F59E0B',
  },
  {
    id: 'cool',
    label: 'Cool (Rosy / Pink)',
    desc: 'Veins appear blue/purple; silver jewelry flatters; burns or turns pink in sun.',
    accent: '#EC4899',
  },
  {
    id: 'neutral',
    label: 'Neutral (Balanced)',
    desc: 'Balanced peach/golden mix; both gold and silver look harmonious.',
    accent: '#8B5CF6',
  },
  {
    id: 'olive',
    label: 'Olive (Greenish / Muted)',
    desc: 'Distinct South Asian green/ashy tone; regular warm shades look too orange, cool shades look ashy.',
    accent: '#84CC16',
  },
];

export const FoundationMatcherPage: React.FC = () => {
  const [selectedDepth, setSelectedDepth] = useState('light_medium');
  const [selectedUndertone, setSelectedUndertone] = useState('warm');
  const [coverage, setCoverage] = useState('Medium');
  const [finish, setFinish] = useState('Matte');
  const [referenceBrand, setReferenceBrand] = useState('MAC');
  const [referenceShade, setReferenceShade] = useState('NC25');
  const [matchData, setMatchData] = useState<FoundationMatchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      const res = await matchFoundationShade({
        skinDepth: selectedDepth,
        undertone: selectedUndertone,
        coverage,
        finish,
        referenceBrand,
        referenceShade,
      });
      if (res.success && res.data) {
        setMatchData(res.data);
      }
      setIsLoading(false);
    }
    load();
  }, [selectedDepth, selectedUndertone, coverage, finish, referenceBrand, referenceShade]);

  return (
    <div className="min-h-screen bg-ivory text-espresso-900 pb-20">
      {/* Header Banner */}
      <section className="bg-gradient-to-b from-rose-100/60 via-ivory to-ivory border-b border-rose-200/50 pt-10 pb-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-rose-200/60 border border-rose-300/60 text-espresso-800 text-xs font-semibold uppercase tracking-wider mb-3">
            <Palette className="w-3.5 h-3.5 text-rose-600" />
            <span>Phase 10 Intelligence • South Asian Colorimetry Matching</span>
          </div>
          <h1 className="font-editorial text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-espresso-900">
            Foundation Shade & <span className="italic font-normal text-rose-600">Undertone Matcher</span>
          </h1>
          <p className="mt-2 text-espresso-600 text-sm sm:text-base max-w-3xl">
            South Asian skin encompasses intricate olive, golden, and neutral undertones often mismatched by Western colorimetry. Find your precise catalog match with algorithmic sebum oxidation adjustments.
          </p>
        </div>
      </section>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 space-y-8">
        {/* Step 1: Skin Depth Selector */}
        <div className="bg-white rounded-2xl border border-rose-200/70 p-6 shadow-soft-lift">
          <h2 className="text-sm font-bold uppercase tracking-wider text-espresso-500 mb-3">
            1. Select Your Skin Depth
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
            {SKIN_DEPTHS.map((depth) => {
              const isSelected = selectedDepth === depth.id;
              return (
                <button
                  key={depth.id}
                  onClick={() => setSelectedDepth(depth.id)}
                  className={`p-3 rounded-2xl text-left border transition-all flex flex-col justify-between ${
                    isSelected
                      ? 'bg-ivory border-rose-600 shadow-soft-lift ring-2 ring-rose-500/30'
                      : 'bg-white border-rose-200/80 hover:border-rose-400'
                  }`}
                >
                  <div
                    className="w-full h-12 rounded-xl mb-2.5 shadow-xs border border-espresso-200/20"
                    style={{ backgroundColor: depth.hex }}
                  />
                  <div>
                    <h3 className="font-serif font-bold text-xs text-espresso-900">{depth.label}</h3>
                    <p className="text-[10px] text-espresso-500 line-clamp-1 mt-0.5">{depth.desc}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Step 2: Undertone Selector */}
        <div className="bg-white rounded-2xl border border-rose-200/70 p-6 shadow-soft-lift">
          <h2 className="text-sm font-bold uppercase tracking-wider text-espresso-500 mb-3">
            2. Select Your Undertone
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {UNDERTONES.map((tone) => {
              const isSelected = selectedUndertone === tone.id;
              return (
                <button
                  key={tone.id}
                  onClick={() => setSelectedUndertone(tone.id)}
                  className={`p-4 rounded-2xl text-left border transition-all ${
                    isSelected
                      ? 'bg-ivory border-rose-600 shadow-soft-lift ring-2 ring-rose-500/30'
                      : 'bg-white border-rose-200/80 hover:border-rose-400'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-2">
                    <span
                      className="w-3.5 h-3.5 rounded-full"
                      style={{ backgroundColor: tone.accent }}
                    />
                    <h3 className="font-serif font-bold text-sm text-espresso-900">{tone.label}</h3>
                  </div>
                  <p className="text-xs text-espresso-600 leading-relaxed">{tone.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Step 3: Reference Converter & Preferences */}
        <div className="bg-white rounded-2xl border border-rose-200/70 p-6 shadow-soft-lift grid md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-espresso-500 mb-2">
              Reference Brand & Shade (Optional)
            </h3>
            <div className="flex gap-2">
              <select
                value={referenceBrand}
                onChange={(e) => setReferenceBrand(e.target.value)}
                className="w-1/2 text-xs px-3 py-2.5 rounded-xl border border-rose-200 bg-white"
              >
                <option value="MAC">M.A.C</option>
                <option value="Maybelline">Maybelline</option>
                <option value="Fenty">Fenty Beauty</option>
                <option value="Loreal">L'Oreal</option>
              </select>
              <input
                type="text"
                value={referenceShade}
                onChange={(e) => setReferenceShade(e.target.value)}
                placeholder="e.g. NC25, 128"
                className="w-1/2 text-xs px-3 py-2.5 rounded-xl border border-rose-200 bg-white"
              />
            </div>
            <p className="text-[10px] text-espresso-400 mt-1">
              Used to fine-tune your depth and calibrate cross-brand accuracy.
            </p>
          </div>

          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-espresso-500 mb-2">
              Desired Coverage
            </h3>
            <div className="flex gap-2">
              {['Sheer', 'Medium', 'Full'].map((cov) => (
                <button
                  key={cov}
                  onClick={() => setCoverage(cov)}
                  className={`flex-1 py-2 rounded-xl text-xs font-medium border transition-colors ${
                    coverage === cov
                      ? 'bg-espresso-900 text-white border-espresso-900'
                      : 'bg-ivory text-espresso-700 border-rose-200 hover:border-rose-400'
                  }`}
                >
                  {cov}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-espresso-500 mb-2">
              Finish Preference
            </h3>
            <div className="flex gap-2">
              {['Matte', 'Natural / Satin', 'Dewy'].map((fin) => (
                <button
                  key={fin}
                  onClick={() => setFinish(fin)}
                  className={`flex-1 py-2 rounded-xl text-xs font-medium border transition-colors ${
                    finish === fin
                      ? 'bg-rose-500 text-white border-rose-500'
                      : 'bg-ivory text-espresso-700 border-rose-200 hover:border-rose-400'
                  }`}
                >
                  {fin}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Presentation */}
        {isLoading ? (
          <div className="p-12 text-center text-espresso-500">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-rose-500 mb-2" />
            <p className="text-sm">Calculating South Asian shade calibration...</p>
          </div>
        ) : matchData ? (
          <div className="space-y-6">
            {/* Undertone Guidance Callout */}
            <div className="p-5 rounded-2xl bg-rose-50/70 border border-rose-200 flex items-start space-x-3.5">
              <Sparkles className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-serif font-bold text-sm text-espresso-900">
                  Undertone Analysis & Colorimetry Notes
                </h4>
                <p className="text-xs text-espresso-700 mt-1 leading-relaxed">
                  {matchData.undertone_guidance}
                </p>
              </div>
            </div>

            {/* Matched Foundations */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-serif font-bold text-lg text-espresso-900">
                  Recommended Catalog Foundations
                </h3>
                <span className="text-xs text-espresso-500">
                  {matchData.matches.length} Matches Found
                </span>
              </div>

              <div className="grid md:grid-cols-2 gap-5">
                {matchData.matches.map((match, i) => (
                  <div
                    key={i}
                    className="bg-white rounded-2xl border border-rose-200/80 p-5 shadow-soft-lift flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold uppercase tracking-wider text-rose-500">
                          {match.brand}
                        </span>
                        <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>{match.confidence_score}% Confidence</span>
                        </div>
                      </div>

                      <div className="flex items-start space-x-4 mb-4">
                        {match.image_url ? (
                          <img
                            src={match.image_url}
                            alt={match.product_title}
                            className="w-20 h-20 rounded-xl object-cover shrink-0 border border-rose-100"
                          />
                        ) : (
                          <div className="w-20 h-20 rounded-xl bg-rose-50 flex items-center justify-center shrink-0 text-rose-400 font-serif font-bold">
                            {match.brand.slice(0, 2)}
                          </div>
                        )}

                        <div>
                          <h4 className="font-serif font-bold text-base text-espresso-900">
                            {match.product_title}
                          </h4>
                          <div className="mt-1 flex items-center space-x-2">
                            <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-rose-100 text-rose-900">
                              Shade: {match.recommended_shade_code}
                            </span>
                            <span className="text-xs text-espresso-500">{match.finish} Finish</span>
                          </div>
                        </div>
                      </div>

                      {/* Oxidation Advisory Box */}
                      <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900">
                        <span className="font-bold block mb-0.5">⚠️ Sebum Oxidation Advisory:</span>
                        <p className="text-amber-800">{match.oxidation_advisory}</p>
                      </div>
                    </div>

                    {/* Cross-Brand Shade Equivalents */}
                    <div className="mt-4 pt-3 border-t border-rose-100 grid grid-cols-3 gap-2 text-center text-[11px]">
                      <div className="p-2 rounded-lg bg-ivory border border-rose-100">
                        <span className="text-espresso-400 uppercase font-bold block text-[9px]">
                          M.A.C Equivalent
                        </span>
                        <span className="font-bold text-espresso-800">{match.mac_equivalent}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-ivory border border-rose-100">
                        <span className="text-espresso-400 uppercase font-bold block text-[9px]">
                          L'Oreal True Match
                        </span>
                        <span className="font-bold text-espresso-800">{match.loreal_equivalent}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-ivory border border-rose-100">
                        <span className="text-espresso-400 uppercase font-bold block text-[9px]">
                          Fenty Beauty
                        </span>
                        <span className="font-bold text-espresso-800">{match.fenty_equivalent}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}

        {/* Mandatory Algorithmic Shade Guidance Disclaimer */}
        <div className="p-4 rounded-xl bg-ivory border border-rose-200/80 text-xs text-espresso-600 flex items-start space-x-3">
          <Info className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
          <p>
            <strong>Algorithmic Shade Guidance Notice:</strong> Foundation shade matches and undertone assessments are estimated using optical colorimetry calibrations and manufacturer specifications. Factors such as skin sebum oxidation, seasonal tanning, and indoor lighting affect appearance. Jawline swatch testing in natural daylight is recommended prior to purchase.
          </p>
        </div>
      </main>
    </div>
  );
};
