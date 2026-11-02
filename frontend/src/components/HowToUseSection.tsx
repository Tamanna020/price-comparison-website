import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon, ShieldAlert, Sparkles, CheckCircle2 } from 'lucide-react';
import { AM_ROUTINE, PM_ROUTINE } from '../data/routines';

export const HowToUseSection: React.FC = () => {
  const [selectedPhase, setSelectedPhase] = useState<'AM' | 'PM'>('AM');

  const activeRoutine = selectedPhase === 'AM' ? AM_ROUTINE : PM_ROUTINE;

  return (
    <section id="routine" className="py-20 bg-white/70 relative border-b border-rose-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sage-100 text-sage-700 text-xs font-bold uppercase tracking-wider mb-2">
            <Sparkles className="w-3.5 h-3.5 text-sage-500" />
            <span>Editorial Skincare Masterclass</span>
          </div>
          <h2 className="font-editorial text-3xl sm:text-5xl font-bold text-espresso-800 tracking-tight">
            How to Use: The Complete Ritual
          </h2>
          <p className="text-espresso-600 text-sm sm:text-base mt-3">
            Maximize your skincare investment by layering products in their correct chronological order. Active ingredients only work when applied in the right sequence.
          </p>

          {/* AM / PM Toggle */}
          <div className="inline-flex p-1 bg-ivory rounded-full border border-rose-200 mt-6 shadow-xs">
            <button
              onClick={() => setSelectedPhase('AM')}
              className={`px-6 py-2.5 rounded-full text-xs font-bold tracking-wider uppercase transition-all flex items-center space-x-2 ${
                selectedPhase === 'AM'
                  ? 'bg-rose-500 text-ivory shadow-xs'
                  : 'text-espresso-600 hover:text-espresso-800'
              }`}
            >
              <Sun className="w-4 h-4 text-champagne-300" />
              <span>Morning Ritual (AM)</span>
            </button>

            <button
              onClick={() => setSelectedPhase('PM')}
              className={`px-6 py-2.5 rounded-full text-xs font-bold tracking-wider uppercase transition-all flex items-center space-x-2 ${
                selectedPhase === 'PM'
                  ? 'bg-espresso-800 text-ivory shadow-xs'
                  : 'text-espresso-600 hover:text-espresso-800'
              }`}
            >
              <Moon className="w-4 h-4 text-rose-300" />
              <span>Nighttime Ritual (PM)</span>
            </button>
          </div>
        </div>

        {/* Routine Steps List */}
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedPhase}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6"
          >
            {activeRoutine.map((step) => (
              <div
                key={step.step}
                className="rounded-2xl bg-ivory border border-rose-200/80 p-5 shadow-soft-lift flex flex-col justify-between hover:border-rose-300 transition-colors"
              >
                <div>
                  {/* Step Header */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="w-7 h-7 rounded-full bg-rose-400 text-ivory flex items-center justify-center font-bold text-xs shadow-xs">
                      {step.step}
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-espresso-400">
                      {step.category}
                    </span>
                  </div>

                  <h3 className="font-editorial text-lg font-bold text-espresso-800 mb-2 leading-snug">
                    {step.name}
                  </h3>

                  <p className="text-xs text-espresso-600 mb-3 leading-relaxed">
                    {step.instructions}
                  </p>
                </div>

                <div className="pt-3 border-t border-rose-100 text-[11px] space-y-1.5">
                  <div className="text-sage-700 font-semibold flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-sage-500 shrink-0" />
                    <span>Tip: {step.proTip}</span>
                  </div>
                  <div className="text-espresso-400">
                    Freq: {step.frequency}
                  </div>
                </div>
              </div>
            ))}
          </motion.div>
        </AnimatePresence>

        {/* Dermatologist Precautions Callout */}
        <div className="mt-12 rounded-2xl bg-champagne-50/70 border border-champagne-200 p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3">
            <ShieldAlert className="w-5 h-5 text-champagne-600 shrink-0 mt-0.5" />
            <div className="text-xs text-espresso-700 leading-relaxed">
              <strong className="text-espresso-900 font-bold block mb-0.5">Golden Dermatologist Precautions:</strong>
              1. Always perform a 24-hour patch test behind your ear before full-face application. <br />
              2. Never combine pure Vitamin C and AHA/BHA exfoliants in the same morning routine. <br />
              3. Introduce active Retinoids gradually (start 1–2 nights weekly) to prevent barrier disruption.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
