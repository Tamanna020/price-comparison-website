"""Tests for Authorization, Multi-User Isolation & Personalization (Phase 7 - Step 10)."""

import os
import tempfile
import pytest

from src.database.connection import get_connection, migrate_db
from src.database.seed import seed_database
from src.services.auth_service import register_user
from src.services.price_tracking_service import (
    add_tracked_product,
    get_tracked_products,
    get_tracking_by_id,
    update_target_price,
    remove_tracking,
    pause_tracking,
    evaluate_tracking_rules,
    get_alert_history,
    mark_alert_read,
)
from src.services.recommendation_service import (
    AdvisorPreferences,
    get_purchase_recommendations,
)


@pytest.fixture
def p7_personal_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_p7_22_user_cannot_access_other_users_tracking_records(p7_personal_db):
    """Verify User A's tracking list and queries do not leak User B's tracked products."""
    _, _, user_a = register_user("usera_trk@example.com", "secret123", "User A", custom_path=p7_personal_db)
    _, _, user_b = register_user("userb_trk@example.com", "secret123", "User B", custom_path=p7_personal_db)

    # User A tracks product 1 at $1,750
    _, _, id_a = add_tracked_product(1, 1750.0, user_id=user_a.id, custom_path=p7_personal_db)

    # User B tracks product 2 at $300
    _, _, id_b = add_tracked_product(2, 300.0, user_id=user_b.id, custom_path=p7_personal_db)

    list_a = get_tracked_products(user_id=user_a.id, custom_path=p7_personal_db)
    list_b = get_tracked_products(user_id=user_b.id, custom_path=p7_personal_db)

    assert len(list_a) == 1
    assert list_a[0].id == id_a
    assert list_a[0].product_id == 1

    assert len(list_b) == 1
    assert list_b[0].id == id_b
    assert list_b[0].product_id == 2

    # Direct query by ID with User B context returns None for User A's record
    assert get_tracking_by_id(id_a, user_id=user_b.id, custom_path=p7_personal_db) is None
    assert get_tracking_by_id(id_b, user_id=user_a.id, custom_path=p7_personal_db) is None


def test_p7_23_user_cannot_edit_other_users_tracking_target(p7_personal_db):
    """Verify User B cannot edit User A's target price."""
    _, _, user_a = register_user("owner_edit@example.com", "secret123", "Owner", custom_path=p7_personal_db)
    _, _, user_b = register_user("attacker_edit@example.com", "secret123", "Attacker", custom_path=p7_personal_db)

    _, _, track_id = add_tracked_product(1, 1750.0, user_id=user_a.id, custom_path=p7_personal_db)

    # User B tries to update User A's target price
    edit_ok, edit_msg = update_target_price(track_id, 1500.0, user_id=user_b.id, custom_path=p7_personal_db)
    assert edit_ok is False
    assert "access denied" in edit_msg.lower()

    # Target price in User A's record must be unchanged
    rec = get_tracking_by_id(track_id, user_id=user_a.id, custom_path=p7_personal_db)
    assert rec.target_price == 1750.0


def test_p7_24_user_cannot_remove_other_users_tracking(p7_personal_db):
    """Verify User B cannot delete or pause User A's tracking record."""
    _, _, user_a = register_user("owner_del@example.com", "secret123", "Owner", custom_path=p7_personal_db)
    _, _, user_b = register_user("attacker_del@example.com", "secret123", "Attacker", custom_path=p7_personal_db)

    _, _, track_id = add_tracked_product(1, 1750.0, user_id=user_a.id, custom_path=p7_personal_db)

    # 1. User B tries to pause User A's tracking
    pause_ok, pause_msg = pause_tracking(track_id, user_id=user_b.id, custom_path=p7_personal_db)
    assert pause_ok is False
    assert "access denied" in pause_msg.lower()

    # 2. User B tries to remove User A's tracking
    rem_ok, rem_msg = remove_tracking(track_id, user_id=user_b.id, custom_path=p7_personal_db)
    assert rem_ok is False
    assert "access denied" in rem_msg.lower()

    # Still exists for User A
    assert get_tracking_by_id(track_id, user_id=user_a.id, custom_path=p7_personal_db) is not None


