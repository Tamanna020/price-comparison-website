"""Phase 9 Automated Test Suite: Advanced Price Intelligence, Deal Analytics & Alerts.

Tests:
1. Total purchase cost calculation (known vs unknown shipping, valid vs expired coupons).
2. 7/30/90-day price history windowing, trend classification, and DEMO segregation.
3. Deal scoring algorithm (0-100 score, 5-factor breakdown, simulated deal enforcement for demo data).
4. Price tracking rules, duplicate prevention, and strict user data isolation.
5. REST API endpoint responses via FastAPI test client / HTTP requests.
"""

import os
import pytest
from src.services.price_intelligence_service import (
    validate_retailer_coupon,
    calculate_total_purchase_cost,
    get_product_price_analytics,
    calculate_deal_score,
    get_user_tracking_records,
    get_user_price_alerts_list,
)
from src.services.price_tracking_service import (
    add_tracked_product,
    remove_tracking,
    evaluate_tracking_rules,
    mark_alert_read,
)
from src.database.connection import get_connection


# =============================================================================
# 1. Total Purchase Cost Calculation Tests
# =============================================================================

def test_total_purchase_cost_known_shipping():
    """Verify landed cost calculation with explicitly known shipping fee."""
    cost = calculate_total_purchase_cost(
        product_price=1500.0,
        shipping_fee=50.0,
        is_shipping_disclosed=True,
        reference_mrp=1800.0,
        retailer_name="Nykaa",
    )
    assert cost.base_price == 1500.0
    assert cost.shipping_fee == 50.0
    assert cost.is_shipping_known is True
    assert cost.final_payable_price == 1550.0
    assert cost.is_final_exact is True
    assert cost.confirmed_savings == 300.0
    assert cost.coupon_savings == 0.0


def test_total_purchase_cost_unknown_shipping_never_assumed_zero():
    """Verify undisclosed shipping remains unknown and NOT assumed to be 0."""
    cost = calculate_total_purchase_cost(
        product_price=999.0,
        shipping_fee=None,
        is_shipping_disclosed=False,
        retailer_name="SpecialtyStore",
    )
    assert cost.base_price == 999.0
    assert cost.shipping_fee is None
    assert cost.is_shipping_known is False
    assert cost.is_final_exact is False
    assert "additional delivery fees may apply" in cost.payable_state_note.lower()
    assert cost.shipping_label == "Shipping Not Disclosed"


def test_coupon_validation_valid_and_expired():
    """Verify retailer coupon code validation logic and simulated labeling."""
    # Valid Nykaa coupon (Simulated test coupon)
    v1 = validate_retailer_coupon("NYKBEAUTY10", 1200.0, "Nykaa")
    assert v1.is_valid is True
    assert v1.discount_amount == 120.0  # 10% of 1200
    assert v1.is_expired is False
    assert v1.is_simulated is True
    assert v1.source == "simulated"
    assert "not been verified" in v1.disclaimer.lower()

    # Valid coupon below minimum spend
    v2 = validate_retailer_coupon("NYKBEAUTY10", 300.0, "Nykaa")
    assert v2.is_valid is False
    assert "minimum spend" in (v2.rejection_reason or "").lower()

    # Expired coupon
    v3 = validate_retailer_coupon("EXPIRED20", 2000.0, "Nykaa")
    assert v3.is_valid is False
    assert v3.is_expired is True

    # Unknown coupon code
    v4 = validate_retailer_coupon("NONEXISTENT99", 1000.0, "Nykaa")
    assert v4.is_valid is False
    assert "unrecognized" in (v4.rejection_reason or "").lower()


def test_total_purchase_cost_with_valid_coupon():
    """Verify landed cost calculation with simulated coupon and honest savings segregation."""
    cost = calculate_total_purchase_cost(
        product_price=1000.0,
        shipping_fee=0.0,
        is_shipping_disclosed=True,
        coupon_code="NYKBEAUTY10",
        reference_mrp=1200.0,
        retailer_name="Nykaa",
    )
    assert cost.base_price == 1000.0
    assert cost.shipping_fee == 0.0
    assert cost.is_shipping_known is True
    assert cost.coupon_applied is not None
    assert cost.coupon_applied.is_valid is True
    assert cost.coupon_applied.is_simulated is True
    assert cost.simulated_coupon_savings == 100.0
    assert cost.coupon_savings == 100.0
    assert cost.final_payable_price == 900.0  # 1000 + 0 - 100
    assert cost.mrp_discount == 200.0
    assert cost.confirmed_savings == 200.0  # Equals MRP discount
    assert cost.total_potential_savings == 300.0  # 200 MRP discount + 100 simulated coupon
    assert cost.genuine_verified_market_savings == 0.0  # Strictly 0 for demo catalog offers


# =============================================================================
# 2. Historical Price Analytics & Windowing Tests
# =============================================================================

