"""User Shopping Preferences Service for PriceWise AI (Phase 7).

Provides:
- Retrieval of persistent shopping preferences per user
- Validation of budget ranges, store selection, categories, and brands
- Updating preferences with upsert semantics
- Resetting preferences to application defaults
"""

from datetime import datetime, timezone
import json
from typing import Optional

from src.database.connection import get_connection, migrate_db
from src.database.models import UserPreferences


DEFAULT_SORT_PREFERENCE = "best_deal"
DEFAULT_PRIORITY = "balanced"
VALID_PRIORITIES = ("lowest_price", "best_deal", "balanced")
VALID_SORTS = (
    "best_deal",
    "lowest_price",
    "highest_price",
    "name",
    "featured",
    "price_asc",
    "price_desc",
    "title_asc",
    "title_desc",
    "name_asc",
    "savings_desc",
)

__all__ = [
    "DEFAULT_SORT_PREFERENCE",
    "DEFAULT_PRIORITY",
    "VALID_PRIORITIES",
    "VALID_SORTS",
    "get_user_preferences",
    "save_user_preferences",
    "reset_user_preferences",
    "get_available_stores",
]


def get_user_preferences(
    user_id: int,
    custom_path: Optional[str] = None,
) -> UserPreferences:
    """
    Retrieve saved shopping preferences for the specified user.
    Falls back to sensible application defaults if no record exists.
    """
    if not user_id:
        return UserPreferences(user_id=0)

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                p.user_id,
                p.preferred_categories,
                p.preferred_brands,
                p.min_budget,
                p.max_budget,
                p.preferred_store_id,
                p.sort_preference,
                p.priority,
                p.updated_at,
                s.name as store_name
            FROM user_preferences p
            LEFT JOIN stores s ON p.preferred_store_id = s.id
            WHERE p.user_id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()

        if not row:
            return UserPreferences(user_id=user_id)

        try:
            categories = json.loads(row["preferred_categories"] or "[]")
        except Exception:
            categories = []

        try:
            brands = json.loads(row["preferred_brands"] or "[]")
        except Exception:
            brands = []

        return UserPreferences(
            user_id=user_id,
            preferred_categories=categories if isinstance(categories, list) else [],
            preferred_brands=brands if isinstance(brands, list) else [],
            min_budget=float(row["min_budget"]) if row["min_budget"] is not None else None,
            max_budget=float(row["max_budget"]) if row["max_budget"] is not None else None,
            preferred_store_id=int(row["preferred_store_id"]) if row["preferred_store_id"] is not None else None,
            preferred_store_name=str(row["store_name"]) if row["store_name"] else None,
            sort_preference=str(row["sort_preference"] or DEFAULT_SORT_PREFERENCE),
            priority=str(row["priority"] or DEFAULT_PRIORITY),
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
        )


def save_user_preferences(
    user_id: int,
    preferred_categories: Optional[list[str]] = None,
    preferred_brands: Optional[list[str]] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    preferred_store_id: Optional[int] = None,
    sort_preference: str = DEFAULT_SORT_PREFERENCE,
    priority: str = DEFAULT_PRIORITY,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Save or update shopping preferences for a user.
    
    Validates:
    - min_budget must be >= 0 when provided
    - max_budget must be >= 0 when provided
    - max_budget >= min_budget when both are provided
    - valid sort_preference and priority values
    """
    if not user_id:
        return False, "User identification is required to save preferences."

    # Validate budgets
    min_b = None
    if min_budget is not None and min_budget != "":
        try:
            min_b = float(min_budget)
            if min_b < 0:
                return False, "Minimum budget must be a positive number or zero."
        except (ValueError, TypeError):
            return False, "Minimum budget must be a valid number."

    max_b = None
    if max_budget is not None and max_budget != "":
        try:
            max_b = float(max_budget)
            if max_b < 0:
                return False, "Maximum budget must be a positive number or zero."
        except (ValueError, TypeError):
            return False, "Maximum budget must be a valid number."

    if min_b is not None and max_b is not None and max_b < min_b:
        return False, f"Maximum budget (${max_b:,.2f}) cannot be less than minimum budget (${min_b:,.2f})."

    # Validate priority & sort
    if priority not in VALID_PRIORITIES:
        priority = DEFAULT_PRIORITY

    if sort_preference not in VALID_SORTS:
        sort_preference = DEFAULT_SORT_PREFERENCE

    # Sanitize categories and brands
    clean_cats = [c.strip() for c in (preferred_categories or []) if c and c.strip()]
    clean_brands = [b.strip() for b in (preferred_brands or []) if b and b.strip()]

    cats_json = json.dumps(clean_cats)
    brands_json = json.dumps(clean_brands)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # Validate preferred store exists if provided
        if preferred_store_id is not None:
            cursor.execute("SELECT id FROM stores WHERE id = ?", (preferred_store_id,))
            if not cursor.fetchone():
                preferred_store_id = None

        cursor.execute(
            """
            INSERT INTO user_preferences (
                user_id, preferred_categories, preferred_brands,
                min_budget, max_budget, preferred_store_id,
                sort_preference, priority, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                preferred_categories = excluded.preferred_categories,
                preferred_brands = excluded.preferred_brands,
                min_budget = excluded.min_budget,
                max_budget = excluded.max_budget,
                preferred_store_id = excluded.preferred_store_id,
                sort_preference = excluded.sort_preference,
                priority = excluded.priority,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                cats_json,
                brands_json,
                min_b,
                max_b,
                preferred_store_id,
                sort_preference,
                priority,
                now_str,
            ),
        )

    return True, "Shopping preferences saved successfully."


def reset_user_preferences(
    user_id: int,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Reset user's preferences to application defaults."""
    if not user_id:
        return False, "User identification is required."

    migrate_db(custom_path)

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_preferences (
                user_id, preferred_categories, preferred_brands,
                min_budget, max_budget, preferred_store_id,
                sort_preference, priority, updated_at
            ) VALUES (?, '[]', '[]', NULL, NULL, NULL, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                preferred_categories = '[]',
                preferred_brands = '[]',
                min_budget = NULL,
                max_budget = NULL,
                preferred_store_id = NULL,
                sort_preference = excluded.sort_preference,
                priority = excluded.priority,
                updated_at = excluded.updated_at
            """,
            (user_id, DEFAULT_SORT_PREFERENCE, DEFAULT_PRIORITY, now_str),
        )

    return True, "Preferences reset to defaults."


def get_available_stores(custom_path: Optional[str] = None) -> list[dict]:
    """Retrieve all available stores from the database for preference selection."""
    migrate_db(custom_path)
    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stores'")
        if not cursor.fetchone():
            return []
        cursor.execute("SELECT id, name, domain FROM stores ORDER BY name ASC")
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "domain": r["domain"] if "domain" in r.keys() and r["domain"] else "",
            }
            for r in rows
        ]


