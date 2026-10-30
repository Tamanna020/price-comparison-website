"""Personal Wishlist Service for PriceWise AI (Phase 7).

Provides:
- Adding canonical products to a user's persistent wishlist
- Removing items with user authorization checks
- Preventing duplicate wishlist entries per user
- Querying wishlist with joined catalog metadata, live lowest pricing, and tracking status
- Updating personal notes on saved items
"""

from datetime import datetime, timezone
from typing import Optional

from src.database.connection import get_connection, migrate_db
from src.database.models import WishlistItem


def add_to_wishlist(
    user_id: int,
    product_id: int,
    note: Optional[str] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str, Optional[int]]:
    """
    Add a product to the specified user's wishlist.
    
    Validations:
    - user_id and product_id must be valid
    - Product must exist in catalog
    - Prevents duplicate wishlist entries for the same user
    
    Returns:
        (success: bool, message: str, wishlist_id: Optional[int])
    """
    if not user_id:
        return False, "User identification is required to save items to wishlist.", None
    if not product_id:
        return False, "Product selection is required.", None

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # 1. Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            return False, f"User account #{user_id} does not exist.", None

        # 2. Verify product exists
        cursor.execute("SELECT id, title FROM products WHERE id = ?", (product_id,))
        prod = cursor.fetchone()
        if not prod:
            return False, f"Product #{product_id} does not exist in the catalog.", None

        prod_title = str(prod["title"])

        # 3. Check for existing wishlist entry
        cursor.execute(
            "SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        existing = cursor.fetchone()
        if existing:
            return False, f"'{prod_title}' is already in your wishlist.", existing["id"]

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        clean_note = note.strip() if note else None

        cursor.execute(
            """
            INSERT INTO wishlist (user_id, product_id, created_at, note)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, product_id, now_str, clean_note),
        )
        new_id = cursor.lastrowid

    return True, f"Added '{prod_title}' to your wishlist.", new_id


def remove_from_wishlist(
    wishlist_id: int,
    user_id: int,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Remove an item from the wishlist with user ownership verification.
    """
    if not wishlist_id or not user_id:
        return False, "Invalid wishlist item or user credentials."

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # Check item exists and verify ownership
        cursor.execute("SELECT id, user_id FROM wishlist WHERE id = ?", (wishlist_id,))
        row = cursor.fetchone()
        if not row:
            return False, f"Wishlist item #{wishlist_id} not found."

        if row["user_id"] != user_id:
            return False, "Access denied: you cannot delete another user's wishlist item."

        cursor.execute("DELETE FROM wishlist WHERE id = ? AND user_id = ?", (wishlist_id, user_id))

    return True, "Item removed from your wishlist."


def remove_product_from_wishlist(
    user_id: int,
    product_id: int,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Remove a product from user's wishlist by product_id."""
    if not user_id or not product_id:
        return False, "Invalid product or user identification."

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM wishlist WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        if cursor.rowcount == 0:
            return False, "Product was not found in your wishlist."

    return True, "Product removed from your wishlist."


def get_user_wishlist(
    user_id: int,
    custom_path: Optional[str] = None,
) -> list[WishlistItem]:
    """
    Retrieve all wishlist items for a given user, enriched with catalog details,
    lowest available price, and current price-tracking status.
    """
    if not user_id:
        return []

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                w.id as wishlist_id,
                w.user_id,
                w.product_id,
                w.created_at,
                w.note,
                p.title as product_title,
                p.brand as product_brand,
                p.category as product_category,
                p.sku as product_sku,
                p.image_url as product_image_url
            FROM wishlist w
            JOIN products p ON w.product_id = p.id
            WHERE w.user_id = ?
            ORDER BY w.created_at DESC, w.id DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()

        items: list[WishlistItem] = []
        for r in rows:
            pid = r["product_id"]

            # Query lowest available offer
            cursor.execute(
                """
                SELECT o.current_price, s.name as store_name, o.availability
                FROM offers o
                JOIN stores s ON o.store_id = s.id
                WHERE o.product_id = ? AND o.current_price > 0
                ORDER BY (
                    CASE WHEN LOWER(o.availability) IN ('out of stock', 'unavailable', 'discontinued') THEN 1 ELSE 0 END
                ) ASC, o.current_price ASC
                LIMIT 1
                """,
                (pid,),
            )
            off = cursor.fetchone()

            if off:
                avail_str = str(off["availability"] or "").strip().lower()
                is_avail = avail_str not in ("out of stock", "unavailable", "discontinued")
                lowest_price = float(off["current_price"])
                store_name = str(off["store_name"])
            else:
                is_avail = False
                lowest_price = None
                store_name = None

            # Check if this user is currently tracking this product
            cursor.execute(
                "SELECT id, target_price FROM price_tracking WHERE user_id = ? AND product_id = ?",
                (user_id, pid),
            )
            trk = cursor.fetchone()
            is_tracked = trk is not None
            tracked_target = float(trk["target_price"]) if trk else None

            items.append(
                WishlistItem(
                    id=r["wishlist_id"],
                    user_id=r["user_id"],
                    product_id=pid,
                    created_at=str(r["created_at"]),
                    note=str(r["note"]) if r["note"] else None,
                    product_title=str(r["product_title"]),
                    product_brand=str(r["product_brand"]),
                    product_category=str(r["product_category"]),
                    product_sku=str(r["product_sku"]),
                    product_image_url=str(r["product_image_url"]),
                    current_lowest_price=lowest_price,
                    current_lowest_store=store_name,
                    is_available=is_avail,
                    is_tracked=is_tracked,
                    tracked_target_price=tracked_target,
                )
            )

        return items


def is_in_wishlist(
    user_id: int,
    product_id: int,
    custom_path: Optional[str] = None,
) -> bool:
    """Check if a specific product is in the user's wishlist."""
    if not user_id or not product_id:
        return False

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        return cursor.fetchone() is not None


def update_wishlist_note(
    wishlist_id: int,
    user_id: int,
    note: Optional[str],
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Update personal shopping note on a wishlist item with authorization check."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id FROM wishlist WHERE id = ?", (wishlist_id,))
        row = cursor.fetchone()
        if not row:
            return False, f"Wishlist item #{wishlist_id} not found."
        if row["user_id"] != user_id:
            return False, "Access denied: you cannot edit another user's wishlist item."

        clean_note = note.strip() if note else None
        cursor.execute(
            "UPDATE wishlist SET note = ? WHERE id = ? AND user_id = ?",
            (clean_note, wishlist_id, user_id),
        )

    return True, "Wishlist note updated."


def get_wishlist_count(
    user_id: int,
    custom_path: Optional[str] = None,
) -> int:
    """Return total count of saved items in the user's wishlist."""
    if not user_id:
        return 0

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM wishlist WHERE user_id = ?", (user_id,))
        return cursor.fetchone()[0]

