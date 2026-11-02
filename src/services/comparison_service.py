"""Comparison service for side-by-side store analysis.
Provides strict product matching, verified savings calculation,
and safe handling of unavailable offers, single-store comparisons, and edge cases.
"""

from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
from src.database.models import Offer, Product


@dataclass
class ComparisonSummary:
    product: Product
    total_stores: int
    total_offers: int
    available_offers_count: int
    lowest_available_offer: Optional[Offer]
    lowest_total_cost_offer: Optional[Offer]
    lowest_price: Optional[float]
    lowest_total_cost: Optional[float]
    highest_price: Optional[float]
    max_price_spread: float
    potential_savings_pct: float
    is_single_store: bool
    has_verified_savings: bool
    savings_claim_explanation: str
    ranked_offers: list[Offer] = field(default_factory=list)
    non_comparable_offers: list[dict] = field(default_factory=list)
    lowest_verified_offer_label: str = "Lowest among available verified offers"
    is_shipping_known_for_all: bool = True
    verified_match_count: int = 0
    possible_match_count: int = 0

    @property
    def cheapest_store_name(self) -> str:
        """Name of the store offering the lowest total cost among available offers."""
        if self.lowest_total_cost_offer:
            return self.lowest_total_cost_offer.store_name
        if self.ranked_offers:
            return self.ranked_offers[0].store_name
        return ""


def validate_offer_compatibility(product: Product, offer: Offer) -> tuple[bool, str]:
    """
    Validate that an offer strictly matches the target product.
    Checks product identity, positive valid pricing, and variant compatibility.
    Rejects uncertain, corrupt, or mismatched offers.
    """
    # 1. Product ID check
    if offer.product_id != product.id:
        return False, "Mismatched Product ID"

    # 2. Price validity check (must be positive, non-zero float)
    if offer.current_price is None or offer.current_price <= 0:
        return False, "Invalid or missing price value"

    # 3. Store name validity
    if not offer.store_name or not offer.store_name.strip():
        return False, "Missing retailer identifier"

    # 4. Strict variant matching:
    # If the product specification specifies a specific storage/capacity or model,
    # the offer variant must not contradict it.
    canonical_specs = product.specs or {}
    offer_variant_lower = (offer.variant_name or "").lower()

    # Check for obvious tech variant contradictions (e.g., 256GB vs 512GB)
    if "Storage" in canonical_specs:
        target_storage = str(canonical_specs["Storage"]).lower().replace(" ", "")
        # If offer specifies a different storage capacity, reject as non-comparable
        for alt_storage in ["128gb", "256gb", "512gb", "1tb", "2tb"]:
            if alt_storage in offer_variant_lower and alt_storage not in target_storage:
                return False, f"Variant mismatch: offer has {alt_storage.upper()} but product is {target_storage.upper()}"

    # Beauty variant checks: Size / Net Quantity
    target_qty_raw = canonical_specs.get("Net Quantity") or canonical_specs.get("Size")
    if target_qty_raw:
        import re
        target_qty = str(target_qty_raw).lower().replace(" ", "")
        for unit in ["ml", "g", "gm", "oz"]:
            target_match = re.search(r"(\d+(?:\.\d+)?)" + unit, target_qty)
            offer_match = re.search(r"(\d+(?:\.\d+)?)" + unit, offer_variant_lower.replace(" ", ""))
            if target_match and offer_match:
                if target_match.group(1) != offer_match.group(1):
                    return False, f"Variant mismatch: Size/volume mismatch: offer has {offer_match.group(0).upper()} but product is {target_match.group(0).upper()}"

    # Beauty variant checks: Shade
    if "Shade" in canonical_specs:
        target_shade = str(canonical_specs["Shade"]).lower().strip()
        for known_shade in ["ruby woo", "reconstruct", "velvet teddy", "warm nude", "encourage", "midnight black"]:
            if known_shade in offer_variant_lower and known_shade not in target_shade:
                return False, f"Variant mismatch: Shade mismatch: offer has shade '{known_shade.title()}' but product is '{target_shade.title()}'"

    # Beauty variant checks: Formulation
    target_form_raw = canonical_specs.get("Product Type") or canonical_specs.get("Formulation")
    if target_form_raw:
        target_type = str(target_form_raw).lower()
        if "waterproof" in target_type and "washable" in offer_variant_lower:
            return False, "Variant mismatch: Formulation mismatch: offer is Washable but product is Waterproof"
        if "washable" in target_type and "waterproof" in offer_variant_lower:
            return False, "Variant mismatch: Formulation mismatch: offer is Waterproof but product is Washable"

    return True, "Verified Exact Match"


