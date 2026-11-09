import requests
import sqlite3
import re
import os
import glob
import time

BASE_URL = "http://127.0.0.1:8000"

def test_security_audit():
    print("=== PriceWise AI: Comprehensive Security & Isolation Audit ===")

    # 1. Unauthenticated access enforcement (401 Unauthorized)
    print("\n1. Testing Protected Endpoints (Expect 401 Without Auth)...")
    protected_endpoints = [
        ("GET", "/api/auth/me"),
        ("GET", "/api/profile"),
        ("PUT", "/api/profile"),
        ("GET", "/api/watchlist"),
        ("POST", "/api/watchlist"),
        ("GET", "/api/routines"),
        ("POST", "/api/routines"),
        ("POST", "/api/verification/manual"),
    ]
    for method, path in protected_endpoints:
        url = f"{BASE_URL}{path}"
        if method == "GET":
            res = requests.get(url)
        elif method == "POST":
            res = requests.post(url, json={})
        elif method == "PUT":
            res = requests.put(url, json={})
        
        assert res.status_code == 401, f"Expected 401 for {method} {path}, got {res.status_code}"
        print(f"  ✓ {method} {path} returned 401 Unauthorized as expected")

    # 2. User Data Isolation Test
    print("\n2. Testing User Data Isolation (User A vs User B)...")
    ts = int(time.time())
    email_a = f"sec_user_a_{ts}@example.com"
    email_b = f"sec_user_b_{ts}@example.com"
    pwd = "SecurePassword123!"

    # Register User A
    res_a = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email_a,
        "password": pwd,
        "full_name": "Security User A"
    })
    assert res_a.status_code in (200, 201), f"Register A failed: {res_a.text}"
    token_a = res_a.json().get("token") or res_a.json().get("access_token")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    res_b = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email_b,
        "password": pwd,
        "full_name": "Security User B"
    })
    assert res_b.status_code in (200, 201), f"Register B failed: {res_b.text}"
    token_b = res_b.json().get("token") or res_b.json().get("access_token")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A adds product 1 to watchlist
    res = requests.post(f"{BASE_URL}/api/watchlist", json={"product_id": 1}, headers=headers_a)
    assert res.status_code in (200, 201), f"Add watchlist A failed: {res.text}"

    # User B checks watchlist -> must NOT see product 1
    res = requests.get(f"{BASE_URL}/api/watchlist", headers=headers_b)
    assert res.status_code == 200
    b_watchlist = res.json().get("items", [])
    b_product_ids = [item.get("product_id") or item.get("id") for item in b_watchlist]
    assert 1 not in b_product_ids, "Security breach: User B saw User A's watchlist item!"
    print("  ✓ Watchlist Isolation Verified: User B cannot view User A's watchlist")

    # User A creates a custom routine
    res = requests.post(f"{BASE_URL}/api/routines", json={
        "title": "User A Secret Routine",
        "routine_type": "AM",
        "items": [{"step_number": 1, "product_id": 1, "step_name": "Sunscreen"}]
    }, headers=headers_a)
    assert res.status_code in (200, 201), f"Create routine A failed: {res.text}"
    routine_a_id = res.json().get("id") or res.json().get("routine", {}).get("id")

    # User B checks routines -> must NOT contain User A's routine ID
    res = requests.get(f"{BASE_URL}/api/routines", headers=headers_b)
    assert res.status_code == 200
    b_routines = res.json().get("routines", [])
    b_routine_ids = [r["id"] for r in b_routines]
    assert routine_a_id not in b_routine_ids, "Security breach: User B saw User A's routine!"
    print("  ✓ Routine Isolation Verified: User B cannot view User A's routines")

    # User B attempts to DELETE User A's routine -> Must fail (403 or 404)
    res = requests.delete(f"{BASE_URL}/api/routines/{routine_a_id}", headers=headers_b)
    assert res.status_code in (403, 404), f"Security breach: User B modified User A's routine! Code: {res.status_code}"
    print(f"  ✓ Cross-User Mutation Prevention: User B cannot delete User A's routine (status {res.status_code})")

    # 3. Password Hashing Verification
    print("\n3. Testing Password Storage Integrity in Database...")
    conn = sqlite3.connect("data/pricewise.db")
    cur = conn.cursor()
    cur.execute("SELECT id, email, password_hash FROM users;")
    users = cur.fetchall()
    conn.close()

    plaintext_count = 0
    for u_id, email, ph in users:
        if not ph or not (ph.startswith("pbkdf2:") or ph.startswith("$2b$") or ph.startswith("argon2")):
            plaintext_count += 1
            print(f"  ⚠ Potentially unhashed password for user {email}")
    assert plaintext_count == 0, f"Found {plaintext_count} users with plaintext or invalid password hashes!"
    print(f"  ✓ All {len(users)} users in database have secure cryptographic password hashes (PBKDF2/bcrypt)")

    # 4. SSRF & URL Domain Allowlist Verification
    print("\n4. Testing SSRF Protection on Manual Verification Endpoint...")
    malicious_urls = [
        ("http://127.0.0.1:8000/api/health", "amazon", "Loopback address"),
        ("http://169.254.169.254/latest/meta-data/", "amazon", "AWS Cloud Metadata address"),
        ("http://localhost:5173", "amazon", "Localhost"),
        ("https://evil-attacker.com/malicious", "amazon", "External unverified domain"),
        ("https://www.google.com", "google", "Unsupported retailer")
    ]
    for url, ret, desc in malicious_urls:
        res = requests.post(
            f"{BASE_URL}/api/verification/manual",
            json={
                "product_id": 1,
                "retailer": ret,
                "product_url": url,
                "claimed_price": 499.0
            },
            headers=headers_a
        )
        assert res.status_code == 400, f"SSRF test failed for {desc}: status {res.status_code}, response: {res.text}"
        print(f"  ✓ Rejected SSRF/Illegal URL '{desc}' ({url}) with HTTP 400")

    # Test valid retailer URL passes validation
    valid_res = requests.post(
        f"{BASE_URL}/api/verification/manual",
        json={
            "product_id": 1,
            "retailer": "Nykaa",
            "product_url": "https://www.nykaa.com/dot-key-watermelon-sunscreen/p/12345",
            "claimed_price": 499.0
        },
        headers=headers_a
    )
    assert valid_res.status_code in (200, 201), f"Valid URL submission failed: {valid_res.text}"
    print("  ✓ Legitimate retailer URL on allowlist accepted with HTTP 200/201")

    # 5. Secret Exposure Scan in Frontend Files
    print("\n5. Testing Frontend Bundle for Leaked Secrets...")
    suspicious_patterns = [
        re.compile(r"AIza[0-9A-Za-z-_]{35}"), # Google API key regex
        re.compile(r"Bearer\s+ey[A-Za-z0-9_-]{20,}"), # Static hardcoded JWT token
    ]
    scanned_files = 0
    found_leaks = []
    for root, _, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".html")):
                filepath = os.path.join(root, file)
                scanned_files += 1
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pat in suspicious_patterns:
                        if pat.search(content):
                            found_leaks.append((filepath, pat.pattern))

    print(f"  Scanned {scanned_files} frontend source files.")
    assert len(found_leaks) == 0, f"Secrets found in frontend source: {found_leaks}"
    print("  ✓ Zero hardcoded API keys or bearer tokens found in frontend source code")

    print("\n✓ Comprehensive Security & Isolation Audit PASSED!")

if __name__ == "__main__":
    test_security_audit()
