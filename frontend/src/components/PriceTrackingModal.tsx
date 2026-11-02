import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Bell, ShieldAlert, CheckCircle2, Trash2 } from 'lucide-react';
import type { Product, TrackedProduct } from '../types';

interface PriceTrackingModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: Product;
  existingRecord?: TrackedProduct;
  onSaveTarget: (targetPrice: number, note?: string) => void;
  onRemoveTracking?: () => void;
}

export const PriceTrackingModal: React.FC<PriceTrackingModalProps> = ({
  isOpen,
  onClose,
  product,
  existingRecord,
  onSaveTarget,
  onRemoveTracking,
}) => {
  const currentPrice = product.price;
  const initialTarget = existingRecord ? existingRecord.targetPrice : Math.round(currentPrice * 0.9);
  const [targetInput, setTargetInput] = useState<string>(initialTarget.toString());
  const [noteInput, setNoteInput] = useState<string>(existingRecord?.note || '');
  const [errorMsg, setErrorMsg] = useState<string>('');

  if (!isOpen) return null;

  const numericTarget = parseFloat(targetInput);
  const isValidNumber = !isNaN(numericTarget) && numericTarget > 0;
  const diff = isValidNumber ? numericTarget - currentPrice : 0;
  const diffPct = isValidNumber && currentPrice > 0 ? Math.round(((currentPrice - numericTarget) / currentPrice) * 100) : 0;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValidNumber) {
      setErrorMsg('Please enter a valid target price greater than ₹0.');
      return;
    }
    setErrorMsg('');
    onSaveTarget(numericTarget, noteInput);
    onClose();
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-y-auto bg-espresso-950/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          className="relative w-full max-w-lg bg-ivory rounded-3xl shadow-2xl border border-rose-200 overflow-hidden p-6 space-y-5"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-rose-100 pb-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-rose-100 flex items-center justify-center text-rose-600">
                <Bell className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-editorial text-xl font-bold text-espresso-900">
                  {existingRecord ? 'Update Price Alert' : 'Set Price-Drop Alert'}
                </h3>
                <span className="text-xs text-espresso-500">
                  Target Price in Indian Rupees (₹)
                </span>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-full hover:bg-rose-100 text-espresso-500 transition-colors"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Product Mini Banner */}
          <div className="flex items-center space-x-3 bg-white p-3 rounded-2xl border border-rose-100">
            <img
              src={product.image}
              alt={product.name}
              className="w-14 h-14 object-cover rounded-xl border border-rose-100"
            />
            <div className="flex-1 min-w-0">
              <span className="text-[10px] font-bold uppercase tracking-wider text-rose-500 block">
                {product.brand} • {product.quantity}
              </span>
              <h4 className="text-xs font-bold text-espresso-900 truncate">
                {product.name}
              </h4>
              <div className="flex items-baseline space-x-2 mt-0.5">
                <span className="text-xs text-espresso-400">Current Lowest:</span>
                <span className="text-sm font-extrabold text-espresso-950 font-sans">
                  ₹{currentPrice.toLocaleString('en-IN')}
                </span>
              </div>
            </div>
          </div>

          {/* Target Price Form */}
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-espresso-800 mb-1">
                Your Target Price (₹ INR)
              </label>
              <div className="relative rounded-xl shadow-2xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-espresso-500 font-bold">
                  ₹
                </div>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={targetInput}
                  onChange={(e) => {
                    setTargetInput(e.target.value);
                    setErrorMsg('');
                  }}
                  className="block w-full pl-8 pr-4 py-2.5 rounded-xl border border-rose-200 bg-white text-espresso-900 font-bold focus:outline-hidden focus:ring-2 focus:ring-rose-400 text-base"
                  placeholder="e.g. 400"
                />
              </div>

              {/* Target Price Presets */}
              <div className="flex items-center space-x-2 mt-2">
                <span className="text-[11px] text-espresso-400">Quick set:</span>
                {[0.05, 0.1, 0.15, 0.2].map((pct) => {
                  const preset = Math.round(currentPrice * (1 - pct));
                  return (
                    <button
                      key={pct}
                      type="button"
                      onClick={() => setTargetInput(preset.toString())}
                      className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-white border border-rose-200 text-espresso-700 hover:bg-rose-50 transition-colors"
                    >
                      -{pct * 100}% (₹{preset})
                    </button>
                  );
                })}
              </div>

              {errorMsg && (
                <p className="text-xs text-rose-600 mt-1.5 font-medium">{errorMsg}</p>
              )}
            </div>

            {/* Target Calculation Preview */}
            {isValidNumber && (
              <div className="p-3 rounded-xl bg-ivory-100 border border-rose-100 text-xs space-y-1">
                {diff <= 0 ? (
                  <div className="flex items-center space-x-1.5 text-sage-700 font-semibold">
                    <CheckCircle2 className="w-4 h-4 text-sage-600" />
                    <span>
                      Target will trigger immediately! Current price is already below target (Save ₹{Math.abs(diff)}).
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between text-espresso-700">
                    <span>Required price drop:</span>
                    <strong className="text-rose-600 font-sans">
                      ₹{diff} ({diffPct}% drop needed)
                    </strong>
                  </div>
                )}
              </div>
            )}

            {/* Optional Note */}
            <div>
              <label className="block text-xs font-semibold text-espresso-700 mb-1">
                Personal Shopping Note (Optional)
              </label>
              <input
                type="text"
                value={noteInput}
                onChange={(e) => setNoteInput(e.target.value)}
                placeholder="e.g. Need restock before next month"
                className="w-full px-3 py-2 rounded-xl border border-rose-200 bg-white text-xs text-espresso-800 focus:outline-hidden focus:ring-2 focus:ring-rose-400"
              />
            </div>

            {/* Transparency Note */}
            <div className="flex items-start space-x-2 p-3 rounded-xl bg-champagne-50/60 border border-champagne-200/80 text-[11px] text-espresso-600">
              <ShieldAlert className="w-4 h-4 text-champagne-700 shrink-0 mt-0.5" />
              <span>
                <strong>In-App Alert Policy:</strong> Alerts are evaluated in real-time when shopping on the platform. External background automated email delivery is currently unconfigured.
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-2">
              {existingRecord && onRemoveTracking ? (
                <button
                  type="button"
                  onClick={() => {
                    onRemoveTracking();
                    onClose();
                  }}
                  className="px-3 py-2 rounded-xl text-rose-600 hover:bg-rose-50 text-xs font-semibold flex items-center space-x-1 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Remove Alert</span>
                </button>
              ) : (
                <div></div>
              )}

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 rounded-xl bg-white border border-rose-200 text-xs font-semibold text-espresso-700 hover:bg-rose-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-espresso-800 hover:bg-espresso-950 text-ivory text-xs font-bold tracking-wide shadow-xs transition-colors"
                >
                  {existingRecord ? 'Update Target' : 'Save Price Alert'}
                </button>
              </div>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

