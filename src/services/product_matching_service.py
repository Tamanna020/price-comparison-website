"""Product Matching & Variant Integrity Service for PriceWise AI Beauty (Phase 11B).

Provides strict multi-factor matching across Indian beauty catalogs:
- Brand identification and normalization
- Exact volume / net quantity extraction and compatibility (30ml != 60ml)
- Unit price calculation (₹/ml, ₹/g) for normalized comparison
- Makeup shade extraction and distinction (e.g., 'Ruby Woo' != 'Velvet Teddy')
- Formulation / finish integrity (e.g., 'Waterproof' != 'Washable', '10%' != '5%')
- Bundle / multi-pack detection (e.g., 'Pack of 2', 'Combo', 'Duo')
- 7-Tier Classification:
  1. EXACT_MATCH: Confirmed identical SKU variant. Safe for direct price comparison.
  2. SIZE_VARIANT: Same product but different size (e.g., 30ml vs 60ml). Normalized unit prices calculated.
  3. FORMULATION_VARIANT: Same brand/line but different active concentration or formulation (e.g. 10% vs 5%, Gel vs Cream).
  4. SHADE_VARIANT: Same makeup product line but different color shade.
  5. BUNDLE_MATCH: Multi-pack or combo compared with single unit.
  6. POSSIBLE_MATCH: High similarity with minor phrasing difference or missing volume specification.
  7. NO_MATCH: Incompatible brand or completely different product.
"""

from dataclasses import dataclass, field
import difflib
import re
from typing import Any, Optional
from src.database.models import Offer, Product


class MatchClassificationType(str):
    """String subclass that allows backward compatibility with legacy 'verified_match' and 'incompatible_mismatch'."""

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, str):
            return False
        s_self = str(self)
        s_other = str(other)
        if s_self == s_other:
            return True
        if s_self in ("EXACT_MATCH", "verified_match") and s_other in ("EXACT_MATCH", "verified_match"):
            return True
        if s_self in ("NO_MATCH", "incompatible_mismatch") and s_other in ("NO_MATCH", "incompatible_mismatch"):
            return True
        return False

    def __hash__(self) -> int:
        return hash(str(self))


class MatchClassification:
    EXACT_MATCH = MatchClassificationType("EXACT_MATCH")
    SIZE_VARIANT = MatchClassificationType("SIZE_VARIANT")
    FORMULATION_VARIANT = MatchClassificationType("FORMULATION_VARIANT")
    SHADE_VARIANT = MatchClassificationType("SHADE_VARIANT")
    BUNDLE_MATCH = MatchClassificationType("BUNDLE_MATCH")
    POSSIBLE_MATCH = MatchClassificationType("POSSIBLE_MATCH")
    NO_MATCH = MatchClassificationType("NO_MATCH")

    # Backward compatibility aliases
    VERIFIED_MATCH = MatchClassificationType("EXACT_MATCH")
    INCOMPATIBLE_MISMATCH = MatchClassificationType("NO_MATCH")


@dataclass
class ProductMatchResult:
    """Detailed evaluation result for product/offer pairing."""
    match_classification: str  # EXACT_MATCH, SIZE_VARIANT, FORMULATION_VARIANT, etc.
    confidence_score: float  # 0.0 to 1.0
    is_comparable: bool  # True only if EXACT_MATCH (or acceptable SIZE_VARIANT with unit price)
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
    target_unit_price: Optional[float] = None
    offer_unit_price: Optional[float] = None
    unit_price_unit: Optional[str] = None
    is_bundle: bool = False
    bundle_quantity: int = 1

    @property
    def is_verified(self) -> bool:
        return self.match_classification in (MatchClassification.EXACT_MATCH, "verified_match")

    @property
    def is_mismatch(self) -> bool:
        return self.match_classification in (
            MatchClassification.NO_MATCH,
            MatchClassification.FORMULATION_VARIANT,
            MatchClassification.SHADE_VARIANT,
            MatchClassification.BUNDLE_MATCH,
            "incompatible_mismatch",
        )

    @property
    def display_badge(self) -> str:
        if self.match_classification in (MatchClassification.EXACT_MATCH, "verified_match"):
            return "Verified Exact Variant"
        elif self.match_classification == MatchClassification.SIZE_VARIANT:
            return "Size Variant (Normalized)"
        elif self.match_classification == MatchClassification.FORMULATION_VARIANT:
            return "Formulation Variant"
        elif self.match_classification == MatchClassification.SHADE_VARIANT:
            return "Shade Variant"
        elif self.match_classification == MatchClassification.BUNDLE_MATCH:
            return "Bundle / Multi-pack"
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
    match = re.search(r"(\d+(?:\.\d+)?)(ml|gm|g|grams?|oz|kg|litres?|l)\b", cleaned)
    if not match:
        # Try looser match without boundary if followed by punctuation
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


