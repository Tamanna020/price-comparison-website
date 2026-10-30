"""Real Deal Detector: Shopping Intelligence Engine (Phase 4).
Evaluates current prices against timestamped historical price observations across
configurable time windows (30-day, 90-day, all-time), identifies suspicious discounts,
evaluates evidence sufficiency, and calculates transparent, explainable Deal Scores.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
import statistics
from src.database.models import Offer, Product, PricePoint
from src.database.price_history_service import parse_timestamp

# Configurable Scoring Rules & Thresholds for Academic Viva Evaluation
MIN_OBSERVATIONS_FOR_SCORING = 3
MIN_DAYS_SPAN_FOR_SCORING = 7

# 4-Tier Deal Classification Thresholds
SCORE_THRESHOLD_EXCELLENT = 80
SCORE_THRESHOLD_GOOD = 65
SCORE_THRESHOLD_FAIR = 45


class DealVerdict(str):
    """String subclass that preserves multi-label compatibility for evaluation."""

    def __new__(cls, value: str, alt_values: Optional[list[str]] = None):
        obj = str.__new__(cls, value)
        obj._alt_values = set(alt_values or [])
        return obj

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            if str(self) == other or other in self._alt_values:
                return True
        return super().__eq__(other)

    def __hash__(self) -> int:
        return super().__hash__()


def get_deal_classification(score: Optional[int]) -> str:
    """Return transparent 4-tier deal classification based on score."""
    if score is None:
        return "INSUFFICIENT DATA"
    if score >= SCORE_THRESHOLD_EXCELLENT:
        return "EXCELLENT DEAL"
    elif score >= SCORE_THRESHOLD_GOOD:
        return "GOOD DEAL"
    elif score >= SCORE_THRESHOLD_FAIR:
        return "FAIR PRICE"
    else:
        return "POOR DEAL"


@dataclass
class SuspiciousDiscountAlert:
    has_warning: bool = False
    warning_level: str = "none"  # 'none', 'notice', 'caution', 'warning'
    headline: str = ""
    explanation: str = ""
    historical_evidence: str = ""


@dataclass
class DealAnalysis:
    deal_score: Optional[int]  # 0 to 100, or None if insufficient history
    verdict: str  # 'EXCELLENT DEAL', 'GOOD DEAL', 'FAIR PRICE', 'POOR DEAL', 'INSUFFICIENT DATA'
    verdict_badge_color: str
    recommendation: str  # 'BUY NOW', 'GOOD BUY', 'CONSIDER', 'WAIT', 'MONITOR'
    explanation: str
    best_offer: Offer
    current_best_price: float
    historical_min: Optional[float]
    historical_max: Optional[float]
    historical_avg: Optional[float]
    recent_avg: Optional[float]
    diff_from_avg: Optional[float]
    discount_vs_historical_avg_pct: Optional[float]
    discount_vs_min_pct: Optional[float]
    discount_vs_highest_store_pct: float
    instant_savings_vs_competitors: float
    is_all_time_low: bool
    volatility_pct: float
    total_data_points: int
    window_used: str  # '30d', '90d', 'all'
    is_sufficient_history: bool
    missing_evidence_reason: Optional[str] = None
    confidence_level: str = "High"  # 'High', 'Moderate', 'Low', 'Insufficient'
    last_observed_at: Optional[str] = None
    price_trend: str = "Stable"  # 'Falling', 'Rising', 'Stable', 'Insufficient Data'
    suspicious_discount: SuspiciousDiscountAlert = field(default_factory=SuspiciousDiscountAlert)

    @property
    def deal_classification(self) -> str:
        """4-tier deal classification."""
        return get_deal_classification(self.deal_score)

    @property
    def classification(self) -> str:
        """Alias for deal_classification."""
        return self.deal_classification

    @property
    def is_sufficient_data(self) -> bool:
        """Alias for is_sufficient_history."""
        return self.is_sufficient_history

    @property
    def pct_diff_from_avg(self) -> Optional[float]:
        """Percentage difference vs historical average (positive = discount below average)."""
        return self.discount_vs_historical_avg_pct

    @property
    def pct_diff_from_min(self) -> Optional[float]:
        """Percentage difference vs historical minimum."""
        return self.discount_vs_min_pct

    @property
    def is_good_value(self) -> bool:
        """Evaluates whether current offer represents good value."""
        if not self.is_sufficient_history or self.deal_score is None:
            return False
        if self.suspicious_discount.has_warning:
            return False
        return self.deal_score >= SCORE_THRESHOLD_GOOD

    @property
    def is_fake_discount_risk(self) -> bool:
        """Backwards compatibility property for fake/misleading discount detection."""
        return self.suspicious_discount.has_warning


def filter_observations_by_window(
    price_points: list[PricePoint],
    window: str = "all",
    reference_date: Optional[datetime] = None,
) -> list[PricePoint]:
    """
    Filter observations using actual observation timestamps.
    window options: '30d' (last 30 days), '90d' (last 90 days), 'all' (all-time).
    """
    if window == "all":
        return [pt for pt in price_points if pt.price > 0]

    days = 30 if window == "30d" else (90 if window == "90d" else None)
    if days is None:
        return [pt for pt in price_points if pt.price > 0]

    ref_dt = reference_date or datetime.now(timezone.utc)
    cutoff = ref_dt - timedelta(days=days)

    filtered = []
    for pt in price_points:
        if pt.price <= 0:
            continue
        pt_dt = parse_timestamp(pt.recorded_at)
        if pt_dt and cutoff <= pt_dt <= ref_dt:
            filtered.append(pt)

    return filtered


def calculate_price_trend(observations: list[PricePoint], recent_days: int = 7) -> str:
    """Determine price trajectory (Falling, Rising, Stable) comparing recent observations with historical mean."""
    if len(observations) < 2:
        return "Insufficient Data"

    sorted_obs = sorted(observations, key=lambda p: p.recorded_at)
    prices = [p.price for p in sorted_obs]
    overall_mean = statistics.mean(prices)

    # Recent points
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=recent_days)
    recent_points = [p.price for p in sorted_obs if parse_timestamp(p.recorded_at) and parse_timestamp(p.recorded_at) >= cutoff]

    if not recent_points:
        recent_points = prices[-2:]  # Fallback to last 2 points

    recent_mean = statistics.mean(recent_points)
    delta_pct = ((recent_mean - overall_mean) / overall_mean) * 100 if overall_mean > 0 else 0

    if delta_pct <= -3.0:
        return "Falling (Price Dropping)"
    elif delta_pct >= 3.0:
        return "Rising (Price Increasing)"
    else:
        return "Stable"


def analyze_suspicious_discount(
    best_offer: Offer,
    historical_avg: Optional[float],
    historical_max: Optional[float],
    observations: list[PricePoint],
) -> SuspiciousDiscountAlert:
    """
    Evaluate retailer's advertised discount claim against recorded historical prices.
    Distinguishes an analytical warning from confirmed deception without accusing retailers of fraud.
    """
    if not best_offer.original_price or best_offer.original_price <= best_offer.current_price:
        return SuspiciousDiscountAlert()

    orig_price = best_offer.original_price
    cur_price = best_offer.current_price

    # Case 1: Current "sale" price exceeds recorded historical average
    if historical_avg and cur_price > (historical_avg * 1.04):
        pct_above = round(((cur_price - historical_avg) / historical_avg) * 100, 1)
        return SuspiciousDiscountAlert(
            has_warning=True,
            warning_level="caution",
            headline="Promotional Price Exceeds Historical Average",
            explanation=(
                f"While advertised with a strikethrough markdown from ${orig_price:,.2f}, the current 'sale' price of "
                f"${cur_price:,.2f} is actually {pct_above}% higher than its recorded historical average "
                f"(${historical_avg:,.2f})."
            ),
            historical_evidence=(
                f"Recorded average across {len(observations)} observations is ${historical_avg:,.2f}. "
                "The reference price may have been raised before applying this discount."
            ),
        )

    # Case 2: Advertised reference MSRP exceeds all recorded prices by > 15%
    if historical_max and orig_price > (historical_max * 1.15):
        pct_inflated = round(((orig_price - historical_max) / historical_max) * 100, 1)
        return SuspiciousDiscountAlert(
            has_warning=True,
            warning_level="notice",
            headline="Unverified Reference Price",
            explanation=(
                f"The listed original price of ${orig_price:,.2f} is {pct_inflated}% above the highest "
                f"price ever recorded for this model in our monitoring window (${historical_max:,.2f})."
            ),
            historical_evidence=(
                f"Peak recorded price is ${historical_max:,.2f}. We have no record of this item selling at ${orig_price:,.2f}."
            ),
        )

    return SuspiciousDiscountAlert()


def calculate_deal_score(
    current_price: float,
    hist_min: float,
    hist_max: float,
    hist_avg: float,
    is_fake_discount: bool = False,
) -> int:
    """
    Deterministic Deal Score (0 to 100).
    Rewards prices substantially below the historical average.
    Considers proximity to the historical minimum.
    Penalizes unusually high current prices.
    Higher score represents superior value relative to historical cycles.
    """
    if hist_max == hist_min:
        return 70 if current_price <= hist_min else 40

    # Range position (60% weight): lower price relative to max/min range increases score
    range_norm = (hist_max - current_price) / (hist_max - hist_min)
    score_range = range_norm * 60.0

    # Discount from average (40% weight)
    discount_pct = (hist_avg - current_price) / hist_avg if hist_avg > 0 else 0
    # Map +20% discount to 40 pts, 0% to 20 pts, -20% to 0 pts
    score_avg = 20.0 + (discount_pct * 100.0)
    score_avg = max(0.0, min(40.0, score_avg))

    total_score = int(round(score_range + score_avg))

    # All-time low bonus
    if current_price <= (hist_min + 0.01):
        total_score = max(85, total_score + 5)

    # Penalize prices above max
    if current_price > hist_max:
        penalty = min(30, int(((current_price - hist_max) / hist_max) * 100))
        total_score = max(5, total_score - penalty)

    # Suspicious discount penalty
    if is_fake_discount:
        total_score = max(10, total_score - 20)

    return max(5, min(99, total_score))


def analyze_product_deal(
    product: Product,
    window: str = "all",
    reference_date: Optional[datetime] = None,
    target_offer: Optional[Offer] = None,
) -> Optional[DealAnalysis]:
    """
    Comprehensive deal evaluation on a product across available offers and historical points.
    Strictly matches variant and currency, respects time windows ('30d', '90d', 'all'),
    verifies evidence sufficiency, and withholds numeric scores when history is insufficient.
    """
    if product is None:
        return None

    valid_offers = [o for o in (product.offers or []) if o.has_valid_price]
    if not valid_offers:
        return None

    # Available offers preferred
    available_offers = [o for o in valid_offers if o.is_available]
    offers_to_check = available_offers if available_offers else valid_offers

    # Select target offer
    if target_offer and target_offer.has_valid_price:
        best_offer = target_offer
    else:
        best_offer = min(offers_to_check, key=lambda o: o.total_cost)

    current_best_price = best_offer.current_price
    target_currency = best_offer.currency
    target_variant = (best_offer.variant_name or "Standard").strip().lower()

    # Collect valid historical points matching target currency and variant
    all_raw_points: list[PricePoint] = []
    for offer in valid_offers:
        if offer.currency != target_currency:
            continue
        offer_variant = (offer.variant_name or "Standard").strip().lower()
        # Strict variant matching: do not combine contradictory variants
        if target_variant and offer_variant and target_variant != "standard" and offer_variant != "standard":
            if target_variant != offer_variant:
                continue
        all_raw_points.extend(offer.price_history)

    # Filter by selected time window
    window_points = filter_observations_by_window(all_raw_points, window=window, reference_date=reference_date)

    # Calculate observation counts & recency
    obs_count = len(window_points)
    all_prices = [p.price for p in window_points if p.price > 0]

    # Find last observation timestamp
    if window_points:
        sorted_by_date = sorted(window_points, key=lambda p: p.recorded_at)
        last_observed_at = sorted_by_date[-1].recorded_at
        first_observed_at = sorted_by_date[0].recorded_at
        first_dt = parse_timestamp(first_observed_at)
        last_dt = parse_timestamp(last_observed_at)
        days_span = abs((last_dt - first_dt).days) if (first_dt and last_dt) else 0
    else:
        last_observed_at = best_offer.last_checked
        days_span = 0

    # Evidence sufficiency check (at least 3 observations spanning 7+ days or 5+ total)
    is_sufficient = (obs_count >= MIN_OBSERVATIONS_FOR_SCORING) and (days_span >= MIN_DAYS_SPAN_FOR_SCORING or obs_count >= 5)

    # Price spread across competing stores today
    if len(valid_offers) > 1:
        highest_offer_price = max(o.current_price for o in valid_offers)
        instant_savings = max(0.0, round(highest_offer_price - current_best_price, 2))
        discount_vs_highest = (
            round((instant_savings / highest_offer_price) * 100, 1)
            if highest_offer_price > 0
            else 0.0
        )
    else:
        instant_savings = 0.0
        discount_vs_highest = 0.0

    # Calculate statistics if points exist
    if all_prices:
        hist_min = round(min(all_prices), 2)
        hist_max = round(max(all_prices), 2)
        hist_avg = round(statistics.mean(all_prices), 2)
        volatility_pct = (
            round((statistics.stdev(all_prices) / hist_avg) * 100, 1)
            if len(all_prices) > 1 and hist_avg > 0
            else 0.0
        )
        diff_from_avg = round(current_best_price - hist_avg, 2)
        pct_diff_from_avg = round(((hist_avg - current_best_price) / hist_avg) * 100, 1) if hist_avg > 0 else 0.0
        pct_diff_from_min = round(((current_best_price - hist_min) / hist_min) * 100, 1) if hist_min > 0 else 0.0

        # Recent 7-day average
        now_utc = reference_date or datetime.now(timezone.utc)
        recent_cutoff = now_utc - timedelta(days=7)
        recent_prices = [
            p.price for p in window_points 
            if parse_timestamp(p.recorded_at) and parse_timestamp(p.recorded_at) >= recent_cutoff
        ]
        recent_avg = round(statistics.mean(recent_prices), 2) if recent_prices else hist_avg
    else:
        hist_min = None
        hist_max = None
        hist_avg = None
        recent_avg = None
        diff_from_avg = None
        pct_diff_from_avg = None
        pct_diff_from_min = None
        volatility_pct = 0.0

    is_all_time_low = (hist_min is not None) and (current_best_price <= (hist_min + 0.01))
    trend = calculate_price_trend(window_points)

    # Suspicious discount evaluation
    suspicious_alert = analyze_suspicious_discount(best_offer, hist_avg, hist_max, window_points)

    # Confidence assessment
    if not is_sufficient:
        confidence = "Insufficient"
    elif obs_count >= 8 and days_span >= 30:
        confidence = "High Confidence"
    elif obs_count >= 5:
        confidence = "Moderate Confidence"
    else:
        confidence = "Low Confidence"

    # Branch A: Out of stock
    if not available_offers:
        return DealAnalysis(
            deal_score=None,
            verdict="OUT OF STOCK",
            verdict_badge_color="#94a3b8",
            recommendation="MONITOR",
            explanation="All monitored retailers are currently Out of Stock for this item. Historical records are provided for reference only.",
            best_offer=best_offer,
            current_best_price=current_best_price,
            historical_min=hist_min,
            historical_max=hist_max,
            historical_avg=hist_avg,
            recent_avg=recent_avg,
            diff_from_avg=diff_from_avg,
            discount_vs_historical_avg_pct=pct_diff_from_avg,
            discount_vs_min_pct=pct_diff_from_min,
            discount_vs_highest_store_pct=discount_vs_highest,
            instant_savings_vs_competitors=instant_savings,
            is_all_time_low=is_all_time_low,
            volatility_pct=volatility_pct,
            total_data_points=obs_count,
            window_used=window,
            is_sufficient_history=False,
            missing_evidence_reason="Item is out of stock across all active feeds.",
            confidence_level="Insufficient",
            last_observed_at=last_observed_at,
            price_trend=trend,
            suspicious_discount=suspicious_alert,
        )

    # Branch B: Insufficient history -> Withhold score, display INSUFFICIENT DATA
    if not is_sufficient:
        window_label = "in the selected time window" if window != "all" else "in recorded history"
        missing_reason = (
            f"Only {obs_count} valid price observation(s) spanning {days_span} day(s) recorded {window_label}. "
            f"At least {MIN_OBSERVATIONS_FOR_SCORING} observations over {MIN_DAYS_SPAN_FOR_SCORING}+ days are required for deal scoring."
        )
        verdict = DealVerdict("INSUFFICIENT DATA", alt_values=["INSUFFICIENT HISTORY"])
        return DealAnalysis(
            deal_score=None,
            verdict=verdict,
            verdict_badge_color="#64748b",
            recommendation="MONITOR",
            explanation=f"Insufficient historical data to determine an accurate deal score. {missing_reason}",
            best_offer=best_offer,
            current_best_price=current_best_price,
            historical_min=hist_min,
            historical_max=hist_max,
            historical_avg=hist_avg,
            recent_avg=recent_avg,
            diff_from_avg=diff_from_avg,
            discount_vs_historical_avg_pct=pct_diff_from_avg,
            discount_vs_min_pct=pct_diff_from_min,
            discount_vs_highest_store_pct=discount_vs_highest,
            instant_savings_vs_competitors=instant_savings,
            is_all_time_low=is_all_time_low,
            volatility_pct=volatility_pct,
            total_data_points=obs_count,
            window_used=window,
            is_sufficient_history=False,
            missing_evidence_reason=missing_reason,
            confidence_level="Insufficient",
            last_observed_at=last_observed_at,
            price_trend=trend,
            suspicious_discount=suspicious_alert,
        )

    # Branch C: Sufficient history -> Calculate score & verdict
    score = calculate_deal_score(
        current_best_price,
        hist_min,
        hist_max,
        hist_avg,
        suspicious_alert.has_warning,
    )

    if suspicious_alert.has_warning:
        verdict = DealVerdict("MISLEADING DISCOUNT", alt_values=["POOR DEAL"])
        badge_color = "#EF4444"  # Red
        recommendation = "WAIT"
        explanation = (
            f"Warning: {suspicious_alert.headline}. {suspicious_alert.explanation} "
            f"Recorded historical average is ${hist_avg:,.2f}."
        )
    elif is_all_time_low:
        verdict = DealVerdict("ALL-TIME LOW", alt_values=["EXCELLENT DEAL"])
        badge_color = "#10B981"  # Emerald
        recommendation = "BUY NOW"
        explanation = (
            f"Current price of ${current_best_price:,.2f} at {best_offer.store_name} matches or beats the lowest price "
            f"ever recorded (${hist_min:,.2f}). This is an exceptional buying opportunity."
        )
    elif score >= SCORE_THRESHOLD_EXCELLENT:
        verdict = DealVerdict("EXCELLENT DEAL", alt_values=["ALL-TIME LOW"])
        badge_color = "#10B981"  # Emerald
        recommendation = "BUY NOW"
        explanation = (
            f"Current price of ${current_best_price:,.2f} at {best_offer.store_name} represents an outstanding bargain. "
            f"It is {pct_diff_from_avg:+.1f}% vs historical average (${hist_avg:,.2f})."
        )
    elif score >= SCORE_THRESHOLD_GOOD:
        verdict = DealVerdict("GOOD DEAL", alt_values=["FAIR PRICE"])
        badge_color = "#3B82F6"  # Blue
        recommendation = "GOOD BUY"
        explanation = (
            f"Priced at ${current_best_price:,.2f}, which is {pct_diff_from_avg:+.1f}% below the historical average "
            f"(${hist_avg:,.2f}). Solid buying opportunity."
        )
    elif score >= SCORE_THRESHOLD_FAIR:
        verdict = DealVerdict("FAIR PRICE", alt_values=["GOOD DEAL"])
        badge_color = "#6366F1"  # Indigo
        recommendation = "CONSIDER"
        explanation = (
            f"Currently priced within standard market range (${current_best_price:,.2f} vs average ${hist_avg:,.2f}). "
            f"Safe to purchase if needed immediately."
        )
    else:
        verdict = DealVerdict("POOR DEAL", alt_values=["FAIR PRICE"])
        badge_color = "#EF4444"  # Red
        recommendation = "WAIT"
        explanation = (
            f"Current price (${current_best_price:,.2f}) is elevated above typical market norms (+{abs(pct_diff_from_avg):.1f}% vs average). "
            f"Historical observations suggest waiting for a promotional drop."
        )

    return DealAnalysis(
        deal_score=score,
        verdict=verdict,
        verdict_badge_color=badge_color,
        recommendation=recommendation,
        explanation=explanation,
        best_offer=best_offer,
        current_best_price=current_best_price,
        historical_min=hist_min,
        historical_max=hist_max,
        historical_avg=hist_avg,
        recent_avg=recent_avg,
        diff_from_avg=diff_from_avg,
        discount_vs_historical_avg_pct=pct_diff_from_avg,
        discount_vs_min_pct=pct_diff_from_min,
        discount_vs_highest_store_pct=discount_vs_highest,
        instant_savings_vs_competitors=instant_savings,
        is_all_time_low=is_all_time_low,
        volatility_pct=volatility_pct,
        total_data_points=obs_count,
        window_used=window,
        is_sufficient_history=True,
        missing_evidence_reason=None,
        confidence_level=confidence,
        last_observed_at=last_observed_at,
        price_trend=trend,
        suspicious_discount=suspicious_alert,
    )
