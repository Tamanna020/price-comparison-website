"""Service layer for querying products and offers."""

import json
from typing import Optional
from src.database.connection import get_connection
from src.database.models import Offer, PricePoint, Product


def parse_specs(specs_raw: Optional[str]) -> dict:
    if not specs_raw:
        return {}
    try:
        return json.loads(specs_raw)
    except Exception:
        return {}


def get_all_categories(custom_path: Optional[str] = None) -> list[str]:
    """Retrieve distinct product categories."""
    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category ASC")
        rows = cursor.fetchall()
        return [r["category"] for r in rows]


def get_all_brands(category: Optional[str] = None, custom_path: Optional[str] = None) -> list[str]:
    """Retrieve distinct product brands, optionally filtered by category."""
    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        if category and category != "All":
            cursor.execute(
                "SELECT DISTINCT brand FROM products WHERE category = ? ORDER BY brand ASC",
                (category,),
            )
        else:
            cursor.execute("SELECT DISTINCT brand FROM products ORDER BY brand ASC")
        rows = cursor.fetchall()
        return [r["brand"] for r in rows if r["brand"]]


def get_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    search_query: Optional[str] = None,
    in_stock_only: bool = False,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "featured",
    include_history: bool = False,
    custom_path: Optional[str] = None,
) -> list[Product]:
    """
    Search and filter products with summary offer information.
    Supports case-insensitive multi-term search across title, brand, sku, description, and specs.
    sort_by options: 'featured', 'price_asc', 'price_desc', 'title_asc', 'title_desc', 'savings_desc'
    """
    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        sql = """
            SELECT 
                p.id, p.sku, p.title, p.brand, p.category, p.description, 
                p.specs_json, p.image_url, p.created_at
            FROM products p
            WHERE 1=1
        """
        params: list = []

        # 1. Category Filter
        if category and category != "All":
            sql += " AND p.category = ?"
            params.append(category)

        # 2. Brand Filter
        if brand and brand != "All":
            sql += " AND p.brand = ?"
            params.append(brand)

        # 3. Case-Insensitive Tokenized Search (matches title, brand, sku, description, specs)
        if search_query and search_query.strip():
            terms = search_query.strip().split()
            for term in terms:
                wildcard = f"%{term.lower()}%"
                sql += """
                    AND (
                        LOWER(p.title) LIKE ?
                        OR LOWER(p.brand) LIKE ?
                        OR LOWER(p.sku) LIKE ?
                        OR LOWER(p.description) LIKE ?
                        OR LOWER(p.specs_json) LIKE ?
                    )
                """
                params.extend([wildcard, wildcard, wildcard, wildcard, wildcard])

        sql += " ORDER BY p.id ASC"
        cursor.execute(sql, params)
        product_rows = cursor.fetchall()

        products: list[Product] = []
        for prow in product_rows:
            # Fetch offers for this product
            cursor.execute(
                """
                SELECT 
                    o.id, o.product_id, o.store_id, o.current_price, o.original_price,
                    o.shipping_cost, o.currency, o.availability, o.variant_name, o.condition,
                    o.offer_url, o.last_checked,
                    s.name as store_name, s.rating as store_rating
                FROM offers o
                JOIN stores s ON o.store_id = s.id
                WHERE o.product_id = ?
                ORDER BY (o.current_price + o.shipping_cost) ASC
                """,
                (prow["id"],),
            )
            offer_rows = cursor.fetchall()

            offers = []
            for orow in offer_rows:
                price_history = []
                if include_history:
                    cursor.execute(
                        """
                        SELECT id, offer_id, price, currency, data_source, data_status, recorded_at
                        FROM price_history
                        WHERE offer_id = ?
                        ORDER BY recorded_at ASC, id ASC
                        """,
                        (orow["id"],),
                    )
                    hist_rows = cursor.fetchall()
                    price_history = [
                        PricePoint(
                            id=h["id"] if "id" in h.keys() else None,
                            offer_id=h["offer_id"] if "offer_id" in h.keys() else orow["id"],
                            price=float(h["price"]),
                            recorded_at=str(h["recorded_at"]),
                            currency=h["currency"] if "currency" in h.keys() else "USD",
                            data_source=h["data_source"] if "data_source" in h.keys() else "demo_seed",
                            data_status=h["data_status"] if "data_status" in h.keys() else "demo",
                        )
                        for h in hist_rows
                    ]

                offers.append(
                    Offer(
                        id=orow["id"],
                        product_id=orow["product_id"],
                        store_id=orow["store_id"],
                        store_name=orow["store_name"],
                        store_rating=float(orow["store_rating"]),
                        current_price=float(orow["current_price"]),
                        original_price=float(orow["original_price"]) if orow["original_price"] is not None else None,
                        shipping_cost=float(orow["shipping_cost"]) if orow["shipping_cost"] is not None else 0.0,
                        currency=orow["currency"],
                        availability=orow["availability"] or "In Stock",
                        variant_name=orow["variant_name"] or "Standard",
                        condition=orow["condition"] or "Brand New",
                        offer_url=orow["offer_url"] or "",
                        last_checked=str(orow["last_checked"]),
                        price_history=price_history,
                    )
                )

            prod = Product(
                id=prow["id"],
                sku=prow["sku"],
                title=prow["title"],
                brand=prow["brand"],
                category=prow["category"],
                description=prow["description"] or "",
                specs=parse_specs(prow["specs_json"]),
                image_url=prow["image_url"] or "",
                created_at=str(prow["created_at"]),
                offers=offers,
            )
            products.append(prod)

        # 4. In-Stock Filter
        if in_stock_only:
            products = [p for p in products if p.available_offer_count > 0]

        # 5. Price Range Filter (based on lowest available price)
        if min_price is not None:
            products = [p for p in products if p.lowest_price is not None and p.lowest_price >= min_price]

        if max_price is not None:
            products = [p for p in products if p.lowest_price is not None and p.lowest_price <= max_price]

        # 6. Sorting Logic
        if sort_by == "price_asc":
            # Lowest available price first; items without valid prices go to end
            products.sort(key=lambda p: (p.lowest_price is None, p.lowest_price or float("inf")))
        elif sort_by == "price_desc":
            # Highest available price first; items without valid prices go to end
            products.sort(key=lambda p: (p.lowest_price is None, -(p.lowest_price or 0.0)))
        elif sort_by == "title_asc":
            products.sort(key=lambda p: p.title.lower())
        elif sort_by == "title_desc":
            products.sort(key=lambda p: p.title.lower(), reverse=True)
        elif sort_by == "savings_desc":
            # Sort by spread among available offers
            def available_spread(p: Product) -> float:
                avail_prices = [o.current_price for o in p.available_offers]
                if len(avail_prices) >= 2:
                    return max(avail_prices) - min(avail_prices)
                return 0.0

            products.sort(key=available_spread, reverse=True)

        return products


