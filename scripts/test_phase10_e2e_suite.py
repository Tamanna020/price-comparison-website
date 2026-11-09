"""Phase 10 E2E Browser Testing Suite using Playwright.

Validates:
1. Ingredient Compatibility & Clash Matrix (/ingredients)
2. AM/PM Routine Safety, Overload & Sunscreen Compliance (/ingredients -> Routine Checker)
3. Master Ingredient Encyclopedia with Clinical Evidence Levels (/ingredients -> Encyclopedia)
4. Indian Climate-Aware Skincare Advisor (/climate-advisor)
5. Foundation Shade, Undertone, and Oxidation Matcher (/shade-matcher)
6. Enhanced Beauty Product Discovery & Intelligence Suite (/)
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"
SCREENSHOT_DIR = os.path.abspath("screenshots/phase10")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def run_phase10_e2e_tests():
    print("=" * 70)
    print("PRICEWISE AI — PHASE 10 E2E AUTOMATED BROWSER TEST SUITE")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # -------------------------------------------------------------
        # Journey 1: Ingredient Compatibility & Clash Matrix
        # -------------------------------------------------------------
        print("\n[Journey 1] Testing Ingredient Compatibility & Clash Matrix...")
        page.goto(f"{BASE_URL}/ingredients", wait_until="networkidle")
        page.wait_for_selector("h1:has-text('Ingredient Compatibility')")
        print("  ✓ Ingredient Compatibility page rendered successfully.")

        # Check default selection contains Retinol and Glycolic Acid
        page.wait_for_selector("text=Active Ingredient Clash Detected")
        page.wait_for_selector("text=Retinoid & AHA Barrier Disruption Risk")
        page.wait_for_selector("text=Scientific Rationale:")
        print("  ✓ Retinol + Glycolic Acid clash warning and scientific rationale verified.")

        time.sleep(1)
        p1 = os.path.join(SCREENSHOT_DIR, "01_ingredient_compatibility_matrix.png")
        page.screenshot(path=p1, full_page=False)
        print(f"  ✓ Screenshot saved: {p1}")

        # -------------------------------------------------------------
        # Journey 2: AM/PM Routine Safety Checker
        # -------------------------------------------------------------
        print("\n[Journey 2] Testing AM/PM Routine Safety & Overload Checker...")
        page.click("button:has-text('Routine Checker')")
        page.wait_for_selector("h3:has-text('Morning (AM) Routine')")
        page.wait_for_selector("h3:has-text('Evening (PM) Routine')")
        print("  ✓ Morning and Evening routine columns loaded.")

        # Click Re-Analyze Routine Safety
        page.click("button:has-text('Re-Analyze Routine Safety')")
        page.wait_for_selector("text=Routine Irritation Assessment")
        page.wait_for_selector("text=Recommended Separation Regimen")
        print("  ✓ Routine safety assessment and separation regimen verified.")

        time.sleep(1)
        p2 = os.path.join(SCREENSHOT_DIR, "02_routine_checker_safety.png")
        page.screenshot(path=p2, full_page=False)
        print(f"  ✓ Screenshot saved: {p2}")

        # -------------------------------------------------------------
        # Journey 3: Master Ingredient Encyclopedia
        # -------------------------------------------------------------
        print("\n[Journey 3] Testing Master Ingredient Encyclopedia...")
        page.click("button:has-text('Encyclopedia')")
        page.wait_for_selector("input[placeholder*='Search cosmetic actives']")
        page.fill("input[placeholder*='Search cosmetic actives']", "Salicylic")
        page.wait_for_selector("h3:has-text('Salicylic Acid')")
        page.wait_for_selector("text=ESTABLISHED EVIDENCE")
        print("  ✓ Encyclopedia search and clinical evidence badge verified.")

        time.sleep(1)
        p3 = os.path.join(SCREENSHOT_DIR, "03_ingredient_encyclopedia.png")
        page.screenshot(path=p3, full_page=False)
        print(f"  ✓ Screenshot saved: {p3}")

        # -------------------------------------------------------------
        # Journey 4: Indian Climate-Aware Skincare Advisor
        # -------------------------------------------------------------
        print("\n[Journey 4] Testing Indian Climate-Aware Skincare Advisor...")
        page.goto(f"{BASE_URL}/climate-advisor", wait_until="networkidle")
        page.wait_for_selector("h1:has-text('Climate-Aware Skincare Advisor')")
        page.wait_for_selector("h2:has-text('Hot & Humid')")
        page.wait_for_selector("text=Real-World Skin Impact")
        page.wait_for_selector("text=Sunscreen Vehicle")
        page.wait_for_selector("text=Catalog Product Matches")
        print("  ✓ Climate profile details and catalog product matches verified.")

        # Test switching climate condition to Winter Dryness
        page.click("button:has-text('Winter Dryness')")
        page.wait_for_selector("h2:has-text('Winter Dryness')")
        print("  ✓ Switched to Winter Dryness condition successfully.")

        time.sleep(1)
        p4 = os.path.join(SCREENSHOT_DIR, "04_climate_skincare_advisor.png")
        page.screenshot(path=p4, full_page=False)
        print(f"  ✓ Screenshot saved: {p4}")

        # -------------------------------------------------------------
        # Journey 5: Foundation Shade & Undertone Matcher
        # -------------------------------------------------------------
        print("\n[Journey 5] Testing Foundation Shade & Undertone Matcher...")
        page.goto(f"{BASE_URL}/shade-matcher", wait_until="networkidle")
        page.wait_for_selector("h1:has-text('Foundation Shade & Undertone Matcher')")

        # Select Medium depth and Olive undertone via specific heading locators
        page.click("button:has(h3:has-text('Medium'))")
        page.click("button:has(h3:has-text('Olive'))")
        page.wait_for_selector("text=Undertone Analysis & Colorimetry Notes")
        page.wait_for_selector("text=Recommended Catalog Foundations")
        page.wait_for_selector("text=Sebum Oxidation Advisory:")
        page.wait_for_selector("text=M.A.C Equivalent")
        print("  ✓ Foundation matching, oxidation advisory, and cross-brand equivalents verified.")

        time.sleep(1)
        p5 = os.path.join(SCREENSHOT_DIR, "05_foundation_shade_matcher.png")
        page.screenshot(path=p5, full_page=False)
        print(f"  ✓ Screenshot saved: {p5}")

        # -------------------------------------------------------------
        # Journey 6: Enhanced Beauty Product Discovery on Homepage
        # -------------------------------------------------------------
        print("\n[Journey 6] Testing Enhanced Discovery Suite on Homepage...")
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        page.wait_for_selector("#catalog")
        page.evaluate("document.getElementById('catalog').scrollIntoView()")

        # Verify the 3 Phase 10 Intelligence cards
        page.wait_for_selector("text=Ingredient Safety & Clashes")
        page.wait_for_selector("text=Indian Climate Skincare")
        page.wait_for_selector("text=Foundation Shade Matcher")
        print("  ✓ Phase 10 Intelligence cards verified on discovery homepage.")

        # Test filtering by active ingredient
        page.select_option("select:has(option[value='niacinamide'])", "niacinamide")
        time.sleep(1)
        print("  ✓ Active ingredient filter applied (Niacinamide).")

        p6 = os.path.join(SCREENSHOT_DIR, "06_enhanced_discovery_catalog.png")
        page.screenshot(path=p6, full_page=False)
        print(f"  ✓ Screenshot saved: {p6}")

        browser.close()

    print("\n" + "=" * 70)
    print("ALL 6 PHASE 10 E2E BROWSER JOURNEYS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase10_e2e_tests()
