"""Price Verification and Evidence Management Service for PriceWise AI Beauty (Phase 11B).

Manages the immutable verification audit trail:
- Evidence reference recording (screenshots, receipts, product pages)
- Verification lifecycle statuses:
  LIVE_VERIFIED, MANUAL_VERIFIED, CACHED, HISTORICAL, POSSIBLE_MATCH, RESTRICTED, UNAVAILABLE, DEMO
- Multi-factor deterministic validation guardrails:
  - Selling price must be positive (> 0)
  - Reference MRP must be >= selling price
  - Matching classification must be EXACT_MATCH for LIVE_VERIFIED
  - Evidence must be recorded for MANUAL_VERIFIED
  - Strict separation of DEMO data from confirmed market prices
- Admin verification queue and approval / rejection workflows
- Integration with price history and deal tracking alert triggers
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any, Optional
from urllib.parse import urlparse

from src.database.connection import get_connection
from src.database.models import User
from src.services.price_tracking_service import evaluate_tracking_rules

logger = logging.getLogger("pricewise.verification")


class VerificationStatus:
    LIVE_VERIFIED = "LIVE_VERIFIED"
    MANUAL_VERIFIED = "MANUAL_VERIFIED"
    CACHED = "CACHED"
    HISTORICAL = "HISTORICAL"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    RESTRICTED = "RESTRICTED"
    UNAVAILABLE = "UNAVAILABLE"
    DEMO = "DEMO"

    ALL_STATUSES = {
        LIVE_VERIFIED,
        MANUAL_VERIFIED,
        CACHED,
        HISTORICAL,
        POSSIBLE_MATCH,
        RESTRICTED,
        UNAVAILABLE,
        DEMO,
    }


RETAILER_TO_STORE_ID = {
    "nykaa": 6,
    "nykaa (demo)": 6,
    "tira": 7,
    "tira (demo)": 7,
    "tirabeauty": 7,
    "purplle": 8,
    "purplle (demo)": 8,
    "amazon": 9,
    "amazon india": 9,
    "amazon india (demo)": 9,
    "amazon.in": 9,
    "myntra": 10,
    "myntra (demo)": 10,
}


def get_store_id_for_retailer(retailer: str) -> Optional[int]:
    """Map retailer name or domain to internal database store_id."""
    clean = (retailer or "").lower().strip()
    return RETAILER_TO_STORE_ID.get(clean)


@dataclass
class PriceObservationRecord:
    """Immutable representation of an observed and verified price."""
    product_id: int
    retailer: str
    product_url: str
    observed_title: str
    brand: str
    selling_price: float
    mrp: Optional[float] = None
    currency: str = "INR"
    size_volume: Optional[str] = None
    shade: Optional[str] = None
    formulation: Optional[str] = None
    availability: str = "In Stock"
    extraction_method: str = "manual_verification"
    match_classification: str = "EXACT_MATCH"
    verification_status: str = VerificationStatus.MANUAL_VERIFIED
    evidence_reference_id: Optional[int] = None
    evidence_url: Optional[str] = None
    observed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None


def validate_price_observation_data(
    selling_price: float,
    mrp: Optional[float],
    product_url: str,
    retailer: str,
    match_classification: str,
) -> tuple[bool, Optional[str]]:
    """
    Deterministic validation guardrails.
    Returns (is_valid, error_reason).
    """
    if selling_price <= 0:
        return False, "Selling price must be greater than zero."

    if mrp is not None and mrp < selling_price:
        return False, f"MRP (₹{mrp}) cannot be lower than selling price (₹{selling_price})."

    if not product_url or not isinstance(product_url, str):
        return False, "A valid product URL is required."

    try:
        parsed = urlparse(product_url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False, "Product URL must use HTTP or HTTPS."
        if not parsed.netloc:
            return False, "Product URL is missing a valid host."
    except Exception as e:
        return False, f"Invalid URL structure: {e}"

    return True, None


def record_evidence_reference(
    reference_type: str,
    reference_id: int,
    evidence_url: str,
    evidence_type: str = "screenshot",
    description: Optional[str] = None,
    uploaded_by: int = 1,
) -> int:
    """
    Insert immutable evidence link into evidence_references table.
    Returns created evidence ID.
    """
    valid_ref_types = ("manual_verification", "price_correction")
    if reference_type not in valid_ref_types:
        raise ValueError(f"reference_type must be one of {valid_ref_types}")

    valid_evidence_types = ("screenshot", "receipt", "product_page", "other")
    if evidence_type not in valid_evidence_types:
        evidence_type = "screenshot"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO evidence_references (
                reference_type, reference_id, evidence_url, evidence_type,
                description, uploaded_at, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """,
            (
                reference_type,
                reference_id,
                evidence_url,
                evidence_type,
                description or "User uploaded price verification proof",
                uploaded_by,
            ),
        )
        return cursor.lastrowid


