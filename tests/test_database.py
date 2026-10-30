"""Tests for database operations and data seeding."""

import tempfile
import os
import pytest
from src.database.connection import init_db, get_connection
from src.database.seed import seed_database
from src.services.product_service import get_products, get_product_by_id, get_all_categories


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    seed_database(custom_path=path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_seed_database_populates_data(temp_db):
    products = get_products(custom_path=temp_db)
    assert len(products) > 0

    categories = get_all_categories(custom_path=temp_db)
    assert "Laptops" in categories
    assert "Smartphones" in categories
    assert "Audio" in categories


def test_product_query_and_details(temp_db):
    products = get_products(category="Laptops", custom_path=temp_db)
    assert len(products) > 0
    first_id = products[0].id

    detailed = get_product_by_id(first_id, custom_path=temp_db)
    assert detailed is not None
    assert detailed.id == first_id
    assert len(detailed.offers) > 0

    # Ensure price history was seeded
    first_offer = detailed.offers[0]
    assert len(first_offer.price_history) > 0


def test_search_filter(temp_db):
    macbooks = get_products(search_query="MacBook", custom_path=temp_db)
    assert len(macbooks) >= 1
    assert any("MacBook" in p.title for p in macbooks)

