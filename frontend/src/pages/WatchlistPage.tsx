import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Heart,
  Bell,
  Trash2,
  ArrowRight,
  ShieldAlert,
  CheckCircle2,
  Clock,
  CloudOff,
  UserCheck,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { removeFromWatchlist } from '../utils/api';

import { PRODUCTS_DATA } from '../data/products';
import { useWishlist } from '../hooks/useWishlist';
import { usePriceTracker } from '../hooks/usePriceTracker';
import { PriceTrackingModal } from '../components/PriceTrackingModal';
import type { Product } from '../types';

export const WatchlistPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, openAuthModal } = useAuth();
  const { wishlist, toggleWishlist } = useWishlist();

  const handleRemoveFromWishlist = async (id: string) => {
    toggleWishlist(id);
    if (user) {
      const numericId = parseInt(id.replace('prod-', ''), 10);
      if (!isNaN(numericId)) {
        await removeFromWatchlist(numericId);
      }
    }
  };
  const {
    trackedProducts,
    alerts,
    unreadAlertCount,
    startTracking,
    stopTracking,
    markAlertAsRead,
    markAllAlertsAsRead,
    clearAlert,
  } = usePriceTracker();

  const [activeTab, setActiveTab] = useState<'watchlist' | 'alerts'>('watchlist');
  const [selectedProductForModal, setSelectedProductForModal] = useState<Product | null>(null);

  // Resolve wishlisted products
  const wishlistedItems = wishlist
    .map((id) => PRODUCTS_DATA.find((p) => p.id === id))
    .filter((p): p is Product => Boolean(p));

  // Resolve tracked products with joined catalog info
  const trackedItemsWithProduct = trackedProducts
    .map((t) => {
      const prod = PRODUCTS_DATA.find((p) => p.id === t.productId);
      return { tracking: t, product: prod };
    })
    .filter((item): item is { tracking: typeof item.tracking; product: Product } => Boolean(item.product));

  return (
    <div className="min-h-screen bg-ivory text-espresso-900 pb-20 pt-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Page Headline */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-rose-100 pb-6">
          <div>
            <div className="text-xs font-bold uppercase tracking-widest text-rose-500 mb-1">
              Personal Shopping Intelligence
            </div>
            <h1 className="font-editorial text-3xl sm:text-4xl font-bold text-espresso-950">
              Watchlist & Price Tracking
            </h1>
            <p className="text-sm text-espresso-600 mt-1 max-w-xl">
              Monitor saved beauty favorites, configure INR target purchase thresholds, and view in-app alerts when prices drop.
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="flex items-center space-x-1 bg-white p-1 rounded-2xl border border-rose-200 shadow-2xs self-start sm:self-auto">
            <button
              onClick={() => setActiveTab('watchlist')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 ${activeTab === 'watchlist'
                  ? 'bg-espresso-800 text-ivory shadow-xs'
                  : 'text-espresso-600 hover:text-espresso-950'
                }`}
            >
              <Heart className="w-3.5 h-3.5" />
              <span>Watchlist ({wishlistedItems.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('alerts')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 relative ${activeTab === 'alerts'
                  ? 'bg-espresso-800 text-ivory shadow-xs'
                  : 'text-espresso-600 hover:text-espresso-950'
                }`}
            >
              <Bell className="w-3.5 h-3.5" />
              <span>Alerts ({alerts.length})</span>
              {unreadAlertCount > 0 && (
                <span className="w-2 h-2 rounded-full bg-rose-500 absolute top-1.5 right-1.5 ring-2 ring-white"></span>
              )}
            </button>
          </div>
        </div>

        {/* Tab 1: Watchlist & Active Trackers */}
        {activeTab === 'watchlist' && (
          <div className="space-y-8">
            {/* Cloud Sync Status Banner */}
            {user ? (
              <div className="p-4 rounded-2xl bg-sage-500/10 border border-sage-300/80 text-xs text-sage-900 flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <UserCheck className="w-4 h-4 text-sage-600 shrink-0" />
                  <span>
                    <strong>Cloud Sync Active:</strong> Linked to your account (<strong>{user.email}</strong>). Items are backed up across devices.
                  </span>
                </div>
                <span className="hidden sm:inline px-2 py-0.5 rounded-full bg-sage-100 text-sage-700 font-bold text-[10px]">
                  Synchronized
                </span>
              </div>
            ) : (
              <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200/80 text-xs text-rose-800 flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <CloudOff className="w-4 h-4 text-rose-500 shrink-0" />
                  <span>
                    <strong>Guest Mode:</strong> Your saved items are stored in your browser only. Sign in to sync across devices.
                  </span>
                </div>
                <button
                  onClick={() => openAuthModal('login')}
                  className="px-3 py-1 rounded-xl bg-rose-500 hover:bg-rose-600 text-ivory text-[11px] font-semibold transition-all shrink-0 ml-3 shadow-xs"
                >
                  Sign In to Sync
                </button>
              </div>
            )}

            {/* Active Monitoring Notice */}
            <div className="p-4 rounded-2xl bg-champagne-50/70 border border-champagne-200/90 text-xs text-espresso-700 flex items-start space-x-3">
              <ShieldAlert className="w-5 h-5 text-champagne-700 shrink-0 mt-0.5" />
              <div>
                <strong>Monitoring Status:</strong> Tracked items evaluate on-demand against monitored retailer feeds (Nykaa, Tira, Purplle, Amazon India, Myntra).
                External background email delivery is currently unconfigured; notifications are delivered in-app.
              </div>
            </div>

            {/* Tracked Products with Target Price */}
            {trackedItemsWithProduct.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="font-editorial text-2xl font-bold text-espresso-900">
                    Active Price-Drop Trackers ({trackedItemsWithProduct.length})
                  </h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {trackedItemsWithProduct.map(({ tracking, product }) => {
                    const currentPrice = product.price;
                    const targetPrice = tracking.targetPrice;
                    const diff = currentPrice - targetPrice;
                    const isTargetReached = currentPrice <= targetPrice;

                    return (
                      <div
                        key={tracking.id}
                        className="p-5 rounded-3xl bg-white border border-rose-200/90 shadow-soft-lift flex flex-col justify-between space-y-4"
                      >
                        <div className="flex items-start space-x-4">
                          <img
                            src={product.image}
                            alt={product.name}
                            className="w-16 h-16 object-cover rounded-2xl border border-rose-100 shrink-0"
                          />
                          <div className="flex-1 min-w-0">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-rose-500 block">
                              {product.brand} • {product.quantity}
                            </span>
                            <Link
                              to={`/product/${product.slug || product.id}`}
                              className="font-editorial text-base font-bold text-espresso-900 hover:text-rose-600 transition-colors line-clamp-1"
                            >
                              {product.name}
                            </Link>

                            <div className="mt-2 flex items-baseline space-x-3">
                              <div>
                                <span className="text-[10px] text-espresso-400 block">Current Lowest</span>
                                <span className="text-base font-extrabold text-espresso-950 font-sans">
                                  ₹{currentPrice.toLocaleString('en-IN')}
                                </span>
                              </div>
                              <div className="border-l border-rose-100 pl-3">
                                <span className="text-[10px] text-espresso-400 block">Target Threshold</span>
                                <span className="text-base font-extrabold text-rose-600 font-sans">
                                  ₹{targetPrice.toLocaleString('en-IN')}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Progress Status Bar */}
                        <div className="pt-2 border-t border-rose-100 text-xs">
                          {isTargetReached ? (
                            <div className="flex items-center space-x-1.5 text-sage-800 bg-sage-50 px-3 py-1.5 rounded-xl border border-sage-200">
                              <CheckCircle2 className="w-4 h-4 text-sage-600 shrink-0" />
                              <span className="font-bold">
                                🎯 Target Met! Current price is ₹{Math.abs(diff)} below target.
                              </span>
                            </div>
                          ) : (
                            <div className="flex items-center justify-between text-espresso-600 bg-ivory-50 px-3 py-1.5 rounded-xl border border-rose-100">
                              <span>Needs price drop:</span>
                              <strong className="text-rose-600 font-sans">
                                -₹{diff} ({Math.round((diff / currentPrice) * 100)}% drop needed)
                              </strong>
                            </div>
                          )}

                          {tracking.note && (
                            <p className="text-[11px] text-espresso-500 italic mt-2">
                              Note: "{tracking.note}"
                            </p>
                          )}
                        </div>

                        {/* Action buttons */}
                        <div className="flex items-center justify-between pt-1">
                          <button
                            onClick={() => setSelectedProductForModal(product)}
                            className="text-xs text-rose-600 hover:text-rose-700 font-semibold"
                          >
                            Edit Target Price
                          </button>

                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => stopTracking(product.id)}
                              className="p-2 text-espresso-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                              title="Remove Tracker"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                            <Link
                              to={`/product/${product.slug || product.id}`}
                              className="px-3.5 py-1.5 rounded-xl bg-espresso-800 text-ivory text-xs font-bold flex items-center space-x-1 hover:bg-espresso-950 transition-colors"
                            >
                              <span>View Product</span>
                              <ArrowRight className="w-3 h-3" />
                            </Link>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Saved Wishlist Items */}
            <div className="space-y-4">
              <h2 className="font-editorial text-2xl font-bold text-espresso-900">
                Saved Wishlist Items ({wishlistedItems.length})
              </h2>

              {wishlistedItems.length === 0 ? (
                <div className="text-center p-12 bg-white rounded-3xl border border-rose-200/80 space-y-3">
                  <Heart className="w-10 h-10 text-rose-300 mx-auto" />
                  <h3 className="text-base font-bold text-espresso-800">Your Wishlist is Empty</h3>
                  <p className="text-xs text-espresso-500 max-w-sm mx-auto">
                    Save your favourite skincare and makeup products while browsing to keep track of prices and set custom alerts.
                  </p>
                  <button
                    onClick={() => navigate('/')}
                    className="mt-2 px-5 py-2.5 rounded-xl bg-espresso-800 text-ivory text-xs font-bold hover:bg-espresso-950 transition-colors"
                  >
                    Explore Beauty Catalog
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {wishlistedItems.map((product) => {
                    const isTracked = trackedProducts.some((t) => t.productId === product.id);

                    return (
                      <div
                        key={product.id}
                        className="p-4 rounded-3xl bg-white border border-rose-100 shadow-soft-lift flex flex-col justify-between space-y-3"
                      >
                        <div className="flex items-center space-x-3">
                          <img
                            src={product.image}
                            alt={product.name}
                            className="w-14 h-14 object-cover rounded-xl border border-rose-100 shrink-0"
                          />
                          <div className="min-w-0 flex-1">
                            <span className="text-[10px] font-bold text-rose-500 uppercase block">
                              {product.brand}
                            </span>
                            <Link
                              to={`/product/${product.slug || product.id}`}
                              className="font-editorial text-sm font-bold text-espresso-900 hover:text-rose-600 transition-colors line-clamp-1"
                            >
                              {product.name}
                            </Link>
                            <span className="text-sm font-extrabold text-espresso-950 font-sans mt-0.5 block">
                              ₹{product.price.toLocaleString('en-IN')}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t border-rose-50">
                          <button
                            type="button"
                            onClick={() => setSelectedProductForModal(product)}
                            className="px-3 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold flex items-center space-x-1 transition-colors"
                          >
                            <Bell className="w-3 h-3" />
                            <span>{isTracked ? 'Update Target' : 'Track Price'}</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleRemoveFromWishlist(product.id)}
                            className="p-1.5 text-espresso-400 hover:text-rose-600 rounded-lg transition-colors"
                            title="Remove from wishlist"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: In-App Price Alerts */}
        {activeTab === 'alerts' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-editorial text-2xl font-bold text-espresso-900">
                  In-App Price-Drop Alerts ({alerts.length})
                </h2>
                <p className="text-xs text-espresso-500">
                  Real alerts triggered by monitored price changes. External email delivery is unconfigured.
                </p>
              </div>

              {unreadAlertCount > 0 && (
                <button
                  onClick={markAllAlertsAsRead}
                  className="px-3 py-1.5 rounded-xl bg-ivory-100 hover:bg-ivory-200 text-espresso-700 text-xs font-bold transition-colors"
                >
                  Mark All Read
                </button>
              )}
            </div>

            {alerts.length === 0 ? (
              <div className="text-center p-12 bg-white rounded-3xl border border-rose-200/80 space-y-3">
                <Bell className="w-10 h-10 text-rose-300 mx-auto" />
                <h3 className="text-base font-bold text-espresso-800">No Alerts Recorded</h3>
                <p className="text-xs text-espresso-500 max-w-sm mx-auto">
                  When a monitored product drops in price or meets your target threshold, an in-app alert will appear here.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-4 sm:p-5 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${alert.isRead
                        ? 'bg-white border-rose-100 opacity-80'
                        : 'bg-rose-50/40 border-rose-300 shadow-2xs'
                      }`}
                  >
                    <div className="flex items-start space-x-3.5">
                      <img
                        src={alert.productImage}
                        alt={alert.productName}
                        className="w-12 h-12 rounded-xl object-cover border border-rose-200 shrink-0"
                      />
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-sm text-espresso-900">
                            {alert.productName}
                          </span>
                          {!alert.isRead && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500 text-ivory">
                              NEW
                            </span>
                          )}
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-ivory-100 text-espresso-600 border border-rose-100">
                            {alert.deliveryStatus === 'in_app_delivered' ? 'In-App Alert' : 'Pending'}
                          </span>
                        </div>

                        <p className="text-xs text-espresso-700 mt-1 leading-relaxed">
                          {alert.message}
                        </p>

                        <div className="flex items-center space-x-3 text-[11px] text-espresso-400 mt-1.5">
                          <span className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{alert.timestamp}</span>
                          </span>
                          <span>•</span>
                          <span>Store: <strong>{alert.storeName}</strong></span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end space-x-3 shrink-0">
                      {!alert.isRead && (
                        <button
                          onClick={() => markAlertAsRead(alert.id)}
                          className="text-xs text-espresso-500 hover:text-espresso-800 font-semibold"
                        >
                          Mark Read
                        </button>
                      )}

                      <button
                        onClick={() => clearAlert(alert.id)}
                        className="p-1.5 text-espresso-400 hover:text-rose-600 transition-colors"
                        title="Delete Alert"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>

                      <Link
                        to={`/product/${alert.productId}`}
                        className="px-3.5 py-2 rounded-xl bg-espresso-800 text-ivory text-xs font-bold hover:bg-espresso-950 transition-colors"
                      >
                        View Deal ↗
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Target Price Modal */}
      {selectedProductForModal && (
        <PriceTrackingModal
          isOpen={Boolean(selectedProductForModal)}
          onClose={() => setSelectedProductForModal(null)}
          product={selectedProductForModal}
          existingRecord={trackedProducts.find((t) => t.productId === selectedProductForModal.id)}
          onSaveTarget={(target, note) => startTracking(selectedProductForModal.id, target, note)}
          onRemoveTracking={() => stopTracking(selectedProductForModal.id)}
        />
      )}
    </div>
  );
};
