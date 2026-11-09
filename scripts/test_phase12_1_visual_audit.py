"""Phase 12.1 Visual Audit: Staging PostgreSQL Live Application Verification."""

import os
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.getcwd(), "screenshots", "phase12_1")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. PostgreSQL Live Health & Readiness Probe
        print("1. Capturing Live PostgreSQL Health / Readiness Endpoint...")
        page.goto("http://127.0.0.1:8000/api/health/ready", wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_postgresql_staging_health_readiness.png"), full_page=False)
        print("Captured 01_postgresql_staging_health_readiness.png")

        # 2. Frontend Catalog powered by PostgreSQL backend
        print("2. Loading Catalog Page against PostgreSQL Backend...")
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_staging_catalog_postgresql_backend.png"), full_page=False)
        print("Captured 02_staging_catalog_postgresql_backend.png")

        # 3. Product Detail Page
        print("3. Navigating to PDP with live PostgreSQL data...")
        page.goto("http://127.0.0.1:5173/product/watermelon-cooling-sunscreen-spf-50", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_staging_pdp_live_postgresql.png"), full_page=False)
        print("Captured 03_staging_pdp_live_postgresql.png")

        browser.close()
        print("Phase 12.1 visual audit screenshots captured successfully!")

if __name__ == "__main__":
    run()
