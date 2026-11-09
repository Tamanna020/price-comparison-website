import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Info,
  CheckCircle2,
  Search,
  FlaskConical,
  Sun,
  Moon,
  Plus,
  Trash2,
  RefreshCw,
} from 'lucide-react';
import {
  fetchMasterIngredients,
  checkIngredientCompatibility,
  checkRoutineSafety,
  type MasterIngredient,
  type IngredientCompatibilityResponse,
  type RoutineCheckerResponse,
  type RoutineCheckerStepInput,
} from '../utils/api';

export const IngredientIntelligencePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'matrix' | 'routine' | 'encyclopedia'>('matrix');

  // Master Ingredients State
  const [ingredients, setIngredients] = useState<MasterIngredient[]>([]);
  const [isLoadingIngredients, setIsLoadingIngredients] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Pairwise Matrix State
  const [selectedActives, setSelectedActives] = useState<string[]>(['retinol', 'glycolic_acid']);
  const [compatibilityResult, setCompatibilityResult] = useState<IngredientCompatibilityResponse | null>(null);
  const [isEvaluatingMatrix, setIsEvaluatingMatrix] = useState(false);

  // Routine Checker State
  const [amSteps, setAmSteps] = useState<RoutineCheckerStepInput[]>([
    { step_name: 'Hydrating Face Wash', key_ingredients: ['Glycerin'] },
    { step_name: '15% Vitamin C Glow Serum', key_ingredients: ['Vitamin C'] },
    { step_name: 'Barrier Gel Moisturizer', key_ingredients: ['Hyaluronic Acid'] },
    { step_name: 'Broad-Spectrum Sunscreen SPF 50+', key_ingredients: ['Tinosorb M'] },
  ]);

  const [pmSteps, setPmSteps] = useState<RoutineCheckerStepInput[]>([
    { step_name: 'Gentle Cleansing Balm', key_ingredients: [] },
    { step_name: '0.3% Retinol Night Serum', key_ingredients: ['Retinol'] },
    { step_name: 'Ceramides Barrier Cream', key_ingredients: ['Ceramides'] },
  ]);

  const [routineResult, setRoutineResult] = useState<RoutineCheckerResponse | null>(null);
  const [isCheckingRoutine, setIsCheckingRoutine] = useState(false);
  const [newAmStep, setNewAmStep] = useState({ name: '', active: 'niacinamide' });
  const [newPmStep, setNewPmStep] = useState({ name: '', active: 'salicylic_acid' });

  // Initial Data Fetch
  useEffect(() => {
    async function load() {
      setIsLoadingIngredients(true);
      const res = await fetchMasterIngredients();
      if (res.success && res.data) {
        setIngredients(res.data.ingredients);
      }
      setIsLoadingIngredients(false);
    }
    load();
  }, []);

  // Evaluate Pairwise Matrix
  useEffect(() => {
    async function evalMatrix() {
      if (selectedActives.length < 2) {
        setCompatibilityResult(null);
        return;
      }
      setIsEvaluatingMatrix(true);
      const res = await checkIngredientCompatibility(selectedActives);
      if (res.success && res.data) {
        setCompatibilityResult(res.data);
      }
      setIsEvaluatingMatrix(false);
    }
    evalMatrix();
  }, [selectedActives]);

  // Evaluate Routine Checker
  const handleCheckRoutine = async () => {
    setIsCheckingRoutine(true);
    const res = await checkRoutineSafety(amSteps, pmSteps);
    if (res.success && res.data) {
      setRoutineResult(res.data);
    }
    setIsCheckingRoutine(false);
  };

  useEffect(() => {
    handleCheckRoutine();
  }, []);

  const toggleActiveSelection = (id: string) => {
    setSelectedActives((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleAddAmStep = () => {
    if (!newAmStep.name.trim()) return;
    setAmSteps((prev) => [
      ...prev,
      { step_name: newAmStep.name.trim(), key_ingredients: [newAmStep.active] },
    ]);
    setNewAmStep({ name: '', active: 'niacinamide' });
  };

  const handleAddPmStep = () => {
    if (!newPmStep.name.trim()) return;
    setPmSteps((prev) => [
      ...prev,
      { step_name: newPmStep.name.trim(), key_ingredients: [newPmStep.active] },
    ]);
    setNewPmStep({ name: '', active: 'salicylic_acid' });
  };

  const removeAmStep = (idx: number) => {
    setAmSteps((prev) => prev.filter((_, i) => i !== idx));
  };

  const removePmStep = (idx: number) => {
    setPmSteps((prev) => prev.filter((_, i) => i !== idx));
  };

  // Filter Encyclopedia
  const filteredIngredients = ingredients.filter((ing) => {
    const matchesSearch =
      ing.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ing.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ing.what_it_does.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat =
      selectedCategory === 'all' ||
      ing.category.toLowerCase().includes(selectedCategory.toLowerCase());
    return matchesSearch && matchesCat;
  });

  return (
    <div className="min-h-screen bg-ivory text-espresso-900 pb-20">
      {/* Header Banner */}
      <section className="bg-gradient-to-b from-rose-100/60 via-ivory to-ivory border-b border-rose-200/50 pt-10 pb-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-rose-200/60 border border-rose-300/60 text-espresso-800 text-xs font-semibold uppercase tracking-wider mb-3">
                <FlaskConical className="w-3.5 h-3.5 text-rose-600" />
                <span>Phase 10 Intelligence • Scientific Skincare Matrix</span>
              </div>
              <h1 className="font-editorial text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-espresso-900">
                Ingredient Compatibility & <span className="italic font-normal text-rose-600">Routine Safety</span>
              </h1>
              <p className="mt-2 text-espresso-600 text-sm sm:text-base max-w-2xl">
                Clinical dermatology intelligence designed to prevent active clashes, detect duplicate overload, and optimize AM/PM layering for healthy barrier repair.
              </p>
            </div>

            {/* Tab Selector */}
            <div className="flex bg-white/90 p-1.5 rounded-xl border border-rose-200 shadow-soft-lift self-start md:self-auto">
              <button
                onClick={() => setActiveTab('matrix')}
                className={`px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  activeTab === 'matrix'
                    ? 'bg-rose-500 text-white shadow-xs font-semibold'
                    : 'text-espresso-700 hover:text-rose-600'
                }`}
              >
                Clash Matrix
              </button>
              <button
                onClick={() => setActiveTab('routine')}
                className={`px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  activeTab === 'routine'
                    ? 'bg-rose-500 text-white shadow-xs font-semibold'
                    : 'text-espresso-700 hover:text-rose-600'
                }`}
              >
                Routine Checker
              </button>
              <button
                onClick={() => setActiveTab('encyclopedia')}
                className={`px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  activeTab === 'encyclopedia'
                    ? 'bg-rose-500 text-white shadow-xs font-semibold'
                    : 'text-espresso-700 hover:text-rose-600'
                }`}
              >
                Encyclopedia
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        {/* ========================================================= */}
        {/* TAB 1: PAIRWISE CLASH & COMPATIBILITY MATRIX              */}
        {/* ========================================================= */}
        {activeTab === 'matrix' && (
          <div className="space-y-8">
            {/* Actives Picker Card */}
            <div className="bg-white rounded-2xl border border-rose-200/70 p-6 shadow-soft-lift">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-serif font-bold text-espresso-900">
                    Select Actives to Test Pairing
                  </h2>
                  <p className="text-xs text-espresso-500">
                    Choose 2 or more ingredients to evaluate their dermatological synergy or irritation risk.
                  </p>
                </div>
                <button
                  onClick={() => setSelectedActives(['retinol', 'glycolic_acid'])}
                  className="text-xs text-rose-600 hover:underline font-medium"
                >
                  Reset Defaults
                </button>
              </div>

              {/* Active Chips */}
              <div className="flex flex-wrap gap-2">
                {ingredients.map((ing) => {
                  const isSelected = selectedActives.includes(ing.id);
                  return (
                    <button
                      key={ing.id}
                      onClick={() => toggleActiveSelection(ing.id)}
                      className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all border ${
                        isSelected
                          ? 'bg-rose-600 text-white border-rose-600 shadow-xs'
                          : 'bg-ivory/80 text-espresso-700 border-rose-200/80 hover:border-rose-400'
                      }`}
                    >
                      {ing.name}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Results Display */}
            {isEvaluatingMatrix ? (
              <div className="p-12 text-center text-espresso-500">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto text-rose-500 mb-2" />
                <p className="text-sm">Evaluating active ingredient chemistry...</p>
              </div>
            ) : compatibilityResult ? (
              <div className="space-y-6">
                {/* Score Banner */}
                <div
                  className={`p-6 rounded-2xl border ${
                    compatibilityResult.overall_status === 'caution'
                      ? 'bg-amber-50/70 border-amber-300'
                      : compatibilityResult.overall_status === 'moderate'
                      ? 'bg-blue-50/70 border-blue-200'
                      : 'bg-emerald-50/70 border-emerald-300'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-start space-x-3">
                      {compatibilityResult.overall_status === 'caution' ? (
                        <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
                      ) : compatibilityResult.overall_status === 'moderate' ? (
                        <Info className="w-6 h-6 text-blue-600 shrink-0 mt-0.5" />
                      ) : (
                        <ShieldCheck className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
                      )}
                      <div>
                        <h3 className="font-serif font-bold text-lg text-espresso-900">
                          {compatibilityResult.overall_status === 'caution'
                            ? 'Active Ingredient Clash Detected'
                            : compatibilityResult.overall_status === 'moderate'
                            ? 'Moderate Compatibility — Buffer Recommended'
                            : 'Synergistic & Barrier-Safe Pairing'}
                        </h3>
                        <p className="text-sm text-espresso-700 mt-0.5">
                          {compatibilityResult.summary}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3 shrink-0">
                      <div className="text-right">
                        <span className="text-[10px] uppercase tracking-wider text-espresso-500 font-bold block">
                          Safety Rating
                        </span>
                        <span className="text-2xl font-bold font-serif text-espresso-900">
                          {compatibilityResult.safety_score} / 100
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Warnings List */}
                {compatibilityResult.warnings.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="font-serif text-base font-bold text-espresso-900 flex items-center space-x-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      <span>Dermatological Clashes ({compatibilityResult.warnings.length})</span>
                    </h3>

                    {compatibilityResult.warnings.map((warn, i) => (
                      <div
                        key={i}
                        className="bg-white rounded-xl border border-rose-200/80 p-5 shadow-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900">
                            {warn.severity.replace(/_/g, ' ')}
                          </span>
                          <span className="text-xs text-espresso-500 font-mono">
                            {warn.ingredient_a} + {warn.ingredient_b}
                          </span>
                        </div>

                        <h4 className="font-serif font-bold text-base text-espresso-900 mt-2">
                          {warn.title}
                        </h4>
                        <p className="text-sm text-espresso-700 mt-1">{warn.explanation}</p>

                        <div className="mt-3 pt-3 border-t border-rose-100 text-xs grid sm:grid-cols-2 gap-3">
                          <div className="bg-ivory/60 p-2.5 rounded-lg border border-rose-100">
                            <span className="font-semibold text-espresso-900 block mb-0.5">
                              Scientific Rationale:
                            </span>
                            <span className="text-espresso-600">{warn.scientific_rationale}</span>
                          </div>
                          <div className="bg-rose-50/60 p-2.5 rounded-lg border border-rose-200">
                            <span className="font-semibold text-rose-900 block mb-0.5">
                              Clinical Separation Advice:
                            </span>
                            <span className="text-rose-800">{warn.routine_separation_advice}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Synergies List */}
                {compatibilityResult.synergies.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="font-serif text-base font-bold text-espresso-900 flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Synergistic Pairings ({compatibilityResult.synergies.length})</span>
                    </h3>

                    {compatibilityResult.synergies.map((syn, i) => (
                      <div
                        key={i}
                        className="bg-white rounded-xl border border-emerald-200/80 p-5 shadow-xs"
                      >
                        <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900">
                          Synergistic Pair
                        </span>
                        <h4 className="font-serif font-bold text-base text-espresso-900 mt-2">
                          {syn.title}
                        </h4>
                        <p className="text-sm text-espresso-700 mt-1">{syn.explanation}</p>
                        <p className="text-xs text-emerald-800 mt-2 font-medium">
                          💡 Recommended Regimen: {syn.recommendation}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 2: AM / PM ROUTINE OVERLOAD & SAFETY CHECKER          */}
        {/* ========================================================= */}
        {activeTab === 'routine' && (
          <div className="space-y-8">
            {/* Routine Simulator Panel */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Morning (AM) Column */}
              <div className="bg-white rounded-2xl border border-rose-200/70 p-5 shadow-soft-lift flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-rose-100 mb-4">
                    <div className="flex items-center space-x-2">
                      <Sun className="w-5 h-5 text-amber-500" />
                      <h3 className="font-serif font-bold text-base text-espresso-900">
                        Morning (AM) Routine
                      </h3>
                    </div>
                    <span className="text-xs text-espresso-500">{amSteps.length} Steps</span>
                  </div>

                  <div className="space-y-2.5">
                    {amSteps.map((step, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 rounded-xl bg-ivory/60 border border-rose-100/80"
                      >
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-bold text-rose-500">{idx + 1}.</span>
                            <span className="text-sm font-medium text-espresso-900">
                              {step.step_name}
                            </span>
                          </div>
                          {step.key_ingredients && step.key_ingredients.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1 pl-4">
                              {step.key_ingredients.map((ing, i) => (
                                <span
                                  key={i}
                                  className="text-[10px] px-2 py-0.5 rounded-full bg-rose-100/70 text-rose-800 font-medium"
                                >
                                  {ing}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => removeAmStep(idx)}
                          className="text-espresso-400 hover:text-rose-600 p-1"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Add Step Input */}
                <div className="mt-4 pt-3 border-t border-rose-100 flex gap-2">
                  <input
                    type="text"
                    value={newAmStep.name}
                    onChange={(e) => setNewAmStep((prev) => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g. Niacinamide Serum"
                    className="flex-1 text-xs px-3 py-2 rounded-lg border border-rose-200 focus:outline-rose-500 bg-white"
                  />
                  <select
                    value={newAmStep.active}
                    onChange={(e) => setNewAmStep((prev) => ({ ...prev, active: e.target.value }))}
                    className="text-xs px-2 py-2 rounded-lg border border-rose-200 bg-white"
                  >
                    <option value="niacinamide">Niacinamide</option>
                    <option value="vitamin_c">Vitamin C</option>
                    <option value="hyaluronic_acid">Hyaluronic</option>
                    <option value="salicylic_acid">Salicylic Acid</option>
                    <option value="uv_filters">Sunscreen (SPF)</option>
                    <option value="retinol">Retinol</option>
                  </select>
                  <button
                    onClick={handleAddAmStep}
                    className="px-3 py-2 rounded-lg bg-rose-500 hover:bg-rose-600 text-white text-xs font-medium"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Evening (PM) Column */}
              <div className="bg-white rounded-2xl border border-rose-200/70 p-5 shadow-soft-lift flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-rose-100 mb-4">
                    <div className="flex items-center space-x-2">
                      <Moon className="w-5 h-5 text-indigo-500" />
                      <h3 className="font-serif font-bold text-base text-espresso-900">
                        Evening (PM) Routine
                      </h3>
                    </div>
                    <span className="text-xs text-espresso-500">{pmSteps.length} Steps</span>
                  </div>

                  <div className="space-y-2.5">
                    {pmSteps.map((step, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 rounded-xl bg-ivory/60 border border-rose-100/80"
                      >
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-bold text-indigo-500">{idx + 1}.</span>
                            <span className="text-sm font-medium text-espresso-900">
                              {step.step_name}
                            </span>
                          </div>
                          {step.key_ingredients && step.key_ingredients.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1 pl-4">
                              {step.key_ingredients.map((ing, i) => (
                                <span
                                  key={i}
                                  className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-100/70 text-indigo-800 font-medium"
                                >
                                  {ing}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => removePmStep(idx)}
                          className="text-espresso-400 hover:text-rose-600 p-1"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Add Step Input */}
                <div className="mt-4 pt-3 border-t border-rose-100 flex gap-2">
                  <input
                    type="text"
                    value={newPmStep.name}
                    onChange={(e) => setNewPmStep((prev) => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g. Glycolic Acid Peel"
                    className="flex-1 text-xs px-3 py-2 rounded-lg border border-rose-200 focus:outline-rose-500 bg-white"
                  />
                  <select
                    value={newPmStep.active}
                    onChange={(e) => setNewPmStep((prev) => ({ ...prev, active: e.target.value }))}
                    className="text-xs px-2 py-2 rounded-lg border border-rose-200 bg-white"
                  >
                    <option value="retinol">Retinol</option>
                    <option value="glycolic_acid">Glycolic Acid</option>
                    <option value="salicylic_acid">Salicylic Acid</option>
                    <option value="ceramides">Ceramides</option>
                    <option value="niacinamide">Niacinamide</option>
                    <option value="peptides">Peptides</option>
                  </select>
                  <button
                    onClick={handleAddPmStep}
                    className="px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Run Analysis Trigger */}
            <div className="flex justify-center">
              <button
                onClick={handleCheckRoutine}
                disabled={isCheckingRoutine}
                className="px-6 py-3 rounded-full bg-rose-500 hover:bg-rose-600 text-white font-medium text-sm shadow-soft-lift flex items-center space-x-2 transition-all transform hover:scale-105"
              >
                <Sparkles className="w-4 h-4" />
                <span>{isCheckingRoutine ? 'Analyzing Regimen...' : 'Re-Analyze Routine Safety'}</span>
              </button>
            </div>

            {/* Analysis Results */}
            {routineResult && (
              <div className="bg-white rounded-2xl border border-rose-200/80 p-6 shadow-soft-lift space-y-6">
                {/* Header Assessment */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-rose-100 gap-4">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-espresso-500">
                      Routine Irritation Assessment
                    </span>
                    <h3 className="font-serif font-bold text-2xl text-espresso-900 mt-1">
                      {routineResult.safety_rating}
                    </h3>
                    <p className="text-xs text-espresso-600 mt-1">
                      {routineResult.sunscreen_compliant
                        ? '✓ Daytime SPF 50+ compliance verified.'
                        : '⚠️ Daytime Broad-Spectrum Sunscreen Missing!'}
                    </p>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-espresso-500 block">
                        Irritation Risk
                      </span>
                      <span
                        className={`text-lg font-bold ${
                          routineResult.irritation_risk === 'High'
                            ? 'text-rose-600'
                            : routineResult.irritation_risk === 'Moderate'
                            ? 'text-amber-600'
                            : 'text-emerald-600'
                        }`}
                      >
                        {routineResult.irritation_risk}
                      </span>
                    </div>

                    <div className="w-16 h-16 rounded-full bg-rose-50 border-2 border-rose-300 flex items-center justify-center">
                      <span className="font-serif font-bold text-lg text-espresso-900">
                        {routineResult.overall_score}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Overload Alert if detected */}
                {routineResult.active_overloads.length > 0 && (
                  <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center space-x-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                      <span>Duplicate Active Ingredient Overload Detected</span>
                    </h4>
                    {routineResult.active_overloads.map((ov, i) => (
                      <div key={i} className="text-xs text-amber-800">
                        <strong>{ov.ingredient}:</strong> {ov.risk}
                        <p className="mt-0.5 text-amber-700">{ov.recommendation}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Conflict Warnings */}
                {routineResult.conflicts.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-serif font-bold text-sm text-espresso-900">
                      Identified Regimen Friction Points
                    </h4>
                    {routineResult.conflicts.map((conf, i) => (
                      <div
                        key={i}
                        className="p-3.5 rounded-xl bg-ivory/60 border border-rose-100 flex items-start space-x-3"
                      >
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div className="text-xs">
                          <span className="font-bold text-espresso-900">{conf.title}</span>
                          <p className="text-espresso-600 mt-0.5">{conf.description}</p>
                          <p className="text-rose-700 font-medium mt-1">
                            Recommendation: {conf.recommendation}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Separation Regimen */}
                <div className="pt-4 border-t border-rose-100">
                  <h4 className="font-serif font-bold text-sm text-espresso-900 mb-2">
                    Recommended Separation Regimen (Skin Cycling)
                  </h4>
                  <ul className="space-y-1 text-xs text-espresso-600">
                    {routineResult.optimization_steps.map((step, i) => (
                      <li key={i} className="flex items-center space-x-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 3: MASTER INGREDIENT ENCYCLOPEDIA                     */}
        {/* ========================================================= */}
        {activeTab === 'encyclopedia' && (
          <div className="space-y-6">
            {/* Search & Filter Bar */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-espresso-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search cosmetic actives (e.g. Niacinamide, Retinol, Salicylic)..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-rose-200 bg-white text-xs sm:text-sm focus:outline-rose-500"
                />
              </div>

              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-4 py-2.5 rounded-xl border border-rose-200 bg-white text-xs sm:text-sm text-espresso-700"
              >
                <option value="all">All Categories</option>
                <option value="Acid">Exfoliating Acids</option>
                <option value="Retinoid">Retinoids</option>
                <option value="Antioxidant">Antioxidants</option>
                <option value="Barrier">Barrier & Lipids</option>
                <option value="Humectant">Humectants</option>
                <option value="Filter">UV Filters</option>
              </select>
            </div>

            {/* Encyclopedia Cards Grid */}
            {isLoadingIngredients ? (
              <div className="p-12 text-center text-espresso-500 bg-white rounded-2xl border border-rose-100">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto text-rose-500 mb-2" />
                <p className="text-sm">Loading cosmetic active ingredients database...</p>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {filteredIngredients.map((ing) => (
                  <div
                    key={ing.id}
                    className="bg-white rounded-2xl border border-rose-200/80 p-5 shadow-soft-lift flex flex-col justify-between hover:border-rose-400 transition-colors"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-rose-100 text-rose-800">
                          {ing.category}
                        </span>
                        <span
                          className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                            ing.evidence_level === 'established'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {ing.evidence_level.toUpperCase()} EVIDENCE
                        </span>
                      </div>

                      <h3 className="font-serif font-bold text-lg text-espresso-900">{ing.name}</h3>
                      <p className="text-[11px] text-espresso-500 font-mono mb-2">
                        INCI: {ing.inci_name}
                      </p>
                      <p className="text-xs text-espresso-700 line-clamp-3 mb-3">
                        {ing.description}
                      </p>

                      <div className="text-[11px] space-y-1.5 pt-3 border-t border-rose-100">
                        <div>
                          <strong className="text-espresso-900">What it does: </strong>
                          <span className="text-espresso-600">{ing.what_it_does}</span>
                        </div>
                        <div>
                          <strong className="text-espresso-900">Optimal pH: </strong>
                          <span className="text-espresso-600 font-mono">{ing.optimal_ph}</span>
                        </div>
                        <div>
                          <strong className="text-espresso-900">Target Concentration: </strong>
                          <span className="text-espresso-600 font-mono">
                            {ing.typical_concentration}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-rose-100">
                      <span className="text-[10px] uppercase font-bold text-espresso-400 block mb-1">
                        Key Benefits
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {ing.benefits.slice(0, 3).map((b, i) => (
                          <span
                            key={i}
                            className="text-[10px] px-2 py-0.5 rounded-md bg-ivory text-espresso-700 border border-rose-100"
                          >
                            {b}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* MANDATORY MEDICAL DISCLAIMER BANNER                       */}
        {/* ========================================================= */}
        <div className="mt-12 p-4 rounded-xl bg-ivory border border-rose-200/80 text-xs text-espresso-600 flex items-start space-x-3">
          <Info className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
          <p>
            <strong>PriceWise AI Cosmetic Guidance Notice:</strong> Skincare routine advice, active
            ingredient compatibility, and climate recommendations are educational cosmetic
            suggestions based on published dermatological literature. They do not constitute
            medical diagnoses, dermatological prescriptions, or medical advice. If irritation,
            persistent erythema, or adverse reactions occur, discontinue use immediately and
            consult a dermatologist.
          </p>
        </div>
      </main>
    </div>
  );
};
