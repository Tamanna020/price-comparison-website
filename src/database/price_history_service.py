"""Persistent price history tracking service.
Handles timestamped price observations, deduplication intervals,
time-window filtering (30-day, 90-day, all-time), and safe updates.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from dataclasses import dataclass
from src.database.connection import get_connection
from src.database.models import PricePoint


def parse_timestamp(ts_str) -> Optional[datetime]:
    """Parse various datetime string formats or native datetime objects into UTC-aware datetime.
    
    PostgreSQL (psycopg) returns native datetime.datetime objects for TIMESTAMP columns.
    SQLite returns strings. This function handles both types safely.
    """
    if not ts_str:
        return None
    # Handle native datetime objects from PostgreSQL psycopg driver
    if isinstance(ts_str, datetime):
        if ts_str.tzinfo is None:
            return ts_str.replace(tzinfo=timezone.utc)
        return ts_str.astimezone(timezone.utc)
    # Handle string timestamps from SQLite
    clean_ts = ts_str.strip()
    try:
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(clean_ts.rstrip("Z"), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def record_price_observation(
    offer_id: int,
    price: float,
    currency: str = "USD",
    recorded_at: Optional[str] = None,
    data_source: str = "manual_check",
    data_status: str = "demo",
    deduplication_window_seconds: int = 3600,
    force: bool = False,
    custom_path: Optional[str] = None,
) -> bool:
    """
    Record a new timestamped price observation for an offer.
    
    Prevents duplicate observations when the same price is recorded repeatedly
    within deduplication_window_seconds, unless force is True or price has changed.
    
    Returns:
        True if the observation was persisted.
        False if skipped due to deduplication or invalid price.
    """
    if price is None or price <= 0:
        return False

    now_utc = datetime.now(timezone.utc)
    ts_str = recorded_at if recorded_at else now_utc.strftime("%Y-%m-%d %H:%M:%S")
    obs_dt = parse_timestamp(ts_str) or now_utc

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()

        # Verify offer exists
        cursor.execute("SELECT id, current_price, currency FROM offers WHERE id = ?", (offer_id,))
        offer_row = cursor.fetchone()
        if not offer_row:
            return False

        # Check last observation for deduplication
        cursor.execute(
            """
            SELECT price, recorded_at 
            FROM price_history 
            WHERE offer_id = ? 
            ORDER BY recorded_at DESC, id DESC 
            LIMIT 1
            """,
            (offer_id,),
        )
        last_obs = cursor.fetchone()

        if last_obs and not force:
            last_price = float(last_obs["price"])
            last_dt = parse_timestamp(last_obs["recorded_at"])

            # If identical price and within deduplication window, skip insertion
            if abs(last_price - price) < 1e-4 and last_dt:
                time_diff = abs((obs_dt - last_dt).total_seconds())
                if time_diff < deduplication_window_seconds:
                    return False

        # Insert new timestamped observation
        cursor.execute(
            """
            INSERT INTO price_history (offer_id, price, currency, data_source, data_status, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (offer_id, round(price, 2), currency, data_source, data_status, ts_str),
        )

        # Update offer current price and last_checked
        cursor.execute(
            """
            UPDATE offers 
            SET current_price = ?, last_checked = ? 
            WHERE id = ?
            """,
            (round(price, 2), ts_str, offer_id),
        )

        return True


