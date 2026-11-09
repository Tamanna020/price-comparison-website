"""Verification Script for Live Cloud Staging Deployment (Phase 13.1).

Usage:
    python scripts/verify_cloud_deployment.py --backend <backend_url> --frontend <frontend_url>

Example:
    python scripts/verify_cloud_deployment.py --backend https://pricewise-backend-staging.onrender.com --frontend https://pricewise-staging.vercel.app
"""

import argparse
import sys
import time
import urllib.request
import json

def test_endpoint(name: str, url: str, expected_status: int = 200, timeout: int = 30):
    print(f"Testing {name} ({url})...")
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PriceWiseStagingAudit/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            body = response.read().decode("utf-8")
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"  [PASS] Status {status} in {elapsed_ms:.1f}ms")
            try:
                data = json.loads(body)
                return True, data
            except Exception:
                return True, body
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  [FAIL] HTTP Error {e.code} in {elapsed_ms:.1f}ms: {e.reason}")
        return False, None
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  [FAIL] Connection Error in {elapsed_ms:.1f}ms: {e}")
        return False, None

def run_cloud_audit(backend_url: str, frontend_url: str):
    print("=" * 75)
    print("PRICEWISE AI — LIVE CLOUD STAGING DEPLOYMENT VERIFICATION")
    print("=" * 75)

    backend_clean = backend_url.rstrip("/")
    frontend_clean = frontend_url.rstrip("/") if frontend_url else None

    # 1. Backend Liveness
    live_ok, live_data = test_endpoint("Backend Liveness Probe", f"{backend_clean}/api/health/live")

    # 2. Backend Readiness (Checks PostgreSQL connection & count)
    ready_ok, ready_data = test_endpoint("Backend PostgreSQL Readiness Probe", f"{backend_clean}/api/health/ready")
    if ready_ok and isinstance(ready_data, dict):
        print(f"   Database Engine:  {ready_data.get('database_engine')}")
        print(f"   Database Healthy: {ready_data.get('database_healthy')}")
        print(f"   Product Count:    {ready_data.get('product_count')}")
        print(f"   Database Latency: {ready_data.get('latency_ms')}ms")

    # 3. Product Catalog
    cat_ok, cat_data = test_endpoint("Product Catalog API", f"{backend_clean}/api/products?limit=3")
    if cat_ok and isinstance(cat_data, list):
        print(f"   Retrieved {len(cat_data)} products. First SKU: {cat_data[0].get('sku')}")

    # 4. Frontend Probe
    if frontend_clean:
        fe_ok, _ = test_endpoint("Frontend SPA Availability", frontend_clean)
    else:
        fe_ok = False
        print("Frontend URL not supplied; skipping frontend check.")

    print("\n" + "=" * 75)
    if live_ok and ready_ok and cat_ok and (not frontend_clean or fe_ok):
        print("ALL LIVE CLOUD STAGING HEALTH PROBES PASSED!")
    else:
        print("SOME CHECKS FAILED OR CLOUD SERVICES ARE STILL INITIALIZING.")
    print("=" * 75)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify PriceWise AI live cloud deployment.")
    parser.add_argument("--backend", required=True, help="FastAPI backend URL (e.g. https://pricewise-api.onrender.com)")
    parser.add_argument("--frontend", required=False, help="Vercel frontend URL (e.g. https://pricewise.vercel.app)")
    args = parser.parse_args()

    run_cloud_audit(args.backend, args.frontend)
