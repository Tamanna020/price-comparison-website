"""Personalized Beauty Product Recommendations Service for PriceWise AI (Phase 7).

Matches catalog products to user beauty profiles:
- Skin Type matching (Oily -> Gel/Sebum-control; Dry -> Ceramides/Rich creams)
- Skin Concern targeting (Acne, Pigmentation, Dryness, Redness, Oiliness)
- Budget constraint filtering (in INR)
- Ingredient avoidance filtering (Fragrance, Alcohol, Parabens, etc.)
- Transparent, explainable cosmetic reasoning (Zero hallucinated clinical claims)
"""

from dataclasses import dataclass, field
import json
import logging
import re
from typing import Optional

from src.database.connection import get_connection, migrate_db
from src.services.profile_service import get_user_profile, UserProfile, MEDICAL_DISCLAIMER

logger = logging.getLogger("pricewise.recommendations")


@dataclass
class RecommendedProductItem:
    """Individual product recommendation with explainable cosmetic match reasoning."""
    product_id: int
    title: str
    brand: str
    category: str
    price: Optional[float]
    image_url: Optional[str]
    slug: str
    match_score: int  # 0 to 100
    match_reasons: list[str] = field(default_factory=list)
    key_ingredients: Optional[str] = None
    skin_type_suitability: Optional[str] = None


@dataclass
class PersonalizedRecommendationsResult:
    """Complete personalized recommendations payload for an authenticated user."""
    user_id: int
    skin_type: str
    skin_concerns: list[str]
    max_budget: Optional[float]
    products: list[RecommendedProductItem]
    has_profile: bool
    medical_disclaimer: str = MEDICAL_DISCLAIMER


CONCERN_KEYWORDS = {
    "acne": ["niacinamide", "salicylic", "bha", "tea tree", "zinc", "clarifying", "acne"],
    "pigmentation": ["vitamin c", "alpha arbutin", "brightening", "kojic", "tranexamic", "glow"],
    "dark_spots": ["vitamin c", "arbutin", "brightening", "dark spot", "radiance"],
    "dryness": ["ceramide", "hyaluronic", "squalane", "barrier", "moistur", "nourishing", "hydrat"],
    "oiliness": ["gel", "sebum", "mattifying", "lightweight", "pore", "oil-free"],
    "redness": ["cica", "centella", "soothing", "calming", "aloe", "panthenol"],
    "fine_lines": ["retinol", "peptide", "collagen", "firming", "anti-aging"],
    "dullness": ["vitamin c", "exfoliat", "lactic", "radiance", "glow", "aha"],
}

SKIN_TYPE_KEYWORDS = {
    "oily": ["gel", "lightweight", "matte", "water-based", "fluid", "non-comedogenic", "oily"],
    "dry": ["cream", "rich", "intensive", "ceramide", "deep hydration", "dry", "nourish"],
    "combination": ["balancing", "lightweight", "fluid", "all skin types", "combination"],
    "sensitive": ["fragrance-free", "gentle", "calming", "soothing", "hypoallergenic", "sensitive"],
    "normal": ["hydrating", "all skin types", "balanced", "daily"],
}


def get_personalized_recommendations(
    user_id: int,
    limit: int = 8,
    custom_path: Optional[str] = None,
) -> PersonalizedRecommendationsResult:
    """
    Generate personalized recommendations based strictly on catalog data and user profile.
    Does not require external paid APIs.
    """
    migrate_db(custom_path)
    profile = get_user_profile(user_id, custom_path=custom_path)

    skin_type = profile.skin_type.lower()
    concerns = [c.lower() for c in profile.skin_concerns]
    max_budget = profile.max_budget
    avoid_ingredients = [a.lower() for a in profile.ingredient_avoidance]
    has_profile = skin_type != "unsure" or len(concerns) > 0 or max_budget is not None

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.id, p.title, p.brand, p.category, p.description, p.specs_json,
                   p.image_url,
                   (SELECT MIN(current_price) FROM offers WHERE product_id = p.id) AS lowest_price
            FROM products p
            """
        )
        rows = cursor.fetchall()

    scored_items: list[tuple[int, RecommendedProductItem]] = []

    for row in rows:
        p_id = row["id"]
        title = str(row["title"] or "")
        brand = str(row["brand"] or "")
        category = str(row["category"] or "")
        desc = str(row["description"] or "")
        slug = re.sub(r"[^a-z0-9]+", "-", f"{brand}-{title}".lower()).strip("-") or f"product-{p_id}"
        price = row["lowest_price"]
        image = row["image_url"]

        specs = {}
        try:
            if row["specs_json"]:
                specs = json.loads(row["specs_json"])
        except Exception:
            specs = {}

        ingredients_text = str(specs.get("Key Ingredients") or "")
        skin_suitability = str(specs.get("Skin Type") or "")
        text_corpus = f"{title} {brand} {category} {desc} {ingredients_text} {skin_suitability}".lower()

        # 1. Ingredient Avoidance check (hard filter)
        if avoid_ingredients:
            if any(avoid in text_corpus for avoid in avoid_ingredients):
                continue

        # 2. Budget check (hard filter if max_budget set)
        if max_budget is not None and price is not None and price > max_budget:
            continue

        score = 40  # Baseline score for valid catalog product
        reasons: list[str] = []

        # 3. Skin Type scoring
        if skin_type in SKIN_TYPE_KEYWORDS:
            type_hits = [k for k in SKIN_TYPE_KEYWORDS[skin_type] if k in text_corpus]
            if type_hits:
                score += min(25, len(type_hits) * 8)
                reasons.append(f"Suitable for {skin_type.capitalize()} skin texture")

        # 4. Skin Concern scoring
        for concern in concerns:
            if concern in CONCERN_KEYWORDS:
                concern_hits = [k for k in CONCERN_KEYWORDS[concern] if k in text_corpus]
                if concern_hits:
                    score += min(25, len(concern_hits) * 10)
                    reasons.append(f"Targets {concern.replace('_', ' ').capitalize()} with active ingredients")

        # 5. Preferred Category match
        if profile.preferred_categories:
            if any(cat.lower() in category.lower() for cat in profile.preferred_categories):
                score += 15
                reasons.append(f"Matches your saved category: {category}")

        # 6. Preferred Brand match
        if profile.preferred_brands:
            if any(b.lower() in brand.lower() for b in profile.preferred_brands):
                score += 15
                reasons.append(f"From your preferred brand: {brand}")

        if not reasons:
            reasons.append("Curated beauty catalog essential")

        item = RecommendedProductItem(
            product_id=p_id,
            title=title,
            brand=brand,
            category=category,
            price=price,
            image_url=image,
            slug=slug,
            match_score=min(100, score),
            match_reasons=reasons[:3],
            key_ingredients=ingredients_text or None,
            skin_type_suitability=skin_suitability or None,
        )
        scored_items.append((score, item))

    # Sort descending by match score
    scored_items.sort(key=lambda t: t[0], reverse=True)
    top_products = [itm for _, itm in scored_items[:limit]]

    return PersonalizedRecommendationsResult(
        user_id=user_id,
        skin_type=profile.skin_type,
        skin_concerns=profile.skin_concerns,
        max_budget=max_budget,
        products=top_products,
        has_profile=has_profile,
    )