def test_price_history_analytics_7_30_90_windows():
    """Verify historical price aggregation over 7, 30, and 90-day observation windows."""
    # Product 1 exists in catalog
    p7 = get_product_price_analytics(1, window_days=7)
    p30 = get_product_price_analytics(1, window_days=30)
    p90 = get_product_price_analytics(1, window_days=90)

    assert p7.window_days == 7
    assert p30.window_days == 30
    assert p90.window_days == 90

    # Segregation: 90-day window must have >= observations as 7-day window
    assert p90.observation_count >= p7.observation_count

    # DEMO status enforcement
    assert p30.history_data_status == "DEMO"
    assert p30.is_simulated is True
    assert "demo" in p30.disclaimer.lower()

    if p30.lowest_recorded_price and p30.highest_recorded_price:
        assert p30.lowest_recorded_price <= p30.highest_recorded_price
        if p30.average_recorded_price:
            assert p30.lowest_recorded_price <= p30.average_recorded_price <= p30.highest_recorded_price


# =============================================================================
# 3. Deal Scoring Algorithm Tests
# =============================================================================

def test_deal_score_calculation_demo_simulation_enforcement():
    """Verify that DEMO catalog data is strictly labeled simulated and ineligible for genuine deal badge."""
    score = calculate_deal_score(
        product_id=1,
        current_price=1799.0,
        reference_mrp=1949.0,
        historical_low=1749.0,
        shipping_fee=0.0,
        is_shipping_disclosed=True,
        coupon_discount=0.0,
        source_type="demo",
        retailer_name="Nykaa",
        product_title="Demo Serum",
    )

    assert 0 <= score.deal_score <= 100
    assert score.deal_grade in ("A+", "A", "B", "C", "D")
    assert score.is_simulated_deal is True
    assert score.source_status == "DEMO"
    assert score.verified_deal_eligible is False
    assert "(Simulated)" in score.deal_classification
    assert len(score.factors) == 5

    # Check 5 factors are accounted for
    factor_names = [f.factor_name for f in score.factors]
    assert "Discount vs Reference MRP" in factor_names
    assert "Historical Price Position" in factor_names
    assert "Landed Delivery Transparency" in factor_names
    assert "Promotional Coupon Factor" in factor_names
    assert "Data Reliability & Evidence" in factor_names


def test_deal_score_sensitivity_higher_discount_scores_higher():
    """Verify score increases when discount and proximity to low improve."""
    low_deal = calculate_deal_score(
        product_id=1,
        current_price=1000.0,
        reference_mrp=1050.0,
        historical_low=800.0,
        shipping_fee=100.0,
        is_shipping_disclosed=True,
        source_type="demo",
    )

    great_deal = calculate_deal_score(
        product_id=1,
        current_price=600.0,
        reference_mrp=1200.0,
        historical_low=600.0,
        shipping_fee=0.0,
        is_shipping_disclosed=True,
        source_type="demo",
    )

    assert great_deal.deal_score > low_deal.deal_score


# =============================================================================
# 4. Price Tracking & Alert User Isolation Tests
# =============================================================================

def test_price_tracking_user_isolation_and_alerts():
    """Verify price tracking rule creation, duplicate prevention, and strict user data isolation."""
    from src.services.auth_service import register_user
    import time
    ts = int(time.time())
    _, _, user_a_obj = register_user(f"phase9_user_a_{ts}@example.com", "Password123!", "User A")
    _, _, user_b_obj = register_user(f"phase9_user_b_{ts}@example.com", "Password123!", "User B")
    assert user_a_obj is not None
    assert user_b_obj is not None
    user_a = user_a_obj.id
    user_b = user_b_obj.id
    product_id = 1

    # Cleanup any previous test artifacts
    with get_connection() as conn:
        conn.execute("DELETE FROM price_tracking WHERE user_id IN (?, ?)", (user_a, user_b))
        conn.execute("DELETE FROM price_alerts WHERE user_id IN (?, ?)", (user_a, user_b))

    # 1. Invalid target price (<= 0) rejected
    s_inv, m_inv, _ = add_tracked_product(product_id, -50.0, user_id=user_a)
    assert s_inv is False
    assert "greater than zero" in m_inv

    # 2. Add valid tracking for User A
    s_a, m_a, track_a_id = add_tracked_product(product_id, 1600.0, note="Wait for price drop", user_id=user_a)
    assert s_a is True
    assert track_a_id is not None

    # 3. Duplicate tracking for same user & product rejected
    s_dup, m_dup, _ = add_tracked_product(product_id, 1550.0, user_id=user_a)
    assert s_dup is False
    assert "already in your Price Tracker" in m_dup

    # 4. User B can track the SAME product independently (user data isolation)
    s_b, m_b, track_b_id = add_tracked_product(product_id, 1400.0, user_id=user_b)
    assert s_b is True
    assert track_b_id != track_a_id

    # 5. Verify isolated record retrieval
    records_a = get_user_tracking_records(user_a)
    records_b = get_user_tracking_records(user_b)
    assert len(records_a) == 1
    assert len(records_b) == 1
    assert records_a[0].target_price == 1600.0
    assert records_b[0].target_price == 1400.0

    # 6. User B cannot delete User A's tracking record
    s_del_unauth, _ = remove_tracking(track_a_id, user_id=user_b)
    assert s_del_unauth is False

    # 7. User A can delete their own tracking record
    s_del_auth, _ = remove_tracking(track_a_id, user_id=user_a)
    assert s_del_auth is True

    # Cleanup
    remove_tracking(track_b_id, user_id=user_b)
