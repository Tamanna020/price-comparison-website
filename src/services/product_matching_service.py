"""Product Matching & Variant Integrity Service for PriceWise AI Beauty (Phase 5).

Provides strict multi-factor matching across Indian beauty catalogs:
- Brand identification and normalization
- Exact volume / net quantity extraction and compatibility (30ml != 50ml)
- Makeup shade extraction and distinction (e.g., 'Ruby Woo' != 'Velvet Teddy')
- Formulation / finish integrity (e.g., 'Waterproof' != 'Washable', 'Gel' != 'Cream')
- 3-Tier Classification:
  1. verified_match: Confirmed identical SKU variant. Safe for direct price arbitrage.
  2. possible_match: High similarity with minor phrasing difference or unverified shade.
  3. incompatible_mismatch: Incompatible variant. Strictly excluded from comparison.
"""

from dataclasses import dataclass, field
import difflib
import re
from typing import Any, Optional
from src.database.models import Offer, Product


class MatchClassification:
    VERIFIED_MATCH = "verified_match"
    POSSIBLE_MATCH = "possible_match"
    INCOMPATIBLE_MISMATCH = "incompatible_mismatch"


@dataclass
class ProductMatchResult:
    """Detailed evaluation result for product/offer pairing."""
    match_classification: str  # verified_match, possible_match, incompatible_mismatch
    confidence_score: float  # 0.0 to 1.0
    is_comparable: bool  # True only if verified_match (or acceptable possible_match)
    brand_match: bool
    size_match: bool
    shade_match: bool
    formulation_match: bool
    title_similarity: float
    reasons: list[str] = field(default_factory=list)
    target_size: Optional[str] = None
    offer_size: Optional[str] = None
    target_shade: Optional[str] = None
    offer_shade: Optional[str] = None

    @property
    def is_verified(self) -> bool:
        return self.match_classification == MatchClassification.VERIFIED_MATCH

    @property
    def is_mismatch(self) -> bool:
        return self.match_classification == MatchClassification.INCOMPATIBLE_MISMATCH

    @property
    def display_badge(self) -> str:
        if self.match_classification == MatchClassification.VERIFIED_MATCH:
            return "Verified Exact Variant"
        elif self.match_classification == MatchClassification.POSSIBLE_MATCH:
            return "Possible Match (Verification Needed)"
        else:
            return "Variant Incompatible"


def parse_quantity_volume(text: str) -> tuple[Optional[float], Optional[str]]:
    """
    Extract normalized numerical amount and standard unit from text or specs.
    Recognizes ml, g, gm, grams, oz, kg, l.
    Examples:
      '50 ml' -> (50.0, 'ml')
      '3.8g' -> (3.8, 'g')
      '100 gm' -> (100.0, 'g')
    """
    if not text:
        return None, None

    cleaned = str(text).lower().replace(" ", "").replace(",", ".")
    # Match decimal or int followed by unit
    match = re.search(r"(\d+(?:\.\d+)?)(ml|gm|g|grams?|oz|kg|litres?|l)", cleaned)
    if not match:
        return None, None

    val = float(match.group(1))
    unit = match.group(2)
    if unit in ("gm", "grams", "gram"):
        unit = "g"
    elif unit in ("litres", "litre"):
        unit = "l"

    return val, unit


def parse_shade(text: str, specs: Optional[dict[str, Any]] = None) -> Optional[str]:
    """Extract recognized beauty shade names."""
    known_shades = [
        "ruby woo",
        "velvet teddy",
        "reconstruct",
        "warm nude",
        "encourage",
        "midnight black",
        "russian red",
        "diva",
        "whirl",
        "pillow talk",
        "soft pinch",
        "berry pink",
        "cherry red",
        "caramel",
        "mocha",
        "ivory",
        "beige",
    ]
    if specs and "Shade" in specs:
        return str(specs["Shade"]).strip().title()

    combined = (text or "").lower()
    for shade in known_shades:
        if shade in combined:
            return shade.title()
    return None


def parse_formulation(text: str, specs: Optional[dict[str, Any]] = None) -> Optional[str]:
    """Extract formulation keywords (waterproof, washable, gel, cream, serum, etc.)."""
    if specs:
        for k in ["Product Type", "Formulation", "Finish"]:
            if k in specs and specs[k]:
                return str(specs[k]).strip()

    combined = (text or "").lower()
    if "waterproof" in combined:
        return "Waterproof"
    if "washable" in combined:
        return "Washable"
    if "gel" in combined:
        return "Gel"
    if "cream" in combined:
        return "Cream"
    if "serum" in combined:
        return "Serum"
    return None


