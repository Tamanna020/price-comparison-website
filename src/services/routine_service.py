"""Personalized Skincare Routines Service for PriceWise AI (Phase 7).

Manages user morning and evening routines:
- Step creation, editing, deletion, and reordering
- Catalog product attachment or custom product names
- Active ingredient conflict detection (Retinol + AHA/BHA, Vit C + Retinol, SPF reminders)
- Precaution and patch-testing guidance
- Default starter routine seeding
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import re
from typing import Any, Optional

from src.database.connection import get_connection, migrate_db

logger = logging.getLogger("pricewise.routines")

ROUTINE_MEDICAL_DISCLAIMER = (
    "Cosmetic Guidance Notice: Skincare routine instructions and active ingredient precautions are cosmetic suggestions "
    "based on general dermatological principles and are not medical prescriptions. "
    "If you experience irritation, redness, or burning, rinse immediately and discontinue use."
)


@dataclass
class RoutineItem:
    """Individual step within a skincare routine."""
    id: int
    routine_id: int
    step_number: int
    step_name: str
    product_id: Optional[int] = None
    custom_product_name: Optional[str] = None
    usage_instructions: Optional[str] = None
    precautions: Optional[str] = None
    created_at: str = ""

    # Joined product catalog fields
    product_title: Optional[str] = None
    product_brand: Optional[str] = None
    product_image_url: Optional[str] = None
    product_price: Optional[float] = None
    product_slug: Optional[str] = None


@dataclass
class Routine:
    """Morning or evening skincare routine owned by a user."""
    id: int
    user_id: int
    routine_type: str  # 'morning', 'evening', 'weekly', 'custom'
    title: str
    description: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    items: list[RoutineItem] = field(default_factory=list)
    conflict_warnings: list[str] = field(default_factory=list)
    medical_disclaimer: str = ROUTINE_MEDICAL_DISCLAIMER


# Standard starter routine templates
STARTER_ROUTINES = [
    {
        "routine_type": "morning",
        "title": "Daily Barrier Defense (AM)",
        "description": "Essential morning protocol to hydrate, shield against pollution, and block UV damage.",
        "items": [
            {
                "step_number": 1,
                "step_name": "Gentle Cleanser",
                "custom_product_name": "Hydrating Gel Cleanser",
                "usage_instructions": "Massage with lukewarm water for 60 seconds; gently pat dry.",
                "precautions": "Avoid stripping foaming cleansers if skin feels tight.",
            },
            {
                "step_number": 2,
                "step_name": "Hydrating Prep Essence",
                "custom_product_name": "Hyaluronic Acid / Ceramide Essence",
                "usage_instructions": "Pat 3-4 drops directly into damp skin until fully absorbed.",
                "precautions": "Apply on damp skin to lock in maximum hydration.",
            },
            {
                "step_number": 3,
                "step_name": "Antioxidant Brightener",
                "custom_product_name": "10% Vitamin C or Niacinamide Serum",
                "usage_instructions": "Dispense 2-3 drops; press into face and neck.",
                "precautions": "Always pair with SPF 50+ when using daytime brightening actives.",
            },
            {
                "step_number": 4,
                "step_name": "Barrier Moisturizer",
                "custom_product_name": "Lightweight Ceramide Gel Cream",
                "usage_instructions": "Smooth evenly across face and neck in upward motions.",
                "precautions": "Do not skip moisturizer even if oily; dehydrated skin overproduces sebum.",
            },
            {
                "step_number": 5,
                "step_name": "Broad-Spectrum Sunscreen",
                "custom_product_name": "SPF 50+ PA++++ Fluid Sunscreen",
                "usage_instructions": "Apply two full finger lengths 15 minutes before sun exposure.",
                "precautions": "Non-negotiable daytime step. Reapply every 2-3 hours when outdoors.",
            },
        ],
    },
    {
        "routine_type": "evening",
        "title": "Cellular Recovery & Barrier Repair (PM)",
        "description": "Overnight regeneration routine to melt daily grime, stimulate cellular renewal, and rebuild lipids.",
        "items": [
            {
                "step_number": 1,
                "step_name": "Double Cleanse",
                "custom_product_name": "Cleansing Balm + Gentle Face Wash",
                "usage_instructions": "Melt sunscreen and makeup with balm; rinse with water-based wash.",
                "precautions": "Ensure cleansing balm emulsifies to milky liquid before rinsing.",
            },
            {
                "step_number": 2,
                "step_name": "Active Treatment / Retinoid",
                "custom_product_name": "Gentle Retinol or Multi-Peptide Serum",
                "usage_instructions": "Apply pea-sized amount onto completely dry skin 2-3 nights per week.",
                "precautions": "Do not combine with chemical peeling acids (AHA/BHA) in the same session.",
            },
            {
                "step_number": 3,
                "step_name": "Overnight Barrier Recovery Cream",
                "custom_product_name": "Rich Ceramide & Squalane Night Cream",
                "usage_instructions": "Press generously into face, neck, and décolletage before bed.",
                "precautions": "Buffer Retinol between moisturizer layers if you experience initial tingling.",
            },
        ],
    },
]


def detect_ingredient_conflicts(routine_type: str, items: list[Any]) -> list[dict[str, str]]:
    """
    Examine routine steps for ingredient clashes and dermatological precautions.
    Supports list of RoutineItem objects or dicts.
    """
    conflicts: list[dict[str, str]] = []
    parts: list[str] = []

    for item in items:
        if isinstance(item, dict):
            s_name = str(item.get("step_name") or "")
            c_name = str(item.get("custom_product_name") or "")
            p_title = str(item.get("product_title") or "")
            key_ings = " ".join(item.get("key_ingredients") or [])
            parts.append(f"{s_name} {c_name} {p_title} {key_ings}".lower())
        else:
            s_name = str(getattr(item, "step_name", "") or "")
            c_name = str(getattr(item, "custom_product_name", "") or "")
            p_title = str(getattr(item, "product_title", "") or "")
            key_ings = " ".join(getattr(item, "key_ingredients", []) or [])
            parts.append(f"{s_name} {c_name} {p_title} {key_ings}".lower())

    text_corpus = " ".join(parts)
    r_type_clean = routine_type.strip().lower()
    is_am = r_type_clean in ["am", "morning", "day"]

    has_retinol = any(k in text_corpus for k in ["retinol", "retinoid", "tretinoin", "granactive"])
    has_aha_bha = any(k in text_corpus for k in ["aha", "bha", "glycolic", "salicylic", "lactic", "peel"])
    has_vit_c = any(k in text_corpus for k in ["vitamin c", "ascorbic", "ascorbyl"])
    has_sunscreen = any(k in text_corpus for k in ["sunscreen", "spf", "sun protection", "sun fluid"])

    # 1. Daytime SPF rule
    if is_am and items and not has_sunscreen:
        conflicts.append({
            "conflict_type": "missing_sunscreen_am",
            "severity": "warning",
            "description": "Daytime Sun Protection Missing: Morning routines should always conclude with broad-spectrum SPF 50+.",
            "recommendation": "Add a broad-spectrum SPF 50+ sunscreen as your final morning step to protect against UV damage.",
        })

    # 2. Retinol daytime warning
    if is_am and has_retinol:
        conflicts.append({
            "conflict_type": "retinoid_daytime_use",
            "severity": "caution",
            "description": "Retinoid Photosensitivity Alert: Retinoids degrade in sunlight and increase UV sensitivity.",
            "recommendation": "Shift Retinol steps to your Evening (PM) routine.",
        })

    # 3. Retinol + Strong Acids Clash
    if has_retinol and has_aha_bha:
        conflicts.append({
            "conflict_type": "retinoid_with_aha_bha",
            "severity": "high",
            "description": "Active Ingredient Clash: Using Retinoids and Exfoliating Acids (AHA/BHA) simultaneously can cause barrier irritation.",
            "recommendation": "Consider alternating nights (Skin Cycling) rather than applying both simultaneously.",
        })

    # 4. Vitamin C + Retinol Clash
    if has_vit_c and has_retinol:
        conflicts.append({
            "conflict_type": "vitamin_c_with_retinol",
            "severity": "medium",
            "description": "Active Ingredient Clash: Vitamin C and Retinol can cause irritation when layered in the same session.",
            "recommendation": "Use Vitamin C in your morning routine and save Retinol for nighttime cellular repair.",
        })

    return conflicts


def get_user_routines(user_id: int, custom_path: Optional[str] = None) -> list[Routine]:
    """Retrieve all skincare routines owned by user, with step items and conflict checks."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # 1. Query user routines
        cursor.execute(
            """
            SELECT id, user_id, routine_type, title, description, created_at, updated_at
            FROM user_routines
            WHERE user_id = ?
            ORDER BY CASE WHEN routine_type = 'morning' THEN 1 WHEN routine_type = 'evening' THEN 2 ELSE 3 END, id ASC
            """,
            (user_id,),
        )
        routine_rows = cursor.fetchall()

        # If user has no routines, automatically seed baseline AM & PM routines
        if not routine_rows:
            return seed_default_routines_for_user(user_id, custom_path=custom_path)

        routines: list[Routine] = []
        for r_row in routine_rows:
            r_id = r_row["id"]
            # 2. Query items for this routine
            cursor.execute(
                """
                SELECT ri.id, ri.routine_id, ri.step_number, ri.step_name,
                       ri.product_id, ri.custom_product_name, ri.usage_instructions,
                       ri.precautions, ri.created_at,
                       p.title AS p_title, p.brand AS p_brand, p.image_url AS p_image,
                       (SELECT MIN(current_price) FROM offers WHERE product_id = p.id) AS p_price
                FROM user_routine_items ri
                LEFT JOIN products p ON ri.product_id = p.id
                WHERE ri.routine_id = ?
                ORDER BY ri.step_number ASC, ri.id ASC
                """,
                (r_id,),
            )
            item_rows = cursor.fetchall()

            items = []
            for row in item_rows:
                p_slug = None
                if row["p_title"]:
                    p_slug = re.sub(r"[^a-z0-9]+", "-", f"{row['p_brand']}-{row['p_title']}".lower()).strip("-") or f"product-{row['product_id']}"
                items.append(
                    RoutineItem(
                        id=row["id"],
                        routine_id=row["routine_id"],
                        step_number=row["step_number"],
                        step_name=row["step_name"],
                        product_id=row["product_id"],
                        custom_product_name=row["custom_product_name"],
                        usage_instructions=row["usage_instructions"],
                        precautions=row["precautions"],
                        created_at=str(row["created_at"] or ""),
                        product_title=row["p_title"],
                        product_brand=row["p_brand"],
                        product_image_url=row["p_image"],
                        product_price=row["p_price"],
                        product_slug=p_slug,
                    )
                )

            warnings = detect_ingredient_conflicts(str(r_row["routine_type"]), items)

            routines.append(
                Routine(
                    id=r_id,
                    user_id=r_row["user_id"],
                    routine_type=str(r_row["routine_type"]),
                    title=str(r_row["title"]),
                    description=r_row["description"],
                    created_at=str(r_row["created_at"] or ""),
                    updated_at=str(r_row["updated_at"] or ""),
                    items=items,
                    conflict_warnings=warnings,
                )
            )

        return routines


