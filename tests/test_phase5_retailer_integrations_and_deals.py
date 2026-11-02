"""Automated Unit & Integration Test Suite for Phase 5:
Retailer Data Integrations, Current Deals, and Verified Price Comparison.

Covers:
1. Modular Retailer Integrations (Nykaa, Tira, Purplle, Amazon India, Myntra)
2. Safe Credentials Handling (missing credentials return unconfigured/demo status, zero crashes)
3. Rate Limiting & Error Handling
4. Multi-Factor Variant Matching (strict 30ml != 50ml, shade check, formulation check)
5. Landed Cost Calculation (shipping known vs undisclosed)
6. Lowest Among Available Verified Offers Logic
7. Beauty Deal Detection, Coupon Verification, and Expiration Filtering
8. Cost-Per-Unit Metric Calculations in Alternatives
9. Environment Configuration Validation
"""

from datetime import datetime, timezone, timedelta
import os
import pytest
from src.database.models import Offer, Product, Store
from src.adapters.base_adapter import RetailerOfferResult
from src.adapters.registry import get_adapter_registry, RetailerAdapterRegistry
from src.adapters.nykaa_adapter import NykaaAdapter
from src.adapters.tira_adapter import TiraAdapter
from src.adapters.purplle_adapter import PurplleAdapter
from src.adapters.amazon_adapter import AmazonIndiaAdapter
from src.adapters.myntra_adapter import MyntraAdapter
from src.services.product_matching_service import (
    MatchClassification,
    ProductMatchResult,
    evaluate_product_match,
    parse_quantity_volume,
    parse_shade,
    parse_formulation,
    match_product_with_offer,
)
from src.services.comparison_service import (
    generate_comparison_summary,
    validate_offer_compatibility,
    ComparisonSummary,
)
from src.services.deal_service import (
    VerifiedBeautyDeal,
    get_verified_beauty_deals,
    calculate_deal_savings,
    check_is_deal_expired,
)
from src.services.alternative_service import (
    get_cheapest_alternatives,
    AlternativeRecommendation,
)


# ==============================================================================
# 1. Retailer Adapter Architecture & Credentials Tests
# ==============================================================================

def test_retailer_registry_discovers_all_five_retailers():
    """Verify that the registry initializes and discovers all 5 target Indian beauty retailers."""
    registry = get_adapter_registry()
    adapters = registry.list_all_unique_adapters()
    adapter_names = {a.retailer_name for a in adapters}
    
    expected = {"Nykaa", "Tira", "Purplle", "Amazon India", "Myntra"}
    assert expected.issubset(adapter_names), f"Missing retailers in {adapter_names}"


def test_adapters_unconfigured_when_env_credentials_missing(monkeypatch):
    """Ensure that with missing environment variables, all adapters report is_configured=False and fail gracefully."""
    # Ensure env vars are cleared
    for key in [
        "NYKAA_API_KEY", "NYKAA_PARTNER_SECRET",
        "TIRA_PARTNER_TOKEN", "TIRA_API_URL",
        "PURPLLE_FEED_URL", "PURPLLE_API_KEY",
        "AMAZON_PAAPI_KEY", "AMAZON_PAAPI_SECRET", "AMAZON_ASSOCIATE_TAG",
        "MYNTRA_PARTNER_KEY", "MYNTRA_AFFILIATE_ID",
    ]:
        monkeypatch.delenv(key, raising=False)

    adapters = [
        NykaaAdapter(),
        TiraAdapter(),
        PurplleAdapter(),
        AmazonIndiaAdapter(),
        MyntraAdapter(),
    ]

    for adapter in adapters:
        assert not adapter.is_configured, f"{adapter.retailer_name} should be unconfigured"
        result = adapter.fetch_product_offer("sku-test-1", context={"product_name": "Lipstick", "brand": "M.A.C"})
        
        # Must return clean unconfigured or unavailable status without raising exceptions
        assert isinstance(result, RetailerOfferResult)
        assert not result.is_available or result.source_type in ("unavailable", "demo")
        assert result.source_type != "verified_live"
        assert "not configured" in (result.error_message or "").lower() or "missing" in (result.error_message or "").lower()


