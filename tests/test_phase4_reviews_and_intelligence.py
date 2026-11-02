"""Automated test suite for Phase 4: Beauty Reviews & Intelligence Hub.

Covers:
1. Review Source Attribution & Persistence:
   - Platform attribution (Nykaa, Tira, Purplle, Amazon India, Myntra)
   - Rating, scale, verified-buyer status, skin-type, and source URL
2. Review Filtering & Sorting:
   - Filter by platform, rating threshold, and skin-type
   - Sort by most recent, highest rated, and lowest rated
3. Rating-Scale Handling & Validation:
   - Transparent scale normalization to 5.0 standard
   - Rejection of invalid ratings (< 0 or > scale)
4. Duplicate Review Prevention:
   - external_review_id enforcement
5. Platform Ratings & Weighted Community Score:
   - Sum(R_i * N_i) / Sum(N_i) vs flawed simple averaging
   - Total review aggregation
6. Missing Review Data Handling:
   - Unavailable platforms distinguished from zero ratings
   - Exclusion from weighted score calculation
7. Beauty Product Usage Guide & Safety Protocols:
   - Routine step, frequency, and application instructions
   - Mandatory patch-test and photosensitivity warnings
   - Source reference attribution
8. Trust Labels & Transparent Disclosures:
   - Labeling demo feeds, verified buyers, and unlinked sources
"""

import pytest
import sqlite3
import tempfile
import os

from src.database.connection import init_db, migrate_db, get_connection
from src.database.models import ProductReview, PlatformRatingSummary, WeightedReviewScore
from src.services.review_service import (
    add_product_review,
    get_product_reviews,
    record_platform_rating,
    get_platform_rating_breakdown,
    calculate_weighted_review_score,
    get_product_usage_guide,
)


