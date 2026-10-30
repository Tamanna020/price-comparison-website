"""Phase 5 Comprehensive Test Suite: Smart Purchase Advisor.

Tests cover all 11 core functional and explainability requirements:
1. Budget compliance & headroom/overrun calculation
2. Total cost including shipping calculation
3. Category and use-case matching & suitability scoring
4. Missing specifications handling (treated as unknown, never assumed)
5. Unavailable / out-of-stock product handling
6. Incorrect product variant isolation
7. Recommendation ranking logic
8. Best Overall, Best Budget, and Best Current Deal selection
9. Insufficient historical evidence handling
10. No suitable product found & closest alternatives generation
11. Recommendation explanation consistency & score breakdown
"""

from datetime import datetime, timezone
import tempfile
import os
import pytest

from src.database.models import Offer, PricePoint, Product
from src.database.seed import seed_database
from src.services.recommendation_service import (
    AdvisorPreferences,
    ProductEvaluation,
    RecommendationResult,
    evaluate_product_for_advisor,
    get_purchase_recommendations,
    extract_ram_gb,
    extract_storage_gb,
    extract_battery_hours,
    has_4k_display,
    has_anc,
    has_discrete_gpu,
)


@pytest.fixture(scope="module")
def p5_test_db():
    """Temporary seeded database for Phase 5 tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


# =====================================================================
# 1. Budget Compliance
# =====================================================================

def test_p5_01_budget_compliance():
    """Verify products above budget are not recommended as satisfying budget, with accurate headroom/overrun."""
    # Product costing $1,200 total
    offer = Offer(id=1, product_id=1, store_id=1, store_name="Store 1", store_rating=4.5, current_price=1180.0, shipping_cost=20.0, availability="In Stock")
    prod = Product(id=1, sku="SKU-BUDGET", title="Laptop A", brand="BrandA", category="Laptops", description="", offers=[offer])

    # Case A: Budget is $1,500 -> Satisfied with $300 headroom (20%)
    pref_ok = AdvisorPreferences(budget=1500.0, category="Laptops", use_case="Everyday Use")
    eval_ok = evaluate_product_for_advisor(prod, pref_ok)
    assert eval_ok.budget_fit is True
    assert eval_ok.total_cost == 1200.0
    assert eval_ok.budget_difference == 300.0
    assert eval_ok.budget_difference_pct == 20.0
    assert eval_ok.is_fully_suitable is True
    assert len(eval_ok.failed_hard_requirements) == 0

    # Case B: Budget is $1,000 -> Fails with $200 overrun
    pref_over = AdvisorPreferences(budget=1000.0, category="Laptops", use_case="Everyday Use")
    eval_over = evaluate_product_for_advisor(prod, pref_over)
    assert eval_over.budget_fit is False
    assert eval_over.total_cost == 1200.0
    assert eval_over.budget_difference == -200.0
    assert eval_over.is_fully_suitable is False
    assert any("exceeds budget" in f.lower() for f in eval_over.failed_hard_requirements)


# =====================================================================
# 2. Total Cost and Shipping Calculation
# =====================================================================

def test_p5_02_total_cost_including_shipping():
    """Verify lowest available offer selection is based on total cost (item price + shipping)."""
    # Offer A: $500 item + $50 shipping = $550 total
    # Offer B: $520 item + $0 shipping = $520 total (Cheaper total checkout!)
    offer_a = Offer(id=1, product_id=2, store_id=1, store_name="Store HighShip", store_rating=4.0, current_price=500.0, shipping_cost=50.0, availability="In Stock")
    offer_b = Offer(id=2, product_id=2, store_id=2, store_name="Store FreeShip", store_rating=4.5, current_price=520.0, shipping_cost=0.0, availability="In Stock")
    prod = Product(id=2, sku="SKU-SHIP", title="Monitor B", brand="BrandB", category="Monitors", description="", offers=[offer_a, offer_b])

    pref = AdvisorPreferences(budget=600.0, category="Monitors")
    evaluation = evaluate_product_for_advisor(prod, pref)
    
    # Store FreeShip must be selected because $520 < $550
    assert evaluation.store_name == "Store FreeShip"
    assert evaluation.base_price == 520.0
    assert evaluation.shipping_cost == 0.0
    assert evaluation.total_cost == 520.0


# =====================================================================
# 3. Category and Use-Case Matching
# =====================================================================

def test_p5_03_category_and_use_case_matching():
    """Verify category filtering enforces match and use cases assign appropriate suitability scores."""
    prod_laptop = Product(
        id=3, sku="SKU-LAP", title="Dev Laptop", brand="BrandC", category="Laptops", description="",
        specs={"RAM": "32GB", "Storage": "1TB SSD"},
        offers=[Offer(id=3, product_id=3, store_id=1, store_name="Store 1", store_rating=4.5, current_price=1500.0, availability="In Stock")]
    )
    prod_tv = Product(
        id=4, sku="SKU-TV", title="Living Room TV", brand="BrandD", category="TVs", description="",
        specs={"Screen Size": "65 Inch", "Refresh Rate": "120Hz"},
        offers=[Offer(id=4, product_id=4, store_id=1, store_name="Store 1", store_rating=4.5, current_price=1200.0, availability="In Stock")]
    )

    # For Programming use case, Laptop with 32GB RAM should score significantly higher than a TV
    pref_prog = AdvisorPreferences(budget=2000.0, category="All", use_case="Programming")
    eval_laptop = evaluate_product_for_advisor(prod_laptop, pref_prog)
    eval_tv = evaluate_product_for_advisor(prod_tv, pref_prog)

    assert eval_laptop.suitability_score > eval_tv.suitability_score
    assert eval_laptop.suitability_score >= 90.0

    # Category filter hard check
    pref_only_laptops = AdvisorPreferences(budget=2000.0, category="Laptops", use_case="Everyday Use")
    eval_tv_filtered = evaluate_product_for_advisor(prod_tv, pref_only_laptops)
    assert eval_tv_filtered.is_fully_suitable is False
    assert any("category mismatch" in f.lower() for f in eval_tv_filtered.failed_hard_requirements)


# =====================================================================
# 4. Missing Specifications Handling
# =====================================================================

def test_p5_04_missing_specifications_treated_as_unknown():
    """Verify missing specs are never silently assumed to meet requirements and are flagged."""
    # Product without RAM recorded
    prod_no_ram = Product(
        id=5, sku="SKU-NORAM", title="Mystery Laptop", brand="BrandE", category="Laptops", description="",
        specs={"Storage": "512GB"},  # No RAM spec
        offers=[Offer(id=5, product_id=5, store_id=1, store_name="Store 1", store_rating=4.0, current_price=800.0, availability="In Stock")]
    )

    # User requires at least 16GB RAM
    pref_ram = AdvisorPreferences(budget=1000.0, category="Laptops", min_ram_gb=16)
    evaluation = evaluate_product_for_advisor(prod_no_ram, pref_ram)

    # Must NOT pass the requirement!
    assert evaluation.is_fully_suitable is False
    assert any("RAM capacity is unrecorded" in f for f in evaluation.failed_hard_requirements)
    assert any("RAM capacity not recorded" in c for c in evaluation.cautions_or_missing_specs)


# =====================================================================
# 5. Unavailable / Out-of-Stock Product Handling
# =====================================================================

def test_p5_05_unavailable_products_handling():
    """Verify out-of-stock offers are not recommended as active purchase options."""
    offer_oos = Offer(
        id=6, product_id=6, store_id=1, store_name="Store OOS", store_rating=4.0,
        current_price=300.0, availability="Out of Stock"
    )
    prod_oos = Product(id=6, sku="SKU-OOS", title="Rare Camera", brand="BrandF", category="Cameras", description="", offers=[offer_oos])

    pref = AdvisorPreferences(budget=500.0, category="Cameras", require_in_stock=True)
    evaluation = evaluate_product_for_advisor(prod_oos, pref)

    assert evaluation.is_available is False
    assert evaluation.is_fully_suitable is False
    assert any("out of stock" in f.lower() for f in evaluation.failed_hard_requirements)


# =====================================================================
# 6. Incorrect Product Variants Isolation
# =====================================================================

def test_p5_06_incorrect_product_variants_isolated():
    """Verify that offers with contradictory specs/variants are excluded from recommendation pricing."""
    # Product specification is 512GB SSD
    # Offer 1: Contradictory variant (128GB) at $400
    # Offer 2: Verified exact variant (512GB) at $900
    offer_bad = Offer(id=7, product_id=7, store_id=1, store_name="Store Bad", store_rating=4.0, current_price=400.0, variant_name="128GB", availability="In Stock")
    offer_good = Offer(id=8, product_id=7, store_id=2, store_name="Store Good", store_rating=4.5, current_price=900.0, variant_name="512GB SSD", availability="In Stock")
    prod = Product(
        id=7, sku="SKU-VAR", title="Tablet Pro", brand="BrandG", category="Laptops", description="",
        specs={"Storage": "512GB SSD"},
        offers=[offer_bad, offer_good]
    )

    pref = AdvisorPreferences(budget=1000.0, category="Laptops")
    evaluation = evaluate_product_for_advisor(prod, pref)

    # Must select Offer 2 ($900), NOT Offer 1 ($400) because Offer 1 has a contradictory variant!
    assert evaluation.best_offer.id == 8
    assert evaluation.total_cost == 900.0
    assert evaluation.store_name == "Store Good"


# =====================================================================
# 7. Recommendation Ranking Logic
# =====================================================================

def test_p5_07_recommendation_ranking_order(p5_test_db):
    """Verify recommendation ranking orders candidates by composite recommendation score."""
    pref = AdvisorPreferences(
        budget=2000.0,
        category="All",
        use_case="Studying",
    )
    result = get_purchase_recommendations(pref, custom_path=p5_test_db)
    
    assert len(result.ranked_candidates) > 0
    scores = [c.recommendation_score for c in result.ranked_candidates]
    # Verify sorted strictly descending
    assert scores == sorted(scores, reverse=True)


# =====================================================================
# 8. Best Overall, Best Budget, and Best Current Deal Selection
# =====================================================================

def test_p5_08_best_categories_selection(p5_test_db):
    """Verify Best Overall, Best Budget, and Best Current Deal selection criteria."""
    pref = AdvisorPreferences(
        budget=2000.0,
        category="Laptops",
        use_case="Programming",
    )
    result = get_purchase_recommendations(pref, custom_path=p5_test_db)

    # Must produce a Best Overall
    assert result.best_overall is not None
    assert result.best_overall.product.category == "Laptops"
    assert result.best_overall.total_cost <= 2000.0

    # Must produce a Best Budget option
    assert result.best_budget is not None
    assert result.best_budget.total_cost <= 2000.0
    # Best Budget total cost must be less than or equal to Best Overall total cost
    assert result.best_budget.total_cost <= result.best_overall.total_cost

    # If Best Current Deal is present, it MUST have deal_score >= 65 and is_good_value=True
    if result.best_deal:
        assert result.best_deal.deal_score is not None
        assert result.best_deal.deal_score >= 65
        assert result.best_deal.is_good_value is True


# =====================================================================
# 9. Insufficient Historical Evidence Handling
# =====================================================================

def test_p5_09_insufficient_historical_evidence_handling():
    """Verify products with scarce history withhold Deal Score and cannot be chosen as Best Current Deal."""
    # Product with 0 price history
    offer = Offer(id=9, product_id=9, store_id=1, store_name="Store New", store_rating=4.5, current_price=100.0, availability="In Stock", price_history=[])
    prod = Product(id=9, sku="SKU-NOHIST", title="New Gadget", brand="BrandH", category="Audio", description="", offers=[offer])

    pref = AdvisorPreferences(budget=200.0, category="Audio")
    eval_item = evaluate_product_for_advisor(prod, pref)

    assert eval_item.deal_score is None
    assert eval_item.deal_classification == "INSUFFICIENT DATA"
    assert eval_item.is_good_value is False
    assert any("integrity" in c.lower() for c in eval_item.cautions_or_missing_specs)


# =====================================================================
# 10. No Suitable Product Found & Closest Alternatives
# =====================================================================

def test_p5_10_no_suitable_product_found_and_closest_alternatives(p5_test_db):
    """Verify when budget is impossible, 0 suitable products are returned and closest alternatives are generated."""
    # Set budget to $500 for Laptops (all demo laptops cost >= $1,799)
    impossible_pref = AdvisorPreferences(
        budget=500.0,
        category="Laptops",
        use_case="Programming",
    )
    result = get_purchase_recommendations(impossible_pref, custom_path=p5_test_db)

    # Suitable candidates must be empty
    assert len(result.ranked_candidates) == 0
    assert result.best_overall is None
    assert result.best_budget is None

    # Closest alternatives must be populated
    assert len(result.closest_alternatives) > 0
    # Alternatives must clearly explain the budget overrun failure
    for alt in result.closest_alternatives:
        assert alt.is_fully_suitable is False
        assert any("exceeds budget" in f.lower() for f in alt.failed_hard_requirements)


# =====================================================================
# 11. Explanation Consistency & Score Breakdown
# =====================================================================

def test_p5_11_explanation_consistency_and_score_breakdown(p5_test_db):
    """Verify every evaluated candidate has non-empty reasons and mathematical score breakdown."""
    pref = AdvisorPreferences(
        budget=1200.0,
        category="Smartphones",
        use_case="Photography",
    )
    result = get_purchase_recommendations(pref, custom_path=p5_test_db)

    assert len(result.all_evaluated) > 0
    for eval_item in result.all_evaluated:
        # Score breakdown contains the 4 components and composite
        b = eval_item.score_breakdown
        assert "Suitability (40%)" in b
        assert "Specifications (30%)" in b
        assert "Budget Efficiency (20%)" in b
        assert "Brand Match (10%)" in b
        assert "Composite Total" in b
        assert len(eval_item.reasons) > 0

