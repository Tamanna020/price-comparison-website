"""Phase 12.2 End-to-End User Journey Audit with Playwright (Desktop & Mobile)."""

import os
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.getcwd(), "screenshots", "phase12_2")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def run():
    print("=" * 70)
    print("STARTING PLAYWRIGHT END-TO-END USER JOURNEY AUDIT (PHASE 12.2)")
    print("=" * 70)

    with sync_playwright() as p:
        # 1. Desktop Browser (1440 x 900)
        browser = p.chromium.launch(headless=True)
        desktop = browser.new_context(viewport={"width": 1440, "height": 900})
        page = desktop.new_page()

        print("\n--- DESKTOP JOURNEY (1440x900) ---")

        # 1.1 Homepage & Navigation
        print("1. Loading Homepage...")
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_desktop_homepage.png"))
        print("   Captured 01_desktop_homepage.png")

        # 1.2 Beauty Product Discovery
        print("2. Testing Product Discovery & Category Filters...")
        # Click on Sunscreen category tab if present, or scroll to catalog
        page.evaluate("window.scrollTo(0, 500)")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_desktop_catalog_discovery.png"))
        print("   Captured 02_desktop_catalog_discovery.png")

        # 1.3 Product Details Page & Price Comparison
        print("3. Navigating to PDP (Watermelon Sunscreen)...")
        page.goto("http://127.0.0.1:5173/product/watermelon-cooling-sunscreen-spf-50", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_desktop_pdp_price_comparison.png"))
        print("   Captured 03_desktop_pdp_price_comparison.png")

        # 1.4 Ingredient Analysis & Alternatives
        print("4. Scrolling to Ingredient Analysis & Alternatives...")
        page.evaluate("window.scrollTo(0, 1100)")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_desktop_pdp_ingredients_and_dupes.png"))
        print("   Captured 04_desktop_pdp_ingredients_and_dupes.png")

        # 1.5 Beauty Assistant
        print("5. Navigating to Beauty Assistant Page...")
        page.goto("http://127.0.0.1:5173/beauty-assistant", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_desktop_beauty_assistant.png"))
        print("   Captured 05_desktop_beauty_assistant.png")

        # 1.6 Ingredient Intelligence
        print("6. Navigating to Ingredient Intelligence Page...")
        page.goto("http://127.0.0.1:5173/ingredients", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_desktop_ingredient_intelligence.png"))
        print("   Captured 06_desktop_ingredient_intelligence.png")

        # 1.7 AM/PM Routine Builder
        print("7. Navigating to Routines Page...")
        page.goto("http://127.0.0.1:5173/routines", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_desktop_routines_builder.png"))
        print("   Captured 07_desktop_routines_builder.png")

        # 1.8 Watchlist & Price Alerts
        print("8. Navigating to Watchlist Page...")
        page.goto("http://127.0.0.1:5173/watchlist", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_desktop_watchlist_alerts.png"))
        print("   Captured 08_desktop_watchlist_alerts.png")

        # 1.9 Admin Verification Queue
        print("9. Navigating to Admin Verification Queue...")
        page.goto("http://127.0.0.1:5173/admin/verifications", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "09_desktop_admin_verification.png"))
        print("   Captured 09_desktop_admin_verification.png")

        desktop.close()

        # 2. Mobile Browser (390 x 844 - iPhone 14/15 size)
        print("\n--- MOBILE RESPONSIVE JOURNEY (390x844) ---")
        mobile = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
        m_page = mobile.new_page()

        # 2.1 Mobile Homepage
        print("10. Loading Mobile Homepage...")
        m_page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        m_page.wait_for_timeout(1500)
        m_page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "10_mobile_homepage.png"))
        print("   Captured 10_mobile_homepage.png")

        # 2.2 Mobile PDP
        print("11. Loading Mobile PDP (Watermelon Sunscreen)...")
        m_page.goto("http://127.0.0.1:5173/product/watermelon-cooling-sunscreen-spf-50", wait_until="networkidle")
        m_page.wait_for_timeout(1500)
        m_page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "11_mobile_pdp.png"))
        print("   Captured 11_mobile_pdp.png")

        mobile.close()
        browser.close()

        print("\nALL 11 PLAYWRIGHT VISUAL AUDIT JOURNEYS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run()
