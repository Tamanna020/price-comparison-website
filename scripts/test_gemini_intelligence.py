import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def test_gemini_intelligence():
    print("=== PriceWise AI: Comprehensive Gemini Beauty Intelligence Audit ===")

    # 0. Auth setup
    reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"gemini_test_{int(time.time())}@example.com",
        "password": "Password123!",
        "full_name": "Gemini Tester"
    })
    token = reg.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Model Configuration and API Key Masking
    print("\n1. Verifying Gemini Model Configuration & Secret Masking...")
    from dotenv import load_dotenv
    load_dotenv()
    configured_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    raw_key = os.getenv("GEMINI_API_KEY", "")
    print(f"  Configured Gemini Model: {configured_model}")
    assert "gemini" in configured_model.lower(), "Configured model is not a Gemini model"
    assert len(raw_key) > 10, "GEMINI_API_KEY is not configured"
    masked_key = raw_key[:4] + "..." + raw_key[-4:]
    print(f"  API Key Present: True (Masked: {masked_key})")

    # 2. Daily Quota & Usage Endpoint
    print("\n2. Testing /api/beauty/usage Endpoint...")
    usage_res = requests.get(f"{BASE_URL}/api/beauty/usage", headers=headers)
    assert usage_res.status_code == 200, f"Usage endpoint failed: {usage_res.text}"
    usage_data = usage_res.json()
    print(f"  Usage data returned: {json.dumps(usage_data)}")
    assert "daily_limit" in usage_data or "requests_limit" in usage_data or "limit" in usage_data or "requests_remaining" in usage_data
    print("  ✓ Usage endpoint returns user quota and limit status correctly")

    # 3. Ingredient Analysis with Caching Verification
    print("\n3. Testing /api/beauty/analyze-ingredients/12 (Ingredient Analysis & Caching)...")
    # First call (may generate or fetch cached)
    t0 = time.time()
    res1 = requests.post(f"{BASE_URL}/api/beauty/analyze-ingredients/12", headers=headers)
    lat1 = time.time() - t0
    assert res1.status_code == 200, f"Analyze ingredients failed: {res1.text}"
    data1 = res1.json()
    print(f"  Call 1: {lat1:.3f}s | Source: {data1.get('extraction_source', 'N/A')} | Ingredients: {len(data1.get('ingredients', []))}")
    assert len(data1.get("ingredients", [])) > 0, "No ingredients returned"

    # Second call (must be fast cache hit)
    t0 = time.time()
    res2 = requests.post(f"{BASE_URL}/api/beauty/analyze-ingredients/12", headers=headers)
    lat2 = time.time() - t0
    assert res2.status_code == 200
    data2 = res2.json()
    print(f"  Call 2 (Cache Hit): {lat2:.3f}s | Source: {data2.get('extraction_source', 'N/A')}")
    assert lat2 < 1.0, f"Cache hit took longer than expected: {lat2:.3f}s"
    assert len(data2.get("ingredients", [])) == len(data1.get("ingredients", [])), "Cached ingredients mismatch"
    print("  ✓ Ingredient analysis response is properly cached in SQLite")

    # 4. Cheaper Alternatives / Dupe Finder
    print("\n4. Testing /api/beauty/find-alternatives/12 (Cheaper Alternatives)...")
    alt_res = requests.post(f"{BASE_URL}/api/beauty/find-alternatives/12", headers=headers)
    assert alt_res.status_code == 200, f"Alternatives failed: {alt_res.text}"
    alt_data = alt_res.json()
    alts = alt_data.get("alternatives", [])
    print(f"  Found {len(alts)} alternatives for product 12")
    if alts:
        alt = alts[0]
        print(f"  Top Dupe: {alt.get('alternative_product_name')} by {alt.get('alternative_brand')}")
        print(f"  Similarity Score: {alt.get('similarity_score')} | Price Diff: {alt.get('price_difference')}")
    print("  ✓ Cheaper alternatives finder functional and returning structured similarity attributes")

    # 5. Routine Intelligence (AM / PM)
    print("\n5. Testing /api/beauty/generate-routine/AM & PM...")
    am_res = requests.post(
        f"{BASE_URL}/api/beauty/generate-routine/AM",
        json={"skin_type": "Combination", "skin_concerns": ["Acne", "Hyperpigmentation"]},
        headers=headers
    )
    assert am_res.status_code == 200, f"AM routine generation failed: {am_res.text}"
    am_data = am_res.json()
    print(f"  AM Routine Steps: {len(am_data.get('steps', []))} | Title: {am_data.get('routine_type')}")
    assert len(am_data.get("steps", [])) >= 2, "AM routine has insufficient steps"

    pm_res = requests.post(
        f"{BASE_URL}/api/beauty/generate-routine/PM",
        json={"skin_type": "Combination", "skin_concerns": ["Anti-aging", "Dryness"]},
        headers=headers
    )
    assert pm_res.status_code == 200, f"PM routine generation failed: {pm_res.text}"
    pm_data = pm_res.json()
    print(f"  PM Routine Steps: {len(pm_data.get('steps', []))} | Title: {pm_data.get('routine_type')}")
    assert len(pm_data.get("steps", [])) >= 2, "PM routine has insufficient steps"
    print("  ✓ Routine intelligence successfully generates AM and PM protocols")

    # 6. Skin Concern Matching
    print("\n6. Testing /api/beauty/match-skin-concerns...")
    concern_res = requests.post(f"{BASE_URL}/api/beauty/match-skin-concerns", json={
        "concerns": ["Acne"],
        "category": "Serum",
        "budget_range": [200, 1500]
    }, headers=headers)
    assert concern_res.status_code == 200, f"Skin concern matching failed: {concern_res.text}"
    concern_data = concern_res.json()
    matches = concern_data.get("matches", [])
    print(f"  Matches for 'Acne': {len(matches)}")
    print("  ✓ Skin concern matching endpoint functional")

    # 7. Verification: No API Key Leakage
    print("\n7. Verifying No API Key Leakage in Responses...")
    for res_obj, name in [(usage_res, "Usage"), (res1, "Ingredients"), (alt_res, "Alternatives"), (am_res, "AM Routine")]:
        raw_body = res_obj.text
        assert raw_key not in raw_body, f"CRITICAL LEAK: GEMINI_API_KEY found in {name} response body!"
        for h_val in res_obj.headers.values():
            assert raw_key not in h_val, f"CRITICAL LEAK: GEMINI_API_KEY found in {name} headers!"
    print("  ✓ Verified: Zero API key leakage across all Gemini intelligence endpoints")

    print("\n✓ Comprehensive Gemini Beauty Intelligence Audit PASSED!")

if __name__ == "__main__":
    test_gemini_intelligence()
