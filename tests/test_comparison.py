"""Tests for multi-store price comparison and lowest-price calculations."""

import pytest
from src.database.models import Offer, Product
from src.services.comparison_service import generate_comparison_summary


def test_lowest_price_calculation():
    offers = [
        Offer(id=1, product_id=10, store_id=1, store_name="Store A", store_rating=4.2, current_price=199.99, original_price=220.0),
        Offer(id=2, product_id=10, store_id=2, store_name="Store B", store_rating=4.8, current_price=179.99, original_price=220.0),
        Offer(id=3, product_id=10, store_id=3, store_name="Store C", store_rating=4.5, current_price=189.99, original_price=220.0),
    ]
    product = Product(
        id=10, sku="COMP-1", title="Compare Item", brand="BrandC",
        category="Tech", description="", offers=offers
    )

    assert product.lowest_price == 179.99
    assert product.highest_price == 199.99
    assert product.offer_count == 3


def test_total_cost_with_shipping():
    # Store A has lower item price ($150) but $20 shipping => $170 total
    # Store B has higher item price ($155) with free shipping => $155 total
    offers = [
        Offer(id=1, product_id=11, store_id=1, store_name="Store A", store_rating=4.0, current_price=150.0, original_price=180.0, shipping_cost=20.0),
        Offer(id=2, product_id=11, store_id=2, store_name="Store B", store_rating=4.5, current_price=155.0, original_price=180.0, shipping_cost=0.0),
    ]
    product = Product(
        id=11, sku="COMP-2", title="Shipping Item", brand="BrandS",
        category="Tech", description="", offers=offers
    )

    summary = generate_comparison_summary(product)
    assert summary is not None
    # Best offer overall considers total cost (price + shipping)
    assert summary.lowest_total_cost == 155.0
    assert summary.cheapest_store_name == "Store B"
    assert summary.ranked_offers[0].store_name == "Store B"
    assert summary.ranked_offers[1].store_name == "Store A"


def test_comparison_summary_spread_and_savings():
    offers = [
        Offer(id=1, product_id=12, store_id=1, store_name="Store High", store_rating=4.0, current_price=500.0, original_price=500.0),
        Offer(id=2, product_id=12, store_id=2, store_name="Store Low", store_rating=4.5, current_price=400.0, original_price=500.0),
    ]
    product = Product(
        id=12, sku="COMP-3", title="Spread Item", brand="BrandT",
        category="Audio", description="", offers=offers
    )

    summary = generate_comparison_summary(product)
    assert summary is not None
    assert summary.max_price_spread == 100.0
    assert summary.potential_savings_pct == 20.0  # (100 / 500) * 100 = 20%

