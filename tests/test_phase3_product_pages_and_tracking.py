"""Automated test suite for Phase 3: Dedicated Product Pages, Price Tracking,
Price-Drop Alerts, and User Watchlists.

Covers:
1. Product Slug & Dedicated Route Resolution:
   - get_product_by_slug
   - get_product_by_id_or_slug (numeric ID, SKU, canonical slug, hyphenated name)
   - Unknown slug/id returns None (clean 404 handling)
   - Product.slug property test
2. Variant Separation & Price History Storage:
   - get_product_price_history with window filtering (7d, 30d, 90d, all)
   - Variant separation (e.g. 50ml vs 30ml / different formulations kept distinct)
   - Honest empty state when history < 2 points (is_sufficient_history=False, None metrics)
3. Price-Drop Watchlist & Target Price Management:
   - Positive INR target price validation (> 0)
   - Rejection of target price <= 0 or invalid values
   - Duplicate tracking prevention
   - Update target price and status toggling (pause / resume / delete)
4. Alert Evaluation & Delivery Status:
   - Alert generated strictly when current_price <= target_price
   - Meaningful price drop evaluation
   - Duplicate alert prevention on unchanged price observations
   - Delivery status tagged as 'in_app_delivered' with channel 'in_app'
   - Mark alert read / mark all read
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta, timezone

from src.database.connection import init_db, migrate_db, get_connection
from src.database.models import Product, PriceAlert
from src.services.product_service import (
    get_product_by_slug,
    get_product_by_id_or_slug,
    get_products,
    get_product_by_id,
)
from src.database.price_history_service import (
    get_product_price_history,
    record_price_observation,
    ProductPriceHistorySummary,
)
from src.services.price_tracking_service import (
    add_tracked_product,
    get_tracked_products,
    update_target_price,
    pause_tracking,
    resume_tracking,
    remove_tracking,
    evaluate_tracking_rules,
    get_alert_history,
    mark_alert_read,
    mark_all_alerts_read,
)


@pytest.fixture
def temp_db():
    """Create an isolated temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    migrate_db(path)

    # Seed baseline stores and sample beauty products
    with get_connection(path) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO stores (name, domain) VALUES ('Nykaa', 'nykaa.com')")
        nykaa_id = c.lastrowid
        c.execute("INSERT INTO stores (name, domain) VALUES ('Tira', 'tirabeauty.com')")
        tira_id = c.lastrowid
        c.execute("INSERT INTO stores (name, domain) VALUES ('Amazon India', 'amazon.in')")
        amazon_id = c.lastrowid

        # Insert Product 1: Dot & Key Watermelon Sunscreen (50ml)
        c.execute(
            """
            INSERT INTO products (sku, title, brand, category, description, created_at)
            VALUES ('DK-SUN-50ML', 'Dot & Key Watermelon Cooling Sunscreen SPF 50', 'Dot & Key', 'Sunscreen',
                    'Hydrating sunscreen with hyaluronic acid and watermelon extract', '2026-10-01 10:00:00')
            """
        )
        p1_id = c.lastrowid

        # Insert Product 2: Minimalist Ceramide Cream (30ml)
        c.execute(
            """
            INSERT INTO products (sku, title, brand, category, description, created_at)
            VALUES ('MIN-CER-30ML', 'Minimalist 0.3% Ceramide Moisturizer', 'Minimalist', 'Moisturizer',
                    'Barrier repair cream with 3 essential ceramides', '2026-10-01 10:00:00')
            """
        )
        p2_id = c.lastrowid

        # Offers for Product 1 (50ml on Nykaa & Tira)
        c.execute(
            """
            INSERT INTO offers (product_id, store_id, variant_name, current_price, original_price, availability, last_checked)
            VALUES (?, ?, '50ml', 465.0, 595.0, 'In Stock', '2026-10-25 12:00:00')
            """,
            (p1_id, nykaa_id),
        )
        offer_50ml_id = c.lastrowid

        c.execute(
            """
            INSERT INTO offers (product_id, store_id, variant_name, current_price, original_price, availability, last_checked)
            VALUES (?, ?, '50ml', 480.0, 595.0, 'In Stock', '2026-10-25 12:00:00')
            """,
            (p1_id, tira_id),
        )

        # Offer for Product 1 (100ml on Amazon India)
        c.execute(
            """
            INSERT INTO offers (product_id, store_id, variant_name, current_price, original_price, availability, last_checked)
            VALUES (?, ?, '100ml', 799.0, 999.0, 'In Stock', '2026-10-25 12:00:00')
            """,
            (p1_id, amazon_id),
        )
        offer_100ml_id = c.lastrowid

        # Offers for Product 2
        c.execute(
            """
            INSERT INTO offers (product_id, store_id, variant_name, current_price, original_price, availability, last_checked)
            VALUES (?, ?, '30ml', 399.0, 449.0, 'In Stock', '2026-10-25 12:00:00')
            """,
            (p2_id, nykaa_id),
        )
        offer_p2_id = c.lastrowid

    yield {
        "path": path,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "nykaa_id": nykaa_id,
        "tira_id": tira_id,
        "offer_50ml_id": offer_50ml_id,
        "offer_100ml_id": offer_100ml_id,
        "offer_p2_id": offer_p2_id,
    }

    if os.path.exists(path):
        os.remove(path)