def test_p7_25_user_cannot_read_or_modify_other_users_alerts(p7_personal_db):
    """Verify alerts generated for User A are isolated from User B."""
    _, _, user_a = register_user("alert_a@example.com", "secret123", "User A", custom_path=p7_personal_db)
    _, _, user_b = register_user("alert_b@example.com", "secret123", "User B", custom_path=p7_personal_db)

    # Product 1 (MacBook Pro) currently sells at $1,799.00
    # User A sets target to $1,850.00 (triggers target reached alert!)
    add_tracked_product(1, 1850.0, user_id=user_a.id, custom_path=p7_personal_db)

    # Evaluate rules for User A
    eval_res = evaluate_tracking_rules(user_id=user_a.id, custom_path=p7_personal_db)
    assert eval_res["alerts_generated"] == 1

    alerts_a = get_alert_history(user_id=user_a.id, custom_path=p7_personal_db)
    alerts_b = get_alert_history(user_id=user_b.id, custom_path=p7_personal_db)

    assert len(alerts_a) == 1
    assert len(alerts_b) == 0

    alert_id = alerts_a[0].id

    # User B tries to mark User A's alert as read
    mark_ok = mark_alert_read(alert_id, user_id=user_b.id, custom_path=p7_personal_db)
    assert mark_ok is False

    # Still unread for User A
    unread_a = get_alert_history(unread_only=True, user_id=user_a.id, custom_path=p7_personal_db)
    assert len(unread_a) == 1


def test_p7_26_legacy_tracking_records_survive_migration(p7_personal_db):
    """Verify legacy tracking records (created before Phase 7) remain intact with user_id NULL."""
    # Insert a legacy tracking record directly with NULL user_id
    with get_connection(p7_personal_db) as conn:
        conn.execute(
            """
            INSERT INTO price_tracking (user_id, product_id, target_price, created_at, status)
            VALUES (NULL, 8, 300.0, '2026-10-30 00:00:00', 'active')
            """
        )

    # Fetch with include_legacy=True
    legacy_records = get_tracked_products(include_legacy=True, custom_path=p7_personal_db)
    matching = [r for r in legacy_records if r.product_id == 8]
    assert len(matching) == 1
    assert matching[0].user_id is None
    assert matching[0].target_price == 300.0


def test_p7_27_running_migrations_twice_is_safe(p7_personal_db):
    """Verify migrate_db can be called multiple times without error or duplicating columns/tables."""
    migrate_db(p7_personal_db)
    migrate_db(p7_personal_db)
    migrate_db(p7_personal_db)

    with get_connection(p7_personal_db) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(price_tracking)")
        cols = [r["name"] for r in cursor.fetchall()]
        assert "user_id" in cols
        # Ensure 'user_id' only appears once
        assert cols.count("user_id") == 1


def test_p7_28_preferred_category_influences_ranking(p7_personal_db):
    """Verify saving a preferred category boosts compliant products in that category."""
    # Budget $2,500, broad use case Everyday Use
    # Candidate categories: Laptops (MacBook Pro $1,799), TVs (LG OLED $1,796), Audio (Sony Headphones $328)
    prefs_default = AdvisorPreferences(budget=2500.0, category="All", use_case="Everyday Use")
    res_default = get_purchase_recommendations(prefs_default, custom_path=p7_personal_db)

    # Now specify preferred category = "Laptops"
    prefs_cat = AdvisorPreferences(
        budget=2500.0,
        category="All",
        use_case="Everyday Use",
        preferred_categories=["Laptops"],
    )
    res_cat = get_purchase_recommendations(prefs_cat, custom_path=p7_personal_db)

    assert res_cat.best_overall is not None
    # Best overall or suitable candidates in Laptops will contain the preferred category reason
    laptop_items = [c for c in res_cat.ranked_candidates if c.product.category == "Laptops"]
    assert len(laptop_items) > 0
    assert any("Matches your saved preferred category 'Laptops'" in r for r in laptop_items[0].reasons)


