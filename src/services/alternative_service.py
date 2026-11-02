"""Cheapest Alternative Recommendation Service for PriceWise AI Beauty (Phase 2).

Recommends lower-priced alternatives based on:
- Matching product category or intended use
- Shared active ingredients and formulation
- Skin-type suitability alignment
- Verified price difference and percentage savings

IMPORTANT: Products are NEVER described as identical or equivalent without verified clinical proof.
Every recommendation provides an explainable breakdown of the exact attributes compared.
"""

from dataclasses import dataclass, field
from typing import Optional
from src.database.models import Product
from src.services.product_service import get_products, get_product_by_id
from src.services.product_matching_service import parse_quantity_volume


@dataclass
class AlternativeRecommendation:
    original_product: Product
    alternative_product: Product
    price_difference: float
    percentage_savings: float
    shared_ingredients: list[str] = field(default_factory=list)
    matching_attributes: list[str] = field(default_factory=list)
    similarity_explanation: str = ""
    cost_per_unit_comparison: str = ""
    original_cost_per_unit: Optional[float] = None
    alternative_cost_per_unit: Optional[float] = None
    cost_per_unit_savings: Optional[float] = None
    cost_per_unit_savings_pct: Optional[float] = None
    unit_name: Optional[str] = None
    cost_per_unit_label: str = ""


def _extract_ingredient_set(product: Product) -> set[str]:
    """Extract normalized ingredient terms from product specs."""
    raw_ingredients = product.specs.get("Key Ingredients", "")
    if isinstance(raw_ingredients, list):
        terms = [t.strip().lower() for t in raw_ingredients if t and t.strip()]
    elif isinstance(raw_ingredients, str):
        # Split by comma or bullet
        terms = [t.strip().lower() for t in raw_ingredients.replace("•", ",").split(",") if t.strip()]
    else:
        terms = []
    return set(terms)


def _extract_skin_types(product: Product) -> set[str]:
    """Extract normalized skin types from product specs."""
    raw_st = product.specs.get("Skin Type", "")
    if isinstance(raw_st, list):
        return {st.strip().lower() for st in raw_st if st.strip()}
    elif isinstance(raw_st, str):
        return {st.strip().lower() for st in raw_st.split(",") if st.strip()}
    return set()


