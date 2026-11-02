"""Retailer Integration Adapters for PriceWise AI Beauty (Phase 5)."""

from src.adapters.base_adapter import (
    BaseRetailerAdapter,
    RetailerOfferResult,
    ExtractedPriceResult,
    CapabilityStatus,
)
from src.adapters.nykaa_adapter import NykaaAdapter
from src.adapters.tira_adapter import TiraAdapter
from src.adapters.purplle_adapter import PurplleAdapter
from src.adapters.amazon_adapter import AmazonIndiaAdapter
from src.adapters.myntra_adapter import MyntraAdapter
from src.adapters.registry import RetailerAdapterRegistry, get_adapter_registry

__all__ = [
    "BaseRetailerAdapter",
    "RetailerOfferResult",
    "ExtractedPriceResult",
    "CapabilityStatus",
    "NykaaAdapter",
    "TiraAdapter",
    "PurplleAdapter",
    "AmazonIndiaAdapter",
    "MyntraAdapter",
    "RetailerAdapterRegistry",
    "get_adapter_registry",
]