def test_p7_29_preferred_brand_influences_ranking(p7_personal_db):
    """Verify user's preferred brand boosts recommendation score and adds explanation reason."""
    # Compare evaluating Sony vs Apple products when preferred_brands = ['Sony']
    prefs_brand = AdvisorPreferences(
        budget=2500.0,
        category="All",
        use_case="Everyday Use",
        preferred_brands=["Sony"],
    )
    res = get_purchase_recommendations(prefs_brand, custom_path=p7_personal_db)

    sony_candidates = [c for c in res.ranked_candidates if c.product.brand == "Sony"]
    assert len(sony_candidates) > 0
    sony_eval = sony_candidates[0]
    assert sony_eval.brand_score == 100.0
    assert any("Matches your saved preferred brand 'Sony'" in r for r in sony_eval.reasons)


def test_p7_30_hard_budget_limits_remain_strictly_enforced(p7_personal_db):
    """Verify personalization preferences NEVER bypass hard budget constraints."""
    # Preferred brand is Apple, but budget is only $500 and category is Laptops.
    # Apple MacBook Pro ($1,799) must NOT be in ranked_candidates!
    prefs = AdvisorPreferences(
        budget=500.0,
        category="Laptops",
        use_case="Everyday Use",
        preferred_brands=["Apple"],
    )
    res = get_purchase_recommendations(prefs, custom_path=p7_personal_db)

    # No laptop under $500 exists, so ranked_candidates must be empty
    assert len(res.ranked_candidates) == 0

    # MacBook Pro ($1,799) appears in alternatives with budget overrun, NOT as compliant candidate
    assert any(c.product.brand == "Apple" for c in res.closest_alternatives)
    for alt in res.closest_alternatives:
        if alt.product.brand == "Apple":
            assert alt.budget_fit is False
            assert alt.total_cost > 500.0


def test_p7_31_out_of_stock_products_remain_excluded(p7_personal_db):
    """Verify unavailable products remain excluded even if they match user preferences."""
    # Product 10 (Sony Alpha 7 IV) has lowest offer ($2,199) Out of Stock, in-stock offer is $2,298
    prefs = AdvisorPreferences(
        budget=2500.0,
        category="Cameras",
        use_case="Photography",
        preferred_brands=["Sony"],
        require_in_stock=True,
    )
    res = get_purchase_recommendations(prefs, custom_path=p7_personal_db)
    for c in res.ranked_candidates:
        assert c.is_available is True
        assert c.best_offer.is_available is True


def test_p7_32_missing_specifications_remain_unknown(p7_personal_db):
    """Verify missing specs are not invented or assumed compliant due to user preferences."""
    prefs = AdvisorPreferences(
        budget=3000.0,
        category="All",
        use_case="Programming",
        min_ram_gb=64,  # No product in catalog has 64GB RAM
        preferred_brands=["Apple", "Dell"],
    )
    res = get_purchase_recommendations(prefs, custom_path=p7_personal_db)

    # All products fail the 64GB RAM requirement
    assert len(res.ranked_candidates) == 0


def test_p7_33_users_without_preferences_retain_default_behavior(p7_personal_db):
    """Verify passing empty or default preferences produces standard Phase 5 recommendations."""
    prefs = AdvisorPreferences(budget=2000.0, category="Laptops", use_case="Programming")
    res = get_purchase_recommendations(prefs, custom_path=p7_personal_db)

    assert res.best_overall is not None
    assert "MacBook" in res.best_overall.product.title or "Dell XPS" in res.best_overall.product.title


def test_p7_34_personalized_explanations_match_actual_recommendation_data(p7_personal_db):
    """Verify explanations for preferred category, brand, and budget only appear when actually true."""
    prefs = AdvisorPreferences(
        budget=2000.0,
        category="Audio",
        use_case="Studying",
        preferred_brands=["Sony"],
        preferred_categories=["Audio"],
        user_saved_min_budget=200.0,
        user_saved_max_budget=400.0,
    )
    res = get_purchase_recommendations(prefs, custom_path=p7_personal_db)

    assert res.best_overall is not None
    reasons = res.best_overall.reasons

    # Must contain genuine matched reasons
    assert any("preferred brand 'Sony'" in r for r in reasons)
    assert any("preferred category 'Audio'" in r for r in reasons)
    assert any("Within your saved budget range" in r for r in reasons)