def get_product_by_id(product_id: int, custom_path: Optional[str] = None) -> Optional[Product]:
    """Retrieve full product details including all store offers and complete price history."""
    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, sku, title, brand, category, description, specs_json, image_url, created_at
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        )
        prow = cursor.fetchone()
        if not prow:
            return None

        # Fetch offers
        cursor.execute(
            """
            SELECT 
                o.id, o.product_id, o.store_id, o.current_price, o.original_price,
                o.shipping_cost, o.currency, o.availability, o.variant_name, o.condition,
                o.offer_url, o.last_checked,
                s.name as store_name, s.rating as store_rating
            FROM offers o
            JOIN stores s ON o.store_id = s.id
            WHERE o.product_id = ?
            ORDER BY (o.current_price + o.shipping_cost) ASC
            """,
            (product_id,),
        )
        offer_rows = cursor.fetchall()

        offers: list[Offer] = []
        for orow in offer_rows:
            # Fetch price history for this offer
            cursor.execute(
                """
                SELECT id, offer_id, price, currency, data_source, data_status, recorded_at
                FROM price_history
                WHERE offer_id = ?
                ORDER BY recorded_at ASC, id ASC
                """,
                (orow["id"],),
            )
            hist_rows = cursor.fetchall()
            price_history = [
                PricePoint(
                    id=h["id"] if "id" in h.keys() else None,
                    offer_id=h["offer_id"] if "offer_id" in h.keys() else orow["id"],
                    price=float(h["price"]),
                    recorded_at=str(h["recorded_at"]),
                    currency=h["currency"] if "currency" in h.keys() else "USD",
                    data_source=h["data_source"] if "data_source" in h.keys() else "demo_seed",
                    data_status=h["data_status"] if "data_status" in h.keys() else "demo",
                )
                for h in hist_rows
            ]

            offers.append(
                Offer(
                    id=orow["id"],
                    product_id=orow["product_id"],
                    store_id=orow["store_id"],
                    store_name=orow["store_name"],
                    store_rating=float(orow["store_rating"]),
                    current_price=float(orow["current_price"]),
                    original_price=float(orow["original_price"]) if orow["original_price"] is not None else None,
                    shipping_cost=float(orow["shipping_cost"]) if orow["shipping_cost"] is not None else 0.0,
                    currency=orow["currency"],
                    availability=orow["availability"] or "In Stock",
                    variant_name=orow["variant_name"] or "Standard",
                    condition=orow["condition"] or "Brand New",
                    offer_url=orow["offer_url"] or "",
                    last_checked=str(orow["last_checked"]),
                    price_history=price_history,
                )
            )

        return Product(
            id=prow["id"],
            sku=prow["sku"],
            title=prow["title"],
            brand=prow["brand"],
            category=prow["category"],
            description=prow["description"] or "",
            specs=parse_specs(prow["specs_json"]),
            image_url=prow["image_url"] or "",
            created_at=str(prow["created_at"]),
            offers=offers,
        )
