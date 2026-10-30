"""Tests for Real Deal Detector intelligence logic."""

import pytest
from src.analysis.deal_detector import analyze_product_deal, calculate_deal_score
from src.database.models import Offer, PricePoint, Product


def test_calculate_deal_score_extremes():
    # When current price is at historical minimum
    score_min = calculate_deal_score(current_price=100.0, hist_min=100.0, hist_max=200.0, hist_avg=150.0, is_fake_discount=False)
    assert score_min >= 95

    # When current price is at historical maximum
    score_max = calculate_deal_score(current_price=200.0, hist_min=100.0, hist_max=200.0, hist_avg=150.0, is_fake_discount=False)
    assert score_max <= 10

    # When current price is historical average
    score_avg = calculate_deal_score(current_price=150.0, hist_min=100.0, hist_max=200.0, hist_avg=150.0, is_fake_discount=False)
    assert 40 <= score_avg <= 60


def test_deal_detector_all_time_low():
    # Offer current price matches historical min
    offer1 = Offer(
        id=1, product_id=1, store_id=1, store_name="Store A", store_rating=4.5,
        current_price=299.0, original_price=399.0, shipping_cost=0.0,
        price_history=[
            PricePoint(price=399.0, recorded_at="2026-09-01"),
            PricePoint(price=349.0, recorded_at="2026-09-15"),
            PricePoint(price=299.0, recorded_at="2026-10-01"),
        ]
    )
    product = Product(
        id=1, sku="TEST-SKU-1", title="Test Product Low", brand="BrandX",
        category="Audio", description="A test product", offers=[offer1]
    )

    analysis = analyze_product_deal(product)
    assert analysis is not None
    assert analysis.is_all_time_low is True
    assert analysis.verdict == "ALL-TIME LOW"
    assert analysis.recommendation == "BUY NOW"
    assert analysis.historical_min == 299.0


def test_deal_detector_fake_discount():
    # Retailer sets original_price to 499.0, current_price to 399.0,
    # but historical average was 350.0! (price is actually inflated above historical norm)
    offer = Offer(
        id=1, product_id=2, store_id=1, store_name="Store B", store_rating=4.0,
        current_price=390.0, original_price=499.0, shipping_cost=0.0,
        price_history=[
            PricePoint(price=320.0, recorded_at="2026-09-01"),
            PricePoint(price=330.0, recorded_at="2026-09-15"),
            PricePoint(price=340.0, recorded_at="2026-10-01"),
        ]
    )
    product = Product(
        id=2, sku="TEST-SKU-2", title="Test Product Fake Discount", brand="BrandY",
        category="Tech", description="Fake discount test", offers=[offer]
    )

    analysis = analyze_product_deal(product)
    assert analysis is not None
    assert analysis.is_fake_discount_risk is True
    assert analysis.verdict == "MISLEADING DISCOUNT"
    assert analysis.recommendation == "WAIT"


def test_deal_detector_empty_offers():
    product = Product(
        id=3, sku="TEST-SKU-EMPTY", title="Empty", brand="None",
        category="None", description="No offers", offers=[]
    )
    analysis = analyze_product_deal(product)
    assert analysis is None

