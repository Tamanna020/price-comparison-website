"""Current Deals and Verified Offers Intelligence Service for PriceWise AI Beauty (Phase 5).

Provides verified beauty deal tracking across Indian retailers:
- Genuine savings calculations against verifiable reference MSRP / historical lows
- Authentic retailer coupon codes with explicit terms (e.g. NYKBEAUTY10, TIRA100)
- Expiration tracking: filters or flags expired promotional campaigns
- Strict anti-deception policies: no synthetic countdown timers or false urgency
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from src.database.models import Product, Offer
from src.database.price_history_service import parse_timestamp
from src.services.product_service import get_products


@dataclass
class VerifiedBeautyDeal:
    """Represents a verified deal or promotional discount on a beauty item."""
    deal_id: str
    product_id: int
    product_slug: str
    product_title: str
    brand: str
    category: str
    subcategory: str
    retailer_name: str
    current_price: float
    original_price: Optional[float]
    net_price: float
    coupon_code: Optional[str] = None
    coupon_discount: float = 0.0
    coupon_terms: Optional[str] = None
    savings_amount: float = 0.0
    savings_pct: float = 0.0
    deal_score: int = 70
    deal_badge: str = ""
    expires_at: Optional[str] = None
    is_expired: bool = False
    data_source: str = "demo"
    image_url: str = ""

    @property
    def is_active(self) -> bool:
        """True if the deal has not expired and provides positive savings."""
        return not self.is_expired and (self.savings_amount > 0 or self.coupon_discount > 0)


def calculate_deal_savings(
    current_price: float,
    reference_price: Optional[float],
    coupon_discount: float = 0.0,
) -> tuple[float, float, float]:
    """
    Calculate effective net price, absolute savings, and savings percentage.
    Returns (net_price, savings_amount, savings_pct).
    """
    net_price = max(0.0, current_price - coupon_discount)
    ref = reference_price if (reference_price and reference_price > 0) else current_price

    if ref > net_price:
        savings = round(ref - net_price, 2)
        pct = round((savings / ref) * 100, 1)
        return round(net_price, 2), savings, pct
    return round(net_price, 2), 0.0, 0.0


def check_is_deal_expired(
    expires_at: Optional[str],
    reference_time: Optional[datetime] = None,
) -> bool:
    """Check whether a deal expiration date has passed."""
    if not expires_at:
        return False
    dt = parse_timestamp(expires_at)
    if not dt:
        return False
    ref_dt = reference_time or datetime.now(timezone.utc)
    return dt < ref_dt


def get_verified_beauty_deals(
    products: Optional[list[Product]] = None,
    include_expired: bool = False,
    min_savings_pct: float = 5.0,
    custom_path: Optional[str] = None,
) -> list[VerifiedBeautyDeal]:
    """
    Evaluate products across Indian retailer offers to identify verified deals.
    Excludes expired deals by default, calculates genuine savings against MRP/reference,
    and sorts by savings percentage and deal score.
    """
    if products is None:
        products = get_products(custom_path=custom_path)

    deals: list[VerifiedBeautyDeal] = []

    for product in products:
        for offer in product.offers:
            if not offer.is_available or not offer.has_valid_price:
                continue

            orig_price = offer.original_price or product.specs.get("MRP")
            try:
                orig_float = float(orig_price) if orig_price else None
            except (ValueError, TypeError):
                orig_float = None

            coupon_code = getattr(offer, "coupon_code", None)
            coupon_discount = getattr(offer, "coupon_discount", 0.0) or 0.0

            # Derive expiration from offer specs or simulated validity window
            expires_at = None
            if hasattr(offer, "expires_at") and offer.expires_at:
                expires_at = offer.expires_at

            is_expired = check_is_deal_expired(expires_at)
            if is_expired and not include_expired:
                continue

            net_price, savings_amt, savings_pct = calculate_deal_savings(
                current_price=offer.current_price,
                reference_price=orig_float,
                coupon_discount=coupon_discount,
            )

            if savings_pct < min_savings_pct and coupon_discount <= 0:
                continue

            # Compute deal badge
            if coupon_code and coupon_discount > 0:
                badge = f"Use {coupon_code} (-₹{coupon_discount:.0f})"
            elif savings_pct >= 20:
                badge = f"{savings_pct:.0f}% OFF"
            else:
                badge = f"Save ₹{savings_amt:.0f}"

            # Deal score: based on savings percentage, store rating, availability
            base_score = int(min(98, max(50, 50 + (savings_pct * 1.2))))
            if offer.store_rating and offer.store_rating >= 4.5:
                base_score = min(98, base_score + 5)

            deal = VerifiedBeautyDeal(
                deal_id=f"deal-{product.id}-{offer.id}",
                product_id=product.id,
                product_slug=product.slug,
                product_title=product.title,
                brand=product.brand,
                category=product.category,
                subcategory=product.specs.get("Subcategory", product.category),
                retailer_name=offer.store_name,
                current_price=offer.current_price,
                original_price=orig_float,
                net_price=net_price,
                coupon_code=coupon_code,
                coupon_discount=coupon_discount,
                coupon_terms=getattr(offer, "coupon_terms", None),
                savings_amount=savings_amt,
                savings_pct=savings_pct,
                deal_score=base_score,
                deal_badge=badge,
                expires_at=expires_at,
                is_expired=is_expired,
                data_source=getattr(offer, "source_type", "demo"),
                image_url=product.image_url,
            )
            deals.append(deal)

    # Sort descending by savings percentage then deal score
    deals.sort(key=lambda d: (not d.is_expired, d.savings_pct, d.deal_score), reverse=True)
    return deals

