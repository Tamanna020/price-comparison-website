"""Diagnostic script for Phase 11A: Retailer Access & Feasibility Audit.

Safely tests 1-2 public endpoints per retailer (robots.txt and public product/search page)
with standard HTTP headers to observe:
1. robots.txt crawling directives and restrictions.
2. HTTP response code and server headers (Akamai, Cloudflare, AWS, etc.).
3. Availability of JSON-LD, OpenGraph, or embedded script payloads in static HTML.
4. Anti-bot / WAF challenge behavior (CAPTCHA, 403 Forbidden, 503 Service Unavailable).
"""

import json
import re
import urllib.request
import urllib.error
import ssl

RETAILERS = [
    {
        "name": "Nykaa",
        "domain": "nykaa.com",
        "robots_url": "https://www.nykaa.com/robots.txt",
        "test_url": "https://www.nykaa.com/dot-key-watermelon-cooling-sunscreen-spf-50-pa/p/7382216",
    },
    {
        "name": "Myntra",
        "domain": "myntra.com",
        "robots_url": "https://www.myntra.com/robots.txt",
        "test_url": "https://www.myntra.com/sunscreen/dot--key/dot--key-watermelon-cooling-sunscreen-spf-50-pa/23577782/buy",
    },
    {
        "name": "Purplle",
        "domain": "purplle.com",
        "robots_url": "https://www.purplle.com/robots.txt",
        "test_url": "https://www.purplle.com/product/dot-and-key-watermelon-cooling-sunscreen-spf-50-pa",
    },
    {
        "name": "Tira",
        "domain": "tirabeauty.com",
        "robots_url": "https://www.tirabeauty.com/robots.txt",
        "test_url": "https://www.tirabeauty.com/product/dot-key-watermelon-cooling-sunscreen-spf-50-pa-50g-1087095",
    },
    {
        "name": "Amazon India",
        "domain": "amazon.in",
        "robots_url": "https://www.amazon.in/robots.txt",
        "test_url": "https://www.amazon.in/Dot-Key-Watermelon-Sunscreen-Hyaluronic/dp/B0B5D982K5",
    },
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Create SSL context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def audit_url(url: str, is_robots: bool = False):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" if not is_robots else "text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            status = response.status
            headers = dict(response.headers)
            body = response.read().decode("utf-8", errors="replace")
            return {
                "status": status,
                "server": headers.get("server", "unknown"),
                "cf_ray": headers.get("cf-ray"),
                "content_type": headers.get("content-type", ""),
                "length": len(body),
                "body_snippet": body[:500],
                "full_body": body,
                "error": None,
            }
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return {
            "status": e.code,
            "server": e.headers.get("server", "unknown") if e.headers else "unknown",
            "cf_ray": e.headers.get("cf-ray") if e.headers else None,
            "content_type": e.headers.get("content-type", "") if e.headers else "",
            "length": len(body),
            "body_snippet": body[:500],
            "full_body": body,
            "error": f"HTTPError {e.code}: {e.reason}",
        }
    except Exception as e:
        return {
            "status": 0,
            "server": "none",
            "cf_ray": None,
            "content_type": "",
            "length": 0,
            "body_snippet": "",
            "full_body": "",
            "error": f"{type(e).__name__}: {str(e)}",
        }


def main():
    results = {}
    print("Beginning Retailer Feasibility Audit...")
    for ret in RETAILERS:
        name = ret["name"]
        print(f"\n--- Auditing {name} ({ret['domain']}) ---")
        
        # 1. Robots.txt
        print(f"Fetching robots.txt: {ret['robots_url']}")
        robots_res = audit_url(ret["robots_url"], is_robots=True)
        print(f"  robots.txt status: {robots_res['status']}, server: {robots_res['server']}, length: {robots_res['length']}")
        
        # Parse robots.txt for User-agent: * Disallow directives
        disallows = []
        user_agent_block = False
        if robots_res["full_body"]:
            for line in robots_res["full_body"].splitlines():
                line = line.strip()
                if line.lower().startswith("user-agent:"):
                    ua = line.split(":", 1)[1].strip()
                    user_agent_block = (ua == "*")
                elif user_agent_block and line.lower().startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path:
                        disallows.append(path)
                elif user_agent_block and line.lower().startswith("allow:"):
                    pass
        print(f"  Disallowed paths for '*': {len(disallows)} rules")

        # 2. Product Page
        print(f"Testing public product page: {ret['test_url']}")
        page_res = audit_url(ret["test_url"])
        print(f"  Page status: {page_res['status']}, server: {page_res['server']}, length: {page_res['length']}")
        if page_res["error"]:
            print(f"  Error: {page_res['error']}")

        # Analyze HTML content for JSON-LD, OpenGraph, prices
        has_json_ld = False
        has_og = False
        has_price_match = False
        has_captcha_or_block = False
        price_val = None

        if page_res["full_body"]:
            body = page_res["full_body"]
            # JSON-LD
            json_ld_matches = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', body, re.DOTALL | re.IGNORECASE)
            has_json_ld = len(json_ld_matches) > 0
            # OpenGraph
            has_og = "og:title" in body or "og:price" in body or "property=\"og:" in body
            # Check price in HTML
            p_match = re.search(r'₹\s*([\d,]+(?:\.\d+)?)', body)
            if p_match:
                has_price_match = True
                price_val = p_match.group(1)
            # Check bot blocks
            if "captcha" in body.lower() or "challenge-running" in body.lower() or "cf-browser-verification" in body.lower() or page_res["status"] in [403, 503, 429]:
                has_captcha_or_block = True

        results[name] = {
            "domain": ret["domain"],
            "robots_status": robots_res["status"],
            "robots_length": robots_res["length"],
            "robots_disallow_sample": disallows[:10],
            "page_url": ret["test_url"],
            "page_status": page_res["status"],
            "server": page_res["server"],
            "cf_ray": page_res["cf_ray"],
            "error": page_res["error"],
            "has_json_ld": has_json_ld,
            "has_og": has_og,
            "has_price_match": has_price_match,
            "price_sample": price_val,
            "has_captcha_or_block": has_captcha_or_block,
            "snippet": page_res["body_snippet"][:200].replace("\n", " "),
        }

    with open("retailer_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\nAudit complete! Results saved to retailer_audit_results.json")


if __name__ == "__main__":
    main()

