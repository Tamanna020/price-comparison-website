import requests
import time
import statistics
import json

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

def benchmark_endpoint(url, method="GET", json_body=None, headers=None, runs=20):
    latencies = []
    statuses = []
    errors = 0

    for _ in range(runs):
        t0 = time.perf_counter()
        try:
            if method == "GET":
                res = requests.get(url, headers=headers, timeout=15)
            else:
                res = requests.post(url, json=json_body, headers=headers, timeout=15)
            dt = (time.perf_counter() - t0) * 1000
            latencies.append(dt)
            statuses.append(res.status_code)
            if res.status_code >= 400:
                errors += 1
        except Exception as e:
            dt = (time.perf_counter() - t0) * 1000
            latencies.append(dt)
            statuses.append(0)
            errors += 1
        time.sleep(0.02)

    latencies.sort()
    n = len(latencies)
    p50 = statistics.median(latencies)
    p95 = latencies[int(n * 0.95)] if n > 0 else 0
    mean = statistics.mean(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)
    std_dev = statistics.stdev(latencies) if n > 1 else 0

    return {
        "n": n,
        "success_rate": round(((n - errors) / n) * 100, 1),
        "mean_ms": round(mean, 2),
        "std_dev_ms": round(std_dev, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "min_ms": round(min_lat, 2),
        "max_ms": round(max_lat, 2),
        "common_status": statuses[0] if statuses else 0
    }

def run_granular_performance_audit():
    print("=== PriceWise AI: Granular Performance & Latency Audit ===")
    
    # Authenticate
    reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"perf_gran_{int(time.time())}@example.com",
        "password": "Password123!",
        "full_name": "Granular Tester"
    })
    token = reg.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}

    backend_endpoints = [
        ("Health Check", f"{BASE_URL}/api/health", "GET", None, None),
        ("Catalog List (All 34)", f"{BASE_URL}/api/products", "GET", None, None),
        ("Product Detail by ID (12)", f"{BASE_URL}/api/products/12", "GET", None, None),
        ("Product Detail by Slug", f"{BASE_URL}/api/products/watermelon-cooling-sunscreen-spf-50", "GET", None, None),
        ("Gemini Quota & Usage API", f"{BASE_URL}/api/beauty/usage", "GET", None, headers),
        ("User Routines API", f"{BASE_URL}/api/routines", "GET", None, headers),
        ("Live Compare API (Cached/Fast)", f"{BASE_URL}/api/compare/auto?product_id=12", "GET", None, None),
    ]

    frontend_routes = [
        ("Root Document (/)", f"{FRONTEND_URL}/", "GET", None, None),
        ("Catalog View (/products)", f"{FRONTEND_URL}/products", "GET", None, None),
        ("PDP Route (/product/...)", f"{FRONTEND_URL}/product/watermelon-cooling-sunscreen-spf-50", "GET", None, None),
        ("Beauty Assistant Route", f"{FRONTEND_URL}/beauty-assistant", "GET", None, None),
        ("Profile Route", f"{FRONTEND_URL}/profile", "GET", None, None),
    ]

    print("\n--- A. BACKEND API PERFORMANCE (N=20 runs per endpoint) ---")
    print(f"{'Endpoint':<30} | {'Status':>6} | {'P50':>8} | {'P95':>8} | {'Mean ± Std':>16} | {'Min - Max':>16}")
    print("-" * 96)
    
    backend_results = {}
    for desc, url, m, b, h in backend_endpoints:
        res = benchmark_endpoint(url, method=m, json_body=b, headers=h, runs=20)
        backend_results[desc] = res
        print(f"{desc:<30} | {res['common_status']:>6} | {res['p50_ms']:>6.1f}ms | {res['p95_ms']:>6.1f}ms | {res['mean_ms']:>5.1f} ± {res['std_dev_ms']:>4.1f}ms | {res['min_ms']:>5.1f} - {res['max_ms']:>5.1f}ms")

    print("\n--- B. FRONTEND ROUTE DELIVERY PERFORMANCE (N=20 runs per route) ---")
    print(f"{'Route':<30} | {'Status':>6} | {'P50':>8} | {'P95':>8} | {'Mean ± Std':>16} | {'Min - Max':>16}")
    print("-" * 96)

    frontend_results = {}
    for desc, url, m, b, h in frontend_routes:
        res = benchmark_endpoint(url, method=m, json_body=b, headers=h, runs=20)
        frontend_results[desc] = res
        print(f"{desc:<30} | {res['common_status']:>6} | {res['p50_ms']:>6.1f}ms | {res['p95_ms']:>6.1f}ms | {res['mean_ms']:>5.1f} ± {res['std_dev_ms']:>4.1f}ms | {res['min_ms']:>5.1f} - {res['max_ms']:>5.1f}ms")

    with open("data/performance_audit_metrics.json", "w") as f:
        json.dump({"backend": backend_results, "frontend": frontend_results}, f, indent=2)
    print("\n✓ Granular performance benchmark complete. Metrics saved to data/performance_audit_metrics.json")
    return backend_results, frontend_results

if __name__ == "__main__":
    run_granular_performance_audit()

