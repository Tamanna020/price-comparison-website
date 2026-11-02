"""Phase 4 Comprehensive Test Suite: Complete Real Deal Detector.

Tests cover all 12 key functional and explainability requirements:
1. Historical average calculation
2. Historical minimum and maximum
3. 30-day and 90-day filtering
4. Excellent deal classification (score 80-100)
5. Good deal classification (score 65-79)
6. Fair price classification (score 45-64)
7. Poor deal classification (score 0-44)
8. Insufficient historical data handling (score withheld, INSUFFICIENT DATA displayed)
9. Invalid and missing prices handling
10. Suspicious advertised discount detection
11. Incorrect product variant matching (variant isolation)
12. Database persistence and retrieval
"""

from datetime import datetime, timezone, timedelta
import tempfile
import os
import pytest

from src.database.connection import get_connection
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
    get_deal_classification,
    filter_observations_by_window,
    calculate_price_trend,
    analyze_suspicious_discount,
    DealAnalysis,
    DealVerdict,
    SCORE_THRESHOLD_EXCELLENT,
    SCORE_THRESHOLD_GOOD,
    SCORE_THRESHOLD_FAIR,
)


@pytest.fixture(scope="module")
def p4_test_db():
    """Temporary seeded database for Phase 4 tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


# =====================================================================
# 1. Historical Average Calculation
# =====================================================================

def test_p4_01_historical_average_calculation():
    """Verify historical average, recent 7-day average, and differences from average."""
    ref_dt = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    
    # 5 observations spanning 40 days:
    # 40d ago: $140
    # 30d ago: $130
    # 20d ago: $120
    # 5d ago: $110 (within 7d)
    # 1d ago: $100 (within 7d)
    # Mean of all 5: (140 + 130 + 120 + 110 + 100) / 5 = 120.0
    # Recent 7-day mean: (110 + 100) / 2 = 105.0
    offer = Offer(
        id=1, product_id=1, store_id=1, store_name="Store Alpha", store_rating=4.8,
        current_price=100.0,
        price_history=[
            PricePoint(price=140.0, recorded_at="2026-09-20 10:00:00"),
            PricePoint(price=130.0, recorded_at="2026-09-30 10:00:00"),
            PricePoint(price=120.0, recorded_at="2026-10-10 10:00:00"),
            PricePoint(price=110.0, recorded_at="2026-10-25 10:00:00"),
            PricePoint(price=100.0, recorded_at="2026-10-29 10:00:00"),
        ]
    )
    product = Product(id=1, sku="SKU-AVG-1", title="Product Avg Test", brand="BrandA", category="Tech", description="", offers=[offer])

    analysis = analyze_product_deal(product, reference_date=ref_dt)
    assert analysis is not None
    assert analysis.historical_avg == 120.0
    assert analysis.recent_avg == 105.0
    # diff_from_avg = current_best_price - hist_avg = 100 - 120 = -20.0
    assert analysis.diff_from_avg == -20.0
    # pct_diff_from_avg = ((hist_avg - current) / hist_avg) * 100 = (20 / 120) * 100 = 16.7%
    assert analysis.pct_diff_from_avg == 16.7


# =====================================================================
# 2. Historical Minimum and Maximum Calculation
# =====================================================================

def test_p4_02_historical_minimum_and_maximum():
    """Verify historical minimum, maximum, and percentage difference from minimum."""
    ref_dt = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    
    # Prices: 100, 150, 200, 250 -> Min = 100, Max = 250
    # Current best price = 120 -> pct_diff_from_min = ((120 - 100) / 100) * 100 = 20.0%
    offer = Offer(
        id=2, product_id=2, store_id=1, store_name="Store Beta", store_rating=4.5,
        current_price=120.0,
        price_history=[
            PricePoint(price=250.0, recorded_at="2026-09-01 10:00:00"),
            PricePoint(price=200.0, recorded_at="2026-09-15 10:00:00"),
            PricePoint(price=150.0, recorded_at="2026-10-01 10:00:00"),
            PricePoint(price=100.0, recorded_at="2026-10-15 10:00:00"),
        ]
    )
    product = Product(id=2, sku="SKU-MINMAX", title="MinMax Test", brand="BrandB", category="Audio", description="", offers=[offer])

    analysis = analyze_product_deal(product, reference_date=ref_dt)
    assert analysis is not None
    assert analysis.historical_min == 100.0
    assert analysis.historical_max == 250.0
    assert analysis.pct_diff_from_min == 20.0
    assert analysis.is_all_time_low is False

    # When current price matches min
    offer.current_price = 100.0
    analysis_low = analyze_product_deal(product, reference_date=ref_dt)
    assert analysis_low.pct_diff_from_min == 0.0
    assert analysis_low.is_all_time_low is True


# =====================================================================
# 3. 30-Day and 90-Day Time Window Filtering
# =====================================================================

def test_p4_03_time_window_filtering_30d_and_90d():
    """Verify 30d, 90d, and all-time window filtering recalculates metrics accurately."""
    ref_dt = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    
    # 4 observations:
    # 10 days ago (2026-10-20): $100 -> in 30d, in 90d, in all
    # 25 days ago (2026-10-05): $110 -> in 30d, in 90d, in all
    # 60 days ago (2026-08-31): $140 -> OUTSIDE 30d, in 90d, in all
    # 120 days ago (2026-07-02): $180 -> OUTSIDE 30d, OUTSIDE 90d, in all
    points = [
        PricePoint(price=100.0, recorded_at="2026-10-20 10:00:00"),
        PricePoint(price=110.0, recorded_at="2026-10-05 10:00:00"),
        PricePoint(price=140.0, recorded_at="2026-08-31 10:00:00"),
        PricePoint(price=180.0, recorded_at="2026-07-02 10:00:00"),
    ]

    p_30d = filter_observations_by_window(points, window="30d", reference_date=ref_dt)
    p_90d = filter_observations_by_window(points, window="90d", reference_date=ref_dt)
    p_all = filter_observations_by_window(points, window="all", reference_date=ref_dt)

    assert len(p_30d) == 2
    assert [p.price for p in p_30d] == [100.0, 110.0]

    assert len(p_90d) == 3
    assert [p.price for p in p_90d] == [100.0, 110.0, 140.0]

    assert len(p_all) == 4
    assert [p.price for p in p_all] == [100.0, 110.0, 140.0, 180.0]

    # Verify analyze_product_deal adapts to the window parameter
    offer = Offer(
        id=3, product_id=3, store_id=1, store_name="Store Gamma", store_rating=4.5,
        current_price=100.0, price_history=points,
    )
    prod = Product(id=3, sku="SKU-WIN", title="Window Product", brand="BrandC", category="Tech", description="", offers=[offer])

    # In 90d window, max was $140 (180 was 120 days ago)
    analysis_90d = analyze_product_deal(prod, window="90d", reference_date=ref_dt)
    assert analysis_90d.historical_max == 140.0
    assert analysis_90d.total_data_points == 3

    # In all-time window, max was $180
    analysis_all = analyze_product_deal(prod, window="all", reference_date=ref_dt)
    assert analysis_all.historical_max == 180.0
    assert analysis_all.total_data_points == 4


# =====================================================================
# 4. Excellent Deal Classification (80–100)
# =====================================================================

def test_p4_04_excellent_deal_classification():
    """Verify deal scores from 80-100 classify as EXCELLENT DEAL and mark is_good_value=True."""
    score = calculate_deal_score(current_price=100.0, hist_min=100.0, hist_max=200.0, hist_avg=150.0)
    assert score >= 80
    classification = get_deal_classification(score)
    assert classification == "EXCELLENT DEAL"

    # End-to-end analysis check
    ref_dt = datetime(2026, 10, 30, tzinfo=timezone.utc)
    offer = Offer(
        id=4, product_id=4, store_id=1, store_name="Store Deal", store_rating=4.7,
        current_price=100.0,
        price_history=[
            PricePoint(price=180.0, recorded_at="2026-09-01 10:00:00"),
            PricePoint(price=160.0, recorded_at="2026-09-15 10:00:00"),
            PricePoint(price=140.0, recorded_at="2026-10-01 10:00:00"),
            PricePoint(price=100.0, recorded_at="2026-10-25 10:00:00"),
        ]
    )
    product = Product(id=4, sku="SKU-EXC", title="Excellent Bargain", brand="BrandD", category="Tech", description="", offers=[offer])
    analysis = analyze_product_deal(product, reference_date=ref_dt)
    
    assert analysis.deal_score >= 80
    assert analysis.deal_classification == "EXCELLENT DEAL"
    assert analysis.verdict == "EXCELLENT DEAL"
    assert analysis.is_good_value is True


# =====================================================================
# 5. Good Deal Classification (65–79)
# =====================================================================

def test_p4_05_good_deal_classification():
    """Verify deal scores from 65-79 classify as GOOD DEAL and mark is_good_value=True."""
    score = calculate_deal_score(current_price=135.0, hist_min=100.0, hist_max=200.0, hist_avg=150.0)
    assert 65 <= score <= 79
    classification = get_deal_classification(score)
    assert classification == "GOOD DEAL"

    ref_dt = datetime(2026, 10, 30, tzinfo=timezone.utc)
    offer = Offer(
        id=5, product_id=5, store_id=1, store_name="Store Good", store_rating=4.5,
        current_price=145.0,
        price_history=[
            PricePoint(price=200.0, recorded_at="2026-09-01 10:00:00"),
            PricePoint(price=180.0, recorded_at="2026-09-15 10:00:00"),
            PricePoint(price=160.0, recorded_at="2026-10-01 10:00:00"),
            PricePoint(price=150.0, recorded_at="2026-10-15 10:00:00"),
            PricePoint(price=120.0, recorded_at="2026-10-28 10:00:00"),
        ]
    )
    product = Product(id=5, sku="SKU-GOOD", title="Good Price Item", brand="BrandE", category="Tech", description="", offers=[offer])
    analysis = analyze_product_deal(product, reference_date=ref_dt)

    assert 65 <= analysis.deal_score <= 79
    assert analysis.deal_classification == "GOOD DEAL"
    assert analysis.verdict == "GOOD DEAL"
    assert analysis.is_good_value is True


# =====================================================================
# 6. Fair Price Classification (45–64)
# =====================================================================

def test_p4_06_fair_price_classification():
    """Verify deal scores from 45-64 classify as FAIR PRICE and mark is_good_value=False."""
    score = calculate_deal_score(current_price=150.0, hist_min=100.0, hist_max=200.0, hist_avg=150.0)
    assert 45 <= score <= 64
    classification = get_deal_classification(score)
    assert classification == "FAIR PRICE"

    ref_dt = datetime(2026, 10, 30, tzinfo=timezone.utc)
    offer = Offer(
        id=6, product_id=6, store_id=1, store_name="Store Fair", store_rating=4.2,
        current_price=150.0,
        price_history=[
            PricePoint(price=180.0, recorded_at="2026-09-01 10:00:00"),
            PricePoint(price=160.0, recorded_at="2026-09-15 10:00:00"),
            PricePoint(price=150.0, recorded_at="2026-10-01 10:00:00"),
            PricePoint(price=140.0, recorded_at="2026-10-15 10:00:00"),
            PricePoint(price=120.0, recorded_at="2026-10-25 10:00:00"),
        ]
    )
    product = Product(id=6, sku="SKU-FAIR", title="Fair Price Item", brand="BrandF", category="Home", description="", offers=[offer])
    analysis = analyze_product_deal(product, reference_date=ref_dt)

    assert 45 <= analysis.deal_score <= 64
    assert analysis.deal_classification == "FAIR PRICE"
    assert analysis.verdict == "FAIR PRICE"
    assert analysis.is_good_value is False


# =====================================================================
# 7. Poor Deal Classification (0–44)
# =====================================================================

def test_p4_07_poor_deal_classification():
    """Verify deal scores from 0-44 classify as POOR DEAL and mark is_good_value=False."""
    score = calculate_deal_score(current_price=195.0, hist_min=100.0, hist_max=200.0, hist_avg=140.0)
    assert score <= 44
    classification = get_deal_classification(score)
    assert classification == "POOR DEAL"

    ref_dt = datetime(2026, 10, 30, tzinfo=timezone.utc)
    offer = Offer(
        id=7, product_id=7, store_id=1, store_name="Store High", store_rating=4.0,
        current_price=195.0,
        price_history=[
            PricePoint(price=140.0, recorded_at="2026-09-01 10:00:00"),
            PricePoint(price=145.0, recorded_at="2026-09-15 10:00:00"),
            PricePoint(price=150.0, recorded_at="2026-10-01 10:00:00"),
            PricePoint(price=195.0, recorded_at="2026-10-25 10:00:00"),
        ]
    )
    product = Product(id=7, sku="SKU-POOR", title="Overpriced Item", brand="BrandG", category="Tech", description="", offers=[offer])
    analysis = analyze_product_deal(product, reference_date=ref_dt)

    assert analysis.deal_score <= 44
    assert analysis.deal_classification == "POOR DEAL"
    assert analysis.verdict == "POOR DEAL"
    assert analysis.is_good_value is False


# =====================================================================
# 8. Insufficient Historical Data Handling
# =====================================================================

def test_p4_08_insufficient_historical_data_handling():
    """Verify score is withheld (None) and INSUFFICIENT DATA is displayed when history is scarce."""
    ref_dt = datetime(2026, 10, 30, tzinfo=timezone.utc)
    
    # Case A: Only 1 observation -> Not enough observations
    offer_one_point = Offer(
        id=8, product_id=8, store_id=1, store_name="Store New", store_rating=4.0,
        current_price=299.0,
        price_history=[PricePoint(price=299.0, recorded_at="2026-10-29 10:00:00")]
    )
    prod_one = Product(id=8, sku="SKU-INSUF1", title="New Launch", brand="BrandH", category="Tech", description="", offers=[offer_one_point])
    analysis_one = analyze_product_deal(prod_one, reference_date=ref_dt)

    assert analysis_one.is_sufficient_history is False
    assert analysis_one.is_sufficient_data is False
    assert analysis_one.deal_score is None  # Score must be None, NOT 0 or fabricated
    assert analysis_one.deal_classification == "INSUFFICIENT DATA"
    assert analysis_one.verdict == "INSUFFICIENT DATA"
    assert "insufficient" in analysis_one.explanation.lower()
    assert analysis_one.missing_evidence_reason is not None

    # Case B: 3 observations but all taken on the same day (0 days span)
    offer_same_day = Offer(
        id=9, product_id=9, store_id=1, store_name="Store Burst", store_rating=4.0,
        current_price=100.0,
        price_history=[
            PricePoint(price=100.0, recorded_at="2026-10-30 08:00:00"),
            PricePoint(price=102.0, recorded_at="2026-10-30 10:00:00"),
            PricePoint(price=100.0, recorded_at="2026-10-30 12:00:00"),
        ]
    )
    prod_burst = Product(id=9, sku="SKU-INSUF2", title="Burst Product", brand="BrandH", category="Tech", description="", offers=[offer_same_day])
    analysis_burst = analyze_product_deal(prod_burst, reference_date=ref_dt)
    assert analysis_burst.is_sufficient_data is False
    assert analysis_burst.deal_score is None


# =====================================================================
# 9. Invalid and Missing Prices Handling
# =====================================================================

def test_p4_09_invalid_and_missing_prices():
    """Verify system safely rejects non-positive, zero, or missing prices."""
    # Price recording rejects invalid prices
    assert record_price_observation(offer_id=1, price=0.0) is False
    assert record_price_observation(offer_id=1, price=-45.0) is False

    # Window filtering discards zero and negative prices
    raw_points = [
        PricePoint(price=0.0, recorded_at="2026-10-25 10:00:00"),
        PricePoint(price=-10.0, recorded_at="2026-10-26 10:00:00"),
        PricePoint(price=99.0, recorded_at="2026-10-27 10:00:00"),
    ]
    cleaned = filter_observations_by_window(raw_points, window="all")
    assert len(cleaned) == 1
    assert cleaned[0].price == 99.0

    # analyze_product_deal returns None if all offers have invalid price
    offer_zero = Offer(id=10, product_id=10, store_id=1, store_name="Broken Store", store_rating=3.0, current_price=0.0)
    prod_broken = Product(id=10, sku="SKU-ZERO", title="Invalid Price", brand="BrandZ", category="Tech", description="", offers=[offer_zero])
    analysis_invalid = analyze_product_deal(prod_broken)
    assert analysis_invalid is None


# =====================================================================
# 10. Suspicious Advertised Discount Detection
# =====================================================================

def test_p4_10_suspicious_advertised_discounts():
    """Verify transparent detection of misleading sales and exaggerated reference MSRPs."""
    # Scenario A: Promotional price higher than historical average
    offer_fake_sale = Offer(
        id=11, product_id=11, store_id=1, store_name="Hype Store", store_rating=3.5,
        current_price=220.0, original_price=280.0
    )
    obs = [
        PricePoint(price=180.0, recorded_at="2026-09-01"),
        PricePoint(price=190.0, recorded_at="2026-09-15"),
        PricePoint(price=185.0, recorded_at="2026-10-01"),
    ]
    # Historical average is ~185.0, but advertised 'sale' price is 220.0!
    alert_sale = analyze_suspicious_discount(offer_fake_sale, historical_avg=185.0, historical_max=200.0, observations=obs)
    assert alert_sale.has_warning is True
    assert alert_sale.warning_level == "caution"
    assert "Promotional Price Exceeds Historical Average" in alert_sale.headline
    assert "185.00" in alert_sale.historical_evidence

    # Scenario B: Exaggerated unverified reference price
    offer_inflated_msrp = Offer(
        id=12, product_id=12, store_id=2, store_name="Store Inflate", store_rating=3.8,
        current_price=100.0, original_price=350.0  # Claims $350 was-price when max was only $150
    )
    alert_msrp = analyze_suspicious_discount(offer_inflated_msrp, historical_avg=110.0, historical_max=150.0, observations=[])
    assert alert_msrp.has_warning is True
    assert alert_msrp.warning_level == "notice"
    assert "Unverified Reference Price" in alert_msrp.headline

    # Scenario C: Clean, genuine discount produces no warning
    offer_genuine = Offer(
        id=13, product_id=13, store_id=3, store_name="Honest Store", store_rating=4.9,
        current_price=80.0, original_price=120.0
    )
    alert_clean = analyze_suspicious_discount(offer_genuine, historical_avg=110.0, historical_max=125.0, observations=[])
    assert alert_clean.has_warning is False


# =====================================================================
# 11. Variant Matching and Isolation
# =====================================================================

def test_p4_11_variant_matching_and_isolation():
    """Verify offers with distinct variant specs are not combined into target historical calculations."""
    # Target offer: 128GB model at $600 with historical points
    offer_128 = Offer(
        id=14, product_id=14, store_id=1, store_name="Store Tech", store_rating=4.5,
        variant_name="128GB",
        current_price=600.0,
        price_history=[
            PricePoint(price=650.0, recorded_at="2026-09-01"),
            PricePoint(price=620.0, recorded_at="2026-09-15"),
            PricePoint(price=600.0, recorded_at="2026-10-01"),
        ]
    )
    # Different variant offer: 512GB model at $900 with historical points
    offer_512 = Offer(
        id=15, product_id=14, store_id=2, store_name="Store HighEnd", store_rating=4.5,
        variant_name="512GB",
        current_price=900.0,
        price_history=[
            PricePoint(price=1000.0, recorded_at="2026-09-01"),
            PricePoint(price=950.0, recorded_at="2026-09-15"),
            PricePoint(price=900.0, recorded_at="2026-10-01"),
        ]
    )
    product = Product(
        id=14, sku="SKU-VAR-ISO", title="Smartphone Pro", brand="BrandPhone", category="Tech", description="",
        offers=[offer_128, offer_512]
    )

    analysis_128 = analyze_product_deal(product, target_offer=offer_128)
    assert analysis_128 is not None
    assert analysis_128.best_offer.variant_name == "128GB"
    # Historical calculations must only include the 128GB observations (650, 620, 600 -> avg 623.33)
    # Must NOT include the 512GB prices (900-1000)
    assert analysis_128.historical_avg == round((650 + 620 + 600) / 3, 2)
    assert analysis_128.historical_max == 650.0


# =====================================================================
# 12. Database Persistence and Retrieval
# =====================================================================

def test_p4_12_database_persistence_and_retrieval(p4_test_db):
    """Verify price observations persist to SQLite schema and can be retrieved accurately."""
    test_offer_id = 3
    test_price = 1499.99
    # Use a future timestamp beyond seed data so it is guaranteed to be the latest observation
    base_dt = datetime.now(timezone.utc) + timedelta(days=1)
    now_ts = base_dt.strftime("%Y-%m-%d %H:%M:%S")
    fifteen_min_later = (base_dt + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")

    # 1. Record observation
    persisted = record_price_observation(
        offer_id=test_offer_id,
        price=test_price,
        currency="USD",
        data_source="automated_test",
        data_status="demo",
        recorded_at=now_ts,
        force=True,
        custom_path=p4_test_db,
    )
    assert persisted is True

    # 2. Retrieve history for offer
    history = get_offer_price_history(test_offer_id, custom_path=p4_test_db)
    assert len(history) > 0
    
    # Check our newly recorded point exists and matches
    matching = [p for p in history if p.data_source == "automated_test" and p.price == test_price]
    assert len(matching) == 1
    pt = matching[0]
    assert pt.price == test_price
    assert pt.currency == "USD"
    assert pt.data_source == "automated_test"
    assert pt.data_status == "demo"
    assert pt.recorded_at == now_ts

    # 3. Verify deduplication window
    dedup_result = record_price_observation(
        offer_id=test_offer_id,
        price=test_price,
        currency="USD",
        data_source="automated_test",
        data_status="demo",
        recorded_at=fifteen_min_later,  # 15 minutes later with same price
        deduplication_window_seconds=3600,
        force=False,
        custom_path=p4_test_db,
    )
    assert dedup_result is False  # Correctly rejected as duplicate!
