"""Phase 6 Comprehensive Test Suite: Price Tracking & Alerts.

Tests cover all 22 required areas across:
Database & Tracking:
1. Create a tracking record
2. Retrieve tracked products
3. Persist tracking across service instances or database connections
4. Update a target price
5. Pause tracking
6. Resume tracking
7. Remove tracking
8. Reject invalid target prices
9. Handle nonexistent products
10. Handle duplicate tracking attempts

Alert Logic:
11. Generate alert when observed price reaches target
12. Do not alert when observed price remains above target
13. Generate a price-drop alert when configured rule is satisfied
14. Do not generate alerts for insignificant changes
15. Do not generate alerts for paused tracking
16. Do not generate price-based alerts when price is missing / out of stock
17. Prevent duplicate alerts on repeated evaluations
18. Allow later meaningful price change to generate a new alert
19. Persist alert history
20. Mark alerts as read / mark all as read
21. Ensure price observations are matched to correct product variant
22. Ensure initial baseline is not incorrectly reported as price drop
"""

from datetime import datetime, timezone
import tempfile
import os
import pytest

from src.database.connection import get_connection, migrate_db
from src.database.seed import seed_database
from src.database.price_history_service import record_price_observation
from src.services.price_tracking_service import (
    add_tracked_product,
    get_tracked_products,
    get_tracking_by_id,
    get_tracking_by_product_id,
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


@pytest.fixture
def p6_test_db():
    """Temporary isolated seeded database for Phase 6 tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    migrate_db(custom_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


# =====================================================================
# Database & Tracking Operations
# =====================================================================

def test_p6_01_create_tracking_record(p6_test_db):
    """Verify creating a valid tracking record succeeds and returns tracking ID."""
    success, msg, track_id = add_tracked_product(
        product_id=1,
        target_price=1600.0,
        note="Looking for holiday deal",
        custom_path=p6_test_db,
    )
    assert success is True
    assert track_id is not None
    assert "Started tracking" in msg

    # Verify fields in database
    record = get_tracking_by_id(track_id, custom_path=p6_test_db)
    assert record is not None
    assert record.product_id == 1
    assert record.target_price == 1600.0
    assert record.status == "active"
    assert record.note == "Looking for holiday deal"
    assert record.last_observed_price is not None


def test_p6_02_retrieve_tracked_products(p6_test_db):
    """Verify retrieving tracked products populates joined product metadata."""
    add_tracked_product(product_id=1, target_price=1700.0, custom_path=p6_test_db)
    add_tracked_product(product_id=2, target_price=1800.0, custom_path=p6_test_db)

    tracked = get_tracked_products(custom_path=p6_test_db)
    assert len(tracked) == 2
    # Verify joined catalog metadata
    p1 = next((t for t in tracked if t.product_id == 1), None)
    assert p1 is not None
    assert "Apple" in p1.product_brand or "MacBook" in p1.product_title
    assert p1.current_lowest_price is not None
    assert p1.current_lowest_store is not None


def test_p6_03_persistence_across_connections(p6_test_db):
    """Verify tracking records persist across separate database connections."""
    success, _, track_id = add_tracked_product(
        product_id=3, target_price=1000.0, note="Persistent check", custom_path=p6_test_db
    )
    assert success is True

    # Open fresh connection to inspect raw table
    with get_connection(p6_test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, target_price, note FROM price_tracking WHERE id = ?", (track_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row["target_price"] == 1000.0
        assert row["note"] == "Persistent check"


def test_p6_04_update_target_price(p6_test_db):
    """Verify updating a target price succeeds and clears last alert price."""
    _, _, track_id = add_tracked_product(product_id=4, target_price=900.0, custom_path=p6_test_db)

    success, msg = update_target_price(track_id, 850.0, custom_path=p6_test_db)
    assert success is True
    assert "$850.00" in msg

    updated = get_tracking_by_id(track_id, custom_path=p6_test_db)
    assert updated.target_price == 850.0
    assert updated.last_alert_price is None


def test_p6_05_pause_tracking(p6_test_db):
    """Verify pausing a tracking record marks it paused and prevents it from being active."""
    _, _, track_id = add_tracked_product(product_id=5, target_price=300.0, custom_path=p6_test_db)

    success, msg = pause_tracking(track_id, custom_path=p6_test_db)
    assert success is True
    assert "paused" in msg.lower()

    rec = get_tracking_by_id(track_id, custom_path=p6_test_db)
    assert rec.is_paused is True
    assert rec.is_active is False

    # Check active filter excludes it
    active_records = get_tracked_products(status="active", custom_path=p6_test_db)
    assert all(r.id != track_id for r in active_records)


def test_p6_06_resume_tracking(p6_test_db):
    """Verify resuming a paused tracking record restores active status."""
    _, _, track_id = add_tracked_product(product_id=6, target_price=350.0, custom_path=p6_test_db)
    pause_tracking(track_id, custom_path=p6_test_db)

    success, msg = resume_tracking(track_id, custom_path=p6_test_db)
    assert success is True
    assert "resumed" in msg.lower()

    rec = get_tracking_by_id(track_id, custom_path=p6_test_db)
    assert rec.is_active is True
    assert rec.is_paused is False


def test_p6_07_remove_tracking(p6_test_db):
    """Verify removing a tracking record deletes it completely."""
    _, _, track_id = add_tracked_product(product_id=7, target_price=400.0, custom_path=p6_test_db)
    assert get_tracking_by_id(track_id, custom_path=p6_test_db) is not None

    success, msg = remove_tracking(track_id, custom_path=p6_test_db)
    assert success is True
    assert "removed" in msg.lower()

    assert get_tracking_by_id(track_id, custom_path=p6_test_db) is None


def test_p6_08_reject_invalid_target_prices(p6_test_db):
    """Verify service rejects zero, negative, None, and non-numeric target prices."""
    # Zero target
    ok, msg, _ = add_tracked_product(product_id=1, target_price=0.0, custom_path=p6_test_db)
    assert ok is False
    assert "greater than zero" in msg

    # Negative target
    ok, msg, _ = add_tracked_product(product_id=1, target_price=-50.0, custom_path=p6_test_db)
    assert ok is False
    assert "greater than zero" in msg

    # None target
    ok, msg, _ = add_tracked_product(product_id=1, target_price=None, custom_path=p6_test_db)
    assert ok is False
    assert "cannot be empty" in msg

    # Updating target price with negative value
    _, _, t_id = add_tracked_product(product_id=1, target_price=500.0, custom_path=p6_test_db)
    update_ok, update_msg = update_target_price(t_id, -20.0, custom_path=p6_test_db)
    assert update_ok is False


def test_p6_09_handle_nonexistent_product(p6_test_db):
    """Verify attempting to track a nonexistent product returns error."""
    ok, msg, _ = add_tracked_product(product_id=999999, target_price=100.0, custom_path=p6_test_db)
    assert ok is False
    assert "does not exist" in msg


def test_p6_10_handle_duplicate_tracking(p6_test_db):
    """Verify attempting to track the same product twice is prevented."""
    ok1, _, track_id = add_tracked_product(product_id=8, target_price=300.0, custom_path=p6_test_db)
    assert ok1 is True

    # Duplicate attempt
    ok2, msg2, existing_id = add_tracked_product(product_id=8, target_price=250.0, custom_path=p6_test_db)
    assert ok2 is False
    assert "already in your Price Tracker" in msg2
    assert existing_id == track_id


# =====================================================================
# Alert Logic & Evaluation Rules
# =====================================================================

def test_p6_11_generate_alert_when_target_reached(p6_test_db):
    """Verify an in-app alert is generated when recorded price reaches or falls below target."""
    # Product 1 current lowest price is $1,799.00
    # Set target to $1,800.00 (current price is below target!)
    _, _, track_id = add_tracked_product(product_id=1, target_price=1800.0, custom_path=p6_test_db)

    eval_result = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert eval_result["alerts_generated"] == 1
    alert = eval_result["alerts"][0]
    assert alert.alert_type == "target_reached"
    assert alert.observed_price <= 1800.0
    assert "Target price reached" in alert.message

    # Check alert persisted in inbox
    inbox = get_alert_history(custom_path=p6_test_db)
    assert len(inbox) >= 1
    assert any(a.tracking_id == track_id for a in inbox)


def test_p6_12_no_alert_when_price_above_target(p6_test_db):
    """Verify no target alert is generated when observed price is strictly above target."""
    # Product 1 lowest price is $1,799.00
    # Set target to $1,200.00 (far below current price)
    _, _, track_id = add_tracked_product(
        product_id=1, target_price=1200.0, alert_trigger_type="target_only", custom_path=p6_test_db
    )

    eval_result = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert eval_result["alerts_generated"] == 0

    alerts = get_alert_history(custom_path=p6_test_db)
    assert all(a.tracking_id != track_id for a in alerts)


def test_p6_13_generate_price_drop_alert(p6_test_db):
    """Verify a price drop alert triggers when a new observation drops below the previous one."""
    # Product 8: Apple Watch (current price ~$329.00)
    # Set target to $200 (so target reached will NOT fire)
    _, _, track_id = add_tracked_product(product_id=8, target_price=200.0, custom_path=p6_test_db)

    # Offer 1 for product 8 drops price from $329 to $299 ($30 drop!)
    with get_connection(p6_test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, current_price FROM offers WHERE product_id = 8 ORDER BY current_price ASC LIMIT 1")
        off = cursor.fetchone()
        offer_id = off["id"]
        old_price = off["current_price"]

    # Record genuine price drop
    new_price = round(old_price - 30.0, 2)
    # Record previous observation first, then new observation
    record_price_observation(offer_id=offer_id, price=old_price, recorded_at="2026-10-31 10:00:00", force=True, custom_path=p6_test_db)
    record_price_observation(offer_id=offer_id, price=new_price, recorded_at="2026-10-31 12:00:00", force=True, custom_path=p6_test_db)

    # Update offer's current_price to reflect the drop
    with get_connection(p6_test_db) as conn:
        conn.execute("UPDATE offers SET current_price = ? WHERE id = ?", (new_price, offer_id))

    eval_res = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert eval_res["alerts_generated"] == 1
    alert = eval_res["alerts"][0]
    assert alert.alert_type == "price_drop"
    assert alert.observed_price == new_price
    assert alert.previous_price == old_price
    assert "dropped $30.00" in alert.message


def test_p6_14_no_alert_for_insignificant_changes(p6_test_db):
    """Verify minor price fluctuations below threshold (< $1.00) do NOT trigger price drop alerts."""
    _, _, track_id = add_tracked_product(product_id=8, target_price=200.0, custom_path=p6_test_db)

    with get_connection(p6_test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, current_price FROM offers WHERE product_id = 8 ORDER BY current_price ASC LIMIT 1")
        off = cursor.fetchone()
        offer_id = off["id"]
        old_price = off["current_price"]

    # Tiny 10 cent change
    new_price = round(old_price - 0.10, 2)
    record_price_observation(offer_id=offer_id, price=old_price, recorded_at="2026-10-30 10:00:00", force=True, custom_path=p6_test_db)
    record_price_observation(offer_id=offer_id, price=new_price, recorded_at="2026-10-30 12:00:00", force=True, custom_path=p6_test_db)
    with get_connection(p6_test_db) as conn:
        conn.execute("UPDATE offers SET current_price = ? WHERE id = ?", (new_price, offer_id))

    eval_res = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    # Must NOT generate price drop alert for 10 cents!
    drop_alerts = [a for a in eval_res["alerts"] if a.alert_type == "price_drop"]
    assert len(drop_alerts) == 0


def test_p6_15_no_alert_when_tracking_paused(p6_test_db):
    """Verify paused tracking records are strictly excluded from generating alerts."""
    # Target is met, but tracking is paused!
    _, _, track_id = add_tracked_product(product_id=1, target_price=2000.0, custom_path=p6_test_db)
    pause_tracking(track_id, custom_path=p6_test_db)

    eval_res = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert eval_res["evaluated_count"] == 0
    assert eval_res["alerts_generated"] == 0


def test_p6_16_no_alert_when_product_out_of_stock(p6_test_db):
    """Verify that an unavailable / out-of-stock product does not generate price-based alerts."""
    # Mark all offers for Product 9 out of stock
    with get_connection(p6_test_db) as conn:
        conn.execute("UPDATE offers SET availability = 'Out of Stock' WHERE product_id = 9")

    _, _, track_id = add_tracked_product(product_id=9, target_price=1000.0, custom_path=p6_test_db)

    eval_res = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert eval_res["alerts_generated"] == 0


def test_p6_17_prevent_duplicate_alerts_on_repeated_evaluations(p6_test_db):
    """Verify repeated evaluations on unchanged prices do NOT generate duplicate notifications."""
    _, _, track_id = add_tracked_product(product_id=1, target_price=1800.0, custom_path=p6_test_db)

    # First evaluation: generates 1 alert
    res1 = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert res1["alerts_generated"] == 1

    # Second evaluation immediately after: MUST generate 0 new alerts!
    res2 = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert res2["alerts_generated"] == 0

    # Third evaluation: STILL 0 new alerts!
    res3 = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert res3["alerts_generated"] == 0

    # Total alerts in inbox for this tracking record must be exactly 1
    inbox = get_alert_history(custom_path=p6_test_db)
    matching = [a for a in inbox if a.tracking_id == track_id]
    assert len(matching) == 1


def test_p6_18_subsequent_price_change_generates_new_alert(p6_test_db):
    """Verify when price changes meaningfully later, a new alert is generated."""
    _, _, track_id = add_tracked_product(product_id=1, target_price=1800.0, custom_path=p6_test_db)

    # 1. First alert at $1,799.00
    res1 = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert res1["alerts_generated"] == 1

    # 2. Later price drops to $1,749.00
    with get_connection(p6_test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM offers WHERE product_id = 1 ORDER BY current_price ASC LIMIT 1")
        off_id = cursor.fetchone()["id"]
        conn.execute("UPDATE offers SET current_price = 1749.0 WHERE id = ?", (off_id,))

    record_price_observation(offer_id=off_id, price=1749.0, recorded_at="2026-10-31 10:00:00", force=True, custom_path=p6_test_db)

    # Now evaluate again: genuine new price condition should generate an alert!
    res2 = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert res2["alerts_generated"] == 1
    assert res2["alerts"][0].observed_price == 1749.0


def test_p6_19_persist_alert_history(p6_test_db):
    """Verify generated alerts persist in SQLite and can be retrieved with timestamps and status."""
    _, _, track_id = add_tracked_product(product_id=1, target_price=1850.0, custom_path=p6_test_db)
    evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)

    alerts = get_alert_history(custom_path=p6_test_db)
    assert len(alerts) >= 1
    top_alert = alerts[0]
    assert top_alert.tracking_id == track_id
    assert top_alert.is_read is False
    assert top_alert.created_at is not None
    assert top_alert.product_title is not None


def test_p6_20_mark_alerts_as_read(p6_test_db):
    """Verify marking a single alert and marking all alerts as read."""
    _, _, t1 = add_tracked_product(product_id=1, target_price=1900.0, custom_path=p6_test_db)
    _, _, t2 = add_tracked_product(product_id=2, target_price=2000.0, custom_path=p6_test_db)
    evaluate_tracking_rules(custom_path=p6_test_db)

    unread = get_alert_history(unread_only=True, custom_path=p6_test_db)
    assert len(unread) >= 2

    # Mark single alert as read
    first_id = unread[0].id
    assert mark_alert_read(first_id, custom_path=p6_test_db) is True

    # Verify first alert is now read
    unread_after_one = get_alert_history(unread_only=True, custom_path=p6_test_db)
    assert all(a.id != first_id for a in unread_after_one)

    # Mark all remaining as read
    marked_count = mark_all_alerts_read(custom_path=p6_test_db)
    assert marked_count >= 1

    unread_final = get_alert_history(unread_only=True, custom_path=p6_test_db)
    assert len(unread_final) == 0


def test_p6_21_price_matched_to_correct_variant(p6_test_db):
    """Verify price observation matches the correct product and its active offers."""
    # Product 10: Sony Alpha 7 IV (lowest offer $2,199 is Out of Stock, lowest in-stock is $2,298)
    _, _, track_id = add_tracked_product(product_id=10, target_price=2350.0, custom_path=p6_test_db)

    eval_res = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    assert eval_res["alerts_generated"] == 1
    alert = eval_res["alerts"][0]
    # Must use the in-stock offer ($2,298), NOT the out-of-stock offer ($2,199)
    assert alert.observed_price == 2298.0


def test_p6_22_initial_baseline_not_reported_as_price_drop(p6_test_db):
    """Verify creating a tracker and evaluating it does NOT falsely report the initial price as a price drop."""
    # Set target below current price so target alert won't fire
    _, _, track_id = add_tracked_product(
        product_id=1, target_price=1000.0, alert_trigger_type="drop_only", custom_path=p6_test_db
    )

    eval_res = evaluate_tracking_rules(tracking_id=track_id, custom_path=p6_test_db)
    # Initial baseline is not a price drop
    assert eval_res["alerts_generated"] == 0
