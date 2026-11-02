"""Base Retailer Integration Adapter for PriceWise AI Beauty (Phase 5).

Provides a standardized, robust interface for Indian beauty retailers:
- Nykaa
- Tira Beauty
- Purplle
- Amazon India
- Myntra

Enforces rate limits, error handling, credentials verification, variant integrity,
and transparent source labeling (verified_live, partner_feed, cached, demo, unavailable).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import os
import re
import time
from typing import Any, Optional

logger = logging.getLogger("pricewise.adapters")


class CapabilityStatus:
    """Retailer extraction capability statuses (Phase 6)."""
    SUPPORTED = "supported"
    RESTRICTED = "restricted"
    UNSUPPORTED = "unsupported"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"


@dataclass
class ExtractedPriceResult:
    """Standardized result from live Playwright HTML / DOM price extraction (Phase 6)."""
    retailer_name: str
    store_id: str
    product_name: Optional[str] = None
    product_url: str = ""
    canonical_url: Optional[str] = None
    listed_price: Optional[float] = None
    mrp: Optional[float] = None
    currency: str = "INR"
    product_size: Optional[str] = None
    variant: Optional[str] = None
    shade: Optional[str] = None
    formulation: Optional[str] = None
    in_stock: bool = True
    stock_status: str = "In Stock"
    shipping_fee: Optional[float] = None  # None indicates undisclosed shipping
    is_shipping_disclosed: bool = True
    coupon_code: Optional[str] = None
    coupon_discount: float = 0.0
    source_type: str = "verified_live"  # "verified_live", "cached", "demo", "unavailable"
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verification_status: str = "retrieved"  # retrieved, restricted, unavailable, unsupported, mismatch, error
    extraction_method: str = "playwright_dom"
    validation_notes: Optional[str] = None

    @property
    def total_cost(self) -> Optional[float]:
        """
        Total landed purchase cost = base listed price + shipping - coupon.
        Crucial Rule: If shipping is undisclosed, total cost CANNOT be computed.
        """
        if not self.is_shipping_disclosed or self.shipping_fee is None:
            return None
        if self.listed_price is None or self.listed_price <= 0:
            return None
        coupon = self.coupon_discount or 0.0
        return round(max(0.0, self.listed_price + self.shipping_fee - coupon), 2)

    @property
    def discount_pct(self) -> float:
        """Percentage discount relative to MRP."""
        if self.mrp and self.listed_price and self.mrp > self.listed_price and self.mrp > 0:
            return round(((self.mrp - self.listed_price) / self.mrp) * 100, 1)
        return 0.0


@dataclass
class RetailerOfferResult:
    """Standardized representation of a product offer retrieved from a retailer."""
    retailer_name: str
    product_url: str
    brand: str
    product_name: str
    current_price: float
    retailer_product_id: Optional[str] = None
    original_price: Optional[float] = None
    discount_pct: float = 0.0
    shipping_cost: Optional[float] = None  # None indicates undisclosed shipping
    is_shipping_disclosed: bool = True
    stock_status: str = "In Stock"  # "In Stock", "Limited Stock", "Out of Stock"
    is_available: bool = True
    variant_name: str = "Standard"
    size_volume: Optional[str] = None
    shade: Optional[str] = None
    formulation: Optional[str] = None
    coupon_code: Optional[str] = None
    coupon_discount: float = 0.0
    coupon_terms: Optional[str] = None
    currency: str = "INR"
    last_successful_fetch: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source_type: str = "demo"  # "verified_live", "partner_feed", "cached", "manually_curated", "demo", "unavailable"
    error_message: Optional[str] = None

    def __post_init__(self):
        # Auto-calculate discount percentage if original price is provided
        if self.original_price and self.original_price > self.current_price and self.original_price > 0:
            self.discount_pct = round(
                ((self.original_price - self.current_price) / self.original_price) * 100, 1
            )
        # Determine availability from stock status
        if self.stock_status.lower() in ("out of stock", "unavailable", "discontinued", "sold out"):
            self.is_available = False

    @property
    def total_cost(self) -> Optional[float]:
        """
        Total landed cost = base price + shipping - coupon.
        Crucial Rule: If shipping is undisclosed, total cost CANNOT be computed.
        Never assume undisclosed shipping is 0.
        """
        if not self.is_shipping_disclosed or self.shipping_cost is None:
            return None
        if self.current_price is None or self.current_price <= 0:
            return None
        coupon = self.coupon_discount or 0.0
        return round(max(0.0, self.current_price + self.shipping_cost - coupon), 2)

    @property
    def currency_symbol(self) -> str:
        return "₹" if (self.currency or "").upper() == "INR" else "$"


class BaseRetailerAdapter(ABC):
    """Abstract base adapter for all beauty retailer data integrations."""

    def __init__(
        self,
        retailer_name: str,
        domain: str,
        rate_limit_per_minute: int = 30,
        timeout_seconds: float = 5.0,
    ):
        self.retailer_name = retailer_name
        self.domain = domain
        self.rate_limit_per_minute = rate_limit_per_minute
        self.timeout_seconds = timeout_seconds
        self._request_timestamps: list[float] = []

    @property
    @abstractmethod
    def required_credentials(self) -> list[str]:
        """List of environment variable keys required for authorized live access."""
        pass

    @property
    def is_configured(self) -> bool:
        """Check whether all required credential environment variables are set."""
        for cred in self.required_credentials:
            val = os.getenv(cred)
            if not val or not val.strip():
                return False
        return True

    def check_rate_limit(self) -> tuple[bool, Optional[str]]:
        """
        Check rate limiting using a 60-second sliding window.
        Returns (is_allowed, error_message).
        """
        now = time.time()
        # Discard timestamps older than 60 seconds
        self._request_timestamps = [t for t in self._request_timestamps if now - t < 60.0]

        if len(self._request_timestamps) >= self.rate_limit_per_minute:
            return (
                False,
                f"Rate limit exceeded for {self.retailer_name} ({self.rate_limit_per_minute} req/min). Please try again shortly.",
            )

        self._request_timestamps.append(now)
        return True, None

    def reset_rate_limit_window(self) -> None:
        """Reset the request timestamp history (useful for testing)."""
        self._request_timestamps.clear()

    def create_unconfigured_result(
        self,
        product_name: str,
        brand: str = "",
        fallback_demo: Optional[RetailerOfferResult] = None,
    ) -> RetailerOfferResult:
        """
        Produce a safe, transparent result when credentials are unconfigured.
        Never pretends to be live data.
        """
        missing_vars = [c for c in self.required_credentials if not os.getenv(c)]
        missing_msg = f"Retailer integration not configured. Missing environment variables: {', '.join(missing_vars)}."

        if fallback_demo:
            # Mark demo fallback explicitly
            fallback_demo.source_type = "demo"
            fallback_demo.error_message = f"Simulated demo data: {missing_msg}"
            return fallback_demo

        return RetailerOfferResult(
            retailer_name=self.retailer_name,
            retailer_product_id=None,
            product_url=f"https://{self.domain}",
            brand=brand,
            product_name=product_name,
            current_price=0.0,
            original_price=None,
            shipping_cost=None,
            is_shipping_disclosed=False,
            stock_status="Unavailable",
            is_available=False,
            source_type="unavailable",
            error_message=missing_msg,
        )

    @abstractmethod
    def fetch_product_offer(
        self,
        retailer_product_id: str,
        context: Optional[dict[str, Any]] = None,
    ) -> RetailerOfferResult:
        """Retrieve a specific product offer by retailer SKU/product ID."""
        pass

    @abstractmethod
    def search_offers(
        self,
        query: str,
        brand: Optional[str] = None,
        size_volume: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> list[RetailerOfferResult]:
        """Search retailer catalog for matching product offers."""
        pass

    # =========================================================================
    # Phase 6: Automatic Live Playwright Browser Extraction Methods
    # =========================================================================

    @property
    def capability_status(self) -> str:
        """Current capability status for automated extraction (Phase 6)."""
        return getattr(self, "_capability_status", CapabilityStatus.SUPPORTED)

    @capability_status.setter
    def capability_status(self, val: str) -> None:
        self._capability_status = val

    @staticmethod
    def clean_price_text(text: Any) -> Optional[float]:
        """Convert messy retailer price text ('₹499.00', 'Rs 1,299', '499') to clean float."""
        if text is None:
            return None
        if isinstance(text, (int, float)):
            return float(text) if text > 0 else None

        cleaned = re.sub(r"[^\d.]", "", str(text).replace(",", ""))
        if not cleaned:
            return None
        try:
            val = float(cleaned)
            return val if val > 0 else None
        except ValueError:
            return None

    def detect_access_restrictions(self, html: str) -> Optional[str]:
        """Check for CAPTCHA, bot challenges, or access blocks."""
        if not html:
            return "Empty response received"
        lower = html.lower()
        if "robot check" in lower or "enter the characters you see below" in lower:
            return "Amazon automated access verification (CAPTCHA challenge)"
        if "cf-turnstile" in lower or "cf-challenge" in lower or "checking your browser" in lower:
            return "Cloudflare bot challenge detected"
        if "access denied" in lower or "403 forbidden" in lower:
            return "Access denied by retailer security policy"
        if "pardon our interruption" in lower or "perimeterx" in lower:
            return "PerimeterX bot protection challenge"
        if "please verify you are human" in lower or "g-recaptcha" in lower or "hcaptcha" in lower:
            return "CAPTCHA human verification challenge"
        return None

    def extract_schema_org_json_ld(self, html: str) -> Optional[dict]:
        """Extract schema.org Product structured JSON-LD data from HTML."""
        if not html:
            return None
        matches = re.findall(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html,
            re.DOTALL | re.IGNORECASE,
        )
        for block in matches:
            try:
                data = json.loads(block.strip())
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict):
                        if "@graph" in item and isinstance(item["@graph"], list):
                            for sub in item["@graph"]:
                                if isinstance(sub, dict) and sub.get("@type") in ("Product", "IndividualProduct"):
                                    return sub
                        if item.get("@type") in ("Product", "IndividualProduct"):
                            return item
            except Exception:
                continue
        return None

    def extract_from_html(self, html: str, url: str) -> ExtractedPriceResult:
        """
        Extract price and product attributes from static/rendered HTML string.
        Can be overridden in subclasses for retailer-specific DOM selectors.
        """
        store_id = getattr(self, "store_id", self.retailer_name.lower().replace(" ", "-"))
        restriction = self.detect_access_restrictions(html)
        if restriction:
            return ExtractedPriceResult(
                retailer_name=self.retailer_name,
                store_id=store_id,
                product_url=url,
                verification_status="restricted",
                validation_notes=restriction,
                source_type="unavailable",
            )

        json_ld = self.extract_schema_org_json_ld(html)
        if json_ld:
            name = json_ld.get("name")
            offers = json_ld.get("offers", {})
            if isinstance(offers, list) and offers:
                offers = offers[0]
            price = self.clean_price_text(offers.get("price"))
            mrp = self.clean_price_text(
                offers.get("highPrice") or (offers.get("priceSpecification") or {}).get("price")
            )
            avail = str(offers.get("availability", "")).lower()
            in_stock = "outofstock" not in avail

            if price:
                return ExtractedPriceResult(
                    retailer_name=self.retailer_name,
                    store_id=store_id,
                    product_name=name,
                    product_url=url,
                    listed_price=price,
                    mrp=mrp,
                    in_stock=in_stock,
                    stock_status="In Stock" if in_stock else "Out of Stock",
                    verification_status="retrieved",
                    extraction_method="schema_org_json_ld",
                )

        return ExtractedPriceResult(
            retailer_name=self.retailer_name,
            store_id=store_id,
            product_url=url,
            verification_status="unavailable",
            validation_notes="Product details could not be extracted from page HTML",
            source_type="unavailable",
        )

    def extract_live_price(self, page: Any, url: str) -> ExtractedPriceResult:
        """
        Extract live price using Playwright Page object.
        """
        store_id = getattr(self, "store_id", self.retailer_name.lower().replace(" ", "-"))
        try:
            content = page.content()
            return self.extract_from_html(content, url)
        except Exception as e:
            return ExtractedPriceResult(
                retailer_name=self.retailer_name,
                store_id=store_id,
                product_url=url,
                verification_status="error",
                validation_notes=f"Browser extraction error: {str(e)}",
                source_type="unavailable",
            )

    def discover_product_url(
        self,
        product_name: str,
        brand: str,
        search_query: str,
        page: Optional[Any] = None,
    ) -> Optional[str]:
        """
        Discover candidate retailer product URL via search or catalog slug.
        Override in subclasses.
        """
        return None

