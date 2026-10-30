"""Price Tracking & Alerts View for PriceWise AI (Phase 6).
Provides:
- Overview summary metrics (Tracked Products, Active, Reached Targets, Unread Alerts)
- Form to add new products to price tracking with target price validation
- Tracked product cards with target progress, status toggles (pause/resume/edit/remove)
- Mini historical price chart with target price reference overlay
- Alerts inbox with filtering (unread, target reached, price drop) and mark-as-read controls
- Evaluation trigger to check active tracking against stored observations
"""

import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime

from src.services.product_service import get_products, get_product_by_id
from src.services.price_tracking_service import (
    add_tracked_product,
    get_tracked_products,
    update_target_price,
    update_tracking_note,
    pause_tracking,
    resume_tracking,
    remove_tracking,
    evaluate_tracking_rules,
    get_alert_history,
    mark_alert_read,
    mark_all_alerts_read,
    get_tracking_summary_stats,
)
from src.services.comparison_service import build_price_history_dataframe


def render_tracking_chart(product_id: int, target_price: float):
    """Renders a compact price history chart with the user's target price line overlay."""
    product = get_product_by_id(product_id)
    if not product:
        return

    df = build_price_history_dataframe(product, window="all")
    if df.empty:
        st.info("No recorded historical price observations found for this product yet.")
        return

    # Base line chart of recorded prices
    base_chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Date:T", title="Observation Timeline"),
            y=alt.Y("Price:Q", title="Price (USD)", scale=alt.Scale(zero=False)),
            color=alt.Color("Store:N", title="Store Feeds"),
            tooltip=["Date:T", "Store:N", alt.Tooltip("Price:Q", format="$.2f")],
        )
        .properties(height=220)
    )

    # Target Price dashed reference line
    target_df = pd.DataFrame([{"Target Price": target_price}])
    rule_target = (
        alt.Chart(target_df)
        .mark_rule(color="#ef4444", strokeDash=[6, 4], size=2)
        .encode(
            y="Target Price:Q",
            tooltip=[alt.Tooltip("Target Price:Q", format="$.2f", title="Your Target Price")],
        )
    )

    chart = alt.layer(base_chart, rule_target).interactive()
    st.altair_chart(chart, use_container_width=True)
    st.caption("🔴 Red dashed line indicates your configured Target Price.")


