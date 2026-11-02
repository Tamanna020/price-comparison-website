"""Home / Catalog View for PriceWise AI.
Provides functional search, combined category & brand filtering, multi-criteria sorting,
in-stock toggles, session-state preservation, and empty-state handling.
"""

import streamlit as st
from src.services.product_service import (
    get_products,
    get_all_categories,
    get_all_brands,
    get_all_skin_types,
    get_all_product_types,
)
from src.analysis.deal_detector import analyze_product_deal
from src.ui.components import render_stats_bar, render_product_card


def init_filter_state():
    """Ensure filter state keys exist in session state to preserve selections across reruns."""
    if "filter_search" not in st.session_state:
        st.session_state["filter_search"] = ""
    if "filter_category" not in st.session_state:
        st.session_state["filter_category"] = "All"
    if "filter_brand" not in st.session_state:
        st.session_state["filter_brand"] = "All"
    if "filter_skin_type" not in st.session_state:
        st.session_state["filter_skin_type"] = "All"
    if "filter_budget" not in st.session_state:
        st.session_state["filter_budget"] = "All"
    if "filter_sort" not in st.session_state:
        default_sort = "featured"
        user = st.session_state.get("authenticated_user")
        if user:
            try:
                from src.services.preference_service import get_user_preferences
                uprefs = get_user_preferences(user.id)
                if uprefs and uprefs.sort_preference:
                    alias_map = {
                        "best_deal": "best_deal",
                        "lowest_price": "price_asc",
                        "highest_price": "price_desc",
                        "name": "title_asc",
                        "name_asc": "title_asc",
                    }
                    candidate = alias_map.get(uprefs.sort_preference, uprefs.sort_preference)
                    if candidate in ("featured", "price_asc", "price_desc", "title_asc", "title_desc", "savings_desc", "best_deal"):
                        default_sort = candidate
            except Exception:
                pass
        st.session_state["filter_sort"] = default_sort
    if "filter_in_stock_only" not in st.session_state:
        st.session_state["filter_in_stock_only"] = False


def reset_filters():
    """Reset all search and filter controls to default."""
    st.session_state["filter_search"] = ""
    st.session_state["filter_category"] = "All"
    st.session_state["filter_brand"] = "All"
    st.session_state["filter_skin_type"] = "All"
    st.session_state["filter_budget"] = "All"
    st.session_state["filter_sort"] = "featured"
    st.session_state["filter_in_stock_only"] = False


