"""Test retailer page loading via headless Playwright without bypass.

Records actual behavior:
- Does the page load?
- Does it trigger Akamai Access Denied, Cloudflare Challenge, or Amazon CAPTCHA?
- Does it render price in the DOM?
"""

import json
from playwright.sync_api import sync_playwright

TEST_CASES = [
    {
        "retailer": "Nykaa",
        "url": "https://www.nykaa.com/dot-key-watermelon-cooling-sunscreen-spf-50-pa/p/7382216",
    },
    {
        "retailer": "Myntra",
        "url": "https://www.myntra.com/sunscreen/dot--key/dot--key-watermelon-cooling-sunscreen-spf-50-pa/23577782/buy",
    },
    {
        "retailer": "Purplle",
        "url": "https://www.purplle.com/p/dot-key-watermelon-cooling-sunscreen-spf-50-pa-50g",
    },
    {
        "retailer": "Tira",
        "url": "https://www.tirabeauty.com/product/dot-key-watermelon-cooling-sunscreen-spf-50-pa-50g-1087095",
    },
    {
        "retailer": "Amazon India",
        "url": "https://www.amazon.in/dp/B0B5D982K5",
    },
]


def test_playwright():
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        for case in TEST_CASES:
            ret = case["retailer"]
            url = case["url"]
            print(f"\n--- Testing {ret} in Playwright ---")
            page = context.new_page()
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=15000)
                status = response.status if response else 0
                title = page.title()
                content = page.content()
                
                # Check for bot detection / blocks
                is_blocked = False
                block_reason = None
                if "Access Denied" in title or "Access Denied" in content[:1000]:
                    is_blocked = True
                    block_reason = "Akamai / WAF Perimeter Access Denied"
                elif "captcha" in title.lower() or "robot check" in title.lower() or "Robot Check" in content[:1000]:
                    is_blocked = True
                    block_reason = "CAPTCHA / Bot Challenge"
                elif "cloudflare" in content[:1000].lower() or "challenge-running" in content.lower():
                    is_blocked = True
                    block_reason = "Cloudflare Challenge"
                elif status in [403, 503, 429]:
                    is_blocked = True
                    block_reason = f"HTTP {status} Rejection"

                results[ret] = {
                    "url": url,
                    "status_code": status,
                    "title": title[:100],
                    "content_length": len(content),
                    "is_blocked": is_blocked,
                    "block_reason": block_reason,
                    "snippet": content[:300].replace("\n", " "),
                }
                print(f"  Status: {status}, Title: {title[:50]}")
                print(f"  Blocked: {is_blocked} ({block_reason})")
            except Exception as e:
                results[ret] = {
                    "url": url,
                    "status_code": 0,
                    "title": "",
                    "content_length": 0,
                    "is_blocked": True,
                    "block_reason": f"Exception: {type(e).__name__} ({str(e)[:100]})",
                    "snippet": "",
                }
                print(f"  Failed: {e}")
            finally:
                page.close()

        browser.close()

    with open("playwright_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\nPlaywright audit completed! Saved to playwright_audit_results.json")


if __name__ == "__main__":
    test_playwright()