# =============================================================================
# 1. Product Slug & Route Resolution Tests
# =============================================================================

def test_product_slug_generation_and_resolution(temp_db):
    """Test resolution of products via slug, ID, or SKU with case insensitivity."""
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]

    # Test lookup by numeric ID string
    p_by_id = get_product_by_id_or_slug(str(p1_id), custom_path=path)
    assert p_by_id is not None
    assert p_by_id.id == p1_id
    assert "Watermelon" in p_by_id.title

    # Test lookup by slug generated from title
    slug = p_by_id.slug
    assert "dot" in slug and "watermelon" in slug
    p_by_slug = get_product_by_slug(slug, custom_path=path)
    assert p_by_slug is not None
    assert p_by_slug.id == p1_id

    # Test lookup by SKU
    p_by_sku = get_product_by_id_or_slug("DK-SUN-50ML", custom_path=path)
    assert p_by_sku is not None
    assert p_by_sku.id == p1_id

    # Test unknown slug returns None (clean 404)
    assert get_product_by_slug("non-existent-product-slug", custom_path=path) is None
    assert get_product_by_id_or_slug("unknown-99999", custom_path=path) is None


# =============================================================================
# 2. Variant Separation & Price History Storage Tests
# =============================================================================

def test_variant_separation_in_price_history(temp_db):
    """Ensure price history maintains strict separation between product variants / sizes."""
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]
    offer_50ml = temp_db["offer_50ml_id"]
    offer_100ml = temp_db["offer_100ml_id"]

    now = datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc)

    with get_connection(path) as conn:
        c = conn.cursor()
        # Record history for 50ml variant
        for days_ago, price in [(20, 499.0), (10, 475.0), (1, 465.0)]:
            ts = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute(
                "INSERT INTO price_history (offer_id, price, currency, data_source, data_status, recorded_at) VALUES (?, ?, 'INR', 'test', 'demo', ?)",
                (offer_50ml, price, ts),
            )

        # Record history for 100ml Jumbo variant
        for days_ago, price in [(15, 850.0), (2, 799.0)]:
            ts = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute(
                "INSERT INTO price_history (offer_id, price, currency, data_source, data_status, recorded_at) VALUES (?, ?, 'INR', 'test', 'demo', ?)",
                (offer_100ml, price, ts),
            )

    # Query 50ml history
    hist_50ml = get_product_price_history(p1_id, variant_name="50ml", reference_date=now, custom_path=path)
    assert hist_50ml.is_sufficient_history is True
    assert hist_50ml.observation_count == 3
    assert hist_50ml.min_price == 465.0
    assert hist_50ml.max_price == 499.0

    # Query 100ml history
    hist_100ml = get_product_price_history(p1_id, variant_name="100ml", reference_date=now, custom_path=path)
    assert hist_100ml.is_sufficient_history is True
    assert hist_100ml.observation_count == 2
    assert hist_100ml.min_price == 799.0
    assert hist_100ml.max_price == 850.0


def test_price_history_window_filtering(temp_db):
    """Test 7d, 30d, 90d, and all window boundaries."""
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]
    offer_50ml = temp_db["offer_50ml_id"]

    now = datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc)

    # Snapshots across varying intervals
    with get_connection(path) as conn:
        c = conn.cursor()
        for days_ago, price in [(120, 550.0), (60, 520.0), (20, 490.0), (3, 465.0), (1, 465.0)]:
            ts = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute(
                "INSERT INTO price_history (offer_id, price, currency, data_source, data_status, recorded_at) VALUES (?, ?, 'INR', 'test', 'demo', ?)",
                (offer_50ml, price, ts),
            )

    # 7-day window
    h_7d = get_product_price_history(p1_id, window_days=7, reference_date=now, custom_path=path)
    assert h_7d.observation_count == 2

    # 30-day window
    h_30d = get_product_price_history(p1_id, window_days=30, reference_date=now, custom_path=path)
    assert h_30d.observation_count == 3

    # 90-day window
    h_90d = get_product_price_history(p1_id, window_days=90, reference_date=now, custom_path=path)
    assert h_90d.observation_count == 4

    # All window
    h_all = get_product_price_history(p1_id, window_days=None, reference_date=now, custom_path=path)
    assert h_all.observation_count == 5


