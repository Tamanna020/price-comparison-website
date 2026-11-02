"""Persistent Price Tracking & Alert Service for PriceWise AI (Phase 6).

Handles:
- Adding/removing tracked products with positive target prices
- Pausing and resuming tracking
- Deterministic alert evaluation (Target Price Reached & Meaningful Price Drop)
- Duplicate alert prevention on repeated evaluations / page refreshes
- Alert history persistence with read/unread tracking
- Safe integration with SQLite database and existing price history
"""

from datetime import datetime, timezone
from typing import Any, Optional

from src.database.connection import get_connection, migrate_db
from src.database.models import PriceAlert, PriceTrackingRecord


# Configurable alert thresholds
MIN_PRICE_DROP_DOLLARS = 1.00  # At least $1.00 drop
MIN_PRICE_DROP_PERCENT = 1.0   # At least 1.0% drop


def add_tracked_product(
    product_id: int,
    target_price: float,
    note: Optional[str] = None,
    alert_trigger_type: str = "target_or_drop",
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str, Optional[int]]:
    """
    Add a product to the user's price tracking list.
    
    Validates:
    - product_id must exist in products table
    - target_price must be positive (> 0)
    - prevents duplicate tracking records for the same product for the given user
    
    Returns:
        (success: bool, message: str, tracking_id: Optional[int])
    """
    # 1. Validate target price
    if target_price is None:
        return False, "Target price cannot be empty.", None
    try:
        target_price_flt = float(target_price)
    except (ValueError, TypeError):
        return False, "Target price must be a valid numeric value.", None

    if target_price_flt <= 0:
        return False, "Target price must be greater than zero.", None

    # 2. Validate trigger type
    valid_types = ("target_or_drop", "target_only", "drop_only")
    if alert_trigger_type not in valid_types:
        alert_trigger_type = "target_or_drop"

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # 3. Validate product exists
        cursor.execute("SELECT id, title FROM products WHERE id = ?", (product_id,))
        prod = cursor.fetchone()
        if not prod:
            return False, f"Product #{product_id} does not exist in the catalog.", None

        # 4. Check for duplicate tracking record for this user / context
        if user_id is not None:
            cursor.execute(
                "SELECT id, status FROM price_tracking WHERE product_id = ? AND user_id = ?",
                (product_id, user_id),
            )
        else:
            cursor.execute(
                "SELECT id, status FROM price_tracking WHERE product_id = ? AND user_id IS NULL",
                (product_id,),
            )

        existing = cursor.fetchone()
        if existing:
            return False, "This product is already in your Price Tracker.", existing["id"]

        # 5. Fetch current lowest available offer price as initial observation baseline
        cursor.execute(
            """
            SELECT o.current_price, o.shipping_cost, s.name as store_name
            FROM offers o
            JOIN stores s ON o.store_id = s.id
            WHERE o.product_id = ? AND o.current_price > 0
              AND LOWER(o.availability) NOT IN ('out of stock', 'unavailable', 'discontinued')
            ORDER BY o.current_price ASC
            LIMIT 1
            """,
            (product_id,),
        )
        offer_row = cursor.fetchone()

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        initial_price = float(offer_row["current_price"]) if offer_row else None

        # 6. Insert tracking record
        cursor.execute(
            """
            INSERT INTO price_tracking (
                user_id, product_id, target_price, created_at, status,
                last_observed_price, last_checked_at, alert_trigger_type, note
            ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            (
                user_id,
                product_id,
                round(target_price_flt, 2),
                now_str,
                initial_price,
                now_str,
                alert_trigger_type,
                note.strip() if note else None,
            ),
        )
        new_id = cursor.lastrowid

    return True, f"Started tracking '{prod['title']}' at target ${target_price_flt:,.2f}.", new_id


def get_tracked_products(
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    include_legacy: bool = False,
    custom_path: Optional[str] = None,
) -> list[PriceTrackingRecord]:
    """
    Retrieve all tracked products with joined catalog and current pricing details.
    Optionally filter by status ('active' or 'paused') and user_id.
    """
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        sql = """
            SELECT 
                t.id, t.user_id, t.product_id, t.target_price, t.created_at, t.status,
                t.last_observed_price, t.last_checked_at, t.last_alert_at,
                t.last_alert_price, t.last_alert_type, t.alert_trigger_type, t.note,
                p.title as product_title, p.brand as product_brand, p.category as product_category,
                p.sku as product_sku, p.image_url as product_image_url
            FROM price_tracking t
            JOIN products p ON t.product_id = p.id
        """
        where_clauses = []
        params = []
        if status:
            where_clauses.append("t.status = ?")
            params.append(status)

        if user_id is not None:
            if include_legacy:
                where_clauses.append("(t.user_id = ? OR t.user_id IS NULL)")
                params.append(user_id)
            else:
                where_clauses.append("t.user_id = ?")
                params.append(user_id)
        elif include_legacy:
            where_clauses.append("t.user_id IS NULL")

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        sql += " ORDER BY t.created_at DESC, t.id DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        records: list[PriceTrackingRecord] = []
        for r in rows:
            # Query lowest available offer for this product
            cursor.execute(
                """
                SELECT o.current_price, s.name as store_name, o.availability
                FROM offers o
                JOIN stores s ON o.store_id = s.id
                WHERE o.product_id = ? AND o.current_price > 0
                ORDER BY (
                    CASE WHEN LOWER(o.availability) IN ('out of stock', 'unavailable', 'discontinued') THEN 1 ELSE 0 END
                ) ASC, o.current_price ASC
                LIMIT 1
                """,
                (r["product_id"],),
            )
            offer_row = cursor.fetchone()

            if offer_row:
                avail_str = str(offer_row["availability"] or "").strip().lower()
                is_avail = avail_str not in ("out of stock", "unavailable", "discontinued")
                cur_price = float(offer_row["current_price"])
                cur_store = str(offer_row["store_name"])
            else:
                is_avail = False
                cur_price = None
                cur_store = None

            records.append(
                PriceTrackingRecord(
                    id=r["id"],
                    user_id=r["user_id"] if ("user_id" in r.keys() and r["user_id"] is not None) else None,
                    product_id=r["product_id"],
                    target_price=float(r["target_price"]),
                    created_at=str(r["created_at"]),
                    status=str(r["status"] or "active"),
                    last_observed_price=float(r["last_observed_price"]) if r["last_observed_price"] is not None else None,
                    last_checked_at=str(r["last_checked_at"]) if r["last_checked_at"] else None,
                    last_alert_at=str(r["last_alert_at"]) if r["last_alert_at"] else None,
                    last_alert_price=float(r["last_alert_price"]) if r["last_alert_price"] is not None else None,
                    last_alert_type=str(r["last_alert_type"]) if r["last_alert_type"] else None,
                    alert_trigger_type=str(r["alert_trigger_type"] or "target_or_drop"),
                    note=str(r["note"]) if r["note"] else None,
                    product_title=str(r["product_title"]),
                    product_brand=str(r["product_brand"]),
                    product_category=str(r["product_category"]),
                    product_sku=str(r["product_sku"]),
                    product_image_url=str(r["product_image_url"]),
                    current_lowest_price=cur_price,
                    current_lowest_store=cur_store,
                    is_available=is_avail,
                )
            )

        return records


def get_tracking_by_id(
    tracking_id: int,
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> Optional[PriceTrackingRecord]:
    """Retrieve a single tracking record by its primary key ID with ownership check."""
    records = get_tracked_products(user_id=user_id, custom_path=custom_path)
    for r in records:
        if r.id == tracking_id:
            return r
    return None


def get_tracking_by_product_id(
    product_id: int,
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> Optional[PriceTrackingRecord]:
    """Retrieve a tracking record for a specific product ID if it exists for the given user."""
    records = get_tracked_products(user_id=user_id, custom_path=custom_path)
    for r in records:
        if r.product_id == product_id:
            return r
    return None


def update_target_price(
    tracking_id: int,
    new_target_price: float,
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Update the target price on an existing tracking record with authorization check.
    Resets the last alert price memory so that if the new target is already met,
    a fresh alert can trigger on the next evaluation.
    """
    if new_target_price is None:
        return False, "Target price cannot be empty."
    try:
        new_target_flt = float(new_target_price)
    except (ValueError, TypeError):
        return False, "Target price must be a valid numeric value."

    if new_target_flt <= 0:
        return False, "Target price must be greater than zero."

    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id FROM price_tracking WHERE id = ?", (tracking_id,))
        row = cursor.fetchone()
        if not row:
            return False, f"Tracking record #{tracking_id} not found."
        if user_id is not None and row["user_id"] is not None and row["user_id"] != user_id:
            return False, "Access denied: you do not own this tracking record."

        cursor.execute(
            """
            UPDATE price_tracking 
            SET target_price = ?, last_alert_price = NULL, last_alert_type = NULL
            WHERE id = ?
            """,
            (round(new_target_flt, 2), tracking_id),
        )

    return True, f"Target price updated to ${new_target_flt:,.2f}."


def update_tracking_note(
    tracking_id: int,
    note: Optional[str],
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Update user note on a tracking record with authorization check."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id FROM price_tracking WHERE id = ?", (tracking_id,))
        row = cursor.fetchone()
        if not row:
            return False, f"Tracking record #{tracking_id} not found."
        if user_id is not None and row["user_id"] is not None and row["user_id"] != user_id:
            return False, "Access denied: you do not own this tracking record."

        cursor.execute(
            "UPDATE price_tracking SET note = ? WHERE id = ?",
            (note.strip() if note else None, tracking_id),
        )

    return True, "Tracking note updated."


def pause_tracking(
    tracking_id: int,
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Pause an active tracking record with authorization check."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id FROM price_tracking WHERE id = ?", (tracking_id,))
        row = cursor.fetchone()
        if not row:
            return False, f"Tracking record #{tracking_id} not found."
        if user_id is not None and row["user_id"] is not None and row["user_id"] != user_id:
            return False, "Access denied: you do not own this tracking record."

        cursor.execute("UPDATE price_tracking SET status = 'paused' WHERE id = ?", (tracking_id,))

    return True, "Price tracking paused."


def resume_tracking(
    tracking_id: int,
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Resume a paused tracking record with authorization check."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id FROM price_tracking WHERE id = ?", (tracking_id,))
        row = cursor.fetchone()
        if not row:
            return False, f"Tracking record #{tracking_id} not found."
        if user_id is not None and row["user_id"] is not None and row["user_id"] != user_id:
            return False, "Access denied: you do not own this tracking record."

        cursor.execute("UPDATE price_tracking SET status = 'active' WHERE id = ?", (tracking_id,))

    return True, "Price tracking resumed."


def remove_tracking(
    tracking_id: int,
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> tuple[bool, str]:
    """Remove a product from price tracking with authorization check."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id FROM price_tracking WHERE id = ?", (tracking_id,))
        row = cursor.fetchone()
        if not row:
            return False, f"Tracking record #{tracking_id} not found."
        if user_id is not None and row["user_id"] is not None and row["user_id"] != user_id:
            return False, "Access denied: you do not own this tracking record."

        cursor.execute("DELETE FROM price_tracking WHERE id = ?", (tracking_id,))

    return True, "Product removed from Price Tracker."


# =====================================================================
# Alert Evaluation & Duplicate Prevention Engine
# =====================================================================

def evaluate_tracking_rules(
    tracking_id: Optional[int] = None,
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
    reference_date: Optional[datetime] = None,
) -> dict[str, Any]:
    """
    Evaluate active tracking records against stored price observations.
    
    Alert Rules:
    1. Target Price Reached: observed_price <= target_price
    2. Meaningful Price Drop: observed_price dropped >= $1.00 and >= 1.0% vs previous observation
    3. Paused records: strictly excluded from alert generation
    4. Out of stock / missing prices: no price-based alerts
    5. Duplicate Alert Prevention:
       - Uses trigger_key constraint and tracking-level alert memory (last_alert_price)
       - Repeating evaluation on unchanged price does NOT generate duplicate alerts
       - A genuine subsequent price change can generate a new alert
    
    Returns:
        dict: {"evaluated_count": int, "alerts_generated": int, "alerts": list[PriceAlert]}
    """
    migrate_db(custom_path)
    now_dt = reference_date or datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    new_alerts: list[PriceAlert] = []
    evaluated_count = 0

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # Query active tracking records
        sql = """
            SELECT 
                t.id, t.user_id, t.product_id, t.target_price, t.status,
                t.last_observed_price, t.last_alert_price, t.last_alert_type,
                t.alert_trigger_type, p.title as product_title, p.brand as product_brand
            FROM price_tracking t
            JOIN products p ON t.product_id = p.id
            WHERE t.status = 'active'
        """
        params = []
        if tracking_id:
            sql += " AND t.id = ?"
            params.append(tracking_id)
        if user_id is not None:
            sql += " AND t.user_id = ?"
            params.append(user_id)

        cursor.execute(sql, params)
        active_records = cursor.fetchall()

        for rec in active_records:
            t_id = rec["id"]
            p_id = rec["product_id"]
            t_user_id = rec["user_id"] if ("user_id" in rec.keys() and rec["user_id"] is not None) else None
            target_price = float(rec["target_price"])
            trigger_type = str(rec["alert_trigger_type"] or "target_or_drop")
            last_alert_price = float(rec["last_alert_price"]) if rec["last_alert_price"] is not None else None
            last_alert_type = str(rec["last_alert_type"]) if rec["last_alert_type"] else None
            prod_title = str(rec["product_title"])

            evaluated_count += 1

            # 1. Fetch lowest available offer with valid price
            cursor.execute(
                """
                SELECT o.id as offer_id, o.current_price, s.name as store_name, o.availability
                FROM offers o
                JOIN stores s ON o.store_id = s.id
                WHERE o.product_id = ? AND o.current_price > 0
                  AND LOWER(o.availability) NOT IN ('out of stock', 'unavailable', 'discontinued')
                ORDER BY o.current_price ASC
                LIMIT 1
                """,
                (p_id,),
            )
            lowest_offer = cursor.fetchone()

            # If out of stock or no valid offer, skip price alerts
            if not lowest_offer:
                cursor.execute(
                    "UPDATE price_tracking SET last_checked_at = ? WHERE id = ?",
                    (now_str, t_id),
                )
                continue

            cur_price = round(float(lowest_offer["current_price"]), 2)
            store_name = str(lowest_offer["store_name"])
            offer_id = lowest_offer["offer_id"]

            # 2. Check previous price from tracker memory
            previous_price: Optional[float] = None
            if rec["last_observed_price"] is not None:
                stored_prev = round(float(rec["last_observed_price"]), 2)
                if abs(stored_prev - cur_price) >= 0.01:
                    previous_price = stored_prev

            # -------------------------------------------------------------
            # Rule A: Target Price Reached Alert
            # -------------------------------------------------------------
            target_alert_triggered = False
            if trigger_type in ("target_or_drop", "target_only"):
                if cur_price <= target_price:
                    # Duplicate Alert Check:
                    # Has this exact price condition already been notified for this target?
                    is_duplicate_target = (
                        last_alert_type == "target_reached"
                        and last_alert_price is not None
                        and abs(last_alert_price - cur_price) < 0.01
                    )

                    if not is_duplicate_target:
                        trigger_key = f"{t_id}:target_reached:{cur_price}"
                        message = (
                            f"🎯 Target price reached! {prod_title} is now ${cur_price:,.2f} "
                            f"at {store_name} (Your Target: ${target_price:,.2f})."
                        )
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO price_alerts (
                                user_id, tracking_id, product_id, alert_type, observed_price,
                                target_price, message, created_at, is_read, trigger_key,
                                delivery_status, channel
                            ) VALUES (?, ?, ?, 'target_reached', ?, ?, ?, ?, 0, ?, 'in_app_delivered', 'in_app')
                            """,
                            (t_user_id, t_id, p_id, cur_price, target_price, message, now_str, trigger_key),
                        )
                        if cursor.rowcount > 0:
                            alert_id = cursor.lastrowid
                            new_alerts.append(
                                PriceAlert(
                                    id=alert_id,
                                    user_id=t_user_id,
                                    tracking_id=t_id,
                                    product_id=p_id,
                                    alert_type="target_reached",
                                    observed_price=cur_price,
                                    target_price=target_price,
                                    message=message,
                                    created_at=now_str,
                                    is_read=False,
                                    trigger_key=trigger_key,
                                    product_title=prod_title,
                                    product_brand=str(rec["product_brand"]),
                                    delivery_status="in_app_delivered",
                                    channel="in_app",
                                )
                            )
                            cursor.execute(
                                """
                                UPDATE price_tracking 
                                SET last_alert_at = ?, last_alert_price = ?, last_alert_type = 'target_reached'
                                WHERE id = ?
                                """,
                                (now_str, cur_price, t_id),
                            )
                            target_alert_triggered = True

            # -------------------------------------------------------------
            # Rule B: Meaningful Price Drop Alert
            # -------------------------------------------------------------
            if trigger_type in ("target_or_drop", "drop_only") and not target_alert_triggered:
                if previous_price is not None and previous_price > cur_price:
                    drop_amount = round(previous_price - cur_price, 2)
                    drop_pct = (drop_amount / previous_price) * 100.0

                    # Check threshold: at least $1.00 AND at least 1.0% drop
                    if drop_amount >= MIN_PRICE_DROP_DOLLARS and drop_pct >= MIN_PRICE_DROP_PERCENT:
                        # Duplicate Drop Alert Check
                        is_duplicate_drop = (
                            last_alert_type == "price_drop"
                            and last_alert_price is not None
                            and abs(last_alert_price - cur_price) < 0.01
                        )

                        if not is_duplicate_drop:
                            drop_key = f"{t_id}:price_drop:{previous_price}->{cur_price}"
                            message = (
                                f"📉 Price drop! {prod_title} dropped ${drop_amount:,.2f} "
                                f"({drop_pct:.1f}%) from ${previous_price:,.2f} to ${cur_price:,.2f} at {store_name}."
                            )
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO price_alerts (
                                    user_id, tracking_id, product_id, alert_type, observed_price,
                                    previous_price, target_price, message, created_at, is_read, trigger_key,
                                    delivery_status, channel
                                ) VALUES (?, ?, ?, 'price_drop', ?, ?, ?, ?, ?, 0, ?, 'in_app_delivered', 'in_app')
                                """,
                                (t_user_id, t_id, p_id, cur_price, previous_price, target_price, message, now_str, drop_key),
                            )
                            if cursor.rowcount > 0:
                                alert_id = cursor.lastrowid
                                new_alerts.append(
                                    PriceAlert(
                                        id=alert_id,
                                        user_id=t_user_id,
                                        tracking_id=t_id,
                                        product_id=p_id,
                                        alert_type="price_drop",
                                        observed_price=cur_price,
                                        previous_price=previous_price,
                                        target_price=target_price,
                                        message=message,
                                        created_at=now_str,
                                        is_read=False,
                                        trigger_key=drop_key,
                                        product_title=prod_title,
                                        product_brand=str(rec["product_brand"]),
                                        delivery_status="in_app_delivered",
                                        channel="in_app",
                                    )
                                )
                                cursor.execute(
                                    """
                                    UPDATE price_tracking 
                                    SET last_alert_at = ?, last_alert_price = ?, last_alert_type = 'price_drop'
                                    WHERE id = ?
                                    """,
                                    (now_str, cur_price, t_id),
                                )

            # Update last observed price and checked timestamp
            cursor.execute(
                """
                UPDATE price_tracking 
                SET last_observed_price = ?, last_checked_at = ?
                WHERE id = ?
                """,
                (cur_price, now_str, t_id),
            )

    return {
        "evaluated_count": evaluated_count,
        "alerts_generated": len(new_alerts),
        "alerts": new_alerts,
    }


# =====================================================================
# Alert History & Inbox Management
# =====================================================================

def get_alert_history(
    unread_only: bool = False,
    alert_type: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 50,
    custom_path: Optional[str] = None,
) -> list[PriceAlert]:
    """Retrieve persisted alert records joined with product information, optionally scoped to user."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        sql = """
            SELECT 
                a.id, a.user_id, a.tracking_id, a.product_id, a.alert_type,
                a.observed_price, a.previous_price, a.target_price,
                a.message, a.created_at, a.is_read, a.trigger_key,
                p.title as product_title, p.brand as product_brand, p.image_url as product_image_url
            FROM price_alerts a
            JOIN products p ON a.product_id = p.id
            WHERE 1=1
        """
        params = []
        if unread_only:
            sql += " AND a.is_read = 0"
        if alert_type and alert_type != "All":
            sql += " AND a.alert_type = ?"
            params.append(alert_type)
        if user_id is not None:
            sql += " AND a.user_id = ?"
            params.append(user_id)

        sql += " ORDER BY a.created_at DESC, a.id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        return [
            PriceAlert(
                id=r["id"],
                user_id=r["user_id"] if ("user_id" in r.keys() and r["user_id"] is not None) else None,
                tracking_id=r["tracking_id"],
                product_id=r["product_id"],
                alert_type=str(r["alert_type"]),
                observed_price=float(r["observed_price"]),
                previous_price=float(r["previous_price"]) if r["previous_price"] is not None else None,
                target_price=float(r["target_price"]) if r["target_price"] is not None else None,
                message=str(r["message"]),
                created_at=str(r["created_at"]),
                is_read=bool(r["is_read"]),
                trigger_key=str(r["trigger_key"]) if r["trigger_key"] else None,
                delivery_status=str(r["delivery_status"]) if "delivery_status" in r.keys() and r["delivery_status"] else "in_app_delivered",
                channel=str(r["channel"]) if "channel" in r.keys() and r["channel"] else "in_app",
                product_title=str(r["product_title"]),
                product_brand=str(r["product_brand"]),
                product_image_url=str(r["product_image_url"]),
            )
            for r in rows
        ]


def mark_alert_read(
    alert_id: int,
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> bool:
    """Mark a specific alert as read with ownership verification."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        if user_id is not None:
            cursor.execute("SELECT id, user_id FROM price_alerts WHERE id = ?", (alert_id,))
            row = cursor.fetchone()
            if not row:
                return False
            if row["user_id"] is not None and row["user_id"] != user_id:
                return False
            cursor.execute(
                "UPDATE price_alerts SET is_read = 1 WHERE id = ? AND (user_id = ? OR user_id IS NULL)",
                (alert_id, user_id),
            )
        else:
            cursor.execute("UPDATE price_alerts SET is_read = 1 WHERE id = ?", (alert_id,))
        return cursor.rowcount > 0


def mark_all_alerts_read(
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> int:
    """Mark all unread alerts as read for the user context. Returns number of updated alerts."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        if user_id is not None:
            cursor.execute(
                "UPDATE price_alerts SET is_read = 1 WHERE is_read = 0 AND user_id = ?",
                (user_id,),
            )
        else:
            cursor.execute("UPDATE price_alerts SET is_read = 1 WHERE is_read = 0")
        return cursor.rowcount


def get_tracking_summary_stats(
    user_id: Optional[int] = None,
    custom_path: Optional[str] = None,
) -> dict[str, int]:
    """Compute dashboard summary counts for tracking and alerts from actual DB records."""
    migrate_db(custom_path)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # 1. Total tracked records
        if user_id is not None:
            cursor.execute("SELECT COUNT(*) as cnt FROM price_tracking WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT COUNT(*) as cnt FROM price_tracking")
        total_tracked = cursor.fetchone()["cnt"]

        # 2. Active tracking records
        if user_id is not None:
            cursor.execute("SELECT COUNT(*) as cnt FROM price_tracking WHERE status = 'active' AND user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT COUNT(*) as cnt FROM price_tracking WHERE status = 'active'")
        active_tracking = cursor.fetchone()["cnt"]

        # 3. Unread alerts
        if user_id is not None:
            cursor.execute("SELECT COUNT(*) as cnt FROM price_alerts WHERE is_read = 0 AND user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT COUNT(*) as cnt FROM price_alerts WHERE is_read = 0")
        unread_alerts = cursor.fetchone()["cnt"]

    # 4. Target reached count based on current lowest prices
    records = get_tracked_products(status="active", user_id=user_id, custom_path=custom_path)
    target_reached = sum(1 for r in records if r.is_target_reached)

    return {
        "total_tracked": total_tracked,
        "active_tracking": active_tracking,
        "target_reached": target_reached,
        "unread_alerts": unread_alerts,
    }
