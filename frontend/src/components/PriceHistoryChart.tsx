import React, { useState, useEffect } from 'react';
import {
  TrendingDown,
  TrendingUp,
  Minus,
  AlertCircle,
  Calendar,
  Info,
  Clock,
  ShieldAlert,
} from 'lucide-react';
import {
  fetchProductPriceHistory,
  type ProductPriceAnalyticsResponse,
  type PricePointDto,
} from '../utils/api';

interface PriceHistoryChartProps {
  productId?: number | string;
  currencySymbol?: string;
  priceHistory?: unknown;
  currentPrice?: number;
  originalPrice?: number;
  targetPrice?: number;
  productName?: string;
}

export const PriceHistoryChart: React.FC<PriceHistoryChartProps> = ({
  productId = 1,
  currencySymbol = '₹',
}) => {
  const [windowDays, setWindowDays] = useState<7 | 30 | 90>(30);
  const [analytics, setAnalytics] = useState<ProductPriceAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<PricePointDto | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchProductPriceHistory(productId, windowDays)
      .then((res) => {
        if (!isMounted) return;
        if (res.success && res.data) {
          setAnalytics(res.data);
        } else {
          setError(res.error || 'Failed to load price history.');
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : 'Network error');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [productId, windowDays]);

  const points = analytics?.points || [];

  // Compute SVG dimensions & scaling
  const chartWidth = 600;
  const chartHeight = 220;
  const padding = { top: 25, right: 30, bottom: 40, left: 55 };
  const innerWidth = chartWidth - padding.left - padding.right;
  const innerHeight = chartHeight - padding.top - padding.bottom;

  let minPrice = analytics?.lowest_recorded_price ?? 0;
  let maxPrice = analytics?.highest_recorded_price ?? 1000;
  if (minPrice === maxPrice) {
    minPrice = Math.max(0, minPrice - 100);
    maxPrice = maxPrice + 100;
  }
  // Add margin
  const priceRange = maxPrice - minPrice || 1;
  const yMin = Math.max(0, minPrice - priceRange * 0.1);
  const yMax = maxPrice + priceRange * 0.1;
  const ySpan = yMax - yMin || 1;

  const getX = (index: number, total: number) => {
    if (total <= 1) return padding.left + innerWidth / 2;
    return padding.left + (index / (total - 1)) * innerWidth;
  };

  const getY = (price: number) => {
    const norm = (price - yMin) / ySpan;
    return padding.top + innerHeight - norm * innerHeight;
  };

  // Build path data
  const linePoints = points.map((p, i) => `${getX(i, points.length)},${getY(p.price)}`);
  const pathD = linePoints.length > 0 ? `M ${linePoints.join(' L ')}` : '';
  const areaD = linePoints.length > 0
    ? `M ${getX(0, points.length)},${padding.top + innerHeight} L ${linePoints.join(' L ')} L ${getX(points.length - 1, points.length)},${padding.top + innerHeight} Z`
    : '';

  // Trend icon and color
  const renderTrendBadge = () => {
    const trend = analytics?.price_trend || 'stable';
    const movement = analytics?.price_movement_pct ?? 0;

    if (trend === 'downward') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <TrendingDown className="w-3.5 h-3.5" />
          Price Drop ({movement}%)
        </span>
      );
    }
    if (trend === 'upward') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          <TrendingUp className="w-3.5 h-3.5" />
          Price Increase (+{movement}%)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
        <Minus className="w-3.5 h-3.5" />
        Stable Price ({movement > 0 ? `+${movement}%` : `${movement}%`})
      </span>
    );
  };

  return (
    <div className="bg-white rounded-3xl border border-rose-200/80 p-6 shadow-soft-lift space-y-6">
      {/* Header with Title, Period Switcher & Trend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-rose-100">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold tracking-widest uppercase text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
              Price Intelligence
            </span>
            {analytics?.is_simulated && (
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold tracking-wider uppercase text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/80">
                <ShieldAlert className="w-3 h-3 text-amber-600" />
                Demo Data (Simulated)
              </span>
            )}
          </div>
          <h3 className="font-serif text-lg font-bold text-espresso-950 flex items-center gap-2">
            Historical Price Dynamics
          </h3>
        </div>

        {/* Window Selector Tabs */}
        <div className="flex items-center gap-1 bg-ivory-100/80 p-1 rounded-2xl border border-rose-200/60 self-start sm:self-auto">
          {([7, 30, 90] as const).map((days) => (
            <button
              key={days}
              type="button"
              onClick={() => setWindowDays(days)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                windowDays === days
                  ? 'bg-espresso-950 text-white shadow-2xs'
                  : 'text-espresso-700 hover:text-espresso-950 hover:bg-white/60'
              }`}
            >
              {days} Days
            </button>
          ))}
        </div>
      </div>

      {/* Metrics Bar: Lowest, Average, Highest, Trend */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-2xl bg-ivory-50/70 border border-rose-100 space-y-0.5">
          <span className="text-[11px] font-medium text-espresso-500 uppercase tracking-wider block">
            Lowest in {windowDays}d
          </span>
          <p className="text-base font-bold text-espresso-950">
            {analytics?.lowest_recorded_price ? `${currencySymbol}${analytics.lowest_recorded_price.toLocaleString('en-IN')}` : '—'}
          </p>
          <span className="text-[10px] text-espresso-400 block">
            {analytics?.is_simulated ? 'Simulated catalog low' : 'Observed low'}
          </span>
        </div>

        <div className="p-3.5 rounded-2xl bg-ivory-50/70 border border-rose-100 space-y-0.5">
          <span className="text-[11px] font-medium text-espresso-500 uppercase tracking-wider block">
            Average in {windowDays}d
          </span>
          <p className="text-base font-bold text-espresso-950">
            {analytics?.average_recorded_price ? `${currencySymbol}${analytics.average_recorded_price.toLocaleString('en-IN')}` : '—'}
          </p>
          <span className="text-[10px] text-espresso-400 block">Weighted window mean</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-ivory-50/70 border border-rose-100 space-y-0.5">
          <span className="text-[11px] font-medium text-espresso-500 uppercase tracking-wider block">
            Highest in {windowDays}d
          </span>
          <p className="text-base font-bold text-espresso-950">
            {analytics?.highest_recorded_price ? `${currencySymbol}${analytics.highest_recorded_price.toLocaleString('en-IN')}` : '—'}
          </p>
          <span className="text-[10px] text-espresso-400 block">Peak recorded price</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-ivory-50/70 border border-rose-100 flex flex-col justify-between">
          <span className="text-[11px] font-medium text-espresso-500 uppercase tracking-wider block">
            Window Trend
          </span>
          <div className="mt-1">{renderTrendBadge()}</div>
        </div>
      </div>

      {/* SVG Interactive Chart Canvas */}
      <div className="relative bg-ivory-50/40 rounded-2xl border border-rose-100/80 p-4">
        {loading ? (
          <div className="h-48 flex flex-col items-center justify-center gap-2 text-espresso-400">
            <Clock className="w-5 h-5 animate-spin text-rose-500" />
            <span className="text-xs">Loading {windowDays}-day price dynamics...</span>
          </div>
        ) : error ? (
          <div className="h-48 flex flex-col items-center justify-center gap-2 text-rose-700">
            <AlertCircle className="w-5 h-5" />
            <span className="text-xs">{error}</span>
          </div>
        ) : points.length === 0 ? (
          <div className="h-48 flex flex-col items-center justify-center gap-2 text-espresso-400">
            <Calendar className="w-5 h-5 text-espresso-300" />
            <span className="text-xs">No price history points recorded for this {windowDays}-day period.</span>
          </div>
        ) : (
          <div>
            <div className="w-full overflow-x-auto">
              <svg
                viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                className="w-full h-48 select-none overflow-visible"
              >
                <defs>
                  <linearGradient id="roseGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Horizontal Grid lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                  const yVal = padding.top + innerHeight * (1 - ratio);
                  const priceLabel = Math.round(yMin + ratio * ySpan);
                  return (
                    <g key={ratio}>
                      <line
                        x1={padding.left}
                        y1={yVal}
                        x2={padding.left + innerWidth}
                        y2={yVal}
                        stroke="#f3e8e8"
                        strokeDasharray="4 4"
                      />
                      <text
                        x={padding.left - 8}
                        y={yVal + 3}
                        textAnchor="end"
                        fontSize="9"
                        fill="#8c7875"
                        fontWeight="500"
                      >
                        {currencySymbol}{priceLabel}
                      </text>
                    </g>
                  );
                })}

                {/* Shaded Area under Curve */}
                {areaD && (
                  <path d={areaD} fill="url(#roseGradient)" />
                )}

                {/* Line Path */}
                {pathD && (
                  <path
                    d={pathD}
                    fill="none"
                    stroke="#e11d48"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Average Price Dashed Line */}
                {analytics?.average_recorded_price && (
                  <line
                    x1={padding.left}
                    y1={getY(analytics.average_recorded_price)}
                    x2={padding.left + innerWidth}
                    y2={getY(analytics.average_recorded_price)}
                    stroke="#c59b27"
                    strokeDasharray="3 3"
                    strokeWidth="1.2"
                    opacity="0.8"
                  />
                )}

                {/* Interactive Points */}
                {points.map((p, idx) => {
                  const cx = getX(idx, points.length);
                  const cy = getY(p.price);
                  const isHovered = hoveredPoint?.recorded_at === p.recorded_at;
                  return (
                    <g key={`${p.recorded_at}-${idx}`}>
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isHovered ? 6 : 3.5}
                        fill={isHovered ? '#881337' : '#ffffff'}
                        stroke="#e11d48"
                        strokeWidth={isHovered ? 2.5 : 2}
                        className="cursor-pointer transition-all duration-150"
                        onMouseEnter={() => setHoveredPoint(p)}
                        onMouseLeave={() => setHoveredPoint(null)}
                      />
                      {/* Subtle X-axis date labels */}
                      {(idx === 0 || idx === Math.floor(points.length / 2) || idx === points.length - 1) && (
                        <text
                          x={cx}
                          y={chartHeight - 12}
                          textAnchor={idx === 0 ? 'start' : idx === points.length - 1 ? 'end' : 'middle'}
                          fontSize="9"
                          fill="#8c7875"
                          fontWeight="500"
                        >
                          {p.date}
                        </text>
                      )}
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Hover Tooltip display */}
            {hoveredPoint && (
              <div className="mt-2 p-2.5 bg-espresso-950 text-white rounded-xl text-xs flex items-center justify-between shadow-lg border border-espresso-800">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-rose-300">
                    {currencySymbol}{hoveredPoint.price.toLocaleString('en-IN')}
                  </span>
                  <span className="text-espresso-400">|</span>
                  <span className="text-espresso-200">{hoveredPoint.retailer_name}</span>
                  <span className="text-espresso-400">({hoveredPoint.date})</span>
                </div>
                <span className="text-[10px] bg-rose-900/60 text-rose-200 px-2 py-0.5 rounded uppercase font-semibold">
                  {hoveredPoint.data_status.toUpperCase()}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Mandatory Transparency Notice */}
      <div className="p-3.5 rounded-2xl bg-amber-50/60 border border-amber-200/70 text-xs text-amber-900 flex items-start gap-2.5 leading-relaxed">
        <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">Historical Pricing Disclosure</span>
          {analytics?.disclaimer ||
            'Price history is aggregated from catalog records and simulated demo observations. PriceWise AI displays genuine retailer tracking evidence where verified.'}
        </div>
      </div>
    </div>
  );
};
export default PriceHistoryChart;
