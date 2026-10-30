"""Tests for User Shopping Preferences (Phase 7 - Step 10)."""

import os
import tempfile
import pytest

from src.database.connection import get_connection
from src.database.seed import seed_database
from src.services.auth_service import register_user
from src.services.preference_service import (
    get_user_preferences,
    save_user_preferences,
    reset_user_preferences,
    get_available_stores,
)


@pytest.fixture
def p7_pref_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_p7_16_save_preferences(p7_pref_db):
    """Verify saving complete user preferences persists correctly."""
    _, _, user = register_user("pref1@example.com", "secret123", "Pref User 1", custom_path=p7_pref_db)

    success, msg = save_user_preferences(
        user_id=user.id,
        preferred_categories=["Laptops", "Audio"],
        preferred_brands=["Apple", "Sony"],
        min_budget=500.0,
        max_budget=2000.0,
        preferred_store_id=1,
        sort_preference="lowest_price",
        priority="best_deal",
        custom_path=p7_pref_db,
    )
    assert success is True
    assert "saved successfully" in msg.lower()

    prefs = get_user_preferences(user.id, custom_path=p7_pref_db)
    assert prefs.user_id == user.id
    assert prefs.preferred_categories == ["Laptops", "Audio"]
    assert prefs.preferred_brands == ["Apple", "Sony"]
    assert prefs.min_budget == 500.0
    assert prefs.max_budget == 2000.0
    assert prefs.preferred_store_id == 1
    assert prefs.sort_preference == "lowest_price"
    assert prefs.priority == "best_deal"


def test_p7_17_retrieve_preferences(p7_pref_db):
    """Verify retrieving preferences returns structured UserPreferences object."""
    _, _, user = register_user("pref2@example.com", "secret123", "Pref User 2", custom_path=p7_pref_db)

    save_user_preferences(
        user_id=user.id,
        preferred_categories=["Smartphones"],
        preferred_brands=["Samsung"],
        min_budget=300.0,
        max_budget=1200.0,
        custom_path=p7_pref_db,
    )

    prefs = get_user_preferences(user.id, custom_path=p7_pref_db)
    assert prefs.preferred_categories == ["Smartphones"]
    assert prefs.preferred_brands == ["Samsung"]
    assert prefs.min_budget == 300.0
    assert prefs.max_budget == 1200.0
    assert prefs.sort_preference == "best_deal"  # Default
    assert prefs.priority == "balanced"  # Default


def test_p7_18_persist_preferences_across_service_instances(p7_pref_db):
    """Verify preferences remain intact across multiple calls and fresh connection instances."""
    _, _, user = register_user("pref3@example.com", "secret123", "Pref User 3", custom_path=p7_pref_db)

    save_user_preferences(
        user_id=user.id,
        preferred_categories=["Cameras"],
        preferred_brands=["Sony"],
        min_budget=1500.0,
        max_budget=3000.0,
        custom_path=p7_pref_db,
    )

    # First fetch
    p1 = get_user_preferences(user.id, custom_path=p7_pref_db)
    assert p1.min_budget == 1500.0

    # Second fetch
    p2 = get_user_preferences(user.id, custom_path=p7_pref_db)
    assert p2.min_budget == 1500.0
    assert p2.preferred_brands == ["Sony"]


def test_p7_19_validate_budget_ranges(p7_pref_db):
    """Verify budget range validations: negative rejection and max < min rejection."""
    _, _, user = register_user("pref4@example.com", "secret123", "Pref User 4", custom_path=p7_pref_db)

    # Negative min budget
    ok_neg, msg_neg = save_user_preferences(
        user_id=user.id,
        preferred_categories=[],
        preferred_brands=[],
        min_budget=-50.0,
        custom_path=p7_pref_db,
    )
    assert ok_neg is False
    assert "positive" in msg_neg.lower() or "zero" in msg_neg.lower()

    # Negative max budget
    ok_neg2, msg_neg2 = save_user_preferences(
        user_id=user.id,
        preferred_categories=[],
        preferred_brands=[],
        max_budget=-10.0,
        custom_path=p7_pref_db,
    )
    assert ok_neg2 is False

    # Max budget < Min budget
    ok_inv, msg_inv = save_user_preferences(
        user_id=user.id,
        preferred_categories=[],
        preferred_brands=[],
        min_budget=1000.0,
        max_budget=500.0,
        custom_path=p7_pref_db,
    )
    assert ok_inv is False
    assert "cannot be less than" in msg_inv.lower()


def test_p7_20_handle_empty_preferences(p7_pref_db):
    """Verify user with no saved preferences receives sensible defaults."""
    _, _, user = register_user("pref5@example.com", "secret123", "Pref User 5", custom_path=p7_pref_db)

    prefs = get_user_preferences(user.id, custom_path=p7_pref_db)
    assert prefs.user_id == user.id
    assert prefs.preferred_categories == []
    assert prefs.preferred_brands == []
    assert prefs.min_budget is None
    assert prefs.max_budget is None
    assert prefs.sort_preference == "best_deal"
    assert prefs.priority == "balanced"


def test_p7_21_reset_preferences(p7_pref_db):
    """Verify resetting preferences clears categories, brands, budgets, and restores defaults."""
    _, _, user = register_user("pref6@example.com", "secret123", "Pref User 6", custom_path=p7_pref_db)

    save_user_preferences(
        user_id=user.id,
        preferred_categories=["Laptops", "Audio"],
        preferred_brands=["Dell", "Bose"],
        min_budget=400.0,
        max_budget=1500.0,
        sort_preference="lowest_price",
        priority="lowest_price",
        custom_path=p7_pref_db,
    )

    reset_ok, reset_msg = reset_user_preferences(user.id, custom_path=p7_pref_db)
    assert reset_ok is True
    assert "defaults" in reset_msg.lower()

    cleared = get_user_preferences(user.id, custom_path=p7_pref_db)
    assert cleared.preferred_categories == []
    assert cleared.preferred_brands == []
    assert cleared.min_budget is None
    assert cleared.max_budget is None
    assert cleared.sort_preference == "best_deal"
    assert cleared.priority == "balanced"


def test_p7_22_get_available_stores(p7_pref_db):
    """Verify get_available_stores retrieves stores sorted by name and handles empty database gracefully."""
    stores = get_available_stores(custom_path=p7_pref_db)
    assert len(stores) > 0
    assert all("id" in s and "name" in s and "domain" in s for s in stores)
    # Check alphabetical ordering by name
    names = [s["name"] for s in stores]
    assert names == sorted(names)

    # Empty temp db test
    fd, empty_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        empty_stores = get_available_stores(custom_path=empty_path)
        assert empty_stores == []
    finally:
        if os.path.exists(empty_path):
            os.remove(empty_path)


