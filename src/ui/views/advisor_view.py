"""Smart Purchase Advisor View for PriceWise AI.
Provides explainable, deterministic product recommendations categorized into:
- BEST OVERALL (highest suitability, specs, and price-to-performance)
- BEST BUDGET (maximum savings satisfying user requirements)
- BEST CURRENT DEAL (highest verified Real Deal Score in recorded history)
- CLOSEST ALTERNATIVES (when hard constraints cannot be fully satisfied)
"""

import streamlit as st
from src.database.models import Product
from src.services.product_service import get_all_categories, get_all_brands
from src.services.recommendation_service import (
    AdvisorPreferences,
    ProductEvaluation,
    RecommendationResult,
    get_purchase_recommendations,
)
from src.services.preference_service import get_user_preferences


def render_recommendation_card(eval_item: ProductEvaluation, category_type: str):
    """Renders a single comprehensive recommendation card."""
    prod = eval_item.product
    badge_class = "advisor-badge-overall"
    badge_label = "🌟 BEST OVERALL"
    badge_sub = "Strongest blend of use-case suitability, specifications, and value"

    if category_type == "budget":
        badge_class = "advisor-badge-budget"
        badge_label = "💰 BEST BUDGET"
        badge_sub = "Maximum budget headroom satisfying your essential requirements"
    elif category_type == "deal":
        badge_class = "advisor-badge-deal"
        badge_label = "🏷️ BEST CURRENT DEAL"
        badge_sub = "Verified price markdown relative to recorded historical observations"
    elif category_type == "alternative":
        badge_class = "advisor-badge-alternative"
        badge_label = "ℹ️ CLOSEST ALTERNATIVE"
        badge_sub = "Near-match option requiring a minor budget or specification tradeoff"

    # Deal Classification Badge color
    deal_class_bg = "#94a3b8"
    if eval_item.deal_classification == "EXCELLENT DEAL":
        deal_class_bg = "#10b981"
    elif eval_item.deal_classification == "GOOD DEAL":
        deal_class_bg = "#3b82f6"
    elif eval_item.deal_classification == "FAIR PRICE":
        deal_class_bg = "#6366f1"
    elif eval_item.deal_classification == "POOR DEAL":
        deal_class_bg = "#ef4444"

    # Headroom formatting
    if eval_item.budget_difference >= 0:
        headroom_html = f'<span class="budget-headroom-positive">✓ ${eval_item.budget_difference:,.2f} Under Budget ({eval_item.budget_difference_pct:+.1f}%)</span>'
    else:
        overrun = abs(eval_item.budget_difference)
        headroom_html = f'<span class="budget-headroom-negative">⚠️ ${overrun:,.2f} Over Budget</span>'

    # Specification chips
    spec_chips_html = ""
    for k, v in prod.specs.items():
        spec_chips_html += f'<span class="spec-chip"><strong>{k}:</strong> {v}</span>'

    # Deal Score Display
    if eval_item.deal_score is not None:
        deal_score_html = f"""
            <div style="text-align: center; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 12px;">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Real Deal Score</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #0f172a;">{eval_item.deal_score}<span style="font-size: 0.75rem; color: #94a3b8;">/100</span></div>
                <div style="font-size: 0.7rem; font-weight: 700; color: {deal_class_bg};">{eval_item.deal_classification}</div>
            </div>
        """
    else:
        deal_score_html = f"""
            <div style="text-align: center; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 12px;">
                <div style="font-size: 0.68rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Real Deal Score</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #94a3b8;">N/A</div>
                <div style="font-size: 0.7rem; font-weight: 600; color: #94a3b8;">INSUFFICIENT DATA</div>
            </div>
        """

    # Recommendation Suitability Score Display
    rec_score_html = f"""
        <div style="text-align: center; background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 8px; padding: 6px 12px;">
            <div style="font-size: 0.68rem; color: #4338ca; font-weight: 700; text-transform: uppercase;">Suitability Score</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #3730a3;">{eval_item.recommendation_score}<span style="font-size: 0.75rem; color: #6366f1;">/100</span></div>
            <div style="font-size: 0.7rem; font-weight: 600; color: #4f46e5;">User Match</div>
        </div>
    """

    # Reasons list
    reasons_html = ""
    for r in eval_item.reasons[:4]:
        reasons_html += f'<li style="margin-bottom: 4px; font-size: 0.88rem; color: #334155;">{r}</li>'

    # Cautions / limitations list
    cautions_html = ""
    if eval_item.cautions_or_missing_specs:
        for c in eval_item.cautions_or_missing_specs[:3]:
            cautions_html += f'<div style="font-size: 0.8rem; color: #9a3412; margin-top: 4px;">⚠️ {c}</div>'

    # Failure explanation if alternative
    failures_html = ""
    if eval_item.failed_hard_requirements:
        for f in eval_item.failed_hard_requirements:
            failures_html += f'<div style="font-size: 0.8rem; color: #b91c1c; font-weight: 600; margin-top: 3px;">✕ {f}</div>'

    shipping_label = "FREE" if eval_item.shipping_cost == 0 else f"${eval_item.shipping_cost:,.2f}"

    st.markdown(
        f"""
        <div class="advisor-rec-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;">
                <div>
                    <span class="{badge_class}">{badge_label}</span>
                    <span style="font-size: 0.8rem; color: #64748b; margin-left: 8px;">{badge_sub}</span>
                    <h3 style="margin: 8px 0 4px 0; font-size: 1.3rem; font-weight: 800; color: #0f172a;">
                        {prod.title}
                    </h3>
                    <div style="font-size: 0.82rem; color: #64748b;">
                        Brand: <strong>{prod.brand}</strong> &nbsp;|&nbsp; Category: <strong>{prod.category}</strong>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; align-items: center;">
                    {rec_score_html}
                    {deal_score_html}
                </div>
            </div>

            <div style="margin: 10px 0;">
                {spec_chips_html}
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin: 14px 0;">
                <div>
                    <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;">Best Store Offer</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #0f172a;">{eval_item.store_name}</div>
                    <div style="font-size: 0.72rem; color: #10b981;">● In Stock</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;">Product Price</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #0f172a; font-family: monospace;">${eval_item.base_price:,.2f}</div>
                    <div style="font-size: 0.72rem; color: #64748b;">Shipping: {shipping_label}</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;">Total Checkout Cost</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #4338ca; font-family: monospace;">${eval_item.total_cost:,.2f}</div>
                    <div style="font-size: 0.72rem; color: #64748b;">Includes shipping</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;">Budget Fit</div>
                    <div style="margin-top: 4px;">{headroom_html}</div>
                </div>
            </div>

            <div style="margin-top: 10px;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                    💡 Why We Recommend This:
                </div>
                <ul style="margin: 0; padding-left: 20px;">
                    {reasons_html}
                </ul>
                {cautions_html}
                {failures_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Detailed Score Breakdown Expander & Navigation Button
    col_breakdown, col_nav = st.columns([3, 1])
    with col_breakdown:
        with st.expander(f"🔍 Score Breakdown & Spec Details for {prod.title[:35]}..."):
            st.markdown("#### Suitability Scoring Breakdown (Independent from Real Deal Score)")
            b = eval_item.score_breakdown
            col_b1, col_b2, col_b3, col_b4 = st.columns(4)
            col_b1.metric("Use-Case Fit (40%)", f"{b.get('Suitability (40%)', 0):.1f} / 40")
            col_b2.metric("Hardware Specs (30%)", f"{b.get('Specifications (30%)', 0):.1f} / 30")
            col_b3.metric("Budget Room (20%)", f"{b.get('Budget Efficiency (20%)', 0):.1f} / 20")
            col_b4.metric("Brand Match (10%)", f"{b.get('Brand Match (10%)', 0):.1f} / 10")

            st.markdown(
                f"""
                - **Suitability Composite Score**: `{eval_item.recommendation_score} / 100`
                - **Real Deal Score**: `{eval_item.deal_score if eval_item.deal_score is not None else 'N/A'} / 100` ({eval_item.deal_classification})
                - **Full Technical Description**: {prod.description}
                """
            )
    with col_nav:
        if st.button("📊 View Price History", key=f"rec_btn_{prod.id}_{category_type}", use_container_width=True):
            st.session_state["selected_product_id"] = prod.id
            st.session_state["current_view"] = "comparison"
            st.rerun()


def render_advisor_view():
    """Renders the interactive Smart Purchase Advisor workspace."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #6366f1; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                🧭 AI-Free Shopping Intelligence
            </div>
            <h1 style="font-size: 2.2rem; font-weight: 800; color: #0f172a; margin: 0 0 8px 0;">
                Smart Purchase Advisor
            </h1>
            <p style="font-size: 1rem; color: #475569; margin: 0; line-height: 1.5; max-width: 850px;">
                Specify your spending limit, primary use case, and hardware requirements. 
                Our deterministic recommendation engine evaluates candidate products against recorded technical specifications, 
                checkout totals, and historical deal ratings.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    authenticated_user = st.session_state.get("authenticated_user")
    user_prefs = get_user_preferences(authenticated_user.id) if authenticated_user else None

    if authenticated_user and user_prefs:
        pref_highlights = []
        if user_prefs.preferred_brands:
            pref_highlights.append(f"Brands: {', '.join(user_prefs.preferred_brands)}")
        if user_prefs.priority and user_prefs.priority != "balanced":
            pref_highlights.append(f"Priority: {user_prefs.priority.replace('_', ' ').title()}")
        if user_prefs.max_budget:
            pref_highlights.append(f"Budget: ${user_prefs.max_budget:,.2f}")

        highlight_str = f" ({' • '.join(pref_highlights)})" if pref_highlights else ""
        st.markdown(
            f"""
            <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 14px; margin-bottom: 18px; font-size: 0.85rem; color: #1e40af; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span>✨</span> <strong>Personalized Scoring Active:</strong> Tailored for {authenticated_user.full_name or authenticated_user.email}{highlight_str}
                </div>
                <div style="font-size: 0.78rem; color: #2563eb; font-weight: 600;">
                    Preferences synced from Profile
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =================================================================
    # Interactive Preference Controls
    # =================================================================
    with st.container():
        st.markdown(
            """
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 20px 8px 20px; margin-bottom: 24px;">
                <div style="font-size: 0.92rem; font-weight: 700; color: #0f172a; margin-bottom: 12px;">
                    🎯 Configure Purchase Criteria & Preferences
                </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1.2, 1.2, 1.2])

        default_budget = float(user_prefs.max_budget) if (user_prefs and user_prefs.max_budget and user_prefs.max_budget >= 100.0) else 1500.0

        with col1:
            budget_val = st.number_input(
                "💰 Spending Budget ($ USD)",
                min_value=100.0,
                max_value=5000.0,
                value=default_budget,
                step=50.0,
                help="Maximum total cost including estimated shipping fees.",
            )

        categories = ["All"] + get_all_categories()
        with col2:
            selected_category = st.selectbox(
                "📦 Product Category",
                options=categories,
                index=0,
                help="Filter by specific hardware category or explore all.",
            )

        use_cases = [
            "Everyday Use",
            "Studying",
            "Programming",
            "Gaming",
            "Photography",
            "Office Work",
        ]
        with col3:
            selected_use_case = st.selectbox(
                "💼 Primary Use Case",
                options=use_cases,
                index=1,
                help="Weights hardware suitability criteria according to workflow requirements.",
            )

        # Dynamic Spec Row depending on Category
        min_ram_val = None
        min_storage_val = None
        min_battery_val = None
        require_anc_val = False
        require_4k_val = False
        require_gpu_val = False

        col_spec1, col_spec2, col_spec3, col_spec4 = st.columns(4)

        if selected_category == "Laptops":
            with col_spec1:
                ram_choice = st.selectbox("Minimum RAM", ["Any", "16GB", "32GB"])
                if ram_choice != "Any":
                    min_ram_val = int(ram_choice.replace("GB", ""))
            with col_spec2:
                storage_choice = st.selectbox("Minimum Storage", ["Any", "512GB", "1TB"])
                if storage_choice != "Any":
                    min_storage_val = 1000 if "1TB" in storage_choice else int(storage_choice.replace("GB", ""))
            with col_spec3:
                require_gpu_val = st.checkbox("Require Discrete GPU", value=False)
            with col_spec4:
                require_in_stock_val = st.checkbox("In-Stock Only", value=True)

        elif selected_category == "Smartphones":
            with col_spec1:
                storage_choice = st.selectbox("Minimum Storage", ["Any", "128GB", "256GB"])
                if storage_choice != "Any":
                    min_storage_val = int(storage_choice.replace("GB", ""))
            with col_spec2:
                require_in_stock_val = st.checkbox("In-Stock Only", value=True)
            with col_spec3:
                free_ship_val = st.checkbox("Free Shipping Only", value=False)
            with col_spec4:
                st.write("")

        elif selected_category == "Audio":
            with col_spec1:
                require_anc_val = st.checkbox("Require ANC (Noise Canceling)", value=True)
            with col_spec2:
                battery_choice = st.selectbox("Minimum Battery Life", ["Any", "20 Hours", "24 Hours", "30 Hours"])
                if battery_choice != "Any":
                    min_battery_val = int(battery_choice.split()[0])
            with col_spec3:
                require_in_stock_val = st.checkbox("In-Stock Only", value=True)
            with col_spec4:
                free_ship_val = st.checkbox("Free Shipping Only", value=False)

        elif selected_category in ["Monitors", "TVs"]:
            with col_spec1:
                require_4k_val = st.checkbox("Require 4K Resolution", value=True)
            with col_spec2:
                require_in_stock_val = st.checkbox("In-Stock Only", value=True)
            with col_spec3:
                free_ship_val = st.checkbox("Free Shipping Only", value=False)
            with col_spec4:
                st.write("")

        else:
            # All Categories / Wearables / Gaming / Cameras
            with col_spec1:
                require_in_stock_val = st.checkbox("In-Stock Only", value=True)
            with col_spec2:
                require_4k_val = st.checkbox("Require 4K / UHD", value=False)
            with col_spec3:
                free_ship_val = st.checkbox("Free Shipping Only", value=False)
            with col_spec4:
                st.write("")

        # Brand Preference
        available_brands = ["All"] + get_all_brands(selected_category if selected_category != "All" else None)
        selected_brand = st.selectbox(
            "🏷️ Preferred Brand (Optional)",
            options=available_brands,
            index=0,
            help="Prioritizes candidate products from your preferred manufacturer.",
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # Build Preferences Dataclass
    prefs = AdvisorPreferences(
        budget=float(budget_val),
        category=selected_category,
        use_case=selected_use_case,
        brand_preference=selected_brand if selected_brand != "All" else None,
        min_ram_gb=min_ram_val,
        min_storage_gb=min_storage_val,
        min_battery_hours=min_battery_val,
        require_in_stock=require_in_stock_val,
        require_anc=require_anc_val,
        require_4k=require_4k_val,
        require_discrete_gpu=require_gpu_val,
        max_shipping_cost=0.0 if locals().get("free_ship_val", False) else None,
        preferred_categories=user_prefs.preferred_categories if user_prefs else [],
        preferred_brands=user_prefs.preferred_brands if user_prefs else [],
        preferred_store_id=user_prefs.preferred_store_id if user_prefs else None,
        priority=user_prefs.priority if user_prefs else "balanced",
        user_saved_min_budget=user_prefs.min_budget if user_prefs else None,
        user_saved_max_budget=user_prefs.max_budget if user_prefs else None,
    )

    # =================================================================
    # Execute Recommendation Analysis
    # =================================================================
    results: RecommendationResult = get_purchase_recommendations(preferences=prefs)

    # Intelligence Summary Banner
    st.markdown(
        f"""
        <div style="background: #eef2ff; border-left: 4px solid #6366f1; border-radius: 8px; padding: 12px 16px; margin-bottom: 24px; color: #1e1b4b; font-size: 0.92rem;">
            <strong>Advisor Intelligence Summary:</strong> {results.summary_explanation}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =================================================================
    # Primary Recommendations: Best Overall, Best Budget, Best Deal
    # =================================================================
    if results.ranked_candidates:
        st.markdown(
            """
            <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin: 0 0 16px 0;">
                Curated Recommendations
            </h2>
            """,
            unsafe_allow_html=True,
        )

        # 1. BEST OVERALL
        if results.best_overall:
            render_recommendation_card(results.best_overall, category_type="overall")

        # 2. BEST BUDGET (if distinct from Best Overall)
        if results.best_budget and results.best_budget.product.id != (results.best_overall.product.id if results.best_overall else -1):
            render_recommendation_card(results.best_budget, category_type="budget")

        # 3. BEST CURRENT DEAL (if distinct and verified)
        if results.best_deal:
            is_dup = (
                results.best_overall and results.best_deal.product.id == results.best_overall.product.id
            ) or (
                results.best_budget and results.best_deal.product.id == results.best_budget.product.id
            )
            if not is_dup:
                render_recommendation_card(results.best_deal, category_type="deal")
            else:
                st.info(
                    f"★ **Best Current Deal Note:** The {results.best_deal.product.title} already holds the top verified "
                    f"Deal Score ({results.best_deal.deal_score}/100) and was featured above."
                )

        # Other qualifying candidates
        other_matches = [
            c for c in results.ranked_candidates 
            if (not results.best_overall or c.product.id != results.best_overall.product.id)
            and (not results.best_budget or c.product.id != results.best_budget.product.id)
            and (not results.best_deal or c.product.id != results.best_deal.product.id)
        ]

        if other_matches:
            with st.expander(f"📦 Additional Matching Options ({len(other_matches)} More In-Budget Products)"):
                for m in other_matches:
                    render_recommendation_card(m, category_type="alternative")

    else:
        # Empty State: No product met all hard constraints
        st.warning(
            "⚠️ **No products in the catalog satisfied all your criteria.** "
            f"No products in category '{selected_category}' met the budget limit of ${budget_val:,.2f} "
            "and all specified hardware requirements."
        )

        if results.closest_alternatives:
            st.markdown(
                """
                <h3 style="font-size: 1.35rem; font-weight: 800; color: #0f172a; margin: 24px 0 12px 0;">
                    🔍 Closest Available Alternatives
                </h3>
                <p style="font-size: 0.9rem; color: #64748b; margin-bottom: 16px;">
                    These candidate products closely align with your workflow but require minor budget flexibility or specification tradeoffs:
                </p>
                """,
                unsafe_allow_html=True,
            )
            for alt in results.closest_alternatives:
                render_recommendation_card(alt, category_type="alternative")

    # Limitations & Academic Notes Footer
    if results.limitations:
        with st.expander("ℹ️ Advisor Scope & Academic Transparency Limitations"):
            for lim in results.limitations:
                st.markdown(f"- {lim}")
            st.markdown(
                """
                - **Deterministic Modeling**: All evaluations are computed via transparent mathematical weighting and parameterized rules without opaque external AI inference.
                - **Dataset Labeling**: All products, stores, and price points are synthetic or curated sample records labeled **DEMO DATA**.
                """
            )

