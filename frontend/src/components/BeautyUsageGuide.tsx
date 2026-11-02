import React from 'react';
import {
  Sparkles,
  AlertTriangle,
  ShieldCheck,
  Clock,
  Sun,
  Moon,
  Info,
  CheckCircle2,
} from 'lucide-react';
import type { Product, KeyActiveDetail } from '../types';

interface BeautyUsageGuideProps {
  product: Product;
}

export const BeautyUsageGuide: React.FC<BeautyUsageGuideProps> = ({ product }) => {
  const { howToUse, category, subcategory, keyIngredients } = product;

  // Infer routine step name if not provided
  const inferStepName = (stepNum: number, subcat: string) => {
    const s = subcat.toLowerCase();
    if (s.includes('wash') || s.includes('cleanser')) return 'Cleanse';
    if (s.includes('toner')) return 'Tone & Prep';
    if (s.includes('serum')) return 'Targeted Treatment';
    if (s.includes('moisturiser') || s.includes('cream')) return 'Hydrate & Seal';
    if (s.includes('sunscreen')) return 'Broad Spectrum UV Defense';
    return `Step ${stepNum}`;
  };

  const stepName = howToUse.stepName || inferStepName(howToUse.stepNumber, subcategory);
  const routine = howToUse.routine || 'AM & PM';
  const frequency = howToUse.frequency || (
    routine === 'AM'
      ? 'Daily every morning as the final skincare layer'
      : routine === 'PM'
      ? 'Daily every evening before sleep'
      : 'Twice daily (Morning & Evening)'
  );

  // Derive active ingredients breakdown
  const actives: KeyActiveDetail[] = howToUse.keyActives && howToUse.keyActives.length > 0
    ? howToUse.keyActives
    : keyIngredients.map((ing) => {
        const lower = ing.toLowerCase();
        let benefit = 'Nourishing hydration & skin conditioning';
        if (lower.includes('niacinamide')) benefit = 'Regulates sebum, minimizes pore appearance & fades post-acne blemishes';
        else if (lower.includes('hyaluronic')) benefit = 'Draws multi-depth moisture into the stratum corneum for plumped elasticity';
        else if (lower.includes('ceramide')) benefit = 'Restores essential epidermal lipid bilayer to repair compromised skin barrier';
        else if (lower.includes('salicylic') || lower.includes('bha')) benefit = 'Lipophilic beta-hydroxy acid that dissolves pore-clogging debris';
        else if (lower.includes('vitamin c') || lower.includes('ascorbic')) benefit = 'Potent antioxidant defense against oxidative stress and uneven hyperpigmentation';
        else if (lower.includes('zinc')) benefit = 'Calms active redness and balances excess cutaneous sebum secretion';
        else if (lower.includes('tinosorb') || lower.includes('uv') || lower.includes('sunscreen')) benefit = 'Photostable broad-spectrum UVA & UVB protection without white residue';
        else if (lower.includes('watermelon')) benefit = 'Instant cooling sensation, soothing hydration and free-radical defense';
        else if (lower.includes('aloe') || lower.includes('cica') || lower.includes('centella')) benefit = 'Soothes inflammation, diminishes erythema and accelerates barrier recovery';
        else if (lower.includes('peptide')) benefit = 'Signal peptides that support collagen synthesis and skin firming';
        return { name: ing, benefit };
      });

  // Check if formulation contains photosensitizing actives
  const containsPhotosensitizer = keyIngredients.some((ing) => {
    const l = ing.toLowerCase();
    return l.includes('salicylic') || l.includes('glycolic') || l.includes('lactic') ||
      l.includes('retinol') || l.includes('retinoid') || l.includes('aha') || l.includes('bha') ||
      l.includes('ascorbic');
  });

  const sunWarning = howToUse.sunSafetyWarning || (
    containsPhotosensitizer
      ? 'Active Formulation Advisory: Exfoliating acids and retinoids increase skin photosensitivity to UV radiation. Always follow with broad-spectrum SPF 50+ during daytime use.'
      : null
  );

  const patchTestAdvice = howToUse.patchTestRecommendation ||
    'Standard Dermatological Safety Protocol: Apply a pea-sized amount onto the clean inner forearm or side of jawline 24 hours prior to first facial application. If erythema, burning, or itching develops, discontinue use immediately.';

  const sourceRef = howToUse.sourceReference || 'Manufacturer Product Label & Indian Cosmetic Safety Guidelines';

  return (
    <section className="bg-white rounded-3xl border border-rose-200/90 p-6 sm:p-8 shadow-soft-lift space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-rose-100">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="text-[10px] font-bold tracking-widest uppercase text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
              Dermatologist-Aligned Usage Guide
            </span>
            <span className="text-espresso-300">•</span>
            <span className="text-[11px] font-semibold text-espresso-600">
              {category.toUpperCase()} • {subcategory}
            </span>
          </div>
          <h3 className="font-editorial text-2xl sm:text-3xl font-bold text-espresso-900">
            Application Ritual & Routine Integration
          </h3>
        </div>

        {/* Routine Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-ivory border border-rose-200 text-xs font-bold text-espresso-800">
            {routine === 'AM' ? (
              <Sun className="w-3.5 h-3.5 text-champagne-600" />
            ) : routine === 'PM' ? (
              <Moon className="w-3.5 h-3.5 text-indigo-500" />
            ) : (
              <div className="flex items-center space-x-0.5">
                <Sun className="w-3.5 h-3.5 text-champagne-600" />
                <Moon className="w-3.5 h-3.5 text-indigo-500" />
              </div>
            )}
            <span>{routine} Routine</span>
          </div>

          <div className="px-3 py-1.5 rounded-xl bg-rose-50 border border-rose-200 text-xs font-bold text-rose-700">
            Step {howToUse.stepNumber}: {stepName}
          </div>
        </div>
      </div>

      {/* Recommended Frequency & Application Steps */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-7 space-y-4">
          <div className="flex items-center space-x-2 text-xs font-bold text-espresso-900 uppercase tracking-wider">
            <Clock className="w-4 h-4 text-rose-500" />
            <span>Recommended Frequency: {frequency}</span>
          </div>

          <div className="p-4 sm:p-5 rounded-2xl bg-ivory-50 border border-rose-100/90 text-xs sm:text-sm text-espresso-800 leading-relaxed space-y-2">
            <h4 className="font-editorial text-base font-bold text-espresso-900">
              Step-by-Step Directions
            </h4>
            <p>{howToUse.instructions}</p>
          </div>

          {howToUse.precautions && (
            <div className="p-4 rounded-2xl bg-white border border-rose-200/90 text-xs text-espresso-700 space-y-1">
              <span className="font-bold text-rose-700 uppercase tracking-wider text-[10px] block">
                Precautions & Storage
              </span>
              <p>{howToUse.precautions}</p>
            </div>
          )}
        </div>

        {/* Cautions, Safety & Patch Test Protocol */}
        <div className="md:col-span-5 space-y-3">
          {/* Patch Test Warning Box */}
          <div className="p-4 rounded-2xl bg-champagne-50/80 border border-champagne-300 text-xs space-y-1.5 shadow-2xs">
            <div className="flex items-center space-x-1.5 text-champagne-800 font-bold">
              <AlertTriangle className="w-4 h-4 text-champagne-700 shrink-0" />
              <span>Mandatory Patch-Test Protocol</span>
            </div>
            <p className="text-espresso-800 leading-relaxed text-[11px]">
              {patchTestAdvice}
            </p>
          </div>

          {/* Sun Sensitivity Alert (if active) */}
          {sunWarning && (
            <div className="p-4 rounded-2xl bg-rose-50/80 border border-rose-200 text-xs space-y-1.5 shadow-2xs">
              <div className="flex items-center space-x-1.5 text-rose-700 font-bold">
                <Sun className="w-4 h-4 text-rose-600 shrink-0" />
                <span>Photosensitivity Precaution</span>
              </div>
              <p className="text-espresso-800 leading-relaxed text-[11px]">
                {sunWarning}
              </p>
            </div>
          )}

          {/* Evidence and Data Attribution */}
          <div className="p-3.5 rounded-2xl bg-white border border-rose-100 text-[11px] text-espresso-600 flex items-start space-x-2">
            <Info className="w-4 h-4 text-sage-600 shrink-0 mt-0.5" />
            <div>
              <strong className="text-espresso-800">Source Evidence:</strong> {sourceRef}.
              Does not replace individualized clinical dermatological advice.
            </div>
          </div>
        </div>
      </div>

      {/* Verified Key Actives & Functional Breakdown */}
      <div className="pt-5 border-t border-rose-100 space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="font-editorial text-lg font-bold text-espresso-900 flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-champagne-500" />
            <span>Verified Key Actives & Ingredient Intelligence</span>
          </h4>
          <span className="text-[11px] text-sage-700 font-semibold flex items-center space-x-1">
            <ShieldCheck className="w-3.5 h-3.5 text-sage-600" />
            <span>No Unsupported Medical Claims</span>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {actives.map((act, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-2xl bg-ivory-50 border border-rose-100 shadow-2xs space-y-1 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-espresso-900 flex items-center space-x-1">
                  <CheckCircle2 className="w-3 h-3 text-sage-600 shrink-0" />
                  <span>{act.name}</span>
                </span>
                {act.concentration && (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-100 text-rose-700">
                    {act.concentration}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-espresso-600 leading-relaxed">
                {act.benefit}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

