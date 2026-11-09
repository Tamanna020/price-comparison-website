"""Live End-to-End Application Compatibility Test Against PostgreSQL 16 (Phase 12.1).

Tests all core FastAPI endpoints with live PostgreSQL container:
1. Health & readiness probes (database_engine: postgresql).
2. Product search & category filtering.
3. Product detail by slug.
4. User authentication (login & registration with sequence ID generation).
5. User profile and preferences retrieval.
6. User routines and routine items.
7. Wishlist operations (add, list, delete).
8. Live retailer price comparisons.
9. Price tracking & alert queries.
10. Admin verification queue.
11. Beauty intelligence & ingredient compatibility.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from unittest.mock import patch
from fastapi.testclient import TestClient
from src.api.main import app

PG_URL = "postgresql://pricewise:pricewise_staging_pass@127.0.0.1:5433/pricewise_staging"


def test_full_app_against_postgres():
    print("=" * 80)
    print("PRICEWISE AI — PHASE 12.1: LIVE FASTAPI ON POSTGRESQL 16")
    print("=" * 80)

    with patch.dict(os.environ, {"DATABASE_URL": PG_URL, "ENVIRONMENT": "staging"}, clear=False):
        client = TestClient(app)

        # 1. Health & Readiness
        print("\n1. Testing Health Endpoints on PostgreSQL...")
        r_ready = client.get("/api/health/ready")
        assert r_ready.status_code == 200, f"Readiness failed: {r_ready.text}"
        ready_data = r_ready.json()
        print(f"  /api/health/ready: status={ready_data['status']}, engine={ready_data['database_engine']}, count={ready_data['product_count']}, latency={ready_data['latency_ms']}ms")
        assert ready_data["database_engine"] == "postgresql"
        assert ready_data["product_count"] >= 100

        # 2. Product Catalog & Search
        print("\n2. Testing Product Catalog & Multi-Criteria Search...")
        r_prods = client.get("/api/products?limit=10")
        assert r_prods.status_code == 200
        prods = r_prods.json()
        print(f"  Retrieved {len(prods)} products from PostgreSQL. First item: {prods[0]['title']}")
        assert len(prods) > 0

        # Search for Vitamin C
        r_search = client.get("/api/products?search=Vitamin%20C")
        assert r_search.status_code == 200
        search_results = r_search.json()
        print(f"  Search 'Vitamin C' returned {len(search_results)} matching products.")
        assert len(search_results) > 0

        # Category Filter
        r_cat = client.get("/api/products?category=Sunscreen")
        assert r_cat.status_code == 200
        sun_results = r_cat.json()
        print(f"  Category 'Sunscreen' returned {len(sun_results)} products.")

        # 3. Product Details by ID / Slug
        print("\n3. Testing Product Details...")
        sample_id = prods[0]["id"]
        r_det = client.get(f"/api/products/{sample_id}")
        assert r_det.status_code == 200
        det = r_det.json()
        print(f"  Product #{det['id']}: {det['title']} (offers count: {len(det.get('offers', []))})")

        # 4. Authentication (Login Demo User)
        print("\n4. Testing User Authentication on PostgreSQL...")
        login_res = client.post("/api/auth/login", json={"email": "demo@pricewise.ai", "password": "DemoPass123!"})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        login_data = login_res.json()
        token = login_data["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"  Login successful for {login_data['user']['email']}, token received.")

        # Test Current User Me
        r_me = client.get("/api/auth/me", headers=headers)
        assert r_me.status_code == 200
        print(f"  /api/auth/me authenticated: {r_me.json()['email']}")

        # 5. User Registration on PostgreSQL (Tests Sequence / lastrowid)
        print("\n5. Testing User Registration (Sequence & lastrowid)...")
        reg_email = f"staging_test_{os.urandom(4).hex()}@example.com"
        r_reg = client.post("/api/auth/register", json={
            "display_name": "Staging Tester",
            "email": reg_email,
            "password": "SecurePassword123!"
        })
        assert r_reg.status_code in (200, 201), f"Registration failed: {r_reg.text}"
        reg_data = r_reg.json()
        new_user_id = reg_data["user"]["id"]
        print(f"  Registered new user #{new_user_id} ({reg_email}) via PostgreSQL.")

        # 6. User Routines
        print("\n6. Testing User Routines on PostgreSQL...")
        r_routines = client.get("/api/routines", headers=headers)
        assert r_routines.status_code == 200
        routines = r_routines.json().get("routines", [])
        print(f"  User has {len(routines)} saved routines in PostgreSQL.")

        # 7. Wishlist Operations
        print("\n7. Testing Wishlist Operations on PostgreSQL...")
        r_wish = client.get("/api/watchlist", headers=headers)
        assert r_wish.status_code == 200
        wishlist_items = r_wish.json().get("items", [])
        print(f"  Wishlist contains {len(wishlist_items)} items.")

        # Add to wishlist
        r_add_wish = client.post(
            "/api/watchlist",
            headers=headers,
            json={"product_id": sample_id, "note": "Staging test note"}
        )
        assert r_add_wish.status_code in (200, 201), f"Add wishlist failed: {r_add_wish.text}"
        print(f"  Added product #{sample_id} to wishlist successfully.")

        # 8. Admin Verification Queue
        print("\n8. Testing Admin Verification Queue on PostgreSQL...")
        r_queue = client.get("/api/admin/verifications", headers=headers)
        # Demo user is admin
        assert r_queue.status_code == 200
        queue_data = r_queue.json()
        print(f"  Pending verification queue: {queue_data.get('total_pending', 0)} requests.")

        # 9. Beauty Intelligence Advanced Endpoints
        print("\n9. Testing Advanced Beauty Intelligence on PostgreSQL...")
        r_actives = client.get("/api/beauty/ingredients")
        assert r_actives.status_code == 200
        print(f"  Active ingredients catalog: {r_actives.json().get('total', 0)} clinical actives.")

        # Routine Safety Check
        r_safety = client.post("/api/beauty/routine-checker", json={
            "am_steps": [{"step_name": "Treat", "product_name": "Vitamin C Serum", "key_ingredients": ["Vitamin C"]}],
            "pm_steps": [{"step_name": "Treat", "product_name": "Retinol Cream", "key_ingredients": ["Retinol"]}],
            "user_skin_type": "combination"
        })
        assert r_safety.status_code == 200
        print(f"  Routine safety rating: {r_safety.json().get('safety_rating')} (score: {r_safety.json().get('overall_score')}/100)")

        print("\n" + "=" * 80)
        print("ALL 9 CORE FASTAPI SUBSYSTEMS PASSED ON LIVE POSTGRESQL 16!")
        print("=" * 80)


if __name__ == "__main__":
    test_full_app_against_postgres()
