import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Sun,
  Moon,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  ArrowUp,
  ArrowDown,
  Trash2,
  Plus,
  Info,
  Clock,
  X,
  Zap,
  Brain,
  Target,
  Heart,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import type { Routine, RoutineItem } from '../types';
import {
  getUserRoutines,
  reorderRoutineItems,
  deleteRoutineItem,
  addRoutineItem,
} from '../utils/api';
import { generateBeautyRoutine } from '../utils/api';
// import { PRODUCTS_DATA } from '../data/products';

const CONCERNS_OPTIONS = [
  { id: 'acne', label: 'Acne & Breakouts' },
  { id: 'pigmentation', label: 'Hyperpigmentation' },
  { id: 'dryness', label: 'Dryness & Dehydration' },
  { id: 'oiliness', label: 'Oil Control' },
  { id: 'dullness', label: 'Dullness & Radiance' },
  { id: 'sensitivity', label: 'Sensitivity' },
  { id: 'aging', label: 'Fine Lines & Firmness' },
  { id: 'pores', label: 'Pore Refinement' },
];

const SKIN_TYPES = [
  { id: 'oily', label: 'Oily' },
  { id: 'dry', label: 'Dry' },
  { id: 'combination', label: 'Combination' },
  { id: 'normal', label: 'Normal' },
  { id: 'sensitive', label: 'Sensitive' },
  { id: 'unsure', label: 'Unsure' },
];

