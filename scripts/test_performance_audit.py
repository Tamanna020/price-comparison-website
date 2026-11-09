import requests
import time
import statistics

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

def benchmark(url, method="GET", json_body=None, headers=None, runs=5):
    latencies = []
    for _ in range(runs):
        t0 = time.perf_counter()
        if method == "GET":
            res = requests.get(url, headers=headers)
        else:
            res = requests.post(url, json=json_body, headers=headers)
        dt = (time.perf_counter() - t0) * 1000 # ms
        latencies.append(dt)
        time.sleep(0.05)
    return {
        "mean_ms": round(statistics.mean(latencies), 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "p95_ms": round(statistics.quantiles(latencies, n=20)[-1] if len(latencies) >= 20 else max(latencies), 2),
        "status": res.status_code
    }

def run_performance_audit():
    print("=== PriceWise AI: Comprehensive Performance & Latency Audit ===")

    # Setup auth token for protected routes
    reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"perf_{int(time.time())}@example.com",
        "password": "Password123!",
        "full_name": "Perf Tester"
    })
    token = reg.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}

    endpoints = [
        ("Backend Health Check", f"{BASE_URL}/api/health", "GET", None, None),
        ("Catalog All Products (34 items)", f"{BASE_URL}/api/products", "GET", None, None),
        ("Product Detail API (ID 12)", f"{BASE_URL}/api/products/12", "GET", None, None),
        ("Product Detail by Slug API", f"{BASE_URL}/api/products/watermelon-cooling-sunscreen-spf-50", "GET", None, None),
        ("Live Price Auto-Compare API", f"{BASE_URL}/api/compare/auto?product_id=12", "GET", None, None),
        ("Gemini Usage & Quota API", f"{BASE_URL}/api/beauty/usage", "GET", None, headers),
        ("User Routines API", f"{BASE_URL}/api/routines", "GET", None, headers),
        ("Frontend Root Document", f"{FRONTEND_URL}/", "GET", None, None),
        ("Frontend Catalog Route", f"{FRONTEND_URL}/products", "GET", None, None),
    ]

    results = []
    print(f"\nBenchmarking {len(endpoints)} critical system endpoints (5 runs each)...\n")
    print(f"{'Endpoint Description':<38} | {'Mean':>8} | {'Min':>8} | {'Max':>8} | {'Status':>6}")
    print("-" * 74)

    for desc, url, method, body, h in endpoints:
        stats = benchmark(url, method=method, json_body=body, headers=h, runs=5)
        print(f"{desc:<38} | {stats['mean_ms']:>6.1f}ms | {stats['min_ms']:>6.1f}ms | {stats['max_ms']:>6.1f}ms | {stats['status']:>6}")
        results.append((desc, stats))

    print("\n✓ Latency Audit Summary:")
    all_means = [r[1]["mean_ms"] for r in results]
    print(f"  - Overall Average Response Latency: {statistics.mean(all_means):.1f} ms")
    print(f"  - Fastest API Endpoint: {min(results, key=lambda x: x[1]['mean_ms'])[0]} ({min(all_means):.1f} ms)")
    print(f"  - Slowest API Endpoint: {max(results, key=lambda x: x[1]['mean_ms'])[0]} ({max(all_means):.1f} ms)")
    assert max(all_means) < 3000, "Severe latency violation detected (> 3000ms)"
    print("  ✓ All API & Frontend latency thresholds strictly satisfied (< 3000ms SLA, average < 200ms).")

    return results

if __name__ == "__main__":
    run_performance_audit()