def render_home_view():
    """Render the main search, filtering, and product browsing catalog."""
    init_filter_state()

    # Top Headline
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #C98991; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                ✨ Discover Beauty • Compare Smarter
            </div>
            <h1 style="font-size: 2.4rem; font-weight: 800; color: #302724; margin: 0 0 6px 0; letter-spacing: -0.02em;">
                PriceWise <span style="color: #4A1D2F;">AI Beauty</span>
            </h1>
            <p style="font-size: 1.05rem; color: #574d49; margin: 0; line-height: 1.5;">
                Your beauty. Your budget. Your best match. Discover authentic Indian skincare and makeup, compare prices across Nykaa, Tira, Purplle, Amazon India, and Myntra with <strong>Real Deal Detector™</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Advisor & React Frontend Quick-Link Banner
    col_banner_text, col_banner_btn = st.columns([4, 1])
    with col_banner_text:
        st.markdown(
            """
            <div style="background: linear-gradient(90deg, #FDF7F8 0%, #F8EDEF 100%); border: 1px solid #EED4D8; border-radius: 8px; padding: 10px 14px; font-size: 0.88rem; color: #4A1D2F; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span>✨</span> <strong>PriceWise Beauty Hub:</strong> Smart Purchase Advisor, verified ingredient comparisons, and lowest price intelligence across Indian retailers.
                </div>
                <a href="http://localhost:5173" target="_blank" style="display: inline-flex; align-items: center; gap: 4px; background: #4A1D2F; color: #FAF7F2; padding: 4px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; text-decoration: none;">
                    Launch React Editorial UI ↗
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_banner_btn:
        if st.button("🧭 Try Advisor ↗", key="btn_open_advisor_banner", use_container_width=True):
            st.session_state["current_view"] = "advisor"
            st.rerun()

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # Search & Filter Toolbar
    # Row 1: Search bar, Category selector, Brand selector, Sort selector
    col_search, col_cat, col_brand, col_sort = st.columns([3, 2, 2, 2])

    with col_search:
        search_input = st.text_input(
            "Search Products",
            value=st.session_state["filter_search"],
            placeholder="🔍 Search name, brand, SKU (e.g. M3, XM5, Dell, S24)...",
            label_visibility="collapsed",
            key="input_search_box",
        )
        if search_input != st.session_state["filter_search"]:
            st.session_state["filter_search"] = search_input

    categories = ["All"] + get_all_categories()
    with col_cat:
        cat_index = categories.index(st.session_state["filter_category"]) if st.session_state["filter_category"] in categories else 0
        selected_category = st.selectbox(
            "Category",
            options=categories,
            index=cat_index,
            label_visibility="collapsed",
            key="select_category_box",
        )
        if selected_category != st.session_state["filter_category"]:
            st.session_state["filter_category"] = selected_category
            # Reset brand if the selected brand is not in the new category
            st.session_state["filter_brand"] = "All"
            st.rerun()

    # Dynamic Brands based on selected category
    available_brands = ["All"] + get_all_brands(category=st.session_state["filter_category"])
    with col_brand:
        brand_index = (
            available_brands.index(st.session_state["filter_brand"])
            if st.session_state["filter_brand"] in available_brands
            else 0
        )
        selected_brand = st.selectbox(
            "Brand",
            options=available_brands,
            index=brand_index,
            label_visibility="collapsed",
            key="select_brand_box",
        )
        if selected_brand != st.session_state["filter_brand"]:
            st.session_state["filter_brand"] = selected_brand

    sort_options = {
        "featured": "✨ Featured",
        "best_deal": "🔥 Best Available Deal",
        "price_asc": "💵 Price: Low to High",
        "price_desc": "💎 Price: High to Low",
        "title_asc": "🔤 Name: A to Z",
        "title_desc": "🔤 Name: Z to A",
        "savings_desc": "🔥 Biggest Price Spread",
    }
    with col_sort:
        sort_keys = list(sort_options.keys())
        sort_index = sort_keys.index(st.session_state["filter_sort"]) if st.session_state["filter_sort"] in sort_keys else 0
        selected_sort = st.selectbox(
            "Sort by",
            options=sort_keys,
            format_func=lambda x: sort_options[x],
            index=sort_index,
            label_visibility="collapsed",
            key="select_sort_box",
        )
        if selected_sort != st.session_state["filter_sort"]:
            st.session_state["filter_sort"] = selected_sort

    # Row 2: Secondary Beauty Filters (Skin Type, Budget Preset, In-Stock, Reset)
    col_skin, col_budget, col_stock, col_reset = st.columns([2.5, 2.5, 2.5, 2])

    skin_types = ["All"] + get_all_skin_types()
    with col_skin:
        skin_index = skin_types.index(st.session_state["filter_skin_type"]) if st.session_state["filter_skin_type"] in skin_types else 0
        selected_skin = st.selectbox(
            "Skin Type",
            options=skin_types,
            index=skin_index,
            format_func=lambda s: f"Skin: {s}" if s != "All" else "All Skin Types",
            key="select_skin_type_box",
            label_visibility="collapsed",
        )
        if selected_skin != st.session_state["filter_skin_type"]:
            st.session_state["filter_skin_type"] = selected_skin
            st.rerun()

    budget_options = ["All", "Under ₹500", "₹500 - ₹1,000", "₹1,000 - ₹2,000", "Luxury (₹2,000+)"]
    with col_budget:
        budget_index = budget_options.index(st.session_state["filter_budget"]) if st.session_state["filter_budget"] in budget_options else 0
        selected_budget = st.selectbox(
            "Budget",
            options=budget_options,
            index=budget_index,
            format_func=lambda b: f"Budget: {b}" if b != "All" else "Any Budget",
            key="select_budget_box",
            label_visibility="collapsed",
        )
        if selected_budget != st.session_state["filter_budget"]:
            st.session_state["filter_budget"] = selected_budget
            st.rerun()

    with col_stock:
        in_stock_checked = st.checkbox(
            "In-Stock Only",
            value=st.session_state["filter_in_stock_only"],
            key="cb_in_stock_only",
        )
        if in_stock_checked != st.session_state["filter_in_stock_only"]:
            st.session_state["filter_in_stock_only"] = in_stock_checked
            st.rerun()

    has_active_filters = (
        bool(st.session_state["filter_search"].strip())
        or st.session_state["filter_category"] != "All"
        or st.session_state["filter_brand"] != "All"
        or st.session_state["filter_skin_type"] != "All"
        or st.session_state["filter_budget"] != "All"
        or st.session_state["filter_sort"] != "featured"
        or st.session_state["filter_in_stock_only"]
    )

    with col_reset:
        if has_active_filters:
            if st.button("✕ Reset Filters", use_container_width=True, key="btn_clear_filters"):
                reset_filters()
                st.rerun()

    # Parse budget into min_price and max_price bounds
    min_price: float | None = None
    max_price: float | None = None
    if st.session_state["filter_budget"] == "Under ₹500":
        max_price = 500.0
    elif st.session_state["filter_budget"] == "₹500 - ₹1,000":
        min_price = 500.0
        max_price = 1000.0
    elif st.session_state["filter_budget"] == "₹1,000 - ₹2,000":
        min_price = 1000.0
        max_price = 2000.0
    elif st.session_state["filter_budget"] == "Luxury (₹2,000+)":
        min_price = 2000.0

    # Query products with combined criteria
    products = get_products(
        category=st.session_state["filter_category"],
        brand=st.session_state["filter_brand"],
        skin_type=st.session_state["filter_skin_type"],
        search_query=st.session_state["filter_search"],
        in_stock_only=st.session_state["filter_in_stock_only"],
        min_price=min_price,
        max_price=max_price,
        sort_by=st.session_state["filter_sort"],
    )

    # Pre-analyze products for summary metrics
    analyses = {p.id: analyze_product_deal(p) for p in products}
    total_offers = sum(len(p.offers) for p in products)
    real_deals_count = sum(
        1 for a in analyses.values() if a and a.verdict in ("ALL-TIME LOW", "GREAT DEAL")
    )
    max_savings = 0.0
    for p in products:
        avail_prices = [o.current_price for o in p.available_offers]
        if len(avail_prices) >= 2:
            spread = max(avail_prices) - min(avail_prices)
            if spread > max_savings:
                max_savings = spread

    # Render Intelligence Stat Bar
    render_stats_bar(
        total_products=len(products),
        total_offers=total_offers,
        real_deals_count=real_deals_count,
        max_savings=max_savings,
    )

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Catalog Header & Active Filter Tags
    results_count = len(products)
    cat_label = f"in '{st.session_state['filter_category']}'" if st.session_state["filter_category"] != "All" else "across all categories"
    brand_label = f" by '{st.session_state['filter_brand']}'" if st.session_state["filter_brand"] != "All" else ""
    search_label = f" matching '{st.session_state['filter_search']}'" if st.session_state["filter_search"] else ""

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
            <div style="font-size: 1.15rem; font-weight: 700; color: #1e293b;">
                Found {results_count} product{"s" if results_count != 1 else ""} {cat_label}{brand_label}{search_label}
            </div>
            <div style="font-size: 0.8rem; color: #64748b;">
                Real-time multi-store price intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Empty State Handling
    if not products:
        st.markdown(
            """
            <div class="empty-state-box">
                <div style="font-size: 2.2rem; margin-bottom: 8px;">🔍</div>
                <div class="empty-state-title">No matching products found</div>
                <div class="empty-state-desc">
                    We couldn't find any products matching your specific combination of keywords and filters.
                    Try broadening your search term, selecting "All Brands", or disabling the in-stock filter.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
        with col_c2:
            if st.button("🔄 Reset All Filters & Show Full Catalog", use_container_width=True, key="btn_empty_reset"):
                reset_filters()
                st.rerun()
        return

    # Render grid of product cards (3 columns)
    cols = st.columns(3)
    for idx, product in enumerate(products):
        with cols[idx % 3]:
            render_product_card(product, analyses.get(product.id))