def get_offer_price_history(
    offer_id: int,
    window_days: Optional[int] = None,
    reference_date: Optional[datetime] = None,
    custom_path: Optional[str] = None,
) -> list[PricePoint]:
    """
    Retrieve timestamped price observations for a specific offer.
    Supports filtering by window_days (e.g. 30, 90, or None for all-time).
    Observations with corrupt or unparseable timestamps are handled safely.
    """
    ref_dt = reference_date or datetime.now(timezone.utc)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, offer_id, price, currency, data_source, data_status, recorded_at
            FROM price_history
            WHERE offer_id = ?
            ORDER BY recorded_at ASC, id ASC
            """,
            (offer_id,),
        )
        rows = cursor.fetchall()

    points: list[PricePoint] = []
    for r in rows:
        pt_dt = parse_timestamp(r["recorded_at"])
        if not pt_dt:
            # Skip invalid timestamp if window filtering is requested
            if window_days is not None:
                continue
        elif window_days is not None:
            # Check window boundary
            cutoff = ref_dt - timedelta(days=window_days)
            if pt_dt < cutoff or pt_dt > ref_dt:
                continue

        points.append(
            PricePoint(
                id=r["id"],
                offer_id=r["offer_id"],
                price=float(r["price"]),
                recorded_at=str(r["recorded_at"]),
                currency=r["currency"] if "currency" in r.keys() else "USD",
                data_source=r["data_source"] if "data_source" in r.keys() else "demo_seed",
                data_status=r["data_status"] if "data_status" in r.keys() else "demo",
            )
        )

    return points


@dataclass
class ProductPriceHistorySummary:
    product_id: int
    variant_name: Optional[str]
    window_days: Optional[int]
    points: list[PricePoint]
    observation_count: int
    is_sufficient_history: bool
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    avg_price: Optional[float] = None
    currency: str = "INR"
    data_status: str = "demo"


def get_product_price_history(
    product_id: int,
    variant_name: Optional[str] = None,
    window_days: Optional[int] = None,
    reference_date: Optional[datetime] = None,
    custom_path: Optional[str] = None,
) -> ProductPriceHistorySummary:
    """
    Retrieve historical prices for a product and matching variant.
    
    Guarantees:
    - Different sizes, shades, and formulations remain separate when variant_name is specified.
    - Window filtering supports 7, 30, 90 days or all-time (window_days=None).
    - min_price, max_price, and avg_price are calculated ONLY when sufficient records exist (>= 2 points).
    - Returns is_sufficient_history=False and None metrics when records < 2 (honest empty state).
    - Avoids fabricating historical price points.
    """
    ref_dt = reference_date or datetime.now(timezone.utc)

    with get_connection(custom_path) as conn:
        cursor = conn.cursor()
        sql = """
            SELECT 
                ph.id, ph.offer_id, ph.price, ph.currency, ph.data_source, ph.data_status, ph.recorded_at,
                o.variant_name, s.name as store_name
            FROM price_history ph
            JOIN offers o ON ph.offer_id = o.id
            JOIN stores s ON o.store_id = s.id
            WHERE o.product_id = ?
        """
        params = [product_id]

        if variant_name and variant_name.strip() and variant_name.lower() != "all":
            sql += " AND LOWER(TRIM(o.variant_name)) = LOWER(TRIM(?))"
            params.append(variant_name)

        sql += " ORDER BY ph.recorded_at ASC, ph.id ASC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    points: list[PricePoint] = []
    currency = "INR"
    for r in rows:
        pt_dt = parse_timestamp(r["recorded_at"])
        if not pt_dt:
            if window_days is not None:
                continue
        elif window_days is not None:
            cutoff = ref_dt - timedelta(days=window_days)
            if pt_dt < cutoff or pt_dt > ref_dt:
                continue

        curr = r["currency"] if "currency" in r.keys() and r["currency"] else "USD"
        currency = curr
        points.append(
            PricePoint(
                id=r["id"],
                offer_id=r["offer_id"],
                price=float(r["price"]),
                recorded_at=str(r["recorded_at"]),
                currency=curr,
                data_source=r["data_source"] if "data_source" in r.keys() else "demo_seed",
                data_status=r["data_status"] if "data_status" in r.keys() else "demo",
            )
        )

    count = len(points)
    is_sufficient = (count >= 2)
    min_p = round(min(p.price for p in points), 2) if is_sufficient else None
    max_p = round(max(p.price for p in points), 2) if is_sufficient else None
    avg_p = round(sum(p.price for p in points) / count, 2) if is_sufficient else None

    return ProductPriceHistorySummary(
        product_id=product_id,
        variant_name=variant_name,
        window_days=window_days,
        points=points,
        observation_count=count,
        is_sufficient_history=is_sufficient,
        min_price=min_p,
        max_price=max_p,
        avg_price=avg_p,
        currency=currency,
        data_status="demo",
    )