def test_adapters_configured_when_env_credentials_present(monkeypatch):
    """Ensure that when valid credentials are supplied, adapters transition to is_configured=True and return verified data."""
    monkeypatch.setenv("NYKAA_API_KEY", "mock-nyk-key-12345")
    monkeypatch.setenv("NYKAA_PARTNER_SECRET", "mock-nyk-secret-67890")

    adapter = NykaaAdapter()
    assert adapter.is_configured
    
    result = adapter.fetch_product_offer("nyk-101", context={"product_name": "Sunscreen", "brand": "Dot & Key", "price": 499.0})
    assert result.is_available
    assert result.source_type == "verified_live"
    assert result.retailer_name == "Nykaa"
    assert result.coupon_code == "NYKBEAUTY10"


def test_adapter_rate_limiting():
    """Verify that rapid requests exceeding the rate limit are throttled cleanly."""
    adapter = NykaaAdapter(rate_limit_per_minute=3)
    adapter.reset_rate_limit_window()

    # 3 allowed requests
    for _ in range(3):
        allowed, err = adapter.check_rate_limit()
        assert allowed
        assert err is None

    # 4th request must be blocked
    allowed, err = adapter.check_rate_limit()
    assert not allowed
    assert "Rate limit exceeded" in err


# ==============================================================================
# 2. Product Matching & Variant Integrity Tests
# ==============================================================================

def test_volume_quantity_parsing():
    """Verify correct numerical and unit parsing for standard beauty packaging."""
    cases = [
        ("50 ml", (50.0, "ml")),
        ("30ml", (30.0, "ml")),
        ("100 gm", (100.0, "g")),
        ("3.8g", (3.8, "g")),
        ("15 g", (15.0, "g")),
        ("1 oz", (1.0, "oz")),
    ]
    for text, expected in cases:
        val, unit = parse_quantity_volume(text)
        assert (val, unit) == expected, f"Failed parsing {text}: got {(val, unit)}"


def test_variant_integrity_strictly_rejects_volume_mismatch():
    """Verify that 30ml is strictly rejected as non-comparable against 50ml."""
    result = evaluate_product_match(
        target_brand="Dot & Key",
        target_title="Watermelon Cooling Sunscreen 50ml",
        target_specs={"Size": "50ml"},
        offer_brand="Dot & Key",
        offer_title="Watermelon Cooling Sunscreen 30ml",
        offer_variant="30ml",
    )
    assert result.match_classification == MatchClassification.INCOMPATIBLE_MISMATCH
    assert not result.is_comparable
    assert not result.size_match
    assert any("30ml cannot be compared with 50ml" in r or "Size mismatch" in r for r in result.reasons)


def test_variant_integrity_strictly_rejects_makeup_shade_mismatch():
    """Verify that different lipstick shades (e.g. Ruby Woo vs Velvet Teddy) are never compared."""
    result = evaluate_product_match(
        target_brand="M.A.C",
        target_title="Retro Matte Lipstick - Ruby Woo",
        target_specs={"Shade": "Ruby Woo", "Size": "3g"},
        offer_brand="M.A.C",
        offer_title="Retro Matte Lipstick - Velvet Teddy",
        offer_variant="Velvet Teddy",
        offer_specs={"Shade": "Velvet Teddy", "Size": "3g"},
    )
    assert result.match_classification == MatchClassification.INCOMPATIBLE_MISMATCH
    assert not result.is_comparable
    assert not result.shade_match
    assert any("Shade mismatch" in r for r in result.reasons)


def test_variant_integrity_strictly_rejects_formulation_mismatch():
    """Verify that Waterproof mascara is never compared against Washable mascara."""
    result = evaluate_product_match(
        target_brand="Maybelline",
        target_title="Lash Sensational Sky High Waterproof Mascara",
        target_specs={"Formulation": "Waterproof", "Size": "7.2ml"},
        offer_brand="Maybelline",
        offer_title="Lash Sensational Sky High Washable Mascara",
        offer_variant="Washable",
        offer_specs={"Formulation": "Washable", "Size": "7.2ml"},
    )
    assert result.match_classification == MatchClassification.INCOMPATIBLE_MISMATCH
    assert not result.is_comparable
    assert not result.formulation_match
    assert any("Formulation mismatch" in r for r in result.reasons)


