"""Ingests the 79 expanded genuine beauty products into data/pricewise.db.
Preserves all existing products, offers, verified requests, and price history records.
"""

from datetime import datetime, timezone
import json
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import sqlite3
from src.database.connection import get_connection
from src.database.expanded_beauty_data import EXPANDED_BEAUTY_PRODUCTS

STORE_NAME_TO_ID = {
    "Nykaa (Demo)": 6,
    "Tira (Demo)": 7,
    "Purplle (Demo)": 8,
    "Amazon India (Demo)": 9,
    "Myntra (Demo)": 10,
}

def ingest_expanded_products():
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check existing product count
        cursor.execute("SELECT COUNT(*) FROM products")
        prev_p_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM offers")
        prev_o_count = cursor.fetchone()[0]

        print(f"Previous Database State: {prev_p_count} products, {prev_o_count} offers")

        added_products = 0
        added_offers = 0
        added_history = 0

        for p in EXPANDED_BEAUTY_PRODUCTS:
            sku = p["sku"]
            title = p["title"]
            brand = p["brand"]
            category = p["category"]
            description = p["description"]
            specs_json = json.dumps(p["specs"])
            image_url = p["image_url"]

            # Check if product SKU already exists
            cursor.execute("SELECT id FROM products WHERE sku = ?", (sku,))
            existing = cursor.fetchone()

            if existing:
                product_id = existing[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO products (sku, title, brand, category, description, specs_json, image_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sku, title, brand, category, description, specs_json, image_url, now_iso),
                )
                product_id = cursor.lastrowid
                added_products += 1

            # Insert offers for this product
            for offer in p.get("offers", []):
                store_name = offer["store_name"]
                store_id = STORE_NAME_TO_ID.get(store_name)
                if not store_id:
                    continue

                curr_price = offer["current_price"]
                orig_price = offer.get("original_price")
                shipping_cost = offer.get("shipping_cost", 0.0)
                availability = offer.get("availability", "In Stock")
                offer_url = offer.get("offer_url", "")

                # Check if offer for this product & store already exists
                cursor.execute(
                    "SELECT id FROM offers WHERE product_id = ? AND store_id = ?",
                    (product_id, store_id),
                )
                existing_offer = cursor.fetchone()

                if not existing_offer:
                    cursor.execute(
                        """
                        INSERT INTO offers (
                            product_id, store_id, current_price, original_price,
                            shipping_cost, currency, availability, variant_name,
                            condition, offer_url, last_checked
                        ) VALUES (?, ?, ?, ?, ?, 'INR', ?, 'Standard', 'Brand New', ?, ?)
                        """,
                        (product_id, store_id, curr_price, orig_price, shipping_cost, availability, offer_url, now_iso),
                    )
                    offer_id = cursor.lastrowid
                    added_offers += 1

                    # Add initial price history entry
                    cursor.execute(
                        """
                        INSERT INTO price_history (
                            offer_id, price, currency, data_source, data_status, recorded_at
                        ) VALUES (?, ?, 'INR', 'demo_seed', 'demo', ?)
                        """,
                        (offer_id, curr_price, now_iso),
                    )
                    added_history += 1

        cursor.execute("SELECT COUNT(*) FROM products")
        new_p_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM offers")
        new_o_count = cursor.fetchone()[0]

        print("=" * 80)
        print("EXPANDED BEAUTY CATALOG INGESTION SUMMARY:")
        print(f"  New Products Added:      {added_products}")
        print(f"  New Offers Added:        {added_offers}")
        print(f"  New Price History Added: {added_history}")
        print(f"  Total Products in DB:    {new_p_count}")
        print(f"  Total Offers in DB:      {new_o_count}")
        print("=" * 80)

if __name__ == "__main__":
    ingest_expanded_products()
