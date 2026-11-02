import React from 'react';
import { motion } from 'framer-motion';
import { Tag, AlertCircle, ArrowRight, Heart } from 'lucide-react';
import type { Product } from '../types';

interface DealSectionProps {
  deals: Product[];
  onViewProduct: (product: Product) => void;
  onToggleWishlist: (id: string) => void;
  isWishlisted: (id: string) => boolean;
}

export const DealSection: React.FC<DealSectionProps> = ({
  deals,
  onViewProduct,
  onToggleWishlist,
  isWishlisted,
}) => {
  return (
    <section id="deals" className="py-20 bg-gradient-to-b from-ivory to-rose-50/40 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <div className="inline-flex items-center space-x-1.5 text-xs font-bold uppercase tracking-wider text-rose-500 bg-rose-100/70 px-3 py-1 rounded-full mb-2">
              <Tag className="w-3.5 h-3.5" />
              <span>Verified Market Arbitrage</span>
            </div>
            <h2 className="font-editorial text-3xl sm:text-5xl font-bold text-espresso-800 tracking-tight">
              Today's Best Beauty Deals
            </h2>
            <p className="text-espresso-600 text-sm sm:text-base mt-2 max-w-xl">
              Curated verified price drops across India’s leading beauty platforms. Discover authentic products marked down to their 30-day lows.
            </p>
          </div>

          {/* Academic Ethical Labeling Notice */}
          <div className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-champagne-100/80 border border-champagne-300/80 text-espresso-700 text-xs shrink-0 self-start md:self-auto">
            <AlertCircle className="w-4 h-4 text-champagne-600 shrink-0" />
            <span className="font-medium">
              <strong>DEMO DATA:</strong> Illustrative sample prices for academic comparison.
            </span>
          </div>
        </div>

        {/* Deals Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {deals.slice(0, 6).map((deal, idx) => {
            const savings = deal.originalPrice ? deal.originalPrice - deal.price : 0;
            const savingsPct = deal.originalPrice ? Math.round((savings / deal.originalPrice) * 100) : 0;
            const wish = isWishlisted(deal.id);

            return (
              <motion.div
                key={deal.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.08 }}
                className="rounded-2xl bg-white border border-rose-200/90 shadow-soft-lift hover:shadow-luxury-card transition-all duration-300 p-5 flex flex-col justify-between relative overflow-hidden group"
              >
                {/* Decorative background glow */}
                <div className="absolute -top-12 -right-12 w-32 h-32 rounded-full bg-rose-100/50 blur-2xl pointer-events-none group-hover:scale-125 transition-transform" />

                {/* Top: Image, Title, Deal Tag */}
                <div>
                  <div className="flex items-start gap-4">
                    <div className="w-24 h-24 rounded-xl overflow-hidden bg-ivory shrink-0 border border-rose-100">
                      <img
                        src={deal.image}
                        alt={deal.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs uppercase font-bold text-rose-500 tracking-wider">
                          {deal.brand}
                        </span>
                        {savingsPct > 0 && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500 text-ivory">
                            {savingsPct}% OFF
                          </span>
                        )}
                      </div>

                      <h3
                        onClick={() => onViewProduct(deal)}
                        className="font-editorial text-lg font-bold text-espresso-800 line-clamp-2 mt-1 hover:text-rose-600 cursor-pointer transition-colors"
                      >
                        {deal.name}
                      </h3>

                      <div className="flex flex-wrap items-center gap-1.5 mt-0.5">
                        <span className="text-xs text-espresso-400 block">
                          {deal.quantity} • {deal.subcategory}
                        </span>
                        {deal.costPerUnit && (
                          <span className="text-[10px] text-sage-800 bg-sage-50 px-1.5 py-0.5 rounded font-medium border border-sage-200">
                            {deal.costPerUnit}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Multi-Store Arbitrage Comparison Bar */}
                  <div className="mt-4 pt-3 border-t border-rose-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-semibold text-espresso-500 uppercase tracking-wider block">
                        Live Store Comparison (Demo Data):
                      </span>
                      {deal.dealExpiresAt && (
                        <span className="text-[10px] text-espresso-400">
                          Expires: {deal.dealExpiresAt}
                        </span>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      {deal.storeOffers.map((offer) => (
                        <div
                          key={offer.storeId}
                          className={`flex items-center justify-between text-xs px-2.5 py-1.5 rounded-lg transition-colors ${
                            offer.isLowestPrice
                              ? 'bg-rose-50 border border-rose-300/80 font-bold text-rose-800'
                              : 'bg-ivory/60 text-espresso-600'
                          }`}
                        >
                          <div className="flex items-center space-x-1.5">
                            <span>{offer.storeName} (Demo)</span>
                            {offer.isLowestPrice && (
                              <span className="text-[10px] bg-rose-500 text-ivory px-1.5 py-0.2 rounded-full uppercase tracking-tighter">
                                Best Price
                              </span>
                            )}
                            {offer.couponCode && (
                              <span className="text-[9px] bg-champagne-100 text-champagne-800 px-1 py-0.2 rounded font-medium">
                                Code: {offer.couponCode}
                              </span>
                            )}
                          </div>
                          <span className="font-sans font-bold">
                            ₹{offer.price.toLocaleString('en-IN')}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Footer Pricing & CTA */}
                <div className="mt-5 pt-3 border-t border-rose-100/80 flex items-center justify-between">
                  <div>
                    <span className="text-[11px] text-espresso-400 block">Lowest Deal</span>
                    <div className="flex items-baseline space-x-2">
                      <span className="text-2xl font-bold font-sans text-espresso-900">
                        ₹{deal.price.toLocaleString('en-IN')}
                      </span>
                      {deal.originalPrice && (
                        <span className="text-xs text-espresso-400 line-through">
                          ₹{deal.originalPrice.toLocaleString('en-IN')}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onToggleWishlist(deal.id)}
                      aria-label={wish ? "Remove from wishlist" : "Add to wishlist"}
                      className={`p-2 rounded-xl border transition-colors ${
                        wish
                          ? 'bg-rose-50 border-rose-300 text-rose-500'
                          : 'bg-ivory border-rose-200 text-espresso-400 hover:text-rose-500'
                      }`}
                    >
                      <Heart className={`w-4 h-4 ${wish ? 'fill-rose-500 text-rose-500' : ''}`} />
                    </button>
                    <button
                      onClick={() => onViewProduct(deal)}
                      className="px-4 py-2 rounded-xl bg-espresso-700 hover:bg-espresso-800 text-ivory text-xs font-semibold tracking-wide transition-all shadow-xs flex items-center space-x-1"
                    >
                      <span>Compare</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