def calculate_unit_price(
    price: Optional[float],
    quantity: Optional[float],
    unit: Optional[str],
) -> tuple[Optional[float], Optional[str]]:
    """
    Calculate normalized price per unit (₹/ml or ₹/g).
    Returns (unit_price, unit_str), e.g. (19.97, '₹/ml').
    """
    if price is None or quantity is None or quantity <= 0 or not unit:
        return None, None

    # Normalize to base units (l -> ml, kg -> g)
    norm_qty = quantity
    norm_unit = unit
    if unit == "l":
        norm_qty = quantity * 1000.0
        norm_unit = "ml"
    elif unit == "kg":
        norm_qty = quantity * 1000.0
        norm_unit = "g"

    unit_price = round(price / norm_qty, 2)
    return unit_price, f"₹/{norm_unit}"


def detect_bundle(text: str) -> tuple[bool, int]:
    """
    Detect multi-pack, combo, or bundle keywords.
    Returns (is_bundle, quantity).
    """
    if not text:
        return False, 1

    clean = text.lower()
    # "pack of 2", "pack of 3"
    pack_match = re.search(r"\b(?:pack|set|combo)\s*(?:of)?\s*(\d+)\b", clean)
    if pack_match:
        qty = int(pack_match.group(1))
        if qty > 1:
            return True, qty

    # "2 x 30ml", "2x50g"
    mult_match = re.search(r"\b(\d+)\s*x\s*\d+\s*(?:ml|g|gm)\b", clean)
    if mult_match:
        qty = int(mult_match.group(1))
        if qty > 1:
            return True, qty

    if "duo" in clean or "combo pack" in clean or "twin pack" in clean:
        return True, 2
    if "trio" in clean:
        return True, 3

    return False, 1


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
        "natural",
        "sand",
        "honey",
        "golden",
        "espresso",
        "toffee",
        "porcelain",
        "warm almond",
        "tawny",
        "nude nuance",
        "touch of spice",
    ]
    if specs and "Shade" in specs:
        return str(specs["Shade"]).strip().title()

    combined = (text or "").lower()
    for shade in known_shades:
        if shade in combined:
            return shade.title()
    return None


def parse_concentration(text: str) -> Optional[str]:
    """Extract active ingredient percentage concentrations (e.g., '10%', '5%', '2%')."""
    if not text:
        return None
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*%", text)
    if match:
        return f"{match.group(1)}%"
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
    if "lotion" in combined:
        return "Lotion"
    if "oil" in combined:
        return "Oil"
    if "balm" in combined:
        return "Balm"
    if "cleanser" in combined or "face wash" in combined:
        return "Cleanser"
    if "toner" in combined:
        return "Toner"
    return None


