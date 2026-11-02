"""Personalized Beauty Profile Service for PriceWise AI (Phase 7).

Manages user beauty profiles including:
- Skin Type: oily, dry, combination, normal, sensitive, unsure
- Skin Concerns: acne, dryness, pigmentation, uneven tone, oiliness, etc.
- Preferred Categories and Brands
- Budget in INR
- Makeup Preferences
- Ingredient Preferences and Avoidances
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
from typing import Any, Optional

from src.database.connection import get_connection, migrate_db

logger = logging.getLogger("pricewise.profile")

VALID_SKIN_TYPES = {"oily", "dry", "combination", "normal", "sensitive", "unsure"}

MEDICAL_DISCLAIMER = (
    "Cosmetic Guidance Notice: PriceWise AI beauty preferences and routine suggestions are cosmetic recommendations "
    "based on product attributes and are not medical or dermatological advice. "
    "For severe, persistent, or concerning skin conditions, please consult a certified dermatologist."
)


@dataclass
class UserProfile:
    """Personalized beauty profile for an authenticated user."""
    user_id: int
    display_name: str = ""
    preferred_name: Optional[str] = None
    skin_type: str = "unsure"
    skin_concerns: list[str] = field(default_factory=list)
    preferred_categories: list[str] = field(default_factory=list)
    preferred_brands: list[str] = field(default_factory=list)
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    makeup_preferences: list[str] = field(default_factory=list)
    ingredient_preferences: list[str] = field(default_factory=list)
    ingredient_avoidance: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    medical_disclaimer: str = MEDICAL_DISCLAIMER


def get_user_profile(user_id: int, custom_path: Optional[str] = None) -> UserProfile:
    """
    Retrieve user beauty profile.
    If no profile exists yet, initializes one using the user's registered name.
    """
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # Check existing profile
        cursor.execute(
            """
            SELECT p.user_id, p.display_name, p.preferred_name, p.skin_type,
                   p.skin_concerns, p.preferred_categories, p.preferred_brands,
                   p.min_budget, p.max_budget, p.makeup_preferences,
                   p.ingredient_preferences, p.ingredient_avoidance, p.updated_at,
                   u.display_name AS user_name
            FROM user_profiles p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()

        if row:
            return UserProfile(
                user_id=row["user_id"],
                display_name=row["display_name"] or row["user_name"] or "",
                preferred_name=row["preferred_name"],
                skin_type=row["skin_type"] or "unsure",
                skin_concerns=json.loads(row["skin_concerns"] or "[]"),
                preferred_categories=json.loads(row["preferred_categories"] or "[]"),
                preferred_brands=json.loads(row["preferred_brands"] or "[]"),
                min_budget=row["min_budget"],
                max_budget=row["max_budget"],
                makeup_preferences=json.loads(row["makeup_preferences"] or "[]"),
                ingredient_preferences=json.loads(row["ingredient_preferences"] or "[]"),
                ingredient_avoidance=json.loads(row["ingredient_avoidance"] or "[]"),
                updated_at=str(row["updated_at"] or ""),
            )

        # No profile yet: lookup user to get base name and seed initial profile
        cursor.execute("SELECT id, display_name FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        base_name = str(user_row["display_name"]) if user_row else "Beauty Shopper"

        cursor.execute(
            """
            INSERT OR IGNORE INTO user_profiles (user_id, display_name)
            VALUES (?, ?)
            """,
            (user_id, base_name),
        )

        return UserProfile(user_id=user_id, display_name=base_name)


def save_user_profile(
    user_id: int,
    display_name: Optional[str] = None,
    preferred_name: Optional[str] = None,
    skin_type: Optional[str] = None,
    skin_concerns: Optional[list[str]] = None,
    preferred_categories: Optional[list[str]] = None,
    preferred_brands: Optional[list[str]] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    makeup_preferences: Optional[list[str]] = None,
    ingredient_preferences: Optional[list[str]] = None,
    ingredient_avoidance: Optional[list[str]] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str, Optional[UserProfile]]:
    """
    Validate and save beauty profile for authenticated user.
    """
    if not user_id:
        return False, "User identification is required.", None

    # Validate skin type
    clean_skin_type = (skin_type or "unsure").strip().lower()
    if clean_skin_type not in VALID_SKIN_TYPES:
        return False, f"Invalid skin type '{skin_type}'. Must be one of: {', '.join(sorted(VALID_SKIN_TYPES))}.", None

    # Validate budgets
    if min_budget is not None and min_budget < 0:
        return False, "Minimum budget cannot be negative.", None
    if max_budget is not None and max_budget < 0:
        return False, "Maximum budget cannot be negative.", None
    if min_budget is not None and max_budget is not None and max_budget < min_budget:
        return False, "Maximum budget cannot be less than minimum budget.", None

    migrate_db(custom_path)

    concerns_json = json.dumps(skin_concerns or [])
    categories_json = json.dumps(preferred_categories or [])
    brands_json = json.dumps(preferred_brands or [])
    makeup_json = json.dumps(makeup_preferences or [])
    ing_pref_json = json.dumps(ingredient_preferences or [])
    ing_avoid_json = json.dumps(ingredient_avoidance or [])

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # Update or insert into user_profiles
        cursor.execute(
            """
            INSERT INTO user_profiles (
                user_id, display_name, preferred_name, skin_type, skin_concerns,
                preferred_categories, preferred_brands, min_budget, max_budget,
                makeup_preferences, ingredient_preferences, ingredient_avoidance,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                display_name = COALESCE(excluded.display_name, user_profiles.display_name),
                preferred_name = excluded.preferred_name,
                skin_type = excluded.skin_type,
                skin_concerns = excluded.skin_concerns,
                preferred_categories = excluded.preferred_categories,
                preferred_brands = excluded.preferred_brands,
                min_budget = excluded.min_budget,
                max_budget = excluded.max_budget,
                makeup_preferences = excluded.makeup_preferences,
                ingredient_preferences = excluded.ingredient_preferences,
                ingredient_avoidance = excluded.ingredient_avoidance,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                display_name,
                preferred_name,
                clean_skin_type,
                concerns_json,
                categories_json,
                brands_json,
                min_budget,
                max_budget,
                makeup_json,
                ing_pref_json,
                ing_avoid_json,
            ),
        )

        # Sync display name back to users table if provided
        if display_name and display_name.strip():
            cursor.execute(
                "UPDATE users SET display_name = ? WHERE id = ?",
                (display_name.strip(), user_id),
            )

    updated = get_user_profile(user_id, custom_path=custom_path)
    return True, "Beauty profile updated successfully.", updated


def reset_user_profile(user_id: int, custom_path: Optional[str] = None) -> tuple[bool, str]:
    """Reset optional profile preferences to clean baseline defaults."""
    if not user_id:
        return False, "User identification is required."

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE user_profiles SET
                preferred_name = NULL,
                skin_type = 'unsure',
                skin_concerns = '[]',
                preferred_categories = '[]',
                preferred_brands = '[]',
                min_budget = NULL,
                max_budget = NULL,
                makeup_preferences = '[]',
                ingredient_preferences = '[]',
                ingredient_avoidance = '[]',
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id,),
        )

    return True, "Beauty profile reset to defaults."
