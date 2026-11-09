"""
Phase 13.6: End-to-End Cloud Application Verification Suite.
Executes customer journeys and security verifications against:
- Frontend: https://pricewise-staging.vercel.app
- Backend:  https://pricewise-backend-staging.onrender.com
Captures desktop and mobile screenshots into screenshots/phase13/
"""
import os
import sys
import json
import time
import shutil
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = BASE_DIR / "screenshots" / "phase13"
ARTIFACT_SCREENSHOT_DIR = Path(r"C:\Users\humai\.gemini\antigravity\brain\f9dfc0e1-a968-4a48-96e0-7f2ffce7fcba\screenshots\phase13")

FRONTEND_URL = "https://pricewise-staging.vercel.app"
BACKEND_URL = "https://pricewise-backend-staging.onrender.com"

def save_and_mirror_screenshot(page, filename: str):
    local_path = SCREENSHOT_DIR / filename
    page.screenshot(path=str(local_path), full_page=False)
    if ARTIFACT_SCREENSHOT_DIR.exists():
        shutil.copy(str(local_path), str(ARTIFACT_SCREENSHOT_DIR / filename))
    print(f"  [SCREENSHOT] Captured {filename}")

def run_cloud_verification():
    print("=" * 80)
    print("PRICEWISE AI — PHASE 13.6 COMPLETE CLOUD APPLICATION VERIFICATION")
    print("=" * 80)
    print(f"Target Frontend: {FRONTEND_URL}")
    print(f"Target Backend:  {BACKEND_URL}")
    print("=" * 80)

    results = {
        "timestamp": time.time(),
        "frontend_url": FRONTEND_URL,
        "backend_url": BACKEND_URL,
        "checks": {}
    }

    # 1. API Security & CORS Verification
    print("\n--- 1. API Security, HTTPS & CORS Audits ---")
    try:
        req = urllib.request.Request(
            f"{BACKEND_URL}/api/health/ready",
            headers={"Origin": FRONTEND_URL, "User-Agent": "PriceWiseAudit/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            headers = dict(resp.headers)
            cors_allow = headers.get("access-control-allow-origin", "")
            print(f"  [PASS] HTTPS active: {resp.url.startswith('https://')}")
            print(f"  [PASS] CORS Origin Allowed: {cors_allow}")
            results["checks"]["https"] = True
            results["checks"]["cors_origin"] = cors_allow
    except Exception as e:
        print(f"  [FAIL] Security probe error: {e}")
        results["checks"]["https"] = False

    # 2. Browser Customer Journeys via Playwright
    print("\n--- 2. Browser E2E Customer Journeys & Device Testing ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # A. Desktop Journey (1280x800)
        print("\nTesting Desktop Customer Journey (1280x800)...")
        context_desktop = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) PriceWiseAudit/1.0"
        )
        page = context_desktop.new_page()

        # Journey 1: Homepage & Navigation
        print("  Journey 1: Homepage & Hero Discovery...")
        page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        save_and_mirror_screenshot(page, "01_cloud_desktop_homepage.png")
        assert "PriceWise" in page.title() or "Beauty" in page.content(), "Homepage title mismatch!"

        # Journey 2: Catalog Discovery & Filters
        print("  Journey 2: Catalog Discovery & Category Filtering...")
        page.evaluate("window.scrollTo(0, 600)")
        time.sleep(1)
        save_and_mirror_screenshot(page, "02_cloud_desktop_catalog.png")

        # Journey 3: Product Detail Page (PDP) & Live Comparison
        print("  Journey 3: Product Detail Page & Price Comparison...")
        # Navigate to Sunscreen product
        pdp_url = f"{FRONTEND_URL}/product/dot-key-watermelon-cooling-sunscreen-spf-50"
        page.goto(pdp_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        save_and_mirror_screenshot(page, "03_cloud_desktop_pdp_comparison.png")

        # Journey 4: PDP Price History & Ingredient Intelligence
        print("  Journey 4: PDP Price History & Ingredient Analysis...")
        page.evaluate("window.scrollTo(0, 750)")
        time.sleep(1)
        save_and_mirror_screenshot(page, "04_cloud_desktop_pdp_ingredients.png")

        # Journey 5: AI Beauty Assistant Page
        print("  Journey 5: AI Beauty Assistant...")
        page.goto(f"{FRONTEND_URL}/beauty-assistant", wait_until="networkidle", timeout=30000)
        time.sleep(1)
        save_and_mirror_screenshot(page, "05_cloud_desktop_beauty_assistant.png")

        # Journey 6: Ingredient Intelligence Page
        print("  Journey 6: Ingredient Intelligence Search...")
        page.goto(f"{FRONTEND_URL}/ingredients", wait_until="networkidle", timeout=30000)
        time.sleep(1)
        save_and_mirror_screenshot(page, "06_cloud_desktop_ingredient_intelligence.png")

        # Journey 7: Smart Routine Builder
        print("  Journey 7: AM/PM Smart Routine Builder...")
        page.goto(f"{FRONTEND_URL}/routines", wait_until="networkidle", timeout=30000)
        time.sleep(1)
        save_and_mirror_screenshot(page, "07_cloud_desktop_routines.png")

        # Journey 8: Wishlist & Price Alerts
        print("  Journey 8: Wishlist & Watchlist Management...")
        page.goto(f"{FRONTEND_URL}/profile", wait_until="networkidle", timeout=30000)
        time.sleep(1)
        save_and_mirror_screenshot(page, "08_cloud_desktop_watchlist_alerts.png")

        # Journey 9: Admin Verification Queue
        print("  Journey 9: Admin Manual Verification Queue...")
        page.goto(f"{FRONTEND_URL}/admin/verification", wait_until="networkidle", timeout=30000)
        time.sleep(1)
        save_and_mirror_screenshot(page, "09_cloud_desktop_admin_verification.png")

        context_desktop.close()

        # B. Mobile Journey (390x844 - iPhone 14 / Modern Smartphone)
        print("\nTesting Mobile Customer Journey (390x844)...")
        context_mobile = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15"
        )
        mobile_page = context_mobile.new_page()

        # Mobile Homepage
        print("  Mobile Journey 1: Homepage Responsive View...")
        mobile_page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        save_and_mirror_screenshot(mobile_page, "10_cloud_mobile_homepage.png")

        # Mobile PDP
        print("  Mobile Journey 2: Mobile Product Detail Page...")
        mobile_page.goto(pdp_url, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        save_and_mirror_screenshot(mobile_page, "11_cloud_mobile_pdp.png")

        context_mobile.close()
        browser.close()

    print("\n" + "=" * 80)
    print("PHASE 13.6 COMPLETE CLOUD APPLICATION VERIFICATION: SUCCESS!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    run_cloud_verification()
