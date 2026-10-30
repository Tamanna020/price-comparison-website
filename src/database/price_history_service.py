"""Persistent price history tracking service.
Handles timestamped price observations, deduplication intervals,
time-window filtering (30-day, 90-day, all-time), and safe updates.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from src.database.connection import get_connection
from src.database.models import PricePoint


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse various datetime string formats into UTC-aware datetime."""
    if not ts_str:
        return None
    # Strip trailing whitespace or Z
    clean_ts = ts_str.strip()
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

