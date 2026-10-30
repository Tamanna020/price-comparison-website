"""Phase 2 comprehensive tests for functional search, filters, sorting,
strict product matching, and multi-store comparison edge cases.
"""

import tempfile
import os
import pytest
from src.database.connection import init_db
from src.database.seed import seed_database
from src.database.models import Offer, PricePoint, Product
from src.services.product_service import (
    get_products,
    get_all_categories,
    get_all_brands,
    get_product_by_id,
)
from src.services.comparison_service import (
    generate_comparison_summary,
    validate_offer_compatibility,
)


@pytest.fixture(scope="module")
def seeded_db():
    """Create a temporary populated database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


# =====================================================================
# 1. Functional Search Tests (Case-insensitive, Model, SKU, Specs)
# =====================================================================

def test_search_case_insensitive_title(seeded_db):
    results_lower = get_products(search_query="macbook", custom_path=seeded_db)
    results_upper = get_products(search_query="MACBOOK", custom_path=seeded_db)
    results_mixed = get_products(search_query="MacBook", custom_path=seeded_db)

    assert len(results_lower) >= 1
    assert len(results_lower) == len(results_upper) == len(results_mixed)
    assert any("MacBook" in p.title for p in results_lower)


def test_search_by_brand(seeded_db):
    sony_products = get_products(search_query="sony", custom_path=seeded_db)
    assert len(sony_products) >= 2
    assert all(p.brand == "Sony" or "Sony" in p.title for p in sony_products)


def test_search_by_sku_and_model_identifier(seeded_db):
    # Test searching by specific SKU
    sku_result = get_products(search_query="LAP-MAC-M3-14", custom_path=seeded_db)
    assert len(sku_result) == 1
    assert sku_result[0].sku == "LAP-MAC-M3-14"

    # Test searching by camera SKU/model
    cam_result = get_products(search_query="A7IV", custom_path=seeded_db)
    assert len(cam_result) >= 1
    assert "Alpha 7 IV" in cam_result[0].title


def test_search_by_specs_keywords(seeded_db):
    # Search by spec term "OLED"
    oled_prods = get_products(search_query="OLED", custom_path=seeded_db)
    assert len(oled_prods) >= 1
    assert any("OLED" in p.title or "OLED" in str(p.specs) for p in oled_prods)


def test_multi_word_tokenized_search(seeded_db):
    # Words in different order than the title
    results = get_products(search_query="pro apple 14 macbook", custom_path=seeded_db)
    assert len(results) >= 1
    assert "MacBook Pro 14" in results[0].title


def test_search_empty_no_matches(seeded_db):
    results = get_products(search_query="NonExistentWidget99999", custom_path=seeded_db)
    assert results == []


# =====================================================================
# 2. Category and Brand Filter Tests
# =====================================================================

def test_filter_by_category(seeded_db):
    laptops = get_products(category="Laptops", custom_path=seeded_db)
    assert len(laptops) >= 2
    assert all(p.category == "Laptops" for p in laptops)


def test_filter_by_brand(seeded_db):
    dell_products = get_products(brand="Dell", custom_path=seeded_db)
    assert len(dell_products) >= 2
    assert all(p.brand == "Dell" for p in dell_products)


def test_combined_category_and_brand_filters(seeded_db):
    # Dell in Laptops category
    dell_laptops = get_products(category="Laptops", brand="Dell", custom_path=seeded_db)
    assert len(dell_laptops) == 1
    assert dell_laptops[0].brand == "Dell"
    assert dell_laptops[0].category == "Laptops"

    # Conflicting filter: Dell in Smartphones category
    conflicting = get_products(category="Smartphones", brand="Dell", custom_path=seeded_db)
    assert conflicting == []


def test_dynamic_brands_per_category(seeded_db):
    all_brands = get_all_brands(custom_path=seeded_db)
    assert "Apple" in all_brands
    assert "Dell" in all_brands
    assert "Sony" in all_brands

    laptop_brands = get_all_brands(category="Laptops", custom_path=seeded_db)
    assert "Dell" in laptop_brands
    assert "Apple" in laptop_brands
    assert "LG" not in laptop_brands


def test_in_stock_filter(seeded_db):
    all_prods = get_products(custom_path=seeded_db)
    in_stock_prods = get_products(in_stock_only=True, custom_path=seeded_db)
    assert len(in_stock_prods) <= len(all_prods)
    assert all(p.available_offer_count > 0 for p in in_stock_prods)


def test_price_range_filter(seeded_db):
    budget_prods = get_products(max_price=500.0, custom_path=seeded_db)
    assert len(budget_prods) >= 1
    assert all(p.lowest_price is not None and p.lowest_price <= 500.0 for p in budget_prods)

    premium_prods = get_products(min_price=1500.0, custom_path=seeded_db)
    assert len(premium_prods) >= 1
    assert all(p.lowest_price is not None and p.lowest_price >= 1500.0 for p in premium_prods)


# =====================================================================
# 3. Sorting Tests
# =====================================================================

def test_sorting_by_price_asc(seeded_db):
    sorted_asc = get_products(sort_by="price_asc", custom_path=seeded_db)
    prices = [p.lowest_price for p in sorted_asc if p.lowest_price is not None]
    assert prices == sorted(prices)


def test_sorting_by_price_desc(seeded_db):
    sorted_desc = get_products(sort_by="price_desc", custom_path=seeded_db)
    prices = [p.lowest_price for p in sorted_desc if p.lowest_price is not None]
    assert prices == sorted(prices, reverse=True)


def test_sorting_by_title_asc_and_desc(seeded_db):
    sorted_title_asc = get_products(sort_by="title_asc", custom_path=seeded_db)
    titles_asc = [p.title.lower() for p in sorted_title_asc]
    assert titles_asc == sorted(titles_asc)

    sorted_title_desc = get_products(sort_by="title_desc", custom_path=seeded_db)
    titles_desc = [p.title.lower() for p in sorted_title_desc]
    assert titles_desc == sorted(titles_desc, reverse=True)


# =====================================================================
# 4. Strict Product Matching & Variant Validation Tests
# =====================================================================

def test_validate_offer_exact_match():
    product = Product(
        id=1, sku="SKU-1", title="Laptop 512GB", brand="BrandA",
        category="Laptops", description="", specs={"Storage": "512GB SSD"}
    )
    valid_offer = Offer(
        id=1, product_id=1, store_id=1, store_name="Store 1", store_rating=4.5,
        current_price=1200.0, original_price=1300.0, variant_name="512GB / Gray"
    )
    is_valid, reason = validate_offer_compatibility(product, valid_offer)
    assert is_valid is True
    assert reason == "Verified Exact Match"


def test_validate_offer_rejects_contradictory_variant():
    product = Product(
        id=1, sku="SKU-1", title="Laptop 512GB", brand="BrandA",
        category="Laptops", description="", specs={"Storage": "512GB SSD"}
    )
    # Contradictory variant: offer is 128GB instead of 512GB
    mismatched_offer = Offer(
        id=2, product_id=1, store_id=2, store_name="Store 2", store_rating=4.5,
        current_price=799.0, original_price=899.0, variant_name="128GB / Gray"
    )
    is_valid, reason = validate_offer_compatibility(product, mismatched_offer)
    assert is_valid is False
    assert "Variant mismatch" in reason


def test_validate_offer_rejects_zero_or_negative_price():
    product = Product(id=2, sku="SKU-2", title="Phone", brand="BrandB", category="Phones", description="")
    zero_offer = Offer(id=3, product_id=2, store_id=1, store_name="Store 1", store_rating=4.0, current_price=0.0, original_price=0.0)
    neg_offer = Offer(id=4, product_id=2, store_id=2, store_name="Store 2", store_rating=4.0, current_price=-50.0, original_price=0.0)

    assert validate_offer_compatibility(product, zero_offer)[0] is False
    assert validate_offer_compatibility(product, neg_offer)[0] is False


def test_validate_offer_rejects_mismatched_product_id():
    product = Product(id=3, sku="SKU-3", title="Monitor", brand="BrandC", category="Monitors", description="")
    mismatched_id_offer = Offer(id=5, product_id=999, store_id=1, store_name="Store 1", store_rating=4.0, current_price=300.0, original_price=350.0)

    assert validate_offer_compatibility(product, mismatched_id_offer)[0] is False


# =====================================================================
# 5. Multi-Store Comparison, Availability & Lowest-Price Selection Tests
# =====================================================================

def test_lowest_price_selection_ignores_out_of_stock_offer():
    # Store A has cheaper price ($100), but is OUT OF STOCK.
    # Store B has price ($120), and is IN STOCK.
    # Store C has price ($140), and is IN STOCK.
    offers = [
        Offer(id=1, product_id=5, store_id=1, store_name="Store A", store_rating=4.0, current_price=100.0, availability="Out of Stock"),
        Offer(id=2, product_id=5, store_id=2, store_name="Store B", store_rating=4.5, current_price=120.0, availability="In Stock"),
        Offer(id=3, product_id=5, store_id=3, store_name="Store C", store_rating=4.2, current_price=140.0, availability="In Stock"),
    ]
    product = Product(id=5, sku="STOCK-1", title="Stock Test", brand="BrandX", category="Tech", description="", offers=offers)

    summary = generate_comparison_summary(product)
    assert summary is not None
    # Lowest AVAILABLE offer must be Store B ($120), NOT the unavailable Store A
    assert summary.lowest_available_offer is not None
    assert summary.lowest_available_offer.store_name == "Store B"
    assert summary.lowest_price == 120.0
    # Verified savings calculated between available offers: $140 - $120 = $20
    assert summary.max_price_spread == 20.0
    assert summary.has_verified_savings is True


def test_single_store_comparison_does_not_claim_verified_savings():
    offers = [
        Offer(id=1, product_id=6, store_id=1, store_name="Exclusive Retailer", store_rating=4.8, current_price=499.0, original_price=599.0, availability="In Stock")
    ]
    product = Product(id=6, sku="SINGLE-1", title="Single Store Item", brand="BrandY", category="Tech", description="", offers=offers)

    summary = generate_comparison_summary(product)
    assert summary is not None
    assert summary.is_single_store is True
    # Crucial: Must NEVER claim verified multi-store savings when only 1 store exists
    assert summary.has_verified_savings is False
    assert summary.max_price_spread == 0.0
    assert summary.potential_savings_pct == 0.0
    assert "Exclusive to Exclusive Retailer" in summary.savings_claim_explanation


def test_uniform_pricing_reports_zero_savings():
    offers = [
        Offer(id=1, product_id=7, store_id=1, store_name="Store 1", store_rating=4.2, current_price=399.0, availability="In Stock"),
        Offer(id=2, product_id=7, store_id=2, store_name="Store 2", store_rating=4.5, current_price=399.0, availability="In Stock"),
    ]
    product = Product(id=7, sku="UNIFORM-1", title="Uniform Item", brand="BrandZ", category="Audio", description="", offers=offers)

    summary = generate_comparison_summary(product)
    assert summary is not None
    assert summary.has_verified_savings is False
    assert summary.max_price_spread == 0.0
    assert "Uniform pricing" in summary.savings_claim_explanation


def test_all_offers_out_of_stock_safely_handled():
    offers = [
        Offer(id=1, product_id=8, store_id=1, store_name="Store 1", store_rating=4.0, current_price=250.0, availability="Out of Stock"),
        Offer(id=2, product_id=8, store_id=2, store_name="Store 2", store_rating=4.5, current_price=280.0, availability="Out of Stock"),
    ]
    product = Product(id=8, sku="ALL-OOS-1", title="OOS Item", brand="BrandW", category="Audio", description="", offers=offers)

    summary = generate_comparison_summary(product)
    assert summary is not None
    assert summary.available_offers_count == 0
    assert summary.lowest_available_offer is None
    assert summary.has_verified_savings is False
    assert "Out of Stock" in summary.savings_claim_explanation

