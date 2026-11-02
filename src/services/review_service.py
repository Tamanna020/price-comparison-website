"""Review and Intelligence Hub service for PriceWise AI Beauty (Phase 4).
Handles:
- Product review storage, retrieval, filtering (by platform, rating, skin type) and sorting
- Cross-platform rating comparisons (Nykaa, Tira, Purplle, Amazon India, Myntra)
- True weighted rating calculation: Sum(Rating_i * Count_i) / Sum(Count_i)
- Honest handling of unavailable platform data (never coerced to 0.0)
- Duplicate review prevention via external_review_id
- Structured beauty product usage guides with patch-test and sun-safety protocols
"""

import json
from datetime import datetime, timezone
from typing import Optional, Any

from src.database.connection import get_connection, migrate_db
from src.database.models import (
    ProductReview,
    PlatformRatingSummary,
    WeightedReviewScore,
    ProductUsageGuide,
)

ALL_BEAUTY_PLATFORMS = ("Nykaa", "Tira", "Purplle", "Amazon India", "Myntra")


def add_product_review(
    product_id: int,
    platform: str,
    reviewer_name: str,
    rating: float,
    comment: str,
    title: Optional[str] = None,
    rating_scale: float = 5.0,
    review_date: Optional[str] = None,
    verified_buyer: bool = False,
    skin_type: Optional[str] = None,
    source_url: Optional[str] = None,
    data_status: str = "demo",
    external_review_id: Optional[str] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str, Optional[int]]:
    """
    Add a new product review with validation and duplicate prevention.
    
    Validation:
    - rating must be between 0 and rating_scale.
    - external_review_id prevents duplicate imports.
    """
    if rating is None or rating < 0:
        return False, "Rating must be a non-negative number.", None
    if rating_scale <= 0:
        return False, "Rating scale must be greater than zero.", None
    if rating > rating_scale:
        return False, f"Rating ({rating}) exceeds maximum scale ({rating_scale}).", None
    if not comment or not comment.strip():
        return False, "Review comment cannot be empty.", None

    migrate_db(custom_path)

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    rev_date = review_date or now_str[:10]

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # Check product exists
        cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
        if not cursor.fetchone():
            return False, f"Product #{product_id} does not exist.", None

        # Check duplicate external_review_id
        if external_review_id:
            cursor.execute(
                "SELECT id FROM product_reviews WHERE external_review_id = ?",
                (external_review_id,),
            )
            existing = cursor.fetchone()
            if existing:
                return False, f"Review with external ID '{external_review_id}' already exists.", existing["id"]

        cursor.execute(
            """
            INSERT INTO product_reviews (
                product_id, platform, reviewer_name, rating, rating_scale,
                title, comment, review_date, verified_buyer, skin_type,
                source_url, data_status, external_review_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                platform.strip(),
                reviewer_name.strip(),
                float(rating),
                float(rating_scale),
                title.strip() if title else None,
                comment.strip(),
                rev_date,
                1 if verified_buyer else 0,
                skin_type.strip() if skin_type else None,
                source_url.strip() if source_url else None,
                data_status,
                external_review_id.strip() if external_review_id else None,
                now_str,
            ),
        )
        review_id = cursor.lastrowid

    return True, "Review added successfully.", review_id


def get_product_reviews(
    product_id: int,
    platform: Optional[str] = None,
    min_rating: Optional[float] = None,
    skin_type: Optional[str] = None,
    sort_by: str = "recent",
    custom_path: Optional[str] = None,
) -> list[ProductReview]:
    """
    Retrieve and filter reviews for a product.
    
    Supported sort_by options:
    - 'recent' (default): by review_date DESC, id DESC
    - 'highest_rated': by normalized rating DESC, id DESC
    - 'lowest_rated': by normalized rating ASC, id DESC
    """
    migrate_db(custom_path)

    sql = """
        SELECT 
            id, product_id, platform, reviewer_name, rating, rating_scale,
            title, comment, review_date, verified_buyer, skin_type,
            source_url, data_status, external_review_id, created_at
        FROM product_reviews
        WHERE product_id = ?
    """
    params: list[Any] = [product_id]

    if platform and platform.strip() and platform.lower() != "all":
        sql += " AND LOWER(platform) LIKE ?"
        params.append(f"%{platform.strip().lower()}%")

    if min_rating is not None:
        sql += " AND (rating / rating_scale * 5.0) >= ?"
        params.append(float(min_rating))

    if skin_type and skin_type.strip() and skin_type.lower() != "all":
        sql += " AND skin_type IS NOT NULL AND LOWER(skin_type) LIKE ?"
        params.append(f"%{skin_type.strip().lower()}%")

    # Sorting
    if sort_by == "highest_rated":
        sql += " ORDER BY (rating / rating_scale) DESC, id DESC"
    elif sort_by == "lowest_rated":
        sql += " ORDER BY (rating / rating_scale) ASC, id DESC"
    else:
        sql += " ORDER BY review_date DESC, id DESC"

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    reviews: list[ProductReview] = []
    for r in rows:
        reviews.append(
            ProductReview(
                id=r["id"],
                product_id=r["product_id"],
                platform=r["platform"],
                reviewer_name=r["reviewer_name"],
                rating=float(r["rating"]),
                rating_scale=float(r["rating_scale"] or 5.0),
                title=r["title"],
                comment=r["comment"],
                review_date=r["review_date"],
                verified_buyer=bool(r["verified_buyer"]),
                skin_type=r["skin_type"],
                source_url=r["source_url"],
                data_status=r["data_status"] or "demo",
                external_review_id=r["external_review_id"],
                created_at=str(r["created_at"]) if r["created_at"] else None,
            )
        )
    return reviews


def record_platform_rating(
    product_id: int,
    platform: str,
    average_rating: Optional[float],
    review_count: Optional[int],
    rating_scale: float = 5.0,
    data_source: str = "Retailer Feed (Demo)",
    product_url: Optional[str] = None,
    last_verified: Optional[str] = None,
    custom_path: Optional[str] = None,
) -> bool:
    """Store or update a platform rating aggregate for a product."""
    migrate_db(custom_path)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    ver_str = last_verified or now_str[:10]

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO product_platform_ratings (
                product_id, platform, average_rating, review_count,
                rating_scale, data_source, product_url, last_verified, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_id, platform) DO UPDATE SET
                average_rating = excluded.average_rating,
                review_count = excluded.review_count,
                rating_scale = excluded.rating_scale,
                data_source = excluded.data_source,
                product_url = excluded.product_url,
                last_verified = excluded.last_verified
            """,
            (
                product_id,
                platform.strip(),
                float(average_rating) if average_rating is not None else None,
                int(review_count) if review_count is not None else None,
                float(rating_scale),
                data_source,
                product_url.strip() if product_url else None,
                ver_str,
                now_str,
            ),
        )
    return True


