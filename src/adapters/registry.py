"""Retailer Integration Adapter Registry for PriceWise AI Beauty.

Centralizes discovery, instantiation, status tracking, and dispatching
for all 5 Indian beauty retailer adapters:
1. Nykaa
2. Tira Beauty
3. Purplle
4. Amazon India
5. Myntra
"""

from typing import Any, Optional
from src.adapters.base_adapter import BaseRetailerAdapter, RetailerOfferResult
from src.adapters.nykaa_adapter import NykaaAdapter
from src.adapters.tira_adapter import TiraAdapter
from src.adapters.purplle_adapter import PurplleAdapter
from src.adapters.amazon_adapter import AmazonIndiaAdapter
from src.adapters.myntra_adapter import MyntraAdapter


class RetailerAdapterRegistry:
    """Registry coordinating retailer integrations."""

    def __init__(self):
        self._adapters: dict[str, BaseRetailerAdapter] = {
            "nykaa": NykaaAdapter(),
            "tira": TiraAdapter(),
            "purplle": PurplleAdapter(),
            "amazon india": AmazonIndiaAdapter(),
            "amazon": AmazonIndiaAdapter(),
            "myntra": MyntraAdapter(),
        }

    def get_adapter(self, name: str) -> Optional[BaseRetailerAdapter]:
        """Look up adapter by normalized retailer name."""
        key = (name or "").strip().lower()
        return self._adapters.get(key)

    def get_adapter_by_url(self, url: str) -> Optional[BaseRetailerAdapter]:
        """Look up adapter matching a retailer product URL."""
        from urllib.parse import urlparse
        try:
            hostname = (urlparse(url).hostname or "").lower()
            for adapter in self.list_all_unique_adapters():
                if adapter.domain in hostname:
                    return adapter
        except Exception:
            pass
        return None

    def list_all_unique_adapters(self) -> list[BaseRetailerAdapter]:
        """Return list of distinct registered adapters."""
        seen = set()
        unique = []
        for adapter in self._adapters.values():
            if adapter.retailer_name not in seen:
                seen.add(adapter.retailer_name)
                unique.append(adapter)
        return unique

    def list_configured_adapters(self) -> list[BaseRetailerAdapter]:
        """Return list of adapters with verified credentials in environment."""
        return [a for a in self.list_all_unique_adapters() if a.is_configured]

    def list_unconfigured_adapters(self) -> list[BaseRetailerAdapter]:
        """Return list of adapters lacking required environment variables."""
        return [a for a in self.list_all_unique_adapters() if not a.is_configured]

    def get_status_summary(self) -> list[dict[str, Any]]:
        """Return overview of all retailers, integration status, and missing credentials."""
        import os
        summary = []
        for adapter in self.list_all_unique_adapters():
            missing = [c for c in adapter.required_credentials if not os.getenv(c)]
            summary.append({
                "retailer": adapter.retailer_name,
                "domain": adapter.domain,
                "is_configured": adapter.is_configured,
                "rate_limit_per_minute": adapter.rate_limit_per_minute,
                "required_credentials": adapter.required_credentials,
                "missing_credentials": missing,
                "status_label": "Configured & Active" if adapter.is_configured else "Unconfigured (Demo / Manual Fallback)",
            })
        return summary

    def fetch_offers_across_retailers(
        self,
        product_name: str,
        brand: str = "",
        size_volume: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> list[RetailerOfferResult]:
        """
        Query all registered adapters for offers.
        If credentials are not present, each adapter returns an unconfigured status or demo fallback.
        """
        results: list[RetailerOfferResult] = []
        ctx = dict(context or {})
        ctx["product_name"] = product_name
        ctx["brand"] = brand
        if size_volume:
            ctx["size_volume"] = size_volume

        for adapter in self.list_all_unique_adapters():
            try:
                offer = adapter.fetch_product_offer(
                    retailer_product_id=f"{adapter.retailer_name.lower()}-sku",
                    context=ctx,
                )
                results.append(offer)
            except Exception as e:
                # Catch unexpected adapter network or parsing exceptions gracefully
                results.append(
                    RetailerOfferResult(
                        retailer_name=adapter.retailer_name,
                        product_url=f"https://{adapter.domain}",
                        brand=brand,
                        product_name=product_name,
                        current_price=0.0,
                        is_available=False,
                        source_type="unavailable",
                        error_message=f"Integration error: {str(e)}",
                    )
                )

        return results


# Global singleton instance
_registry = RetailerAdapterRegistry()


def get_adapter_registry() -> RetailerAdapterRegistry:
    """Get global RetailerAdapterRegistry instance."""
    return _registry