export const SmartRoutineBuilder: React.FC = () => {
  const { user, openAuthModal } = useAuth();

  const [routines, setRoutines] = useState<Routine[]>([]);
  const [activeRoutineType, setActiveRoutineType] = useState<'AM' | 'PM'>('AM');
  const [loading, setLoading] = useState(true);
  const [disclaimer, setDisclaimer] = useState<string>('');
  const [actionError, setActionError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  // AI Generator Modal State
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [genSkinType, setGenSkinType] = useState<'oily' | 'dry' | 'combination' | 'normal' | 'sensitive' | 'unsure'>('combination');
  const [genConcerns, setGenConcerns] = useState<string[]>([]);
  const [genBudget, setGenBudget] = useState<[number, number]>([300, 3000]);
  const [genUseExisting, setGenUseExisting] = useState(true);
  const [genSource, setGenSource] = useState<'ai' | 'heuristic' | null>(null);

  // Manual Add Step Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [stepName, setStepName] = useState('');
  const [category, setCategory] = useState('Face Wash');
  const [customProductName, setCustomProductName] = useState('');
  const [usageInstructions, setUsageInstructions] = useState('');
  const [precautions, setPrecautions] = useState('');
  const [submittingStep, setSubmittingStep] = useState(false);

  const loadRoutines = useCallback(async () => {
    setLoading(true);
    setActionError(null);
    const res = await getUserRoutines();
    if (res.routines) {
      setRoutines(res.routines);
    }
    if (res.disclaimer) {
      setDisclaimer(res.disclaimer);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (user) {
      loadRoutines();
    } else {
      setLoading(false);
    }
  }, [user, loadRoutines]);

  const activeRoutine = routines.find((r) => r.routine_type === activeRoutineType) || routines[0];

  const handleMoveStep = async (itemIndex: number, direction: 'up' | 'down') => {
    if (!activeRoutine || !activeRoutine.items) return;
    const items = [...activeRoutine.items];
    const targetIndex = direction === 'up' ? itemIndex - 1 : itemIndex + 1;
    if (targetIndex < 0 || targetIndex >= items.length) return;

    const [movedItem] = items.splice(itemIndex, 1);
    items.splice(targetIndex, 0, movedItem);

    const updatedRoutine = { ...activeRoutine, items };
    setRoutines((prev) => prev.map((r) => (r.id === activeRoutine.id ? updatedRoutine : r)));

    const itemOrder = items.map((i) => i.id);
    const res = await reorderRoutineItems(activeRoutine.id, itemOrder);
    if (!res.success) {
      setActionError(res.error || 'Failed to reorder steps');
      loadRoutines();
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    if (!activeRoutine) return;
    if (!window.confirm('Remove this step from your routine?')) return;

    const updatedItems = activeRoutine.items.filter((i) => i.id !== itemId);
    setRoutines((prev) => prev.map((r) => (r.id === activeRoutine.id ? { ...r, items: updatedItems } : r)));

    const res = await deleteRoutineItem(activeRoutine.id, itemId);
    if (!res.success) {
      setActionError(res.error || 'Failed to delete step');
      loadRoutines();
    }
  };

  const handleAddStep = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRoutine) return;
    if (!stepName.trim()) {
      setActionError('Step name is required');
      return;
    }

    setSubmittingStep(true);
    const res = await addRoutineItem(activeRoutine.id, {
      step_name: stepName.trim(),
      category: category.trim(),
      custom_product_name: customProductName.trim() || undefined,
      usage_instructions: usageInstructions.trim() || undefined,
      precautions: precautions.trim() || undefined,
    });

    if (res.success) {
      setIsAddModalOpen(false);
      setStepName('');
      setCustomProductName('');
      setUsageInstructions('');
      setPrecautions('');
      loadRoutines();
    } else {
      setActionError(res.error || 'Failed to add step');
    }
    setSubmittingStep(false);
  };

  const handleGenerateRoutine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRoutine) return;
    if (genConcerns.length === 0) {
      setActionError('Please select at least one skin concern');
      return;
    }

    setGenerating(true);
    setActionError(null);

    const existingProductIds = genUseExisting && activeRoutine.items
      ? activeRoutine.items.filter((i) => i.product_id).map((i) => i.product_id!)
      : [];

    const res = await generateBeautyRoutine(activeRoutineType, {
      skin_type: genSkinType,
      skin_concerns: genConcerns,
      existing_products: existingProductIds,
      budget_range: genBudget,
    });

    if (res.success && res.data) {
      const routine = res.data;
      setGenSource(routine.generation_source === 'gemini_model' ? 'ai' : 'heuristic');

      // Convert routine steps to routine items and add them
      for (const step of routine.steps) {
        if (step.product_id) {
          await addRoutineItem(activeRoutine.id, {
            step_name: step.step_name,
            category: step.category || '',
            product_id: step.product_id,
            usage_instructions: step.usage_instructions,
            precautions: step.precautions,
            key_ingredients: step.key_ingredients,
          });
        } else {
          await addRoutineItem(activeRoutine.id, {
            step_name: step.step_name,
            category: step.category || '',
            custom_product_name: step.product_name,
            usage_instructions: step.usage_instructions,
            precautions: step.precautions,
            key_ingredients: step.key_ingredients,
          });
        }
      }

      setIsGenerateModalOpen(false);
      setGenConcerns([]);
      loadRoutines();
    } else {
      setActionError(res.error || 'Failed to generate routine');
    }
    setGenerating(false);
  };

  const toggleConcern = (concernId: string) => {
    setGenConcerns((prev) =>
      prev.includes(concernId) ? prev.filter((c) => c !== concernId) : [...prev, concernId]
    );
  };

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="bg-white/80 border border-rose-200/80 rounded-3xl p-10 sm:p-14 shadow-soft-lift glass-panel max-w-xl mx-auto">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-rose-200 to-rose-400 mx-auto flex items-center justify-center text-ivory mb-5 shadow-xs">
            <Sparkles className="w-8 h-8" />
          </div>
          <h2 className="font-editorial text-3xl font-bold text-espresso-900 mb-2">
            Smart Routine Builder
          </h2>
          <p className="text-sm text-espresso-600 mb-8 leading-relaxed">
            Sign in to build AI-powered morning and evening skincare routines with ingredient compatibility checking,
            budget awareness, and personalized product matching.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => openAuthModal('login')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-rose-500 hover:bg-rose-600 text-ivory text-sm font-semibold shadow-md transition-all"
            >
              Sign In to Build Routines
            </button>
            <button
              onClick={() => openAuthModal('register')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white border border-rose-200 hover:border-rose-400 text-espresso-700 text-sm font-semibold transition-all"
            >
              Create Free Account
            </button>
          </div>
        </div>
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
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-rose-100 pb-6">
        <div>
          <div className="flex items-center space-x-2 text-rose-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" />
            <span>Smart Regimen Builder</span>
          </div>
          <h1 className="font-editorial text-3xl sm:text-4xl font-bold text-espresso-900">
            AI-Powered Skincare Routines
          </h1>
          <p className="text-sm text-espresso-600 mt-1">
            Build, optimize, and verify your {activeRoutineType} routine with Gemini AI ingredient intelligence.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsGenerateModalOpen(true)}
            disabled={generating}
            className="px-5 py-2.5 text-xs font-semibold text-ivory bg-rose-500 hover:bg-rose-600 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <Brain className="w-4 h-4" />
            <span>{generating ? 'Generating...' : 'Generate with AI'}</span>
          </button>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="px-5 py-2.5 text-xs font-semibold text-ivory bg-sage-600 hover:bg-sage-700 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Add Step Manually</span>
          </button>
        </div>
      </div>

      {/* Routine Type Tabs */}
      <div className="flex bg-white/70 p-1.5 rounded-2xl border border-rose-200/80 shadow-xs max-w-md">
        <button
          type="button"
          onClick={() => setActiveRoutineType('AM')}
          className={activeRoutineType === 'AM'
            ? 'flex-1 py-2.5 px-4 text-xs font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all bg-gradient-to-r from-amber-400 to-amber-500 text-ivory shadow-xs'
            : 'flex-1 py-2.5 px-4 text-xs font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all text-espresso-600 hover:text-amber-600'
          }>
          <Sun className="w-4 h-4" />
          <span>Morning Defense (AM)</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveRoutineType('PM')}
          className={activeRoutineType === 'PM'
            ? 'flex-1 py-2.5 px-4 text-xs font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all bg-gradient-to-r from-indigo-900 to-slate-900 text-ivory shadow-xs'
            : 'flex-1 py-2.5 px-4 text-xs font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all text-espresso-600 hover:text-indigo-900'
          }>
          <Moon className="w-4 h-4" />
          <span>Evening Repair (PM)</span>
        </button>
      </div>

      {/* Error alert */}
      {actionError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* AI Generation Result Banner */}
      {genSource && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-sage-50 to-rose-50 border border-sage-200 flex flex-wrap items-center justify-between gap-2 text-xs sm:text-sm animate-slide-in">
          <div className="flex items-center space-x-2 text-espresso-800">
            {genSource === 'ai' ? (
              <Brain className="w-4 h-4 text-rose-500 shrink-0" />
            ) : (
              <Zap className="w-4 h-4 text-champagne-600 shrink-0" />
            )}
            <span>
              Generated <strong>{activeRoutineType} routine</strong> with{" "}
              <span className={genSource === 'ai' ? 'text-rose-600' : 'text-champagne-600'}>
                {genSource === 'ai' ? 'Gemini AI' : 'Heuristic Fallback'}
              </span>
              . {genSource === 'ai' && <ShieldCheck className="w-3.5 h-3.5 text-sage-600 ml-1" />}
            </span>
          </div>
          <button
            onClick={() => setGenSource(null)}
            className="px-2 py-1 rounded-lg bg-white/80 border border-rose-200 text-espresso-600 hover:bg-rose-50"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Active Ingredient Conflict Warning Banner */}
      {activeRoutine?.conflicts && activeRoutine.conflicts.length > 0 && (
        <div className="space-y-3">
          {activeRoutine.conflicts.map((conflict, idx) => (
            <div
              key={idx}
              className="p-4 sm:p-5 rounded-2xl bg-amber-500/15 border border-amber-400 text-espresso-900 text-xs sm:text-sm flex items-start space-x-3.5 shadow-xs"
            >
              <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-amber-950 uppercase tracking-wide text-[11px] block">
                  Ingredient Conflict: {conflict.conflict_type.replace('_', ' ')}
                </span>
                <p className="text-xs text-espresso-800 font-medium mt-0.5">{conflict.description}</p>
                <p className="text-xs text-espresso-700 mt-1 italic">Recommendation: {conflict.recommendation}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Routine Steps List */}
      <div className="space-y-4">
        {(!activeRoutine || !activeRoutine.items || activeRoutine.items.length === 0) ? (
          <div className="p-12 text-center bg-white/60 border border-rose-100 rounded-3xl text-espresso-600 text-sm">
            <Sparkles className="w-8 h-8 text-rose-400 mx-auto mb-2 opacity-60" />
            <p className="font-semibold text-espresso-800">No steps in this routine yet.</p>
            <p className="text-xs text-espresso-500 mt-1">
              Click "Generate with AI" for a personalized regimen, or "Add Step Manually" to build step-by-step.
            </p>
          </div>
        ) : (
          activeRoutine.items.map((item: RoutineItem, idx: number) => (
            <motion.div
              key={item.id}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/90 border border-rose-100 rounded-3xl p-5 sm:p-6 shadow-xs hover:shadow-soft-lift transition-all glass-panel flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              {/* Step Information */}
              <div className="flex items-start space-x-4">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-rose-100 to-rose-200 border border-rose-300/60 flex items-center justify-center text-rose-700 font-serif font-bold text-base shrink-0 shadow-xs">
                  {idx + 1}
                </div>

                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center space-x-2 flex-wrap">
                    <span className="px-2.5 py-0.5 rounded-full bg-rose-50 border border-rose-200/60 text-[10px] font-bold text-rose-700 uppercase tracking-wider">
                      {item.category || 'Step'}
                    </span>
                    <h3 className="font-editorial text-lg font-bold text-espresso-900 truncate">
                      {item.step_name}
                    </h3>
                    {item.product_id && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sage-100 text-sage-700 border border-sage-200 flex items-center space-x-1">
                        <ShieldCheck className="w-2.5 h-2.5" />
                        <span>Catalog Linked</span>
                      </span>
                    )}
                  </div>

                  {item.custom_product_name && (
                    <p className="text-xs font-semibold text-espresso-700">
                      Product: <span className="text-rose-600">{item.custom_product_name}</span>
                    </p>
                  )}

                  {item.usage_instructions && (
                    <p className="text-xs text-espresso-600 flex items-center space-x-1.5 pt-0.5">
                      <Clock className="w-3.5 h-3.5 text-espresso-400 shrink-0" />
                      <span>{item.usage_instructions}</span>
                    </p>
                  )}

                  {item.precautions && (
                    <p className="text-[11px] text-amber-700 flex items-center space-x-1.5 pt-0.5">
                      <Info className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      <span>{item.precautions}</span>
                    </p>
                  )}

                  {item.key_ingredients && item.key_ingredients.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {item.key_ingredients.slice(0, 4).map((ing, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-champagne-50 text-champagne-700 text-[10px] border border-champagne-100">
                          {ing}
                        </span>
                    ))}



              )

                    </div>
                  )}
                </div>
              </div>

              {/* Step Controls (Reorder & Delete) */}
              <div className="flex items-center space-x-2 self-end sm:self-center">
                <button
                  type="button"
                  onClick={() => handleMoveStep(idx, 'up')}
                  disabled={idx === 0}
                  className="p-2 rounded-xl bg-white border border-rose-200 hover:border-rose-400 text-espresso-600 hover:text-rose-600 disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-xs"
                  aria-label="Move step up"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => handleMoveStep(idx, 'down')}
                  disabled={idx === activeRoutine.items.length - 1}
                  className="p-2 rounded-xl bg-white border border-rose-200 hover:border-rose-400 text-espresso-600 hover:text-rose-600 disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-xs"
                  aria-label="Move step down"
                >
                  <ArrowDown className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteItem(item.id)}
                  className="p-2 rounded-xl bg-white border border-rose-200 hover:border-rose-500 hover:bg-rose-50 text-espresso-400 hover:text-rose-600 transition-all shadow-xs"
                  aria-label="Remove step"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
           )))}
     </div>

      {/* Routine Summary & Stats */}
      {activeRoutine && activeRoutine.items && activeRoutine.items.length > 0 && (
        <div className="pt-4 border-t border-rose-100">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-white/80 border border-rose-100 shadow-xs">
              <div className="flex items-center space-x-2 text-xs text-espresso-500 mb-1">
                <Target className="w-4 h-4" />
                <span>Total Steps</span>
              </div>
              <p className="font-editorial text-3xl font-bold text-espresso-900">{activeRoutine.items.length}</p>
            </div>
            <div className="p-4 rounded-2xl bg-white/80 border border-rose-100 shadow-xs">
              <div className="flex items-center space-x-2 text-xs text-espresso-500 mb-1">
                <Heart className="w-4 h-4" />
                <span>Catalog Linked</span>
              </div>
              <p className="font-editorial text-3xl font-bold text-espresso-900">
                {activeRoutine.items.filter((i) => i.product_id).length} / {activeRoutine.items.length}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-white/80 border border-rose-100 shadow-xs">
              <div className="flex items-center space-x-2 text-xs text-espresso-500 mb-1">
                <Zap className="w-4 h-4" />
                <span>Conflicts</span>
              </div>
              <p className="font-editorial text-3xl font-bold text-espresso-900">
                {activeRoutine.conflicts?.length || 0}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Non-medical Cosmetic Disclaimer Banner */}
      <div className="p-4 sm:p-5 rounded-2xl bg-amber-500/10 border border-amber-300/60 text-espresso-800 text-xs sm:text-sm flex items-start space-x-3 mt-10">
        <ShieldCheck className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block text-espresso-900 mb-0.5">
            Cosmetic Guidance Notice
          </span>
          <p className="text-xs text-espresso-700 leading-relaxed">
            {disclaimer || 'Skincare routine steps and compatibility alerts are provided for cosmetic discovery and education only. They do not constitute dermatological or medical diagnosis. Discontinue use if irritation occurs and perform a patch test before introducing new active formulas.'}
          </p>
        </div>
      </div>

      {/* Modal: Generate Routine with AI */}
      {isGenerateModalOpen && (
        <>
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
          >
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsGenerateModalOpen(false)}
              className="fixed inset-0 bg-espresso-950/60 backdrop-blur-sm transition-opacity"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="relative w-full max-w-2xl bg-ivory border border-rose-200/80 rounded-3xl shadow-2xl overflow-hidden z-10 p-6 sm:p-8"
            >
              <div className="flex items-center justify-between pb-4 border-b border-rose-100">
                <h3 className="font-editorial text-2xl font-bold text-espresso-900">
                  Generate {activeRoutineType} Routine with AI
                </h3>
                <button
                  onClick={() => setIsGenerateModalOpen(false)}
                  className="p-1.5 rounded-full hover:bg-rose-100 text-espresso-500 hover:text-espresso-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleGenerateRoutine} className="mt-4 space-y-5">
                {/* Skin Type */}
                <div>
                  <label className="block text-xs font-semibold text-espresso-700 mb-2">Skin Type</label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                    {SKIN_TYPES.map((type) => (
                      <button
                        key={type.id}
                        type="button"
                        onClick={() => setGenSkinType(type.id as any)}
                        className={genSkinType === type.id
                          ? 'p-3 rounded-2xl border border-rose-400 bg-rose-50/70 shadow-xs text-center'
                          : 'p-3 rounded-2xl border border-rose-100 hover:border-rose-200 bg-white/60 text-center'
                        }>
                        <p className={genSkinType === type.id ? 'font-semibold text-sm text-rose-700' : 'font-semibold text-sm text-espresso-800'}>
                          {type.label}
                        </p>
                      </button>
                    ))}


                  </div>
                </div>

                {/* Skin Concerns */}
                <div>
                  <label className="block text-xs font-semibold text-espresso-700 mb-2">Skin Concerns (Select Multiple)</label>
                  <div className="flex flex-wrap gap-2">
                    {CONCERNS_OPTIONS.map((c) => {
                      const active = genConcerns.includes(c.id);
                      return (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => toggleConcern(c.id)}
                          className={active
                            ? 'px-3 py-2 rounded-xl text-xs font-medium bg-rose-500 text-ivory border-rose-500 shadow-xs'
                            : 'px-3 py-2 rounded-xl text-xs font-medium border bg-white border-rose-200/80 text-espresso-700 hover:border-rose-300'
                          }>
                          {c.label}
                        </button>
                      );
                    })}
                  </div>
                  <p className="text-[10px] text-espresso-500 mt-1">Select all that apply. More concerns = more targeted routine.</p>
                </div>

                {/* Budget Range */}
                <div>
                  <label className="block text-xs font-semibold text-espresso-700 mb-2">Budget Range (INR)</label>
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs text-espresso-600 mb-1">Min: ₹{genBudget[0].toLocaleString('en-IN')}</label>
                        <input
                          type="range"
                          min="100"
                          max="2000"
                          step="50"
                          value={genBudget[0]}
                          onChange={(e) => setGenBudget([Math.min(Number(e.target.value), genBudget[1] - 100), genBudget[1]])}
                          className="w-full accent-rose-500 cursor-pointer"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-espresso-600 mb-1">Max: ₹{genBudget[1].toLocaleString('en-IN')}</label>
                        <input
                          type="range"
                          min="500"
                          max="10000"
                          step="100"
                          value={genBudget[1]}
                          onChange={(e) => setGenBudget([genBudget[0], Math.max(Number(e.target.value), genBudget[0] + 100)])}
                          className="w-full accent-rose-500 cursor-pointer"
                        />
                      </div>
                    </div>
                    <div className="p-3 bg-rose-50/50 rounded-xl border border-rose-100 text-center">
                      <span className="text-xs text-espresso-700">Range: <strong className="text-rose-600">₹{genBudget[0].toLocaleString('en-IN')} – ₹{genBudget[1].toLocaleString('en-IN')}</strong></span>
                    </div>
                  </div>
                </div>

                {/* Options */}
                <div className="space-y-3">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={genUseExisting}
                      onChange={(e) => setGenUseExisting(e.target.checked)}
                      className="w-4 h-4 accent-rose-500 rounded border-rose-300"
                    />
                    <span className="text-xs text-espresso-700">
                      Use existing catalog-linked products from this routine
                    </span>
                  </label>
                </div>

                {/* Generate Button */}
                <div className="flex items-center justify-end space-x-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setIsGenerateModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium text-espresso-600 hover:text-rose-600"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={generating || genConcerns.length === 0}
                    className="px-5 py-2.5 text-xs font-semibold text-ivory bg-rose-500 hover:bg-rose-600 rounded-xl shadow-md transition-all disabled:opacity-50"
                  >
                    {generating ? 'Generating...' : 'Generate & Add to Routine'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        </>
      )}

      {/* Modal: Add Routine Step */}
      {isAddModalOpen && (
        <>
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
          >
            <div
              className="fixed inset-0 bg-espresso-950/60 backdrop-blur-sm"
              onClick={() => setIsAddModalOpen(false)}
            />
            <div className="relative w-full max-w-lg bg-ivory border border-rose-200/80 rounded-3xl shadow-2xl overflow-hidden z-10 p-6 sm:p-8">
              <div className="flex items-center justify-between pb-4 border-b border-rose-100">
                <h3 className="font-editorial text-2xl font-bold text-espresso-900">
                  Add Step to {activeRoutineType} Routine
                </h3>
                <button
                  onClick={() => setIsAddModalOpen(false)}
                  className="p-1.5 rounded-full hover:bg-rose-100 text-espresso-500 hover:text-espresso-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleAddStep} className="mt-4 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-espresso-700 mb-1">Step Name / Purpose *</label>
                  <input
                    type="text"
                    required
                    value={stepName}
                    onChange={(e) => setStepName(e.target.value)}
                    placeholder="e.g. Salicylic Acid Exfoliant, Vitamin C Serum"
                    className="w-full px-3.5 py-2.5 bg-white border border-rose-200 rounded-xl text-sm text-espresso-900 focus:outline-hidden focus:border-rose-400"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-espresso-700 mb-1">Category</label>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="w-full px-3.5 py-2.5 bg-white border border-rose-200 rounded-xl text-sm text-espresso-900 focus:outline-hidden focus:border-rose-400"
                    >
                      <option value="Face Wash">Face Wash / Cleanser</option>
                      <option value="Toner">Toner / Essence</option>
                      <option value="Serum">Active Serum</option>
                      <option value="Moisturiser">Moisturiser</option>
                      <option value="Sunscreen">Sunscreen SPF 50+</option>
                      <option value="Eye Care">Eye Cream</option>
                      <option value="Treatment">Spot Treatment</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-espresso-700 mb-1">Product Name (Optional)</label>
                    <input
                      type="text"
                      value={customProductName}
                      onChange={(e) => setCustomProductName(e.target.value)}
                      placeholder="e.g. Minimalist 2% Salicylic Acid"
                      className="w-full px-3.5 py-2.5 bg-white border border-rose-200 rounded-xl text-sm text-espresso-900 focus:outline-hidden focus:border-rose-400"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-espresso-700 mb-1">Application Instructions</label>
                  <input
                    type="text"
                    value={usageInstructions}
                    onChange={(e) => setUsageInstructions(e.target.value)}
                    placeholder="e.g. Apply 2-3 drops to dry skin, pat gently"
                    className="w-full px-3.5 py-2.5 bg-white border border-rose-200 rounded-xl text-sm text-espresso-900 focus:outline-hidden focus:border-rose-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-espresso-700 mb-1">Precautions / SPF Alert</label>
                  <input
                    type="text"
                    value={precautions}
                    onChange={(e) => setPrecautions(e.target.value)}
                    placeholder="e.g. Use sunscreen daily; do not combine with AHA/BHA"
                    className="w-full px-3.5 py-2.5 bg-white border border-rose-200 rounded-xl text-sm text-espresso-900 focus:outline-hidden focus:border-rose-400"
                  />
                </div>

                <div className="flex items-center justify-end space-x-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setIsAddModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium text-espresso-600 hover:text-rose-600"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingStep}
                    className="px-5 py-2.5 text-xs font-semibold text-ivory bg-rose-500 hover:bg-rose-600 rounded-xl shadow-md transition-all disabled:opacity-50"
                  >
                    {submittingStep ? 'Saving...' : 'Add Step'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SmartRoutineBuilder;
