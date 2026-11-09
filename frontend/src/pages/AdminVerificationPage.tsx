import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Clock,
  AlertCircle,
  ArrowLeft,
  Image as ImageIcon,
  RefreshCw,
} from 'lucide-react';
import {
  getAdminVerificationQueue,
  approveManualVerificationRequest,
  rejectManualVerificationRequest,
  approvePriceCorrectionSubmission,
  rejectPriceCorrectionSubmission,
  type AdminVerificationItem,
} from '../utils/api';

export const AdminVerificationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'verifications' | 'corrections'>('verifications');
  const [manualList, setManualList] = useState<AdminVerificationItem[]>([]);
  const [correctionList, setCorrectionList] = useState<AdminVerificationItem[]>([]);
  const [totalPending, setTotalPending] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Approval modal state
  const [selectedItem, setSelectedItem] = useState<AdminVerificationItem | null>(null);
  const [isApproveOpen, setIsApproveOpen] = useState<boolean>(false);
  const [approvePrice, setApprovePrice] = useState<string>('');
  const [approveMrp, setApproveMrp] = useState<string>('');
  const [approveNotes, setApproveNotes] = useState<string>('');
  const [isSubmittingAction, setIsSubmittingAction] = useState<boolean>(false);

  // Rejection modal state
  const [isRejectOpen, setIsRejectOpen] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('');

  // Evidence preview modal state
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null);

  const loadQueue = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getAdminVerificationQueue();
      if (res.success) {
        setManualList(res.manualVerifications);
        setCorrectionList(res.priceCorrections);
        setTotalPending(res.totalPending);
      } else {
        setError(res.error || 'Failed to fetch verification queue. Admin privileges required.');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error loading queue');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const handleOpenApprove = (item: AdminVerificationItem) => {
    setSelectedItem(item);
    const initialPrice = item.user_submitted_price ?? item.submitted_price ?? '';
    const initialMrp = item.submitted_mrp ?? '';
    setApprovePrice(String(initialPrice));
    setApproveMrp(String(initialMrp));
    setApproveNotes(item.notes || 'Verified against evidence');
    setIsApproveOpen(true);
  };

  const handleOpenReject = (item: AdminVerificationItem) => {
    setSelectedItem(item);
    setRejectReason('Variant mismatch or unverifiable evidence');
    setIsRejectOpen(true);
  };

  const submitApproval = async () => {
    if (!selectedItem) return;
    const priceNum = parseFloat(approvePrice);
    if (isNaN(priceNum) || priceNum <= 0) {
      alert('Please enter a valid positive price.');
      return;
    }
    const mrpNum = approveMrp ? parseFloat(approveMrp) : undefined;
    if (mrpNum !== undefined && mrpNum < priceNum) {
      alert('MRP cannot be lower than verified price.');
      return;
    }

    setIsSubmittingAction(true);
    try {
      let res;
      if (activeTab === 'verifications') {
        res = await approveManualVerificationRequest(selectedItem.id, {
          verified_price: priceNum,
          verified_mrp: mrpNum,
          notes: approveNotes,
        });
      } else {
        res = await approvePriceCorrectionSubmission(selectedItem.id, {
          verified_price: priceNum,
          verified_mrp: mrpNum,
          notes: approveNotes,
        });
      }

      if (res.success) {
        setIsApproveOpen(false);
        setSelectedItem(null);
        await loadQueue();
      } else {
        alert(res.error || 'Approval failed');
      }
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const submitRejection = async () => {
    if (!selectedItem || !rejectReason.trim()) return;

    setIsSubmittingAction(true);
    try {
      let res;
      if (activeTab === 'verifications') {
        res = await rejectManualVerificationRequest(selectedItem.id, rejectReason.trim());
      } else {
        res = await rejectPriceCorrectionSubmission(selectedItem.id, rejectReason.trim());
      }

      if (res.success) {
        setIsRejectOpen(false);
        setSelectedItem(null);
        await loadQueue();
      } else {
        alert(res.error || 'Rejection failed');
      }
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const currentItems = activeTab === 'verifications' ? manualList : correctionList;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back button & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-rose-200 pb-6">
        <div>
          <Link
            to="/"
            className="inline-flex items-center space-x-1.5 text-xs font-semibold text-espresso-600 hover:text-espresso-950 transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Catalog</span>
          </Link>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-espresso-900 text-ivory flex items-center justify-center font-bold">
              <ShieldCheck className="w-5 h-5 text-rose-300" />
            </div>
            <div>
              <h1 className="font-editorial text-2xl sm:text-3xl font-bold text-espresso-950">
                Price Verification & Evidence Queue
              </h1>
              <p className="text-xs text-espresso-500">
                Phase 11B Admin Portal — Review genuine retailer evidence, validate unit prices, and approve verified offers.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300">
            {totalPending} Pending Approvals
          </span>
          <button
            type="button"
            onClick={loadQueue}
            disabled={isLoading}
            className="px-3 py-2 rounded-xl border border-rose-200 bg-white hover:bg-rose-50 text-espresso-800 text-xs font-semibold flex items-center space-x-1.5 shadow-2xs transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-rose-600' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-rose-200">
        <button
          type="button"
          onClick={() => setActiveTab('verifications')}
          className={`px-5 py-3 text-xs sm:text-sm font-bold border-b-2 transition-all flex items-center space-x-2 ${
            activeTab === 'verifications'
              ? 'border-espresso-900 text-espresso-950'
              : 'border-transparent text-espresso-500 hover:text-espresso-800'
          }`}
        >
          <span>Manual Price Verifications</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-rose-100 text-rose-800">
            {manualList.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('corrections')}
          className={`px-5 py-3 text-xs sm:text-sm font-bold border-b-2 transition-all flex items-center space-x-2 ${
            activeTab === 'corrections'
              ? 'border-espresso-900 text-espresso-950'
              : 'border-transparent text-espresso-500 hover:text-espresso-800'
          }`}
        >
          <span>Price Correction Submissions</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-rose-100 text-rose-800">
            {correctionList.length}
          </span>
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2.5">
          <AlertCircle className="w-5 h-5 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Queue items */}
      {isLoading ? (
        <div className="p-12 text-center text-espresso-500 text-sm animate-pulse">
          Loading verification queue...
        </div>
      ) : currentItems.length === 0 ? (
        <div className="p-12 text-center rounded-3xl border border-dashed border-rose-200 bg-white space-y-2">
          <CheckCircle2 className="w-8 h-8 text-sage-600 mx-auto" />
          <h3 className="font-bold text-sm text-espresso-900">All caught up!</h3>
          <p className="text-xs text-espresso-500">
            There are no pending {activeTab === 'verifications' ? 'price verification requests' : 'price correction submissions'} in the review queue.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {currentItems.map((item) => {
            const price = item.user_submitted_price ?? item.submitted_price;
            const mrp = item.submitted_mrp ?? item.verified_mrp;
            const submittedDate = item.submitted_at || item.created_at;

            return (
              <div
                key={item.id}
                className="p-5 rounded-3xl border border-rose-200 bg-white shadow-soft-lift space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-base text-espresso-950">
                        {item.product_title || `Product #${item.product_id}`}
                      </span>
                      {item.product_brand && (
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-ivory-100 text-espresso-700 border border-rose-100">
                          {item.product_brand}
                        </span>
                      )}
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                        {item.retailer}
                      </span>
                    </div>

                    <p className="text-xs text-espresso-500 mt-1 flex items-center space-x-2">
                      <span>Submitted by <strong>{item.user_name || item.user_email || 'User'}</strong></span>
                      {submittedDate && (
                        <>
                          <span>•</span>
                          <span className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{new Date(submittedDate).toLocaleString('en-IN')}</span>
                          </span>
                        </>
                      )}
                    </p>
                  </div>

                  <div className="text-left sm:text-right">
                    <span className="text-xs text-espresso-500 block">Submitted Price:</span>
                    <span className="text-xl font-bold font-sans text-espresso-950">
                      ₹{price ? price.toLocaleString('en-IN') : 'N/A'}
                    </span>
                    {mrp && mrp > (price || 0) && (
                      <span className="text-xs text-espresso-400 block line-through">
                        MRP: ₹{mrp.toLocaleString('en-IN')}
                      </span>
                    )}
                  </div>
                </div>

                {/* Variant and Notes metadata */}
                <div className="p-3.5 rounded-2xl bg-ivory-50 border border-rose-100 text-xs grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <div>
                    <span className="text-espresso-400 block text-[11px]">Size / Volume:</span>
                    <span className="font-medium text-espresso-800">{item.size_volume || 'Standard / Unspecified'}</span>
                  </div>
                  <div>
                    <span className="text-espresso-400 block text-[11px]">Shade / Formulation:</span>
                    <span className="font-medium text-espresso-800">{item.shade || item.formulation || 'Standard'}</span>
                  </div>
                  <div>
                    <span className="text-espresso-400 block text-[11px]">Retailer Product URL:</span>
                    <a
                      href={item.product_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-rose-700 hover:underline flex items-center space-x-1 truncate"
                    >
                      <span className="truncate">{item.product_url}</span>
                      <ExternalLink className="w-3 h-3 shrink-0" />
                    </a>
                  </div>
                </div>

                {item.notes && (
                  <p className="text-xs text-espresso-700 bg-rose-50/50 p-2.5 rounded-xl border border-rose-100">
                    <strong>User Notes:</strong> {item.notes}
                  </p>
                )}

                {/* Uploaded Evidence References */}
                {item.evidence && item.evidence.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-bold text-espresso-700 uppercase tracking-wider block">
                      Uploaded Proof & Evidence ({item.evidence.length})
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {item.evidence.map((ev) => (
                        <button
                          key={ev.id}
                          type="button"
                          onClick={() => setPreviewImageUrl(ev.evidence_url)}
                          className="px-3 py-1.5 rounded-xl border border-rose-200 bg-white hover:bg-rose-50 text-xs font-medium text-espresso-800 flex items-center space-x-1.5 transition-all shadow-2xs"
                        >
                          <ImageIcon className="w-3.5 h-3.5 text-rose-500" />
                          <span>View Evidence Screenshot</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-end space-x-3 pt-3 border-t border-rose-100">
                  <button
                    type="button"
                    onClick={() => handleOpenReject(item)}
                    className="px-4 py-2 rounded-xl border border-rose-200 bg-white hover:bg-rose-50 text-rose-700 text-xs font-bold transition-all shadow-2xs flex items-center space-x-1.5"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleOpenApprove(item)}
                    className="px-5 py-2 rounded-xl bg-espresso-900 hover:bg-espresso-950 text-ivory text-xs font-bold transition-all shadow-xs flex items-center space-x-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4 text-sage-400" />
                    <span>Approve & Publish Live</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Approval Modal */}
      {isApproveOpen && selectedItem && (
        <div className="fixed inset-0 z-50 bg-espresso-950/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 space-y-4 border border-rose-200 shadow-2xl">
            <h3 className="font-editorial text-xl font-bold text-espresso-950">
              Approve & Verify Retailer Price
            </h3>
            <p className="text-xs text-espresso-600">
              Publishing will update the product's catalog offer, append to immutable price history, and trigger price alerts for tracking users.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-espresso-800 block mb-1">Confirmed Selling Price (₹):</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={approvePrice}
                  onChange={(e) => setApprovePrice(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-rose-200 focus:outline-hidden focus:ring-2 focus:ring-rose-300"
                />
              </div>

              <div>
                <label className="font-bold text-espresso-800 block mb-1">Confirmed MRP / List Price (₹) (Optional):</label>
                <input
                  type="number"
                  step="0.01"
                  value={approveMrp}
                  onChange={(e) => setApproveMrp(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-rose-200 focus:outline-hidden focus:ring-2 focus:ring-rose-300"
                />
              </div>

              <div>
                <label className="font-bold text-espresso-800 block mb-1">Verification Audit Notes:</label>
                <input
                  type="text"
                  value={approveNotes}
                  onChange={(e) => setApproveNotes(e.target.value)}
                  placeholder="e.g. Verified via official retailer invoice / screenshot"
                  className="w-full px-3 py-2 rounded-xl border border-rose-200 focus:outline-hidden focus:ring-2 focus:ring-rose-300"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-rose-100">
              <button
                type="button"
                onClick={() => setIsApproveOpen(false)}
                className="px-4 py-2 rounded-xl border border-rose-200 text-espresso-700 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmittingAction}
                onClick={submitApproval}
                className="px-5 py-2 rounded-xl bg-espresso-900 hover:bg-espresso-950 text-ivory text-xs font-bold disabled:opacity-50"
              >
                {isSubmittingAction ? 'Processing...' : 'Confirm Approval'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rejection Modal */}
      {isRejectOpen && selectedItem && (
        <div className="fixed inset-0 z-50 bg-espresso-950/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 space-y-4 border border-rose-200 shadow-2xl">
            <h3 className="font-editorial text-xl font-bold text-espresso-950">
              Reject Verification Request
            </h3>
            <p className="text-xs text-espresso-600">
              State the rejection reason clearly for audit compliance.
            </p>

            <div className="text-xs space-y-1.5">
              <label className="font-bold text-espresso-800 block">Rejection Reason:</label>
              <textarea
                rows={3}
                required
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Explain why this price verification cannot be approved..."
                className="w-full px-3 py-2 rounded-xl border border-rose-200 focus:outline-hidden focus:ring-2 focus:ring-rose-300"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-rose-100">
              <button
                type="button"
                onClick={() => setIsRejectOpen(false)}
                className="px-4 py-2 rounded-xl border border-rose-200 text-espresso-700 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmittingAction || !rejectReason.trim()}
                onClick={submitRejection}
                className="px-5 py-2 rounded-xl bg-rose-700 hover:bg-rose-800 text-ivory text-xs font-bold disabled:opacity-50"
              >
                {isSubmittingAction ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Evidence Image Preview Modal */}
      {previewImageUrl && (
        <div className="fixed inset-0 z-50 bg-espresso-950/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-espresso-800">Screenshot Evidence</span>
              <button
                type="button"
                onClick={() => setPreviewImageUrl(null)}
                className="text-xs text-espresso-500 hover:text-espresso-950 font-bold"
              >
                Close (ESC)
              </button>
            </div>
            <div className="max-h-[80vh] overflow-auto rounded-2xl border border-rose-200 bg-gray-50 flex items-center justify-center p-2">
              <img
                src={previewImageUrl}
                alt="Uploaded Evidence"
                className="max-w-full max-h-[70vh] object-contain rounded-xl"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
