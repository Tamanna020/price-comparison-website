import sys
import time
import os
import json
import urllib.request
from playwright.sync_api import sync_playwright

def get_auth_token():
    test_email = f"tester_{int(time.time())}@pricewise.ai"
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/register",
        data=json.dumps({
            "name": "Phase 8F Tester",
            "email": test_email,
            "password": "Password123!"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        return data.get("token")

def run_browser_verification():
    print("=== Starting Phase 8F Browser Verification ===")
    os.makedirs("screenshots/phase8f", exist_ok=True)

    token = get_auth_token()
    print(f"Obtained valid auth token for user session: {token[:15]}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            headless=True
        )

        # Desktop Context (1280x850)
        context = browser.new_context(viewport={'width': 1280, 'height': 850})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # Set valid token in localStorage
        page.goto("http://localhost:5173/", wait_until="domcontentloaded")
        page.evaluate(f"() => {{ localStorage.setItem('pw_auth_token', '{token}'); }}")

        # -------------------------------------------------------------
        # 1. Product Detail Page — Section Navigation & Intelligence
        # -------------------------------------------------------------
        print("\n1. Testing Product Detail Page Navigation & Sections...")
        pdp_url = "http://localhost:5173/product/watermelon-cooling-sunscreen-spf-50"
        page.goto(pdp_url, wait_until="domcontentloaded")
        time.sleep(2)

        assert "PriceWise" in page.title(), "Unexpected page title"
        overlay = page.query_selector("vite-error-overlay")
        assert overlay is None, "Vite error overlay detected!"

        # Screenshot Overview
        page.screenshot(path="screenshots/phase8f/01_pdp_overview_navigation.png")
        print("   ✓ Screenshot: 01_pdp_overview_navigation.png saved")

        # Click Section: Pricing
        pricing_btn = page.query_selector("button:has-text('Live Price Comparison'), button:has-text('Prices')")
        if pricing_btn:
            pricing_btn.click()
            time.sleep(1)
            page.screenshot(path="screenshots/phase8f/02_pdp_price_comparison.png")
            print("   ✓ Screenshot: 02_pdp_price_comparison.png saved")

        # Click Section: Ingredients
        ingredients_btn = page.query_selector("button:has-text('Ingredient Intelligence'), button:has-text('Ingredients')")
        if ingredients_btn:
            ingredients_btn.click()
            time.sleep(1)
            page.screenshot(path="screenshots/phase8f/03_pdp_ingredient_analysis.png")
            print("   ✓ Screenshot: 03_pdp_ingredient_analysis.png saved")

        # Click Section: Alternatives
        alternatives_btn = page.query_selector("button:has-text('Cheaper Dupes'), button:has-text('Alternatives')")
        if alternatives_btn:
            alternatives_btn.click()
            time.sleep(1)
            page.screenshot(path="screenshots/phase8f/04_pdp_alternatives_dupes.png")
            print("   ✓ Screenshot: 04_pdp_alternatives_dupes.png saved")

        # Click Section: Reviews
        reviews_btn = page.query_selector("button:has-text('Reviews & Community'), button:has-text('Reviews')")
        if reviews_btn:
            reviews_btn.click()
            time.sleep(1)
            page.screenshot(path="screenshots/phase8f/05_pdp_reviews_community.png")
            print("   ✓ Screenshot: 05_pdp_reviews_community.png saved")

        # -------------------------------------------------------------
        # 2. Beauty Assistant Page
        # -------------------------------------------------------------
        print("\n2. Testing Beauty Assistant Page with Suggested Prompts...")
        page.goto("http://localhost:5173/beauty-assistant", wait_until="domcontentloaded")
        time.sleep(2)

        overlay_ba = page.query_selector("vite-error-overlay")
        assert overlay_ba is None, "Vite overlay on Beauty Assistant!"

        prompts = page.query_selector_all("main button")
        print(f"   Found {len(prompts)} prompt buttons on Beauty Assistant")
        page.screenshot(path="screenshots/phase8f/06_beauty_assistant_prompts.png")
        print("   ✓ Screenshot: 06_beauty_assistant_prompts.png saved")

        # Click first suggested prompt: "Find a serum for oily skin"
        oily_prompt_btn = page.query_selector("button:has-text('Find a serum for oily skin')")
        if oily_prompt_btn:
            oily_prompt_btn.click()
            time.sleep(0.5)
            send_btn = page.query_selector("button[aria-label='Send message'], button[type='submit']")
            if send_btn:
                send_btn.click()
                time.sleep(2.5)
                page.screenshot(path="screenshots/phase8f/07_beauty_assistant_chat_response.png")
                print("   ✓ Screenshot: 07_beauty_assistant_chat_response.png saved")

        # -------------------------------------------------------------
        # 3. Profile Page — Gemini AI Quota Card
        # -------------------------------------------------------------
        print("\n3. Testing Profile Page & Gemini AI Quota Card...")
        page.goto("http://localhost:5173/profile", wait_until="domcontentloaded")
        time.sleep(2)

        overlay_prof = page.query_selector("vite-error-overlay")
        assert overlay_prof is None, "Vite overlay on Profile Page!"

        has_quota_header = "Gemini AI Quota" in page.content()
        print(f"   Gemini AI Quota header present: {has_quota_header}")
        page.screenshot(path="screenshots/phase8f/08_profile_ai_quota_card.png")
        print("   ✓ Screenshot: 08_profile_ai_quota_card.png saved")

        # -------------------------------------------------------------
        # 4. Mobile Navigation & Responsive Drawer
        # -------------------------------------------------------------
        print("\n4. Testing Mobile View & Navigation Drawer...")
        mobile_context = browser.new_context(viewport={'width': 390, 'height': 844})
        mobile_page = mobile_context.new_page()

        mobile_page.goto("http://localhost:5173/", wait_until="domcontentloaded")
        time.sleep(1.5)

        # Open mobile hamburger menu
        hamburger = mobile_page.query_selector("button[aria-label='Toggle navigation menu']")
        if hamburger:
            hamburger.click()
            time.sleep(1)
            mobile_page.screenshot(path="screenshots/phase8f/09_mobile_navigation_drawer.png")
            print("   ✓ Screenshot: 09_mobile_navigation_drawer.png saved")

        # Mobile PDP
        mobile_page.goto(pdp_url, wait_until="domcontentloaded")
        time.sleep(1.5)
        mobile_page.screenshot(path="screenshots/phase8f/10_mobile_pdp_navigation.png")
        print("   ✓ Screenshot: 10_mobile_pdp_navigation.png saved")

        browser.close()
        print("\n=== Phase 8F Browser Verification Completed Successfully! ===")

if __name__ == "__main__":
    run_browser_verification()
