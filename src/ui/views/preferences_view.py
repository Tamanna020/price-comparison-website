"""Shopping Preferences & Personalization View for PriceWise AI (Phase 7).
Enables authenticated users to configure:
- Preferred hardware categories and manufacturer brands
- Minimum and maximum budget envelopes
- Preferred retailer for store affinity
- Recommendation priority weighting (Balanced, Lowest Price, Best Deal)
- Default catalog sort order
"""

from typing import Optional
import streamlit as st

from src.services.preference_service import (
    get_user_preferences,
    save_user_preferences,
    reset_user_preferences,
    get_available_stores,
    DEFAULT_SORT_PREFERENCE,
    DEFAULT_PRIORITY,
)
from src.services.product_service import get_all_categories, get_all_brands


def render_preferences_view():
    """Renders the shopping preferences and personalization settings page."""
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #6366f1; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                ⚙️ Shopping Intelligence Profile
            </div>
            <h1 style="font-size: 2.2rem; font-weight: 800; color: #0f172a; margin: 0 0 8px 0;">
                Shopping Preferences & Personalization
            </h1>
            <p style="font-size: 1rem; color: #475569; margin: 0; line-height: 1.5; max-width: 850px;">
                Customize your personal shopping profile. Your preferences tailor the Smart Purchase Advisor scoring,
                highlight your favorite brands and retailers, and prefill budget thresholds across PriceWise AI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    authenticated_user = st.session_state.get("authenticated_user")

    if not authenticated_user:
        # Guest call-to-action state
        st.markdown(
            """
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 28px; text-align: center; max-width: 650px; margin: 20px auto;">
                <div style="font-size: 2.5rem; margin-bottom: 12px;">🔒</div>
                <h3 style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 0 0 8px 0;">
                    Personalization Requires an Account
                </h3>
                <p style="font-size: 0.95rem; color: #475569; line-height: 1.6; margin-bottom: 20px;">
                    Sign in or create a free account to customize brand affinities, set budget guardrails,
                    and receive personalized Smart Purchase Advisor recommendations.
                </p>
                <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                    <span style="background: #eff6ff; color: #1d4ed8; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">🏷️ Brand Affinities</span>
                    <span style="background: #ecfdf5; color: #047857; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">💰 Budget Envelopes</span>
                    <span style="background: #f5f3ff; color: #6d28d9; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">🏪 Preferred Retailers</span>
                    <span style="background: #fffbeb; color: #b45309; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">🧭 Tailored Advice</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("💡 Please log in or create an account using the controls in the left sidebar to access your profile.")
        return

    # Authenticated user view
    st.markdown(
        f"""
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 14px 18px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="font-size: 0.85rem; color: #1e40af; font-weight: 700;">Signed in as:</span>
                <span style="font-size: 1rem; font-weight: 800; color: #1e3a8a; margin-left: 6px;">{authenticated_user.full_name or authenticated_user.email}</span>
                <span style="font-size: 0.8rem; color: #3b82f6; margin-left: 8px;">({authenticated_user.email})</span>
            </div>
            <div style="font-size: 0.8rem; font-weight: 600; color: #2563eb; background: #ffffff; padding: 4px 10px; border-radius: 16px; border: 1px solid #bfdbfe;">
                Member ID #{authenticated_user.id}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_prefs = get_user_preferences(authenticated_user.id)
    all_categories = get_all_categories()
    all_brands = get_all_brands()
    available_stores = get_available_stores()

    with st.form("preferences_form"):
        st.markdown("### 🏷️ Category & Brand Affinities")
        st.markdown(
            "<p style='font-size: 0.88rem; color: #64748b; margin-top: -8px; margin-bottom: 14px;'>Select categories and manufacturer brands you are most interested in. The Advisor prioritizes these when ranking candidates.</p>",
            unsafe_allow_html=True,
        )

        col_c, col_b = st.columns(2)

        with col_c:
            pre_selected_cats = [c for c in current_prefs.preferred_categories if c in all_categories]
            selected_categories = st.multiselect(
                "Preferred Product Categories",
                options=all_categories,
                default=pre_selected_cats,
                help="When specified, recommendations in these categories receive priority visibility.",
            )

        with col_b:
            pre_selected_brands = [b for b in current_prefs.preferred_brands if b in all_brands]
            selected_brands = st.multiselect(
                "Preferred Brands",
                options=all_brands,
                default=pre_selected_brands,
                help="Products from these manufacturers receive a 100% brand suitability score in the Smart Advisor.",
            )

        st.markdown("---")
        st.markdown("### 💰 Budget Envelope")
        st.markdown(
            "<p style='font-size: 0.88rem; color: #64748b; margin-top: -8px; margin-bottom: 14px;'>Default spending range used to prefill the Smart Purchase Advisor and filter recommendations.</p>",
            unsafe_allow_html=True,
        )

        col_bmin, col_bmax = st.columns(2)

        with col_bmin:
            min_val = float(current_prefs.min_budget) if current_prefs.min_budget is not None else 0.0
            min_budget_input = st.number_input(
                "Minimum Target Budget ($ USD)",
                min_value=0.0,
                max_value=10000.0,
                value=min_val,
                step=50.0,
                help="Lower bound for product searches and advisor recommendations (optional). Set 0 for no minimum.",
            )

        with col_bmax:
            max_val = float(current_prefs.max_budget) if current_prefs.max_budget is not None else 0.0
            max_budget_input = st.number_input(
                "Maximum Spending Budget ($ USD)",
                min_value=0.0,
                max_value=10000.0,
                value=max_val,
                step=50.0,
                help="Hard spending ceiling including shipping costs. Set 0 for no maximum ceiling.",
            )

        st.markdown("---")
        st.markdown("### 🧭 Optimization Priority & Store Preference")

        col_pri, col_st, col_sort = st.columns(3)

        priority_options = {
            "balanced": "⚖️ Balanced (Specs, Value & Price)",
            "lowest_price": "💵 Lowest Price First",
            "best_deal": "🏷️ Best Deal First (Real Deal Score)",
        }
        with col_pri:
            cur_pri = current_prefs.priority if current_prefs.priority in priority_options else DEFAULT_PRIORITY
            selected_priority = st.selectbox(
                "Recommendation Priority",
                options=list(priority_options.keys()),
                format_func=lambda k: priority_options[k],
                index=list(priority_options.keys()).index(cur_pri),
                help="Determines ranking tie-breakers in the Smart Purchase Advisor.",
            )

        with col_st:
            store_options = {0: "No Specific Store Preference"}
            for s in available_stores:
                domain_str = f" ({s['domain']})" if s.get("domain") else ""
                store_options[s["id"]] = f"🏬 {s['name']}{domain_str}"

            current_store_choice = current_prefs.preferred_store_id if current_prefs.preferred_store_id in store_options else 0
            selected_store_id = st.selectbox(
                "Preferred Retailer",
                options=list(store_options.keys()),
                format_func=lambda sid: store_options[sid],
                index=list(store_options.keys()).index(current_store_choice),
                help="Offers from your favorite retailer are highlighted when prices are competitive.",
            )

        sort_options = {
            "featured": "⭐ Featured / Best Value",
            "price_asc": "💲 Price: Low to High",
            "price_desc": "💲 Price: High to Low",
            "name_asc": "🔤 Product Name: A to Z",
        }
        sort_alias_map = {
            "best_deal": "featured",
            "lowest_price": "price_asc",
            "highest_price": "price_desc",
            "name": "name_asc",
            "title_asc": "name_asc",
        }
        raw_sort = current_prefs.sort_preference or DEFAULT_SORT_PREFERENCE
        cur_sort = sort_alias_map.get(raw_sort, raw_sort if raw_sort in sort_options else "featured")

        with col_sort:
            selected_sort = st.selectbox(
                "Default Catalog Sort",
                options=list(sort_options.keys()),
                format_func=lambda k: sort_options[k],
                index=list(sort_options.keys()).index(cur_sort),
                help="Default sorting criterion applied on the product catalog view.",
            )

        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
        col_submit, col_pad = st.columns([1, 3])

        with col_submit:
            submitted = st.form_submit_button("💾 Save Preferences", use_container_width=True)

        if submitted:
            # Parse budget inputs: 0 or None means unconstrained
            clean_min_b = float(min_budget_input) if min_budget_input > 0 else None
            clean_max_b = float(max_budget_input) if max_budget_input > 0 else None
            clean_store_id = int(selected_store_id) if selected_store_id != 0 else None

            # Validation: if max < min, warn user
            if clean_min_b is not None and clean_max_b is not None and clean_max_b < clean_min_b:
                st.error("Maximum budget cannot be less than minimum budget.")
            else:
                ok, msg = save_user_preferences(
                    user_id=authenticated_user.id,
                    preferred_categories=selected_categories,
                    preferred_brands=selected_brands,
                    min_budget=clean_min_b,
                    max_budget=clean_max_b,
                    preferred_store_id=clean_store_id,
                    sort_preference=selected_sort,
                    priority=selected_priority,
                )
                if ok:
                    st.success("✓ Preferences updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Error saving preferences: {msg}")

    # Reset button outside form
    col_r1, col_r2 = st.columns([1, 4])
    with col_r1:
        if st.button("🔄 Reset to Defaults", use_container_width=True, help="Clears personalized settings and restores system defaults."):
            ok, msg = reset_user_preferences(authenticated_user.id)
            if ok:
                st.info("Preferences have been reset to system defaults.")
                st.rerun()
            else:
                st.error(f"Error resetting preferences: {msg}")

