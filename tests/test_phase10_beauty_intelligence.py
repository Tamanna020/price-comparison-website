"""Phase 10: Advanced Beauty Intelligence & Personalised Product Discovery Unit Tests.

Covers:
1. Phase 10A: Master Ingredient Intelligence, Compatibility & Routine Safety Matrix
2. Phase 10B: Indian Climate-Aware Skincare Recommendation Engine
3. Phase 10C: Foundation Shade, Undertone, and Oxidation Matcher
4. Phase 10D: Multi-Criteria Advanced Beauty Product Discovery
5. REST API endpoints for all Phase 10 services
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.services.beauty_intelligence_advanced import (
    MASTER_INGREDIENTS,
    INTERACTION_MATRIX,
    CLIMATE_PROFILES,
    SHADE_BENCHMARKS,
    identify_ingredient_keys,
    check_ingredient_compatibility,
    check_routine_safety,
    get_climate_recommendations,
    match_foundation_shade,
    search_advanced_discovery,
    ROUTINE_MEDICAL_DISCLAIMER,
    FOUNDATION_MATCH_DISCLAIMER,
)


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


# =============================================================================
# 1. Phase 10A: Master Ingredient & Compatibility Matrix Tests
# =============================================================================

def test_master_ingredients_structure_and_evidence():
    """Verify master ingredients are populated with clinical and consumer fields."""
    assert len(MASTER_INGREDIENTS) >= 12
    for key, ing in MASTER_INGREDIENTS.items():
        assert ing.id == key
        assert len(ing.name) > 0
        assert len(ing.category) > 0
        assert len(ing.description) > 0
        assert len(ing.what_it_does) > 0
        assert len(ing.why_used) > 0
        assert len(ing.benefits) > 0
        assert ing.evidence_level in ["established", "moderate", "preliminary"]
        assert len(ing.keywords) > 0


def test_identify_ingredient_keys_from_text():
    """Verify keyword extraction accurately maps product titles and descriptions."""
    text_1 = "Minimalist 10% Niacinamide Face Serum with Zinc PCA"
    keys_1 = identify_ingredient_keys(text_1)
    assert "niacinamide" in keys_1

    text_2 = "Dot & Key Watermelon Cooling Sunscreen SPF 50+ PA++++ with Hyaluronic Acid"
    keys_2 = identify_ingredient_keys(text_2)
    assert "hyaluronic_acid" in keys_2
    assert "uv_filters" in keys_2

    text_3 = "Retinol Night Cream with Glycolic Acid Peel"
    keys_3 = identify_ingredient_keys(text_3)
    assert "retinol" in keys_3
    assert "glycolic_acid" in keys_3


def test_ingredient_compatibility_conflicts():
    """Test detection of high-risk active pairings."""
    # Retinol + Glycolic Acid
    res1 = check_ingredient_compatibility(["retinol", "glycolic_acid"])
    assert res1["overall_status"] == "caution"
    assert res1["safety_score"] < 60
    assert any(w["severity"] == "high_irritation_risk" for w in res1["warnings"])
    assert "Glycolic Acid" in res1["warnings"][0]["recommendation"] or "separate" in res1["warnings"][0]["recommendation"].lower()

    # Retinol + Salicylic Acid
    res2 = check_ingredient_compatibility(["retinol", "salicylic_acid"])
    assert res2["overall_status"] == "caution"
    assert any("BHA" in w["title"] or "Salicylic" in w["title"] for w in res2["warnings"])

    # Benzoyl Peroxide + Retinol
    res3 = check_ingredient_compatibility(["benzoyl_peroxide", "retinol"])
    assert any(w["severity"] == "formulation_incompatibility" for w in res3["warnings"])


def test_ingredient_compatibility_synergies():
    """Test detection of synergistic pairings."""
    # Ceramides + Hyaluronic Acid
    res = check_ingredient_compatibility(["ceramides", "hyaluronic_acid"])
    assert res["overall_status"] == "compatible"
    assert res["safety_score"] >= 90
    assert len(res["synergies"]) >= 1
    assert any("Barrier" in s["title"] or "Hydration" in s["title"] for s in res["synergies"])

    # Vitamin C + UV Filters
    res_spf = check_ingredient_compatibility(["vitamin_c", "uv_filters"])
    assert len(res_spf["synergies"]) >= 1
    assert any("Photoprotection" in s["title"] for s in res_spf["synergies"])


def test_routine_checker_sunscreen_and_photosensitivity():
    """Test routine checker flags daytime photosensitizers and missing sunscreen."""
    # AM routine with Retinol and no sunscreen
    am = [{"step_name": "Retinol Serum", "key_ingredients": ["Retinol"]}]
    pm = [{"step_name": "Gentle Cleanser"}]
    res = check_routine_safety(am, pm)

    assert res["sunscreen_compliant"] is False
    assert res["irritation_risk"] == "High"
    # Must flag daytime retinol
    assert any(c["type"] == "photosensitivity_warning" for c in res["conflicts"])
    # Must flag missing AM sunscreen
    assert any(c["type"] == "missing_sunscreen" for c in res["conflicts"])
    # Disclaimer check
    assert ROUTINE_MEDICAL_DISCLAIMER in res["medical_disclaimer"]


def test_routine_checker_duplicate_active_overload():
    """Test routine checker detects active ingredient overload across steps."""
    am = [
        {"step_name": "Niacinamide Cleanser", "key_ingredients": ["Niacinamide"]},
        {"step_name": "Niacinamide Toner", "key_ingredients": ["Niacinamide"]},
        {"step_name": "Niacinamide Serum", "key_ingredients": ["Niacinamide"]},
        {"step_name": "Sunscreen SPF 50", "key_ingredients": ["Tinosorb M"]},
    ]
    pm = [
        {"step_name": "Gentle Cleanser"},
        {"step_name": "Barrier Cream", "key_ingredients": ["Ceramides"]},
    ]
    res = check_routine_safety(am, pm)
    assert len(res["active_overloads"]) >= 1
    assert "Niacinamide" in res["active_overloads"][0]["ingredient"]
    assert res["active_overloads"][0]["count"] >= 3


def test_routine_checker_balanced_routine():
    """Test routine checker assigns top rating to balanced, compliant routine."""
    am = [
        {"step_name": "Hydrating Cleanser", "key_ingredients": ["Glycerin"]},
        {"step_name": "Vitamin C Serum", "key_ingredients": ["Vitamin C"]},
        {"step_name": "Lightweight Moisturizer", "key_ingredients": ["Hyaluronic Acid"]},
        {"step_name": "Cooling Sunscreen SPF 50+", "key_ingredients": ["Tinosorb M"]},
    ]
    pm = [
        {"step_name": "Cleansing Balm"},
        {"step_name": "Gentle Retinol", "key_ingredients": ["Retinol"]},
        {"step_name": "Ceramide Night Cream", "key_ingredients": ["Ceramides"]},
    ]
    res = check_routine_safety(am, pm)
    assert res["irritation_risk"] == "Low"
    assert res["safety_rating"] == "Optimized & Balanced"
    assert res["overall_score"] >= 95
    assert res["sunscreen_compliant"] is True


# =============================================================================
# 2. Phase 10B: Indian Climate-Aware Skincare Tests
# =============================================================================

def test_climate_profiles_coverage():
    """Verify all 6 core Indian climate conditions are profiled."""
    expected_codes = ["hot_humid", "hot_dry", "monsoon", "winter_dry", "ac_indoor", "temperate_seasonal"]
    for code in expected_codes:
        assert code in CLIMATE_PROFILES
        cp = CLIMATE_PROFILES[code]
        assert len(cp.name) > 0
        assert len(cp.regions) > 0
        assert len(cp.cleanser_guidance) > 0
        assert len(cp.moisturizer_guidance) > 0
        assert len(cp.sunscreen_guidance) > 0
        assert len(cp.recommended_actives) > 0


def test_climate_recommendations_hot_humid():
    """Test hot & humid coastal climate recommendations."""
    res = get_climate_recommendations("hot_humid", skin_type="Oily")
    assert res["climate_profile"]["code"] == "hot_humid"
    assert "Mumbai" in res["climate_profile"]["regions"] or "Chennai" in res["climate_profile"]["regions"]
    assert len(res["matched_catalog_products"]) > 0
    # Should recommend cooling / gel / sunscreen products
    titles = [p["title"] for p in res["matched_catalog_products"]]
    assert any("Cooling" in t or "Sunscreen" in t or "Niacinamide" in t for t in titles)


def test_climate_recommendations_winter_dry():
    """Test North Indian winter dryness recommendations."""
    res = get_climate_recommendations("winter_dry", skin_type="Dry")
    assert res["climate_profile"]["code"] == "winter_dry"
    assert len(res["matched_catalog_products"]) > 0
    # Should prioritize rich barrier / ceramide products
    titles = [p["title"] for p in res["matched_catalog_products"]]
    assert any("Ceramide" in t or "Hydrator" in t or "Gentle" in t for t in titles)


# =============================================================================
# 3. Phase 10C: Foundation Shade and Undertone Matcher Tests
# =============================================================================

def test_foundation_benchmarks_coverage():
    """Verify shade benchmarks cover fair through rich deep across undertones."""
    depths = {bm.depth for bm in SHADE_BENCHMARKS}
    undertones = {bm.undertone for bm in SHADE_BENCHMARKS}
    assert "fair" in depths
    assert "light_medium" in depths
    assert "medium" in depths
    assert "tan" in depths
    assert "deep" in depths
    assert "rich_deep" in depths

    assert "cool" in undertones
    assert "warm" in undertones
    assert "neutral" in undertones
    assert "olive" in undertones


def test_foundation_matching_medium_olive():
    """Test foundation matching for South Asian olive undertone."""
    res = match_foundation_shade(skin_depth="medium", undertone="olive")
    assert res["user_profile"]["skin_depth"] == "medium"
    assert res["user_profile"]["undertone"] == "olive"
    assert "Olive" in res["undertone_guidance"]
    assert len(res["matches"]) > 0
    match = res["matches"][0]
    assert match["confidence_score"] >= 80.0
    assert "Oxidation" in match["oxidation_advisory"] or "oxidation" in match["oxidation_advisory"].lower()
    assert FOUNDATION_MATCH_DISCLAIMER in res["disclaimer"]


def test_foundation_matching_with_mac_reference_shade():
    """Test calibration using reference shade converter."""
    res = match_foundation_shade(
        skin_depth="light_medium",
        undertone="warm",
        reference_brand="MAC",
        reference_shade="NC42",
    )
    # NC42 should calibrate to tan depth
    assert res["user_profile"]["skin_depth"] == "tan"
    assert len(res["matches"]) > 0


# =============================================================================
# 4. Phase 10D: Advanced Beauty Product Discovery Tests
# =============================================================================

def test_advanced_discovery_category_filter():
    """Verify filtering by category retrieves actual catalog products."""
    res = search_advanced_discovery(category="sunscreens")
    assert res["total_results"] >= 2
    for p in res["products"]:
        assert "sunscreen" in p["category"].lower() or "sunscreen" in p["title"].lower()


def test_advanced_discovery_skin_type_and_active():
    """Verify multi-factor filtering with skin type and key ingredient."""
    res = search_advanced_discovery(skin_type="Oily", ingredient="niacinamide")
    assert res["total_results"] >= 1
    titles = [p["title"] for p in res["products"]]
    assert any("Niacinamide" in t for t in titles)


def test_advanced_discovery_price_filter():
    """Verify price range constraints work properly."""
    res = search_advanced_discovery(min_price=400, max_price=600)
    for p in res["products"]:
        if p["price"] > 0:
            assert 400 <= p["price"] <= 600


# =============================================================================
# 5. REST API Integration Tests
# =============================================================================

def test_api_get_master_ingredients(client):
    """Test GET /api/beauty/ingredients endpoint."""
    response = client.get("/api/beauty/ingredients")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 12
    assert len(data["ingredients"]) >= 12
    assert "inci_name" in data["ingredients"][0]


def test_api_post_ingredient_compatibility(client):
    """Test POST /api/beauty/ingredient-compatibility endpoint."""
    payload = {"ingredients": ["retinol", "glycolic_acid"]}
    response = client.post("/api/beauty/ingredient-compatibility", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "caution"
    assert data["total_conflicts"] >= 1


def test_api_post_routine_checker(client):
    """Test POST /api/beauty/routine-checker endpoint."""
    payload = {
        "am_steps": [
            {"step_name": "Face Wash"},
            {"step_name": "SPF 50 Sunscreen", "key_ingredients": ["Tinosorb M"]},
        ],
        "pm_steps": [
            {"step_name": "Double Cleanse"},
            {"step_name": "Retinol Serum", "key_ingredients": ["Retinol"]},
        ],
        "user_skin_type": "Combination",
    }
    response = client.post("/api/beauty/routine-checker", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sunscreen_compliant"] is True
    assert data["irritation_risk"] in ["Low", "Moderate"]


def test_api_post_climate_recommendations(client):
    """Test POST /api/beauty/climate-recommendations endpoint."""
    payload = {
        "climate_code": "monsoon",
        "skin_type": "Oily",
        "concerns": ["Acne", "Enlarged Pores"],
    }
    response = client.post("/api/beauty/climate-recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["climate_profile"]["code"] == "monsoon"
    assert len(data["matched_catalog_products"]) > 0


def test_api_post_foundation_matcher(client):
    """Test POST /api/beauty/foundation-matcher endpoint."""
    payload = {
        "skin_depth": "medium",
        "undertone": "warm",
        "coverage": "Medium",
        "finish": "Matte",
    }
    response = client.post("/api/beauty/foundation-matcher", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) > 0
    assert data["matches"][0]["confidence_score"] > 80.0


def test_api_get_advanced_discovery(client):
    """Test GET /api/beauty/advanced-discovery endpoint."""
    response = client.get("/api/beauty/advanced-discovery?category=serums")
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    assert "products" in data

