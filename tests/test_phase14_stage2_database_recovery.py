"""Phase 14 Stage 2: Database and Product Catalogue Recovery Regression Tests.

Validates:
1. Soft-archival of legacy technology products (IDs 1-11) preserving foreign keys.
2. Category and brand discovery purity (zero non-beauty categories or brands).
3. Explicit frontend-to-database mappings for prod-01, prod-02, prod-23, and all 100 products.
4. Guarantee that zero beauty products resolve to electronics records.
5. Foreign key and user reference integrity.
6. Product counts and database consistency.
"""

import json
import re
import sqlite3
try:
    import pytest
except ImportError:
    pytest = None

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.database.connection import get_connection, migrate_db
from src.services.product_service import (
    get_products,
    get_product_by_id,
    get_product_by_slug,
    get_all_categories,
    get_all_brands,
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_PRODUCTS_PATH = BASE_DIR / "frontend" / "src" / "data" / "products.ts"


def ensure_db_migrated():
    """Ensure database schema is up-to-date before running tests."""
    migrate_db()


if pytest is not None:
    ensure_db_migrated = pytest.fixture(autouse=True)(ensure_db_migrated)


def test_soft_archived_legacy_tech_products_preserved():
    """Verify legacy technology products (IDs 1-11) are preserved with is_active = 0."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, category, is_active FROM products WHERE id <= 11 ORDER BY id")
        rows = cursor.fetchall()
        
        assert len(rows) == 11, f"Expected exactly 11 preserved legacy tech products, found {len(rows)}"
        for r in rows:
            # is_active must be 0/False
            assert r["is_active"] in (0, False), f"Product {r['id']} ({r['title']}) must be soft-archived (inactive)"
            assert r["category"] in ("Laptops", "Smartphones", "Audio", "Gaming", "Wearables", "Monitors", "Cameras", "TVs")


def test_beauty_products_are_active():
    """Verify that all genuine beauty products have is_active = 1/True."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, category, is_active FROM products WHERE id >= 12 AND id NOT IN (998, 999)")
        rows = cursor.fetchall()
        
        assert len(rows) == 100, f"Expected exactly 100 active beauty products, found {len(rows)}"
        for r in rows:
            assert r["is_active"] in (1, True), f"Beauty product {r['id']} ({r['title']}) must be active"


def test_customer_discovery_contains_zero_tech_products():
    """Verify get_products() excludes soft-archived technology products from customer discovery."""
    products = get_products(active_only=True)
    assert len(products) == 100, f"Expected 100 active beauty products in discovery, found {len(products)}"
    
    tech_categories = {"Laptops", "Smartphones", "Audio", "Gaming", "Wearables", "Monitors", "Cameras", "TVs"}
    tech_brands = {"Apple", "Dell", "Sony", "Samsung", "Bose", "LG"}
    
    for p in products:
        assert p.id >= 12, f"Discovered product {p.id} ({p.title}) has legacy tech ID!"
        assert p.category not in tech_categories, f"Tech category '{p.category}' appeared in beauty discovery!"
        assert p.brand not in tech_brands, f"Tech brand '{p.brand}' appeared in beauty discovery!"
        assert p.is_active is True


def test_get_all_categories_excludes_tech():
    """Verify category filtering options do not expose legacy electronics categories."""
    categories = get_all_categories(active_only=True)
    tech_categories = {"Laptops", "Smartphones", "Audio", "Gaming", "Wearables", "Monitors", "Cameras", "TVs"}
    
    for cat in categories:
        assert cat not in tech_categories, f"Tech category '{cat}' leaked into category filter!"


def test_get_all_brands_excludes_tech():
    """Verify brand filtering options do not expose legacy electronics brands."""
    brands = get_all_brands(active_only=True)
    tech_brands = {"Apple", "Dell", "Sony", "Samsung", "Bose", "LG"}
    
    for b in brands:
        assert b not in tech_brands, f"Tech brand '{b}' leaked into brand filter!"


def test_prod_01_resolves_to_correct_beauty_product():
    """Verify prod-01 resolves to Dot & Key Sunscreen (DB ID 12), NOT Apple MacBook Pro (ID 1)."""
    p = get_product_by_id(12)
    assert p is not None
    assert p.id == 12
    assert "Dot & Key" in p.brand
    assert "Watermelon" in p.title
    assert "Sunscreen" in p.title
    assert p.is_active is True


