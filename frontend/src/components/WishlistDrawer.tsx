import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Trash2, ArrowRight, Heart } from 'lucide-react';
import type { Product } from '../types';

interface WishlistDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  wishlistIds: string[];
  allProducts: Product[];
  onRemoveFromWishlist: (id: string) => void;
  onClearWishlist: () => void;
  onViewProduct: (product: Product) => void;
  onExploreProducts: () => void;
}

export const WishlistDrawer: React.FC<WishlistDrawerProps> = ({
  isOpen,
  onClose,
  wishlistIds,
  allProducts,
  onRemoveFromWishlist,
  onClearWishlist,
  onViewProduct,
  onExploreProducts,
}) => {
  if (!isOpen) return null;

  const wishlistedProducts = allProducts.filter((p) => wishlistIds.includes(p.id));
  const totalValue = wishlistedProducts.reduce((sum, p) => sum + p.price, 0);
  const totalOriginal = wishlistedProducts.reduce((sum, p) => sum + (p.originalPrice || p.price), 0);
  const totalSavings = totalOriginal - totalValue;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-hidden bg-espresso-950/50 backdrop-blur-xs flex justify-end">
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 250 }}
          className="relative w-full max-w-md bg-ivory h-full shadow-2xl border-l border-rose-200 flex flex-col justify-between"
        >
          {/* Header */}
          <div className="p-5 border-b border-rose-100 flex items-center justify-between bg-white/70">
            <div className="flex items-center space-x-2">
              <Heart className="w-5 h-5 text-rose-500 fill-rose-500" />
              <h3 className="font-editorial text-xl font-bold text-espresso-800">
                Your Saved Beauty Vault
              </h3>
              <span className="text-xs bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full font-bold">
                {wishlistedProducts.length}
              </span>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-full hover:bg-rose-100 text-espresso-400 hover:text-espresso-700 transition-colors"
              aria-label="Close wishlist drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body: Product List or Empty State */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {wishlistedProducts.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="w-16 h-16 rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-400">
                  <Heart className="w-8 h-8" />
                </div>
                <h4 className="font-editorial text-xl font-bold text-espresso-800">
                  Your beauty vault is empty
                </h4>
                <p className="text-xs text-espresso-500 max-w-xs">
                  Save your holy grails, skincare serums, and dream makeup to monitor price drops across Indian retailers.
                </p>
                <button
                  onClick={() => {
                    onClose();
                    onExploreProducts();
                  }}
                  className="px-6 py-2.5 rounded-full bg-rose-500 text-ivory text-xs font-semibold hover:bg-rose-600 transition-colors shadow-xs"
                >
                  Start Exploring
                </button>
              </div>
            ) : (
              <>
                {wishlistedProducts.map((prod) => (
                  <div
                    key={prod.id}
                    className="p-3 rounded-2xl bg-white border border-rose-100 shadow-soft-lift flex items-center space-x-3 group relative"
                  >
                    <div
                      onClick={() => {
                        onClose();
                        onViewProduct(prod);
                      }}
                      className="w-16 h-16 rounded-xl overflow-hidden bg-ivory shrink-0 border border-rose-100 cursor-pointer"
                    >
                      <img src={prod.image} alt={prod.name} className="w-full h-full object-cover" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <span className="text-[10px] font-bold uppercase text-rose-500 tracking-wider block">
                        {prod.brand}
                      </span>
                      <h4
                        onClick={() => {
                          onClose();
                          onViewProduct(prod);
                        }}
                        className="font-editorial text-sm font-bold text-espresso-800 line-clamp-1 hover:text-rose-600 cursor-pointer"
                      >
                        {prod.name}
                      </h4>
                      <div className="flex items-baseline space-x-2 mt-1">
                        <span className="text-sm font-bold font-sans text-espresso-900">
                          ₹{prod.price.toLocaleString('en-IN')}
                        </span>
                        {prod.originalPrice && (
                          <span className="text-[11px] text-espresso-400 line-through">
                            ₹{prod.originalPrice.toLocaleString('en-IN')}
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => onRemoveFromWishlist(prod.id)}
                      className="p-2 text-espresso-300 hover:text-rose-500 transition-colors"
                      aria-label="Remove item"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </>
            )}
          </div>

          {/* Footer: Total and Actions */}
          {wishlistedProducts.length > 0 && (
            <div className="p-5 border-t border-rose-200 bg-white/80 space-y-3">
              <div className="flex items-center justify-between text-xs text-espresso-600">
                <span>Vault Estimated Total:</span>
                <span className="text-base font-bold font-sans text-espresso-900">
                  ₹{totalValue.toLocaleString('en-IN')}
                </span>
              </div>

              {totalSavings > 0 && (
                <div className="flex items-center justify-between text-xs text-sage-700 bg-sage-50 px-3 py-1.5 rounded-lg border border-sage-200">
                  <span>Total Discount Savings:</span>
                  <strong className="font-bold">Save ₹{totalSavings.toLocaleString('en-IN')}</strong>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 pt-1">
                <button
                  onClick={onClearWishlist}
                  className="py-2.5 rounded-xl border border-rose-200 hover:bg-rose-50 text-espresso-600 text-xs font-semibold transition-colors"
                >
                  Clear All
                </button>
                <button
                  onClick={() => {
                    onClose();
                    onExploreProducts();
                  }}
                  className="py-2.5 rounded-xl bg-rose-500 hover:bg-rose-600 text-ivory text-xs font-semibold transition-colors flex items-center justify-center space-x-1"
                >
                  <span>Continue Browsing</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
