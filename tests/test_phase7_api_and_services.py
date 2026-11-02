"""Phase 7 Test Suite: Secure Authentication, User Profiles, Personalized Routines & Watchlist Synchronization.

Tests:
1. Authentication endpoints (/api/auth/register, /api/auth/login, /api/auth/logout, /api/auth/me).
2. Password security (PBKDF2-HMAC-SHA256, salting, constant-time verification, no plaintext hashes).
3. Session token management (signed HMAC-SHA256, Bearer header, and HTTP-only cookie support).
4. Beauty Profile endpoints (/api/profile GET, PUT, DELETE) & IDOR protection.
5. Personalized Skincare Routines (/api/routines, step addition, reordering, deletion).
6. Active ingredient conflict detection (Retinoids + AHA/BHA, Vit C + Retinol, SPF reminders).
7. Watchlist synchronization (/api/watchlist, /api/watchlist/sync, delete, multi-user isolation).
8. Catalog-driven personalized recommendations (/api/recommendations/personalized).
9. Cosmetic non-medical disclaimers.
"""

import uuid
import unittest
from starlette.testclient import TestClient

from src.api.main import app
from src.services.auth_service import hash_password, verify_password, generate_session_token, verify_session_token
from src.services.routine_service import detect_ingredient_conflicts