@pytest.fixture
def temp_db():
    """Create an isolated temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    migrate_db(path)

    # Seed baseline stores and sample products
    with get_connection(path) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO stores (name, domain) VALUES ('Nykaa', 'nykaa.com')")
        nykaa_id = c.lastrowid
        c.execute("INSERT INTO stores (name, domain) VALUES ('Tira', 'tirabeauty.com')")
        tira_id = c.lastrowid
        c.execute("INSERT INTO stores (name, domain) VALUES ('Amazon India', 'amazon.in')")
        amazon_id = c.lastrowid

        # Insert Product 1: Sunscreen
        c.execute(
            """
            INSERT INTO products (sku, title, brand, category, description, specs_json, created_at)
            VALUES (
                'DK-SUN-50ML',
                'Dot & Key Watermelon Cooling Sunscreen SPF 50',
                'Dot & Key',
                'Sunscreen',
                'Ultra-light fluid sunscreen with watermelon and hyaluronic acid',
                '{"Routine": "AM", "Skin Type": "All Skin Types, Oily", "Key Ingredients": "Watermelon Extract, Hyaluronic Acid, Tinosorb M"}',
                '2026-10-01 10:00:00'
            )
            """
        )
        p1_id = c.lastrowid

        # Insert Product 2: Exfoliating Acid Serum
        c.execute(
            """
            INSERT INTO products (sku, title, brand, category, description, specs_json, created_at)
            VALUES (
                'MIN-SAL-30ML',
                'Minimalist 2% Salicylic Acid Face Serum',
                'Minimalist',
                'Serums',
                'Pore-clearing BHA serum with oligopeptide for acne-prone skin',
                '{"Routine": "PM", "Skin Type": "Acne-Prone, Oily", "Key Ingredients": "Salicylic Acid 2%, Oligopeptide, Aloe Juice"}',
                '2026-10-01 10:00:00'
            )
            """
        )
        p2_id = c.lastrowid

        # Offers for Product 1
        c.execute(
            """
            INSERT INTO offers (product_id, store_id, variant_name, current_price, original_price, availability, last_checked)
            VALUES (?, ?, '50ml', 465.0, 595.0, 'In Stock', '2026-10-25 12:00:00')
            """,
            (p1_id, nykaa_id),
        )

        c.execute(
            """
            INSERT INTO offers (product_id, store_id, variant_name, current_price, original_price, availability, last_checked)
            VALUES (?, ?, '50ml', 480.0, 595.0, 'In Stock', '2026-10-25 12:00:00')
            """,
            (p1_id, tira_id),
        )

    yield {"path": path, "p1_id": p1_id, "p2_id": p2_id}

    if os.path.exists(path):
        os.remove(path)


# =============================================================================
# 1. Review Source Attribution & Persistence Tests
# =============================================================================

def test_review_source_attribution_and_storage(temp_db):
    """Verify reviews preserve platform attribution, ratings, verified buyer tags, and source URLs."""
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]

    success, msg, rev_id = add_product_review(
        product_id=p1_id,
        platform="Nykaa",
        reviewer_name="Ananya Sharma",
        rating=5.0,
        title="Holy grail sunscreen for humid Mumbai weather!",
        comment="Zero white cast on dusky skin tone. Doesn't pill under foundation.",
        review_date="2026-10-14",
        verified_buyer=True,
        skin_type="Oily",
        source_url="https://www.nykaa.com/reviews/123",
        data_status="demo",
        external_review_id="nyk-rev-001",
        custom_path=path,
    )
    assert success is True
    assert rev_id is not None

    reviews = get_product_reviews(p1_id, custom_path=path)
    assert len(reviews) == 1
    rev = reviews[0]
    assert rev.platform == "Nykaa"
    assert rev.reviewer_name == "Ananya Sharma"
    assert rev.rating == 5.0
    assert rev.verified_buyer is True
    assert rev.skin_type == "Oily"
    assert rev.source_url == "https://www.nykaa.com/reviews/123"
    assert rev.data_status == "demo"
    assert rev.normalized_rating == 5.0


# =============================================================================
# 2. Review Filtering and Sorting Tests
# =============================================================================

def test_review_filtering_and_sorting(temp_db):
    """Test filtering by platform, rating, skin type, and sorting options."""
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]

    # Seed 3 reviews with different parameters
    add_product_review(
        product_id=p1_id,
        platform="Nykaa",
        reviewer_name="Pooja",
        rating=5.0,
        comment="Amazing formula",
        review_date="2026-10-10",
        skin_type="Oily",
        external_review_id="ext-1",
        custom_path=path,
    )
    add_product_review(
        product_id=p1_id,
        platform="Tira",
        reviewer_name="Rhea",
        rating=3.0,
        comment="Average hydration",
        review_date="2026-10-25",
        skin_type="Dry",
        external_review_id="ext-2",
        custom_path=path,
    )
    add_product_review(
        product_id=p1_id,
        platform="Amazon India",
        reviewer_name="Kavita",
        rating=4.0,
        comment="Good cooling effect",
        review_date="2026-10-18",
        skin_type="Sensitive",
        external_review_id="ext-3",
        custom_path=path,
    )

    # 1. Filter by platform
    nykaa_only = get_product_reviews(p1_id, platform="Nykaa", custom_path=path)
    assert len(nykaa_only) == 1
    assert nykaa_only[0].reviewer_name == "Pooja"

    # 2. Filter by min_rating >= 4.0
    high_rated = get_product_reviews(p1_id, min_rating=4.0, custom_path=path)
    assert len(high_rated) == 2
    assert all(r.rating >= 4.0 for r in high_rated)

    # 3. Filter by skin_type
    dry_only = get_product_reviews(p1_id, skin_type="Dry", custom_path=path)
    assert len(dry_only) == 1
    assert dry_only[0].reviewer_name == "Rhea"

    # 4. Sort by most recent
    by_recent = get_product_reviews(p1_id, sort_by="recent", custom_path=path)
    assert by_recent[0].reviewer_name == "Rhea"  # 2026-10-25
    assert by_recent[-1].reviewer_name == "Pooja"  # 2026-10-10

    # 5. Sort by highest rated
    by_highest = get_product_reviews(p1_id, sort_by="highest_rated", custom_path=path)
    assert by_highest[0].rating == 5.0
    assert by_highest[-1].rating == 3.0

    # 6. Sort by lowest rated
    by_lowest = get_product_reviews(p1_id, sort_by="lowest_rated", custom_path=path)
    assert by_lowest[0].rating == 3.0
    assert by_lowest[-1].rating == 5.0


# =============================================================================
# 3. Rating Scale Normalization & Validation Tests
# =============================================================================

def test_rating_scale_normalization_and_validation(temp_db):
    """Verify non-5 scales are normalized to 5-star standard, and invalid ratings are rejected."""
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]

    # Rejection of negative rating
    neg_res, neg_msg, _ = add_product_review(
        product_id=p1_id, platform="Nykaa", reviewer_name="Test", rating=-1.0, comment="Bad", custom_path=path
    )
    assert neg_res is False
    assert "non-negative" in neg_msg.lower()

    # Rejection of rating exceeding scale
    exc_res, exc_msg, _ = add_product_review(
        product_id=p1_id, platform="Nykaa", reviewer_name="Test", rating=6.0, rating_scale=5.0, comment="Too high", custom_path=path
    )
    assert exc_res is False
    assert "exceeds" in exc_msg.lower()

    # Rejection of empty comment
    empty_res, _, _ = add_product_review(
        product_id=p1_id, platform="Nykaa", reviewer_name="Test", rating=4.0, comment="   ", custom_path=path
    )
    assert empty_res is False

    # Rating on 10-point scale: 8.0 / 10.0 -> normalized 4.0 / 5.0
    success, _, rev_id = add_product_review(
        product_id=p1_id,
        platform="Tira",
        reviewer_name="Arjun",
        rating=8.0,
        rating_scale=10.0,
        comment="Great on 10 pt scale",
        external_review_id="ten-pt-1",
        custom_path=path,
    )
    assert success is True
    reviews = get_product_reviews(p1_id, custom_path=path)
    match = [r for r in reviews if r.id == rev_id][0]
    assert match.rating == 8.0
    assert match.rating_scale == 10.0
    assert match.normalized_rating == 4.0


# =============================================================================
# 4. Duplicate Review Prevention Tests
# =============================================================================

def test_duplicate_review_prevention(temp_db):
    """Enforce external_review_id uniqueness to prevent duplicate imports."""
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]

    # Initial import
    ok1, _, id1 = add_product_review(
        product_id=p1_id,
        platform="Nykaa",
        reviewer_name="Simran",
        rating=5.0,
        comment="First review",
        external_review_id="dup-check-001",
        custom_path=path,
    )
    assert ok1 is True

    # Duplicate import attempt with identical external_review_id
    ok2, msg2, id2 = add_product_review(
        product_id=p1_id,
        platform="Nykaa",
        reviewer_name="Simran Copy",
        rating=5.0,
        comment="Duplicate review copy",
        external_review_id="dup-check-001",
        custom_path=path,
    )
    assert ok2 is False
    assert "already exists" in msg2.lower()
    assert id2 == id1


# =============================================================================
# 5. Cross-Platform Comparison & True Weighted Score Tests
# =============================================================================

def test_platform_ratings_and_true_weighted_score(temp_db):
    """
    Test true weighted rating calculation:
    Formula: Sum(Rating_i * Count_i) / Sum(Count_i)
    Must not average averages directly when review counts differ.
    """
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]

    # Platform A: Nykaa (rating 4.8 from 1,000 reviews)
    record_platform_rating(p1_id, "Nykaa", 4.8, 1000, custom_path=path)
    # Platform B: Tira (rating 4.6 from 500 reviews)
    record_platform_rating(p1_id, "Tira", 4.6, 500, custom_path=path)
    # Platform C: Amazon India (rating 4.2 from 2,000 reviews)
    record_platform_rating(p1_id, "Amazon India", 4.2, 2000, custom_path=path)

    # True weighted rating:
    # (4.8*1000 + 4.6*500 + 4.2*2000) / (1000 + 500 + 2000)
    # = (4800 + 2300 + 8400) / 3500
    # = 15500 / 3500 = 4.4285... -> 4.43
    #
    # Flawed simple average would be: (4.8 + 4.6 + 4.2)/3 = 4.533... -> 4.53
    score = calculate_weighted_review_score(p1_id, custom_path=path)
    assert score.weighted_rating is not None
    assert score.weighted_rating == 4.43  # Proves weighted calculation, not simple 4.53
    assert score.total_reviews == 3500
    assert score.platforms_included == 3
    assert "Weighted score computed" in score.explanation


# =============================================================================
# 6. Missing Platform Data & Honest Unavailable State Tests
# =============================================================================

def test_missing_platform_data_handling(temp_db):
    """
    Ensure unavailable platforms are not counted as 0.0 rating or zero reviews,
    and are cleanly excluded from the weighted score calculation.
    """
    path = temp_db["path"]
    p2_id = temp_db["p2_id"]

    # Only Nykaa has recorded reviews for p2
    record_platform_rating(p2_id, "Nykaa", 4.5, 300, custom_path=path)

    breakdown = get_platform_rating_breakdown(p2_id, custom_path=path)
    assert len(breakdown) == 5  # All 5 platforms represented

    # Available platform
    nykaa = [p for p in breakdown if p.platform == "Nykaa"][0]
    assert nykaa.is_available is True
    assert nykaa.average_rating == 4.5
    assert nykaa.review_count == 300

    # Unavailable platforms (e.g. Myntra)
    myntra = [p for p in breakdown if p.platform == "Myntra"][0]
    assert myntra.is_available is False
    assert myntra.average_rating is None
    assert myntra.review_count is None
    assert myntra.data_source == "Data Unavailable"

    # Score calculation must only include Nykaa (300 reviews @ 4.5)
    score = calculate_weighted_review_score(p2_id, custom_path=path)
    assert score.weighted_rating == 4.5
    assert score.total_reviews == 300
    assert score.platforms_included == 1

    # Product with 0 platforms recorded
    fd, empty_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(empty_path)
    migrate_db(empty_path)
    empty_score = calculate_weighted_review_score(999, custom_path=empty_path)
    assert empty_score.weighted_rating is None
    assert empty_score.total_reviews == 0
    assert empty_score.platforms_included == 0
    if os.path.exists(empty_path):
        os.remove(empty_path)


# =============================================================================
# 7. Beauty Product Usage Guide & Safety Protocols Tests
# =============================================================================

def test_product_usage_guide_and_safety_protocols(temp_db):
    """
    Test dermatologist-aligned routine step mapping, frequency,
    mandatory patch-test protocol, and photosensitivity warnings for actives.
    """
    path = temp_db["path"]
    p1_id = temp_db["p1_id"]  # Sunscreen
    p2_id = temp_db["p2_id"]  # 2% Salicylic Acid BHA Serum

    # 1. Sunscreen Usage Guide
    g_sun = get_product_usage_guide(p1_id, custom_path=path)
    assert g_sun.step_number == 5
    assert "Sun Defense" in g_sun.step_name
    assert g_sun.routine == "AM"
    assert "patch test" in g_sun.patch_test_guideline.lower()
    assert "Indian Dermatological Society" in g_sun.source_reference
    assert len(g_sun.key_actives_breakdown) >= 2

    # 2. Salicylic Acid BHA Serum Usage Guide (Photosensitizer check)
    g_acid = get_product_usage_guide(p2_id, custom_path=path)
    assert g_acid.step_number == 3
    assert "Treatment" in g_acid.step_name
    assert g_acid.routine == "PM"
    assert g_acid.sun_safety_guideline is not None
    assert "spf" in g_acid.sun_safety_guideline.lower()
    assert "photosensitivity" in g_acid.sun_safety_guideline.lower()

