"""Advanced Price Intelligence & Deal Analytics Service for PriceWise AI (Phase 9A).

Provides comprehensive price intelligence capabilities:
1. Total purchase cost calculation (price + shipping - valid coupons).
2. Unknown shipping preservation (never assume zero if undisclosed).
3. Coupon validation and expiration enforcement.
4. Historical price analytics across 7-day, 30-day, and 90-day windows.
5. Strict DEMO vs. LIVE_VERIFIED data segregation.
6. Multi-factor explainable deal scoring (0-100) with simulated flags for demo data.
7. User-isolated price alert management and duplicate prevention.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Optional, Dict, List, Tuple
from src.database.connection import get_connection
from src.database.models import PricePoint, PriceAlert, PriceTrackingRecord
from src.database.price_history_service import parse_timestamp, get_product_price_history
from src.services.product_service import get_product_by_id, get_product_by_slug
from src.services.price_tracking_service import (
    add_tracked_product,
    get_tracked_products,
    remove_tracking,
    evaluate_tracking_rules,
    get_alert_history,
    mark_alert_read,
)

logger = logging.getLogger("pricewise.price_intelligence")


# =============================================================================
# 1. Total Purchase Cost & Coupon Intelligence Data Classes
# =============================================================================

@dataclass
class CouponValidationResult:
    """Validation result for an e-commerce coupon code."""
    code: str
    is_valid: bool
    discount_amount: float = 0.0
    discount_pct: Optional[float] = None
    min_spend: float = 0.0
    description: str = ""
    rejection_reason: Optional[str] = None
    expires_at: Optional[str] = None
    is_expired: bool = False
    source: str = "simulated"
    is_simulated: bool = True
    disclaimer: str = "Simulated coupon for demonstration only. Coupon eligibility and terms have not been verified with retailer."


@dataclass
class TotalPurchaseCostBreakdown:
    """Itemized breakdown of the true landed purchase cost."""
    retailer_name: str
    base_price: float
    shipping_fee: Optional[float]
    is_shipping_known: bool
    shipping_label: str  # "Free Shipping", "Paid Shipping", "Shipping Not Disclosed"
    coupon_applied: Optional[CouponValidationResult] = None
    final_payable_price: float = 0.0
    is_final_exact: bool = True  # False if shipping is unknown
    payable_state_note: str = ""
    reference_mrp: Optional[float] = None
    mrp_discount: float = 0.0  # Discount against manufacturer reference MRP (not verified market savings)
    confirmed_savings: float = 0.0  # Kept for schema backwards compatibility (= mrp_discount)
    simulated_coupon_savings: float = 0.0  # Hypothetical test coupon deduction
    coupon_savings: float = 0.0  # Kept for schema backwards compatibility (= simulated_coupon_savings)
    total_potential_savings: float = 0.0  # Total potential discount vs MRP if simulated coupon is accepted
    genuine_verified_market_savings: float = 0.0  # Strictly 0.0 for demo data (requires verified live cross-store evidence)
    currency: str = "INR"
    data_status: str = "demo"  # "demo", "live_verified", "manual"
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Simulated test coupons for demonstration - NOT backed by official retailer API feeds
SIMULATED_TEST_COUPONS = {
    "NYKBEAUTY10": {
        "discount_pct": 10.0,
        "max_discount": 150.0,
        "min_spend": 499.0,
        "description": "[Simulated Test Coupon] Hypothetical 10% demo discount (Max ₹150) for platform evaluation. Not verified with Nykaa.",
        "expires_at": "2026-12-31 23:59:59",
        "retailer": "Nykaa",
    },
    "TIRA100": {
        "fixed_discount": 100.0,
        "min_spend": 899.0,
        "description": "[Simulated Test Coupon] Hypothetical ₹100 flat demo discount for platform evaluation. Not verified with Tira.",
        "expires_at": "2026-12-31 23:59:59",
        "retailer": "Tira",
    },
    "PURPLLE50": {
        "fixed_discount": 50.0,
        "min_spend": 399.0,
        "description": "[Simulated Test Coupon] Hypothetical ₹50 flat demo discount for platform evaluation. Not verified with Purplle.",
        "expires_at": "2026-12-31 23:59:59",
        "retailer": "Purplle",
    },
    "EXPIRED20": {
        "discount_pct": 20.0,
        "max_discount": 300.0,
        "min_spend": 500.0,
        "description": "[Simulated Test Coupon] Expired demonstration coupon for testing rejection logic. Not a real retailer promo.",
        "expires_at": "2026-01-01 00:00:00",
        "retailer": "Amazon India",
    },
}
KNOWN_COUPONS = SIMULATED_TEST_COUPONS


def validate_retailer_coupon(
    coupon_code: Optional[str],
    order_amount: float,
    retailer_name: Optional[str] = None,
    reference_time: Optional[datetime] = None,
) -> CouponValidationResult:
    """
    Validate coupon code against known rules, expiration, and minimum spend.
    Rule: Never apply an expired coupon or assume unknown eligibility.
    """
    if not coupon_code or not coupon_code.strip():
        return CouponValidationResult(
            code="",
            is_valid=False,
            rejection_reason="No coupon code provided",
        )

    code_clean = coupon_code.strip().upper()
    rule = KNOWN_COUPONS.get(code_clean)

    if not rule:
        return CouponValidationResult(
            code=code_clean,
            is_valid=False,
            rejection_reason=f"Coupon code '{code_clean}' is unverified or unrecognized for this store.",
        )

    # Expiration check
    ref_dt = reference_time or datetime.now(timezone.utc)
    exp_str = rule.get("expires_at")
    if exp_str:
        exp_dt = parse_timestamp(exp_str)
        if exp_dt and exp_dt < ref_dt:
            return CouponValidationResult(
                code=code_clean,
                is_valid=False,
                is_expired=True,
                expires_at=exp_str,
                description=rule.get("description", ""),
                rejection_reason=f"Coupon '{code_clean}' expired on {exp_str}.",
            )

    # Minimum spend check
    min_spend = float(rule.get("min_spend", 0.0))
    if order_amount < min_spend:
        return CouponValidationResult(
            code=code_clean,
            is_valid=False,
            min_spend=min_spend,
            description=rule.get("description", ""),
            rejection_reason=f"Order amount ₹{order_amount:.0f} is below minimum spend threshold ₹{min_spend:.0f}.",
        )

    # Calculate discount
    discount = 0.0
    if "discount_pct" in rule:
        pct = float(rule["discount_pct"])
        calc = (order_amount * pct) / 100.0
        max_d = rule.get("max_discount")
        discount = min(calc, float(max_d)) if max_d else calc
    elif "fixed_discount" in rule:
        discount = min(order_amount, float(rule["fixed_discount"]))

    return CouponValidationResult(
        code=code_clean,
        is_valid=True,
        discount_amount=round(discount, 2),
        discount_pct=rule.get("discount_pct"),
        min_spend=min_spend,
        description=rule.get("description", ""),
        expires_at=exp_str,
        is_expired=False,
        source="simulated",
        is_simulated=True,
        disclaimer="Simulated test coupon; eligibility and terms have not been verified with retailer.",
    )


def calculate_total_purchase_cost(
    product_price: float,
    shipping_fee: Optional[float] = None,
    is_shipping_disclosed: bool = True,
    coupon_code: Optional[str] = None,
    retailer_name: str = "Retailer",
    reference_mrp: Optional[float] = None,
    data_status: str = "demo",
) -> TotalPurchaseCostBreakdown:
    """
    Calculate landed purchase cost.
    
    Formula: Final payable price = Product price + Shipping - Valid discounts.
    
    Strict Rules:
    - Unknown shipping remains unknown (NOT automatically zero).
    - Unknown/expired coupon eligibility must not be assumed.
    - Clearly distinguish Reference MRP discount from genuine verified market savings.
    """
    if product_price is None or product_price < 0:
        product_price = 0.0

    # 1. Shipping evaluation
    is_shipping_known = bool(is_shipping_disclosed and shipping_fee is not None)
    actual_shipping = float(shipping_fee) if is_shipping_known else 0.0

    if not is_shipping_disclosed or shipping_fee is None:
        shipping_label = "Shipping Not Disclosed"
    elif shipping_fee == 0:
        shipping_label = "Free Shipping"
    else:
        shipping_label = f"+ ₹{shipping_fee:.0f} Shipping"

    # 2. Coupon evaluation
    coupon_res = None
    coupon_discount = 0.0
    if coupon_code and coupon_code.strip():
        coupon_res = validate_retailer_coupon(coupon_code, product_price, retailer_name)
        if coupon_res.is_valid:
            coupon_discount = coupon_res.discount_amount

    # 3. Final payable calculation
    final_price = max(0.0, product_price + actual_shipping - coupon_discount)
    is_final_exact = is_shipping_known

    if not is_shipping_known:
        payable_note = "Total does not include shipping; additional delivery fees may apply at retailer checkout."
    elif coupon_discount > 0:
        payable_note = f"Includes ₹{coupon_discount:.0f} simulated test coupon deduction from code {coupon_res.code}. Coupon eligibility has not been verified with retailer."
    else:
        payable_note = "Estimated landed cost with disclosed shipping."

    # 4. Savings segregation
    mrp_discount = max(0.0, reference_mrp - product_price) if (reference_mrp and reference_mrp > product_price) else 0.0
    total_savings = mrp_discount + coupon_discount
    genuine_market_savings = 0.0  # Zero genuine verified market savings for demo catalog data

    return TotalPurchaseCostBreakdown(
        retailer_name=retailer_name,
        base_price=round(product_price, 2),
        shipping_fee=round(shipping_fee, 2) if is_shipping_known else None,
        is_shipping_known=is_shipping_known,
        shipping_label=shipping_label,
        coupon_applied=coupon_res,
        final_payable_price=round(final_price, 2),
        is_final_exact=is_final_exact,
        payable_state_note=payable_note,
        reference_mrp=round(reference_mrp, 2) if reference_mrp else None,
        mrp_discount=round(mrp_discount, 2),
        confirmed_savings=round(mrp_discount, 2),
        simulated_coupon_savings=round(coupon_discount, 2),
        coupon_savings=round(coupon_discount, 2),
        total_potential_savings=round(total_savings, 2),
        genuine_verified_market_savings=genuine_market_savings,
        currency="INR",
        data_status=data_status,
    )


# =============================================================================
# 2. Historical Price Analytics Data Classes & Service
# =============================================================================

@dataclass
class PricePointDto:
    """Individual timestamped price observation for analytics."""
    id: int
    offer_id: int
    price: float
    currency: str
    recorded_at: str
    data_source: str
    data_status: str


@dataclass
class ProductPriceAnalyticsResponse:
    """Aggregated historical price analytics over a defined observation window."""
    product_id: int
    product_slug: str
    product_title: str
    window_days: int  # 7, 30, or 90
    points: List[PricePointDto]
    lowest_recorded_price: Optional[float]
    highest_recorded_price: Optional[float]
    average_recorded_price: Optional[float]
    current_lowest_price: Optional[float]
    price_movement_pct: Optional[float]
    price_trend: str  # "downward", "upward", "stable", "volatile", "insufficient_data"
    observation_count: int
    is_sufficient_history: bool
    currency: str = "INR"
    history_data_status: str = "DEMO"  # "DEMO" or "VERIFIED"
    is_simulated: bool = True
    disclaimer: str = ""


def compute_price_trend(points: List[PricePoint]) -> Tuple[str, Optional[float]]:
    """Determine price trend direction and percentage change from chronological points."""
    if len(points) < 2:
        return "insufficient_data", 0.0

    first_price = points[0].price
    last_price = points[-1].price

    if first_price <= 0:
        return "stable", 0.0

    movement_pct = round(((last_price - first_price) / first_price) * 100, 2)

    if movement_pct <= -2.0:
        trend = "downward"
    elif movement_pct >= 2.0:
        trend = "upward"
    else:
        # Check volatility
        prices = [p.price for p in points]
        spread = max(prices) - min(prices)
        if spread / first_price > 0.15:
            trend = "volatile"
        else:
            trend = "stable"

    return trend, movement_pct


def get_product_price_analytics(
    product_id_or_slug: str | int,
    window_days: int = 30,
    custom_path: Optional[str] = None,
) -> ProductPriceAnalyticsResponse:
    """
    Compute rigorous price history analytics for a product across a 7, 30, or 90-day window.
    
    Strict Rules:
    - Compute statistics only from eligible records in that window.
    - Keep DEMO history labeled as DEMO. Never claim demo low is market low.
    - Do not invent missing records.
    """
    if window_days not in (7, 30, 90, 180):
        window_days = 30

    product = None
    if isinstance(product_id_or_slug, int) or str(product_id_or_slug).isdigit():
        product = get_product_by_id(int(product_id_or_slug), custom_path=custom_path)
    if not product:
        product = get_product_by_slug(str(product_id_or_slug), custom_path=custom_path)

    if not product:
        return ProductPriceAnalyticsResponse(
            product_id=0,
            product_slug=str(product_id_or_slug),
            product_title="Product Not Found",
            window_days=window_days,
            points=[],
            lowest_recorded_price=None,
            highest_recorded_price=None,
            average_recorded_price=None,
            current_lowest_price=None,
            price_movement_pct=None,
            price_trend="insufficient_data",
            observation_count=0,
            is_sufficient_history=False,
            disclaimer="Product not found in catalog.",
        )

    # Use existing price history service to extract windowed points
    summary = get_product_price_history(
        product_id=product.id,
        variant_name=None,
        window_days=window_days,
        custom_path=custom_path,
    )

    points = summary.points
    trend, movement = compute_price_trend(points)

    current_low = None
    if product.offers:
        valid_offers = [o.current_price for o in product.offers if o.current_price > 0 and "out of stock" not in (o.availability or "").lower()]
        current_low = min(valid_offers) if valid_offers else None

    # Check whether any genuine live data exists in the points
    has_verified = any(p.data_status == "live_verified" for p in points)
    history_status = "VERIFIED" if has_verified else "DEMO"
    is_simulated = not has_verified

    disclaimer = (
        "Simulated Catalog History (DEMO): Price movements and historical lows represent illustrative "
        "sample data for platform testing and demonstration. They do not reflect verified live retail observations."
        if is_simulated else
        "Verified Historical Market Data: Captured from authenticated live retailer observations."
    )

    point_dtos = [
        PricePointDto(
            id=p.id,
            offer_id=p.offer_id,
            price=p.price,
            currency=p.currency,
            recorded_at=p.recorded_at,
            data_source=p.data_source,
            data_status=p.data_status,
        )
        for p in points
    ]

    return ProductPriceAnalyticsResponse(
        product_id=product.id,
        product_slug=product.slug or f"product-{product.id}",
        product_title=product.title,
        window_days=window_days,
        points=point_dtos,
        lowest_recorded_price=summary.min_price,
        highest_recorded_price=summary.max_price,
        average_recorded_price=summary.avg_price,
        current_lowest_price=current_low,
        price_movement_pct=movement,
        price_trend=trend,
        observation_count=summary.observation_count,
        is_sufficient_history=summary.is_sufficient_history,
        currency="INR",
        history_data_status=history_status,
        is_simulated=is_simulated,
        disclaimer=disclaimer,
    )


# =============================================================================
# 3. Transparent Deal Scoring Engine
# =============================================================================

@dataclass
class DealFactorExplanation:
    """Individual factor contributing to the deal score."""
    factor_name: str
    points_awarded: float
    max_points: float
    explanation: str


@dataclass
class DealIntelligenceScore:
    """Complete transparent deal score analysis."""
    product_id: int
    product_title: str
    retailer_name: str
    current_price: float
    deal_score: int  # 0 to 100
    deal_grade: str  # "A+", "A", "B", "C", "D"
    deal_classification: str  # "Exceptional Value", "Great Value", "Fair Market", "Above Market"
    is_simulated_deal: bool  # True for all DEMO data
    source_status: str  # "DEMO", "LIVE_VERIFIED", "MANUAL_VERIFIED"
    verified_deal_eligible: bool  # False for DEMO data
    confidence_score: float  # 0.0 to 1.0
    factors: List[DealFactorExplanation]
    landed_cost_breakdown: TotalPurchaseCostBreakdown
    summary_verdict: str


def calculate_deal_score(
    product_id: int,
    current_price: float,
    reference_mrp: Optional[float] = None,
    historical_low: Optional[float] = None,
    shipping_fee: Optional[float] = None,
    is_shipping_disclosed: bool = True,
    coupon_discount: float = 0.0,
    source_type: str = "demo",
    retailer_name: str = "Retailer",
    product_title: str = "Product",
    coupon_code: Optional[str] = None,
) -> DealIntelligenceScore:
    """
    Transparent, explainable deal scoring algorithm (0 to 100 points).
    
    Factors:
    1. Discount vs MRP / Baseline (0-35 points)
    2. Proximity to Historical Low (0-25 points)
    3. Landed Cost & Shipping Disclosure (0-15 points)
    4. Promotional & Coupon Value (0-10 points)
    5. Source Reliability & Confidence (0-15 points)
    
    MANDATORY RULE:
    Do not award a genuine deal classification to DEMO data.
    DEMO data receives an explicit '(Simulated)' label and verified_deal_eligible=False.
    """
    factors: List[DealFactorExplanation] = []
    total_score = 0.0

    # 1. Discount vs MRP (0 - 35 points)
    discount_pts = 0.0
    if reference_mrp and reference_mrp > current_price:
        savings_pct = ((reference_mrp - current_price) / reference_mrp) * 100.0
        if savings_pct >= 40:
            discount_pts = 35.0
        elif savings_pct >= 25:
            discount_pts = 28.0
        elif savings_pct >= 15:
            discount_pts = 20.0
        elif savings_pct >= 5:
            discount_pts = 12.0
        else:
            discount_pts = 5.0
        factors.append(DealFactorExplanation(
            factor_name="Discount vs Reference MRP",
            points_awarded=discount_pts,
            max_points=35.0,
            explanation=f"Discount of {savings_pct:.1f}% relative to product reference MRP of ₹{reference_mrp:.0f}.",
        ))
    else:
        discount_pts = 10.0
        factors.append(DealFactorExplanation(
            factor_name="Discount vs Reference MRP",
            points_awarded=10.0,
            max_points=35.0,
            explanation="Product listed at baseline reference price with no standard percentage markdown.",
        ))
    total_score += discount_pts

    # 2. Historical Position (0 - 25 points)
    hist_pts = 0.0
    if historical_low and historical_low > 0:
        ratio = current_price / historical_low
        if ratio <= 1.02:  # At or within 2% of recorded low
            hist_pts = 25.0
            hist_exp = f"Price is matching or within 2% of the 90-day recorded low (₹{historical_low:.0f})."
        elif ratio <= 1.10:
            hist_pts = 18.0
            hist_exp = f"Price is within 10% of the 90-day recorded low (₹{historical_low:.0f})."
        elif ratio <= 1.25:
            hist_pts = 10.0
            hist_exp = f"Price is moderately above the recorded low (₹{historical_low:.0f})."
        else:
            hist_pts = 5.0
            hist_exp = f"Price is significantly higher than historical recorded minimum of ₹{historical_low:.0f}."
    else:
        hist_pts = 14.0
        hist_exp = "Insufficient recorded price history; awarded neutral historical baseline score."
    factors.append(DealFactorExplanation(
        factor_name="Historical Price Position",
        points_awarded=hist_pts,
        max_points=25.0,
        explanation=hist_exp,
    ))
    total_score += hist_pts

    # 3. Shipping & Landed Cost Disclosure (0 - 15 points)
    ship_pts = 0.0
    if not is_shipping_disclosed or shipping_fee is None:
        ship_pts = 2.0
        ship_exp = "Retailer shipping cost is undisclosed. Risk of unexpected delivery fees at checkout."
    elif shipping_fee == 0.0:
        ship_pts = 15.0
        ship_exp = "Free shipping disclosed with no additional delivery surcharge."
    elif shipping_fee <= 50.0:
        ship_pts = 10.0
        ship_exp = f"Reasonable disclosed delivery charge (+ ₹{shipping_fee:.0f})."
    else:
        ship_pts = 5.0
        ship_exp = f"High delivery fee (+ ₹{shipping_fee:.0f}) reduces landed purchase value."
    factors.append(DealFactorExplanation(
        factor_name="Landed Delivery Transparency",
        points_awarded=ship_pts,
        max_points=15.0,
        explanation=ship_exp,
    ))
    total_score += ship_pts

    # 4. Coupon Applicability (0 - 10 points)
    coupon_pts = 0.0
    if coupon_discount > 0:
        coupon_pts = min(10.0, 5.0 + (coupon_discount / 20.0))
        coupon_exp = f"[Simulated] Test promo coupon applies hypothetical ₹{coupon_discount:.0f} deduction. Terms unverified with retailer."
    else:
        coupon_pts = 4.0
        coupon_exp = "No test coupon applied. Retailer promotion terms unverified."
    factors.append(DealFactorExplanation(
        factor_name="Promotional Coupon Factor",
        points_awarded=round(coupon_pts, 1),
        max_points=10.0,
        explanation=coupon_exp,
    ))
    total_score += coupon_pts

    # 5. Data Reliability & Source Confidence (0 - 15 points)
    is_live = (source_type.lower() == "live_verified")
    is_manual = (source_type.lower() == "manual_verified")
    source_pts = 0.0

    if is_live:
        source_pts = 15.0
        confidence = 0.95
        source_exp = "Verified live observation authenticated via authorized retailer feed."
    elif is_manual:
        source_pts = 12.0
        confidence = 0.85
        source_exp = "Manual human verification supported by source evidence."
    else:
        source_pts = 8.0
        confidence = 0.50
        source_exp = "Demo catalog data. Deal score is simulated for platform evaluation; no live market evidence authenticated."

    factors.append(DealFactorExplanation(
        factor_name="Data Reliability & Evidence",
        points_awarded=source_pts,
        max_points=15.0,
        explanation=source_exp,
    ))
    total_score += source_pts

    final_score = int(round(total_score))
    final_score = max(0, min(100, final_score))

    # Grade and Classification
    is_simulated = not is_live and not is_manual
    prefix = " (Simulated)" if is_simulated else ""

    if final_score >= 85:
        grade = "A+"
        classification = f"Exceptional Value{prefix}"
    elif final_score >= 70:
        grade = "A"
        classification = f"Great Value{prefix}"
    elif final_score >= 50:
        grade = "B"
        classification = f"Fair Market Price{prefix}"
    else:
        grade = "C"
        classification = f"Above Market{prefix}"

    verdict = (
        f"Simulated Score ({final_score}/100, Grade {grade}): {classification}. Based on demo catalog data; "
        "not an authenticated live market deal."
        if is_simulated else
        f"Verified Score ({final_score}/100, Grade {grade}): {classification}. Supported by verified market evidence."
    )

    landed = calculate_total_purchase_cost(
        product_price=current_price,
        shipping_fee=shipping_fee,
        is_shipping_disclosed=is_shipping_disclosed,
        coupon_code=coupon_code,
        reference_mrp=reference_mrp,
        retailer_name=retailer_name,
        data_status="demo" if is_simulated else "live_verified",
    )

    return DealIntelligenceScore(
        product_id=product_id,
        product_title=product_title,
        retailer_name=retailer_name,
        current_price=round(current_price, 2),
        deal_score=final_score,
        deal_grade=grade,
        deal_classification=classification,
        is_simulated_deal=is_simulated,
        source_status="DEMO" if is_simulated else ("LIVE_VERIFIED" if is_live else "MANUAL_VERIFIED"),
        verified_deal_eligible=(not is_simulated),
        confidence_score=confidence,
        factors=factors,
        landed_cost_breakdown=landed,
        summary_verdict=verdict,
    )


# =============================================================================
# 4. Price Alerts & Tracking Service Wrapper
# =============================================================================

@dataclass
class PriceTrackingItemDto:
    """DTO for active price tracking records."""
    id: int
    user_id: int
    product_id: int
    product_title: str
    target_price: float
    current_price: float
    status: str
    alert_trigger_type: str
    note: Optional[str]
    created_at: str
    last_observed_price: Optional[float]
    last_alert_at: Optional[str]


@dataclass
class PriceAlertDto:
    """DTO for price alerts with user data isolation."""
    id: int
    user_id: int
    product_id: int
    product_title: str
    alert_type: str
    observed_price: float
    previous_price: Optional[float]
    target_price: float
    message: str
    created_at: str
    is_read: bool
    is_demo: bool = True


def get_user_tracking_records(user_id: int, custom_path: Optional[str] = None) -> List[PriceTrackingItemDto]:
    """Retrieve active price tracking records for a specific authenticated user."""
    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pt.*, p.title as product_title, p.brand as product_brand
            FROM price_tracking pt
            JOIN products p ON pt.product_id = p.id
            WHERE pt.user_id = ?
            ORDER BY pt.created_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()

    results = []
    for r in rows:
        results.append(
            PriceTrackingItemDto(
                id=r["id"],
                user_id=r["user_id"],
                product_id=r["product_id"],
                product_title=r["product_title"],
                target_price=float(r["target_price"]),
                current_price=float(r["last_observed_price"] or r["target_price"]),
                status=r["status"] or "active",
                alert_trigger_type=r["alert_trigger_type"] or "target_or_drop",
                note=r["note"],
                created_at=str(r["created_at"]),
                last_observed_price=float(r["last_observed_price"]) if r["last_observed_price"] else None,
                last_alert_at=str(r["last_alert_at"]) if r["last_alert_at"] else None,
            )
        )
    return results


def get_user_price_alerts_list(user_id: int, unread_only: bool = False, custom_path: Optional[str] = None) -> List[PriceAlertDto]:
    """Retrieve price alerts for an authenticated user with strict user isolation."""
    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        sql = """
            SELECT pa.*, p.title as product_title
            FROM price_alerts pa
            JOIN products p ON pa.product_id = p.id
            WHERE pa.user_id = ?
        """
        params = [user_id]
        if unread_only:
            sql += " AND pa.is_read = 0"
        sql += " ORDER BY pa.created_at DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    alerts = []
    for r in rows:
        alerts.append(
            PriceAlertDto(
                id=r["id"],
                user_id=r["user_id"],
                product_id=r["product_id"],
                product_title=r["product_title"],
                alert_type=r["alert_type"],
                observed_price=float(r["observed_price"]),
                previous_price=float(r["previous_price"]) if r["previous_price"] else None,
                target_price=float(r["target_price"]),
                message=r["message"],
                created_at=str(r["created_at"]),
                is_read=bool(r["is_read"]),
                is_demo=True,  # All demo catalog alerts are demo
            )
        )
    return alerts
