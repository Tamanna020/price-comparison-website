import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import type { Routine, RoutineItem } from '../types';
import {
  getUserRoutines,
  reorderRoutineItems,
  deleteRoutineItem,
  addRoutineItem,
} from '../utils/api';

export const RoutinesPage: React.FC = () => {
  const { user, openAuthModal } = useAuth();

  const [routines, setRoutines] = useState<Routine[]>([]);
  const [activeRoutineType, setActiveRoutineType] = useState<'AM' | 'PM'>('AM');
  const [loading, setLoading] = useState(true);
  const [disclaimer, setDisclaimer] = useState<string>('');
  const [actionError, setActionError] = useState<string | null>(null);

  // New step modal state
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

    // Swap positions
    const [movedItem] = items.splice(itemIndex, 1);
    items.splice(targetIndex, 0, movedItem);

    // Optimistically update
    const updatedRoutine = { ...activeRoutine, items };
    setRoutines((prev) =>
      prev.map((r) => (r.id === activeRoutine.id ? updatedRoutine : r))
    );

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

    // Optimistically remove
    const updatedItems = activeRoutine.items.filter((i) => i.id !== itemId);
    setRoutines((prev) =>
      prev.map((r) => (r.id === activeRoutine.id ? { ...r, items: updatedItems } : r))
    );

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

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/80 border border-rose-200/80 rounded-3xl p-10 sm:p-14 shadow-soft-lift glass-panel max-w-xl mx-auto"
        >
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-rose-200 to-rose-400 mx-auto flex items-center justify-center text-ivory mb-5 shadow-xs">
            <Sparkles className="w-8 h-8" />
          </div>
          <h2 className="font-editorial text-3xl font-bold text-espresso-900 mb-2">
            Personalized Daily Routines
          </h2>
          <p className="text-sm text-espresso-600 mb-8 leading-relaxed">
            Curate morning (AM) and evening (PM) skincare regimens, check active ingredient compatibility, and reorder steps safely with dermatological guidance notices.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => openAuthModal('login')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-rose-500 hover:bg-rose-600 text-ivory text-sm font-semibold shadow-md transition-all"
            >
              Sign In to View Routines
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
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-rose-100 pb-6">
        <div>
          <div className="flex items-center space-x-2 text-rose-500 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" />
            <span>Regimen Builder</span>
          </div>
          <h1 className="font-editorial text-3xl sm:text-4xl font-bold text-espresso-900">
            Personalized Skincare Routines
          </h1>
          <p className="text-sm text-espresso-600 mt-1">
            Build, sequence, and verify your morning and evening skincare steps.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="px-5 py-2.5 text-xs font-semibold text-ivory bg-rose-500 hover:bg-rose-600 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Routine Step</span>
        </button>
      </div>

      {/* Routine Type Tabs */}
      <div className="flex bg-white/70 p-1.5 rounded-2xl border border-rose-200/80 shadow-xs max-w-md">
        <button
          type="button"
          onClick={() => setActiveRoutineType('AM')}
          className={`flex-1 py-2.5 px-4 text-xs font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all ${
            activeRoutineType === 'AM'
              ? 'bg-gradient-to-r from-amber-400 to-amber-500 text-ivory shadow-xs'
              : 'text-espresso-600 hover:text-amber-600'
          }`}
        >
          <Sun className="w-4 h-4" />
          <span>Morning Defense (AM)</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveRoutineType('PM')}
          className={`flex-1 py-2.5 px-4 text-xs font-semibold rounded-xl flex items-center justify-center space-x-2 transition-all ${
            activeRoutineType === 'PM'
              ? 'bg-gradient-to-r from-indigo-900 to-slate-900 text-ivory shadow-xs'
              : 'text-espresso-600 hover:text-indigo-900'
          }`}
        >
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

      {/* Active Ingredient Conflict Warning Banner */}
      {activeRoutine?.conflicts && activeRoutine.conflicts.length > 0 && (
        <div className="space-y-3">
          {activeRoutine.conflicts.map((conflict, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 sm:p-5 rounded-2xl bg-amber-500/15 border border-amber-400 text-espresso-900 text-xs sm:text-sm flex items-start space-x-3.5 shadow-xs"
            >
              <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-amber-950 uppercase tracking-wide text-[11px] block">
                  Ingredient Conflict Detected: {conflict.conflict_type.replace('_', ' ')}
                </span>
                <p className="text-xs text-espresso-800 font-medium mt-0.5">
                  {conflict.description}
                </p>
                <p className="text-xs text-espresso-700 mt-1 italic">
                  Recommendation: {conflict.recommendation}
                </p>
              </div>
            </motion.div>
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
              Click &quot;Add Routine Step&quot; above to sequence your cleanser, actives, and moisturizer.
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

                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-rose-50 border border-rose-200/60 text-[10px] font-bold text-rose-700 uppercase tracking-wider">
                      {item.category || 'Step'}
                    </span>
                    <h3 className="font-editorial text-lg font-bold text-espresso-900">
                      {item.step_name}
                    </h3>
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
          ))
        )}
      </div>

      {/* Non-medical Cosmetic Disclaimer Banner */}
      <div className="p-4 sm:p-5 rounded-2xl bg-amber-500/10 border border-amber-300/60 text-espresso-800 text-xs sm:text-sm flex items-start space-x-3 mt-10">
        <ShieldCheck className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block text-espresso-900 mb-0.5">
            Cosmetic Guidance Notice
          </span>
          <p className="text-xs text-espresso-700 leading-relaxed">
            {disclaimer ||
              'Skincare routine steps and compatibility alerts are provided for cosmetic discovery and education only. They do not constitute dermatological or medical diagnosis. Discontinue use if irritation occurs and perform a patch test before introducing new active formulas.'}
          </p>
        </div>
      </div>

      {/* Modal: Add Routine Step */}
      <AnimatePresence>
        {isAddModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsAddModalOpen(false)}
              className="fixed inset-0 bg-espresso-950/60 backdrop-blur-sm transition-opacity"
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="relative w-full max-w-lg bg-ivory border border-rose-200/80 rounded-3xl shadow-2xl overflow-hidden z-10 p-6 sm:p-8"
            >
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
                  <label className="block text-xs font-semibold text-espresso-700 mb-1">
                    Step Name / Purpose *
                  </label>
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
                    <label className="block text-xs font-semibold text-espresso-700 mb-1">
                      Category
                    </label>
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
                    <label className="block text-xs font-semibold text-espresso-700 mb-1">
                      Product Name (Optional)
                    </label>
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
                  <label className="block text-xs font-semibold text-espresso-700 mb-1">
                    Application Instructions
                  </label>
                  <input
                    type="text"
                    value={usageInstructions}
                    onChange={(e) => setUsageInstructions(e.target.value)}
                    placeholder="e.g. Apply 2-3 drops to dry skin, pat gently"
                    className="w-full px-3.5 py-2.5 bg-white border border-rose-200 rounded-xl text-sm text-espresso-900 focus:outline-hidden focus:border-rose-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-espresso-700 mb-1">
                    Precautions / SPF Alert
                  </label>
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
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