class TestPhase7AuthAndSecurity(unittest.TestCase):
    """Test suite for authentication, tokens, and password cryptography."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.unique_suffix = uuid.uuid4().hex[:8]

    def test_password_hashing_and_verification(self):
        """Verify PBKDF2 salted password hashing and constant-time verification."""
        raw_pw = "SuperSecretBeautyPassword123!"
        hashed = hash_password(raw_pw)

        # Ensure hash contains algorithm, iterations, salt, and hash components
        parts = hashed.split("$")
        self.assertEqual(len(parts), 3)
        self.assertTrue(parts[0].startswith("pbkdf2:sha256:260000"))
        salt_hex, hash_hex = parts[1], parts[2]
        self.assertEqual(len(salt_hex), 32)  # 16 bytes in hex
        self.assertEqual(len(hash_hex), 64)  # 32 bytes sha256 in hex

        # Verification succeeds with right password
        self.assertTrue(verify_password(raw_pw, hashed))
        # Verification fails with wrong password
        self.assertFalse(verify_password("WrongPassword123!", hashed))

    def test_session_token_cryptography(self):
        """Verify session token signing, verification, and tamper rejection."""
        user_id = 999
        email = "test@pricewise.ai"
        token = generate_session_token(user_id, email)

        # Verification extracts correct payload
        verified = verify_session_token(token)
        self.assertIsNotNone(verified)
        self.assertEqual(verified["user_id"], user_id)
        self.assertEqual(verified["email"], email)

        # Tampered token is rejected
        tampered_token = token[:-5] + "XXXXX"
        self.assertIsNone(verify_session_token(tampered_token))

    def test_user_registration_and_login_flow(self):
        """Verify complete registration, duplicate handling, login, and cookie issuance."""
        test_email = f"user_{self.unique_suffix}@example.com"
        test_password = "SecurePassword2026!"
        test_name = "Ananya Iyer"

        # 1. Register new user
        reg_res = self.client.post("/api/auth/register", json={
            "name": test_name,
            "email": test_email,
            "password": test_password,
        })
        self.assertEqual(reg_res.status_code, 200)
        reg_data = reg_res.json()
        self.assertIn("token", reg_data)
        self.assertEqual(reg_data["user"]["email"], test_email.lower())
        self.assertEqual(reg_data["user"]["name"], test_name)
        # Ensure password_hash is never leaked in response
        self.assertNotIn("password_hash", reg_data["user"])
        self.assertNotIn("password", reg_data["user"])

        # 2. Reject duplicate email
        dup_res = self.client.post("/api/auth/register", json={
            "name": "Duplicate User",
            "email": test_email.upper(),  # Email case normalization check
            "password": test_password,
        })
        self.assertEqual(dup_res.status_code, 409)

        # 3. Login with correct credentials
        login_res = self.client.post("/api/auth/login", json={
            "email": test_email,
            "password": test_password,
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.json()
        token = login_data["token"]
        self.assertIsNotNone(token)
        # Verify HTTP-only session cookie is set
        self.assertIn("session_token", login_res.cookies)

        # 4. Login with wrong password
        fail_login = self.client.post("/api/auth/login", json={
            "email": test_email,
            "password": "WrongPassword!",
        })
        self.assertEqual(fail_login.status_code, 401)
        self.assertIn("Invalid email or password", fail_login.json()["detail"])

        # 5. Access protected /api/auth/me with Bearer token
        me_bearer = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_bearer.status_code, 200)
        self.assertEqual(me_bearer.json()["user"]["email"], test_email.lower())

        # 6. Access protected /api/auth/me without credentials (clear cookies first)
        self.client.cookies.clear()
        unauth_res = self.client.get("/api/auth/me")
        self.assertEqual(unauth_res.status_code, 401)

        # 7. Access protected /api/auth/me with session cookie
        cookie_res = self.client.get("/api/auth/me", cookies={"session_token": token})
        self.assertEqual(cookie_res.status_code, 200)
        self.assertEqual(cookie_res.json()["user"]["email"], test_email.lower())

        # 8. Logout clears session cookie
        logout_res = self.client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_res.status_code, 200)


class TestPhase7ProfileAndPreferences(unittest.TestCase):
    """Test suite for Beauty Profile endpoints and IDOR isolation."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.suffix = uuid.uuid4().hex[:8]

        # Register User A
        res_a = cls.client.post("/api/auth/register", json={
            "name": f"User A {cls.suffix}",
            "email": f"usera_{cls.suffix}@test.com",
            "password": "Password123!",
        })
        cls.token_a = res_a.json()["token"]

        # Register User B
        res_b = cls.client.post("/api/auth/register", json={
            "name": f"User B {cls.suffix}",
            "email": f"userb_{cls.suffix}@test.com",
            "password": "Password123!",
        })
        cls.token_b = res_b.json()["token"]
        cls.client.cookies.clear()

    def test_profile_crud_and_disclaimer(self):
        """Verify profile creation, retrieval, updating, reset, and medical disclaimer."""
        headers_a = {"Authorization": f"Bearer {self.token_a}"}

        # 1. Initial profile fetch returns defaults + non-medical disclaimer
        get_res = self.client.get("/api/profile", headers=headers_a)
        self.assertEqual(get_res.status_code, 200)
        data = get_res.json()
        self.assertIn("profile", data)
        self.assertIn("disclaimer", data)
        self.assertIn("Cosmetic Guidance Notice", data["disclaimer"])

        # 2. Update User A profile
        put_res = self.client.put("/api/profile", headers=headers_a, json={
            "skin_type": "combination",
            "skin_concerns": ["acne", "pigmentation", "pores"],
            "preferred_brands": ["Minimalist", "The Derma Co"],
            "preferred_categories": ["skincare"],
            "budget_min": 400,
            "budget_max": 1800,
            "makeup_preferences": {
                "finish_preference": "dewy",
                "coverage_preference": "medium",
                "undertone": "warm",
            },
            "ingredient_avoidances": ["fragrance", "essential_oils"],
        })
        self.assertEqual(put_res.status_code, 200)
        profile_a = put_res.json()["profile"]
        self.assertEqual(profile_a["skin_type"], "combination")
        self.assertIn("acne", profile_a["skin_concerns"])
        self.assertEqual(profile_a["budget_max"], 1800)
        self.assertIn("fragrance", profile_a["ingredient_avoidances"])

        # 3. Verify User B has separate isolated profile (IDOR protection)
        headers_b = {"Authorization": f"Bearer {self.token_b}"}
        get_b = self.client.get("/api/profile", headers=headers_b)
        self.assertEqual(get_b.status_code, 200)
        profile_b = get_b.json()["profile"]
        # User B should not have User A's updated skin type or concerns
        self.assertNotEqual(profile_b["skin_type"], "combination")

        # 4. Reset User A profile
        del_res = self.client.delete("/api/profile", headers=headers_a)
        self.assertEqual(del_res.status_code, 200)
        get_reset = self.client.get("/api/profile", headers=headers_a)
        self.assertEqual(get_reset.json()["profile"]["skin_type"], "unsure")


