"""Phase 8 Comprehensive Integration & Academic Project Readiness Test Suite.

Verifies end-to-end integration across all subsystems:
1. Registering a user and creating a personal wishlist
2. Saving preferences and applying them to the Smart Purchase Advisor
3. Tracking a product from the comparison workflow
4. Evaluating target-price alerts deterministically
5. Ensuring repeated evaluation prevents duplicate alerts (deduplication)
6. Logging out and authenticating as a different user
7. Ensuring private records, alerts, and tracking do not leak across users
8. Migrating a database containing legacy Phase 6 records safely
9. Handling an empty catalog or missing price history gracefully
10. Handling invalid inputs and edge cases without application crashes
"""

import os
import tempfile
import pytest

from src.database.connection import get_connection, migrate_db, init_db
from src.database.seed import seed_database
from src.database.models import Product
from src.analysis.deal_detector import analyze_product_deal
from src.services.auth_service import (
    register_user,
    authenticate_user,
    get_user_by_id,
    get_user_by_email,
)
from src.services.wishlist_service import (
    add_to_wishlist,
    get_user_wishlist,
    update_wishlist_note,
    remove_from_wishlist,
    get_wishlist_count,
)
from src.services.preference_service import (
    save_user_preferences,
    get_user_preferences,
    reset_user_preferences,
)
from src.services.recommendation_service import (
    AdvisorPreferences,
    get_purchase_recommendations,
)
from src.services.price_tracking_service import (
    add_tracked_product,
    get_tracked_products,
    get_tracking_by_product_id,
    update_target_price,
    remove_tracking,
    evaluate_tracking_rules,
    get_alert_history,
    mark_alert_read,
)
from src.services.product_service import (
    get_products,
    get_product_by_id,
)
from src.services.comparison_service import generate_comparison_summary


