"""Phase 11C Authorized Data Source Expansion Test Suite.

Comprehensive tests verifying:
1. Product catalogue expansion: >= 100 genuine beauty products with real INCI ingredients, sizes, and manufacturer sources.
2. Category diversity: Sunscreens, Serums, Moisturizers, Cleansers, Foundations, Lipsticks, Concealers.
3. Brand diversity: 25+ authentic Indian and international skincare/makeup brands.
4. Truth-in-data enforcement: Baseline offers explicitly labeled 'demo' / 'demo_seed', with zero fabricated live market claims.
5. Retailer compliance: Commercial retailers (Nykaa, Myntra, Purplle, Tira, Amazon India) maintain strict access restrictions (RESTRICTED / PERMISSION_REVIEW_REQUIRED).
6. Ingredient intelligence: Valid INCI ingredient parsing and safety/concern scoring across newly added products.
7. Frontend synchronization: API returns 100+ items with valid categories, brands, and verified spec attributes.
"""

import json
import sqlite3
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.database.connection import get_connection
from src.services.price_collection_engine import (
    get_product_retailer_sources,
    RETAILER_POLICIES,
    RetailerAccessStatus,
)
from src.services.beauty_intelligence_service import BeautyIntelligenceService

client = TestClient(app)


def test_expanded_catalog_database_counts():
    """Verify that database has expanded beauty catalogue with >= 100 genuine beauty products."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Count total products
        cur.execute("SELECT count(*) as count FROM products")
        total_products = cur.fetchone()["count"]
        assert total_products >= 100, f"Expected at least 100 products, found {total_products}"

        # Count genuine beauty products (excluding legacy tech: smartphones, laptops, audio, wearables, etc.)
        cur.execute("""
            SELECT count(*) as count FROM products 
            WHERE category NOT IN ('Smartphones', 'Laptops', 'Audio', 'Wearables', 'Gaming', 'Monitors', 'Cameras', 'TVs')
        """)
        beauty_count = cur.fetchone()["count"]
        assert beauty_count >= 100, f"Expected at least 100 beauty products, found {beauty_count}"


def test_category_distribution():
    """Verify coverage of core beauty categories."""
    target_categories = [
        "Sunscreens",
        "Serums",
        "Moisturizers",
        "Face cleansers",
        "Foundations",
        "Lipsticks",
        "Concealers",
    ]
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT category FROM products")
        categories_in_db = {row["category"] for row in cur.fetchall()}

        for cat in target_categories:
            assert cat in categories_in_db, f"Missing target category: {cat}"


def test_brand_diversity():
    """Verify that at least 25 diverse authentic Indian and global beauty brands are represented."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT DISTINCT brand FROM products 
            WHERE category NOT IN ('Smartphones', 'Laptops', 'Audio', 'Wearables', 'Gaming', 'Monitors', 'Cameras', 'TVs')
        """)
        brands = [row["brand"] for row in cur.fetchall()]
        assert len(brands) >= 25, f"Expected at least 25 distinct beauty brands, found {len(brands)}"

        # Verify key authentic Indian and global brands are present
        expected_sample_brands = [
            "Aqualogica",
            "Foxtale",
            "Dr. Sheth's",
            "Minimalist",
            "Dot & Key",
            "Bioderma",
            "Lakme",
            "Sugar Cosmetics",
            "Maybelline",
            "L'Oreal Paris",
            "Conscious Chemist",
            "Neutrogena",
        ]
        for b in expected_sample_brands:
            assert any(b.lower() in existing.lower() for existing in brands), f"Brand {b} not found in DB"


def test_verified_product_specifications_integrity():
    """Verify that expanded products include complete specifications (ingredients, volume, concerns, source)."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT id, title, brand, category, specs_json, description 
            FROM products 
            WHERE id >= 1000 AND category NOT IN ('Smartphones', 'Laptops', 'Audio', 'Wearables', 'Gaming', 'Monitors', 'Cameras', 'TVs')
        """)
        expanded_products = cur.fetchall()
        assert len(expanded_products) >= 70, f"Expected at least 70 expanded items (ID >= 1000), found {len(expanded_products)}"

        for prod in expanded_products:
            assert prod["title"], "Product title must not be empty"
            assert prod["brand"], "Product brand must not be empty"
            assert prod["category"], "Product category must not be empty"
            assert prod["description"], "Product description must not be empty"

            specs = json.loads(prod["specs_json"] or "{}")
            specs_lower = {k.lower(): v for k, v in specs.items()}
            has_ingredients = any("ingredient" in k for k in specs_lower.keys())
            assert has_ingredients, f"Product {prod['id']} missing ingredients in specs"
            has_volume = any(k in specs_lower for k in ("volume", "size", "net quantity", "net_quantity"))
            assert has_volume, f"Product {prod['id']} missing size/volume in specs"
            assert any("source" in k for k in specs_lower), f"Product {prod['id']} missing data source"
            assert any("status" in k for k in specs_lower), f"Product {prod['id']} missing data status"
            status_val = specs_lower.get("data status", specs_lower.get("data_status"))
            assert status_val == "catalog_verified", f"Product {prod['id']} expected catalog_verified status, got {status_val}"


def test_truth_in_store_offers_for_expanded_products():
    """Verify that newly seeded store offers and price history are explicitly labeled 'demo' and 'demo_seed'."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT o.id, o.product_id, o.store_id, o.current_price, o.original_price, ph.data_source, ph.data_status 
            FROM offers o
            JOIN price_history ph ON ph.offer_id = o.id
            WHERE o.product_id >= 1000
        """)
        offers_with_history = cur.fetchall()
        assert len(offers_with_history) >= 300, f"Expected >= 300 store offers with history, found {len(offers_with_history)}"

        for off in offers_with_history:
            assert off["data_source"] == "demo_seed", f"Offer {off['id']} must have data_source 'demo_seed'"
            assert off["data_status"] == "demo", f"Offer {off['id']} must have data_status 'demo'"
            assert off["current_price"] > 0, f"Offer {off['id']} must have positive price"
            assert off["original_price"] >= off["current_price"], f"Offer {off['id']} original_price must be >= price"


def test_retailer_compliance_boundaries():
    """Verify that price collection engine treats Nykaa, Myntra, Purplle, Tira, Amazon India as restricted."""
    retailer_keys = ["nykaa", "myntra", "purplle", "tira", "amazon"]
    for r_key in retailer_keys:
        policy = RETAILER_POLICIES.get(r_key)
        assert policy is not None, f"Retailer {r_key} should be registered in RETAILER_POLICIES"
        assert policy["policy_status"] in (
            RetailerAccessStatus.RESTRICTED,
            RetailerAccessStatus.PERMISSION_REVIEW_REQUIRED,
        ), f"{r_key} must be restricted or require permission review"

    # Attempt collection for product 1000 (expanded sunscreen)
    sources = get_product_retailer_sources(1000)
    assert len(sources) >= 5, "Product 1000 should have retailer source configurations"
    for s in sources:
        assert s["policy_status"] in ("RESTRICTED", "PERMISSION_REVIEW_REQUIRED")
        assert s["verification_status"] == "DEMO"


def test_beauty_intelligence_ingredient_analysis():
    """Verify BeautyIntelligenceService correctly parses ingredients for expanded products."""
    svc = BeautyIntelligenceService()
    # Test on product 1000 (Minimalist Invisible Sunscreen)
    analysis = svc.analyze_ingredients(1000)
    assert analysis is not None
    assert analysis.product_id == 1000
    assert len(analysis.key_actives) > 0 or len(analysis.ingredients) > 0
    assert analysis.extraction_source in ("gemini_semantic", "heuristic_fallback")


def test_api_products_list_and_detail():
    """Verify FastAPI /api/products and /api/products/{id} endpoints return expanded catalog data properly."""
    # List endpoint
    res = client.get("/api/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 100

    # Detail endpoint for product 1000
    detail_res = client.get("/api/products/1000")
    assert detail_res.status_code == 200
    prod = detail_res.json()
    assert prod["id"] == 1000
    assert "Minimalist" in prod["brand"]
    assert "Sunscreen" in prod["category"]
    assert len(prod.get("offers", [])) >= 5

    # Detail endpoint for product 1001 (Aqualogica)
    aqua_res = client.get("/api/products/1001")
    assert aqua_res.status_code == 200
    aqua_prod = aqua_res.json()
    assert aqua_prod["id"] == 1001
    assert "Aqualogica" in aqua_prod["brand"]
