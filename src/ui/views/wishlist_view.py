"""Personal Wishlist & Dashboard View for PriceWise AI (Phase 7).
Enables authenticated users to:
- View saved products with live lowest offer prices and stock status
- Monitor active price tracking status directly from the wishlist
- Add personal notes to wishlist items (e.g. 'Wait for Black Friday', 'Birthday gift')
- Quickly jump to store comparison or setup price tracking
- Remove items from their personal wishlist
- Quickly add catalog items to their wishlist
"""

from typing import Optional
import streamlit as st

from src.config import PRODUCT_IMAGE_FALLBACK
from src.services.wishlist_service import (
    get_user_wishlist,
    get_wishlist_count,
    add_to_wishlist,
    remove_from_wishlist,
    update_wishlist_note,
    is_in_wishlist,
)
from src.services.price_tracking_service import (
    get_tracked_products,
    get_alert_history,
    add_tracked_product,
)
from src.services.product_service import get_products, get_product_by_id


def render_wishlist_view():
    """Renders the user's personal wishlist and shopping dashboard."""
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #ec4899; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                💖 Personal Shopping Space
            </div>
            <h1 style="font-size: 2.2rem; font-weight: 800; color: #0f172a; margin: 0 0 8px 0;">
                My Wishlist & Personal Dashboard
            </h1>
            <p style="font-size: 1rem; color: #475569; margin: 0; line-height: 1.5; max-width: 850px;">
                Keep track of items you plan to buy, monitor current lowest retailer prices,
                and manage target price alerts for all your saved items in one central place.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    authenticated_user = st.session_state.get("authenticated_user")

    if not authenticated_user:
        st.markdown(
            """
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 32px; text-align: center; max-width: 650px; margin: 20px auto;">
                <div style="font-size: 2.8rem; margin-bottom: 12px;">💖</div>
                <h3 style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 0 0 8px 0;">
                    Your Personal Wishlist Awaits
                </h3>
                <p style="font-size: 0.95rem; color: #475569; line-height: 1.6; margin-bottom: 20px;">
                    Create a free account or sign in to save products to your personal wishlist, 
                    record shopping notes, and track price changes across all 5 demo retailers.
                </p>
                <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                    <span style="background: #fdf2f8; color: #db2777; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">📌 Save Favorite Products</span>
                    <span style="background: #eff6ff; color: #2563eb; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">🔔 Real-Time Price Tracking</span>
                    <span style="background: #f0fdf4; color: #16a34a; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">📝 Custom Shopping Notes</span>
                    <span style="background: #faf5ff; color: #9333ea; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">⚡ Instant Store Comparison</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("💡 Use the account sign-in controls in the left sidebar to log in or register.")
        return

    # Authenticated User Dashboard
    user_id = authenticated_user.id
    wishlist_items = get_user_wishlist(user_id)
    tracked_items = get_tracked_products(user_id=user_id)
    active_tracked = [t for t in tracked_items if t.is_active]
    target_met_count = len([t for t in tracked_items if t.is_target_reached])
    unread_alerts = get_alert_history(user_id=user_id, unread_only=True)

    # Personal KPI Tiles
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)

    with col_k1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Saved in Wishlist</div>
                <div class="stat-value" style="color: #ec4899;">{len(wishlist_items)}</div>
                <div class="stat-sub">Personal Saved Items</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_k2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Actively Tracked</div>
                <div class="stat-value" style="color: #059669;">{len(active_tracked)}</div>
                <div class="stat-sub">Evaluating Price Drops</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_k3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Targets Reached</div>
                <div class="stat-value" style="color: #10b981;">{target_met_count}</div>
                <div class="stat-sub">At or Below Target</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_k4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Unread Alerts</div>
                <div class="stat-value" style="color: #6366f1;">{len(unread_alerts)}</div>
                <div class="stat-sub">Personal Notifications</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Quick Add Section
    all_products = get_products()
    wishlist_prod_ids = {item.product_id for item in wishlist_items}
    available_to_add = [p for p in all_products if p.id not in wishlist_prod_ids]

    if available_to_add:
        with st.expander("➕ Quickly Add Product to Wishlist", expanded=False):
            col_sel, col_note, col_btn = st.columns([2.5, 2.5, 1])
            with col_sel:
                prod_choices = {p.id: f"{p.brand} - {p.title} (${p.lowest_price:,.2f})" if p.lowest_price else f"{p.brand} - {p.title}" for p in available_to_add}
                chosen_pid = st.selectbox(
                    "Select Product",
                    options=list(prod_choices.keys()),
                    format_func=lambda pid: prod_choices[pid],
                    label_visibility="collapsed",
                    key="quick_add_product_select",
                )
            with col_note:
                quick_note = st.text_input(
                    "Optional Note",
                    placeholder="e.g., Target price $250, wait for holiday sale...",
                    label_visibility="collapsed",
                    key="quick_add_note_input",
                )
            with col_btn:
                if st.button("Add to Wishlist", use_container_width=True, key="btn_quick_add_wishlist"):
                    ok, msg, _ = add_to_wishlist(user_id=user_id, product_id=chosen_pid, note=quick_note)
                    if ok:
                        st.success("✓ Added to wishlist!")
                        st.rerun()
                    else:
                        st.error(msg)

    # Empty State Handling
    if not wishlist_items:
        st.markdown(
            """
            <div class="empty-state-box" style="margin-top: 20px;">
                <div style="font-size: 2.4rem; margin-bottom: 8px;">🤍</div>
                <div class="empty-state-title">Your wishlist is empty</div>
                <div class="empty-state-desc">
                    You haven't saved any items to your wishlist yet.
                    Browse our catalog or explore the Smart Purchase Advisor to discover and save products.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
        with col_c2:
            if st.button("🛍️ Browse Product Catalog", use_container_width=True, key="btn_empty_to_catalog"):
                st.session_state["current_view"] = "home"
                st.rerun()
        return

    # Render Wishlist Items
    st.markdown(f"### 📋 Saved Items ({len(wishlist_items)})")

    for item in wishlist_items:
        with st.container():
            st.markdown(
                f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display: flex; gap: 16px; align-items: center; flex-wrap: wrap;">
                        <div style="width: 80px; height: 80px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: center; padding: 6px; flex-shrink: 0;">
                            <img src="{item.image_url or PRODUCT_IMAGE_FALLBACK}" alt="{item.title}" style="max-height: 100%; max-width: 100%; object-fit: contain;" onerror="this.onerror=null;this.src='{PRODUCT_IMAGE_FALLBACK}';" />
                        </div>
                        <div style="flex-grow: 1; min-width: 200px;">
                            <div style="font-size: 0.75rem; font-weight: 700; color: #6366f1; text-transform: uppercase;">
                                {item.brand} • {item.category} • SKU: {item.sku}
                            </div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #0f172a; margin: 2px 0 4px 0;">
                                {item.title}
                            </div>
                            <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap; font-size: 0.85rem;">
                                <span>Lowest Price: <strong style="font-size: 1.05rem; color: #0f172a; font-family: monospace;">${item.lowest_price:,.2f}</strong></span>
                                <span style="color: #64748b;">({item.lowest_store_name or 'N/A'})</span>
                                {f'<span style="background: #ecfdf5; color: #059669; font-weight: 600; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">🔔 Tracking: ${item.tracking_target_price:,.2f}</span>' if item.is_tracked else '<span style="background: #f1f5f9; color: #64748b; font-weight: 500; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">🔕 Not Tracked</span>'}
                                <span style="color: #94a3b8; font-size: 0.75rem;">Added {item.created_at[:10]}</span>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Actions & Note Row
            col_actions, col_note_disp = st.columns([1.5, 2.5])

            with col_actions:
                col_btn_comp, col_btn_track, col_btn_del = st.columns(3)
                with col_btn_comp:
                    if st.button("📊 Compare", key=f"btn_wish_comp_{item.id}", use_container_width=True, help="Compare store prices for this product"):
                        st.session_state["selected_product_id"] = item.product_id
                        st.session_state["current_view"] = "comparison"
                        st.rerun()

                with col_btn_track:
                    track_label = "🔔 Alert" if item.is_tracked else "➕ Track"
                    if st.button(track_label, key=f"btn_wish_track_{item.id}", use_container_width=True, help="Configure price alert for this item"):
                        st.session_state["current_view"] = "tracking"
                        st.rerun()

                with col_btn_del:
                    if st.button("🗑️ Remove", key=f"btn_wish_del_{item.id}", use_container_width=True, help="Remove from wishlist"):
                        ok, msg = remove_from_wishlist(item.id, user_id=user_id)
                        if ok:
                            st.success("Removed from wishlist.")
                            st.rerun()
                        else:
                            st.error(msg)

            with col_note_disp:
                # Personal note editing / display
                current_note = item.note or ""
                with st.expander(f"📝 Note: {current_note if current_note else '(No note added)'}", expanded=False):
                    new_note_val = st.text_input(
                        "Edit Shopping Note",
                        value=current_note,
                        key=f"note_input_{item.id}",
                        placeholder="Add a reminder or condition (e.g., buy if under $400)...",
                    )
                    if st.button("Save Note", key=f"btn_save_note_{item.id}"):
                        ok, msg = update_wishlist_note(item.id, user_id=user_id, note=new_note_val)
                        if ok:
                            st.success("Note saved.")
                            st.rerun()
                        else:
                            st.error(msg)