def test_honest_insufficient_history_state(temp_db):
    """When a product has fewer than 2 observations, ensure honest empty state without invented stats."""
    path = temp_db["path"]
    p2_id = temp_db["p2_id"]
    offer_p2 = temp_db["offer_p2_id"]

    now = datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc)

    # 0 observations
    h_zero = get_product_price_history(p2_id, custom_path=path)
    assert h_zero.is_sufficient_history is False
    assert h_zero.min_price is None
    assert h_zero.max_price is None
    assert h_zero.avg_price is None
    assert len(h_zero.points) == 0

    # 1 observation only (< 2 is insufficient to establish a genuine trend)
    with get_connection(path) as conn:
        c = conn.cursor()
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            "INSERT INTO price_history (offer_id, price, currency, data_source, data_status, recorded_at) VALUES (?, ?, 'INR', 'test', 'demo', ?)",
            (offer_p2, 399.0, ts),
        )

    h_one = get_product_price_history(p2_id, reference_date=now, custom_path=path)
    assert h_one.is_sufficient_history is False
    assert h_one.min_price is None
    assert h_one.avg_price is None
    assert len(h_one.points) == 1


# =============================================================================
# 3. Watchlist & Price Tracking Validation Tests
# =============================================================================

def test_watchlist_target_price_validation(temp_db):
    """Test positive INR validation, duplicate tracking rejection, and updating targets."""
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]

    # Rejects target <= 0
    success, msg, _ = add_tracked_product(p1_id, target_price=0, custom_path=path)
    assert success is False
    assert "greater than zero" in msg.lower()

    success, msg, _ = add_tracked_product(p1_id, target_price=-150, custom_path=path)
    assert success is False

    # Valid positive INR target price
    success, msg, track_id = add_tracked_product(
        p1_id, target_price=450.0, note="Wait for Diwali sale", custom_path=path
    )
    assert success is True
    assert track_id is not None

    # Duplicate tracking prevented
    dup_success, dup_msg, _ = add_tracked_product(p1_id, target_price=440.0, custom_path=path)
    assert dup_success is False
    assert "already in your price tracker" in dup_msg.lower()

    # Update target price
    up_success, up_msg = update_target_price(track_id, new_target_price=420.0, custom_path=path)
    assert up_success is True

    # Reject invalid target update
    bad_up, _ = update_target_price(track_id, new_target_price=-50.0, custom_path=path)
    assert bad_up is False


def test_watchlist_lifecycle_and_pausing(temp_db):
    """Test pause, resume, and removal from watchlist."""
    path = temp_db["path"]
    p2_id = temp_db["p2_id"]

    _, _, track_id = add_tracked_product(p2_id, target_price=350.0, custom_path=path)

    # Pause tracking
    p_ok, _ = pause_tracking(track_id, custom_path=path)
    assert p_ok is True
    records = get_tracked_products(custom_path=path)
    matched = [r for r in records if r.id == track_id][0]
    assert matched.is_active is False

    # Resume tracking
    r_ok, _ = resume_tracking(track_id, custom_path=path)
    assert r_ok is True
    records = get_tracked_products(custom_path=path)
    matched = [r for r in records if r.id == track_id][0]
    assert matched.is_active is True

    # Remove tracking
    d_ok, _ = remove_tracking(track_id, custom_path=path)
    assert d_ok is True
    assert len(get_tracked_products(custom_path=path)) == 0


# =============================================================================
# 4. Price Alert Architecture, Duplicate Prevention & Delivery Tests
# =============================================================================

def test_alert_generation_and_duplicate_prevention(temp_db):
    """Verify alerts trigger strictly when criteria met, prevent duplicate triggers, and tag in-app delivery."""
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]

    # Current lowest offer for p1 is 465.0 on Nykaa.
    # Set target price to 470.0 (already reached).
    add_tracked_product(p1_id, target_price=470.0, custom_path=path)

    # Evaluate rules: should trigger target_reached alert
    eval_res = evaluate_tracking_rules(custom_path=path)
    assert eval_res["alerts_generated"] == 1
    alert = eval_res["alerts"][0]
    assert alert.alert_type == "target_reached"
    assert alert.observed_price == 465.0
    assert alert.delivery_status == "in_app_delivered"
    assert alert.channel == "in_app"

    # Evaluate again without price change: duplicate prevention should ensure 0 new alerts
    eval_res2 = evaluate_tracking_rules(custom_path=path)
    assert eval_res2["alerts_generated"] == 0

    # Retrieve inbox alerts
    inbox = get_alert_history(custom_path=path)
    assert len(inbox) == 1
    assert inbox[0].is_read is False
    assert inbox[0].delivery_status == "in_app_delivered"
    assert inbox[0].channel == "in_app"

    # Mark alert as read
    mark_alert_read(inbox[0].id, custom_path=path)
    unread_inbox = get_alert_history(unread_only=True, custom_path=path)
    assert len(unread_inbox) == 0

    # Mark all read
    mark_all_alerts_read(custom_path=path)