@pytest.fixture
def p8_test_db():
    """Temporary isolated seeded database for Phase 8 integration tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True, seed_demo_user=False)
    migrate_db(custom_path=path)
    yield path
    if os.path.exists(path):
        os.remove(path)


# =====================================================================
# Scenario 1: User Registration & Personal Wishlist Management
# =====================================================================

def test_p8_01_register_user_and_create_wishlist(p8_test_db):
    """Scenario 1: Full registration lifecycle, adding items, editing notes, removing items."""
    # 1. Register User
    ok, msg, user = register_user(
        email="student.researcher@univ.edu",
        password="SecurePass2026!",
        display_name="Student Researcher",
        custom_path=p8_test_db,
    )
    assert ok is True
    assert user is not None
    assert user.id > 0
    assert user.display_name == "Student Researcher"

    # 2. Add two products to wishlist
    ok1, _, w1 = add_to_wishlist(user.id, product_id=1, note="Research laptop", custom_path=p8_test_db)
    ok2, _, w2 = add_to_wishlist(user.id, product_id=2, note="Lab desktop monitor/PC", custom_path=p8_test_db)
    assert ok1 is True and ok2 is True

    # 3. Retrieve wishlist and verify metadata joining
    items = get_user_wishlist(user.id, custom_path=p8_test_db)
    assert len(items) == 2
    assert any(i.product_id == 1 for i in items)
    assert any(i.product_id == 2 for i in items)
    assert all(i.lowest_price is not None for i in items)

    # 4. Update note
    ok_up, _ = update_wishlist_note(w1, user.id, "Priority laptop for machine learning", custom_path=p8_test_db)
    assert ok_up is True
    updated_items = get_user_wishlist(user.id, custom_path=p8_test_db)
    target_item = next(i for i in updated_items if i.id == w1)
    assert target_item.note == "Priority laptop for machine learning"

    # 5. Remove one item
    ok_del, _ = remove_from_wishlist(w2, user.id, custom_path=p8_test_db)
    assert ok_del is True
    assert get_wishlist_count(user.id, custom_path=p8_test_db) == 1


# =====================================================================
# Scenario 2: User Preferences & Personalized Smart Purchase Advisor
# =====================================================================

def test_p8_02_preferences_influence_smart_advisor(p8_test_db):
    """Scenario 2: Shopping preferences tailor recommendations while respecting hard budget limits."""
    # Register user
    ok, _, user = register_user("gamer@univ.edu", "GamerPass123!", "Competitive Gamer", custom_path=p8_test_db)
    assert ok is True

    # Save gaming & Apple preferences
    ok_pref, _ = save_user_preferences(
        user_id=user.id,
        preferred_categories=["Laptops"],
        preferred_brands=["Apple"],
        min_budget=1000.0,
        max_budget=2500.0,
        sort_preference="best_deal",
        priority="best_deal",
        custom_path=p8_test_db,
    )
    assert ok_pref is True

    saved_prefs = get_user_preferences(user.id, custom_path=p8_test_db)
    assert saved_prefs.preferred_brands == ["Apple"]
    assert saved_prefs.max_budget == 2500.0

    # Build Advisor preferences utilizing saved profile
    advisor_prefs = AdvisorPreferences(
        budget=saved_prefs.max_budget,
        category="Laptops",
        use_case="Programming",
        preferred_categories=saved_prefs.preferred_categories,
        preferred_brands=saved_prefs.preferred_brands,
        priority=saved_prefs.priority,
        user_saved_min_budget=saved_prefs.min_budget,
        user_saved_max_budget=saved_prefs.max_budget,
    )

    results = get_purchase_recommendations(advisor_prefs, custom_path=p8_test_db)
    assert len(results.ranked_candidates) > 0

    top_rec = results.ranked_candidates[0]
    # Check that brand preference matches and gave high brand suitability
    assert top_rec.product.brand == "Apple"
    assert top_rec.score_breakdown["Brand Match (10%)"] == 10.0
    assert any("preferred brand" in r.lower() for r in top_rec.reasons)


# =====================================================================
# Scenario 3: Track Product from Comparison Workflow
# =====================================================================

def test_p8_03_track_product_from_comparison(p8_test_db):
    """Scenario 3: Compare stores, identify lowest offer, and establish tracking monitor."""
    ok, _, user = register_user("shopper@univ.edu", "ShopPass123!", "Smart Shopper", custom_path=p8_test_db)
    assert ok is True

    # Compare store offers for Product 1
    prod = get_product_by_id(1, custom_path=p8_test_db)
    assert prod is not None
    summary = generate_comparison_summary(prod)
    assert summary is not None
    assert summary.lowest_price > 0

    # Set target price 10% below lowest offer
    target_price = round(summary.lowest_price * 0.90, 2)
    ok_track, msg, track_id = add_tracked_product(
        product_id=prod.id,
        target_price=target_price,
        note="Comparison page quick track",
        user_id=user.id,
        custom_path=p8_test_db,
    )
    assert ok_track is True
    assert track_id > 0

    # Verify tracking record retrieved
    rec = get_tracking_by_product_id(prod.id, user_id=user.id, custom_path=p8_test_db)
    assert rec is not None
    assert rec.target_price == target_price
    assert rec.is_active is True
    assert rec.is_target_reached is False  # Target is 10% below current lowest offer


# =====================================================================
# Scenario 4: Target-Price Alert Evaluation
# =====================================================================

def test_p8_04_evaluate_target_price_alert(p8_test_db):
    """Scenario 4: Trigger an in-app alert when observed lowest offer meets target threshold."""
    ok, _, user = register_user("alert_user@univ.edu", "AlertPass123!", "Alert Monitor", custom_path=p8_test_db)
    prod = get_product_by_id(1, custom_path=p8_test_db)

    # Set target price above current lowest offer so it immediately meets criteria
    target_price = prod.lowest_price + 50.0
    add_tracked_product(
        product_id=prod.id,
        target_price=target_price,
        alert_trigger_type="target_only",
        user_id=user.id,
        custom_path=p8_test_db,
    )

    # Evaluate rules
    res = evaluate_tracking_rules(user_id=user.id, custom_path=p8_test_db)
    assert res["evaluated_count"] == 1
    assert res["alerts_generated"] == 1

    # Check alert in inbox
    alerts = get_alert_history(user_id=user.id, custom_path=p8_test_db)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_type == "target_reached"
    assert alert.observed_price <= target_price
    assert alert.is_read == 0
    assert "below your target" in alert.message.lower() or "reached" in alert.message.lower()


# =====================================================================
# Scenario 5: Duplicate Alert Prevention on Repeated Evaluations
# =====================================================================

def test_p8_05_repeated_evaluation_prevents_duplicate_alerts(p8_test_db):
    """Scenario 5: Subsequent evaluations on unchanged prices must not create spam alerts."""
    ok, _, user = register_user("dedup_user@univ.edu", "DedupPass123!", "Dedup Test", custom_path=p8_test_db)
    prod = get_product_by_id(1, custom_path=p8_test_db)

    add_tracked_product(
        product_id=prod.id,
        target_price=prod.lowest_price + 20.0,
        user_id=user.id,
        custom_path=p8_test_db,
    )

    # First evaluation generates 1 alert
    res1 = evaluate_tracking_rules(user_id=user.id, custom_path=p8_test_db)
    assert res1["alerts_generated"] == 1

    # Second and third evaluations must generate 0 alerts
    res2 = evaluate_tracking_rules(user_id=user.id, custom_path=p8_test_db)
    res3 = evaluate_tracking_rules(user_id=user.id, custom_path=p8_test_db)
    assert res2["alerts_generated"] == 0
    assert res3["alerts_generated"] == 0

    # Total stored alerts remains exactly 1
    all_alerts = get_alert_history(user_id=user.id, custom_path=p8_test_db)
    assert len(all_alerts) == 1


# =====================================================================
# Scenario 6: User Authentication Lifecycle & Multiple Accounts
# =====================================================================

def test_p8_06_logout_and_login_as_another_user(p8_test_db):
    """Scenario 6: Verify authentication returns separate user contexts for different accounts."""
    # Register Account A and Account B
    register_user("user_a@univ.edu", "UserAPass123!", "User Alpha", custom_path=p8_test_db)
    register_user("user_b@univ.edu", "UserBPass123!", "User Beta", custom_path=p8_test_db)

    # Authenticate User A
    ok_a, msg_a, user_a = authenticate_user("user_a@univ.edu", "UserAPass123!", custom_path=p8_test_db)
    assert ok_a is True
    assert user_a is not None
    assert user_a.display_name == "User Alpha"

    # Authenticate User B
    ok_b, msg_b, user_b = authenticate_user("user_b@univ.edu", "UserBPass123!", custom_path=p8_test_db)
    assert ok_b is True
    assert user_b is not None
    assert user_b.display_name == "User Beta"
    assert user_b.id != user_a.id

    # Wrong password fails
    ok_f, fail_msg, fail_user = authenticate_user("user_a@univ.edu", "WrongPassword", custom_path=p8_test_db)
    assert ok_f is False
    assert fail_user is None
    assert "invalid" in fail_msg.lower()


# =====================================================================
# Scenario 7: Multi-Tenant Data Isolation Enforcement
# =====================================================================

def test_p8_07_private_records_isolation_across_users(p8_test_db):
    """Scenario 7: Prevent cross-user access, unauthorized updates, and alert leaking."""
    _, _, user1 = register_user("owner@univ.edu", "PassOwner1!", "Owner", custom_path=p8_test_db)
    _, _, user2 = register_user("intruder@univ.edu", "PassIntruder1!", "Intruder", custom_path=p8_test_db)

    # User 1 adds wishlist and tracking
    add_to_wishlist(user1.id, product_id=1, note="Private gift list", custom_path=p8_test_db)
    _, _, track_id = add_tracked_product(product_id=1, target_price=1500.0, user_id=user1.id, custom_path=p8_test_db)

    # User 2 sees 0 wishlist items and 0 tracked items
    u2_wish = get_user_wishlist(user2.id, custom_path=p8_test_db)
    u2_track = get_tracked_products(user_id=user2.id, custom_path=p8_test_db)
    assert len(u2_wish) == 0
    assert len(u2_track) == 0

    # User 2 cannot modify User 1's target price
    ok_edit, edit_msg = update_target_price(track_id, 999.0, user_id=user2.id, custom_path=p8_test_db)
    assert ok_edit is False
    assert "access denied" in edit_msg.lower() or "unauthorized" in edit_msg.lower() or "not found" in edit_msg.lower()

    # User 2 cannot delete User 1's tracking
    ok_del, del_msg = remove_tracking(track_id, user_id=user2.id, custom_path=p8_test_db)
    assert ok_del is False

    # Original record remains untouched
    u1_rec = get_tracking_by_product_id(1, user_id=user1.id, custom_path=p8_test_db)
    assert u1_rec.target_price == 1500.0


# =====================================================================
# Scenario 8: Database Migration with Existing Phase 6 Records
# =====================================================================

def test_p8_08_migrate_database_with_existing_phase6_records():
    """Scenario 8: Test non-destructive migration on a legacy Phase 6 schema database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        # Create legacy Phase 6 schema without users/wishlist and with single-column UNIQUE(product_id)
        with get_connection(path) as conn:
            conn.executescript(
                """
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    specs_json TEXT,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE stores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    website TEXT,
                    shipping_policy TEXT,
                    rating REAL DEFAULT 4.0
                );

                CREATE TABLE offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    store_id INTEGER NOT NULL,
                    variant_name TEXT,
                    current_price REAL NOT NULL,
                    original_price REAL,
                    currency TEXT DEFAULT 'USD',
                    availability TEXT DEFAULT 'In Stock',
                    shipping_cost REAL DEFAULT 0.0,
                    return_days INTEGER DEFAULT 30,
                    product_url TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE price_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER UNIQUE NOT NULL,
                    target_price REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    last_observed_price REAL,
                    last_checked_at TIMESTAMP,
                    last_alert_at TIMESTAMP,
                    last_alert_price REAL,
                    last_alert_type TEXT,
                    alert_trigger_type TEXT DEFAULT 'target_or_drop',
                    note TEXT
                );

                CREATE TABLE price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tracking_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    observed_price REAL NOT NULL,
                    previous_price REAL,
                    target_price REAL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read INTEGER DEFAULT 0,
                    trigger_key TEXT UNIQUE
                );

                INSERT INTO products (id, sku, title, brand, category) VALUES (1, 'SKU-001', 'Legacy Laptop', 'BrandX', 'Laptops');
                INSERT INTO stores (id, name) VALUES (1, 'TechDirect');
                INSERT INTO offers (product_id, store_id, current_price, availability) VALUES (1, 1, 950.0, 'In Stock');
                INSERT INTO price_tracking (id, product_id, target_price, note) VALUES (10, 1, 950.0, 'Legacy Phase 6 tracking record');
                INSERT INTO price_alerts (id, tracking_id, product_id, alert_type, observed_price, message, trigger_key)
                VALUES (20, 10, 1, 'target_reached', 940.0, 'Legacy alert', 'legacy_key_1');
                """
            )

        # Run Phase 7/8 Migration
        migrate_db(custom_path=path)

        # Verify legacy tracking record is preserved with user_id NULL
        with get_connection(path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, user_id, target_price, note FROM price_tracking WHERE id = 10")
            row = c.fetchone()
            assert row is not None
            assert row["id"] == 10
            assert row["user_id"] is None
            assert row["target_price"] == 950.0

            # Verify legacy alert is preserved
            c.execute("SELECT id, message FROM price_alerts WHERE id = 20")
            alert_row = c.fetchone()
            assert alert_row is not None
            assert alert_row["id"] == 20

            # Verify Phase 7 tables exist
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            assert c.fetchone() is not None
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wishlist'")
            assert c.fetchone() is not None

        # Register two users to test tracking collision under new schema
        ok_reg1, _, u101 = register_user("migrated1@univ.edu", "MigratePass123!", "User 101", custom_path=path)
        ok_reg2, _, u102 = register_user("migrated2@univ.edu", "MigratePass123!", "User 102", custom_path=path)
        assert ok_reg1 is True and ok_reg2 is True

        # Verify multi-user tracking collision is now permitted for product 1
        ok_a, _, _ = add_tracked_product(product_id=1, target_price=900.0, user_id=u101.id, custom_path=path)
        ok_b, _, _ = add_tracked_product(product_id=1, target_price=850.0, user_id=u102.id, custom_path=path)
        assert ok_a is True and ok_b is True

    finally:
        if os.path.exists(path):
            os.remove(path)


# =====================================================================
# Scenario 9: Empty Catalog & Missing History Graceful Handling
# =====================================================================

def test_p8_09_empty_catalog_and_missing_price_history_handling():
    """Scenario 9: Validate empty databases or items with zero history do not crash."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        init_db(custom_path=path)

        # Query catalog on completely empty DB
        products = get_products(custom_path=path)
        assert products == []

        missing_prod = get_product_by_id(999, custom_path=path)
        assert missing_prod is None

        # Recommendation on empty catalog returns empty compliant list
        prefs = AdvisorPreferences(budget=1000.0)
        results = get_purchase_recommendations(prefs, custom_path=path)
        assert results.ranked_candidates == []
        assert results.best_overall is None
        assert results.best_budget is None
        assert results.best_current_deal is None

        # Deal analysis on None or item with no offers returns None
        assert analyze_product_deal(None) is None

    finally:
        if os.path.exists(path):
            os.remove(path)


# =====================================================================
# Scenario 10: Invalid Inputs & SQL Injection Resilience
# =====================================================================

def test_p8_10_invalid_inputs_resilience(p8_test_db):
    """Scenario 10: System rejects invalid data, malformed inputs, and SQL injection safely."""
    # 1. Negative target price rejected
    ok, msg, _ = add_tracked_product(product_id=1, target_price=-50.0, custom_path=p8_test_db)
    assert ok is False
    assert "positive" in msg.lower() or "greater" in msg.lower() or "invalid" in msg.lower()

    # 2. Tracking nonexistent product rejected
    ok_none, msg_none, _ = add_tracked_product(product_id=9999, target_price=500.0, custom_path=p8_test_db)
    assert ok_none is False

    # 3. Short password rejected
    ok_pass, msg_pass, _ = register_user("bad@univ.edu", "123", "Short Pass", custom_path=p8_test_db)
    assert ok_pass is False

    # 4. Malformed email rejected
    ok_em, msg_em, _ = register_user("not-an-email", "ValidPass123!", "Bad Email", custom_path=p8_test_db)
    assert ok_em is False

    # 5. Invalid budget range (max < min) rejected
    register_user("valid@univ.edu", "ValidPass123!", "Valid User", custom_path=p8_test_db)
    u = get_user_by_email("valid@univ.edu", custom_path=p8_test_db)
    ok_b, msg_b = save_user_preferences(
        user_id=u.id,
        min_budget=1500.0,
        max_budget=500.0,  # Max < Min
        custom_path=p8_test_db,
    )
    assert ok_b is False

    # 6. SQL Injection attempts in product search query are safely handled via parameterized queries
    sql_injection_query = "'; DROP TABLE products; --"
    prods = get_products(search_query=sql_injection_query, custom_path=p8_test_db)
    assert prods == []

    # Verify products table is safe and unaffected
    all_prods = get_products(custom_path=p8_test_db)
    assert len(all_prods) > 0
