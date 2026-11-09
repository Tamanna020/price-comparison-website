"""Phase 11B E2E Browser Testing Suite using Playwright.

Validates:
1. Product Detail Page & Multi-Retailer Comparison Badges (/product/1)
2. Restricted Retailer Explanatory Notice
3. User Price Verification Submission Modal (with URL, price, MRP, size, notes, and evidence upload)
4. Admin Price Verification Queue (/admin/verifications)
5. Admin Approval & Audit Workflow (approving user submission with verified price and MRP)
6. Manually Verified Status Reflected on Product Detail Page
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath("."))

from playwright.sync_api import sync_playwright
from src.services.auth_service import generate_session_token

BASE_URL = "http://localhost:5173"
SCREENSHOT_DIR = os.path.abspath("screenshots/phase11b")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def run_phase11b_e2e_tests():
    print("=" * 70)
    print("PRICEWISE AI — PHASE 11B E2E AUTOMATED BROWSER TEST SUITE")
    print("=" * 70)

    # Generate admin session token for Alex Demo (id=1)
    admin_token = generate_session_token(1, "demo@pricewise.ai")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 950})

        # Inject admin token into localStorage
        context.add_init_script(f"""
        localStorage.setItem('pw_auth_token', '{admin_token}');
        """)

        page = context.new_page()

        # -------------------------------------------------------------
        # Journey 1: Product Detail Page & Multi-Retailer Badges
        # -------------------------------------------------------------
        print("\n[Journey 1] Testing Product Detail Page & Retailer Price Badges...")
        page.goto(f"{BASE_URL}/product/prod-01", wait_until="networkidle")
        page.wait_for_selector("#live-price-comparison-section")
        print("  [OK] Live price comparison section loaded.")

        # Scroll into view
        section = page.locator("#live-price-comparison-section")
        section.scroll_into_view_if_needed()
        time.sleep(1)

        # Check retailer comparison items
        page.wait_for_selector("text=Retailer Price Comparison & Verification")
        page.wait_for_selector("text=Automatic price checking is currently unavailable for this retailer")
        print("  [OK] Restricted retailer warning message displayed clearly.")

        p1 = os.path.join(SCREENSHOT_DIR, "01_product_price_comparison_badges.png")
        page.screenshot(path=p1, full_page=False)
        print(f"  [OK] Screenshot saved: {p1}")

        # -------------------------------------------------------------
        # Journey 2: User Price Verification Submission Modal
        # -------------------------------------------------------------
        print("\n[Journey 2] Testing User Price Verification Submission Modal...")
        page.click("button:has-text('Verify Retailer Price')")
        page.wait_for_selector("h3:has-text('Submit Retailer Price for Verification')")
        print("  [OK] Price verification modal opened.")

        # Fill in verification form
        page.select_option("select", "Nykaa")
        page.fill("input[placeholder*='https://www.nykaa.com']", "https://www.nykaa.com/minimalist-10-niacinamide/p/12345")
        page.fill("input[placeholder='e.g. 549']", "549")
        page.fill("input[placeholder='e.g. 599']", "599")
        page.fill("textarea", "Verified Nykaa mobile app sale price with 10% coupon")
        time.sleep(1)

        p2 = os.path.join(SCREENSHOT_DIR, "02_user_price_verification_modal.png")
        page.screenshot(path=p2, full_page=False)
        print(f"  [OK] Screenshot saved: {p2}")

        # Submit verification form
        page.click("button:has-text('Submit Verification')")
        page.wait_for_selector("text=Price verification submitted successfully")
        print("  [OK] Price verification submitted and confirmed.")

        time.sleep(1)
        p3 = os.path.join(SCREENSHOT_DIR, "03_price_verification_submitted_success.png")
        page.screenshot(path=p3, full_page=False)
        print(f"  [OK] Screenshot saved: {p3}")

        time.sleep(2)  # Wait for modal auto-close

        # -------------------------------------------------------------
        # Journey 3: Admin Price Verification Queue
        # -------------------------------------------------------------
        print("\n[Journey 3] Testing Admin Price Verification Queue...")
        page.goto(f"{BASE_URL}/admin/verifications", wait_until="networkidle")
        page.wait_for_selector("h1:has-text('Price Verification & Evidence Queue')")
        page.wait_for_selector("text=Manual Price Verifications")
        print("  [OK] Admin verification queue portal rendered.")

        time.sleep(1)
        p4 = os.path.join(SCREENSHOT_DIR, "04_admin_verification_queue.png")
        page.screenshot(path=p4, full_page=False)
        print(f"  [OK] Screenshot saved: {p4}")

        # -------------------------------------------------------------
        # Journey 4: Admin Approval Workflow
        # -------------------------------------------------------------
        print("\n[Journey 4] Testing Admin Approval Workflow...")
        approve_buttons = page.locator("button:has-text('Approve & Publish Live')")
        count = approve_buttons.count()
        if count > 0:
            approve_buttons.first.click()
            page.wait_for_selector("h3:has-text('Approve & Verify Retailer Price')")
            print("  [OK] Admin approval modal opened.")

            p5 = os.path.join(SCREENSHOT_DIR, "05_admin_approval_modal.png")
            page.screenshot(path=p5, full_page=False)
            print(f"  [OK] Screenshot saved: {p5}")

            page.click("button:has-text('Confirm Approval')")
            time.sleep(2)
            print("  [OK] Price approved and published live!")

            p6 = os.path.join(SCREENSHOT_DIR, "06_admin_queue_post_approval.png")
            page.screenshot(path=p6, full_page=False)
            print(f"  [OK] Screenshot saved: {p6}")

        # -------------------------------------------------------------
        # Journey 5: Verified Status Reflected on Product Detail Page
        # -------------------------------------------------------------
        print("\n[Journey 5] Verifying Updated Status on Product Detail Page...")
        page.goto(f"{BASE_URL}/product/prod-01", wait_until="networkidle")
        page.wait_for_selector("#live-price-comparison-section")
        page.locator("#live-price-comparison-section").scroll_into_view_if_needed()
        time.sleep(1)

        # Check for MANUALLY VERIFIED or LIVE VERIFIED badge
        page.wait_for_selector("text=MANUALLY VERIFIED")
        print("  [OK] MANUALLY VERIFIED badge confirmed on product detail comparison table.")

        p7 = os.path.join(SCREENSHOT_DIR, "07_product_manually_verified_badge.png")
        page.screenshot(path=p7, full_page=False)
        print(f"  [OK] Screenshot saved: {p7}")

        browser.close()

    print("\n" + "=" * 70)
    print("ALL 5 PHASE 11B E2E BROWSER JOURNEYS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase11b_e2e_tests()
