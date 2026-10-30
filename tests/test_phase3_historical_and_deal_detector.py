"""Phase 3 comprehensive tests for persistent historical price tracking,
deduplication, 30d/90d window filtering, Deal Scoring thresholds,
insufficient history handling, and suspicious discount analysis.
"""

from datetime import datetime, timezone, timedelta
import tempfile
import os
import pytest
from src.database.connection import init_db, migrate_db, get_connection
from src.database.seed import seed_database
from src.database.models import Offer, PricePoint, Product
from src.database.price_history_service import (
    record_price_observation,
    get_offer_price_history,
    parse_timestamp,
)
from src.analysis.deal_detector import (
    analyze_product_deal,
    calculate_deal_score,
    filter_observations_by_window,
    calculate_price_trend,
    analyze_suspicious_discount,
    DealAnalysis,
)


@pytest.fixture(scope="module")
def p3_test_db():
    """Temporary seeded database for Phase 3 tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


# =====================================================================
# 1. Persistent Price Observations & Deduplication
# =====================================================================

def test_record_new_price_observation_persists(p3_test_db):
    # Offer 1: record a price change
    success = record_price_observation(
        offer_id=1,
        price=1750.00,
        currency="USD",
        data_source="manual_test",
        data_status="demo",
        custom_path=p3_test_db,
    )
    assert success is True

    # Verify persisted in database
    with get_connection(p3_test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT price, currency, data_source FROM price_history WHERE offer_id = 1 ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        assert row is not None
        assert row["price"] == 1750.00
        assert row["currency"] == "USD"
        assert row["data_source"] == "manual_test"


def test_deduplication_prevents_duplicate_observations(p3_test_db):
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Record first observation
    first = record_price_observation(
        offer_id=2,
        price=1849.00,
        recorded_at=now_ts,
        deduplication_window_seconds=3600,
        force=False,
        custom_path=p3_test_db,
    )

    # Immediately attempt duplicate observation with identical price
    duplicate = record_price_observation(
        offer_id=2,
        price=1849.00,
        recorded_at=now_ts,
        deduplication_window_seconds=3600,
        force=False,
        custom_path=p3_test_db,
    )
    assert duplicate is False  # Correctly deduplicated!

    # But forcing it records the observation
    forced = record_price_observation(
        offer_id=2,
        price=1849.00,
        recorded_at=now_ts,
        force=True,
        custom_path=p3_test_db,
    )
    assert forced is True


def test_record_price_observation_rejects_non_positive_price(p3_test_db):
    assert record_price_observation(offer_id=1, price=0.0, custom_path=p3_test_db) is False
    assert record_price_observation(offer_id=1, price=-25.0, custom_path=p3_test_db) is False


# =====================================================================
# 2. Historical Window Filtering (30-day, 90-day, All-time)
# =====================================================================

def test_filter_observations_by_window_using_real_timestamps():
    ref_date = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    points = [
        PricePoint(price=100.0, recorded_at="2026-10-25 10:00:00"),  # 5 days ago (in 30d, in 90d)
        PricePoint(price=110.0, recorded_at="2026-10-10 10:00:00"),  # 20 days ago (in 30d, in 90d)
        PricePoint(price=120.0, recorded_at="2026-09-15 10:00:00"),  # 45 days ago (outside 30d, in 90d)
        PricePoint(price=130.0, recorded_at="2026-07-01 10:00:00"),  # 121 days ago (outside 30d and 90d)
    ]

    in_30d = filter_observations_by_window(points, window="30d", reference_date=ref_date)
    assert len(in_30d) == 2
    assert [p.price for p in in_30d] == [100.0, 110.0]

    in_90d = filter_observations_by_window(points, window="90d", reference_date=ref_date)
    assert len(in_90d) == 3
    assert [p.price for p in in_90d] == [100.0, 110.0, 120.0]

    in_all = filter_observations_by_window(points, window="all", reference_date=ref_date)
    assert len(in_all) == 4


def test_window_filtering_handles_invalid_timestamps():
    points = [
        PricePoint(price=100.0, recorded_at="NotADate"),
        PricePoint(price=105.0, recorded_at="2026-10-25 10:00:00"),
    ]
    ref_date = datetime(2026, 10, 30, tzinfo=timezone.utc)
    filtered = filter_observations_by_window(points, window="30d", reference_date=ref_date)
    assert len(filtered) == 1
    assert filtered[0].price == 105.0


# =====================================================================
# 3. Deal Score Thresholds & Insufficient History
# =====================================================================

def test_deal_score_threshold_tiers():
    # 80-100: Excellent Deal
    excellent_score = calculate_deal_score(current_price=100.0, hist_min=100.0, hist_max=200.0, hist_avg=150.0, is_fake_discount=False)
    assert excellent_score >= 80

    # 65-79: Good Deal
    good_score = calculate_deal_score(current_price=130.0, hist_min=100.0, hist_max=200.0, hist_avg=155.0, is_fake_discount=False)
    assert 65 <= good_score <= 79

    # 45-64: Fair Price
    fair_score = calculate_deal_score(current_price=150.0, hist_min=100.0, hist_max=200.0, hist_avg=150.0, is_fake_discount=False)
    assert 45 <= fair_score <= 64

    # 0-44: Poor Deal
    poor_score = calculate_deal_score(current_price=195.0, hist_min=100.0, hist_max=200.0, hist_avg=150.0, is_fake_discount=False)
    assert poor_score < 45


def test_insufficient_history_withholds_score():
    # Only 1 observation recorded -> insufficient history
    ref_dt = datetime(2026, 10, 30, tzinfo=timezone.utc)
    offer = Offer(
        id=1, product_id=1, store_id=1, store_name="Store 1", store_rating=4.5,
        current_price=500.0,
        price_history=[PricePoint(price=500.0, recorded_at="2026-10-30 10:00:00")]
    )
    product = Product(id=1, sku="SKU-INSUF", title="New Arrival", brand="BrandA", category="Tech", description="", offers=[offer])

    analysis = analyze_product_deal(product, reference_date=ref_dt)
    assert analysis is not None
    assert analysis.is_sufficient_history is False
    # Score MUST be withheld as None, NOT 0
    assert analysis.deal_score is None
    assert analysis.verdict == "INSUFFICIENT HISTORY"
    assert "insufficient" in analysis.explanation.lower()
    assert analysis.missing_evidence_reason is not None


def test_sufficient_history_calculates_metrics():
    # 5 observations spanning 60 days
    ref_dt = datetime(2026, 10, 30, tzinfo=timezone.utc)
    offer = Offer(
        id=1, product_id=2, store_id=1, store_name="Store 1", store_rating=4.5,
        current_price=80.0,
        price_history=[
            PricePoint(price=100.0, recorded_at="2026-09-01 10:00:00"),
            PricePoint(price=95.0, recorded_at="2026-09-15 10:00:00"),
            PricePoint(price=90.0, recorded_at="2026-10-01 10:00:00"),
            PricePoint(price=85.0, recorded_at="2026-10-15 10:00:00"),
            PricePoint(price=80.0, recorded_at="2026-10-29 10:00:00"),
        ]
    )
    product = Product(id=2, sku="SKU-SUFF", title="Seasoned Product", brand="BrandB", category="Audio", description="", offers=[offer])

    analysis = analyze_product_deal(product, reference_date=ref_dt)
    assert analysis is not None
    assert analysis.is_sufficient_history is True
    assert analysis.deal_score is not None
    assert analysis.historical_min == 80.0
    assert analysis.historical_max == 100.0
    assert analysis.historical_avg == 90.0
    assert analysis.is_all_time_low is True
    assert analysis.price_trend == "Falling (Price Dropping)"


# =====================================================================
# 4. Suspicious Discount Analysis
# =====================================================================

def test_suspicious_discount_when_promotional_price_exceeds_average():
    # Retailer advertises "Was $599, Now $499", but historical average was $420!
    offer = Offer(
        id=1, product_id=3, store_id=1, store_name="Store X", store_rating=4.0,
        current_price=490.0, original_price=599.0
    )
    observations = [
        PricePoint(price=400.0, recorded_at="2026-09-01"),
        PricePoint(price=420.0, recorded_at="2026-09-15"),
        PricePoint(price=440.0, recorded_at="2026-10-01"),
    ]
    alert = analyze_suspicious_discount(offer, historical_avg=420.0, historical_max=440.0, observations=observations)

    assert alert.has_warning is True
    assert alert.warning_level == "caution"
    assert "Promotional Price Exceeds Historical Average" in alert.headline
    assert "Recorded average across 3 observations is $420.00" in alert.historical_evidence


def test_suspicious_discount_when_reference_price_is_unverified():
    # Retailer claims original price of $999 on an item whose historical max was only $500
    offer = Offer(
        id=1, product_id=4, store_id=1, store_name="Store Y", store_rating=4.0,
        current_price=450.0, original_price=999.0
    )
    alert = analyze_suspicious_discount(offer, historical_avg=450.0, historical_max=500.0, observations=[])

    assert alert.has_warning is True
    assert alert.warning_level == "notice"
    assert "Unverified Reference Price" in alert.headline


def test_no_suspicious_discount_on_genuine_bargain():
    # Regular MSRP $200, normal avg $180, on real sale for $140
    offer = Offer(
        id=1, product_id=5, store_id=1, store_name="Store Z", store_rating=4.5,
        current_price=140.0, original_price=200.0
    )
    alert = analyze_suspicious_discount(offer, historical_avg=180.0, historical_max=200.0, observations=[])
    assert alert.has_warning is False


# =====================================================================
# 5. Variant and Currency Isolation
# =====================================================================

def test_variant_and_currency_isolation():
    # Offer 1: USD currency with historical points
    # Offer 2: EUR currency with historical points (should not be mixed into USD calculations)
    offer_usd = Offer(
        id=1, product_id=6, store_id=1, store_name="Store US", store_rating=4.5,
        current_price=100.0, currency="USD",
        price_history=[
            PricePoint(price=120.0, recorded_at="2026-09-01", currency="USD"),
            PricePoint(price=110.0, recorded_at="2026-09-15", currency="USD"),
            PricePoint(price=100.0, recorded_at="2026-10-01", currency="USD"),
        ]
    )
    offer_eur = Offer(
        id=2, product_id=6, store_id=2, store_name="Store EU", store_rating=4.5,
        current_price=150.0, currency="EUR",
        price_history=[
            PricePoint(price=180.0, recorded_at="2026-09-01", currency="EUR"),
            PricePoint(price=160.0, recorded_at="2026-09-15", currency="EUR"),
            PricePoint(price=150.0, recorded_at="2026-10-01", currency="EUR"),
        ]
    )
    product = Product(id=6, sku="SKU-CURR", title="Global Gadget", brand="BrandG", category="Tech", description="", offers=[offer_usd, offer_eur])

    analysis = analyze_product_deal(product)
    assert analysis is not None
    # Best offer chosen is USD ($100 < 150)
    assert analysis.best_offer.currency == "USD"
    # Historical calculations must only include USD observations (100, 110, 120 -> avg 110.0), NOT EUR points
    assert analysis.historical_avg == 110.0
    assert analysis.historical_max == 120.0