def render_tracking_view():
    """Renders the comprehensive Price Tracker & Alerts view."""
    authenticated_user = st.session_state.get("authenticated_user")
    user_id = authenticated_user.id if authenticated_user else None

    # Top Headline
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #6366f1; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                🔔 Autonomous Price Monitoring
            </div>
            <h1 style="font-size: 2.2rem; font-weight: 800; color: #0f172a; margin: 0 0 8px 0;">
                Price Tracker & Alerts
            </h1>
            <p style="font-size: 1rem; color: #475569; margin: 0; line-height: 1.5; max-width: 850px;">
                Track products, specify target purchase thresholds, and review in-app alerts 
                generated when recorded retailer observations meet your criteria.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if authenticated_user:
        st.markdown(
            f"""
            <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 14px; margin-bottom: 18px; font-size: 0.85rem; color: #1e40af; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span>👤</span> <strong>Personal Tracking Active:</strong> {authenticated_user.full_name or authenticated_user.email} 
                    <span style="color: #60a5fa; margin-left: 6px;">({authenticated_user.email})</span>
                </div>
                <div style="font-size: 0.78rem; color: #2563eb; font-weight: 600;">
                    Data Isolated to Member #{authenticated_user.id}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px; margin-bottom: 18px; font-size: 0.85rem; color: #475569; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span>👤</span> <strong>Guest Tracking:</strong> You are currently tracking products in guest mode.
                </div>
                <div style="font-size: 0.78rem; color: #6366f1; font-weight: 600;">
                    Sign in via the sidebar to link alerts to your permanent account.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Live Overview Summary Tiles
    stats = get_tracking_summary_stats(user_id=user_id)

    col_s1, col_s2, col_s3, col_s4, col_eval = st.columns([1, 1, 1, 1, 1.3])

    with col_s1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Tracked Products</div>
                <div class="stat-value">{stats['total_tracked']}</div>
                <div class="stat-sub">In Watchlist</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_s2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Active Monitors</div>
                <div class="stat-value" style="color: #059669;">{stats['active_tracking']}</div>
                <div class="stat-sub">Evaluating Feeds</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_s3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Targets Reached</div>
                <div class="stat-value" style="color: #10b981;">{stats['target_reached']}</div>
                <div class="stat-sub">At / Below Target</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_s4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Unread Alerts</div>
                <div class="stat-value" style="color: #6366f1;">{stats['unread_alerts']}</div>
                <div class="stat-sub">Inbox Notifications</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_eval:
        st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
        if st.button("⚡ Check Observations Now", key="btn_eval_rules", use_container_width=True, help="Evaluates tracked products against stored observations and triggers in-app alerts."):
            eval_res = evaluate_tracking_rules(user_id=user_id)
            if eval_res["alerts_generated"] > 0:
                st.success(f"✓ Evaluated {eval_res['evaluated_count']} product(s). Generated {eval_res['alerts_generated']} new alert(s)!")
            else:
                st.info(f"✓ Evaluated {eval_res['evaluated_count']} product(s). No new price conditions triggered.")
            st.rerun()

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    tab_tracking, tab_alerts = st.tabs(["📋 My Tracked Products", f"📬 Alerts Inbox ({stats['unread_alerts']})"])

    # =================================================================
    # TAB 1: Tracked Products & Add New Product Form
    # =================================================================
    with tab_tracking:
        # Add Product Expander
        with st.expander("➕ Add a Product to Price Tracker", expanded=(stats["total_tracked"] == 0)):
            catalog_products = get_products()
            if not catalog_products:
                st.info("No products available in the catalog to track.")
            else:
                product_map = {
                    p.id: f"{p.brand} - {p.title} (Current: ${p.lowest_price:,.2f})" if p.lowest_price else f"{p.brand} - {p.title}"
                    for p in catalog_products
                }

                col_add_p, col_add_t, col_add_type = st.columns([2, 1, 1])

                with col_add_p:
                    selected_pid = st.selectbox(
                        "Select Product to Track",
                        options=list(product_map.keys()),
                        format_func=lambda pid: product_map[pid],
                        key="tracker_add_product_select",
                    )
                    sel_prod = next((p for p in catalog_products if p.id == selected_pid), None)

                # Default target price to 10% below current price if available
                default_target = round((sel_prod.lowest_price or 100.0) * 0.90, 2) if sel_prod and sel_prod.lowest_price else 100.0

                with col_add_t:
                    target_input = st.number_input(
                        "Target Price ($ USD)",
                        min_value=1.0,
                        max_value=10000.0,
                        value=float(default_target),
                        step=10.0,
                        help="You will receive an in-app alert when recorded price reaches or falls below this target.",
                        key="tracker_add_target_input",
                    )

                with col_add_type:
                    trigger_choice = st.selectbox(
                        "Alert Conditions",
                        options=["target_or_drop", "target_only", "drop_only"],
                        format_func=lambda x: {
                            "target_or_drop": "🎯 Target & 📉 Price Drop",
                            "target_only": "🎯 Target Reached Only",
                            "drop_only": "📉 Price Drop Only",
                        }[x],
                        key="tracker_add_trigger_select",
                    )

                note_input = st.text_input(
                    "Tracking Note (Optional)",
                    placeholder="e.g. Waiting for seasonal promotion or birthday purchase",
                    key="tracker_add_note_input",
                )

                if st.button("🔔 Start Tracking Product", key="btn_confirm_add_tracking", type="primary"):
                    success, msg, _ = add_tracked_product(
                        product_id=selected_pid,
                        target_price=target_input,
                        note=note_input,
                        alert_trigger_type=trigger_choice,
                        user_id=user_id,
                    )
                    if success:
                        st.success(f"✓ {msg}")
                        # Automatically run rule evaluation
                        evaluate_tracking_rules(user_id=user_id)
                        st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")

        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

        # List of Tracked Products
        tracked_records = get_tracked_products(user_id=user_id)

        if not tracked_records:
            st.markdown(
                """
                <div class="empty-state-box">
                    <div style="font-size: 2.2rem; margin-bottom: 8px;">🔔</div>
                    <div class="empty-state-title">No Tracked Products Yet</div>
                    <div class="empty-state-desc">
                        You haven't added any products to your Price Tracker. Use the form above to set your first target price.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for rec in tracked_records:
                status_badge = (
                    '<span class="badge-status-active">● ACTIVE</span>'
                    if rec.is_active
                    else '<span class="badge-status-paused">⏸ PAUSED</span>'
                )

                if rec.is_target_reached:
                    progress_html = f'<span class="badge-target-reached">🎯 TARGET REACHED! (${abs(rec.price_to_target or 0):,.2f} below target)</span>'
                elif rec.price_to_target is not None:
                    progress_html = f'<span style="background: #eff6ff; color: #2563eb; font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 10px;">⏳ ${rec.price_to_target:,.2f} to target ({rec.price_to_target_pct:+.1f}%)</span>'
                else:
                    progress_html = '<span style="background: #f1f5f9; color: #64748b; font-size: 0.72rem; font-weight: 600; padding: 3px 8px; border-radius: 10px;">Price pending</span>'

                cur_price_str = f"${rec.current_lowest_price:,.2f}" if rec.current_lowest_price is not None else "Out of Stock"
                store_str = f"at {rec.current_lowest_store}" if rec.current_lowest_store else ""
                note_html = f'<div style="font-size: 0.8rem; color: #475569; margin-top: 6px; font-style: italic;">📝 Note: {rec.note}</div>' if rec.note else ""
                last_chk = rec.last_checked_at[:16] if rec.last_checked_at else "Recent"

                st.markdown(
                    f"""
                    <div class="tracker-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                            <div>
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                                    {status_badge}
                                    {progress_html}
                                    <span style="font-size: 0.72rem; color: #94a3b8;">Checked: {last_chk}</span>
                                </div>
                                <h3 style="margin: 0 0 4px 0; font-size: 1.25rem; font-weight: 800; color: #0f172a;">
                                    {rec.product_title}
                                </h3>
                                <div style="font-size: 0.82rem; color: #64748b;">
                                    Brand: <strong>{rec.product_brand}</strong> &nbsp;|&nbsp; Category: <strong>{rec.product_category}</strong> &nbsp;|&nbsp; SKU: {rec.product_sku}
                                </div>
                                {note_html}
                            </div>
                            <div style="display: flex; gap: 16px; align-items: baseline; text-align: right;">
                                <div>
                                    <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;">Current Price</div>
                                    <div style="font-size: 1.3rem; font-weight: 800; color: #0f172a; font-family: monospace;">{cur_price_str}</div>
                                    <div style="font-size: 0.72rem; color: #64748b;">{store_str}</div>
                                </div>
                                <div>
                                    <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;">Your Target</div>
                                    <div style="font-size: 1.3rem; font-weight: 800; color: #ef4444; font-family: monospace;">${rec.target_price:,.2f}</div>
                                    <div style="font-size: 0.72rem; color: #64748b;">Trigger: {rec.alert_trigger_type.replace('_', ' ').title()}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Controls Row for Tracked Product
                col_chart, col_action_pause, col_action_edit, col_action_del = st.columns([2.5, 1, 1.2, 1])

                with col_chart:
                    with st.expander(f"📈 Price History & Target Line"):
                        render_tracking_chart(rec.product_id, rec.target_price)

                with col_action_pause:
                    if rec.is_active:
                        if st.button("⏸ Pause", key=f"btn_pause_{rec.id}", use_container_width=True):
                            pause_tracking(rec.id, user_id=user_id)
                            st.rerun()
                    else:
                        if st.button("▶ Resume", key=f"btn_resume_{rec.id}", use_container_width=True):
                            resume_tracking(rec.id, user_id=user_id)
                            evaluate_tracking_rules(tracking_id=rec.id, user_id=user_id)
                            st.rerun()

                with col_action_edit:
                    with st.popover("✏️ Edit Target"):
                        new_t = st.number_input("New Target ($)", value=float(rec.target_price), min_value=1.0, step=10.0, key=f"edit_target_{rec.id}")
                        new_note = st.text_input("Edit Note", value=rec.note or "", key=f"edit_note_{rec.id}")
                        if st.button("Save Changes", key=f"btn_save_target_{rec.id}"):
                            update_target_price(rec.id, new_t, user_id=user_id)
                            if new_note != (rec.note or ""):
                                update_tracking_note(rec.id, new_note, user_id=user_id)
                            evaluate_tracking_rules(tracking_id=rec.id, user_id=user_id)
                            st.success("Target updated!")
                            st.rerun()

                with col_action_del:
                    with st.popover("🗑 Remove"):
                        st.write("Remove tracking for this product?")
                        if st.button("Confirm Delete", key=f"btn_del_conf_{rec.id}", type="primary"):
                            remove_tracking(rec.id, user_id=user_id)
                            st.success("Tracking removed.")
                            st.rerun()

                st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

    # =================================================================
    # TAB 2: Alerts Inbox
    # =================================================================
    with tab_alerts:
        col_f1, col_f2, col_mark_all = st.columns([1.5, 1.5, 1.5])

        with col_f1:
            unread_filter = st.checkbox("Show Unread Only", value=False, key="filter_unread_alerts_cb")

        with col_f2:
            type_filter = st.selectbox(
                "Filter by Alert Type",
                options=["All", "target_reached", "price_drop"],
                format_func=lambda x: {
                    "All": "All Alert Types",
                    "target_reached": "🎯 Target Reached",
                    "price_drop": "📉 Price Drops",
                }[x],
                key="filter_type_alerts_select",
            )

        with col_mark_all:
            if st.button("✓ Mark All as Read", key="btn_mark_all_read", use_container_width=True):
                updated = mark_all_alerts_read(user_id=user_id)
                st.success(f"Marked {updated} alert(s) as read.")
                st.rerun()

        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

        alerts = get_alert_history(user_id=user_id, unread_only=unread_filter, alert_type=type_filter)

        if not alerts:
            st.markdown(
                """
                <div class="empty-state-box">
                    <div style="font-size: 2.2rem; margin-bottom: 8px;">📬</div>
                    <div class="empty-state-title">Your Alerts Inbox is Clear</div>
                    <div class="empty-state-desc">
                        No price alerts match the current filter. Alerts will appear here when recorded prices reach your target or experience meaningful drops.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for alert in alerts:
                box_class = "alert-item-unread" if not alert.is_read else "alert-item-read"
                badge = (
                    '<span class="badge-target-reached">🎯 TARGET REACHED</span>'
                    if alert.alert_type == "target_reached"
                    else '<span class="badge-price-drop">📉 PRICE DROP</span>'
                )

                st.markdown(
                    f"""
                    <div class="alert-item-box {box_class}">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                                {badge}
                                <span style="font-size: 0.72rem; color: #94a3b8;">{alert.created_at}</span>
                                {'<span style="background: #e0e7ff; color: #4338ca; font-size: 0.68rem; font-weight: 700; padding: 2px 6px; border-radius: 4px;">NEW</span>' if not alert.is_read else ''}
                            </div>
                            <h4 style="margin: 0 0 4px 0; font-size: 1.05rem; font-weight: 700; color: #0f172a;">
                                {alert.product_title}
                            </h4>
                            <p style="margin: 0; font-size: 0.88rem; color: #334155; line-height: 1.4;">
                                {alert.message}
                            </p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_a1, col_a2 = st.columns([4, 1])
                with col_a2:
                    if not alert.is_read:
                        if st.button("Mark as Read", key=f"btn_read_{alert.id}", use_container_width=True):
                            mark_alert_read(alert.id, user_id=user_id)
                            st.rerun()

                st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

    # Academic Prototype Notice
    st.markdown(
        """
        <div style="font-size: 0.75rem; color: #94a3b8; text-align: center; margin-top: 30px; padding-top: 14px; border-top: 1px solid #e2e8f0;">
            PriceWise AI Academic Prototype — Tracking is stored locally in the application SQLite database. 
            Price alerts are generated strictly against recorded historical observations (DEMO DATASET). 
            External web scraping or live push notifications are not configured.
        </div>
        """,
        unsafe_allow_html=True,
    )

