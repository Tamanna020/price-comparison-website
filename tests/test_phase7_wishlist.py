"""Tests for User Wishlist functionality (Phase 7 - Step 10)."""

import os
import tempfile
import pytest

from src.database.connection import get_connection
from src.database.seed import seed_database
from src.services.auth_service import register_user
from src.services.price_tracking_service import add_tracked_product
from src.services.wishlist_service import (
    add_to_wishlist,
    get_user_wishlist,
    remove_from_wishlist,
    remove_product_from_wishlist,
    is_in_wishlist,
    update_wishlist_note,
    get_wishlist_count,
)


@pytest.fixture
def p7_wishlist_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_p7_09_add_product_to_wishlist(p7_wishlist_db):
    """Verify authenticated user can add a catalog product to their personal wishlist."""
    _, _, user = register_user("wish1@example.com", "secret123", "User 1", custom_path=p7_wishlist_db)

    # Product 1: MacBook Pro 14"
    success, msg, wish_id = add_to_wishlist(
        user_id=user.id,
        product_id=1,
        note="Saving for holiday bonus",
        custom_path=p7_wishlist_db,
    )
    assert success is True
    assert wish_id is not None
    assert "added" in msg.lower()

    # Check existence
    assert is_in_wishlist(user.id, 1, custom_path=p7_wishlist_db) is True
    assert get_wishlist_count(user.id, custom_path=p7_wishlist_db) == 1


def test_p7_10_retrieve_user_wishlist_with_pricing_and_tracking(p7_wishlist_db):
    """Verify retrieving wishlist includes current price, store, and tracking status."""
    _, _, user = register_user("wish2@example.com", "secret123", "User 2", custom_path=p7_wishlist_db)

    # Add product 1 and product 2
    add_to_wishlist(user.id, 1, note="MacBook note", custom_path=p7_wishlist_db)
    add_to_wishlist(user.id, 2, note="Headphones note", custom_path=p7_wishlist_db)

    # Start tracking product 1 at $1,750 for this user
    add_tracked_product(product_id=1, target_price=1750.0, user_id=user.id, custom_path=p7_wishlist_db)

    items = get_user_wishlist(user.id, custom_path=p7_wishlist_db)
    assert len(items) == 2

    # Map by product_id
    item_map = {item.product_id: item for item in items}

    # Item 1: MacBook Pro (tracked by user)
    m1 = item_map[1]
    assert "MacBook" in m1.product_title
    assert m1.current_lowest_price is not None
    assert m1.current_lowest_price > 0
    assert m1.is_available is True
    assert m1.is_tracked is True
    assert m1.tracked_target_price == 1750.0
    assert m1.note == "MacBook note"

    # Item 2: Not tracked by user
    m2 = item_map[2]
    assert m2.is_tracked is False
    assert m2.tracked_target_price is None


def test_p7_11_remove_wishlist_item(p7_wishlist_db):
    """Verify user can remove an item from their wishlist."""
    _, _, user = register_user("wish3@example.com", "secret123", "User 3", custom_path=p7_wishlist_db)
    _, _, wish_id = add_to_wishlist(user.id, 3, custom_path=p7_wishlist_db)

    assert get_wishlist_count(user.id, custom_path=p7_wishlist_db) == 1

    rem_ok, rem_msg = remove_from_wishlist(wish_id, user_id=user.id, custom_path=p7_wishlist_db)
    assert rem_ok is True
    assert "removed" in rem_msg.lower()
    assert get_wishlist_count(user.id, custom_path=p7_wishlist_db) == 0
    assert is_in_wishlist(user.id, 3, custom_path=p7_wishlist_db) is False


def test_p7_12_prevent_duplicate_entries(p7_wishlist_db):
    """Verify the same product cannot be added twice to a single user's wishlist."""
    _, _, user = register_user("wish4@example.com", "secret123", "User 4", custom_path=p7_wishlist_db)

    ok1, _, id1 = add_to_wishlist(user.id, 4, custom_path=p7_wishlist_db)
    assert ok1 is True

    # Attempt duplicate
    ok2, msg2, id2 = add_to_wishlist(user.id, 4, custom_path=p7_wishlist_db)
    assert ok2 is False
    assert id2 == id1
    assert "already in your wishlist" in msg2.lower()
    assert get_wishlist_count(user.id, custom_path=p7_wishlist_db) == 1


def test_p7_13_reject_nonexistent_products(p7_wishlist_db):
    """Verify adding a non-existent product ID fails gracefully."""
    _, _, user = register_user("wish5@example.com", "secret123", "User 5", custom_path=p7_wishlist_db)

    success, msg, wish_id = add_to_wishlist(user.id, 999999, custom_path=p7_wishlist_db)
    assert success is False
    assert wish_id is None
    assert "does not exist" in msg.lower()


def test_p7_14_prevent_access_to_another_users_wishlist(p7_wishlist_db):
    """Verify User A's wishlist query does not return User B's saved items."""
    _, _, user_a = register_user("user_a@example.com", "secret123", "User A", custom_path=p7_wishlist_db)
    _, _, user_b = register_user("user_b@example.com", "secret123", "User B", custom_path=p7_wishlist_db)

    # User A saves products 1 and 2
    add_to_wishlist(user_a.id, 1, custom_path=p7_wishlist_db)
    add_to_wishlist(user_a.id, 2, custom_path=p7_wishlist_db)

    # User B saves product 3
    add_to_wishlist(user_b.id, 3, custom_path=p7_wishlist_db)

    list_a = get_user_wishlist(user_a.id, custom_path=p7_wishlist_db)
    list_b = get_user_wishlist(user_b.id, custom_path=p7_wishlist_db)

    pids_a = {item.product_id for item in list_a}
    pids_b = {item.product_id for item in list_b}

    assert pids_a == {1, 2}
    assert pids_b == {3}
    assert 3 not in pids_a
    assert 1 not in pids_b


def test_p7_15_prevent_cross_user_deletion_and_edit(p7_wishlist_db):
    """Verify User B cannot remove or edit User A's wishlist item."""
    _, _, user_a = register_user("owner@example.com", "secret123", "Owner", custom_path=p7_wishlist_db)
    _, _, user_b = register_user("attacker@example.com", "secret123", "Attacker", custom_path=p7_wishlist_db)

    _, _, wish_id = add_to_wishlist(user_a.id, 1, note="Original Note", custom_path=p7_wishlist_db)

    # 1. User B tries to update note on User A's item
    edit_ok, edit_msg = update_wishlist_note(wish_id, user_id=user_b.id, note="Hacked!", custom_path=p7_wishlist_db)
    assert edit_ok is False
    assert "access denied" in edit_msg.lower()

    # Verify note was unchanged
    items_a = get_user_wishlist(user_a.id, custom_path=p7_wishlist_db)
    assert items_a[0].note == "Original Note"

    # 2. User B tries to delete User A's item
    del_ok, del_msg = remove_from_wishlist(wish_id, user_id=user_b.id, custom_path=p7_wishlist_db)
    assert del_ok is False
    assert "access denied" in del_msg.lower()

    # Verify item is still present in User A's wishlist
    assert get_wishlist_count(user_a.id, custom_path=p7_wishlist_db) == 1

