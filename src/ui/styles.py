"""CSS Styles for PriceWise AI UI."""

CUSTOM_CSS = """
<style>
/* Global Imports & Base Typography */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus+Jakarta+Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* Header & Banner */
.demo-banner {
    background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
    border-left: 4px solid #f59e0b;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #e2e8f0;
    font-size: 0.88rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.06);
}

.demo-banner strong {
    color: #fbbf24;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-size: 0.78rem;
    padding: 2px 8px;
    background: rgba(245, 158, 11, 0.15);
    border-radius: 4px;
    margin-right: 8px;
}

/* Intelligence Stat Bar */
.stat-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
}

.stat-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.stat-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #0f172a;
    margin-top: 4px;
}

.stat-sub {
    font-size: 0.75rem;
    color: #10b981;
    font-weight: 500;
    margin-top: 2px;
}

/* Product Card */
.product-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    margin-bottom: 20px;
}

.product-card:hover {
    border-color: #6366f1;
    transform: translateY(-3px);
    box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.card-badge-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.category-tag {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #6366f1;
    background: #eef2ff;
    padding: 3px 8px;
    border-radius: 6px;
    letter-spacing: 0.04em;
}

.deal-pill {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.deal-pill-emerald {
    background: #ecfdf5;
    color: #059669;
    border: 1px solid #a7f3d0;
}

.deal-pill-blue {
    background: #eff6ff;
    color: #2563eb;
    border: 1px solid #bfdbfe;
}

.deal-pill-indigo {
    background: #eef2ff;
    color: #4f46e5;
    border: 1px solid #c7d2fe;
}

.deal-pill-amber {
    background: #fffbeb;
    color: #d97706;
    border: 1px solid #fde68a;
}

.deal-pill-red {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
}

.product-img-wrapper {
    width: 100%;
    height: 180px;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 14px;
    background: #f8fafc;
    display: flex;
    align-items: center;
    justify-content: center;
}

.product-img-wrapper img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    padding: 6px;
    transition: transform 0.2s ease;
}

.product-card:hover .product-img-wrapper img {
    transform: scale(1.03);
}

.product-brand {
    font-size: 0.78rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    margin-bottom: 4px;
}

.product-title {
    font-size: 0.98rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.35;
    margin-bottom: 12px;
    min-height: 2.7em;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.pricing-block {
    background: #f8fafc;
    border-radius: 8px;
    padding: 10px 12px;
    margin-top: auto;
    margin-bottom: 12px;
}

.price-main {
    font-size: 1.35rem;
    font-weight: 800;
    color: #0f172a;
    font-family: 'JetBrains Mono', monospace;
}

.price-sub {
    font-size: 0.78rem;
    color: #64748b;
}

.price-savings {
    font-size: 0.78rem;
    font-weight: 600;
    color: #059669;
}

/* Real Deal Detector Intelligence Card */
.detector-card {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 16px;
    padding: 24px;
    color: #ffffff;
    box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.25);
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}

.detector-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.score-circle {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 90px;
    height: 90px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    border: 3px solid #6366f1;
    text-align: center;
}

.score-num {
    font-size: 1.8rem;
    font-weight: 900;
    line-height: 1;
    font-family: 'JetBrains Mono', monospace;
}

.score-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    color: #94a3b8;
    margin-top: 2px;
}

/* Comparison Table Styling */
.comparison-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
    margin-top: 16px;
    background: #ffffff;
}

.comparison-table th {
    background: #f8fafc;
    color: #475569;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 14px 16px;
    border-bottom: 2px solid #e2e8f0;
    text-align: left;
}

.comparison-table td {
    padding: 16px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 0.92rem;
    color: #1e293b;
    vertical-align: middle;
}

.comparison-table tr:last-child td {
    border-bottom: none;
}

.comparison-table tr:hover {
    background-color: #f8fafc;
}

.best-row {
    background-color: #f0fdf4 !important;
}

.oos-row {
    background-color: #f8fafc !important;
    opacity: 0.72;
}

.trust-badge {
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #475569;
}

.match-badge {
    background: #e0e7ff;
    color: #4338ca;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}

.oos-badge {
    background: #fee2e2;
    color: #991b1b;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
}

.empty-state-box {
    background: #ffffff;
    border: 1px dashed #cbd5e1;
    border-radius: 14px;
    padding: 40px 24px;
    text-align: center;
    margin: 24px 0;
}

.empty-state-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 8px;
}

.empty-state-desc {
    font-size: 0.92rem;
    color: #64748b;
    max-width: 500px;
    margin: 0 auto 20px auto;
    line-height: 1.5;
}

.savings-verified-box {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #16a34a;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 14px;
    margin-bottom: 16px;
    color: #166534;
    font-size: 0.9rem;
    line-height: 1.5;
}

.savings-unverified-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #94a3b8;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 14px;
    margin-bottom: 16px;
    color: #475569;
    font-size: 0.9rem;
    line-height: 1.5;
}

/* Suspicious Discount Alerts */
.suspicious-alert-box {
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 18px;
    margin-bottom: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.suspicious-alert-caution {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 4px solid #d97706;
    color: #92400e;
}

.suspicious-alert-notice {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 4px solid #2563eb;
    color: #1e40af;
}

.suspicious-alert-title {
    font-size: 0.95rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;
}

.suspicious-alert-desc {
    font-size: 0.88rem;
    line-height: 1.45;
}

.suspicious-alert-evidence {
    font-size: 0.8rem;
    font-weight: 600;
    opacity: 0.9;
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px dashed rgba(0,0,0,0.1);
}

.confidence-chip {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.confidence-high {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
}

.confidence-moderate {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
}

.confidence-low {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
}

.confidence-insufficient {
    background: rgba(148, 163, 184, 0.2);
    color: #cbd5e1;
}

/* Smart Purchase Advisor Styles (Phase 5) */
.advisor-rec-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.advisor-rec-card:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
}

.advisor-badge-overall {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: #ffffff;
    font-size: 0.76rem;
    font-weight: 800;
    padding: 5px 12px;
    border-radius: 20px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    display: inline-block;
}

.advisor-badge-budget {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: #ffffff;
    font-size: 0.76rem;
    font-weight: 800;
    padding: 5px 12px;
    border-radius: 20px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    display: inline-block;
}

.advisor-badge-deal {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
    color: #ffffff;
    font-size: 0.76rem;
    font-weight: 800;
    padding: 5px 12px;
    border-radius: 20px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    display: inline-block;
}

.advisor-badge-alternative {
    background: #f1f5f9;
    color: #475569;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 12px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: 1px solid #cbd5e1;
    display: inline-block;
}

.spec-chip {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    color: #334155;
    font-size: 0.76rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    display: inline-block;
    margin-right: 6px;
    margin-bottom: 6px;
}

.budget-headroom-positive {
    color: #15803d;
    background: #dcfce7;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 700;
    display: inline-block;
}

.budget-headroom-negative {
    color: #b91c1c;
    background: #fee2e2;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 700;
    display: inline-block;
}

/* Phase 6: Price Tracking & Alerts Styles */
.tracker-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.tracker-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
}

.alert-item-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 14px;
}

.alert-item-unread {
    background: #f8fafc;
    border-left: 4px solid #6366f1;
}

.alert-item-read {
    border-left: 4px solid #cbd5e1;
    opacity: 0.85;
}

.badge-target-reached {
    background: #dcfce7;
    color: #15803d;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 12px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-price-drop {
    background: #e0f2fe;
    color: #0369a1;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 12px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-status-active {
    background: #ecfdf5;
    color: #059669;
    border: 1px solid #a7f3d0;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 10px;
}

.badge-status-paused {
    background: #fffbeb;
    color: #b45309;
    border: 1px solid #fde68a;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 10px;
}
</style>
"""

