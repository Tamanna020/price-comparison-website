import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  RotateCcw,
  Info,
  Brain,
  Zap,
} from 'lucide-react';
import type { IngredientInfo, IngredientAnalysisResponse } from '../utils/api';
import { analyzeProductIngredients } from '../utils/api';

interface IngredientAnalysisSectionProps {
  productId: number;
  productName: string;
  brand: string;
  category: string;
  subcategory: string;
}

export const IngredientAnalysisSection: React.FC<IngredientAnalysisSectionProps> = ({
  productId,
  productName: _productName,
  brand: _brand,
  category,
  subcategory,
}) => {
  const [analysis, setAnalysis] = useState<IngredientAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<'ai' | 'heuristic' | null>(null);
  const isAI = source === 'ai';

  const fetchAnalysis = async (force = false) => {
    setLoading(true);
    setError(null);
    const res = await analyzeProductIngredients(productId, force);
    if (res.success && res.data) {
      setAnalysis(res.data);
      setSource(res.data.extraction_source === 'gemini_model' ? 'ai' : 'heuristic');
    } else {
      setError(res.error || 'Failed to analyze ingredients');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchAnalysis();
  }, [productId]);

  if (!analysis && !loading && !error) return null;

  // // // // // // // // // // // // // const isAI = source === 'gemini_model';
  const confidence = analysis?.confidence_score ?? 0;

  return (
    <section className="bg-white rounded-3xl border border-rose-200/90 p-6 sm:p-8 shadow-soft-lift space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-rose-100">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="text-[10px] font-bold tracking-widest uppercase text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
              AI Ingredient Intelligence
            </span>
            <span className="text-espresso-300">•</span>
            <span className="text-[11px] font-semibold text-espresso-600">
              {category.toUpperCase()} • {subcategory}
            </span>
          </div>
          <h3 className="font-editorial text-2xl sm:text-3xl font-bold text-espresso-900">
            Ingredient Analysis & Functional Breakdown
          </h3>
        </div>

        {/* Source & Confidence Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold">
            {isAI ? (
              <>
                <Brain className="w-3.5 h-3.5 text-rose-500" />
                <span className="text-rose-700 border-rose-200 bg-rose-50">AI Analyzed</span>
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5 text-champagne-600" />
                <span className="text-champagne-800 border-champagne-300 bg-champagne-50">Heuristic Fallback</span>
              </>
            )}
          </div>
          {analysis && confidence > 0 && (
            <div className="px-3 py-1.5 rounded-xl bg-ivory border border-rose-100 text-xs font-bold text-espresso-800">
              Confidence: {Math.round(confidence * 100)}%
            </div>
          )}
          <button
            onClick={() => fetchAnalysis(true)}
            disabled={loading}
            className="px-3 py-1.5 rounded-xl border border-rose-200 bg-white hover:bg-rose-50/70 text-espresso-700 text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-2xs disabled:opacity-50"
            title="Re-analyze with fresh data"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-rose-600' : ''}`} />
            <span>{loading ? 'Analyzing...' : 'Re-analyze'}</span>
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && !analysis && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-sm text-rose-700 flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading State */}
      {loading && !analysis && (
        <div className="space-y-3 animate-pulse">
          <div className="h-8 bg-rose-100 rounded-xl w-3/4" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-24 bg-rose-50 rounded-2xl border border-rose-100" />
            ))}
          </div>
        </div>
      )}

      {analysis && (
        <>
          {/* Key Actives */}
          {analysis.key_actives && analysis.key_actives.length > 0 && (
            <div className="p-4 rounded-2xl bg-gradient-to-r from-champagne-50/70 to-rose-50/70 border border-champagne-200 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-bold text-espresso-900 uppercase tracking-wider">
                <Sparkles className="w-4 h-4 text-champagne-600 shrink-0" />
                <span>Key Actives Identified</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {analysis.key_actives.map((active, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 rounded-xl bg-white/80 border border-champagne-300 text-sm font-semibold text-champagne-800 shadow-xs"
                  >
                    {active}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Ingredient Cards Grid */}
          <div className="pt-5 border-t border-rose-100 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-editorial text-lg font-bold text-espresso-900 flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-champagne-500" />
                <span>Ingredient Intelligence Breakdown</span>
              </h4>
              <span className="text-[11px] text-sage-700 font-semibold flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5 text-sage-600" />
                <span>No Unsupported Medical Claims</span>
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {analysis.ingredients.map((ing, idx) => (
                <IngredientCard
                  key={idx}
                  ingredient={ing}
                  isAI={isAI}
                />
              ))}
            </div>
          </div>

          {/* Potential Conflicts */}
          {analysis.potential_conflicts && analysis.potential_conflicts.length > 0 && (
            <div className="pt-5 border-t border-rose-100 space-y-3">
              <h4 className="font-editorial text-lg font-bold text-espresso-900 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Potential Ingredient Conflicts</span>
              </h4>
              <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs space-y-1.5">
                {analysis.potential_conflicts.map((conflict, idx) => (
                  <p key={idx} className="text-espresso-800 leading-relaxed text-[11px] flex items-start space-x-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0 mt-1.5" />
                    <span>{conflict}</span>
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Routine Compatibility */}
          {analysis.routine_compatibility && (
            Object.keys(analysis.routine_compatibility).length > 0 && (
              <div className="pt-5 border-t border-rose-100 space-y-3">
                <h4 className="font-editorial text-lg font-bold text-espresso-900 flex items-center space-x-2">
                  <Info className="w-4 h-4 text-sage-600" />
                  <span>Routine Compatibility</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {Object.entries(analysis.routine_compatibility).map(([routine, ingredients]) => (
                    <div
                      key={routine}
                      className="p-3.5 rounded-2xl bg-ivory-50 border border-rose-100 shadow-2xs space-y-1 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-espresso-900 flex items-center space-x-1">
                          {routine === 'AM' ? (
                            <span className="text-champagne-600">☀</span>
                          ) : (
                            <span className="text-indigo-500">🌙</span>
                          )}
                          <span>{routine} Routine</span>
                        </span>
                      </div>
                      <p className="text-[11px] text-espresso-600 leading-relaxed">
                        {ingredients.length > 0
                          ? ingredients.join(', ')
                          : 'No specific actives recommended for this routine'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )
          )}

          {/* Data Attribution */}
          <div className="pt-5 border-t border-rose-100">
            <div className="p-3.5 rounded-2xl bg-white border border-rose-100 text-[11px] text-espresso-600 flex items-start space-x-2">
              <Info className="w-4 h-4 text-sage-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-espresso-800">Source:</strong>{' '}
                {isAI
                  ? 'Gemini AI analysis of product specifications & cosmetic ingredient databases. '
                  : 'Heuristic ingredient parsing from product label data. '}
                Does not replace individualized clinical dermatological advice.
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
};

// Ingredient Card Component
interface IngredientCardProps {
  ingredient: IngredientInfo;
  isAI: boolean;
}

const IngredientCard: React.FC<IngredientCardProps> = ({ ingredient, isAI: _isAI }) => {
  const safetyColors: Record<string, string> = {
    safe: 'bg-sage-100 text-sage-800 border-sage-300',
    caution: 'bg-amber-100 text-amber-800 border-amber-300',
    avoid: 'bg-rose-100 text-rose-800 border-rose-300',
  };

  return (
    <div className="p-3.5 rounded-2xl bg-ivory-50 border border-rose-100 shadow-2xs space-y-1 text-xs">
      <div className="flex items-center justify-between">
        <span className="font-bold text-espresso-900 flex items-center space-x-1">
          <CheckCircle2 className="w-3 h-3 text-sage-600 shrink-0" />
          <span>{ingredient.name}</span>
        </span>
        {ingredient.safety_rating && (
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${safetyColors[ingredient.safety_rating] || 'bg-ivory-100 text-espresso-700 border-rose-200'}`}>
            {ingredient.safety_rating.toUpperCase()}
          </span>
        )}
      </div>
      <p className="text-[11px] text-espresso-600 leading-relaxed">
        <strong>Function:</strong> {ingredient.function}
      </p>
      <p className="text-[11px] text-espresso-600 leading-relaxed">
        <strong>Benefits:</strong> {ingredient.benefits.join(', ') || 'General skin conditioning'}
      </p>
      {ingredient.concerns && ingredient.concerns.length > 0 && (
        <p className="text-[11px] text-amber-700 leading-relaxed">
          <strong>Concerns:</strong> {ingredient.concerns.join(', ')}
        </p>
      )}
      {ingredient.concentration_range && (
        <p className="text-[11px] text-champagne-700 leading-relaxed">
          <strong>Typical Range:</strong> {ingredient.concentration_range}
        </p>
      )}
      <div className="flex flex-wrap gap-1 mt-1">
        {ingredient.compatible_with?.slice(0, 3).map((comp, i) => (
          <span
            key={i}
            className="px-1.5 py-0.5 rounded bg-sage-100 text-sage-700 text-[10px] border border-sage-200"
          >
            + {comp}
          </span>
        ))}
        {ingredient.avoid_with?.slice(0, 2).map((avoid, i) => (
          <span
            key={i}
            className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 text-[10px] border border-rose-200"
          >
            ✕ {avoid}
          </span>
        ))}
      </div>
    </div>
  );
};

export default IngredientAnalysisSection;