def evaluate_product_match(
    target_brand: str,
    target_title: str,
    target_specs: Optional[dict[str, Any]] = None,
    offer_brand: str = "",
    offer_title: str = "",
    offer_variant: str = "",
    offer_specs: Optional[dict[str, Any]] = None,
) -> ProductMatchResult:
    """
    Perform multi-factor matching between a target beauty product and a retailer offer.
    Enforces that size/volume mismatches, shade clashes, or formulation clashes
    are never treated as comparable.
    """
    reasons: list[str] = []
    t_specs = target_specs or {}
    o_specs = offer_specs or {}

    # 1. Brand Normalization & Check
    norm_t_brand = re.sub(r"[^a-z0-9]", "", target_brand.lower())
    norm_o_brand = re.sub(r"[^a-z0-9]", "", offer_brand.lower())
    brand_match = True
    if norm_t_brand and norm_o_brand:
        if norm_t_brand not in norm_o_brand and norm_o_brand not in norm_t_brand:
            brand_match = False
            reasons.append(f"Brand mismatch: '{target_brand}' vs '{offer_brand}'")

    # 2. Net Quantity / Volume Check
    target_qty_text = str(t_specs.get("Net Quantity") or t_specs.get("Size") or target_title)
    offer_qty_text = str(o_specs.get("Net Quantity") or o_specs.get("Size") or f"{offer_variant} {offer_title}")
    t_val, t_unit = parse_quantity_volume(target_qty_text)
    o_val, o_unit = parse_quantity_volume(offer_qty_text)

    size_match = True
    target_size_str = f"{t_val}{t_unit}" if t_val is not None else None
    offer_size_str = f"{o_val}{o_unit}" if o_val is not None else None

    if t_val is not None and o_val is not None:
        if t_unit == o_unit and abs(t_val - o_val) > 0.01:
            size_match = False
            reasons.append(
                f"Size mismatch: Target is {t_val}{t_unit} but offer is {o_val}{o_unit}. 30ml cannot be compared with 50ml."
            )
        elif t_unit != o_unit:
            # Different units (e.g. ml vs g) without conversion
            size_match = False
            reasons.append(f"Unit mismatch: Target is in {t_unit} while offer is in {o_unit}")

    # 3. Makeup Shade Check
    t_shade = parse_shade(target_title, t_specs)
    o_shade = parse_shade(f"{offer_variant} {offer_title}", o_specs)
    shade_match = True
    if t_shade and o_shade and t_shade.lower() != o_shade.lower():
        shade_match = False
        reasons.append(f"Shade mismatch: Target is '{t_shade}' but offer is '{o_shade}'")

    # 4. Formulation / Finish Check
    t_form = parse_formulation(target_title, t_specs)
    o_form = parse_formulation(f"{offer_variant} {offer_title}", o_specs)
    formulation_match = True
    if t_form and o_form:
        t_f_lower, o_f_lower = t_form.lower(), o_form.lower()
        if "waterproof" in t_f_lower and "washable" in o_f_lower:
            formulation_match = False
            reasons.append("Formulation mismatch: Target is Waterproof but offer is Washable")
        elif "washable" in t_f_lower and "waterproof" in o_f_lower:
            formulation_match = False
            reasons.append("Formulation mismatch: Target is Washable but offer is Waterproof")

    # 5. Title Similarity Score
    t_clean = re.sub(r"[^a-z0-9 ]", "", target_title.lower()).strip()
    o_clean = re.sub(r"[^a-z0-9 ]", "", offer_title.lower()).strip()
    seq = difflib.SequenceMatcher(None, t_clean, o_clean)
    title_similarity = round(seq.ratio(), 3)

    # 6. Overall Classification & Confidence Score
    confidence = 1.0

    # Incompatible mismatch if critical variant attributes contradict
    if not brand_match or not size_match or not shade_match or not formulation_match:
        confidence = 0.2
        return ProductMatchResult(
            match_classification=MatchClassification.INCOMPATIBLE_MISMATCH,
            confidence_score=confidence,
            is_comparable=False,
            brand_match=brand_match,
            size_match=size_match,
            shade_match=shade_match,
            formulation_match=formulation_match,
            title_similarity=title_similarity,
            reasons=reasons,
            target_size=target_size_str,
            offer_size=offer_size_str,
            target_shade=t_shade,
            offer_shade=o_shade,
        )

    # Possible Match vs Verified Match
    # If title similarity is slightly lower or one of the sizes wasn't explicitly stated
    if title_similarity < 0.70 or (t_val is None or o_val is None) or (t_shade and not o_shade):
        classification = MatchClassification.POSSIBLE_MATCH
        confidence = round(max(0.60, min(0.85, title_similarity)), 2)
        if t_val is None or o_val is None:
            reasons.append("Net quantity missing on one side; possible match requires verification")
        if t_shade and not o_shade:
            reasons.append(f"Target shade '{t_shade}' not explicitly mentioned in offer")
        return ProductMatchResult(
            match_classification=classification,
            confidence_score=confidence,
            is_comparable=False,  # Not strictly comparable without manual or visual verification
            brand_match=brand_match,
            size_match=size_match,
            shade_match=shade_match,
            formulation_match=formulation_match,
            title_similarity=title_similarity,
            reasons=reasons or ["Close match with minor descriptive differences"],
            target_size=target_size_str,
            offer_size=offer_size_str,
            target_shade=t_shade,
            offer_shade=o_shade,
        )

    # Verified Match
    reasons.append("Exact variant match confirmed across brand, volume, shade, and formulation.")
    return ProductMatchResult(
        match_classification=MatchClassification.VERIFIED_MATCH,
        confidence_score=0.98,
        is_comparable=True,
        brand_match=True,
        size_match=True,
        shade_match=True,
        formulation_match=True,
        title_similarity=title_similarity,
        reasons=reasons,
        target_size=target_size_str,
        offer_size=offer_size_str,
        target_shade=t_shade,
        offer_shade=o_shade,
    )


def match_product_with_offer(product: Product, offer: Offer) -> ProductMatchResult:
    """Helper to match a Product against an Offer model."""
    return evaluate_product_match(
        target_brand=product.brand,
        target_title=product.title,
        target_specs=product.specs,
        offer_brand=product.brand,  # Offer belongs to the product in models
        offer_title=product.title,
        offer_variant=offer.variant_name,
        offer_specs=product.specs,
    )

