"""Automatic Live Retailer Price Comparison Engine for PriceWise AI Beauty (Phase 6).

Coordinates:
1. Product identification & query generation via GeminiService.
2. Independent modular retailer adapters (Nykaa, Myntra, Purplle, Tira, Amazon).
3. Browser automation via Playwright with SSRF protection and resource blocking.
4. Multi-factor variant validation via evaluate_product_match (30ml != 50ml).
5. Lowest listed price vs lowest total purchase cost calculation.
6. Timestamped observation persistence in SQLite & deal detection.
7. Request deduplication and freshness caching (10-minute TTL).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Optional
from urllib.parse import urlparse

from src.adapters.base_adapter import (
    BaseRetailerAdapter,
    ExtractedPriceResult,
    CapabilityStatus,
)
from src.adapters.registry import get_adapter_registry
from src.database.connection import get_connection
from src.database.price_history_service import record_price_observation
from src.services.gemini_service import get_gemini_service
from src.services.product_matching_service import evaluate_product_match, MatchClassification
from src.services.product_service import get_product_by_slug, get_product_by_id
from src.workers.browser_manager import BrowserManager, BrowserSecurityError
from src.workers.security_policy import validate_browser_url

logger = logging.getLogger("pricewise.engine")

# Freshness window in seconds (10 minutes)
CACHE_TTL_SECONDS = 600


@dataclass
class LiveRetailerOfferItem:
    """Individual retailer price comparison offer presented to the user."""
    retailer_name: str
    store_id: str
    status: str  # "retrieved", "unavailable", "unsupported", "restricted", "mismatch"
    listed_price: Optional[float] = None
    mrp: Optional[float] = None
    discount_pct: float = 0.0
    shipping_fee: Optional[float] = None
    is_shipping_disclosed: bool = True
    coupon_code: Optional[str] = None
    coupon_discount: float = 0.0
    total_cost: Optional[float] = None
    stock_status: str = "In Stock"
    in_stock: bool = True
    purchase_url: str = ""
    variant_detected: Optional[str] = None
    match_classification: str = "verified_match"
    is_lowest_listed: bool = False
    is_lowest_total: bool = False
    source_type: str = "verified_live"  # "verified_live", "cached", "demo", "unavailable"
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validation_notes: Optional[str] = None


@dataclass
class LiveComparisonSummary:
    """Aggregated price comparison intelligence across all checked retailers."""
    lowest_listed_price: Optional[float] = None
    lowest_listed_retailer: Optional[str] = None
    lowest_total_cost: Optional[float] = None
    lowest_total_retailer: Optional[str] = None
    retailers_checked: int = 0
    retailers_retrieved: int = 0
    retailers_unavailable: int = 0
    retailers_unsupported: int = 0
    retailers_restricted: int = 0
    cheapest_savings_amount: float = 0.0
    cheapest_savings_percent: float = 0.0


@dataclass
class LiveComparisonResult:
    """Complete response payload for an automatic live price comparison check."""
    product_id: Optional[int]
    product_title: str
    brand: str
    target_variant: str
    is_cached: bool
    freshness_seconds: int
    retrieval_timestamp: str
    offers: list[LiveRetailerOfferItem]
    summary: LiveComparisonSummary

    @property
    def status(self) -> str:
        """Aggregate comparison status from individual retailer results.

        Returns:
            "retrieved"       — at least one verified live offer with price
            "unavailable"     — no offers could be retrieved
            "restricted"      — all offers blocked by retailer access restrictions
            "unsupported"     — all retailers unsupported for this product
            "partial"         — mixed results (some retrieved, some not)
        """
        if not self.offers:
            return "unavailable"

        statuses = {o.status for o in self.offers}
        if "retrieved" in statuses:
            if len(statuses) == 1:
                return "retrieved"
            return "partial"
        if statuses == {"restricted"}:
            return "restricted"
        if statuses == {"unsupported"}:
            return "unsupported"
        if statuses == {"unavailable"}:
            return "unavailable"
        return "partial"


class LiveComparisonEngine:
    """
    Core engine managing live retailer extraction, rate limiting, and verification.
    """

    def __init__(self, max_browser_workers: int = 2):
        self.max_browser_workers = max_browser_workers
        self.registry = get_adapter_registry()
        self.gemini_service = get_gemini_service()

        # In-memory freshness cache: cache_key -> (timestamp, LiveComparisonResult)
        self._cache: dict[str, tuple[float, LiveComparisonResult]] = {}
        self._lock = threading.Lock()
        self._in_flight: dict[str, threading.Event] = {}

    def _get_cache_key(self, product_id: Optional[int], slug: Optional[str]) -> str:
        return f"{product_id or 0}:{slug or 'unknown'}"

    def get_cached_comparison(self, cache_key: str) -> Optional[LiveComparisonResult]:
        """Return cached comparison if within TTL window."""
        with self._lock:
            entry = self._cache.get(cache_key)
            if not entry:
                return None
            cached_time, result = entry
            elapsed = time.time() - cached_time
            if elapsed < CACHE_TTL_SECONDS:
                result.is_cached = True
                result.freshness_seconds = int(elapsed)
                return result
            # Expired
            self._cache.pop(cache_key, None)
            return None

    def _set_cached_comparison(self, cache_key: str, result: LiveComparisonResult) -> None:
        with self._lock:
            self._cache[cache_key] = (time.time(), result)

    def log_check_audit(
        self,
        product_id: Optional[int],
        retailer_id: str,
        retailer_name: str,
        status: str,
        product_url: Optional[str] = None,
        listed_price: Optional[float] = None,
        mrp: Optional[float] = None,
        shipping_fee: Optional[float] = None,
        coupon_code: Optional[str] = None,
        coupon_discount: Optional[float] = None,
        total_cost: Optional[float] = None,
        variant_detected: Optional[str] = None,
        match_classification: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Persist check log into price_check_logs audit table."""
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO price_check_logs (
                        product_id, retailer_id, retailer_name, product_url,
                        status, listed_price, mrp, shipping_fee, coupon_code,
                        coupon_discount, total_cost, variant_detected,
                        match_classification, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        retailer_id,
                        retailer_name,
                        product_url,
                        status,
                        listed_price,
                        mrp,
                        shipping_fee,
                        coupon_code,
                        coupon_discount or 0.0,
                        total_cost,
                        variant_detected,
                        match_classification,
                        notes,
                    ),
                )
        except Exception as e:
            logger.warning(f"Failed to record price_check_log: {e}")

    def execute_live_comparison(
        self,
        product_id: Optional[int] = None,
        slug_or_id: Optional[str] = None,
        force_refresh: bool = False,
        mock_html_fixtures: Optional[dict[str, str]] = None,
    ) -> LiveComparisonResult:
        """
        Execute automatic live price comparison for a given catalog product.
        Checks cache first unless force_refresh is True.
        """
        # 1. Resolve product metadata
        product = None
        if product_id:
            product = get_product_by_id(product_id)
        if not product and slug_or_id:
            product = get_product_by_slug(slug_or_id)

        target_title = product.title if product else (slug_or_id or "Beauty Product")
        target_brand = product.brand if product else ""
        target_specs = product.specs if product else {}
        resolved_id = product.id if product else product_id

        # Target variant (e.g. 50ml, 30g, Standard)
        target_size = str(target_specs.get("Net Quantity") or target_specs.get("Size") or "")
        if not target_size and product:
            target_size = product.specs.get("Net Quantity", "Standard")

        cache_key = self._get_cache_key(resolved_id, slug_or_id)

        # 2. Check cache if not forcing refresh
        if not force_refresh:
            cached = self.get_cached_comparison(cache_key)
            if cached:
                return cached

        # 3. Deduplicate in-flight requests for the same product
        in_flight_event = None
        with self._lock:
            if cache_key in self._in_flight:
                in_flight_event = self._in_flight[cache_key]
            else:
                in_flight_event = threading.Event()
                self._in_flight[cache_key] = in_flight_event

        if in_flight_event and in_flight_event.is_set():
            cached = self.get_cached_comparison(cache_key)
            if cached:
                return cached

        try:
            # 4. Generate search query using GeminiService
            search_query = self.gemini_service.generate_search_query(
                brand=target_brand,
                product_name=target_title,
                size_volume=target_size,
            )

            # 5. Check each retailer adapter
            adapters = self.registry.list_all_unique_adapters()
            offer_items: list[LiveRetailerOfferItem] = []

            for adapter in adapters:
                offer_item = self._check_single_retailer(
                    adapter=adapter,
                    target_brand=target_brand,
                    target_title=target_title,
                    target_specs=target_specs,
                    search_query=search_query,
                    product_id=resolved_id,
                    mock_html=mock_html_fixtures.get(adapter.store_id) if mock_html_fixtures else None,
                )
                offer_items.append(offer_item)

            # 6. Calculate summary metrics (cheapest listed price vs cheapest total landed cost)
            summary = self._compute_summary(offer_items)

            result = LiveComparisonResult(
                product_id=resolved_id,
                product_title=target_title,
                brand=target_brand,
                target_variant=target_size or "Standard",
                is_cached=False,
                freshness_seconds=0,
                retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                offers=offer_items,
                summary=summary,
            )

            # 7. Store in cache & return
            self._set_cached_comparison(cache_key, result)
            return result

        finally:
            with self._lock:
                if cache_key in self._in_flight:
                    self._in_flight[cache_key].set()
                    self._in_flight.pop(cache_key, None)

    def _check_single_retailer(
        self,
        adapter: BaseRetailerAdapter,
        target_brand: str,
        target_title: str,
        target_specs: dict[str, Any],
        search_query: str,
        product_id: Optional[int],
        mock_html: Optional[str] = None,
    ) -> LiveRetailerOfferItem:
        """
        Check a single retailer with full error boundary and capability tracking.
        """
        store_id = getattr(adapter, "store_id", adapter.retailer_name.lower().replace(" ", "-"))

        # 1. Capability check
        if adapter.capability_status == CapabilityStatus.UNSUPPORTED:
            return LiveRetailerOfferItem(
                retailer_name=adapter.retailer_name,
                store_id=store_id,
                status="unsupported",
                source_type="unavailable",
                validation_notes="Automated extraction currently unsupported for this retailer",
            )

        # 2. Mock fixture execution (for fast deterministic tests)
        if mock_html is not None:
            extracted = adapter.extract_from_html(mock_html, f"https://www.{adapter.domain}/product/test")
            return self._process_extracted_result(
                adapter=adapter,
                extracted=extracted,
                target_brand=target_brand,
                target_title=target_title,
                target_specs=target_specs,
                product_id=product_id,
            )

        # 3. Live Playwright browser execution
        target_url = adapter.discover_product_url(
            product_name=target_title,
            brand=target_brand,
            search_query=search_query,
        )
        if not target_url:
            return LiveRetailerOfferItem(
                retailer_name=adapter.retailer_name,
                store_id=store_id,
                status="unavailable",
                source_type="unavailable",
                validation_notes="Product could not be resolved in retailer catalog",
            )

        # Validate URL against security policy
        is_safe, reason = validate_browser_url(target_url)
        if not is_safe:
            return LiveRetailerOfferItem(
                retailer_name=adapter.retailer_name,
                store_id=store_id,
                status="unsupported",
                source_type="unavailable",
                validation_notes=f"Security navigation policy rejected URL: {reason}",
            )

        try:
            with BrowserManager(headless=True, timeout_ms=8000) as bm:
                with bm.page_session() as page:
                    bm.safe_navigate(page, target_url, wait_until="domcontentloaded")
                    extracted = adapter.extract_live_price(page, target_url)

            return self._process_extracted_result(
                adapter=adapter,
                extracted=extracted,
                target_brand=target_brand,
                target_title=target_title,
                target_specs=target_specs,
                product_id=product_id,
            )

        except BrowserSecurityError as bse:
            logger.warning(f"Browser security blocked navigation to {adapter.retailer_name}: {bse}")
            return LiveRetailerOfferItem(
                retailer_name=adapter.retailer_name,
                store_id=store_id,
                status="unsupported",
                source_type="unavailable",
                validation_notes=str(bse),
            )
        except Exception as e:
            logger.info(f"Retailer check failed for {adapter.retailer_name}: {e}")
            self.log_check_audit(
                product_id=product_id,
                retailer_id=store_id,
                retailer_name=adapter.retailer_name,
                status="unavailable",
                product_url=target_url,
                notes=str(e),
            )
            return LiveRetailerOfferItem(
                retailer_name=adapter.retailer_name,
                store_id=store_id,
                status="unavailable",
                source_type="unavailable",
                validation_notes=f"Retailer feed currently unavailable ({type(e).__name__})",
            )

    def _process_extracted_result(
        self,
        adapter: BaseRetailerAdapter,
        extracted: ExtractedPriceResult,
        target_brand: str,
        target_title: str,
        target_specs: dict[str, Any],
        product_id: Optional[int],
    ) -> LiveRetailerOfferItem:
        """Validate variant matching, record persistence, and return offer item."""
        store_id = getattr(adapter, "store_id", adapter.retailer_name.lower().replace(" ", "-"))

        # Access restriction / CAPTCHA
        if extracted.verification_status == "restricted":
            self.log_check_audit(
                product_id=product_id,
                retailer_id=store_id,
                retailer_name=adapter.retailer_name,
                status="restricted",
                product_url=extracted.product_url,
                notes=extracted.validation_notes,
            )
            return LiveRetailerOfferItem(
                retailer_name=adapter.retailer_name,
                store_id=store_id,
                status="restricted",
                source_type="unavailable",
                purchase_url=extracted.product_url,
                validation_notes=extracted.validation_notes or "Access restricted by retailer bot protection",
            )

        # Unavailable
        if extracted.verification_status != "retrieved" or not extracted.listed_price or extracted.listed_price <= 0:
            self.log_check_audit(
                product_id=product_id,
                retailer_id=store_id,
                retailer_name=adapter.retailer_name,
                status="unavailable",
                product_url=extracted.product_url,
                notes=extracted.validation_notes,
            )
            return LiveRetailerOfferItem(
                retailer_name=adapter.retailer_name,
                store_id=store_id,
                status="unavailable",
                source_type="unavailable",
                purchase_url=extracted.product_url,
                validation_notes=extracted.validation_notes or "Product price not available on retailer page",
            )

        # Multi-factor variant matching check
        offer_title = extracted.product_name or target_title
        match_result = evaluate_product_match(
            target_brand=target_brand,
            target_title=target_title,
            target_specs=target_specs,
            offer_brand=target_brand,
            offer_title=offer_title,
            offer_variant=extracted.variant or "",
            offer_specs={"Size": extracted.product_size} if extracted.product_size else None,
        )

        if match_result.is_mismatch:
            self.log_check_audit(
                product_id=product_id,
                retailer_id=store_id,
                retailer_name=adapter.retailer_name,
                status="mismatch",
                product_url=extracted.product_url,
                listed_price=extracted.listed_price,
                variant_detected=extracted.variant or extracted.product_size,
                match_classification=match_result.match_classification,
                notes="; ".join(match_result.reasons),
            )
            return LiveRetailerOfferItem(
                retailer_name=adapter.retailer_name,
                store_id=store_id,
                status="mismatch",
                listed_price=extracted.listed_price,
                mrp=extracted.mrp,
                purchase_url=extracted.product_url,
                match_classification=match_result.match_classification,
                validation_notes=f"Variant mismatch: {'; '.join(match_result.reasons)}",
                source_type="unavailable",
            )

        # Verified live offer!
        discount = extracted.discount_pct
        total = extracted.total_cost

        # Record observation in SQLite price history if matched offer exists
        if product_id:
            self._persist_observation_if_offer_exists(
                product_id=product_id,
                store_id=store_id,
                price=extracted.listed_price,
            )

        self.log_check_audit(
            product_id=product_id,
            retailer_id=store_id,
            retailer_name=adapter.retailer_name,
            status="retrieved",
            product_url=extracted.product_url,
            listed_price=extracted.listed_price,
            mrp=extracted.mrp,
            shipping_fee=extracted.shipping_fee,
            coupon_code=extracted.coupon_code,
            coupon_discount=extracted.coupon_discount,
            total_cost=total,
            variant_detected=extracted.variant or extracted.product_size,
            match_classification=match_result.match_classification,
        )

        return LiveRetailerOfferItem(
            retailer_name=adapter.retailer_name,
            store_id=store_id,
            status="retrieved",
            listed_price=extracted.listed_price,
            mrp=extracted.mrp,
            discount_pct=discount,
            shipping_fee=extracted.shipping_fee,
            is_shipping_disclosed=extracted.is_shipping_disclosed,
            coupon_code=extracted.coupon_code,
            coupon_discount=extracted.coupon_discount,
            total_cost=total,
            stock_status=extracted.stock_status,
            in_stock=extracted.in_stock,
            purchase_url=extracted.product_url,
            variant_detected=extracted.variant or extracted.product_size,
            match_classification=match_result.match_classification,
            source_type="verified_live",
            retrieved_at=extracted.retrieved_at,
        )

    def _persist_observation_if_offer_exists(self, product_id: int, store_id: str, price: float) -> None:
        """Look up existing offer row in database and record price observation."""
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT o.id FROM offers o
                    JOIN stores s ON o.store_id = s.id
                    WHERE o.product_id = ? AND (LOWER(s.name) LIKE ? OR LOWER(s.domain) LIKE ?)
                    LIMIT 1
                    """,
                    (product_id, f"%{store_id}%", f"%{store_id}%"),
                )
                row = cur.fetchone()
                if row:
                    offer_id = row[0]
                    record_price_observation(
                        offer_id=offer_id,
                        price=price,
                        currency="INR",
                        data_source="live_browser_worker",
                        data_status="verified_live",
                    )
        except Exception as e:
            logger.warning(f"Could not link price observation to offer table: {e}")

    def _compute_summary(self, offers: list[LiveRetailerOfferItem]) -> LiveComparisonSummary:
        """Compute lowest listed price and lowest total purchase cost among verified offers."""
        retrieved_offers = [
            o for o in offers
            if o.status == "retrieved" and o.listed_price and o.listed_price > 0 and o.in_stock
        ]

        summary = LiveComparisonSummary(
            retailers_checked=len(offers),
            retailers_retrieved=len(retrieved_offers),
            retailers_unavailable=sum(1 for o in offers if o.status == "unavailable"),
            retailers_unsupported=sum(1 for o in offers if o.status == "unsupported"),
            retailers_restricted=sum(1 for o in offers if o.status == "restricted"),
        )

        if not retrieved_offers:
            return summary

        # 1. Lowest Listed Price
        cheapest_listed = min(retrieved_offers, key=lambda o: o.listed_price)
        summary.lowest_listed_price = cheapest_listed.listed_price
        summary.lowest_listed_retailer = cheapest_listed.retailer_name
        cheapest_listed.is_lowest_listed = True

        # 2. Lowest Total Purchase Cost (only where shipping is disclosed and known)
        offers_with_total = [o for o in retrieved_offers if o.total_cost is not None]
        if offers_with_total:
            cheapest_total = min(offers_with_total, key=lambda o: o.total_cost)
            summary.lowest_total_cost = cheapest_total.total_cost
            summary.lowest_total_retailer = cheapest_total.retailer_name
            cheapest_total.is_lowest_total = True

            # Calculate savings relative to highest total or highest listed
            max_cost = max(o.total_cost for o in offers_with_total)
            if max_cost > cheapest_total.total_cost:
                summary.cheapest_savings_amount = round(max_cost - cheapest_total.total_cost, 2)
                summary.cheapest_savings_percent = round((summary.cheapest_savings_amount / max_cost) * 100, 1)

        return summary

    def check_manual_url_price(
        self,
        url: str,
        mock_html: Optional[str] = None,
    ) -> ExtractedPriceResult:
        """
        Extract price from a user-submitted product URL.
        Enforces strict domain allowlisting and URL safety before navigation.
        """
        if not url or not isinstance(url, str):
            return ExtractedPriceResult(
                retailer_name="Unknown",
                store_id="unknown",
                product_url=str(url),
                verification_status="error",
                validation_notes="URL must be a non-empty string",
                source_type="unavailable",
            )

        clean_url = url.strip()
        is_safe, reason = validate_browser_url(clean_url)
        if not is_safe:
            return ExtractedPriceResult(
                retailer_name="Blocked",
                store_id="blocked",
                product_url=clean_url,
                verification_status="unsupported",
                validation_notes=f"Navigation blocked by security policy: {reason}",
                source_type="unavailable",
            )

        adapter = self.registry.get_adapter_by_url(clean_url)
        if not adapter:
            return ExtractedPriceResult(
                retailer_name="Unsupported",
                store_id="unsupported",
                product_url=clean_url,
                verification_status="unsupported",
                validation_notes="No retailer adapter found for domain",
                source_type="unavailable",
            )

        # Mock fixture mode
        if mock_html is not None:
            return adapter.extract_from_html(mock_html, clean_url)

        # Live navigation
        try:
            with BrowserManager(headless=True, timeout_ms=8000) as bm:
                with bm.page_session() as page:
                    bm.safe_navigate(page, clean_url, wait_until="domcontentloaded")
                    return adapter.extract_live_price(page, clean_url)
        except Exception as e:
            return ExtractedPriceResult(
                retailer_name=adapter.retailer_name,
                store_id=getattr(adapter, "store_id", "retailer"),
                product_url=clean_url,
                verification_status="error",
                validation_notes=f"Failed to access product page: {e}",
                source_type="unavailable",
            )


# Global singleton instance
_live_engine = LiveComparisonEngine()


def get_live_comparison_engine() -> LiveComparisonEngine:
    """Get global LiveComparisonEngine instance."""
    return _live_engine

