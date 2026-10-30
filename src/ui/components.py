"""Reusable UI components for PriceWise AI."""

import streamlit as st
import altair as alt
import pandas as pd
from src.config import DEMO_BADGE_LABEL, PRODUCT_IMAGE_FALLBACK
from src.database.models import Product
from src.analysis.deal_detector import analyze_product_deal, DealAnalysis
from src.services.comparison_service import ComparisonSummary, build_price_history_dataframe
from src.services.wishlist_service import is_in_wishlist, add_to_wishlist, remove_product_from_wishlist


def render_demo_banner():
    """Renders prominent demo data warning required for academic project transparency."""
    st.markdown(
        f"""
        <div class="demo-banner">
            <div>
                <strong>{DEMO_BADGE_LABEL}</strong>
                <span>All products, prices, store names, and historical trends are curated simulated records for academic evaluation.</span>
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; white-space: nowrap;">
                Academic Prototype v0.2
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats_bar(total_products: int, total_offers: int, real_deals_count: int, max_savings: float):
    """Renders top-level shopping intelligence metrics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Products Analyzed</div>
                <div class="stat-value">{total_products}</div>
                <div class="stat-sub">Across Monitored Feeds</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Store Offers Monitored</div>
                <div class="stat-value">{total_offers}</div>
                <div class="stat-sub">Demo Retail Feeds</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Active Real Deals</div>
                <div class="stat-value" style="color: #10b981;">{real_deals_count}</div>
                <div class="stat-sub">Below Historical Norms</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Max Arbitrage Spread</div>
                <div class="stat-value" style="color: #6366f1;">${max_savings:,.2f}</div>
                <div class="stat-sub">Verified In-Stock Delta</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def get_pill_class(verdict: str) -> str:
    """Map deal verdict to CSS pill style."""
    if verdict == "ALL-TIME LOW":
        return "deal-pill-emerald"
    elif verdict == "GREAT DEAL":
        return "deal-pill-blue"
    elif verdict in ("FAIR PRICE", "CONSIDER"):
        return "deal-pill-indigo"
    elif verdict == "ABOVE AVERAGE":
        return "deal-pill-amber"
    else:
        return "deal-pill-red"


def render_product_card(product: Product, analysis: DealAnalysis | None):
    """Renders an attractive product card with shopping intelligence tags."""
    verdict = analysis.verdict if analysis else "MONITORED"
    pill_class = get_pill_class(verdict)
    lowest_price = product.lowest_price
    has_available = product.available_offer_count > 0

    # Calculate spread only across available offers
    available_prices = [o.current_price for o in product.available_offers]
    if len(available_prices) >= 2:
        savings_delta = round(max(available_prices) - min(available_prices), 2)
    else:
        savings_delta = 0.0

    with st.container():
        # Pricing subtext
        if has_available and lowest_price is not None:
            price_display = f"${lowest_price:,.2f}"
            price_subtext = "Starting from"
            stock_info = f"{product.offer_count} offers ({product.available_offer_count} in stock)"
        elif lowest_price is not None:
            price_display = f"${lowest_price:,.2f}"
            price_subtext = "Last listed price"
            stock_info = "<span style='color: #dc2626; font-weight: 600;'>Out of Stock</span>"
        else:
            price_display = "N/A"
            price_subtext = "No active offers"
            stock_info = "Unavailable"

        st.markdown(
            f"""
            <div class="product-card">
                <div>
                    <div class="card-badge-container">
                        <span class="category-tag">{product.category}</span>
                        <span class="deal-pill {pill_class}">{verdict}</span>
                    </div>
                    <div class="product-img-wrapper">
                        <img src="{product.image_url or PRODUCT_IMAGE_FALLBACK}" alt="{product.title}" loading="lazy" onerror="this.onerror=null;this.src='{PRODUCT_IMAGE_FALLBACK}';" />
                    </div>
                    <div class="product-brand">{product.brand}</div>
                    <div class="product-title" title="{product.title}">{product.title}</div>
                </div>
                <div>
                    <div class="pricing-block">
                        <div class="price-sub">{price_subtext}</div>
                        <div class="price-main">{price_display}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                            <span class="price-sub">{stock_info}</span>
                            {f'<span class="price-savings">Save ${savings_delta:,.2f}</span>' if savings_delta > 0 else ''}
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_c_btn, col_w_btn = st.columns([3.5, 1])
        with col_c_btn:
            if st.button("📊 Compare Stores", key=f"btn_comp_{product.id}", use_container_width=True):
                st.session_state["selected_product_id"] = product.id
                st.session_state["current_view"] = "comparison"
                st.rerun()

        with col_w_btn:
            user = st.session_state.get("authenticated_user")
            in_wish = is_in_wishlist(user.id, product.id) if user else False
            btn_txt = "💖" if in_wish else "🤍"
            btn_help = "In your Wishlist (Click to remove)" if in_wish else "Add to Wishlist"
            if st.button(btn_txt, key=f"btn_card_wish_{product.id}", use_container_width=True, help=btn_help):
                if user:
                    if in_wish:
                        remove_product_from_wishlist(user.id, product.id)
                    else:
                        add_to_wishlist(user.id, product.id)
                    st.rerun()
                else:
                    st.toast("Please log in or register via the sidebar to save items to your wishlist.")


def render_real_deal_detector(analysis: DealAnalysis):
    """
    Renders the flagship Real Deal Detector intelligence panel.
    Evaluates current price against recorded historical price data,
    displays evidence sufficiency, price trend, and suspicious discount alerts.
    """
    badge_bg = analysis.verdict_badge_color
    rec = analysis.recommendation

    # Confidence CSS mapping
    conf_class = "confidence-insufficient"
    if analysis.confidence_level == "High Confidence":
        conf_class = "confidence-high"
    elif analysis.confidence_level == "Moderate Confidence":
        conf_class = "confidence-moderate"
    elif analysis.confidence_level == "Low Confidence":
        conf_class = "confidence-low"

    # Score Circle Content
    if analysis.deal_score is not None:
        score_html = f"""
            <div class="score-circle">
                <span class="score-num">{analysis.deal_score}</span>
                <span class="score-label">Deal Score</span>
            </div>
        """
    else:
        score_html = """
            <div class="score-circle" style="border-color: #94a3b8; background: rgba(148, 163, 184, 0.1);">
                <span class="score-num" style="font-size: 1.15rem; color: #cbd5e1;">N/A</span>
                <span class="score-label" style="font-size: 0.55rem; color: #94a3b8;">INSUFFICIENT</span>
            </div>
        """

    # Formatted values with N/A guards
    hist_min_str = f"${analysis.historical_min:,.2f}" if analysis.historical_min is not None else "--"
    hist_avg_str = f"${analysis.historical_avg:,.2f}" if analysis.historical_avg is not None else "--"
    hist_max_str = f"${analysis.historical_max:,.2f}" if analysis.historical_max is not None else "--"
    recent_avg_str = f"${analysis.recent_avg:,.2f}" if analysis.recent_avg is not None else "--"
    
    if analysis.discount_vs_historical_avg_pct is not None and analysis.diff_from_avg is not None:
        direction = "below" if analysis.diff_from_avg <= 0 else "above"
        diff_avg_str = f"{analysis.discount_vs_historical_avg_pct:+.1f}% ({direction})"
    elif analysis.discount_vs_historical_avg_pct is not None:
        diff_avg_str = f"{analysis.discount_vs_historical_avg_pct:+.1f}% vs Avg"
    else:
        diff_avg_str = "--"

    if analysis.is_all_time_low:
        diff_min_str = "★ All-Time Low"
    elif analysis.pct_diff_from_min is not None:
        diff_min_str = f"{analysis.pct_diff_from_min:+.1f}% vs Min"
    else:
        diff_min_str = "Recorded Low"

    last_obs_str = analysis.last_observed_at[:16] if analysis.last_observed_at else "Recent"

    # Good value badge
    if analysis.is_good_value:
        value_chip = '<span style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 9999px; border: 1px solid rgba(52, 211, 153, 0.4);">✓ GOOD VALUE</span>'
    elif analysis.is_sufficient_history:
        value_chip = '<span style="background: rgba(148, 163, 184, 0.15); color: #cbd5e1; font-size: 0.72rem; font-weight: 600; padding: 3px 8px; border-radius: 9999px;">● REGULAR VALUE</span>'
    else:
        value_chip = '<span style="background: rgba(148, 163, 184, 0.15); color: #94a3b8; font-size: 0.72rem; font-weight: 600; padding: 3px 8px; border-radius: 9999px;">INSUFFICIENT DATA</span>'

    st.markdown(
        f"""
        <div class="detector-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                <div style="max-width: 70%;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap;">
                        <span class="detector-badge" style="background-color: {badge_bg}; color: white;">
                            {analysis.verdict}
                        </span>
                        <span class="confidence-chip {conf_class}">
                            {analysis.confidence_level}
                        </span>
                        {value_chip}
                        <span style="font-size: 0.78rem; letter-spacing: 0.05em; color: #94a3b8; text-transform: uppercase;">
                            Recommendation: <strong style="color: white;">{rec}</strong>
                        </span>
                    </div>
                    <h2 style="margin: 0 0 8px 0; font-size: 1.45rem; font-weight: 800; color: #ffffff;">
                        Real Deal Detector™ Evaluation
                    </h2>
                    <p style="margin: 0; font-size: 0.94rem; line-height: 1.5; color: #cbd5e1;">
                        {analysis.explanation}
                    </p>
                </div>
                <div style="display: flex; gap: 18px; align-items: center;">
                    {score_html}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-top: 22px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.12);">
                <div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Current Best</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #38bdf8;">${analysis.current_best_price:,.2f}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">at {analysis.best_offer.store_name}</div>
                </div>
                <div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Historical Min</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #34d399;">{hist_min_str}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">{diff_min_str}</div>
                </div>
                <div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Historical Average</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9;">{hist_avg_str}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">{diff_avg_str}</div>
                </div>
                <div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Recent (7-Day) Avg</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #e2e8f0;">{recent_avg_str}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">Trend: {analysis.price_trend}</div>
                </div>
                <div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Historical Max</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #f87171;">{hist_max_str}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">Peak Observed</div>
                </div>
                <div>
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">Observation Evidence</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #a78bfa;">{analysis.total_data_points} obs</div>
                    <div style="font-size: 0.7rem; color: #64748b;">Last: {last_obs_str}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Suspicious Discount Alert Section (if active)
    if analysis.suspicious_discount.has_warning:
        alert = analysis.suspicious_discount
        alert_class = "suspicious-alert-caution" if alert.warning_level == "caution" else "suspicious-alert-notice"
        icon = "⚠️" if alert.warning_level == "caution" else "ℹ️"
        st.markdown(
            f"""
            <div class="suspicious-alert-box {alert_class}">
                <div class="suspicious-alert-title">
                    <span>{icon}</span> {alert.headline}
                </div>
                <div class="suspicious-alert-desc">
                    {alert.explanation}
                </div>
                <div class="suspicious-alert-evidence">
                    <strong>Historical Evidence:</strong> {alert.historical_evidence}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_comparison_table(summary: ComparisonSummary):
    """Renders the detailed multi-store comparison table with strict matching and availability awareness."""
    # Savings explanation banner
    box_class = "savings-verified-box" if summary.has_verified_savings else "savings-unverified-box"
    icon = "💰" if summary.has_verified_savings else "ℹ️"
    st.markdown(
        f"""
        <div class="{box_class}">
            <strong>{icon} Shopping Intelligence:</strong> {summary.savings_claim_explanation}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Inform if any offers were excluded due to variant mismatch
    if summary.non_comparable_offers:
        st.info(
            f"Note: {len(summary.non_comparable_offers)} offer(s) were excluded from this comparison "
            "because specifications or variants did not match the target model."
        )

    rows_html = ""
    for offer in summary.ranked_offers:
        is_available = offer.is_available
        is_lowest_total = (
            summary.lowest_total_cost_offer is not None
            and offer.id == summary.lowest_total_cost_offer.id
            and is_available
        )
        is_lowest_base = (
            summary.lowest_available_offer is not None
            and offer.id == summary.lowest_available_offer.id
            and is_available
            and not is_lowest_total
        )

        row_class = 'class="best-row"' if is_lowest_total else ('class="oos-row"' if not is_available else "")

        badge = ""
        if is_lowest_total:
            badge = '<span style="background: #dcfce7; color: #15803d; font-size: 0.72rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">★ BEST TOTAL DEAL</span>'
        elif is_lowest_base:
            badge = '<span style="background: #e0f2fe; color: #0369a1; font-size: 0.72rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">★ LOWEST ITEM PRICE</span>'

        shipping_text = "FREE" if offer.shipping_cost == 0 else f"${offer.shipping_cost:,.2f}"

        if is_available:
            avail_html = f'<span style="color: #15803d; font-weight: 600; font-size: 0.82rem;">● {offer.availability}</span>'
        else:
            avail_html = f'<span class="oos-badge">● {offer.availability}</span>'

        last_updated = offer.last_checked[:16] if offer.last_checked else "Recent"

        rows_html += f"""
        <tr {row_class}>
            <td>
                <strong>{offer.store_name}</strong> {badge}<br/>
                <span class="trust-badge">★ {offer.store_rating} Rating</span>
            </td>
            <td>
                <span class="match-badge">✓ Exact Match</span><br/>
                <span style="font-size: 0.8rem; color: #475569;">{offer.variant_name}</span><br/>
                <span style="font-size: 0.72rem; color: #94a3b8;">{offer.condition}</span>
            </td>
            <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700;">
                ${offer.current_price:,.2f}
                {f'<br/><span style="text-decoration: line-through; color: #94a3b8; font-size: 0.78rem;">${offer.original_price:,.2f}</span>' if offer.original_price else ''}
            </td>
            <td style="color: #64748b; font-size: 0.88rem;">
                {shipping_text}
            </td>
            <td style="font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 1.05rem; color: #0f172a;">
                ${offer.total_cost:,.2f}
            </td>
            <td>
                {avail_html}<br/>
                <span style="font-size: 0.7rem; color: #94a3b8;">Checked: {last_updated}</span>
            </td>
            <td>
                <span style="background: #f1f5f9; color: #475569; padding: 6px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; cursor: not-allowed;" title="Demo link (not an external live store)">
                    Demo Store ↗
                </span>
            </td>
        </tr>
        """

    st.markdown(
        f"""
        <div style="margin-top: 10px; margin-bottom: 24px; overflow-x: auto;">
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Store & Reliability</th>
                        <th>Variant & Match</th>
                        <th>Product Price</th>
                        <th>Est. Shipping</th>
                        <th>Total Checkout</th>
                        <th>Status & Timestamp</th>
                        <th>Demo Store Link</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_price_history_chart(product: Product, analysis: DealAnalysis | None, window: str = "all"):
    """Renders interactive historical price trend chart using Altair with window filtering."""
    df = build_price_history_dataframe(product, window=window)
    if df.empty:
        st.info(
            f"No recorded historical price observations found in the selected {window.upper()} window. "
            "Broaden the time window above to inspect earlier historical trends."
        )
        return

    # Base line + points chart
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Date:T", title="Timeline (Recorded Historical Checks)"),
            y=alt.Y("Price:Q", title=f"Price ({df['Currency'].iloc[0] if not df.empty else 'USD'})", scale=alt.Scale(zero=False)),
            color=alt.Color("Store:N", title="Store Feeds", scale=alt.Scale(scheme="category10")),
            tooltip=[
                alt.Tooltip("Date:T", title="Observed Date"),
                alt.Tooltip("Store:N", title="Retailer"),
                alt.Tooltip("Price:Q", format="$.2f", title="Price"),
                alt.Tooltip("Data Status:N", title="Status"),
            ],
        )
        .properties(height=340)
        .interactive()
    )

    layers = [chart]

    # Add historical average guideline if available
    if analysis and analysis.historical_avg is not None:
        avg_df = pd.DataFrame([{"Historical Average": analysis.historical_avg}])
        rule_avg = (
            alt.Chart(avg_df)
            .mark_rule(color="#94a3b8", strokeDash=[6, 4], size=1.5)
            .encode(y="Historical Average:Q")
        )
        layers.append(rule_avg)

    # Add historical minimum guideline if available
    if analysis and analysis.historical_min is not None:
        min_df = pd.DataFrame([{"Historical Min": analysis.historical_min}])
        rule_min = (
            alt.Chart(min_df)
            .mark_rule(color="#10b981", strokeDash=[3, 3], size=1.5)
            .encode(y="Historical Min:Q")
        )
        layers.append(rule_min)

    final_chart = alt.layer(*layers)
    st.altair_chart(final_chart, use_container_width=True)

    st.markdown(
        "<div style='font-size: 0.75rem; color: #94a3b8; text-align: right; margin-top: -10px; margin-bottom: 20px;'>"
        "★ Green dotted line = Historical Min &nbsp;|&nbsp; ── Gray dashed line = Historical Average &nbsp;|&nbsp; "
        "<strong>DEMO DATASET</strong>"
        "</div>",
        unsafe_allow_html=True,
    )
