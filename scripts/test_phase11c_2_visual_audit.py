"""Phase 11C.2 Visual Audit Script."""

import os
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.getcwd(), "screenshots", "phase11c_2")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Catalog grid
        print("1. Loading Catalog page...")
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_catalog_verified_specs_100_products.png"), full_page=False)
        print("Captured 01_catalog_verified_specs_100_products.png")

        # 2. PDP for prod-01 (Now verified with official Dot & Key URL)
        print("2. Navigating to prod-01 PDP...")
        page.goto("http://127.0.0.1:5173/product/watermelon-cooling-sunscreen-spf-50", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_pdp_dot_and_key_verified_spec.png"), full_page=False)
        print("Captured 02_pdp_dot_and_key_verified_spec.png")

        # 3. PDP for prod-14 (M.A.C Foundation)
        print("3. Navigating to prod-14 PDP (M.A.C Foundation)...")
        page.goto("http://127.0.0.1:5173/product/mac-studio-fix-fluid-spf-15", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_pdp_mac_foundation_spec.png"), full_page=False)
        print("Captured 03_pdp_mac_foundation_spec.png")

        browser.close()
        print("Phase 11C.2 visual audit completed successfully!")

if __name__ == "__main__":
    run()
