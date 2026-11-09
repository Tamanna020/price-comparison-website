"""Phase 11C.1 Visual Audit Script.
Captures screenshots of truthful badge corrections:
1. Catalog grid showing Verified Spec vs Partially Verified Specs badges
2. PDP of partially verified product showing amber banner
3. PDP of catalog verified product showing emerald banner
"""

import os
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.getcwd(), "screenshots", "phase11c_1")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Catalog grid
        print("1. Loading Discovery / Catalog page...")
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_catalog_truthful_badges_grid.png"), full_page=False)
        print("Captured 01_catalog_truthful_badges_grid.png")

        # 2. PDP for prod-01 (Partially verified)
        print("2. Navigating to prod-01 PDP (Partially verified)...")
        page.goto("http://127.0.0.1:5173/product/watermelon-cooling-sunscreen-spf-50", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_pdp_partially_verified_banner.png"), full_page=False)
        print("Captured 02_pdp_partially_verified_banner.png")

        # 3. PDP for prod-34 (Catalog verified)
        print("3. Navigating to prod-34 PDP (Catalog verified)...")
        page.goto("http://127.0.0.1:5173/product/aqualogica-aqualogica-radiance-dewy-sunscreen-spf-50-pa-with-watermelon", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_pdp_catalog_verified_banner.png"), full_page=False)
        print("Captured 03_pdp_catalog_verified_banner.png")

        browser.close()
        print("Phase 11C.1 visual audit screenshots captured successfully!")

if __name__ == "__main__":
    run()