def evaluate_product_match(
    target_brand: str,
    target_title: str,
    target_specs: Optional[dict[str, Any]] = None,
    offer_brand: str = "",
    offer_title: str = "",
    offer_variant: str = "",
    offer_specs: Optional[dict[str, Any]] = None,
    target_price: Optional[float] = None,
    offer_price: Optional[float] = None,
) -> ProductMatchResult:
    """
    Perform multi-factor matching between a target beauty product and a retailer offer.
    Supports 7-tier classifications:
    - EXACT_MATCH
    - SIZE_VARIANT (with unit price normalization)
    - FORMULATION_VARIANT (e.g. 10% vs 5%, Waterproof vs Washable)
    - SHADE_VARIANT (e.g. Ruby Woo vs Velvet Teddy)
    - BUNDLE_MATCH (pack of 2 vs single)
    - POSSIBLE_MATCH
    - NO_MATCH
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

    if not brand_match:
        return ProductMatchResult(
            match_classification=MatchClassification.NO_MATCH,
            confidence_score=0.10,
            is_comparable=False,
            brand_match=False,
            size_match=False,
            shade_match=False,
            formulation_match=False,
            title_similarity=0.0,
            reasons=reasons,
        )

    # 2. Bundle Detection
    t_is_bundle, t_bundle_qty = detect_bundle(target_title)
    o_is_bundle, o_bundle_qty = detect_bundle(f"{offer_variant} {offer_title}")
    if o_is_bundle and not t_is_bundle:
        reasons.append(f"Bundle / multi-pack detected in offer ({o_bundle_qty} items) vs single target product")
        return ProductMatchResult(
            match_classification=MatchClassification.BUNDLE_MATCH,
            confidence_score=0.70,
            is_comparable=False,
            brand_match=True,
            size_match=False,
            shade_match=True,
            formulation_match=True,
            title_similarity=round(difflib.SequenceMatcher(None, target_title.lower(), offer_title.lower()).ratio(), 3),
            reasons=reasons,
            is_bundle=True,
            bundle_quantity=o_bundle_qty,
        )

    # 3. Active Concentration & Formulation Check
    t_conc = parse_concentration(target_title)
    o_conc = parse_concentration(f"{offer_variant} {offer_title}")
    if t_conc and o_conc and t_conc != o_conc:
        reasons.append(f"Formulation concentration mismatch: Target is {t_conc} but offer is {o_conc}")
        return ProductMatchResult(
            match_classification=MatchClassification.FORMULATION_VARIANT,
            confidence_score=0.75,
            is_comparable=False,
            brand_match=True,
            size_match=True,
            shade_match=True,
            formulation_match=False,
            title_similarity=round(difflib.SequenceMatcher(None, target_title.lower(), offer_title.lower()).ratio(), 3),
            reasons=reasons,
        )

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
        elif t_f_lower != o_f_lower and t_f_lower in ("gel", "cream", "serum", "lotion", "oil", "balm") and o_f_lower in ("gel", "cream", "serum", "lotion", "oil", "balm"):
            formulation_match = False
            reasons.append(f"Formulation mismatch: Target is {t_form} but offer is {o_form}")

    if not formulation_match:
        return ProductMatchResult(
            match_classification=MatchClassification.FORMULATION_VARIANT,
            confidence_score=0.75,
            is_comparable=False,
            brand_match=True,
            size_match=True,
            shade_match=True,
            formulation_match=False,
            title_similarity=round(difflib.SequenceMatcher(None, target_title.lower(), offer_title.lower()).ratio(), 3),
            reasons=reasons,
        )

    # 4. Makeup Shade Check
    t_shade = parse_shade(target_title, t_specs)
    o_shade = parse_shade(f"{offer_variant} {offer_title}", o_specs)
    shade_match = True
    if t_shade and o_shade and t_shade.lower() != o_shade.lower():
        shade_match = False
        reasons.append(f"Shade mismatch: Target is '{t_shade}' but offer is '{o_shade}'")
        return ProductMatchResult(
            match_classification=MatchClassification.SHADE_VARIANT,
            confidence_score=0.75,
            is_comparable=False,
            brand_match=True,
            size_match=True,
            shade_match=False,
            formulation_match=True,
            title_similarity=round(difflib.SequenceMatcher(None, target_title.lower(), offer_title.lower()).ratio(), 3),
            reasons=reasons,
            target_shade=t_shade,
            offer_shade=o_shade,
        )

    # 5. Net Quantity / Volume Check & Unit Price Normalization
    target_qty_text = str(t_specs.get("Net Quantity") or t_specs.get("Size") or target_title)
    offer_qty_text = str(o_specs.get("Net Quantity") or o_specs.get("Size") or f"{offer_variant} {offer_title}")
    t_val, t_unit = parse_quantity_volume(target_qty_text)
    o_val, o_unit = parse_quantity_volume(offer_qty_text)

    target_size_str = f"{t_val}{t_unit}" if t_val is not None else None
    offer_size_str = f"{o_val}{o_unit}" if o_val is not None else None

    # Calculate unit prices
    t_unit_price, t_unit_str = calculate_unit_price(target_price, t_val, t_unit)
    o_unit_price, o_unit_str = calculate_unit_price(offer_price, o_val, o_unit)

    size_match = True
    is_size_variant = False
    if t_val is not None and o_val is not None:
        if t_unit == o_unit and abs(t_val - o_val) > 0.01:
            size_match = False
            is_size_variant = True
            reasons.append(
                f"Size mismatch: Target is {t_val}{t_unit} but offer is {o_val}{o_unit}. 30ml cannot be compared directly with 50ml."
            )
        elif t_unit != o_unit:
            size_match = False
            is_size_variant = True
            reasons.append(f"Unit mismatch: Target is in {t_unit} while offer is in {o_unit}")

    # Title similarity
    t_clean = re.sub(r"[^a-z0-9 ]", "", target_title.lower()).strip()
    o_clean = re.sub(r"[^a-z0-9 ]", "", offer_title.lower()).strip()
    title_similarity = round(difflib.SequenceMatcher(None, t_clean, o_clean).ratio(), 3)

    if is_size_variant:
        reasons.append(f"Size variant detected: {target_size_str} vs {offer_size_str}. Unit prices calculated.")
        return ProductMatchResult(
            match_classification=MatchClassification.SIZE_VARIANT,
            confidence_score=0.88,
            is_comparable=False,  # Not directly comparable without unit price comparison
            brand_match=True,
            size_match=False,
            shade_match=True,
            formulation_match=True,
            title_similarity=title_similarity,
            reasons=reasons,
            target_size=target_size_str,
            offer_size=offer_size_str,
            target_shade=t_shade,
            offer_shade=o_shade,
            target_unit_price=t_unit_price,
            offer_unit_price=o_unit_price,
            unit_price_unit=o_unit_str or t_unit_str,
        )

    # 6. Possible Match vs Exact Match
    if title_similarity < 0.65 or (t_val is None or o_val is None) or (t_shade and not o_shade):
        classification = MatchClassification.POSSIBLE_MATCH
        confidence = round(max(0.60, min(0.85, title_similarity)), 2)
        if t_val is None or o_val is None:
            reasons.append("Net quantity missing on one side; possible match requires verification")
        if t_shade and not o_shade:
            reasons.append(f"Target shade '{t_shade}' not explicitly mentioned in offer")
        return ProductMatchResult(
            match_classification=classification,
            confidence_score=confidence,
            is_comparable=False,
            brand_match=True,
            size_match=size_match,
            shade_match=shade_match,
            formulation_match=True,
            title_similarity=title_similarity,
            reasons=reasons or ["Close match with minor descriptive differences"],
            target_size=target_size_str,
            offer_size=offer_size_str,
            target_shade=t_shade,
            offer_shade=o_shade,
            target_unit_price=t_unit_price,
            offer_unit_price=o_unit_price,
            unit_price_unit=o_unit_str or t_unit_str,
        )

    # Exact Match
    reasons.append("Exact variant match confirmed across brand, volume, shade, and formulation.")
    return ProductMatchResult(
        match_classification=MatchClassification.EXACT_MATCH,
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
        target_unit_price=t_unit_price,
        offer_unit_price=o_unit_price,
        unit_price_unit=o_unit_str or t_unit_str,
    )


def match_product_with_offer(product: Product, offer: Offer) -> ProductMatchResult:
    """Helper to match a Product against an Offer model."""
    return evaluate_product_match(
        target_brand=product.brand,
        target_title=product.title,
        target_specs=product.specs,
        target_price=product.price,
        offer_brand=product.brand,
        offer_title=product.title,
        offer_variant=offer.variant_name,
        offer_specs=product.specs,
        offer_price=offer.current_price,
    )
