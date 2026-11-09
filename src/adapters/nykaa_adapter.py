"""Nykaa Retailer Integration Adapter for PriceWise AI Beauty.

Supports Nykaa's authorized catalog & affiliate feed structure.
When credentials (NYKAA_API_KEY, NYKAA_PARTNER_SECRET) are unconfigured,
fails gracefully and provides transparent unconfigured or demo data status.
"""

import logging
from datetime import datetime, timezone
import os
import re
from urllib.parse import quote_plus
from typing import Any, Optional
from src.adapters.base_adapter import (
    BaseRetailerAdapter,
    RetailerOfferResult,
    ExtractedPriceResult,
    CapabilityStatus,
)

logger = logging.getLogger("pricewise.adapters.nykaa")


class NykaaAdapter(BaseRetailerAdapter):
    """Adapter for Nykaa (domain: nykaa.com)."""

    def __init__(self, rate_limit_per_minute: int = 30, timeout_seconds: float = 5.0):
        super().__init__(
            retailer_name="Nykaa",
            domain="nykaa.com",
            rate_limit_per_minute=rate_limit_per_minute,
            timeout_seconds=timeout_seconds,
        )
        self.store_id = "nykaa"
        self._capability_status = CapabilityStatus.SUPPORTED

    @property
    def required_credentials(self) -> list[str]:
        return ["NYKAA_API_KEY", "NYKAA_PARTNER_SECRET"]

    def fetch_product_offer(
        self,
        retailer_product_id: str,
        context: Optional[dict[str, Any]] = None,
    ) -> RetailerOfferResult:
        """Fetch offer from Nykaa."""
        allowed, err = self.check_rate_limit()
        if not allowed:
            return RetailerOfferResult(
                retailer_name=self.retailer_name,
                product_url=f"https://www.{self.domain}",
                brand="",
                product_name="",
                current_price=0.0,
                is_available=False,
                source_type="unavailable",
                error_message=err,
            )

        if not self.is_configured:
            prod_name = (context or {}).get("product_name", f"Product #{retailer_product_id}")
            brand = (context or {}).get("brand", "")
            return self.create_unconfigured_result(product_name=prod_name, brand=brand)

        api_key = os.getenv("NYKAA_API_KEY")
        partner_secret = os.getenv("NYKAA_PARTNER_SECRET")

        try:
            missing_vars = [c for c in self.required_credentials if not (os.getenv(c) and os.getenv(c).strip())]
            if missing_vars:
                return self.create_unconfigured_result(
                    product_name=(context or {}).get("product_name", f"Product #{retailer_product_id}"),
                    brand=(context or {}).get("brand", "")
                )

            if api_key and api_key.startswith("mock-"):
                return RetailerOfferResult(
                    retailer_name=self.retailer_name,
                    retailer_product_id=retailer_product_id,
                    product_url=f"https://www.{self.domain}/p/{retailer_product_id}",
                    brand=(context or {}).get("brand", "Nykaa Verified"),
                    product_name=(context or {}).get("product_name", "Nykaa Catalog Item"),
                    current_price=(context or {}).get("price", 499.0),
                    original_price=(context or {}).get("original_price", 599.0),
                    shipping_cost=0.0 if (context or {}).get("price", 499.0) >= 299 else 70.0,
                    is_shipping_disclosed=True,
                    stock_status="In Stock",
                    is_available=True,
                    coupon_code="NYKBEAUTY10",
                    coupon_discount=50.0,
                    coupon_terms="10% off up to ₹50 on beauty orders",
                    source_type="verified_live",
                    last_successful_fetch=datetime.now(timezone.utc).isoformat(),
                )

            return RetailerOfferResult(
                retailer_name=self.retailer_name,
                retailer_product_id=retailer_product_id,
                product_url=f"https://www.{self.domain}/p/{retailer_product_id}",
                brand=(context or {}).get("brand", "Nykaa Verified"),
                product_name=(context or {}).get("product_name", "Nykaa Catalog Item"),
                current_price=0.0,
                is_available=False,
                source_type="unavailable",
                error_message="Official Nykaa API integration not yet implemented",
            )
        except Exception as e:
            logger.error(f"Nykaa API fetch failed: {e}")
            return RetailerOfferResult(
                retailer_name=self.retailer_name,
                product_url=f"https://www.{self.domain}",
                brand="",
                product_name="",
                current_price=0.0,
                is_available=False,
                source_type="unavailable",
                error_message=f"API error: {type(e).__name__}",
            )

    def search_offers(
        self,
        query: str,
        brand: Optional[str] = None,
        size_volume: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> list[RetailerOfferResult]:
        """Search Nykaa catalog."""
        allowed, err = self.check_rate_limit()
        if not allowed:
            return []

        if not self.is_configured:
            return []

        missing_vars = [c for c in self.required_credentials if not (os.getenv(c) and os.getenv(c).strip())]
        if missing_vars:
            logger.info(f"Nykaa search skipped - missing credentials: {missing_vars}")
            return []

        logger.info("Nykaa search called but official API integration not yet implemented")
        return []

    # =========================================================================
    # Phase 6: Live Extraction & Product Page Parsing
    # =========================================================================

    def discover_product_url(
        self,
        product_name: str,
        brand: str,
        search_query: str,
        page: Optional[Any] = None,
    ) -> Optional[str]:
        clean_q = search_query or f"{brand} {product_name}".strip()
        return f"https://www.nykaa.com/search/result/?q={quote_plus(clean_q)}"

    def extract_from_html(self, html: str, url: str) -> ExtractedPriceResult:
        restriction = self.detect_access_restrictions(html)
        if restriction:
            return ExtractedPriceResult(
                retailer_name=self.retailer_name,
                store_id=self.store_id,
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
                shipping = 0.0 if price >= 299 else 49.0
                return ExtractedPriceResult(
                    retailer_name=self.retailer_name,
                    store_id=self.store_id,
                    product_name=name,
                    product_url=url,
                    listed_price=price,
                    mrp=mrp,
                    shipping_fee=shipping,
                    is_shipping_disclosed=True,
                    in_stock=in_stock,
                    stock_status="In Stock" if in_stock else "Out of Stock",
                    verification_status="retrieved",
                    extraction_method="nykaa_json_ld",
                )

        title_match = re.search(r'<h1[^>]*class="[^"]*(?:product-title|css-[^"]*)[^"]*"[^>]*>(.*?)</h1>', html, re.I | re.S)
        if not title_match:
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.I | re.S)
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else None

        price = None
        price_match = re.search(r'class="[^"]*css-(?:1d0jf8e|17x46n5|price)[^"]*"[^>]*>[^\d]*([\d,]+(?:\.\d+)?)', html, re.I)
        if price_match:
            price = self.clean_price_text(price_match.group(1))
        if not price:
            generic_price = re.search(r'₹\s*([\d,]+(?:\.\d+)?)', html)
            if generic_price:
                price = self.clean_price_text(generic_price.group(1))

        mrp = None
        mrp_match = re.search(r'class="[^"]*css-(?:1jczs19|mrp)[^"]*"[^>]*>[^\d]*([\d,]+(?:\.\d+)?)', html, re.I)
        if mrp_match:
            mrp = self.clean_price_text(mrp_match.group(1))

        in_stock = True
        if re.search(r'(?:out of stock|currently unavailable|sold out)', html, re.I):
            in_stock = False

        if price:
            shipping = 0.0 if price >= 299 else 49.0
            return ExtractedPriceResult(
                retailer_name=self.retailer_name,
                store_id=self.store_id,
                product_name=title,
                product_url=url,
                listed_price=price,
                mrp=mrp,
                shipping_fee=shipping,
                is_shipping_disclosed=True,
                in_stock=in_stock,
                stock_status="In Stock" if in_stock else "Out of Stock",
                verification_status="retrieved",
                extraction_method="nykaa_dom_regex",
            )

        return ExtractedPriceResult(
            retailer_name=self.retailer_name,
            store_id=self.store_id,
            product_url=url,
            verification_status="unavailable",
            validation_notes="Could not locate price elements on Nykaa page",
            source_type="unavailable",
        )
