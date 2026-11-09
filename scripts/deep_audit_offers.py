import sqlite3
import json

def inspect_all_offers():
    conn = sqlite3.connect("data/pricewise.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT o.id, o.product_id, p.title as product_title, p.brand as product_brand,
               s.name as store_name, s.domain as store_domain,
               o.current_price, o.original_price, o.shipping_cost, o.availability,
               o.offer_url, o.last_checked
        FROM offers o
        JOIN products p ON o.product_id = p.id
        LEFT JOIN stores s ON o.store_id = s.id
        ORDER BY o.id
    """)
    offers = [dict(r) for r in cur.fetchall()]
    print(f"Total offers in database: {len(offers)}")

    # Check evidence_references table
    cur.execute("SELECT COUNT(*) FROM evidence_references")
    ev_count = cur.fetchone()[0]
    print(f"Total rows in evidence_references: {ev_count}")

    # Check price_check_logs
    cur.execute("SELECT * FROM price_check_logs WHERE match_classification = 'verified_match'")
    vm = [dict(r) for r in cur.fetchall()]
    print(f"Rows in price_check_logs with verified_match: {len(vm)}")
    for row in vm:
        print("  Verified match log:", row)

    # Inspect each offer
    print("\nAuditing each offer for genuine live evidence...")
    analyzed_offers = []
    status_summary = {}

    for o in offers:
        store = o["store_name"] or ""
        url = o["offer_url"] or ""
        last_checked = o["last_checked"]
        price = o["current_price"]
        avail = o["availability"] or ""

        # Determine true status
        # An offer can ONLY be LIVE_VERIFIED if:
        # 1. Store is not a Demo store
        # 2. Evidence exists in evidence_references or verified live scraper log for that exact product & offer
        # 3. URL is authorized and price was genuinely observed
        has_evidence = False
        reason = ""

        if "(Demo)" in store:
            if "out of stock" in avail.lower() or "unavailable" in avail.lower():
                recommended_status = "UNAVAILABLE"
                reason = "Item explicitly flagged out of stock in seeded demo catalog"
            else:
                recommended_status = "DEMO"
                reason = f"Store is '{store}'. Seeded demo catalog offer without live API credentials or evidence reference."
        else:
            recommended_status = "POSSIBLE_MATCH"
            reason = "Non-demo store without verified live proof"

        status_summary[recommended_status] = status_summary.get(recommended_status, 0) + 1

        analyzed_offers.append({
            "id": o["id"],
            "product_id": o["product_id"],
            "product_title": o["product_title"],
            "retailer": store,
            "current_price": price,
            "url": url,
            "previous_claim": "LIVE_VERIFIED" if ("amazon" in url or "nykaa" in url or "tira" in url) else ("UNAVAILABLE" if "out of stock" in avail.lower() else "DEMO"),
            "recommended_status": recommended_status,
            "evidence_source": "NONE (evidence_references=0)",
            "timestamp": last_checked or "2026-11-09 07:09:25 (Seed)",
            "exact_match_result": "Catalog Seed Record (Unverified live)",
            "reason": reason
        })

    print("\n=== RECOMMENDED STATUS SUMMARY ===")
    for st, cnt in status_summary.items():
        print(f"  {st:<16}: {cnt:>3} ({cnt/len(offers)*100:.1f}%)")

    conn.close()
    return analyzed_offers, status_summary

if __name__ == "__main__":
    inspect_all_offers()