def generate_comparison_summary(product: Product) -> Optional[ComparisonSummary]:
    """
    Analyze and rank all matching offers for a single product.
    Ensures that only comparable, valid offers are evaluated, and never
    claims verified savings unless there are at least two distinct in-stock store offers.
    """
    if not product.offers:
        return None

    # Step 1: Filter and partition into comparable vs non-comparable offers
    comparable_offers: list[Offer] = []
    non_comparable_offers: list[dict] = []

    for offer in product.offers:
        is_comp, reason = validate_offer_compatibility(product, offer)
        if is_comp:
            comparable_offers.append(offer)
        else:
            non_comparable_offers.append({"offer": offer, "reason": reason})

    if not comparable_offers:
        return None

    # Step 2: Separate available (in-stock) vs unavailable offers
    available = [o for o in comparable_offers if o.is_available]

    # Rank offers: Available first (sorted by total_cost, then rating), followed by unavailable
    ranked_available = sorted(available, key=lambda o: (o.total_cost, -o.store_rating))
    unavailable = [o for o in comparable_offers if not o.is_available]
    ranked_unavailable = sorted(unavailable, key=lambda o: (o.total_cost, -o.store_rating))
    all_ranked = ranked_available + ranked_unavailable

    # Step 3: Determine lowest available offers
    if ranked_available:
        lowest_total_offer = ranked_available[0]
        # Offer with lowest base item price
        lowest_price_offer = min(ranked_available, key=lambda o: o.current_price)
        lowest_price = lowest_price_offer.current_price
        lowest_total_cost = lowest_total_offer.total_cost
        available_prices = [o.current_price for o in ranked_available]
        highest_price = max(available_prices)
    else:
        # Fallback when all offers are out of stock
        lowest_total_offer = None
        lowest_price_offer = min(comparable_offers, key=lambda o: o.current_price)
        lowest_price = lowest_price_offer.current_price
        lowest_total_cost = min(o.total_cost for o in comparable_offers)
        highest_price = max(o.current_price for o in comparable_offers)

    unique_stores = {o.store_name for o in comparable_offers}
    total_stores = len(unique_stores)
    is_single_store = total_stores <= 1

    # Step 4: Calculate savings and price spread safely
    # Verified savings can ONLY be claimed if:
    # 1. More than 1 store is offering the product.
    # 2. At least 2 available (in-stock) offers exist.
    # 3. There is a positive price spread (highest_price > lowest_price).
    has_verified_savings = False
    max_price_spread = 0.0
    potential_savings_pct = 0.0
    savings_explanation = ""

    if len(ranked_available) >= 2 and not is_single_store:
        max_price_spread = round(highest_price - lowest_price, 2)
        if highest_price > 0 and max_price_spread > 0:
            potential_savings_pct = round((max_price_spread / highest_price) * 100, 1)
            has_verified_savings = True
            highest_offer = max(ranked_available, key=lambda o: o.current_price)
            savings_explanation = (
                f"Verified savings of ${max_price_spread:,.2f} ({potential_savings_pct}%) available between "
                f"{lowest_price_offer.store_name} (${lowest_price:,.2f}) and "
                f"{highest_offer.store_name} (${highest_price:,.2f}) for the exact same model."
            )
        else:
            savings_explanation = f"Uniform pricing of ${lowest_price:,.2f} across all available stores ($0.00 price difference)."
    elif is_single_store:
        savings_explanation = (
            f"Exclusive to {comparable_offers[0].store_name} (${lowest_price:,.2f}). "
            "No competing store offers currently recorded for price spread comparison."
        )
    elif len(ranked_available) == 1:
        savings_explanation = (
            f"Only 1 store ({ranked_available[0].store_name}) currently has this item in stock. "
            "Alternative retailers are currently Out of Stock."
        )
    else:
        savings_explanation = "This item is currently Out of Stock across all monitored stores. Historical prices shown for reference."

    is_shipping_known = all(getattr(o, "is_shipping_disclosed", True) for o in comparable_offers)

    return ComparisonSummary(
        product=product,
        total_stores=total_stores,
        total_offers=len(comparable_offers),
        available_offers_count=len(ranked_available),
        lowest_available_offer=lowest_price_offer if ranked_available else None,
        lowest_total_cost_offer=lowest_total_offer,
        lowest_price=lowest_price,
        lowest_total_cost=lowest_total_cost,
        highest_price=highest_price,
        max_price_spread=max_price_spread,
        potential_savings_pct=potential_savings_pct,
        is_single_store=is_single_store,
        has_verified_savings=has_verified_savings,
        savings_claim_explanation=savings_explanation,
        ranked_offers=all_ranked,
        non_comparable_offers=non_comparable_offers,
        lowest_verified_offer_label="Lowest among available verified offers",
        is_shipping_known_for_all=is_shipping_known,
        verified_match_count=len(comparable_offers),
        possible_match_count=len(non_comparable_offers),
    )


def build_price_history_dataframe(
    product: Product,
    window: str = "all",
    reference_date: Optional[object] = None,
) -> pd.DataFrame:
    """
    Consolidates historical price data across all stores for time-series visualization.
    Supports time windows ('30d', '90d', 'all') based on real observation timestamps.
    Returns a pandas DataFrame formatted for Altair/Streamlit charting.
    """
    from datetime import datetime, timezone, timedelta
    from src.database.price_history_service import parse_timestamp

    ref_dt = reference_date or datetime.now(timezone.utc)
    cutoff = None
    if window == "30d":
        cutoff = ref_dt - timedelta(days=30)
    elif window == "90d":
        cutoff = ref_dt - timedelta(days=90)

    records = []
    for offer in product.offers:
        for hp in offer.price_history:
            if hp.price <= 0:
                continue
            hp_dt = parse_timestamp(hp.recorded_at)
            if cutoff and hp_dt and hp_dt < cutoff:
                continue
            records.append({
                "Date": hp.recorded_at[:10],
                "Store": offer.store_name,
                "Price": hp.price,
                "Currency": hp.currency or "USD",
                "Data Status": "DEMO DATA",
            })

    if not records:
        return pd.DataFrame(columns=["Date", "Store", "Price", "Currency", "Data Status"])

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["Date", "Store"]).sort_values(by="Date")
    return df
    df = df.drop_duplicates(subset=["Date", "Store"]).sort_values(by="Date")
    return df
