"""Product Comparison & Deal Intelligence View for PriceWise AI.
Displays matching offers across stores with verified variant matching,
clear lowest-price highlights, and historical pricing charts.
"""

import streamlit as st
from src.config import PRODUCT_IMAGE_FALLBACK
from src.services.product_service import get_product_by_id, get_products
from src.services.comparison_service import generate_comparison_summary
from src.services.price_tracking_service import get_tracking_by_product_id
from src.services.wishlist_service import is_in_wishlist, add_to_wishlist, remove_product_from_wishlist
from src.analysis.deal_detector import analyze_product_deal
from src.ui.components import (
    render_real_deal_detector,
    render_comparison_table,
    render_price_history_chart,
)


def render_comparison_view():
    """Renders the comprehensive multi-store price comparison and deal analysis page."""
    # Top bar: Back to Catalog and Quick Product Switcher
    col_nav_back, col_nav_switch = st.columns([1, 2])

    with col_nav_back:
        if st.button("← Back to Product Catalog", key="btn_back_to_catalog"):
            st.session_state["current_view"] = "home"
            st.rerun()

    all_catalog_products = get_products()
    product_options = {p.id: f"{p.brand} - {p.title}" for p in all_catalog_products}

    current_id = st.session_state.get("selected_product_id")
    if current_id not in product_options and all_catalog_products:
        current_id = all_catalog_products[0].id
        st.session_state["selected_product_id"] = current_id

    with col_nav_switch:
        selected_id = st.selectbox(
            "Switch Product",
            options=list(product_options.keys()),
            format_func=lambda pid: product_options[pid],
            index=list(product_options.keys()).index(current_id) if current_id in product_options else 0,
            label_visibility="collapsed",
            key="comparison_product_selector",
        )
        if selected_id != current_id:
            st.session_state["selected_product_id"] = selected_id
            st.rerun()

    product = get_product_by_id(current_id)
    if not product:
        st.error(f"Product #{current_id} not found.")
        return

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Product Overview Hero
    col_img, col_info = st.columns([1, 2])

    with col_img:
        st.markdown(
            f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; display: flex; align-items: center; justify-content: center; height: 260px; overflow: hidden;">
                <img src="{product.image_url or PRODUCT_IMAGE_FALLBACK}" alt="{product.title}" style="max-height: 100%; max-width: 100%; object-fit: contain;" onerror="this.onerror=null;this.src='{PRODUCT_IMAGE_FALLBACK}';" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_info:
        st.markdown(
            f"""
            <div style="font-size: 0.8rem; font-weight: 700; color: #6366f1; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
                {product.brand} • {product.category} • SKU: {product.sku}
            </div>
            <h1 style="font-size: 1.65rem; font-weight: 800; color: #0f172a; margin: 0 0 10px 0; line-height: 1.3;">
                {product.title}
            </h1>
            <p style="font-size: 0.92rem; color: #475569; line-height: 1.5; margin-bottom: 14px;">
                {product.description}
            </p>
            """,
            unsafe_allow_html=True,
        )

        # Specifications pills
        if product.specs:
            specs_html = " ".join(
                f'<span style="background: #f1f5f9; color: #334155; font-size: 0.75rem; font-weight: 600; padding: 4px 8px; border-radius: 6px; display: inline-block; margin-right: 6px; margin-bottom: 6px;"><strong>{k}:</strong> {v}</span>'
                for k, v in product.specs.items()
            )
            st.markdown(f'<div style="margin-bottom: 12px;">{specs_html}</div>', unsafe_allow_html=True)

        # Tracking and Wishlist Actions
        authenticated_user = st.session_state.get("authenticated_user")
        user_id = authenticated_user.id if authenticated_user else None

        existing_tr = get_tracking_by_product_id(product.id, user_id=user_id)
        in_wish = is_in_wishlist(user_id, product.id) if user_id else False

        col_act1, col_act2 = st.columns([1.2, 1])

        with col_act1:
            if existing_tr:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #059669; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 6px; padding: 6px 12px; width: fit-content;">
                        <span>🔔</span> <strong>Tracking:</strong> ${existing_tr.target_price:,.2f} ({'🎯 Met!' if existing_tr.is_target_reached else 'Active'})
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                if st.button("🔔 Track Price & Set Alert", key=f"btn_quick_track_{product.id}", use_container_width=True):
                    st.session_state["current_view"] = "tracking"
                    st.rerun()

        with col_act2:
            if in_wish:
                if st.button("💖 In Wishlist (Remove)", key=f"btn_wish_toggle_{product.id}", use_container_width=True):
                    remove_product_from_wishlist(user_id, product.id)
                    st.rerun()
            else:
                if st.button("🤍 Add to Wishlist", key=f"btn_wish_toggle_{product.id}", use_container_width=True):
                    if user_id:
                        add_to_wishlist(user_id, product.id)
                        st.success("Added to your wishlist!")
                        st.rerun()
                    else:
                        st.info("Sign in via sidebar to save to wishlist.")

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # Time Window Toolbar
    col_win_title, col_win_pills = st.columns([1, 2])
    with col_win_title:
        st.markdown(
            """
            <div style="font-size: 0.95rem; font-weight: 700; color: #1e293b; padding-top: 4px;">
                ⏱️ Historical Evidence Window:
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_win_pills:
        window_options = {
            "30d": "📅 Last 30 Days",
            "90d": "📆 Last 90 Days",
            "all": "📈 All-Time History",
        }
        window_choice = st.radio(
            "Evidence Window",
            options=list(window_options.keys()),
            format_func=lambda k: window_options[k],
            index=2,  # Default to All-Time
            horizontal=True,
            label_visibility="collapsed",
            key=f"window_choice_{product.id}",
        )

    # 1. Real Deal Detector Evaluation Section
    analysis = analyze_product_deal(product, window=window_choice)
    if analysis:
        render_real_deal_detector(analysis)

    # 2. Multi-Store Comparison Table
    summary = generate_comparison_summary(product)
    if summary:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 10px; flex-wrap: wrap; gap: 8px;">
                <h3 style="font-size: 1.25rem; font-weight: 800; color: #0f172a; margin: 0;">
                    Live Store Price Comparison ({summary.total_stores} Retailers • {summary.total_offers} Offers)
                </h3>
                <span style="font-size: 0.85rem; color: #64748b;">
                    Offers matched by canonical model & variant specifications
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_comparison_table(summary)
    else:
        st.info("No matching store offers available for this item.")

    # 3. Historical Price Trends Chart
    st.markdown(
        f"""
        <div style="margin-top: 20px; margin-bottom: 8px;">
            <h3 style="font-size: 1.25rem; font-weight: 800; color: #0f172a; margin: 0 0 4px 0;">
                Recorded Price History & Volatility Trend ({window_choice.upper()} View)
            </h3>
            <p style="font-size: 0.88rem; color: #64748b; margin: 0 0 12px 0;">
                Timestamped price tracking across stores within the selected window. 
                Dashed line indicates historical average; dotted line indicates historical minimum.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_price_history_chart(product, analysis, window=window_choice)
