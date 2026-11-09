"""Inspect LIVE_VERIFIED offers 39 and 62."""

import sqlite3

conn = sqlite3.connect('data/pricewise.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

for oid in (39, 62):
    print(f"\n=================== INSPECTING OFFER {oid} ===================")
    cur.execute('''
        SELECT o.*, p.title as product_title, p.brand, p.category, s.name as store_name
        FROM offers o
        JOIN products p ON o.product_id = p.id
        JOIN stores s ON o.store_id = s.id
        WHERE o.id = ?
    ''', (oid,))
    offer = cur.fetchone()
    if not offer:
        print(f"Offer {oid} not found!")
        continue
    for k in offer.keys():
        print(f"  {k}: {offer[k]}")

    print("\n  Price History Entries:")
    cur.execute('''
        SELECT id, offer_id, price, currency, data_source, data_status, recorded_at
        FROM price_history WHERE offer_id = ?
        ORDER BY recorded_at
    ''', (oid,))
    for ph in cur.fetchall():
        print(f"    id={ph['id']}, price={ph['price']}, data_source={ph['data_source']}, data_status={ph['data_status']}, recorded_at={ph['recorded_at']}")

    print("\n  Evidence References linked:")
    cur.execute('''
        SELECT id, offer_id, product_id, store_id, evidence_type, file_path, source_url, verification_status, observed_price, created_at, notes
        FROM evidence_references WHERE offer_id = ? OR product_id = ?
    ''', (oid, offer['product_id']))
    evidence = cur.fetchall()
    if evidence:
        for ev in evidence:
            print(f"    Evidence #{ev['id']}: type={ev['evidence_type']}, status={ev['verification_status']}, url={ev['source_url']}, price={ev['observed_price']}, notes={ev['notes']}")
    else:
        print("    NO evidence_references record found!")
