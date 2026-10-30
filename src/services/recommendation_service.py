"""Recommendation Service for PriceWise AI: Smart Purchase Advisor.

Provides deterministic, explainable product recommendations based on:
1. Hard budget constraints and shipping total cost
2. Category and use-case suitability matching
3. Specific recorded technical specifications (RAM, Storage, Display, Battery, ANC, GPU)
4. Safe handling of missing specifications (treated as unknown, not assumed)
5. Lowest comparable, available offer selection
6. Real Deal Detector intelligence (evaluating historical price attractiveness separately)
7. 3-tier recommendation categories: BEST OVERALL, BEST BUDGET, and BEST CURRENT DEAL
8. Clear identification of closest alternatives when requirements cannot be fully met
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Optional

from src.analysis.deal_detector import analyze_product_deal, DealAnalysis
from src.database.models import Offer, Product
from src.services.comparison_service import validate_offer_compatibility
from src.services.product_service import get_products


@dataclass
class AdvisorPreferences:
    """User preferences and constraints supplied to the Smart Purchase Advisor."""
    budget: float
    category: Optional[str] = "All"
    use_case: str = "Everyday Use"  # 'Studying', 'Programming', 'Gaming', 'Photography', 'Office Work', 'Everyday Use'
    brand_preference: Optional[str] = None  # None, 'All', or specific brand
    min_ram_gb: Optional[int] = None
    min_storage_gb: Optional[int] = None
    min_battery_hours: Optional[int] = None
    require_in_stock: bool = True
    require_anc: bool = False
    require_4k: bool = False
    require_discrete_gpu: bool = False
    max_shipping_cost: Optional[float] = None
    custom_spec_requirements: dict[str, Any] = field(default_factory=dict)

    # Phase 7 Personalization fields
    preferred_categories: list[str] = field(default_factory=list)
    preferred_brands: list[str] = field(default_factory=list)
    preferred_store_id: Optional[int] = None
    priority: str = "balanced"  # 'lowest_price', 'best_deal', 'balanced'
    user_saved_min_budget: Optional[float] = None
    user_saved_max_budget: Optional[float] = None


@dataclass
class ProductEvaluation:
    """Detailed explainable evaluation of a single product candidate."""
    product: Product
    best_offer: Optional[Offer]
    base_price: Optional[float]
    shipping_cost: float
    total_cost: Optional[float]
    store_name: str
    is_available: bool
    budget_fit: bool
    budget_difference: float  # budget - total_cost (positive = remaining, negative = overrun)
    budget_difference_pct: float  # (budget - total_cost) / budget * 100

    # Suitability & Spec evaluation
    suitability_score: float  # 0 to 100
    spec_score: float  # 0 to 100
    budget_score: float  # 0 to 100
    brand_score: float  # 0 to 100
    recommendation_score: float  # 0 to 100 composite

    # Explainability fields
    score_breakdown: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    cautions_or_missing_specs: list[str] = field(default_factory=list)
    matched_hard_requirements: list[str] = field(default_factory=list)
    failed_hard_requirements: list[str] = field(default_factory=list)

    # Real Deal Detector (separate score!)
    deal_analysis: Optional[DealAnalysis] = None
    deal_score: Optional[int] = None
    deal_classification: str = "INSUFFICIENT DATA"
    is_good_value: bool = False

    @property
    def is_fully_suitable(self) -> bool:
        """Indicates whether all hard requirements and budget were satisfied."""
        return len(self.failed_hard_requirements) == 0 and self.budget_fit and self.is_available


@dataclass
class RecommendationResult:
    """Complete Purchase Advisor result containing categorized recommendations and alternatives."""
    preferences: AdvisorPreferences
    best_overall: Optional[ProductEvaluation]
    best_budget: Optional[ProductEvaluation]
    best_deal: Optional[ProductEvaluation]
    ranked_candidates: list[ProductEvaluation]  # All products that met hard requirements
    closest_alternatives: list[ProductEvaluation]  # Products that failed budget or 1 hard requirement
    all_evaluated: list[ProductEvaluation]
    summary_explanation: str
    limitations: list[str] = field(default_factory=list)

    @property
    def best_current_deal(self) -> Optional[ProductEvaluation]:
        return self.best_deal


# =====================================================================
# Specification Parsing & Extraction Helpers
# =====================================================================

def extract_ram_gb(product: Product) -> Optional[int]:
    """Extract RAM capacity in gigabytes from specifications, title, or description."""
    specs = product.specs or {}
    ram_str = specs.get("RAM")
    if ram_str:
        match = re.search(r"(\d+)\s*(?:GB|gb)", str(ram_str))
        if match:
            return int(match.group(1))

    # Fallback to title/description regex
    text_to_search = f"{product.title} {product.description}"
    match = re.search(r"(\d+)\s*(?:GB|gb)\s*(?:RAM|Unified Memory|Memory)", text_to_search, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def extract_storage_gb(product: Product) -> Optional[int]:
    """Extract storage capacity in gigabytes from specifications or title."""
    specs = product.specs or {}
    storage_str = specs.get("Storage")
    if storage_str:
        # Check TB first
        match_tb = re.search(r"(\d+)\s*(?:TB|tb)", str(storage_str))
        if match_tb:
            return int(match_tb.group(1)) * 1000
        match_gb = re.search(r"(\d+)\s*(?:GB|gb)", str(storage_str))
        if match_gb:
            return int(match_gb.group(1))

    # Check title/description
    text_to_search = f"{product.title} {product.description}"
    match_tb = re.search(r"(\d+)\s*(?:TB|tb)\s*(?:SSD|Storage|NVMe)?", text_to_search, re.IGNORECASE)
    if match_tb:
        return int(match_tb.group(1)) * 1000
    match_gb = re.search(r"(\d+)\s*(?:GB|gb)\s*(?:SSD|Storage|NVMe|ROM)?", text_to_search, re.IGNORECASE)
    if match_gb:
        return int(match_gb.group(1))

    return None


def extract_battery_hours(product: Product) -> Optional[int]:
    """Extract battery run time in hours from specifications or description."""
    specs = product.specs or {}
    battery_str = specs.get("Battery")
    if battery_str:
        match = re.search(r"(\d+)\s*(?:Hours|hours|h|hrs)", str(battery_str), re.IGNORECASE)
        if match:
            return int(match.group(1))

    # Description search
    match = re.search(r"(\d+)\s*(?:Hours|hours|h|hrs)\s*battery", product.description, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def has_4k_display(product: Product) -> bool:
    """Determine whether the product features a 4K, 3.5K, or UHD resolution display."""
    specs = product.specs or {}
    search_space = " ".join([
        str(specs.get("Screen", "")),
        str(specs.get("Panel", "")),
        str(specs.get("Display", "")),
        str(specs.get("Max Resolution", "")),
        product.title,
        product.description,
    ]).lower()
    return any(k in search_space for k in ["4k", "3840", "3.5k", "uhd", "2160"])


def has_anc(product: Product) -> bool:
    """Determine whether the product features Active Noise Cancellation."""
    specs = product.specs or {}
    search_space = " ".join([
        str(specs.get("ANC", "")),
        str(specs.get("Modes", "")),
        product.title,
        product.description,
    ]).lower()
    return any(k in search_space for k in ["anc", "noise-canceling", "noise cancelling", "noise cancellation", "quiet"])


def has_discrete_gpu(product: Product) -> bool:
    """Determine whether the product features a dedicated discrete GPU."""
    specs = product.specs or {}
    gpu_val = str(specs.get("GPU", "")).lower()
    if gpu_val and gpu_val != "none":
        return True
    desc = product.description.lower()
    return any(k in desc for k in ["geforce", "rtx", "radeon", "discrete gpu", "discrete graphics"])


# =====================================================================
# Use-Case Suitability Scoring Logic
# =====================================================================

def evaluate_use_case_suitability(product: Product, use_case: str) -> tuple[float, list[str]]:
    """
    Evaluate product suitability for a specified use case on a 0-100 scale.
    Returns (suitability_score, reasons).
    """
    category = product.category.lower()
    specs = product.specs or {}
    reasons: list[str] = []
    score = 50.0

    if use_case == "Studying":
        if category == "laptops":
            score = 85.0
            reasons.append("Laptops provide the primary interface for research, coursework, and essay writing.")
            if "weight" in [k.lower() for k in specs.keys()]:
                reasons.append("Portable form-factor suitable for campus and library commuting.")
        elif category == "audio":
            score = 85.0
            if has_anc(product):
                score += 10.0
                reasons.append("Active Noise Cancellation blocks library and dorm ambient distractions.")
            else:
                reasons.append("Private listening for recorded lectures and study focus.")
        elif category in ["wearables", "smartphones"]:
            score = 75.0
            reasons.append("Reliable scheduling, timer, and communication tools for students.")
        elif category == "monitors":
            score = 70.0
            reasons.append("Expanded screen real estate for multi-window research papers.")
        else:
            score = 35.0
            reasons.append(f"Category '{product.category}' has secondary relevance for academic study.")

    elif use_case == "Programming":
        if category == "laptops":
            ram = extract_ram_gb(product)
            if ram and ram >= 32:
                score = 98.0
                reasons.append(f"Exceptional 32GB RAM capacity effortlessly handles Docker, VMs, and heavy builds.")
            elif ram and ram >= 16:
                score = 90.0
                reasons.append(f"Generous {ram}GB RAM accommodates modern IDEs, multi-container stacks, and compilation.")
            else:
                score = 75.0
                reasons.append("Capable development machine for standard programming workloads.")
        elif category == "monitors":
            score = 88.0
            if has_4k_display(product):
                score += 7.0
                reasons.append("High-DPI 4K display maximizes code view and terminal clarity.")
            if "hub" in product.title.lower() or "ports" in [k.lower() for k in specs.keys()]:
                reasons.append("USB-C Hub provides single-cable docking for developer laptops.")
        elif category in ["gaming", "smartphones"]:
            score = 50.0
            reasons.append("Useful for mobile app testing or recreational downtime.")
        else:
            score = 30.0
            reasons.append("Limited direct utility for software engineering pipelines.")

    elif use_case == "Gaming":
        if category == "gaming":
            score = 96.0
            reasons.append("Dedicated gaming console hardware optimized for high-fidelity ray tracing and 4K 120Hz.")
        elif category == "laptops":
            if has_discrete_gpu(product):
                score = 92.0
                reasons.append("Dedicated discrete GeForce RTX GPU delivers high frame rates and hardware acceleration.")
            else:
                score = 55.0
                reasons.append("Integrated graphics limit modern AAA gaming performance.")
        elif category in ["tvs", "monitors"]:
            score = 85.0
            if "120hz" in f"{product.title} {product.specs}".lower():
                score += 10.0
                reasons.append("120Hz high-refresh display ensures fluid low-latency gaming output.")
            else:
                reasons.append("High-resolution external display for console or PC gaming.")
        elif category == "smartphones":
            score = 65.0
            reasons.append("High-end mobile chip and 120Hz screen support responsive mobile gaming.")
        else:
            score = 25.0
            reasons.append("Hardware not optimized for interactive gaming workloads.")

    elif use_case == "Photography":
        if category == "cameras":
            score = 98.0
            reasons.append("Full-frame interchangeable lens mirrorless camera engineered for professional stills and 4K video.")
        elif category == "monitors":
            score = 88.0
            reasons.append("Color-accurate panel (IPS / Wide Color Gamut) for reliable photo editing and color grading.")
        elif category == "laptops":
            if "oled" in f"{product.title} {product.specs}".lower() or "xdr" in f"{product.title} {product.specs}".lower():
                score = 92.0
                reasons.append("High dynamic range OLED/XDR display offers wide gamut color grading on location.")
            else:
                score = 80.0
                reasons.append("Powerful editing platform for Adobe Lightroom and Photoshop workflows.")
        elif category == "smartphones":
            score = 82.0
            reasons.append("Multi-camera array with dedicated high-megapixel sensor and RAW capture.")
        else:
            score = 30.0
            reasons.append("Lacks dedicated photographic imaging sensors or color calibration.")

    elif use_case == "Office Work":
        if category == "monitors":
            score = 92.0
            reasons.append("Expanded desktop surface drastically improves spreadsheet and document multi-tasking.")
        elif category == "audio":
            score = 90.0
            if has_anc(product):
                reasons.append("Active noise cancellation blocks open-plan office chatter and enhances call intelligibility.")
            else:
                reasons.append("Clear audio monitoring for meetings and conference calls.")
        elif category == "laptops":
            score = 90.0
            reasons.append("Complete productivity workstation with all-day battery life and full business suite support.")
        elif category in ["wearables", "smartphones"]:
            score = 80.0
            reasons.append("Keeps calendar alerts, notifications, and urgent email correspondence accessible.")
        else:
            score = 40.0
            reasons.append("Recreational hardware not tailored to standard office productivity.")

    else:  # Everyday Use
        score = 75.0
        reasons.append("Well-rounded consumer technology suited for versatile daily activities.")

    return min(100.0, max(10.0, score)), reasons


# =====================================================================
# Product Candidate Evaluation Engine
# =====================================================================

def evaluate_product_for_advisor(
    product: Product,
    preferences: AdvisorPreferences,
    reference_date: Optional[datetime] = None,
) -> ProductEvaluation:
    """
    Evaluates a candidate product against the user's hard requirements and preferences.
    Calculates separate Suitability, Spec, Budget, and Recommendation scores,
    while running the Real Deal Detector independently.
    """
    failed_hards: list[str] = []
    matched_hards: list[str] = []
    cautions_or_missing: list[str] = []

    # 1. Select Lowest Comparable, Available Offer
    comparable_offers: list[Offer] = []
    for offer in product.offers:
        is_comp, _ = validate_offer_compatibility(product, offer)
        if is_comp:
            comparable_offers.append(offer)

    available_offers = [o for o in comparable_offers if o.is_available]
    
    if available_offers:
        best_offer = min(available_offers, key=lambda o: o.total_cost)
        is_available = True
        base_price = best_offer.current_price
        shipping_cost = best_offer.shipping_cost
        total_cost = best_offer.total_cost
        store_name = best_offer.store_name
        matched_hards.append(f"In Stock at {store_name} (${base_price:,.2f} + ${shipping_cost:,.2f} shipping)")
    elif comparable_offers:
        best_offer = min(comparable_offers, key=lambda o: o.total_cost)
        is_available = False
        base_price = best_offer.current_price
        shipping_cost = best_offer.shipping_cost
        total_cost = best_offer.total_cost
        store_name = best_offer.store_name
        cautions_or_missing.append("Currently Out of Stock across monitored retailers.")
        if preferences.require_in_stock:
            failed_hards.append("Out of stock across all monitored retailers")
    else:
        best_offer = None
        is_available = False
        base_price = None
        shipping_cost = 0.0
        total_cost = None
        store_name = "None"
        failed_hards.append("No comparable, valid offers found for this product")

    # 2. Hard Requirement: Budget Constraint
    budget = preferences.budget
    if total_cost is not None:
        budget_diff = round(budget - total_cost, 2)
        budget_diff_pct = round((budget_diff / budget) * 100, 1) if budget > 0 else 0.0
        budget_fit = total_cost <= budget

        if budget_fit:
            matched_hards.append(f"Within budget (${total_cost:,.2f} vs ${budget:,.2f} limit, saving ${budget_diff:,.2f})")
        else:
            overrun = abs(budget_diff)
            failed_hards.append(f"Exceeds budget of ${budget:,.2f} by ${overrun:,.2f} (Total: ${total_cost:,.2f})")
    else:
        budget_diff = 0.0
        budget_diff_pct = 0.0
        budget_fit = False
        failed_hards.append("Price is unavailable; cannot verify budget compliance")

    # 3. Hard Requirement: Category Filter
    if preferences.category and preferences.category != "All":
        if product.category.lower() == preferences.category.lower():
            matched_hards.append(f"Matches category '{preferences.category}'")
        else:
            failed_hards.append(f"Category mismatch: item is in '{product.category}', not '{preferences.category}'")

    # 4. Hard Requirement: Shipping Cost Tolerance
    if preferences.max_shipping_cost is not None:
        if shipping_cost <= preferences.max_shipping_cost:
            matched_hards.append(f"Shipping fee (${shipping_cost:,.2f}) within ${preferences.max_shipping_cost:,.2f} limit")
        else:
            failed_hards.append(f"Shipping fee (${shipping_cost:,.2f}) exceeds maximum tolerance (${preferences.max_shipping_cost:,.2f})")

    # 5. Technical Specifications: RAM
    if preferences.min_ram_gb is not None:
        ram = extract_ram_gb(product)
        if ram is None:
            failed_hards.append(f"Missing specification: RAM capacity is unrecorded (requires ≥ {preferences.min_ram_gb}GB)")
            cautions_or_missing.append("RAM capacity not recorded in product specifications database")
        elif ram < preferences.min_ram_gb:
            failed_hards.append(f"RAM capacity ({ram}GB) is below required minimum of {preferences.min_ram_gb}GB")
        else:
            matched_hards.append(f"Satisfies RAM requirement ({ram}GB ≥ {preferences.min_ram_gb}GB)")

    # 6. Technical Specifications: Storage
    if preferences.min_storage_gb is not None:
        storage = extract_storage_gb(product)
        if storage is None:
            failed_hards.append(f"Missing specification: Storage capacity is unrecorded (requires ≥ {preferences.min_storage_gb}GB)")
            cautions_or_missing.append("Storage capacity not recorded in product specifications database")
        elif storage < preferences.min_storage_gb:
            failed_hards.append(f"Storage capacity ({storage}GB) is below required minimum of {preferences.min_storage_gb}GB")
        else:
            matched_hards.append(f"Satisfies Storage requirement ({storage}GB ≥ {preferences.min_storage_gb}GB)")

    # 7. Technical Specifications: Battery Run Time
    if preferences.min_battery_hours is not None:
        battery = extract_battery_hours(product)
        if battery is None:
            failed_hards.append(f"Missing specification: Battery runtime hours unrecorded (requires ≥ {preferences.min_battery_hours}h)")
            cautions_or_missing.append("Battery runtime in hours not recorded in database")
        elif battery < preferences.min_battery_hours:
            failed_hards.append(f"Battery runtime ({battery}h) is below required minimum of {preferences.min_battery_hours}h")
        else:
            matched_hards.append(f"Satisfies Battery runtime ({battery}h ≥ {preferences.min_battery_hours}h)")

    # 8. Technical Specifications: Discrete GPU
    if preferences.require_discrete_gpu:
        if has_discrete_gpu(product):
            matched_hards.append("Features dedicated discrete GPU")
        else:
            failed_hards.append("Product lacks a dedicated discrete GPU")
            cautions_or_missing.append("Discrete GPU not detected in hardware specifications")

    # 9. Technical Specifications: 4K Display
    if preferences.require_4k:
        if has_4k_display(product):
            matched_hards.append("Features 4K / Ultra HD resolution display")
        else:
            failed_hards.append("Product does not feature a 4K display")
            cautions_or_missing.append("4K resolution not detected in display specifications")

    # 10. Technical Specifications: Active Noise Cancellation (ANC)
    if preferences.require_anc:
        if has_anc(product):
            matched_hards.append("Features Active Noise Cancellation (ANC)")
        else:
            failed_hards.append("Product lacks Active Noise Cancellation (ANC)")
            cautions_or_missing.append("Active Noise Cancellation not supported or unrecorded")

    # =================================================================
    # Component Scoring (0 to 100 each)
    # =================================================================

    # Factor A: Use Case Suitability (40% weight)
    suitability_score, use_case_reasons = evaluate_use_case_suitability(product, preferences.use_case)

    # Factor B: Specification Excellence (30% weight)
    spec_score = 60.0
    ram_val = extract_ram_gb(product)
    if ram_val and ram_val >= 32:
        spec_score += 20.0
    elif ram_val and ram_val >= 16:
        spec_score += 10.0

    storage_val = extract_storage_gb(product)
    if storage_val and storage_val >= 1000:
        spec_score += 10.0
    elif storage_val and storage_val >= 512:
        spec_score += 5.0

    if has_4k_display(product):
        spec_score += 10.0
    if has_anc(product):
        spec_score += 10.0
    if has_discrete_gpu(product):
        spec_score += 15.0

    battery_val = extract_battery_hours(product)
    if battery_val and battery_val >= 24:
        spec_score += 10.0

    spec_score = min(100.0, spec_score)

    # Factor C: Budget Efficiency (20% weight)
    if total_cost is not None and budget > 0:
        if total_cost <= budget:
            # Rewards remaining headroom while ensuring the product is substantial
            headroom_ratio = (budget - total_cost) / budget
            budget_score = 60.0 + (headroom_ratio * 40.0)
        else:
            overrun_ratio = (total_cost - budget) / budget
            budget_score = max(0.0, 50.0 - (overrun_ratio * 100.0))
    else:
        budget_score = 0.0

    # Factor D: Brand Preference (10% weight)
    if not preferences.brand_preference or preferences.brand_preference == "All":
        if preferences.preferred_brands:
            if any(product.brand.lower() == b.lower() for b in preferences.preferred_brands):
                brand_score = 100.0
                use_case_reasons.append(f"Matches your saved preferred brand '{product.brand}'.")
            else:
                brand_score = 50.0
        else:
            brand_score = 100.0
    elif product.brand.lower() == preferences.brand_preference.lower():
        brand_score = 100.0
        use_case_reasons.append(f"Matches preferred brand '{product.brand}'.")
    else:
        brand_score = 40.0

    # Phase 7 Personalization: Preferred categories boost & explanation
    if preferences.preferred_categories and any(product.category.lower() == c.lower() for c in preferences.preferred_categories):
        suitability_score = min(100.0, suitability_score + 5.0)
        use_case_reasons.append(f"Matches your saved preferred category '{product.category}'.")

    # Phase 7 Personalization: Preferred store affinity
    if preferences.preferred_store_id and best_offer and best_offer.store_id == preferences.preferred_store_id:
        use_case_reasons.append(f"Available at your preferred store '{store_name}'.")

    # Phase 7 Personalization: Saved budget range verification
    if (
        preferences.user_saved_min_budget is not None
        and preferences.user_saved_max_budget is not None
        and total_cost is not None
    ):
        if preferences.user_saved_min_budget <= total_cost <= preferences.user_saved_max_budget:
            use_case_reasons.append(
                f"Within your saved budget range (${preferences.user_saved_min_budget:,.2f} - ${preferences.user_saved_max_budget:,.2f})."
            )

    # Composite Recommendation Score (0 to 100)
    rec_score = round(
        (0.40 * suitability_score)
        + (0.30 * spec_score)
        + (0.20 * budget_score)
        + (0.10 * brand_score),
        1
    )

    # Compile Score Breakdown
    breakdown = {
        "Suitability (40%)": round(suitability_score * 0.40, 1),
        "Specifications (30%)": round(spec_score * 0.30, 1),
        "Budget Efficiency (20%)": round(budget_score * 0.20, 1),
        "Brand Match (10%)": round(brand_score * 0.10, 1),
        "Composite Total": rec_score,
    }

    # =================================================================
    # Run Real Deal Detector Independently (Never merged into rec_score)
    # =================================================================
    deal_analysis: Optional[DealAnalysis] = None
    deal_score: Optional[int] = None
    deal_classification = "INSUFFICIENT DATA"
    is_good_val = False

    if best_offer and best_offer.price_history:
        deal_analysis = analyze_product_deal(
            product,
            target_offer=best_offer,
            reference_date=reference_date,
        )
        if deal_analysis:
            deal_score = deal_analysis.deal_score
            deal_classification = deal_analysis.deal_classification
            is_good_val = deal_analysis.is_good_value

            if deal_analysis.is_all_time_low:
                use_case_reasons.append(f"Selling at an All-Time Low price (${base_price:,.2f}) according to historical records.")
            elif deal_score and deal_score >= 80:
                use_case_reasons.append(f"Real Deal Score is {deal_score}/100 (EXCELLENT DEAL) based on recorded price cycles.")
            elif deal_score and deal_score >= 65:
                use_case_reasons.append(f"Real Deal Score is {deal_score}/100 (GOOD DEAL) with recorded markdown.")

            if deal_analysis.suspicious_discount.has_warning:
                cautions_or_missing.append(
                    f"Notice: Advertised strikethrough discount flagged: {deal_analysis.suspicious_discount.headline}"
                )
    else:
        cautions_or_missing.append("Historical price trail is unrecorded; Deal Score withheld to preserve integrity.")

    return ProductEvaluation(
        product=product,
        best_offer=best_offer,
        base_price=base_price,
        shipping_cost=shipping_cost,
        total_cost=total_cost,
        store_name=store_name,
        is_available=is_available,
        budget_fit=budget_fit,
        budget_difference=budget_diff,
        budget_difference_pct=budget_diff_pct,
        suitability_score=suitability_score,
        spec_score=spec_score,
        budget_score=budget_score,
        brand_score=brand_score,
        recommendation_score=rec_score,
        score_breakdown=breakdown,
        reasons=use_case_reasons,
        cautions_or_missing_specs=cautions_or_missing,
        matched_hard_requirements=matched_hards,
        failed_hard_requirements=failed_hards,
        deal_analysis=deal_analysis,
        deal_score=deal_score,
        deal_classification=deal_classification,
        is_good_value=is_good_val,
    )


# =====================================================================
# Main Recommendation Aggregator
# =====================================================================

def get_purchase_recommendations(
    preferences: AdvisorPreferences,
    custom_path: Optional[str] = None,
    reference_date: Optional[datetime] = None,
) -> RecommendationResult:
    """
    Main recommendation engine.
    Fetches candidate products from the database, evaluates every candidate,
    partitions into fully suitable candidates vs closest alternatives,
    and identifies:
      1. BEST OVERALL
      2. BEST BUDGET
      3. BEST CURRENT DEAL
    """
    # Fetch all candidate products with full historical price records
    category_filter = preferences.category if preferences.category != "All" else None
    products = get_products(
        category=category_filter,
        include_history=True,
        custom_path=custom_path,
    )

    all_evaluated: list[ProductEvaluation] = []
    suitable_candidates: list[ProductEvaluation] = []
    alternatives: list[ProductEvaluation] = []

    for product in products:
        eval_item = evaluate_product_for_advisor(
            product=product,
            preferences=preferences,
            reference_date=reference_date,
        )
        all_evaluated.append(eval_item)

        if eval_item.is_fully_suitable:
            suitable_candidates.append(eval_item)
        else:
            # Check if it qualifies as a 'closest alternative'
            # Allowed as alternative if it failed only budget (by <= 35%) OR failed only 1 spec
            if eval_item.is_available and eval_item.total_cost is not None:
                budget_overrun = eval_item.total_cost - preferences.budget
                overrun_pct = (budget_overrun / preferences.budget) * 100 if preferences.budget > 0 else 100.0
                if 0 < budget_overrun and overrun_pct <= 35.0:
                    alternatives.append(eval_item)
                elif len(eval_item.failed_hard_requirements) <= 2:
                    alternatives.append(eval_item)

    # Sort suitable candidates by priority preference or Recommendation Score
    if preferences.priority == "lowest_price":
        suitable_candidates.sort(key=lambda x: (x.total_cost if x.total_cost else float("inf"), -x.recommendation_score))
    elif preferences.priority == "best_deal":
        suitable_candidates.sort(key=lambda x: (x.deal_score or 0, x.recommendation_score), reverse=True)
    else:
        suitable_candidates.sort(key=lambda x: x.recommendation_score, reverse=True)

    # Sort alternatives by smallest budget overrun or lowest score deficit
    alternatives.sort(
        key=lambda x: (
            len(x.failed_hard_requirements),
            x.total_cost if x.total_cost else float("inf"),
        )
    )

    best_overall: Optional[ProductEvaluation] = None
    best_budget: Optional[ProductEvaluation] = None
    best_deal: Optional[ProductEvaluation] = None
    limitations: list[str] = []

    if suitable_candidates:
        # A. BEST OVERALL: Candidate with highest recommendation score
        best_overall = suitable_candidates[0]

        # B. BEST BUDGET: Suitable candidate that yields the highest budget savings (lowest total cost)
        # We prefer a distinct product from Best Overall if multiple candidates exist
        cheapest_candidate = min(suitable_candidates, key=lambda x: x.total_cost or float("inf"))
        if cheapest_candidate.product.id != best_overall.product.id:
            best_budget = cheapest_candidate
        elif len(suitable_candidates) > 1:
            # Best Overall is already the cheapest candidate!
            # Select the second lowest-cost candidate as an alternative budget option
            other_candidates = [c for c in suitable_candidates if c.product.id != best_overall.product.id]
            best_budget = min(other_candidates, key=lambda x: x.total_cost or float("inf"))
        else:
            # Only 1 candidate exists
            best_budget = cheapest_candidate
            limitations.append(
                "Only one product in the catalog met all criteria, so it qualifies as both Best Overall and Best Budget."
            )

        # C. BEST CURRENT DEAL: Candidate with strong Real Deal Score (>= 65, EXCELLENT DEAL or GOOD DEAL)
        # Must not be selected purely because it has the lowest price!
        deal_candidates = [
            c for c in suitable_candidates 
            if c.deal_score is not None and c.deal_score >= 65 and c.is_good_value
        ]
        deal_candidates.sort(key=lambda x: (x.deal_score or 0), reverse=True)

        if deal_candidates:
            # Try to pick a distinct product if possible
            distinct_deals = [
                d for d in deal_candidates 
                if d.product.id != best_overall.product.id and (not best_budget or d.product.id != best_budget.product.id)
            ]
            if distinct_deals:
                best_deal = distinct_deals[0]
            else:
                best_deal = deal_candidates[0]
        else:
            limitations.append(
                "No candidate product currently possesses a verified Good Deal or Excellent Deal rating in historical price tracking."
            )

        summary = (
            f"Evaluated {len(products)} products against ${preferences.budget:,.2f} budget and '{preferences.use_case}' criteria. "
            f"Found {len(suitable_candidates)} fully compliant options."
        )

    else:
        summary = (
            f"No products in the catalog satisfied all hard requirements for your budget (${preferences.budget:,.2f}) "
            f"and '{preferences.use_case}' criteria. Showing closest alternative options below."
        )
        limitations.append("All products in the selected category either exceeded budget or missed required specifications.")

    return RecommendationResult(
        preferences=preferences,
        best_overall=best_overall,
        best_budget=best_budget,
        best_deal=best_deal,
        ranked_candidates=suitable_candidates,
        closest_alternatives=alternatives[:3],  # top 3 closest alternatives
        all_evaluated=all_evaluated,
        summary_explanation=summary,
        limitations=limitations,
    )