class TestPhase7RoutinesAndConflictDetection(unittest.TestCase):
    """Test suite for personalized routines, step sequencing, and ingredient conflict warnings."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.suffix = uuid.uuid4().hex[:8]

        res = cls.client.post("/api/auth/register", json={
            "name": f"Routine User {cls.suffix}",
            "email": f"routine_{cls.suffix}@test.com",
            "password": "Password123!",
        })
        cls.token = res.json()["token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        cls.client.cookies.clear()

    def test_default_routines_seeding(self):
        """Verify AM and PM starter routines are seeded upon first access."""
        res = self.client.get("/api/routines", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        routines = data["routines"]
        self.assertGreaterEqual(len(routines), 2)

        types = [r["routine_type"] for r in routines]
        self.assertIn("AM", types)
        self.assertIn("PM", types)

        # Check cosmetic disclaimer
        self.assertIn("disclaimer", data)
        self.assertIn("Cosmetic Guidance Notice", data["disclaimer"])

    def test_routine_steps_reordering_and_deletion(self):
        """Verify adding, reordering, and deleting steps in a routine."""
        # Create a new custom routine
        create_res = self.client.post("/api/routines", headers=self.headers, json={
            "name": "Weekend Reset Routine",
            "routine_type": "custom",
            "description": "Weekly deep exfoliation and hydrating barrier treatment",
        })
        self.assertEqual(create_res.status_code, 200)
        routine_id = create_res.json()["routine"]["id"]

        # Add Step 1
        s1 = self.client.post(f"/api/routines/{routine_id}/items", headers=self.headers, json={
            "step_name": "Salicylic Cleanser",
            "category": "Face Wash",
            "usage_instructions": "Lather on wet face for 60 seconds",
        })
        self.assertEqual(s1.status_code, 200)
        item1_id = s1.json()["item"]["id"]

        # Add Step 2
        s2 = self.client.post(f"/api/routines/{routine_id}/items", headers=self.headers, json={
            "step_name": "Hyaluronic Acid Serum",
            "category": "Serum",
            "usage_instructions": "Apply to damp skin",
        })
        self.assertEqual(s2.status_code, 200)
        item2_id = s2.json()["item"]["id"]

        # Reorder steps (reverse order)
        reorder_res = self.client.put(f"/api/routines/{routine_id}/reorder", headers=self.headers, json={
            "item_order": [item2_id, item1_id],
        })
        self.assertEqual(reorder_res.status_code, 200)

        # Verify reversed order
        get_res = self.client.get("/api/routines", headers=self.headers)
        custom_r = next(r for r in get_res.json()["routines"] if r["id"] == routine_id)
        self.assertEqual(custom_r["items"][0]["id"], item2_id)
        self.assertEqual(custom_r["items"][1]["id"], item1_id)

        # Delete step 1
        del_item_res = self.client.delete(f"/api/routines/{routine_id}/items/{item1_id}", headers=self.headers)
        self.assertEqual(del_item_res.status_code, 200)

        # Delete custom routine
        del_routine_res = self.client.delete(f"/api/routines/{routine_id}", headers=self.headers)
        self.assertEqual(del_routine_res.status_code, 200)

    def test_ingredient_conflict_detection_engine(self):
        """Verify the cosmetic ingredient conflict rule engine flags dangerous pairings."""
        # 1. Test Retinol + AHA/BHA conflict in PM routine
        conflicting_pm_items = [
            {"step_name": "Glycolic Acid 7% Toner", "category": "Toner", "custom_product_name": "The Ordinary Glycolic Acid", "key_ingredients": ["glycolic acid"]},
            {"step_name": "Retinol 0.3% Serum", "category": "Serum", "custom_product_name": "Minimalist Retinol 0.3%", "key_ingredients": ["retinol"]},
        ]
        conflicts_pm = detect_ingredient_conflicts("PM", conflicting_pm_items)
        self.assertTrue(any(c["conflict_type"] == "retinoid_with_aha_bha" for c in conflicts_pm))

        # 2. Test Vitamin C + Retinol conflict in AM routine
        conflicting_am_items = [
            {"step_name": "Vitamin C 16% Serum", "category": "Serum", "custom_product_name": "Minimalist 16% Vit C", "key_ingredients": ["vitamin c", "ethyl ascorbic acid"]},
            {"step_name": "Night Retinol Cream", "category": "Moisturiser", "custom_product_name": "Olay Retinol 24", "key_ingredients": ["retinol"]},
            {"step_name": "SPF 50 Sunscreen", "category": "Sunscreen", "custom_product_name": "Dot & Key Sunscreen", "key_ingredients": []},
        ]
        conflicts_am = detect_ingredient_conflicts("AM", conflicting_am_items)
        self.assertTrue(any(c["conflict_type"] == "vitamin_c_with_retinol" for c in conflicts_am))

        # 3. Test missing SPF warning in AM routine
        missing_spf_items = [
            {"step_name": "Gentle Cleanser", "category": "Face Wash", "key_ingredients": []},
            {"step_name": "Moisturiser", "category": "Moisturiser", "key_ingredients": []},
        ]
        conflicts_no_spf = detect_ingredient_conflicts("AM", missing_spf_items)
        self.assertTrue(any(c["conflict_type"] == "missing_sunscreen_am" for c in conflicts_no_spf))


class TestPhase7WatchlistAndPersonalization(unittest.TestCase):
    """Test suite for watchlist cloud sync and personalized catalog recommendations."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.suffix = uuid.uuid4().hex[:8]

        res = cls.client.post("/api/auth/register", json={
            "name": f"Watchlist User {cls.suffix}",
            "email": f"watchlist_{cls.suffix}@test.com",
            "password": "Password123!",
        })
        cls.token = res.json()["token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        cls.client.cookies.clear()
        cls.client.cookies.clear()

    def test_watchlist_cloud_sync_and_crud(self):
        """Verify adding, syncing anonymous items, retrieving, and removing from watchlist."""
        prods = self.client.get("/api/products").json()
        pid1 = prods[0]["id"]
        pid2 = prods[1]["id"]
        pid3 = prods[2]["id"]

        # 1. Add item
        add_res = self.client.post("/api/watchlist", headers=self.headers, json={
            "product_id": pid1,
            "target_price": 450,
            "notes": "Wait for Nykaa Pink Friday sale",
        })
        self.assertEqual(add_res.status_code, 200)

        # 2. Sync anonymous localStorage items (simulating items saved before login)
        sync_res = self.client.post("/api/watchlist/sync", headers=self.headers, json={
            "items": [
                {"product_id": pid2, "target_price": 599},
                {"product_id": pid3, "target_price": 899},
            ]
        })
        self.assertEqual(sync_res.status_code, 200)
        self.assertGreaterEqual(sync_res.json()["synced_count"], 2)

        # 3. Get watchlist
        get_res = self.client.get("/api/watchlist", headers=self.headers)
        self.assertEqual(get_res.status_code, 200)
        items = get_res.json()["items"]
        product_ids = [item["product_id"] for item in items]
        self.assertIn(pid1, product_ids)
        self.assertIn(pid2, product_ids)

        # 4. Remove item
        del_res = self.client.delete(f"/api/watchlist/{pid1}", headers=self.headers)
        self.assertEqual(del_res.status_code, 200)

        # Confirm removal
        get_after = self.client.get("/api/watchlist", headers=self.headers)
        remaining_ids = [item["product_id"] for item in get_after.json()["items"]]
        self.assertNotIn(pid1, remaining_ids)

    def test_personalized_catalog_recommendations(self):
        """Verify catalog-driven personalized recommendations score based on profile."""
        # Set user profile with oily skin, acne concerns, and Minimalist brand
        self.client.put("/api/profile", headers=self.headers, json={
            "skin_type": "oily",
            "skin_concerns": ["acne", "pores"],
            "preferred_brands": ["Minimalist", "The Derma Co"],
            "preferred_categories": ["skincare"],
            "budget_min": 200,
            "budget_max": 2000,
            "ingredient_avoidances": ["fragrance"],
        })

        rec_res = self.client.get("/api/recommendations/personalized?limit=5", headers=self.headers)
        self.assertEqual(rec_res.status_code, 200)
        data = rec_res.json()
        recs = data["recommendations"]

        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)

        top_rec = recs[0]
        self.assertIn("recommendation_score", top_rec)
        self.assertGreater(top_rec["recommendation_score"], 0)
        self.assertIn("matched_reasons", top_rec)
        self.assertGreater(len(top_rec["matched_reasons"]), 0)

        # Non-medical disclaimer is present
        self.assertIn("disclaimer", data)
        self.assertIn("Cosmetic Guidance Notice", data["disclaimer"])


if __name__ == "__main__":
    unittest.main()
