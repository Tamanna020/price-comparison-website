import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, Percent } from 'lucide-react';
import { ALTERNATIVES_DATA } from '../data/alternatives';

interface DupesSectionProps {
  onSelectAlternative: (productId: string) => void;
}

export const DupesSection: React.FC<DupesSectionProps> = ({ onSelectAlternative }) => {
  return (
    <section id="dupes" className="py-20 bg-ivory relative border-b border-rose-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-14">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-champagne-100 text-champagne-700 text-xs font-bold uppercase tracking-wider mb-2">
            <Sparkles className="w-3.5 h-3.5 text-champagne-500" />
            <span>Smart Beauty Intelligence</span>
          </div>
          <h2 className="font-editorial text-3xl sm:text-5xl font-bold text-espresso-800 tracking-tight">
            Affordable Alternatives (Dupes)
          </h2>
          <p className="text-espresso-600 text-sm sm:text-base mt-3">
            Love luxury results but on a smart budget? Compare high-end icons with verified budget formulas that share key active ingredients and performance.
          </p>
        </div>

        {/* Dupe Cards Stack */}
        <div className="space-y-8">
          {ALTERNATIVES_DATA.map((dupe, idx) => (
            <motion.div
              key={dupe.id}
              initial={{ opacity: 0, y: 25 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: idx * 0.1 }}
              className="rounded-3xl bg-white border border-rose-200/90 shadow-soft-lift hover:shadow-luxury-card transition-all p-6 sm:p-8 relative overflow-hidden"
            >
              {/* Top Banner: Savings Pill */}
              <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-rose-100">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-sage-500 animate-pulse" />
                  <span className="text-xs font-bold uppercase tracking-wider text-espresso-600">
                    Match Confidence: <strong className="text-sage-600">{dupe.similarityScore}% Formula Match</strong>
                  </span>
                </div>

                <div className="flex items-center space-x-2 bg-rose-50 px-3.5 py-1.5 rounded-full border border-rose-200">
                  <Percent className="w-3.5 h-3.5 text-rose-500" />
                  <span className="text-xs font-bold text-rose-700">
                    You Save ₹{dupe.priceDifference.toLocaleString('en-IN')} ({dupe.percentageSaved}% Less)
                  </span>
                </div>
              </div>

              {/* Side-by-side comparison */}
              <div className="grid grid-cols-1 md:grid-cols-11 gap-6 items-center">
                {/* 1. Original Luxury Product (Left) */}
                <div className="md:col-span-5 rounded-2xl bg-ivory/60 border border-rose-100 p-5 flex items-center space-x-4">
                  <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-xl overflow-hidden bg-white shrink-0 border border-rose-200/60 shadow-xs">
                    <img
                      src={dupe.originalProduct.image}
                      alt={dupe.originalProduct.name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-champagne-600 bg-champagne-50 px-2 py-0.5 rounded-md inline-block mb-1">
                      High-End Original
                    </span>
                    <span className="text-xs text-espresso-400 block font-semibold">{dupe.originalProduct.brand}</span>
                    <h4 className="font-editorial text-lg font-bold text-espresso-800 line-clamp-1">
                      {dupe.originalProduct.name}
                    </h4>
                    <span className="text-xs text-espresso-500 block mt-0.5">Size: {dupe.originalProduct.quantity}</span>

                    <div className="mt-2 flex items-baseline space-x-2">
                      <span className="text-xl font-bold font-sans text-espresso-900">
                        ₹{dupe.originalProduct.price.toLocaleString('en-IN')}
                      </span>
                      <span className="text-[11px] text-espresso-400">({dupe.originalProduct.costPerUnit})</span>
                    </div>
                  </div>
                </div>

                {/* 2. Middle VS Badge */}
                <div className="md:col-span-1 flex items-center justify-center">
                  <div className="w-10 h-10 rounded-full bg-espresso-700 text-ivory flex items-center justify-center font-serif italic font-bold text-sm shadow-md">
                    VS
                  </div>
                </div>

                {/* 3. Affordable Alternative Product (Right) */}
                <div className="md:col-span-5 rounded-2xl bg-gradient-to-br from-rose-50/70 to-ivory border border-rose-300 p-5 flex items-center space-x-4 relative shadow-xs">
                  <div className="absolute top-3 right-3">
                    <span className="text-[10px] uppercase font-bold tracking-wider bg-rose-500 text-ivory px-2 py-0.5 rounded-full shadow-xs">
                      Best Value Match
                    </span>
                  </div>

                  <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-xl overflow-hidden bg-white shrink-0 border border-rose-200/80 shadow-xs">
                    <img
                      src={dupe.alternativeProduct.image}
                      alt={dupe.alternativeProduct.name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-rose-600 bg-rose-100/70 px-2 py-0.5 rounded-md inline-block mb-1">
                      Smart Alternative
                    </span>
                    <span className="text-xs text-espresso-400 block font-semibold">{dupe.alternativeProduct.brand}</span>
                    <h4 className="font-editorial text-lg font-bold text-espresso-800 line-clamp-1">
                      {dupe.alternativeProduct.name}
                    </h4>
                    <span className="text-xs text-espresso-500 block mt-0.5">Size: {dupe.alternativeProduct.quantity}</span>

                    <div className="mt-2 flex items-baseline space-x-2">
                      <span className="text-xl font-bold font-sans text-rose-600">
                        ₹{dupe.alternativeProduct.price.toLocaleString('en-IN')}
                      </span>
                      <span className="text-[11px] text-sage-700 font-semibold">({dupe.alternativeProduct.costPerUnit})</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Analysis & Shared Ingredients */}
              <div className="mt-6 pt-5 border-t border-rose-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex-1">
                  <p className="text-xs text-espresso-600 leading-relaxed">
                    <strong className="text-espresso-800">Formula Breakdown:</strong> {dupe.similarityExplanation}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5 items-center">
                    <span className="text-[11px] font-semibold text-espresso-400">Key Shared Ingredients:</span>
                    {dupe.keySharedIngredients.map((ing) => (
                      <span key={ing} className="px-2 py-0.5 rounded-md bg-white border border-rose-200 text-[11px] text-espresso-600">
                        {ing}
                      </span>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => onSelectAlternative(dupe.alternativeProductId)}
                  className="px-5 py-2.5 rounded-xl bg-rose-500 hover:bg-rose-600 text-ivory text-xs font-semibold tracking-wide transition-all shadow-xs flex items-center space-x-1.5 shrink-0 self-end sm:self-center"
                >
                  <span>View Smart Match</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
