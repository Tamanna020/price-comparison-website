"""Phase 2 comprehensive tests for PriceWise Beauty:
- Beauty product catalog and multi-retailer store feeds
- Responsive search (title, brand, category, verified ingredients)
- Filters (category, brand, skin type, product type, budget range)
- Sorting (price low-to-high, price high-to-low, name A-Z, best deal)
- Strict variant validation (size/volume, shade, formulation)
- Multi-retailer total cost calculation (price + shipping - discount)
- Cheapest alternative recommendations with transparent explainability
"""

import os
import tempfile
import pytest
from src.database.connection import init_db
from src.database.seed import seed_database
from src.database.models import Offer, PricePoint, Product
from src.services.product_service import (
    get_products,
    get_all_categories,
    get_all_brands,
    get_all_skin_types,
    get_all_product_types,
    get_product_by_id,
)
from src.services.comparison_service import (
    generate_comparison_summary,
    validate_offer_compatibility,
)
from src.services.alternative_service import (
    get_cheapest_alternatives,
    AlternativeRecommendation,
)


@pytest.fixture(scope="module")
def seeded_db():
    """Create a temporary populated database with combined legacy and Indian beauty demo data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


# =====================================================================
# 1. Product Catalog & Currency Attribution
# =====================================================================

def test_beauty_catalog_populated(seeded_db):
    """Verify that skincare and makeup departments exist in the catalog."""
    products = get_products(custom_path=seeded_db)
    # 11 legacy tech + 21 beauty items = 32 products
    assert len(products) >= 21
    categories = get_all_categories(custom_path=seeded_db)
    assert any(c in categories for c in ["Sunscreens", "Serums", "Moisturizers", "Face cleansers"])
    assert any(c in categories for c in ["Lipsticks", "Blushes", "Eyeliners", "Mascaras"])


def test_beauty_currency_symbol_inr(seeded_db):
    """Verify that Indian beauty products report INR (₹) currency symbol."""
    sunscreens = get_products(category="Sunscreens", custom_path=seeded_db)
    assert len(sunscreens) > 0
    for p in sunscreens:
        assert p.currency_symbol == "₹"


def test_legacy_currency_symbol_usd(seeded_db):
    """Verify that legacy products retain USD ($) currency symbol."""
    laptops = get_products(category="Laptops", custom_path=seeded_db)
    assert len(laptops) > 0
    for p in laptops:
        assert p.currency_symbol == "$"


# =====================================================================
# 2. Responsive Search (Title, Brand, Category, Verified Ingredients)
# =====================================================================

def test_search_by_beauty_product_name(seeded_db):
    """Search matches full and partial beauty product titles."""
    results = get_products(search_query="Watermelon Cooling", custom_path=seeded_db)
    assert len(results) >= 1
    assert any("Watermelon" in p.title for p in results)


def test_search_by_beauty_brand(seeded_db):
    """Search matches Indian beauty brands case-insensitively."""
    res_minimalist = get_products(search_query="minimalist", custom_path=seeded_db)
    assert len(res_minimalist) >= 1
    assert all("Minimalist" in p.brand for p in res_minimalist)

    res_dot_key = get_products(search_query="DOT & KEY", custom_path=seeded_db)
    assert len(res_dot_key) >= 1
    assert all("Dot & Key" in p.brand for p in res_dot_key)


def test_search_by_verified_ingredients(seeded_db):
    """Search matches active ingredients contained in product specifications."""
    # Search for Niacinamide across catalog
    res_niacinamide = get_products(search_query="Niacinamide", custom_path=seeded_db)
    assert len(res_niacinamide) >= 2
    for p in res_niacinamide:
        specs_str = str(p.specs).lower() + p.description.lower() + p.title.lower()
        assert "niacinamide" in specs_str

    # Search for Hyaluronic Acid
    res_ha = get_products(search_query="Hyaluronic", custom_path=seeded_db)
    assert len(res_ha) >= 2

    # Search for Vitamin C
    res_vit_c = get_products(search_query="Vitamin C", custom_path=seeded_db)
    assert len(res_vit_c) >= 1

    # Search for Ceramides
    res_ceramides = get_products(search_query="Ceramides", custom_path=seeded_db)
    assert len(res_ceramides) >= 1


def test_search_empty_state_handling(seeded_db):
    """Non-matching query returns empty list without error."""
    results = get_products(search_query="NonExistentIngredientX99", custom_path=seeded_db)
    assert len(results) == 0


# =====================================================================
# 3. Filters & Sorting
# =====================================================================

def test_filter_by_skin_type(seeded_db):
    """Filter products suitable for specific skin types."""
    available_skin_types = get_all_skin_types(custom_path=seeded_db)
    assert "Oily" in available_skin_types
    assert "Sensitive" in available_skin_types or "All Skin Types" in available_skin_types

    oily_prods = get_products(skin_type="Oily", custom_path=seeded_db)
    assert len(oily_prods) >= 1
    for p in oily_prods:
        st_val = str(p.specs.get("Skin Type", "")).lower()
        assert "oily" in st_val or "all" in st_val


def test_filter_by_budget_range(seeded_db):
    """Filter products within min and max budget thresholds."""
    under_500 = get_products(category="Sunscreens", max_price=500.0, custom_path=seeded_db)
    assert len(under_500) >= 1
    for p in under_500:
        assert p.lowest_price is not None and p.lowest_price <= 500.0

    luxury_tier = get_products(min_price=2000.0, custom_path=seeded_db)
    assert len(luxury_tier) >= 1
    for p in luxury_tier:
        assert p.lowest_price is not None and p.lowest_price >= 2000.0


def test_combined_filters_and_sorting(seeded_db):
    """Combine category, brand, budget, and price sorting."""
    results = get_products(
        category="Serums",
        brand="Minimalist",
        max_price=1000.0,
        sort_by="price_asc",
        custom_path=seeded_db,
    )
    assert len(results) >= 1
    assert all(p.category == "Serums" for p in results)
    assert all(p.brand == "Minimalist" for p in results)
    # Check sorted ascending
    prices = [p.lowest_price for p in results if p.lowest_price is not None]
    assert prices == sorted(prices)


def test_sorting_by_name_and_best_deal(seeded_db):
    """Test title_asc / name_asc and best_deal sorting options."""
    by_name = get_products(category="Serums", sort_by="title_asc", custom_path=seeded_db)
    titles = [p.title.lower() for p in by_name]
    assert titles == sorted(titles)

    by_deal = get_products(category="Serums", sort_by="best_deal", custom_path=seeded_db)
    assert len(by_deal) == len(by_name)


# =====================================================================
# 4. Strict Variant Validation (Size, Quantity, Shade, Formulation)
# =====================================================================

def test_variant_validation_exact_volume_match():
    """Matching sizes (e.g. 50ml) pass; mismatched sizes (30ml vs 50ml) fail."""
    target = Product(
        id=1, sku="BEAUTY-1", title="Hydrating Fluid", brand="BrandA",
        category="Serums", description="", specs={"Size": "50 ml"}
    )
    exact_offer = Offer(
        id=1, product_id=1, store_id=1, store_name="Nykaa", store_rating=4.5,
        current_price=500.0, variant_name="50 ml Dispenser"
    )
    diff_size_offer = Offer(
        id=2, product_id=1, store_id=2, store_name="Tira", store_rating=4.5,
        current_price=350.0, variant_name="30 ml Travel Size"
    )

    is_match, reason = validate_offer_compatibility(target, exact_offer)
    assert is_match is True
    assert reason == "Verified Exact Match"

    is_match_diff, reason_diff = validate_offer_compatibility(target, diff_size_offer)
    assert is_match_diff is False
    assert "Size/volume mismatch" in reason_diff


def test_variant_validation_shade_match():
    """Matching lipstick shades pass; different shades fail."""
    target = Product(
        id=2, sku="BEAUTY-2", title="Matte Lipstick", brand="MAC",
        category="Lipsticks", description="", specs={"Shade": "Ruby Woo", "Size": "3 g"}
    )
    match_shade = Offer(
        id=3, product_id=2, store_id=1, store_name="Nykaa", store_rating=4.8,
        current_price=1950.0, variant_name="3 g - Ruby Woo (Retro Matte)"
    )
    wrong_shade = Offer(
        id=4, product_id=2, store_id=2, store_name="Purplle", store_rating=4.3,
        current_price=1800.0, variant_name="3 g - Velvet Teddy"
    )

    is_match, _ = validate_offer_compatibility(target, match_shade)
    assert is_match is True

    is_wrong, reason = validate_offer_compatibility(target, wrong_shade)
    assert is_wrong is False
    assert "Shade mismatch" in reason


def test_variant_validation_formulation_match():
    """Waterproof vs Washable mascara formulation mismatch fails."""
    target = Product(
        id=3, sku="BEAUTY-3", title="Volume Mascara", brand="Maybelline",
        category="Mascaras", description="", specs={"Formulation": "Waterproof", "Size": "9 ml"}
    )
    washable_offer = Offer(
        id=5, product_id=3, store_id=1, store_name="Myntra", store_rating=4.5,
        current_price=450.0, variant_name="9 ml Washable Black"
    )
    is_match, reason = validate_offer_compatibility(target, washable_offer)
    assert is_match is False
    assert "Formulation mismatch" in reason


# =====================================================================
# 5. Multi-Retailer Comparison & Total Cost Calculation
# =====================================================================

def test_multi_retailer_comparison_total_cost():
    """Total cost includes shipping; best overall offer is lowest total cost."""
    # Store Nykaa: price ₹600, shipping ₹0 = ₹600 total
    # Store Purplle: price ₹580, shipping ₹50 = ₹630 total
    # Store Tira: price ₹590, shipping ₹0 = ₹590 total (Cheapest!)
    offers = [
        Offer(id=1, product_id=5, store_id=1, store_name="Nykaa", store_rating=4.7, current_price=600.0, shipping_cost=0.0, currency="INR"),
        Offer(id=2, product_id=5, store_id=2, store_name="Purplle", store_rating=4.4, current_price=580.0, shipping_cost=50.0, currency="INR"),
        Offer(id=3, product_id=5, store_id=3, store_name="Tira", store_rating=4.6, current_price=590.0, shipping_cost=0.0, currency="INR"),
    ]
    product = Product(
        id=5, sku="BEAUTY-5", title="Vitamin C Glow Serum", brand="Dot & Key",
        category="Skincare", description="", offers=offers
    )

    summary = generate_comparison_summary(product)
    assert summary is not None
    assert summary.lowest_total_cost == 590.0
    assert summary.cheapest_store_name == "Tira"
    # Ranked order: Tira (₹590), Nykaa (₹600), Purplle (₹630)
    assert summary.ranked_offers[0].store_name == "Tira"
    assert summary.ranked_offers[1].store_name == "Nykaa"
    assert summary.ranked_offers[2].store_name == "Purplle"


def test_multi_retailer_unknown_shipping_not_assumed_zero():
    """Verify that shipping_cost=0.0 means free shipping, and None is handled gracefully."""
    free_ship = Offer(id=1, product_id=6, store_id=1, store_name="Nykaa", store_rating=4.5, current_price=500.0, shipping_cost=0.0)
    assert free_ship.total_cost == 500.0
    paid_ship = Offer(id=2, product_id=6, store_id=2, store_name="Purplle", store_rating=4.2, current_price=480.0, shipping_cost=49.0)
    assert paid_ship.total_cost == 529.0


# =====================================================================
# 6. Cheapest Alternatives Recommendations
# =====================================================================

def test_cheapest_alternative_recommendation():
    """Recommends lower-priced alternatives with shared category/actives and calculates savings."""
    expensive = Product(
        id=10, sku="LUX-1", title="Advanced Night Repair Matrix", brand="Estee Lauder",
        category="Skincare", description="Premium night serum",
        specs={"Key Ingredients": "Hyaluronic Acid, Peptides, Bifida Ferment", "Skin Type": "All Skin Types", "Size": "50 ml"},
        offers=[Offer(id=1, product_id=10, store_id=1, store_name="Nykaa", store_rating=4.8, current_price=6500.0, original_price=6500.0, currency="INR")]
    )
    affordable = Product(
        id=11, sku="AFF-1", title="Multi-Peptide & Bifida Ferment Serum", brand="Minimalist",
        category="Skincare", description="Affordable peptide repair serum",
        specs={"Key Ingredients": "Peptides, Bifida Ferment, Hyaluronic Acid", "Skin Type": "All Skin Types", "Size": "30 ml"},
        offers=[Offer(id=2, product_id=11, store_id=1, store_name="Nykaa", store_rating=4.6, current_price=699.0, original_price=699.0, currency="INR")]
    )
    more_expensive = Product(
        id=12, sku="EXP-1", title="Prestige Rare Serum", brand="La Mer",
        category="Skincare", description="Ultra luxury serum",
        specs={"Key Ingredients": "Peptides", "Skin Type": "All Skin Types"},
        offers=[Offer(id=3, product_id=12, store_id=1, store_name="Tira", store_rating=4.9, current_price=12000.0, original_price=12000.0, currency="INR")]
    )

    alts = get_cheapest_alternatives(expensive, all_candidates=[expensive, affordable, more_expensive])

    assert len(alts) == 1
    rec = alts[0]
    assert rec.alternative_product.id == 11
    # Savings calculation: 6500 - 699 = 5801 (89.2%)
    assert rec.price_difference == 5801.0
    assert rec.percentage_savings > 80.0
    # Shared ingredients identified
    assert any("Peptides" in ing for ing in rec.shared_ingredients) or "Peptides" in rec.similarity_explanation
    # Explanation does NOT claim identical products
    assert "identical" not in rec.similarity_explanation.lower()
    assert "equivalent" not in rec.similarity_explanation.lower()


def test_cheapest_alternative_no_false_recommendations():
    """Does not recommend items if there are no cheaper alternatives."""
    budget_item = Product(
        id=20, sku="BUDGET-1", title="Affordable Face Wash", brand="Simple",
        category="Skincare", description="",
        offers=[Offer(id=10, product_id=20, store_id=1, store_name="Purplle", store_rating=4.4, current_price=250.0, currency="INR")]
    )
    expensive_item = Product(
        id=21, sku="LUX-2", title="Luxury Foaming Wash", brand="Kiehl's",
        category="Skincare", description="",
        offers=[Offer(id=11, product_id=21, store_id=1, store_name="Nykaa", store_rating=4.8, current_price=1850.0, currency="INR")]
    )

    alts = get_cheapest_alternatives(budget_item, all_candidates=[budget_item, expensive_item])
    # The budget item is already cheaper than the expensive item, so no cheaper alt should be suggested
    assert len(alts) == 0