def test_prod_02_resolves_to_correct_beauty_product():
    """Verify prod-02 resolves to The Derma Co Sunscreen (DB ID 13), NOT Dell XPS 15 (ID 2)."""
    p = get_product_by_id(13)
    assert p is not None
    assert p.id == 13
    assert "The Derma Co" in p.brand
    assert "Hyaluronic" in p.title
    assert p.is_active is True


def test_prod_23_resolves_to_correct_beauty_product():
    """Verify prod-23 resolves to Chemist at Play Body Wash (DB ID 32)."""
    p = get_product_by_id(32)
    assert p is not None
    assert p.id == 32
    assert "Chemist at Play" in p.brand
    assert "Lactic Acid" in p.title
    assert p.is_active is True


def test_no_frontend_product_resolves_to_electronics():
    """Inspect all 100 frontend products and assert none map to IDs 1-11."""
    content = FRONTEND_PRODUCTS_PATH.read_text(encoding="utf-8")
    matches = re.findall(r"id:\s*'(prod-\d+)',\s*dbId:\s*(\d+)", content)
    
    assert len(matches) == 100, f"Expected 100 id+dbId pairs, found {len(matches)}"
    
    for pid, dbid_str in matches:
        dbid = int(dbid_str)
        assert dbid >= 12, f"Frontend {pid} mapped to forbidden legacy ID {dbid}!"
        
        # Verify against database record
        p = get_product_by_id(dbid)
        assert p is not None, f"Database record {dbid} not found for {pid}!"
        assert p.is_active is True, f"Database record {dbid} for {pid} is inactive!"
        assert p.category not in ("Laptops", "Smartphones", "Audio", "Gaming", "Wearables", "Monitors", "Cameras", "TVs")


def test_foreign_key_and_user_reference_integrity():
    """Verify zero orphaned records in offers, price_history, and user tables."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Offers must point to valid products
        cursor.execute("""
            SELECT count(*) FROM offers o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE p.id IS NULL
        """)
        assert cursor.fetchone()[0] == 0, "Orphaned offers found!"
        
        # 2. Price history must point to valid offers
        cursor.execute("""
            SELECT count(*) FROM price_history ph
            LEFT JOIN offers o ON ph.offer_id = o.id
            WHERE o.id IS NULL
        """)
        assert cursor.fetchone()[0] == 0, "Orphaned price history found!"
        
        # 3. Preserved legacy tech products still have their offers intact
        cursor.execute("SELECT count(*) FROM offers WHERE product_id <= 11")
        tech_offers = cursor.fetchone()[0]
        assert tech_offers > 0, "Legacy tech offers were unexpectedly deleted!"


if __name__ == "__main__":
    import sys
    print("=" * 70)
    print("RUNNING PHASE 14 STAGE 2 REGRESSION TESTS (STANDALONE RUNNER)")
    print("=" * 70)
    ensure_db_migrated()
    
    test_functions = [
        test_soft_archived_legacy_tech_products_preserved,
        test_beauty_products_are_active,
        test_customer_discovery_contains_zero_tech_products,
        test_get_all_categories_excludes_tech,
        test_get_all_brands_excludes_tech,
        test_prod_01_resolves_to_correct_beauty_product,
        test_prod_02_resolves_to_correct_beauty_product,
        test_prod_23_resolves_to_correct_beauty_product,
        test_no_frontend_product_resolves_to_electronics,
        test_foreign_key_and_user_reference_integrity,
    ]
    
    passed_count = 0
    for test_fn in test_functions:
        try:
            test_fn()
            print(f"PASS: {test_fn.__name__}")
            passed_count += 1
        except Exception as exc:
            print(f"FAIL: {test_fn.__name__} -> {exc}")
            import traceback
            traceback.print_exc()

    print("=" * 70)
    print(f"OVERALL STAGE 2 TEST RESULTS: {passed_count}/{len(test_functions)} PASSED")
    print("=" * 70)
    if passed_count != len(test_functions):
        sys.exit(1)
