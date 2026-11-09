import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Tag,
  Check,
  X,
  Truck,
  Calculator,
} from 'lucide-react';
import {
  fetchDealIntelligence,
  calculateLandedCost,
  type DealIntelligenceResponse,
  type TotalPurchaseCostBreakdown,
} from '../utils/api';

interface DealScoreCardProps {
  productId: number | string;
  retailerName?: string;
  currencySymbol?: string;
}

export const DealScoreCard: React.FC<DealScoreCardProps> = ({
  productId,
  retailerName,
  currencySymbol = '₹',
}) => {
  const [dealData, setDealData] = useState<DealIntelligenceResponse | null>(null);
  const [landedCost, setLandedCost] = useState<TotalPurchaseCostBreakdown | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [expandedFactors, setExpandedFactors] = useState<boolean>(false);
  const [couponInput, setCouponInput] = useState<string>('');
  const [applyingCoupon, setApplyingCoupon] = useState<boolean>(false);
  const [couponError, setCouponError] = useState<string | null>(null);

  const loadDealIntelligence = (couponCode?: string) => {
    setLoading(true);
    setCouponError(null);

    fetchDealIntelligence(productId, retailerName, couponCode)
      .then((res) => {
        if (res.success && res.data) {
          setDealData(res.data);
          setLandedCost(res.data.landed_cost_breakdown);
        }
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    loadDealIntelligence();
  }, [productId, retailerName]);

  const handleApplyCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!couponInput.trim()) return;

    setApplyingCoupon(true);
    setCouponError(null);

    try {
      const res = await calculateLandedCost(productId, {
        retailer_name: retailerName || 'Retailer',
        coupon_code: couponInput.trim().toUpperCase(),
        custom_price: dealData?.current_price,
      });

      if (res.success && res.data) {
        setLandedCost(res.data);
        if (res.data.coupon_applied && !res.data.coupon_applied.is_valid) {
          setCouponError(res.data.coupon_applied.rejection_reason || 'Coupon could not be applied.');
        } else {
          // Re-evaluate deal intelligence with valid coupon
          loadDealIntelligence(couponInput.trim().toUpperCase());
        }
      }
    } catch (err: unknown) {
      setCouponError(err instanceof Error ? err.message : 'Error validating coupon');
    } finally {
      setApplyingCoupon(false);
    }
  };

  if (loading && !dealData) {
    return (
      <div className="bg-white rounded-3xl border border-rose-200/80 p-6 shadow-soft-lift animate-pulse space-y-4">
        <div className="h-6 bg-rose-100/50 rounded-xl w-1/3"></div>
        <div className="h-20 bg-ivory-100 rounded-2xl"></div>
        <div className="h-12 bg-ivory-50 rounded-xl"></div>
      </div>
    );
  }

  if (!dealData) return null;

  const getScoreColor = (score: number) => {
    if (score >= 80) return { bg: 'bg-emerald-500', text: 'text-emerald-700', badge: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
    if (score >= 65) return { bg: 'bg-champagne-500', text: 'text-champagne-700', badge: 'bg-champagne-50 text-champagne-800 border-champagne-200' };
    if (score >= 50) return { bg: 'bg-amber-500', text: 'text-amber-700', badge: 'bg-amber-50 text-amber-800 border-amber-200' };
    return { bg: 'bg-rose-500', text: 'text-rose-700', badge: 'bg-rose-50 text-rose-800 border-rose-200' };
  };

  const colors = getScoreColor(dealData.deal_score);

  return (
    <div className="bg-white rounded-3xl border border-rose-200/80 p-6 sm:p-7 shadow-soft-lift space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-rose-100">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold tracking-widest uppercase text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
              Deal Intelligence
            </span>
            {dealData.is_simulated_deal && (
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold tracking-wider uppercase text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/80">
                <ShieldAlert className="w-3 h-3 text-amber-600" />
                Simulated Deal Score
              </span>
            )}
          </div>
          <h3 className="font-serif text-lg font-bold text-espresso-950 flex items-center gap-2">
            Value & Landed Cost Scoring
          </h3>
        </div>

        {/* Grade Badge */}
        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          <div className="text-right">
            <span className="text-[10px] font-medium text-espresso-500 block uppercase tracking-wider">
              Deal Grade
            </span>
            <span className="text-xs font-semibold text-espresso-900">
              {dealData.deal_classification}
            </span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-espresso-950 text-white flex items-center justify-center font-serif text-xl font-bold shadow-md">
            {dealData.deal_grade}
          </div>
        </div>
      </div>

      {/* Main Score & Summary Banner */}
      <div className="p-5 rounded-2xl bg-ivory-50/70 border border-rose-100/90 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-espresso-700">
            Algorithmic Deal Score
          </span>
          <span className="text-sm font-extrabold text-espresso-950">
            {dealData.deal_score} <span className="text-espresso-400 font-normal">/ 100</span>
          </span>
        </div>

        {/* Progress Bar Gauge */}
        <div className="w-full bg-rose-100/70 rounded-full h-3 overflow-hidden shadow-inner">
          <div
            className={`h-full ${colors.bg} transition-all duration-700 rounded-full`}
            style={{ width: `${Math.max(5, dealData.deal_score)}%` }}
          />
        </div>

        <p className="text-xs text-espresso-700 leading-relaxed pt-1">
          {dealData.summary_verdict}
        </p>
      </div>

      {/* Factor Breakdown Accordion */}
      <div className="space-y-3">
        <button
          type="button"
          onClick={() => setExpandedFactors(!expandedFactors)}
          className="w-full flex items-center justify-between p-3 rounded-2xl bg-ivory-50/50 hover:bg-ivory-100/60 border border-rose-100 text-xs font-semibold text-espresso-900 transition-colors"
        >
          <span className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-rose-500" />
            View 5-Factor Scoring Breakdown
          </span>
          {expandedFactors ? <ChevronUp className="w-4 h-4 text-espresso-500" /> : <ChevronDown className="w-4 h-4 text-espresso-500" />}
        </button>

        {expandedFactors && (
          <div className="space-y-2.5 pt-1">
            {dealData.factors.map((factor, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-2xl bg-white border border-rose-100/80 shadow-2xs space-y-1 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-espresso-900">{factor.factor_name}</span>
                  <span className="font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-100">
                    +{factor.points_awarded.toFixed(1)} / {factor.max_points.toFixed(0)} pts
                  </span>
                </div>
                <p className="text-espresso-600 text-[11px] leading-relaxed">
                  {factor.explanation}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Total Landed Cost Breakdown Card */}
      {landedCost && (
        <div className="p-5 rounded-2xl bg-ivory-50/50 border border-rose-200/70 space-y-4">
          <div className="flex items-center justify-between border-b border-rose-100 pb-3">
            <div className="flex items-center gap-2">
              <Calculator className="w-4 h-4 text-rose-600" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-espresso-900">
                Itemized Landed Cost ({landedCost.retailer_name})
              </h4>
            </div>
            <span className="text-[10px] text-espresso-500 font-medium">
              {landedCost.is_final_exact ? 'Exact Disclosed Cost' : 'Estimated Base'}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            {/* Base Product Price */}
            <div className="flex items-center justify-between text-espresso-700">
              <span>Catalog Product Price:</span>
              <span className="font-medium text-espresso-950">
                {currencySymbol}{landedCost.base_price.toLocaleString('en-IN')}
              </span>
            </div>

            {/* Disclosed or Undisclosed Shipping */}
            <div className="flex items-center justify-between text-espresso-700">
              <span className="flex items-center gap-1.5">
                <Truck className="w-3.5 h-3.5 text-espresso-400" />
                Shipping & Delivery:
              </span>
              <span className={`font-medium ${landedCost.is_shipping_known ? 'text-espresso-950' : 'text-amber-700 font-semibold'}`}>
                {landedCost.shipping_label}
              </span>
            </div>

            {/* Applied Coupon Discount */}
            {landedCost.coupon_savings > 0 && (
              <div className="flex items-center justify-between text-amber-800 font-medium bg-amber-50/70 p-2 rounded-xl border border-amber-200/60">
                <span className="flex items-center gap-1.5 text-[11px]">
                  <Tag className="w-3.5 h-3.5 text-amber-600" />
                  Simulated Coupon ({landedCost.coupon_applied?.code}):
                </span>
                <span className="font-bold text-xs">
                  - {currencySymbol}{landedCost.coupon_savings.toLocaleString('en-IN')}
                </span>
              </div>
            )}

            {/* Total Landed Payable */}
            <div className="pt-2 border-t border-rose-100/90 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-espresso-950 block">
                  Final Payable Price:
                </span>
                <span className="text-[10px] text-espresso-500 block">
                  {landedCost.payable_state_note}
                </span>
              </div>
              <span className="text-base font-extrabold text-rose-600">
                {currencySymbol}{landedCost.final_payable_price.toLocaleString('en-IN')}
              </span>
            </div>

            {/* Savings Classification & Truth in Advertising */}
            <div className="pt-2 space-y-1.5">
              {landedCost.reference_mrp && landedCost.reference_mrp > landedCost.base_price && (
                <div className="flex items-center justify-between text-[11px] text-espresso-700">
                  <span>Reference MRP Discount:</span>
                  <span className="font-semibold text-espresso-900">
                    {currencySymbol}{(landedCost.reference_mrp - landedCost.base_price).toLocaleString('en-IN')}
                  </span>
                </div>
              )}

              {landedCost.total_potential_savings > 0 && (
                <div className="flex items-center justify-between text-[11px] text-espresso-600">
                  <span>Total Potential Discount vs MRP:</span>
                  <span className="font-medium text-espresso-900">
                    {currencySymbol}{landedCost.total_potential_savings.toLocaleString('en-IN')}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between text-[10px] text-espresso-500 bg-ivory-100/80 p-2 rounded-xl border border-rose-100">
                <span>Genuine Verified Market Savings:</span>
                <span className="font-semibold text-espresso-700">
                  {currencySymbol}0 (Demo catalog data)
                </span>
              </div>
            </div>
          </div>

          {/* Test Promotional Coupon Input */}
          <form onSubmit={handleApplyCoupon} className="pt-2 space-y-2">
            <span className="text-[11px] font-semibold text-espresso-700 block">
              Test Simulated Promo Code (Demo):
            </span>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="e.g. NYKBEAUTY10, TIRA100"
                  value={couponInput}
                  onChange={(e) => setCouponInput(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 bg-white rounded-xl border border-rose-200 text-xs font-mono uppercase text-espresso-950 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-400"
                />
              </div>
              <button
                type="submit"
                disabled={applyingCoupon || !couponInput.trim()}
                className="px-4 py-2 bg-espresso-950 hover:bg-espresso-900 disabled:opacity-50 text-white text-xs font-medium rounded-xl transition-all shadow-2xs"
              >
                {applyingCoupon ? 'Checking...' : 'Apply'}
              </button>
            </div>

            {couponError && (
              <p className="text-[11px] text-rose-600 flex items-center gap-1">
                <X className="w-3.5 h-3.5" />
                {couponError}
              </p>
            )}

            {landedCost.coupon_applied?.is_valid && (
              <div className="p-2.5 rounded-xl bg-amber-50/80 border border-amber-200/70 text-[11px] text-amber-900 space-y-1">
                <p className="flex items-center gap-1 font-semibold text-amber-950">
                  <Check className="w-3.5 h-3.5 text-amber-700" />
                  {landedCost.coupon_applied.description}
                </p>
                <p className="text-[10px] text-amber-800 leading-normal">
                  ⚠ Simulated test coupon for platform evaluation. Coupon terms and eligibility have not been verified with retailer.
                </p>
              </div>
            )}
          </form>
        </div>
      )}
    </div>
  );
};

export default DealScoreCard;