def test_verified_match_for_identical_variant():
    """Verify that identical variant across brand, volume, shade, and formulation is classified as verified_match."""
    result = evaluate_product_match(
        target_brand="Dot & Key",
        target_title="Watermelon Cooling Sunscreen SPF 50+ PA++++",
        target_specs={"Net Quantity": "50g", "Product Type": "Gel Sunscreen"},
        offer_brand="Dot & Key",
        offer_title="Watermelon Cooling Sunscreen SPF 50+ PA++++",
        offer_variant="50g Standard",
        offer_specs={"Net Quantity": "50g", "Product Type": "Gel Sunscreen"},
    )
    assert result.match_classification == MatchClassification.VERIFIED_MATCH
    assert result.is_comparable
    assert result.confidence_score >= 0.90


# ==============================================================================
# 3. Landed Cost & Verified Price Comparison Tests
# ==============================================================================

def test_landed_cost_with_known_shipping_and_coupon():
    """Verify total cost calculation: price + shipping - coupon discount."""
    offer = Offer(
        id=1,
        product_id=1,
        store_id=1,
        store_name="Nykaa",
        store_rating=4.8,
        current_price=500.0,
        original_price=600.0,
        shipping_cost=50.0,
        is_shipping_disclosed=True,
        coupon_discount=40.0,
        coupon_code="NYKBEAUTY",
    )
    # Total cost = 500 + 50 - 40 = 510.0
    assert offer.total_cost == 510.0
    assert offer.landed_cost == 510.0


def test_landed_cost_undisclosed_shipping_returns_none():
    """Crucial Rule: When shipping is undisclosed, landed_cost must be None (never assumed to be 0)."""
    offer = Offer(
        id=2,
        product_id=1,
        store_id=2,
        store_name="Myntra",
        store_rating=4.5,
        current_price=480.0,
        original_price=600.0,
        shipping_cost=None,
        is_shipping_disclosed=False,
    )
    assert offer.landed_cost is None
    assert not offer.is_shipping_disclosed


def test_comparison_summary_lowest_verified_offer_label():
    """Verify comparison summary generates proper lowest verified offer label."""
    p = Product(
        id=10,
        sku="SKU-SUN-01",
        title="Watermelon Sunscreen 50ml",
        brand="Dot & Key",
        category="Sunscreen",
        description="Cooling Sunscreen",
        specs={"Size": "50ml"},
        offers=[
            Offer(id=1, product_id=10, store_id=1, store_name="Nykaa", store_rating=4.8, current_price=450.0, shipping_cost=0.0),
            Offer(id=2, product_id=10, store_id=2, store_name="Tira", store_rating=4.7, current_price=480.0, shipping_cost=0.0),
        ]
    )
    summary = generate_comparison_summary(p)
    assert summary is not None
    assert summary.has_verified_savings
    assert summary.lowest_verified_offer_label == "Lowest among available verified offers"
    assert summary.lowest_price == 450.0


# ==============================================================================
# 4. Beauty Deal Intelligence & Expiration Tests
# ==============================================================================

def test_calculate_deal_savings():
    """Verify net price, absolute savings, and percentage savings computation."""
    net_price, savings_amt, savings_pct = calculate_deal_savings(
        current_price=450.0,
        reference_price=600.0,
        coupon_discount=50.0,
    )
    # net_price = 450 - 50 = 400.0
    # savings = 600 - 400 = 200.0
    # savings_pct = (200 / 600) * 100 = 33.3%
    assert net_price == 400.0
    assert savings_amt == 200.0
    assert savings_pct == 33.3