def get_platform_rating_breakdown(
    product_id: int,
    custom_path: Optional[str] = None,
) -> list[PlatformRatingSummary]:
    """
    Retrieve platform-by-platform rating aggregates for a product.
    Includes supported platforms, marking missing ones as unavailable
    without assuming 0.0 rating or fabricated review counts.
    """
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT platform, average_rating, review_count, rating_scale, data_source, product_url, last_verified
            FROM product_platform_ratings
            WHERE product_id = ?
            """,
            (product_id,),
        )
        stored_rows = {r["platform"].lower(): r for r in cursor.fetchall()}

    summaries: list[PlatformRatingSummary] = []
    for plat in ALL_BEAUTY_PLATFORMS:
        plat_lower = plat.lower()
        if plat_lower in stored_rows:
            r = stored_rows[plat_lower]
            avg = float(r["average_rating"]) if r["average_rating"] is not None else None
            cnt = int(r["review_count"]) if r["review_count"] is not None else None
            summaries.append(
                PlatformRatingSummary(
                    platform=plat,
                    average_rating=avg,
                    review_count=cnt,
                    rating_scale=float(r["rating_scale"] or 5.0),
                    data_source=r["data_source"] or "Retailer Feed (Demo)",
                    product_url=r["product_url"],
                    last_verified=r["last_verified"],
                    is_available=(avg is not None and cnt is not None),
                )
            )
        else:
            # Platform is unlinked or has no verified feed for this product
            summaries.append(
                PlatformRatingSummary(
                    platform=plat,
                    average_rating=None,
                    review_count=None,
                    rating_scale=5.0,
                    data_source="Data Unavailable",
                    product_url=None,
                    last_verified=None,
                    is_available=False,
                )
            )

    return summaries


def calculate_weighted_review_score(
    product_id: int,
    custom_path: Optional[str] = None,
    platform_breakdown: Optional[list[PlatformRatingSummary]] = None,
) -> WeightedReviewScore:
    """
    Calculate statistically valid cross-platform weighted rating:
    
    Formula:
        Weighted Rating = Sum(Rating_i * Count_i) / Sum(Count_i)
    
    Invariants:
    - Never averages averages directly (avoids distortion when review volumes differ).
    - Excludes unavailable or unlinked platforms (never treats missing as 0.0).
    - Normalizes differing rating scales to a standard 5.0 scale before weighting.
    """
    breakdown = platform_breakdown or get_platform_rating_breakdown(product_id, custom_path=custom_path)

    valid_platforms = [
        p for p in breakdown
        if p.is_available and p.average_rating is not None and p.review_count is not None and p.review_count > 0
    ]

    if not valid_platforms:
        return WeightedReviewScore(
            product_id=product_id,
            weighted_rating=None,
            total_reviews=0,
            platforms_included=0,
            platform_breakdown=breakdown,
            calculation_method="Sum(Rating_i * Count_i) / Sum(Count_i)",
            explanation="Insufficient platform review observations available to compute weighted community score.",
            data_status="unavailable",
        )

    sum_weighted_ratings = 0.0
    total_reviews = 0

    for p in valid_platforms:
        # Scale normalization: rating / scale * 5.0
        normalized = (p.average_rating / p.rating_scale) * 5.0 if p.rating_scale > 0 else p.average_rating
        weight = p.review_count
        sum_weighted_ratings += normalized * weight
        total_reviews += weight

    weighted_score = round(sum_weighted_ratings / total_reviews, 2) if total_reviews > 0 else None

    explanation = (
        f"Weighted score computed as Sum(Normalized Rating × Review Count) / Total Reviews ({total_reviews:,}) "
        f"across {len(valid_platforms)} retailer platforms. Platforms with unlinked or unavailable data "
        f"are excluded from calculation to prevent zero-skew bias."
    )

    return WeightedReviewScore(
        product_id=product_id,
        weighted_rating=weighted_score,
        total_reviews=total_reviews,
        platforms_included=len(valid_platforms),
        platform_breakdown=breakdown,
        calculation_method="Sum(Rating_i * Count_i) / Sum(Count_i)",
        explanation=explanation,
        data_status="demo",
    )


def get_product_usage_guide(
    product_id: int,
    custom_path: Optional[str] = None,
) -> ProductUsageGuide:
    """
    Retrieve or construct a comprehensive, dermatologist-aligned beauty usage guide.
    Includes routine step, frequency, application ritual, precautions, patch test protocols,
    and ingredient breakdown.
    """
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, category, description, specs_json FROM products WHERE id = ?", (product_id,))
        prod = cursor.fetchone()

    if not prod:
        return ProductUsageGuide(
            product_id=product_id,
            routine="AM & PM",
            step_number=3,
            step_name="Treatment",
            frequency="Daily as tolerated",
            application_instructions="Apply an even amount to cleansed skin.",
            precautions="For external cosmetic use only. Discontinue if persistent irritation occurs.",
            patch_test_guideline="Perform a 24-hr patch test on inner wrist or jawline before first full application.",
            source_reference="Standard Dermatological Skincare Guidelines",
        )

    category = str(prod["category"] or "").lower()
    desc = str(prod["description"] or "")
    specs = {}
    if prod["specs_json"]:
        try:
            specs = json.loads(prod["specs_json"])
        except Exception:
            specs = {}

    routine = specs.get("Routine", "AM & PM")
    skin_type = specs.get("Skin Type", "All Skin Types")
    key_ing_raw = specs.get("Key Ingredients", "")

    # Routine step inference
    if "cleanser" in category or "face wash" in category:
        step_number = 1
        step_name = "Cleanse"
        frequency = "Twice daily (Morning & Evening)"
        instructions = "Lather a small coin-sized amount with lukewarm water. Massage over face in circular motions for 60 seconds, then rinse thoroughly and pat dry."
        precautions = "Avoid contact with direct eye area. If contact occurs, rinse immediately with clean water."
    elif "toner" in category:
        step_number = 2
        step_name = "Tone & Prep"
        frequency = "Twice daily after cleansing"
        instructions = "Pour 3-4 drops onto palms or a soft cotton pad. Press gently onto face and neck until fully absorbed before active serums."
        precautions = "Do not pull or tug delicate skin."
    elif "serum" in category:
        step_number = 3
        step_name = "Targeted Treatment"
        frequency = "Daily (Morning or Evening based on active formulation)"
        instructions = "Dispense 2-3 drops directly onto forehead and cheeks. Smooth gently and pat into skin. Allow 1-2 minutes absorption before moisturizer."
        precautions = "Check compatibility: Do not combine pure L-Ascorbic Acid and AHA/BHA in the same immediate layer unless skin is conditioned."
    elif "moisturizer" in category or "cream" in category:
        step_number = 4
        step_name = "Moisturize & Barrier Support"
        frequency = "Twice daily (Morning & Night)"
        instructions = "Warm a nickel-sized amount between fingertips. Smooth over face and neck in upward strokes to seal in hydration and strengthen barrier."
        precautions = "Store in a cool, dry place away from direct sunlight."
    elif "sunscreen" in category or "spf" in category:
        step_number = 5
        step_name = "Sun Defense (Final AM Step)"
        frequency = "Daily every morning; reapply every 2-3 hours during outdoor exposure"
        instructions = "Apply two full finger-lengths generously to face, ears, and neck 15 minutes before sun exposure. Reapply after excessive sweating or towel drying."
        precautions = "Do not rely solely on SPF for extreme midday sun. Avoid prolonged sun exposure even with sunscreen."
    else:
        # Makeup & cosmetic items
        step_number = 6
        step_name = "Enhance & Define"
        frequency = "As desired during makeup ritual"
        instructions = "Apply evenly across desired facial areas using fingertips, a blender sponge, or brush for optimal payoff."
        precautions = "Remove thoroughly before sleep using an oil-based or micellar cleanser."

    # Parse active ingredients
    actives_list: list[dict[str, str]] = []
    if key_ing_raw:
        items = [i.strip() for i in key_ing_raw.split(",") if i.strip()]
        for item in items:
            benefit = "Hydration & Barrier Conditioning"
            item_lower = item.lower()
            if "niacinamide" in item_lower:
                benefit = "Sebum control & post-blemish tone evening"
            elif "hyaluronic" in item_lower:
                benefit = "Multi-depth epidermal hydration & humectant retention"
            elif "ceramide" in item_lower:
                benefit = "Lipid barrier repair & moisture loss prevention"
            elif "salicylic" in item_lower or "bha" in item_lower:
                benefit = "Pore decongestion & gentle sebum exfoliation"
            elif "vitamin c" in item_lower or "ascorbic" in item_lower:
                benefit = "Antioxidant protection & luminous radiance"
            elif "zinc" in item_lower:
                benefit = "Anti-inflammatory calming & excess oil balance"
            elif "sunscreen" in item_lower or "uv" in item_lower or "tinosorb" in item_lower:
                benefit = "Broad-spectrum photostable UVA/UVB filters"
            elif "watermelon" in item_lower:
                benefit = "Soothing skin refreshment & natural antioxidant boost"
            actives_list.append({"name": item, "benefit": benefit})

    sun_safety = (
        "Active ingredient reminder: Formulations containing AHAs, BHAs, Retinoids, or Vitamin C increase "
        "cutaneous photosensitivity and sun sensitivity. Always follow with broad-spectrum SPF 50+ during daytime."
        if any(act in key_ing_raw.lower() for act in ["salicylic", "glycolic", "lactic", "retinol", "ascorbic", "aha", "bha"])
        else None
    )

    patch_test = (
        "Standard Dermatological Protocol: Always perform a 24-hour patch test on the inner forearm or behind the ear. "
        "Monitor for 24 hours. If burning, redness, or swelling occurs, do not proceed with facial application."
    )

    return ProductUsageGuide(
        product_id=product_id,
        routine=routine,
        step_number=step_number,
        step_name=step_name,
        frequency=frequency,
        application_instructions=instructions,
        precautions=precautions,
        patch_test_guideline=patch_test,
        sun_safety_guideline=sun_safety,
        key_actives_breakdown=actives_list,
        source_reference="Manufacturer Packaging & Indian Dermatological Society Guidelines",
    )