def seed_default_routines_for_user(user_id: int, custom_path: Optional[str] = None) -> list[Routine]:
    """Seed standard morning and evening starter routines for a new user account."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        for tpl in STARTER_ROUTINES:
            cursor.execute(
                """
                INSERT INTO user_routines (user_id, routine_type, title, description)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, tpl["routine_type"], tpl["title"], tpl["description"]),
            )
            routine_id = cursor.lastrowid

            for item in tpl["items"]:
                cursor.execute(
                    """
                    INSERT INTO user_routine_items (
                        routine_id, step_number, step_name, custom_product_name,
                        usage_instructions, precautions
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        routine_id,
                        item["step_number"],
                        item["step_name"],
                        item["custom_product_name"],
                        item["usage_instructions"],
                        item["precautions"],
                    ),
                )

    return get_user_routines(user_id, custom_path=custom_path)


def get_user_routine_by_id(
    user_id: int,
    routine_id: int,
    custom_path: Optional[str] = None,
) -> Optional[Routine]:
    """Retrieve single routine ensuring strict ownership verification."""
    routines = get_user_routines(user_id, custom_path=custom_path)
    for r in routines:
        if r.id == routine_id:
            return r
    return None


def create_user_routine(
    user_id: int,
    routine_type: str,
    title: str,
    description: Optional[str] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str, Optional[Routine]]:
    """Create a new custom skincare routine for user."""
    raw_type = (routine_type or "custom").strip().lower()
    clean_type = "morning" if raw_type in ("am", "morning") else "evening" if raw_type in ("pm", "evening") else raw_type
    if clean_type not in ("morning", "evening", "weekly", "custom"):
        return False, "Routine type must be morning (AM), evening (PM), weekly, or custom.", None

    clean_title = (title or "").strip()
    if not clean_title:
        return False, "Routine title cannot be empty.", None

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_routines (user_id, routine_type, title, description)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, clean_type, clean_title, description),
        )
        new_id = cursor.lastrowid

    created = get_user_routine_by_id(user_id, new_id, custom_path=custom_path)
    return True, "Routine created successfully.", created


def update_user_routine(
    user_id: int,
    routine_id: int,
    title: str,
    description: Optional[str] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str, Optional[Routine]]:
    """Update title and description of an existing routine."""
    clean_title = (title or "").strip()
    if not clean_title:
        return False, "Routine title cannot be empty.", None

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE user_routines SET title = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (clean_title, description, routine_id, user_id),
        )
        if cursor.rowcount == 0:
            return False, "Routine not found or access denied.", None

    updated = get_user_routine_by_id(user_id, routine_id, custom_path=custom_path)
    return True, "Routine updated successfully.", updated


def delete_user_routine(
    user_id: int,
    routine_id: int,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Delete a routine and all its associated items."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM user_routines WHERE id = ? AND user_id = ?",
            (routine_id, user_id),
        )
        if cursor.rowcount == 0:
            return False, "Routine not found or access denied."

    return True, "Routine deleted successfully."


def add_routine_item(
    user_id: int,
    routine_id: int,
    step_name: str,
    product_id: Optional[int] = None,
    custom_product_name: Optional[str] = None,
    usage_instructions: Optional[str] = None,
    precautions: Optional[str] = None,
    step_number: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str, Optional[RoutineItem]]:
    """Add a new step/product to an existing routine with auto-assigned step number."""
    clean_step = (step_name or "").strip()
    if not clean_step:
        return False, "Step name cannot be empty.", None

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # 1. Verify routine ownership
        cursor.execute(
            "SELECT id FROM user_routines WHERE id = ? AND user_id = ?",
            (routine_id, user_id),
        )
        if not cursor.fetchone():
            return False, "Routine not found or access denied.", None

        # 2. Determine step number if not provided
        if step_number is None:
            cursor.execute(
                "SELECT COALESCE(MAX(step_number), 0) + 1 FROM user_routine_items WHERE routine_id = ?",
                (routine_id,),
            )
            step_number = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO user_routine_items (
                routine_id, step_number, step_name, product_id,
                custom_product_name, usage_instructions, precautions
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                routine_id,
                step_number,
                clean_step,
                product_id,
                custom_product_name,
                usage_instructions,
                precautions,
            ),
        )
        new_item_id = cursor.lastrowid

        # Update routine updated_at timestamp
        cursor.execute(
            "UPDATE user_routines SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (routine_id,),
        )

    # Fetch updated routine item
    routine = get_user_routine_by_id(user_id, routine_id, custom_path=custom_path)
    if routine:
        for itm in routine.items:
            if itm.id == new_item_id:
                return True, "Routine step added successfully.", itm

    return True, "Routine step added successfully.", None


def reorder_routine_items(
    user_id: int,
    routine_id: int,
    item_ids_in_order: list[int],
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Reorder steps in a routine by updating step_number according to provided list order."""
    if not item_ids_in_order:
        return False, "Item IDs list cannot be empty."

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # Verify routine ownership
        cursor.execute(
            "SELECT id FROM user_routines WHERE id = ? AND user_id = ?",
            (routine_id, user_id),
        )
        if not cursor.fetchone():
            return False, "Routine not found or access denied."

        for idx, item_id in enumerate(item_ids_in_order, start=1):
            cursor.execute(
                "UPDATE user_routine_items SET step_number = ? WHERE id = ? AND routine_id = ?",
                (idx, item_id, routine_id),
            )

        cursor.execute(
            "UPDATE user_routines SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (routine_id,),
        )

    return True, "Routine steps reordered successfully."


def delete_routine_item(
    user_id: int,
    routine_id: int,
    item_id: int,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Remove a step from a routine and resequence remaining steps."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # Verify routine ownership
        cursor.execute(
            "SELECT id FROM user_routines WHERE id = ? AND user_id = ?",
            (routine_id, user_id),
        )
        if not cursor.fetchone():
            return False, "Routine not found or access denied."

        cursor.execute(
            "DELETE FROM user_routine_items WHERE id = ? AND routine_id = ?",
            (item_id, routine_id),
        )
        if cursor.rowcount == 0:
            return False, "Routine step not found."

        # Resequence remaining steps
        cursor.execute(
            """
            SELECT id FROM user_routine_items
            WHERE routine_id = ?
            ORDER BY step_number ASC, id ASC
            """,
            (routine_id,),
        )
        remaining = cursor.fetchall()
        for new_idx, row in enumerate(remaining, start=1):
            cursor.execute(
                "UPDATE user_routine_items SET step_number = ? WHERE id = ?",
                (new_idx, row["id"]),
            )

        cursor.execute(
            "UPDATE user_routines SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (routine_id,),
        )

    return True, "Routine step removed successfully."