def get_cheapest_alternatives(
    product: Product,
    all_candidates: Optional[list[Product]] = None,
    max_results: int = 3,
    custom_path: Optional[str] = None,
) -> list[AlternativeRecommendation]:
    """
    Identify and rank lower-priced alternatives for a given product.
    
    Evaluates:
    - Same category
    - Ingredient overlap
    - Formulation / Product Type alignment
    - Skin suitability
    - Price difference > 0 (Alternative must be genuinely cheaper)
    """
    target_price = product.lowest_price
    if target_price is None or target_price <= 0:
        return []

    if all_candidates is None:
        all_candidates = get_products(custom_path=custom_path)

    target_ingredients = _extract_ingredient_set(product)
    target_skin_types = _extract_skin_types(product)
    target_type = str(product.specs.get("Product Type", "")).strip().lower()
    target_finish = str(product.specs.get("Finish", "")).strip().lower()
    target_category = (product.category or "").strip().lower()

    recommendations: list[AlternativeRecommendation] = []

    for candidate in all_candidates:
        if candidate.id == product.id or candidate.sku == product.sku:
            continue

        cand_price = candidate.lowest_price
        if cand_price is None or cand_price <= 0:
            continue

        # Must be strictly cheaper to qualify as an alternative
        if cand_price >= target_price:
            continue

        cand_category = (candidate.category or "").strip().lower()
        cand_ingredients = _extract_ingredient_set(candidate)
        cand_skin_types = _extract_skin_types(candidate)
        cand_type = str(candidate.specs.get("Product Type", "")).strip().lower()
        cand_finish = str(candidate.specs.get("Finish", "")).strip().lower()

        # Score relevance
        matching_attrs = []
        is_same_category = (cand_category == target_category)
        if is_same_category:
            matching_attrs.append(f"Category: {candidate.category}")

        shared_ings = [
            ing.title() for ing in target_ingredients.intersection(cand_ingredients)
        ]
        if shared_ings:
            matching_attrs.append(f"Shared Actives: {', '.join(shared_ings[:3])}")

        if target_type and cand_type and (target_type in cand_type or cand_type in target_type):
            matching_attrs.append(f"Formulation: {candidate.specs.get('Product Type')}")

        if target_finish and cand_finish and (target_finish in cand_finish or cand_finish in target_finish):
            matching_attrs.append(f"Finish: {candidate.specs.get('Finish')}")

        shared_skin = target_skin_types.intersection(cand_skin_types)
        if shared_skin:
            matching_attrs.append("Skin Suitability: Matching Profile")

        # Must have at least category match OR active ingredient overlap to be considered an alternative
        if not is_same_category and not shared_ings:
            continue

        price_diff = round(target_price - cand_price, 2)
        pct_savings = round((price_diff / target_price) * 100, 1)

        # Build transparent explanation
        explanation_parts = []
        if shared_ings:
            explanation_parts.append(f"Shares key ingredients ({', '.join(shared_ings[:3])})")
        if target_finish and target_finish == cand_finish:
            explanation_parts.append(f"similar {cand_finish} finish")
        elif is_same_category:
            explanation_parts.append(f"similar intended use in {candidate.category}")
        explanation_parts.append(f"saves ₹{price_diff:,.0f} ({pct_savings:.0f}% cheaper)")

        explanation = f"Affordable alternative: {'; '.join(explanation_parts)}."

        # Unit cost comparison
        target_qty_str = str(product.specs.get("Net Quantity") or product.specs.get("Size") or "")
        cand_qty_str = str(candidate.specs.get("Net Quantity") or candidate.specs.get("Size") or "")
        t_val, t_unit = parse_quantity_volume(target_qty_str)
        c_val, c_unit = parse_quantity_volume(cand_qty_str)

        orig_cpu: Optional[float] = None
        alt_cpu: Optional[float] = None
        cpu_savings: Optional[float] = None
        cpu_savings_pct: Optional[float] = None
        unit_name: Optional[str] = None
        cost_unit_comp = f"Target ({target_qty_str}) @ ₹{target_price:.0f} vs Alternative ({cand_qty_str}) @ ₹{cand_price:.0f}"
        cpu_label = ""

        if t_val and c_val and t_val > 0 and c_val > 0 and t_unit == c_unit:
            unit_name = t_unit
            orig_cpu = round(target_price / t_val, 2)
            alt_cpu = round(cand_price / c_val, 2)
            cpu_savings = round(orig_cpu - alt_cpu, 2)
            if orig_cpu > 0:
                cpu_savings_pct = round(((orig_cpu - alt_cpu) / orig_cpu) * 100, 1)
            cost_unit_comp = (
                f"₹{alt_cpu:.2f}/{unit_name} vs ₹{orig_cpu:.2f}/{unit_name} "
                f"(Saves ₹{cpu_savings:.2f}/{unit_name}, {cpu_savings_pct:.0f}% cheaper per unit)"
            )
            cpu_label = f"₹{alt_cpu:.2f}/{unit_name} vs ₹{orig_cpu:.2f}/{unit_name}"

        recommendations.append(
            AlternativeRecommendation(
                original_product=product,
                alternative_product=candidate,
                price_difference=price_diff,
                percentage_savings=pct_savings,
                shared_ingredients=shared_ings,
                matching_attributes=matching_attrs,
                similarity_explanation=explanation,
                cost_per_unit_comparison=cost_unit_comp,
                original_cost_per_unit=orig_cpu,
                alternative_cost_per_unit=alt_cpu,
                cost_per_unit_savings=cpu_savings,
                cost_per_unit_savings_pct=cpu_savings_pct,
                unit_name=unit_name,
                cost_per_unit_label=cpu_label,
            )
        )

    # Sort by relevance: percentage savings & number of matching attributes
    recommendations.sort(
        key=lambda r: (len(r.shared_ingredients) > 0, len(r.matching_attributes), r.percentage_savings),
        reverse=True,
    )

    return recommendations[:max_results]