def test_deal_expiration_check():
    """Verify expired deal timestamps are correctly identified."""
    now_utc = datetime.now(timezone.utc)
    past_date = (now_utc - timedelta(days=2)).isoformat()
    future_date = (now_utc + timedelta(days=5)).isoformat()

    assert check_is_deal_expired(past_date)
    assert not check_is_deal_expired(future_date)
    assert not check_is_deal_expired(None)


def test_get_verified_beauty_deals_filtering():
    """Verify that get_verified_beauty_deals filters out non-deals and respects expiration."""
    p = Product(
        id=20,
        sku="SKU-SERUM-01",
        title="Niacinamide 10% Serum 30ml",
        brand="Minimalist",
        category="Serums",
        description="Serum",
        specs={"MRP": 600.0, "Size": "30ml"},
        offers=[
            Offer(
                id=1,
                product_id=20,
                store_id=1,
                store_name="Nykaa",
                store_rating=4.9,
                current_price=450.0,
                original_price=600.0,
                coupon_code="NYK10",
                coupon_discount=45.0,
            ),
        ]
    )
    deals = get_verified_beauty_deals([p])
    assert len(deals) == 1
    d = deals[0]
    assert d.product_id == 20
    assert d.coupon_code == "NYK10"
    assert d.savings_amount > 0
    assert not d.is_expired


# ==============================================================================
# 5. Cost-Per-Unit in Alternatives Tests
# ==============================================================================

def test_cost_per_unit_calculation_in_alternatives():
    """Verify cost-per-ml calculations between luxury and budget alternatives."""
    luxury_prod = Product(
        id=30,
        sku="LUX-01",
        title="Luxury Hydration Serum 50ml",
        brand="Luxury Brand",
        category="Serums",
        description="Luxury Serum",
        specs={"Net Quantity": "50 ml", "Key Ingredients": "Hyaluronic Acid, Peptides"},
        offers=[Offer(id=1, product_id=30, store_id=1, store_name="Store A", store_rating=4.5, current_price=1050.0)],
    )
    budget_prod = Product(
        id=31,
        sku="BUD-01",
        title="Budget Hydration Serum 50ml",
        brand="Smart Brand",
        category="Serums",
        description="Budget Serum",
        specs={"Net Quantity": "50 ml", "Key Ingredients": "Hyaluronic Acid, Ceramides"},
        offers=[Offer(id=2, product_id=31, store_id=1, store_name="Store A", store_rating=4.5, current_price=450.0)],
    )

    alts = get_cheapest_alternatives(luxury_prod, all_candidates=[luxury_prod, budget_prod])
    assert len(alts) == 1
    alt = alts[0]

    # Target: ₹1,050 / 50ml = ₹21.00/ml
    # Alternative: ₹450 / 50ml = ₹9.00/ml
    # Unit savings: ₹12.00/ml (57.1% cheaper)
    assert alt.original_cost_per_unit == 21.00
    assert alt.alternative_cost_per_unit == 9.00
    assert alt.cost_per_unit_savings == 12.00
    assert alt.cost_per_unit_savings_pct == 57.1
    assert alt.unit_name == "ml"
    assert "₹9.00/ml vs ₹21.00/ml" in alt.cost_per_unit_comparison


# ==============================================================================
# 6. Environment Configuration File Validation
# ==============================================================================

def test_env_example_file_exists_and_documents_retailers():
    """Verify that .env.example exists and documents environment variables for all 5 retailers."""
    assert os.path.exists(".env.example"), ".env.example must exist in project root"
    with open(".env.example", "r", encoding="utf-8") as f:
        content = f.read()

    required_vars = [
        "NYKAA_API_KEY", "NYKAA_PARTNER_SECRET",
        "TIRA_PARTNER_TOKEN", "TIRA_API_URL",
        "PURPLLE_FEED_URL", "PURPLLE_API_KEY",
        "AMAZON_PAAPI_KEY", "AMAZON_PAAPI_SECRET", "AMAZON_ASSOCIATE_TAG",
        "MYNTRA_PARTNER_KEY", "MYNTRA_AFFILIATE_ID",
    ]
    for var in required_vars:
        assert var in content, f".env.example is missing documentation for {var}"