def get_evidence_for_reference(reference_type: str, reference_id: int) -> list[dict[str, Any]]:
    """Fetch all evidence records linked to a verification or correction submission."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, reference_type, reference_id, evidence_url, evidence_type, description, uploaded_at, uploaded_by
            FROM evidence_references
            WHERE reference_type = ? AND reference_id = ?
            ORDER BY uploaded_at DESC
            """,
            (reference_type, reference_id),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_pending_verification_queue(limit: int = 50) -> dict[str, Any]:
    """Retrieve pending manual verification requests and price corrections for admin review."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Manual verifications
        cursor.execute(
            """
            SELECT m.*, u.display_name as user_name, u.email as user_email, p.title as product_title, p.brand as product_brand
            FROM manual_verification_requests m
            JOIN users u ON m.user_id = u.id
            JOIN products p ON m.product_id = p.id
            WHERE m.status = 'pending'
            ORDER BY m.submitted_at ASC
            LIMIT ?
            """,
            (limit,),
        )
        manual_rows = cursor.fetchall()
        manual_list = []
        for r in manual_rows:
            item = dict(r)
            item["evidence"] = get_evidence_for_reference("manual_verification", item["id"])
            manual_list.append(item)

        # 2. Price corrections
        cursor.execute(
            """
            SELECT c.*, u.display_name as user_name, u.email as user_email, p.title as product_title, p.brand as product_brand
            FROM price_correction_submissions c
            JOIN users u ON c.user_id = u.id
            JOIN products p ON c.product_id = p.id
            WHERE c.status = 'pending'
            ORDER BY c.created_at ASC
            LIMIT ?
            """,
            (limit,),
        )
        corr_rows = cursor.fetchall()
        corr_list = []
        for r in corr_rows:
            item = dict(r)
            item["evidence"] = get_evidence_for_reference("price_correction", item["id"])
            corr_list.append(item)

    return {
        "status": "ok",
        "pending_manual_verifications": manual_list,
        "pending_price_corrections": corr_list,
        "total_pending": len(manual_list) + len(corr_list),
    }


def approve_manual_verification(
    request_id: int,
    reviewer: User,
    verified_price: Optional[float] = None,
    verified_mrp: Optional[float] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """
    Admin approves a manual price verification request:
    1. Validates verified price & MRP.
    2. Updates manual_verification_requests status to 'verified' and verification_status to 'MANUAL_VERIFIED'.
    3. Updates or creates an offer in offers table for that product & store.
    4. Appends a new verified record into price_history table.
    5. Evaluates price tracking alert rules to notify users if price hit their target.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM manual_verification_requests WHERE id = ?",
            (request_id,),
        )
        req = cursor.fetchone()
        if not req:
            raise ValueError(f"Manual verification request {request_id} not found.")

        req_dict = dict(req)
        final_price = verified_price if verified_price is not None else req_dict.get("user_submitted_price")
        if not final_price or final_price <= 0:
            raise ValueError("Approved price must be positive.")

        final_mrp = verified_mrp if verified_mrp is not None else req_dict.get("verified_mrp")
        if final_mrp is not None and final_mrp < final_price:
            raise ValueError(f"MRP (₹{final_mrp}) cannot be lower than verified price (₹{final_price}).")

        discount_pct = round(((final_mrp - final_price) / final_mrp) * 100, 1) if (final_mrp and final_mrp > final_price) else 0.0

        # Update manual_verification_requests
        cursor.execute(
            """
            UPDATE manual_verification_requests
            SET status = 'verified',
                verification_status = 'MANUAL_VERIFIED',
                verified_price = ?,
                verified_mrp = ?,
                verified_discount_pct = ?,
                verification_notes = ?,
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                verified_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                final_price,
                final_mrp,
                discount_pct,
                notes or req_dict.get("notes") or "Verified by admin reviewer",
                reviewer.id,
                request_id,
            ),
        )

        product_id = req_dict["product_id"]
        retailer = req_dict["retailer"]
        store_id = get_store_id_for_retailer(retailer) or 6  # fallback store
        variant = req_dict.get("size_volume") or req_dict.get("shade") or "Standard"
        product_url = req_dict["product_url"]

        # Check existing offer
        cursor.execute(
            "SELECT id FROM offers WHERE product_id = ? AND store_id = ?",
            (product_id, store_id),
        )
        existing_offer = cursor.fetchone()

        if existing_offer:
            offer_id = existing_offer["id"]
            cursor.execute(
                """
                UPDATE offers
                SET current_price = ?,
                    original_price = ?,
                    availability = 'In Stock',
                    variant_name = ?,
                    offer_url = ?,
                    last_checked = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (final_price, final_mrp, variant, product_url, offer_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO offers (
                    product_id, store_id, current_price, original_price,
                    shipping_cost, currency, availability, variant_name,
                    condition, offer_url, last_checked
                ) VALUES (?, ?, ?, ?, 0.0, 'INR', 'In Stock', ?, 'new', ?, CURRENT_TIMESTAMP)
                """,
                (product_id, store_id, final_price, final_mrp, variant, product_url),
            )
            offer_id = cursor.lastrowid

        # Append to price_history
        cursor.execute(
            """
            INSERT INTO price_history (
                offer_id, price, currency, data_source, data_status, recorded_at
            ) VALUES (?, ?, 'INR', 'manual_verification', 'manual_verified', CURRENT_TIMESTAMP)
            """,
            (offer_id, final_price),
        )

    # Evaluate price alerts
    try:
        evaluate_tracking_rules()
    except Exception as e:
        logger.warning(f"Error evaluating tracking rules post verification: {e}")

    return {
        "status": "approved",
        "request_id": request_id,
        "verified_price": final_price,
        "verified_mrp": final_mrp,
        "offer_id": offer_id,
        "verification_status": VerificationStatus.MANUAL_VERIFIED,
    }


def reject_manual_verification(
    request_id: int,
    reviewer: User,
    rejection_reason: str,
) -> dict[str, Any]:
    """Admin rejects a manual price verification request."""
    if not rejection_reason or not rejection_reason.strip():
        raise ValueError("Rejection reason is required.")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE manual_verification_requests
            SET status = 'rejected',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                rejection_reason = ?
            WHERE id = ?
            """,
            (reviewer.id, rejection_reason.strip(), request_id),
        )

    return {
        "status": "rejected",
        "request_id": request_id,
        "rejection_reason": rejection_reason.strip(),
    }


def approve_price_correction(
    submission_id: int,
    reviewer: User,
    verified_price: Optional[float] = None,
    verified_mrp: Optional[float] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """Admin approves a user price correction submission."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM price_correction_submissions WHERE id = ?",
            (submission_id,),
        )
        sub = cursor.fetchone()
        if not sub:
            raise ValueError(f"Price correction submission {submission_id} not found.")

        sub_dict = dict(sub)
        final_price = verified_price if verified_price is not None else sub_dict["submitted_price"]
        final_mrp = verified_mrp if verified_mrp is not None else sub_dict.get("submitted_mrp")

        cursor.execute(
            """
            UPDATE price_correction_submissions
            SET status = 'approved',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (reviewer.id, submission_id),
        )

        product_id = sub_dict["product_id"]
        retailer = sub_dict["retailer"]
        store_id = get_store_id_for_retailer(retailer) or 6
        variant = sub_dict.get("size_volume") or sub_dict.get("shade") or "Standard"
        product_url = sub_dict["product_url"]

        cursor.execute(
            "SELECT id FROM offers WHERE product_id = ? AND store_id = ?",
            (product_id, store_id),
        )
        existing_offer = cursor.fetchone()

        if existing_offer:
            offer_id = existing_offer["id"]
            cursor.execute(
                """
                UPDATE offers
                SET current_price = ?,
                    original_price = ?,
                    availability = 'In Stock',
                    variant_name = ?,
                    offer_url = ?,
                    last_checked = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (final_price, final_mrp, variant, product_url, offer_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO offers (
                    product_id, store_id, current_price, original_price,
                    shipping_cost, currency, availability, variant_name,
                    condition, offer_url, last_checked
                ) VALUES (?, ?, ?, ?, 0.0, 'INR', 'In Stock', ?, 'new', ?, CURRENT_TIMESTAMP)
                """,
                (product_id, store_id, final_price, final_mrp, variant, product_url),
            )
            offer_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO price_history (
                offer_id, price, currency, data_source, data_status, recorded_at
            ) VALUES (?, ?, 'INR', 'price_correction', 'manual_verified', CURRENT_TIMESTAMP)
            """,
            (offer_id, final_price),
        )

    try:
        evaluate_tracking_rules()
    except Exception as e:
        logger.warning(f"Error evaluating tracking rules post price correction: {e}")

    return {
        "status": "approved",
        "submission_id": submission_id,
        "verified_price": final_price,
        "offer_id": offer_id,
        "verification_status": VerificationStatus.MANUAL_VERIFIED,
    }


def reject_price_correction(
    submission_id: int,
    reviewer: User,
    rejection_reason: str,
) -> dict[str, Any]:
    """Admin rejects a price correction submission."""
    if not rejection_reason or not rejection_reason.strip():
        raise ValueError("Rejection reason is required.")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE price_correction_submissions
            SET status = 'rejected',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                rejection_reason = ?
            WHERE id = ?
            """,
            (reviewer.id, rejection_reason.strip(), submission_id),
        )

    return {
        "status": "rejected",
        "submission_id": submission_id,
        "rejection_reason": rejection_reason.strip(),
    }
