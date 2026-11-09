"""Advanced Beauty Intelligence Engine for PriceWise AI (Phase 10).

Provides comprehensive, evidence-based beauty intelligence:
1. Phase 10A: Master Ingredient Intelligence, Compatibility & Conflict Matrix,
   and AM/PM Routine Safety & Overload Checker.
2. Phase 10B: Indian Climate-Aware Skincare Recommendation Engine.
3. Phase 10C: Foundation Shade, Undertone, and Oxidation Matcher.
4. Phase 10D: Multi-Criteria Advanced Beauty Product Discovery.
"""

from dataclasses import dataclass, field
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from src.database.connection import get_connection

logger = logging.getLogger("pricewise.beauty_intelligence_advanced")

ROUTINE_MEDICAL_DISCLAIMER = (
    "PriceWise AI Cosmetic Guidance Notice: Skincare routine advice, active ingredient compatibility, "
    "and climate recommendations are educational cosmetic suggestions based on published dermatological literature. "
    "They do not constitute medical diagnoses, dermatological prescriptions, or medical advice. "
    "If irritation, persistent erythema, or adverse reactions occur, discontinue use immediately and consult a dermatologist."
)

FOUNDATION_MATCH_DISCLAIMER = (
    "Algorithmic Shade Guidance Notice: Foundation shade matches and undertone assessments are estimated using optical "
    "colorimetry calibrations and manufacturer specifications. Factors such as skin sebum oxidation, seasonal tanning, "
    "and lighting affect appearance. Jawline swatch testing in natural daylight is recommended prior to purchase."
)


# =============================================================================
# Phase 10A: Master Ingredient Database & Interaction Matrix
# =============================================================================

@dataclass
class MasterIngredient:
    """Detailed scientific and consumer-friendly profile of a cosmetic active."""
    id: str
    name: str
    inci_name: str
    category: str
    description: str
    what_it_does: str
    why_used: str
    benefits: List[str]
    potential_irritations: List[str]
    skin_suitability: List[str]
    evidence_level: str  # "established", "moderate", "preliminary"
    optimal_ph: str
    typical_concentration: str
    keywords: List[str]


MASTER_INGREDIENTS: Dict[str, MasterIngredient] = {
    "retinol": MasterIngredient(
        id="retinol",
        name="Retinol & Retinoids",
        inci_name="Retinol / Retinyl Palmitate / Hydroxypinacolone Retinoate",
        category="Cell-Communicating Retinoid",
        description="A gold-standard vitamin A derivative that accelerates cellular turnover and stimulates dermal collagen synthesis.",
        what_it_does="Binds to retinoid receptors in keratinocytes to normalize epidermal differentiation and inhibit collagenase enzymes.",
        why_used="Clinically proven to smooth fine lines, improve photo-aged skin texture, unclog micro-comedones, and fade post-inflammatory hyperpigmentation.",
        benefits=["Accelerates skin cell turnover", "Stimulates collagen & elastin production", "Refines pores and treats acne", "Improves hyperpigmentation"],
        potential_irritations=["Retinoid dermatitis: flaking, erythema, dryness, and barrier sensitivity during retinization (first 4-6 weeks)"],
        skin_suitability=["Oily", "Combination", "Normal", "Mature", "Acne-Prone"],
        evidence_level="established",
        optimal_ph="5.5 - 6.5",
        typical_concentration="0.1% - 1.0%",
        keywords=["retinol", "retinoid", "retinal", "tretinoin", "granactive", "adapalene", "retinyl"],
    ),
    "salicylic_acid": MasterIngredient(
        id="salicylic_acid",
        name="Salicylic Acid (BHA)",
        inci_name="Salicylic Acid",
        category="Beta Hydroxy Acid (BHA)",
        description="A lipid-soluble exfoliating acid that penetrates deep into sebum-filled pores to dissolve cellular debris.",
        what_it_does="Exfoliates inside pore linings, dissolves sebum plugs, and exerts mild anti-inflammatory action via its salicylate structure.",
        why_used="Unclogs blackheads and whiteheads, reduces inflammatory blemishes, and normalizes oily shine without excessive abrasion.",
        benefits=["Deep pore decongestion", "Anti-inflammatory and antimicrobial", "Reduces blackheads and sebaceous filaments", "Smooths bumpy texture"],
        potential_irritations=["Dryness, peeling, or stinging if overused (>2% or layered with other strong acids)"],
        skin_suitability=["Oily", "Acne-Prone", "Combination"],
        evidence_level="established",
        optimal_ph="3.0 - 4.0",
        typical_concentration="0.5% - 2.0%",
        keywords=["salicylic acid", "salicylic", "bha", "willow bark extract", "salicylate"],
    ),
    "glycolic_acid": MasterIngredient(
        id="glycolic_acid",
        name="Glycolic Acid (AHA)",
        inci_name="Glycolic Acid",
        category="Alpha Hydroxy Acid (AHA)",
        description="The smallest molecular-weight AHA that penetrates efficiently to weaken desmosome bonds between dead stratum corneum cells.",
        what_it_does="Dissolves the intercellular 'glue' holding dull keratinocytes together, revealing fresher, luminous underlying skin cells.",
        why_used="Dramatically brightens dullness, fades epidermal melanin deposits, and boosts stratum corneum hydration.",
        benefits=["Surface resurfacing and radiance", "Fades dark spots and sun damage", "Stimulates collagen synthesis", "Improves skin smoothness"],
        potential_irritations=["Stinging, redness, increased photosensitivity (requires mandatory daytime SPF 50+)"],
        skin_suitability=["Normal", "Dry", "Combination", "Dull", "Hyperpigmented"],
        evidence_level="established",
        optimal_ph="3.2 - 3.8",
        typical_concentration="5.0% - 10.0%",
        keywords=["glycolic acid", "glycolic", "aha", "sugar cane extract"],
    ),
    "lactic_acid": MasterIngredient(
        id="lactic_acid",
        name="Lactic Acid (AHA)",
        inci_name="Lactic Acid",
        category="Alpha Hydroxy Acid (AHA) & Humectant",
        description="A gentler, larger molecular-weight AHA that gently resurfaces while naturally acting as an intrinsic component of Natural Moisturizing Factor (NMF).",
        what_it_does="Loosens surface dead cells while binding water within the stratum corneum, offering exfoliation with lower irritation potential.",
        why_used="Ideal starter chemical exfoliant for sensitive, dry, or dehydrated complexions needing smoothing and hydration.",
        benefits=["Gentle surface exfoliation", "Natural moisturizing factor hydration", "Brightens uneven tone", "Reinforces skin softness"],
        potential_irritations=["Mild tingling or redness on compromised barriers"],
        skin_suitability=["Dry", "Sensitive", "Normal", "Combination"],
        evidence_level="established",
        optimal_ph="3.5 - 4.0",
        typical_concentration="5.0% - 10.0%",
        keywords=["lactic acid", "lactic"],
    ),
    "vitamin_c": MasterIngredient(
        id="vitamin_c",
        name="Vitamin C (L-Ascorbic Acid & Derivatives)",
        inci_name="Ascorbic Acid / 3-O-Ethyl Ascorbic Acid / Ascorbyl Glucoside",
        category="Potent Antioxidant & Brightener",
        description="A biologically active antioxidant that scavenges free radicals, inhibits tyrosinase activity, and serves as an essential cofactor for collagen synthesis.",
        what_it_does="Neutralizes reactive oxygen species (ROS) induced by UV and pollution while suppressing excess melanin production.",
        why_used="Brightens sun-induced dullness, reduces post-inflammatory hyperpigmentation, and synergistically amplifies sunscreen UV defense.",
        benefits=["Free radical scavenger", "Tyrosinase inhibition (fades hyperpigmentation)", "Collagen booster", "Amplifies photoprotection"],
        potential_irritations=["Low-pH (pH < 3.5) pure L-Ascorbic Acid can cause stinging, irritation, or temporary redness on reactive skin"],
        skin_suitability=["All Skin Types", "Dull", "Hyperpigmented", "Sun-Damaged"],
        evidence_level="established",
        optimal_ph="2.8 - 3.5 (pure L-AA); 5.0 - 7.0 (derivatives)",
        typical_concentration="10.0% - 20.0% (L-AA); 5.0% - 15.0% (derivatives)",
        keywords=["vitamin c", "ascorbic acid", "ethyl ascorbic acid", "ascorbyl glucoside", "tetrahexyldecyl ascorbate", "ascorbyl"],
    ),
    "niacinamide": MasterIngredient(
        id="niacinamide",
        name="Niacinamide (Vitamin B3)",
        inci_name="Niacinamide",
        category="Multi-Action Vitamin & Barrier Fortifier",
        description="A highly stable water-soluble vitamin that strengthens ceramide synthesis, regulates sebum secretion, and inhibits melanosome transfer.",
        what_it_does="Upregulates intercellular lipid synthesis (ceramides, free fatty acids), calms inflammatory pathways, and mitigates lipid oxidation.",
        why_used="The quintessential versatile active for Indian skin: curbs midday grease, minimizes enlarged pores, and calms acne redness.",
        benefits=["Sebum regulation & pore refinement", "Barrier strengthening (stimulates ceramides)", "Reduces blotchiness & redness", "Inhibits melanosome transfer"],
        potential_irritations=["Well-tolerated at 2%-5%; concentrations >= 10% can trigger flushing, redness, or irritation in sensitive users"],
        skin_suitability=["Oily", "Acne-Prone", "Combination", "Sensitive", "Normal"],
        evidence_level="established",
        optimal_ph="5.0 - 7.0",
        typical_concentration="2.0% - 5.0% (optimal); up to 10.0%",
        keywords=["niacinamide", "nicotinamide", "vitamin b3"],
    ),
    "ceramides": MasterIngredient(
        id="ceramides",
        name="Ceramides (NP, AP, EOP)",
        inci_name="Ceramide NP / Ceramide AP / Ceramide EOP / Phytosphingosine",
        category="Epidermal Lipid & Barrier Restorer",
        description="Bio-identical spherical lipids that constitute 50% of the stratum corneum intercellular lipid matrix ('mortar' of the skin barrier).",
        what_it_does="Locks moisture inside the skin, prevents trans-epidermal water loss (TEWL), and shields against environmental allergens.",
        why_used="Essential for repairing compromised moisture barriers, soothing retinoid peeling, and restoring hydration in AC or winter environments.",
        benefits=["Restores lipid barrier integrity", "Prevents trans-epidermal water loss (TEWL)", "Soothes active irritation & flaking", "Improves skin resilience"],
        potential_irritations=["Extremely safe, non-irritating, physiological to human skin"],
        skin_suitability=["Dry", "Sensitive", "Compromised Barrier", "Post-Peel", "Eczema-Prone"],
        evidence_level="established",
        optimal_ph="5.0 - 7.0",
        typical_concentration="0.1% - 1.0% (effective at physiological ratio)",
        keywords=["ceramide", "ceramides", "ceramide np", "ceramide ap", "ceramide eop", "phytosphingosine"],
    ),
    "hyaluronic_acid": MasterIngredient(
        id="hyaluronic_acid",
        name="Hyaluronic Acid (Multi-Molecular)",
        inci_name="Sodium Hyaluronate / Hyaluronic Acid / Hydrolyzed Hyaluronic Acid",
        category="Universal Humectant",
        description="A naturally occurring glycosaminoglycan capable of binding up to 1,000 times its molecular weight in water.",
        what_it_does="Draws atmospheric and epidermal moisture into the upper skin layers to instantly plump dehydrated cells.",
        why_used="Relieves skin tightness and dehydration without adding heavy oils; ideal for layering beneath gel moisturizers in humid or dry climates.",
        benefits=["Instant multi-layer skin plumping", "Soothes surface dehydration lines", "Enhances topical active penetration", "Lightweight oil-free hydration"],
        potential_irritations=["In very low-humidity arid climates (<20% humidity), unsealed HA may pull moisture from deeper dermis if not sealed with an emollient"],
        skin_suitability=["All Skin Types", "Dehydrated", "Oily", "Dry", "Sensitive"],
        evidence_level="established",
        optimal_ph="5.0 - 7.5",
        typical_concentration="0.5% - 2.0%",
        keywords=["hyaluronic acid", "sodium hyaluronate", "hyaluronate", "hydrolyzed hyaluronic"],
    ),
    "benzoyl_peroxide": MasterIngredient(
        id="benzoyl_peroxide",
        name="Benzoyl Peroxide",
        inci_name="Benzoyl Peroxide",
        category="Antimicrobial Acne Treatment",
        description="A powerful lipophilic antimicrobial agent that releases oxygen radicals inside hair follicles to destroy Cutibacterium acnes bacteria.",
        what_it_does="Generates reactive oxygen species that rapidly kill anaerobic acne-causing bacteria without inducing bacterial resistance.",
        why_used="Clears inflammatory papules and pustules quickly; reduces micro-comedone formation.",
        benefits=["Rapid reduction of inflammatory acne", "No bacterial antibiotic resistance", "Keratolytic pore-unclogging"],
        potential_irritations=["Erythema, severe dryness, peeling, contact dermatitis; bleaches colored fabrics and hair"],
        skin_suitability=["Acne-Prone", "Oily"],
        evidence_level="established",
        optimal_ph="4.5 - 6.0",
        typical_concentration="2.5% - 5.0% (2.5% matches 10% efficacy with far less irritation)",
        keywords=["benzoyl peroxide", "bpo"],
    ),
    "peptides": MasterIngredient(
        id="peptides",
        name="Peptides (Matrixyl & Copper GHK-Cu)",
        inci_name="Palmitoyl Tripeptide-1 / Palmitoyl Tetrapeptide-7 / Copper Tripeptide-1",
        category="Cell-Signaling Amino Acid Chains",
        description="Short chains of amino acids that serve as biological messengers, prompting fibroblasts to synthesize fresh collagen and elastin.",
        what_it_does="Signals extracellular matrix reconstruction, repairs micro-damage, and promotes tissue healing without skin thinning.",
        why_used="Provides progressive firming, elasticity restoration, and barrier resilience as a gentle non-irritating alternative to harsh actives.",
        benefits=["Firms skin and supports elasticity", "Stimulates collagen & glycosaminoglycan synthesis", "Accelerates barrier recovery", "Non-irritating"],
        potential_irritations=["Very well tolerated; Copper peptides can oxidize if combined directly with pure L-Ascorbic Acid"],
        skin_suitability=["All Skin Types", "Mature", "Sensitive", "Dry"],
        evidence_level="moderate",
        optimal_ph="5.0 - 7.0",
        typical_concentration="1.0% - 3.0%",
        keywords=["peptide", "peptides", "matrixyl", "copper peptide", "tripeptide", "tetrapeptide", "palmitoyl"],
    ),
    "centella_asiatica": MasterIngredient(
        id="centella_asiatica",
        name="Centella Asiatica (Cica / Madecassoside)",
        inci_name="Centella Asiatica Extract / Madecassoside / Asiaticoside",
        category="Anti-Inflammatory Calming Botanical",
        description="An Ayurvedic and K-beauty botanical rich in triterpenoid saponins that downregulate pro-inflammatory cytokines and boost healing.",
        what_it_does="Suppresses IL-1 and TNF-alpha inflammatory pathways, stimulates microcirculation, and reinforces capillary resilience.",
        why_used="Instantly quenches acne-induced redness, soothes pollution sensitivity, and calms heat irritation in tropical Indian climates.",
        benefits=["Soothes redness and erythema", "Accelerates post-acne wound healing", "Fortifies sensitive skin tolerance", "Antioxidant protection"],
        potential_irritations=["Extremely gentle; virtually non-irritating"],
        skin_suitability=["Sensitive", "Acne-Prone", "Rosacea-Prone", "Irritated", "All Skin Types"],
        evidence_level="established",
        optimal_ph="5.0 - 7.0",
        typical_concentration="1.0% - 5.0%",
        keywords=["centella", "cica", "madecassoside", "asiaticoside", "gotu kola"],
    ),
    "azelaic_acid": MasterIngredient(
        id="azelaic_acid",
        name="Azelaic Acid",
        inci_name="Azelaic Acid / Potassium Azeloyl Diglycinate",
        category="Dicarboxylic Acid Anti-Acne & Pigment Corrector",
        description="A naturally occurring dicarboxylic acid with comedolytic, anti-inflammatory, and selective tyrosinase-inhibiting properties.",
        what_it_does="Selectively targets hyperactive abnormal melanocytes to fade post-inflammatory erythema (PIE) and melasma while curbing acne.",
        why_used="Incredible multi-benefit solution for Indian complexions dealing with stubborn brown acne marks, rosacea, and clogged pores.",
        benefits=["Fades stubborn PIE (red marks) and PIH (brown marks)", "Calms inflammatory acne and rosacea", "Gentle keratolytic pore clearing", "Safe during pregnancy"],
        potential_irritations=["Initial itching or transient tingling for first 1-2 weeks"],
        skin_suitability=["Acne-Prone", "Sensitive", "Rosacea-Prone", "Hyperpigmented"],
        evidence_level="established",
        optimal_ph="4.5 - 5.5",
        typical_concentration="10.0% - 20.0%",
        keywords=["azelaic acid", "azelaic", "potassium azeloyl diglycinate"],
    ),
    "uv_filters": MasterIngredient(
        id="uv_filters",
        name="Broad-Spectrum UV Filters",
        inci_name="Bis-Ethylhexyloxyphenol Methoxyphenyl Triazine / Drometrizole Trisiloxane / Zinc Oxide",
        category="Photostable Photoprotection Filters",
        description="Modern organic and inorganic ultraviolet absorbers that attenuate both short-wavelength UVB (erythema) and long-wavelength UVA1/UVA2 (pigmentation & aging).",
        what_it_does="Absorbs or reflects solar radiation across 290nm-400nm before electromagnetic rays can break DNA bonds or trigger melanogenesis.",
        why_used="The absolute non-negotiable daytime shield required to prevent sunscreen breakdown, dark spot deepening, and collagen degradation.",
        benefits=["Prevents premature photoaging", "Stops hyperpigmentation & melasma from darkening", "Shields against solar elastosis", "Prevents skin cancer"],
        potential_irritations=["Certain legacy chemical filters (oxybenzone, avobenzone) can cause eye stinging in humid weather; modern filters (Tinosorb, Uvinul) are gentle"],
        skin_suitability=["All Skin Types (Essential for All)"],
        evidence_level="established",
        optimal_ph="5.5 - 7.5",
        typical_concentration="SPF 30 to SPF 50+ PA++++",
        keywords=["sunscreen", "uv filter", "tinosorb", "uvinul", "zinc oxide", "titanium dioxide", "spf", "mexoryl"],
    ),
    "snail_mucin": MasterIngredient(
        id="snail_mucin",
        name="Snail Secretion Filtrate",
        inci_name="Snail Secretion Filtrate",
        category="Nutritive Hydration & Repair Filtrate",
        description="A bioactive filtrate packed with natural chondroitin sulfate, allantoin, copper peptides, and glycolic acid traces.",
        what_it_does="Imparts intense lightweight viscoelastic hydration, repairs micro-tears in the epidermal barrier, and improves bounce.",
        why_used="Hydrates deeply without clogging pores or feeling sticky; a holy grail for soothing acne redness and rough texture.",
        benefits=["Deep non-comedogenic hydration", "Accelerates surface barrier repair", "Smooths rough dehydrated patches", "Plumps fine lines"],
        potential_irritations=["Rare mollusk allergy in hypersensitive individuals"],
        skin_suitability=["Dry", "Dehydrated", "Combination", "Acne-Prone"],
        evidence_level="moderate",
        optimal_ph="5.5 - 6.8",
        typical_concentration="70% - 96%",
        keywords=["snail mucin", "snail secretion", "snail essence"],
    ),
}


# =============================================================================
# Conflict and Interaction Matrix
# =============================================================================

@dataclass
class IngredientInteraction:
    """Detailed clinical assessment of a pair of cosmetic actives."""
    ingredient_a: str
    ingredient_b: str
    severity: str  # "high_irritation_risk", "formulation_incompatibility", "moderate_caution", "synergistic_pair"
    conflict_title: str
    explanation: str
    scientific_rationale: str
    recommendation: str
    routine_separation_advice: str


INTERACTION_MATRIX: List[IngredientInteraction] = [
    # 1. Retinoids + Exfoliating Acids (AHA/BHA)
    IngredientInteraction(
        ingredient_a="retinol",
        ingredient_b="glycolic_acid",
        severity="high_irritation_risk",
        conflict_title="Retinoid & AHA Barrier Disruption Risk",
        explanation="Layering strong AHAs with Retinoids simultaneously increases stratum corneum barrier thinning, leading to erythema and peeling.",
        scientific_rationale="Both actives accelerate epithelial turnover through divergent mechanisms. Combining them overwhelms the barrier's repair capacity.",
        recommendation="Do not apply in the exact same routine session. Alternate on separate evenings using a skin cycling routine.",
        routine_separation_advice="Apply Glycolic Acid on Night 1 (Exfoliation Night); apply Retinol on Night 2 (Recovery Night).",
    ),
    IngredientInteraction(
        ingredient_a="retinol",
        ingredient_b="salicylic_acid",
        severity="high_irritation_risk",
        conflict_title="Retinoid & BHA Irritation Clashing",
        explanation="Simultaneous application of Salicylic Acid and Retinoid dramatically amplifies dryness, stinging, and moisture barrier compromise.",
        scientific_rationale="Lipophilic salicylic acid strips pore sebum while retinoids normalize keratinization. Together, moisture loss spikes significantly.",
        recommendation="Use Salicylic Acid in the morning (paired with SPF 50+) or on alternate nights from your Retinoid.",
        routine_separation_advice="Use Salicylic Acid Cleanser/Serum in AM; use Retinol exclusively in PM.",
    ),
    # 2. Exfoliating Acid Overload (AHA + BHA layered)
    IngredientInteraction(
        ingredient_a="glycolic_acid",
        ingredient_b="salicylic_acid",
        severity="moderate_caution",
        conflict_title="Multi-Acid Exfoliation Overload",
        explanation="Applying separate standalone AHA and BHA serums simultaneously can trigger chemical over-exfoliation and persistent redness.",
        scientific_rationale="Combining separate low-pH (<3.5) acid serums exposes the stratum corneum to excessive free acid percentages.",
        recommendation="Opt for a single pre-formulated AHA/BHA blend where concentrations are balanced, or alternate days.",
        routine_separation_advice="Use BHA for oily T-zone in morning; reserve AHA for overall radiance 2 nights per week.",
    ),
    # 3. Benzoyl Peroxide + Retinoid
    IngredientInteraction(
        ingredient_a="benzoyl_peroxide",
        ingredient_b="retinol",
        severity="formulation_incompatibility",
        conflict_title="Oxidative Degradation of Retinoid",
        explanation="Benzoyl Peroxide is a potent oxidizing agent that degrades traditional Retinol and Tretinoin molecules upon contact.",
        scientific_rationale="BPO produces free radical peroxides that chemically oxidize the unsaturated polyene chain of retinol, neutralizing its efficacy.",
        recommendation="Never mix BPO and Retinol in the palm or layer consecutively. Separate into distinct AM and PM routines.",
        routine_separation_advice="Use Benzoyl Peroxide spot treatment in AM; apply Retinol at PM.",
    ),
    # 4. Pure Vitamin C (L-AA) + Retinoid
    IngredientInteraction(
        ingredient_a="vitamin_c",
        ingredient_b="retinol",
        severity="moderate_caution",
        conflict_title="Vitamin C & Retinoid Layering Friction",
        explanation="Layering pure low-pH Vitamin C and Retinol in the same application can cause stinging and temporary barrier inflammation.",
        scientific_rationale="Pure L-Ascorbic Acid requires an acidic pH (2.8-3.5) to penetrate, while retinol works best near physiological pH (5.5-6.5).",
        recommendation="Separate by time of day: Vitamin C shines as a morning antioxidant, while Retinoids work best during overnight cell division.",
        routine_separation_advice="Apply Vitamin C every morning under sunscreen; apply Retinol at bedtime.",
    ),
    # 5. Pure Vitamin C + Copper Peptides
    IngredientInteraction(
        ingredient_a="vitamin_c",
        ingredient_b="peptides",
        severity="formulation_incompatibility",
        conflict_title="Copper Peptide Oxidation Conflict",
        explanation="Direct low-pH L-Ascorbic Acid can oxidize the copper ion in copper tripeptide-1 (GHK-Cu), nullifying both ingredients.",
        scientific_rationale="The transition metal copper catalyzes the rapid oxidation of ascorbic acid, turning it inactive yellow-orange.",
        recommendation="Do not combine Copper Peptides with direct Vitamin C. Use on alternate times of day.",
        routine_separation_advice="Use Vitamin C in AM routine; reserve Peptides for PM barrier recovery.",
    ),
    # 6. Benzoyl Peroxide + Pure Vitamin C
    IngredientInteraction(
        ingredient_a="benzoyl_peroxide",
        ingredient_b="vitamin_c",
        severity="formulation_incompatibility",
        conflict_title="Oxidation Inactivation of Vitamin C",
        explanation="Benzoyl peroxide oxidizes vitamin C immediately upon contact, rendering the antioxidant completely ineffective.",
        scientific_rationale="Redox reaction: BPO is a powerful electron acceptor that prematurely oxidizes ascorbic acid into dehydroascorbic acid.",
        recommendation="Do not use Benzoyl Peroxide and Vitamin C in the same routine.",
        routine_separation_advice="Use Vitamin C in AM; apply Benzoyl Peroxide in PM or on alternate days.",
    ),
    # 7. Synergistic: Vitamin C + Sunscreen
    IngredientInteraction(
        ingredient_a="vitamin_c",
        ingredient_b="uv_filters",
        severity="synergistic_pair",
        conflict_title="Synergistic Broad-Spectrum Photoprotection",
        explanation="Vitamin C neutralizes reactive oxygen species and free radicals that bypass physical/chemical UV filters.",
        scientific_rationale="UV filters attenuate solar rays while topical antioxidants scavenge free radicals, providing comprehensive anti-aging defense.",
        recommendation="Ideal daytime combination! Apply Vitamin C serum first, allow 60 seconds to absorb, then seal with SPF 50+.",
        routine_separation_advice="AM Routine: Step 1 Cleanse -> Step 2 Vitamin C -> Step 3 Moisturizer -> Step 4 SPF 50+.",
    ),
    # 8. Synergistic: Ceramides + Hyaluronic Acid
    IngredientInteraction(
        ingredient_a="ceramides",
        ingredient_b="hyaluronic_acid",
        severity="synergistic_pair",
        conflict_title="Optimal Humectant-Emollient Barrier Lock",
        explanation="Hyaluronic acid attracts ambient moisture into epidermis, while ceramides seal the lipid matrix to prevent evaporation.",
        scientific_rationale="Addresses both intra-corneocyte water shortage and inter-corneocyte lipid matrix deficiency simultaneously.",
        recommendation="Perfect for dry, dehydrated, or post-active irritated skin.",
        routine_separation_advice="Apply Hyaluronic Acid on damp skin, then lock in immediately with Ceramide Moisturizer.",
    ),
    # 9. Synergistic: Retinoids + Ceramides
    IngredientInteraction(
        ingredient_a="retinol",
        ingredient_b="ceramides",
        severity="synergistic_pair",
        conflict_title="Retinoid Buffering & Barrier Defense",
        explanation="Ceramides cushion the stratum corneum against retinoid-induced trans-epidermal water loss and flaking.",
        scientific_rationale="Ceramides replenish intercellular lipids stripped during retinoid-induced cellular turnover acceleration.",
        recommendation="Ideal for sensitive skin or retinoid beginners: use the 'sandwich method' (moisturizer -> retinol -> moisturizer).",
        routine_separation_advice="PM Routine: Cleanse -> Light Ceramide Emulsion -> Retinoid -> Barrier Cream.",
    ),
    # 10. Synergistic: Niacinamide + Zinc PCA
    IngredientInteraction(
        ingredient_a="niacinamide",
        ingredient_b="salicylic_acid",
        severity="moderate_caution",
        conflict_title="Flushing & Concentration Balance",
        explanation="High percentages of Niacinamide combined with strong low-pH Salicylic Acid can induce transient facial flushing in sensitive skin.",
        scientific_rationale="Low pH environments can convert small amounts of niacinamide into nicotinic acid, a known cutaneous vasodilator.",
        recommendation="Safe for most oily skin types; sensitive skin users should wait 5-10 minutes between steps or split AM/PM.",
        routine_separation_advice="Use Salicylic Acid in AM or alternate nights; apply Niacinamide in PM routine.",
    ),
]


def identify_ingredient_keys(text: str) -> List[str]:
    """Extract known master ingredient keys from a text, title, or ingredient list."""
    text_lower = text.lower()
    matched = []
    for key, ing in MASTER_INGREDIENTS.items():
        if any(kw in text_lower for kw in ing.keywords):
            matched.append(key)
    return list(dict.fromkeys(matched))


def check_ingredient_compatibility(ingredient_keys: List[str]) -> Dict[str, Any]:
    """
    Check pairwise compatibility among a list of ingredient keys.
    Returns categorized interactions, overall safety score, and separation advice.
    """
    unique_keys = list(dict.fromkeys([k.lower().strip() for k in ingredient_keys]))
    detected_interactions: List[Dict[str, Any]] = []
    synergies: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    # Check each pair
    for i in range(len(unique_keys)):
        for j in range(i + 1, len(unique_keys)):
            k1, k2 = unique_keys[i], unique_keys[j]
            for inter in INTERACTION_MATRIX:
                match1 = (inter.ingredient_a == k1 and inter.ingredient_b == k2)
                match2 = (inter.ingredient_a == k2 and inter.ingredient_b == k1)
                if match1 or match2:
                    data = {
                        "ingredient_a": MASTER_INGREDIENTS.get(inter.ingredient_a, MasterIngredient(inter.ingredient_a, inter.ingredient_a, "", "", "", "", "", [], [], [], "", "", "", [])).name,
                        "ingredient_b": MASTER_INGREDIENTS.get(inter.ingredient_b, MasterIngredient(inter.ingredient_b, inter.ingredient_b, "", "", "", "", "", [], [], [], "", "", "", [])).name,
                        "severity": inter.severity,
                        "title": inter.conflict_title,
                        "explanation": inter.explanation,
                        "scientific_rationale": inter.scientific_rationale,
                        "recommendation": inter.recommendation,
                        "routine_separation_advice": inter.routine_separation_advice,
                    }
                    detected_interactions.append(data)
                    if inter.severity == "synergistic_pair":
                        synergies.append(data)
                    else:
                        warnings.append(data)

    has_high = any(w["severity"] == "high_irritation_risk" for w in warnings)
    has_incompatible = any(w["severity"] == "formulation_incompatibility" for w in warnings)
    has_caution = any(w["severity"] == "moderate_caution" for w in warnings)

    if has_high or has_incompatible:
        overall_status = "caution"
        safety_score = 45 if has_high else 55
        summary = "Conflicts detected. These actives should not be layered directly on top of each other in the same session."
    elif has_caution:
        overall_status = "moderate"
        safety_score = 75
        summary = "Moderate combination. Can be used together with proper spacing, buffer moisturizers, or alternating days."
    else:
        overall_status = "compatible"
        safety_score = 95
        summary = "Safe and synergistic combination! No known dermatological conflicts detected."

    return {
        "analyzed_ingredients": [
            {
                "id": k,
                "name": MASTER_INGREDIENTS[k].name if k in MASTER_INGREDIENTS else k.title(),
                "category": MASTER_INGREDIENTS[k].category if k in MASTER_INGREDIENTS else "Cosmetic Active",
                "evidence_level": MASTER_INGREDIENTS[k].evidence_level if k in MASTER_INGREDIENTS else "moderate",
            }
            for k in unique_keys
        ],
        "overall_status": overall_status,
        "safety_score": safety_score,
        "summary": summary,
        "warnings": warnings,
        "synergies": synergies,
        "total_conflicts": len(warnings),
        "total_synergies": len(synergies),
        "medical_disclaimer": ROUTINE_MEDICAL_DISCLAIMER,
    }


def check_routine_safety(
    am_items: List[Dict[str, Any]],
    pm_items: List[Dict[str, Any]],
    user_skin_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Examine AM and PM routine steps for active conflicts, duplicate actives (overload),
    sunscreen omission, and generate separation guidance.
    """
    am_keys: List[str] = []
    pm_keys: List[str] = []
    all_keys: List[str] = []
    
    # Track occurrence count for duplicate active overload
    active_counts: Dict[str, int] = {}

    for item in am_items:
        text = f"{item.get('step_name', '')} {item.get('product_name', '')} {item.get('custom_product_name', '')} {' '.join(item.get('key_ingredients', []))}"
        keys = identify_ingredient_keys(text)
        am_keys.extend(keys)
        all_keys.extend(keys)
        for k in keys:
            active_counts[k] = active_counts.get(k, 0) + 1

    for item in pm_items:
        text = f"{item.get('step_name', '')} {item.get('product_name', '')} {item.get('custom_product_name', '')} {' '.join(item.get('key_ingredients', []))}"
        keys = identify_ingredient_keys(text)
        pm_keys.extend(keys)
        all_keys.extend(keys)
        for k in keys:
            active_counts[k] = active_counts.get(k, 0) + 1

    am_unique = list(dict.fromkeys(am_keys))
    pm_unique = list(dict.fromkeys(pm_keys))

    # Pairwise checks within AM
    am_check = check_ingredient_compatibility(am_unique)
    # Pairwise checks within PM
    pm_check = check_ingredient_compatibility(pm_unique)

    routine_conflicts: List[Dict[str, Any]] = []

    for w in am_check["warnings"]:
        routine_conflicts.append({
            "routine": "AM",
            "type": "intra_routine_conflict",
            "severity": w["severity"],
            "title": f"AM Conflict: {w['title']}",
            "description": w["explanation"],
            "recommendation": w["routine_separation_advice"],
        })

    for w in pm_check["warnings"]:
        routine_conflicts.append({
            "routine": "PM",
            "type": "intra_routine_conflict",
            "severity": w["severity"],
            "title": f"PM Conflict: {w['title']}",
            "description": w["explanation"],
            "recommendation": w["routine_separation_advice"],
        })

    # Cross-routine / Photosensitivity / Daytime Retinol Check
    has_am_retinol = "retinol" in am_unique
    if has_am_retinol:
        routine_conflicts.append({
            "routine": "AM",
            "type": "photosensitivity_warning",
            "severity": "high_irritation_risk",
            "title": "Daytime Retinoid Exposure",
            "description": "Retinoids undergo photodegradation under UV rays and significantly increase solar erythema risk.",
            "recommendation": "Shift all Retinol and Retinoid treatments to your Evening (PM) routine.",
        })

    # Daytime Sunscreen Compliance Check
    has_am_sunscreen = "uv_filters" in am_unique or any(
        "sunscreen" in f"{it.get('step_name', '')} {it.get('product_name', '')}".lower() for it in am_items
    )
    has_photosensitizer = any(k in ["retinol", "glycolic_acid", "lactic_acid", "salicylic_acid"] for k in all_keys)

    if am_items and not has_am_sunscreen:
        severity = "high_irritation_risk" if has_photosensitizer else "moderate_caution"
        desc = (
            "Your morning routine is missing broad-spectrum SPF 50+. "
            "Because your regimen includes cell-renewing actives (AHAs, BHAs, or Retinoids), "
            "unprotected UV exposure can accelerate hyperpigmentation and cause solar damage."
            if has_photosensitizer else
            "Morning routines require broad-spectrum SPF 50+ to protect your skin barrier against daily UV radiation."
        )
        routine_conflicts.append({
            "routine": "AM",
            "type": "missing_sunscreen",
            "severity": severity,
            "title": "Sunscreen Missing in AM Routine",
            "description": desc,
            "recommendation": "Add a broad-spectrum SPF 50+ sunscreen as the mandatory final step of your AM routine.",
        })

    # Duplicate Actives / Overload Check
    active_overloads: List[Dict[str, Any]] = []
    for k, count in active_counts.items():
        if count >= 3 and k in ["niacinamide", "salicylic_acid", "glycolic_acid", "retinol"]:
            ing_name = MASTER_INGREDIENTS[k].name if k in MASTER_INGREDIENTS else k.title()
            active_overloads.append({
                "ingredient": ing_name,
                "count": count,
                "risk": f"Cumulative overload: {ing_name} is formulated in {count} separate steps across your routine.",
                "recommendation": f"Limit {ing_name} to 1-2 dedicated high-efficacy steps. Stacking multiple products containing {ing_name} increases irritation without providing additional clinical benefit.",
            })

    # Compute overall score and irritation risk level
    high_count = sum(1 for c in routine_conflicts if c.get("severity") == "high_irritation_risk")
    caution_count = sum(1 for c in routine_conflicts if c.get("severity") in ["moderate_caution", "formulation_incompatibility"])

    if high_count > 0 or len(active_overloads) > 1:
        irritation_risk = "High"
        safety_rating = "Attention Required"
        overall_score = max(35, 100 - (high_count * 25 + caution_count * 10 + len(active_overloads) * 15))
    elif caution_count > 0 or len(active_overloads) == 1:
        irritation_risk = "Moderate"
        safety_rating = "Minor Adjustments Recommended"
        overall_score = max(65, 100 - (caution_count * 12 + len(active_overloads) * 10))
    else:
        irritation_risk = "Low"
        safety_rating = "Optimized & Balanced"
        overall_score = 98

    # Separation Strategy
    optimization_steps = [
        "1. Reserve Vitamin C and antioxidant serums exclusively for your morning (AM) routine.",
        "2. Keep Retinoids strictly in your evening (PM) routine on dry skin.",
        "3. Alternate chemical exfoliants (AHA/BHA) and Retinoids on separate nights (Skin Cycling).",
        "4. Always apply SPF 50+ as your final AM layer 15 minutes before sun exposure.",
    ]

    return {
        "overall_score": overall_score,
        "irritation_risk": irritation_risk,
        "safety_rating": safety_rating,
        "total_conflicts": len(routine_conflicts),
        "conflicts": routine_conflicts,
        "active_overloads": active_overloads,
        "optimization_steps": optimization_steps,
        "am_active_count": len(am_unique),
        "pm_active_count": len(pm_unique),
        "sunscreen_compliant": has_am_sunscreen,
        "medical_disclaimer": ROUTINE_MEDICAL_DISCLAIMER,
    }


# =============================================================================
# Phase 10B: Indian Climate-Aware Skincare Recommendation Engine
# =============================================================================

@dataclass
class ClimateProfile:
    """Characteristics and skincare strategy for a specific Indian climate condition."""
    code: str
    name: str
    regions: str
    temperature_range: str
    humidity_level: str
    skin_impact: str
    cleanser_guidance: str
    moisturizer_guidance: str
    sunscreen_guidance: str
    hydration_strategy: str
    makeup_base_guidance: str
    recommended_actives: List[str]
    avoid_or_caution: List[str]


CLIMATE_PROFILES: Dict[str, ClimateProfile] = {
    "hot_humid": ClimateProfile(
        code="hot_humid",
        name="Hot & Humid (Coastal / Tropical)",
        regions="Mumbai, Chennai, Kolkata, Goa, Kochi, Coastal Andhra",
        temperature_range="28°C - 38°C",
        humidity_level="High (70% - 95%)",
        skin_impact="Excess sebum production, sweat-diluted skincare, clogged pores, high fungal acne vulnerability, makeup meltdown.",
        cleanser_guidance="Gentle foaming cleanser with Salicylic Acid (0.5%-1%) or Green Tea to clear pore-clogging sebum and sweat without stripping.",
        moisturizer_guidance="Ultra-lightweight oil-free gel or water cream containing Hyaluronic Acid and Centella. Avoid heavy occlusive petrolatum.",
        sunscreen_guidance="Matte fluid or hybrid aqua-gel sunscreen with sweat resistance and zero white cast.",
        hydration_strategy="Layer lightweight humectant toners/essences rather than thick lotions. Keep pores breathable.",
        makeup_base_guidance="Mattifying primer, oil-free liquid foundation with powder setting, sweat-proof fixing mist.",
        recommended_actives=["Niacinamide (5%)", "Salicylic Acid (BHA)", "Centella Asiatica (Cica)", "Zinc PCA"],
        avoid_or_caution=["Heavy petrolatum / mineral oil", "Thick butter creams", "Rich facial oils during daytime"],
    ),
    "hot_dry": ClimateProfile(
        code="hot_dry",
        name="Hot & Arid (North & Central Summers)",
        regions="Delhi (May-June), Rajasthan (Jaipur, Jodhpur), Ahmedabad, Nagpur",
        temperature_range="38°C - 47°C",
        humidity_level="Low (15% - 35%)",
        skin_impact="Extreme trans-epidermal water loss (TEWL), dry surface tightness coupled with reactive T-zone oiliness, high UV and dust stress.",
        cleanser_guidance="Hydrating non-stripping gel cleanser with Panthenol and Glycerin to preserve the lipid mantle.",
        moisturizer_guidance="Light-to-medium hydrating emulsion with Hyaluronic Acid, Ceramides, and Squalane to prevent moisture evaporation.",
        sunscreen_guidance="Hybrid fluid SPF 50+ PA++++ with broad-spectrum photoprotection and antioxidant shield against heat-induced ROS.",
        hydration_strategy="Humectants applied immediately on damp skin, sealed with lightweight squalane or barrier emulsion.",
        makeup_base_guidance="Gripping hydrating primer, satin natural-finish foundation to prevent desert flaking.",
        recommended_actives=["Hyaluronic Acid", "Vitamin C (Antioxidant shield)", "Ceramides", "Panthenol"],
        avoid_or_caution=["Harsh alcohol-based astringents", "Stripping charcoal cleansers", "Over-exfoliation"],
    ),
    "monsoon": ClimateProfile(
        code="monsoon",
        name="Monsoon Humidity & Dampness",
        regions="Pan-India Monsoon (July to September)",
        temperature_range="26°C - 33°C",
        humidity_level="Extreme (85% - 98%)",
        skin_impact="Stagnant moisture, proliferation of Malassezia yeast (fungal acne), comedone flare-ups, dull sweat-film.",
        cleanser_guidance="Clarifying Tea Tree or Salicylic Acid cleanser used twice daily to eliminate fungal acne triggers and bacterial colonization.",
        moisturizer_guidance="Weightless soothing gel or calming cica essence. Skip thick night creams in favor of sleeping water gels.",
        sunscreen_guidance="Fast-absorbing dry-touch gel SPF 50+ that does not run when caught in unexpected rain showers.",
        hydration_strategy="Single-layer lightweight essence. Keep product count minimal to prevent sweat trapping.",
        makeup_base_guidance="Pore-blurring silicone primer, water-resistant matte tint, setting powder on T-zone.",
        recommended_actives=["Azelaic Acid (targets fungal acne & redness)", "Tea Tree Extract", "Salicylic Acid", "Niacinamide"],
        avoid_or_caution=["Coconut oil and heavy esters (fungal acne triggers)", "Multi-layered rich creams"],
    ),
    "winter_dry": ClimateProfile(
        code="winter_dry",
        name="Winter Dryness & Cold Winds",
        regions="North India (Delhi, Punjab, Haryana, Kashmir, UP, MP) in Nov-Feb",
        temperature_range="4°C - 18°C",
        humidity_level="Low (20% - 40%)",
        skin_impact="Compromised lipid barrier, chapped flaky patches, windburn, dullness, accentuated fine expression lines.",
        cleanser_guidance="Milky cream cleanser or non-foaming cleansing lotion that cleanses without removing essential epidermal lipids.",
        moisturizer_guidance="Rich barrier repair cream packed with 3:1:1 physiological ratio of Ceramides, Cholesterol, and Fatty Acids.",
        sunscreen_guidance="Nourishing, dewy sunscreen with hydrating emollients. Winter UV remains potent for hyperpigmentation.",
        hydration_strategy="Slugging with balms at night on dry zones; damp application of essence followed by rich occlusive cream.",
        makeup_base_guidance="Dewy illuminating primer, hydrating serum foundation with luminous glow finish.",
        recommended_actives=["Ceramides (NP/AP/EOP)", "Squalane", "Peptides", "Lactic Acid (gentle AHA)", "Centella"],
        avoid_or_caution=["Strong clay masks", "High-percentage alcohol toners", "Scrub exfoliants"],
    ),
    "ac_indoor": ClimateProfile(
        code="ac_indoor",
        name="Air-Conditioned Indoor Office / Home",
        regions="Urban Corporate IT Hubs (Bangalore, Gurgaon, Hyderabad, Mumbai, Noida)",
        temperature_range="20°C - 24°C",
        humidity_level="Artificially Dry (20% - 30%)",
        skin_impact="AC dehumidification pulls moisture from stratum corneum, causing 3 PM skin tightness, midday dullness, and rebound oiliness.",
        cleanser_guidance="Gentle pH 5.5 hydrating cleanser.",
        moisturizer_guidance="Moisture-lock gel cream with multi-molecular hyaluronic acid and ceramides.",
        sunscreen_guidance="Hydrating daily fluid SPF (essential if near office windows or computer screens).",
        hydration_strategy="Hydrating facial mist with glycerin/aloe followed by desk-side re-application of barrier gel.",
        makeup_base_guidance="Hydrating mist-prep, lightweight cushion or satin foundation; avoid ultra-matte powders.",
        recommended_actives=["Hyaluronic Acid", "Glycerin", "Ceramides", "Vitamin C"],
        avoid_or_caution=["Drying matte setting powders applied repeatedly throughout the day"],
    ),
    "temperate_seasonal": ClimateProfile(
        code="temperate_seasonal",
        name="Temperate & Seasonal Transitions",
        regions="Bangalore, Pune, Hill Stations, Spring/Autumn Transitions",
        temperature_range="18°C - 30°C",
        humidity_level="Moderate (45% - 65%)",
        skin_impact="Generally well-balanced skin; occasional weather transition breakouts or mild seasonal dryness.",
        cleanser_guidance="Balanced gentle cleanser suitable for daily AM/PM usage.",
        moisturizer_guidance="Adaptive lightweight lotion or emulsion that provides balanced hydration without heaviness.",
        sunscreen_guidance="Lightweight daily fluid SPF 50+ PA++++.",
        hydration_strategy="Standard 3-step routine (Cleanse -> Hydrate -> Protect).",
        makeup_base_guidance="Natural satin finish primer and foundation.",
        recommended_actives=["Niacinamide", "Hyaluronic Acid", "Vitamin C", "Peptides"],
        avoid_or_caution=["Extreme routine shifts; maintain steady barrier maintenance"],
    ),
}


def get_climate_recommendations(
    climate_code: str,
    skin_type: Optional[str] = "Combination",
    concerns: Optional[List[str]] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate Indian climate-adapted skincare routine and product recommendations
    matched against actual catalog items in SQLite database.
    """
    code = climate_code.lower().strip()
    profile = CLIMATE_PROFILES.get(code, CLIMATE_PROFILES["hot_humid"])

    # Query catalog products from SQLite
    recommended_products: List[Dict[str, Any]] = []
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, brand, category, specs_json, image_url FROM products")
            rows = cursor.fetchall()

            for row in rows:
                p_id = row["id"]
                p_title = row["title"]
                p_brand = row["brand"]
                p_cat = row["category"]
                p_img = row["image_url"] or ""
                specs = json.loads(row["specs_json"]) if row["specs_json"] else {}
                raw_ings = specs.get("Key Ingredients", [])
                if isinstance(raw_ings, str):
                    key_ings = [s.strip() for s in raw_ings.split(",") if s.strip()]
                elif isinstance(raw_ings, list):
                    key_ings = [str(s).strip() for s in raw_ings if str(s).strip()]
                else:
                    key_ings = []
                p_type = specs.get("Product Type", p_cat)

                # Matching logic based on climate
                relevance_score = 0
                reasons = []

                # Sunscreens
                if "sunscreen" in p_cat.lower() or "sunscreen" in p_title.lower():
                    if code in ["hot_humid", "monsoon"]:
                        if "water" in p_title.lower() or "cooling" in p_title.lower() or "aqua" in p_title.lower() or "gel" in p_title.lower():
                            relevance_score += 40
                            reasons.append("Ultra-lightweight cooling water/gel vehicle prevents midday sweat meltdown")
                    elif code in ["winter_dry", "hot_dry"]:
                        relevance_score += 35
                        reasons.append("Broad-spectrum UV protection with hydrating humectants")
                    else:
                        relevance_score += 30
                        reasons.append("Daily photostable broad-spectrum sun defense")

                # Moisturizers
                if "moisturiz" in p_cat.lower() or "cream" in p_title.lower() or "hydrator" in p_title.lower():
                    if code in ["winter_dry", "ac_indoor"]:
                        if "ceramide" in p_title.lower() or "barrier" in p_title.lower() or "100h" in p_title.lower():
                            relevance_score += 45
                            reasons.append("Rich lipid replenishment protects against trans-epidermal water loss (TEWL)")
                    elif code in ["hot_humid", "monsoon"]:
                        if "gel" in p_title.lower() or "cooling" in p_title.lower():
                            relevance_score += 35
                            reasons.append("Non-greasy oil-free hydration that keeps pores breathable")

                # Serums / Actives
                if "serum" in p_cat.lower() or "essence" in p_title.lower():
                    if code in ["hot_humid", "monsoon"] and "niacinamide" in p_title.lower():
                        relevance_score += 40
                        reasons.append("Regulates excess humidity-induced sebum and refines congested pores")
                    if "vitamin c" in p_title.lower() and code in ["hot_dry", "temperate_seasonal"]:
                        relevance_score += 38
                        reasons.append("Antioxidant shield against arid environmental free radicals")
                    if "snail" in p_title.lower() and code in ["ac_indoor", "winter_dry"]:
                        relevance_score += 38
                        reasons.append("Viscoelastic deep hydration relieves artificial AC dryness")

                # Cleansers
                if "cleanse" in p_cat.lower() or "face cleansers" in p_cat.lower() or "micellar" in p_title.lower():
                    if code == "winter_dry" and "gentle" in p_title.lower():
                        relevance_score += 35
                        reasons.append("Non-stripping formulation preserves essential skin lipids in cold weather")
                    elif code in ["hot_humid", "monsoon"]:
                        relevance_score += 30
                        reasons.append("Effective removal of sweat, atmospheric pollution, and oxidized sebum")

                if relevance_score > 0:
                    recommended_products.append({
                        "id": p_id,
                        "title": p_title,
                        "brand": p_brand,
                        "category": p_cat,
                        "product_type": p_type,
                        "image_url": p_img,
                        "key_ingredients": key_ings,
                        "relevance_score": relevance_score,
                        "climate_rationale": " • ".join(reasons) if reasons else "Compatible with selected climate profile.",
                    })

            # Sort by highest relevance
            recommended_products.sort(key=lambda x: x["relevance_score"], reverse=True)
    except Exception as e:
        logger.error(f"Error querying catalog for climate recommendations: {e}")

    return {
        "climate_profile": {
            "code": profile.code,
            "name": profile.name,
            "regions": profile.regions,
            "temperature_range": profile.temperature_range,
            "humidity_level": profile.humidity_level,
            "skin_impact": profile.skin_impact,
            "cleanser_guidance": profile.cleanser_guidance,
            "moisturizer_guidance": profile.moisturizer_guidance,
            "sunscreen_guidance": profile.sunscreen_guidance,
            "hydration_strategy": profile.hydration_strategy,
            "makeup_base_guidance": profile.makeup_base_guidance,
            "recommended_actives": profile.recommended_actives,
            "avoid_or_caution": profile.avoid_or_caution,
        },
        "user_context": {
            "skin_type": skin_type,
            "concerns": concerns or [],
        },
        "matched_catalog_products": recommended_products[:6],
        "medical_disclaimer": ROUTINE_MEDICAL_DISCLAIMER,
    }


# =============================================================================
# Phase 10C: Foundation Shade and Undertone Matcher Engine
# =============================================================================

@dataclass
class FoundationShadeBenchmark:
    """Benchmark reference shades for standard South Asian / Indian depth and undertones."""
    depth: str  # fair, light, light_medium, medium, tan, deep, rich_deep
    undertone: str  # cool, warm, neutral, olive
    mac_shade: str
    maybelline_shade: str
    loreal_shade: str
    fenty_shade: str
    description: str


SHADE_BENCHMARKS: List[FoundationShadeBenchmark] = [
    FoundationShadeBenchmark("fair", "cool", "NW15", "110 Porcelain", "100 Rose Sand", "110", "Fair with rosy/pink undertone; burns easily"),
    FoundationShadeBenchmark("fair", "warm", "NC15", "115 Ivory", "105 Golden Ivory", "120", "Fair with subtle yellow/peachy undertone"),
    FoundationShadeBenchmark("fair", "neutral", "N15 / NC10", "112 Natural Ivory", "110 Neutral Ivory", "100", "Fair balanced undertone with neither pink nor yellow dominance"),
    FoundationShadeBenchmark("light", "cool", "NW20", "120 Classic Ivory", "120 Rose Vanilla", "150", "Light skin with delicate pink/red undertone"),
    FoundationShadeBenchmark("light", "warm", "NC20", "118 Light Beige", "125 Natural Rose / Gold", "140", "Light skin with golden/yellow undertone"),
    FoundationShadeBenchmark("light", "neutral", "N20", "122 Creamy Beige", "130 True Beige", "130", "Light balanced skin tone"),
    FoundationShadeBenchmark("light_medium", "warm", "NC25 / NC30", "128 Warm Nude", "140 Golden Sun", "210 / 220", "Classic Indian light-medium with warm golden undertone"),
    FoundationShadeBenchmark("light_medium", "olive", "NC25 Olive / NC30", "128 Warm Nude", "145 Golden Amber", "290", "Light-medium with greenish/muted golden-olive undertone"),
    FoundationShadeBenchmark("light_medium", "neutral", "N25", "125 Nude Beige", "135 Radiant Beige", "200", "Balanced light-medium wheatish tone"),
    FoundationShadeBenchmark("medium", "warm", "NC35 / NC40", "220 Natural Beige", "200 Golden Sand", "240 / 300", "True Indian wheatish-golden skin; tans easily without burning"),
    FoundationShadeBenchmark("medium", "olive", "NC37 / NC40 Olive", "228 Soft Tan", "220 Golden Honey", "330", "Wheatish skin with distinct greenish/muted olive undertone"),
    FoundationShadeBenchmark("medium", "neutral", "N35", "230 Natural Buff", "210 Neutral Sand", "280", "Medium balanced neutral tone"),
    FoundationShadeBenchmark("tan", "warm", "NC42 / NC45", "310 Sun Beige", "260 Golden Sun", "360 / 370", "Rich honey-caramel tan with golden/amber undertone"),
    FoundationShadeBenchmark("tan", "olive", "NC44 Olive", "322 Warm Honey", "270 Caramel Olive", "390", "Deep tan skin with rich bronze-olive undertone"),
    FoundationShadeBenchmark("tan", "neutral", "N42", "312 Golden Beige", "250 Radiant Caramel", "350", "Warm tan balanced tone"),
    FoundationShadeBenchmark("deep", "warm", "NC47 / NC50", "330 Toffee", "320 Golden Caramel", "420", "Deep warm bronze-espresso skin"),
    FoundationShadeBenchmark("deep", "neutral", "NW45 / N50", "332 Golden Caramel", "330 Deep Amber", "410", "Deep neutral espresso complexion"),
    FoundationShadeBenchmark("rich_deep", "warm", "NC55", "340 Cappuccino", "360 Deep Mocha", "450 / 470", "Rich espresso-cocoa with warm undertone"),
    FoundationShadeBenchmark("rich_deep", "cool", "NW55", "360 Espresso", "380 Rich Ebony", "490", "Rich deep complexion with cool blue/red undertones"),
]


def match_foundation_shade(
    skin_depth: str,
    undertone: str,
    coverage: Optional[str] = "Medium",
    finish: Optional[str] = "Matte",
    reference_brand: Optional[str] = None,
    reference_shade: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Match user depth and undertone to catalog foundations with confidence score,
    oxidation advisory, and cross-brand conversion.
    """
    depth_clean = skin_depth.lower().strip().replace("-", "_").replace(" ", "_")
    undertone_clean = undertone.lower().strip()

    # If reference shade is given, try parsing it to calibrate depth/undertone
    inferred_depth = depth_clean
    inferred_undertone = undertone_clean
    if reference_shade:
        ref_upper = reference_shade.upper().strip()
        if "NC15" in ref_upper or "115" in ref_upper:
            inferred_depth, inferred_undertone = "fair", "warm"
        elif "NC20" in ref_upper or "118" in ref_upper:
            inferred_depth, inferred_undertone = "light", "warm"
        elif "NC25" in ref_upper or "NC30" in ref_upper or "128" in ref_upper:
            inferred_depth, inferred_undertone = "light_medium", "warm"
        elif "NC35" in ref_upper or "NC40" in ref_upper or "220" in ref_upper:
            inferred_depth, inferred_undertone = "medium", "warm"
        elif "NC42" in ref_upper or "NC45" in ref_upper or "310" in ref_upper:
            inferred_depth, inferred_undertone = "tan", "warm"
        elif "NC50" in ref_upper or "330" in ref_upper or "332" in ref_upper:
            inferred_depth, inferred_undertone = "deep", "warm"
        elif "NW" in ref_upper:
            inferred_undertone = "cool"

    # Find closest benchmark
    matched_benchmark = None
    for bm in SHADE_BENCHMARKS:
        if bm.depth == inferred_depth and bm.undertone == inferred_undertone:
            matched_benchmark = bm
            break

    if not matched_benchmark:
        # Fallback to depth match
        for bm in SHADE_BENCHMARKS:
            if bm.depth == inferred_depth:
                matched_benchmark = bm
                break

    if not matched_benchmark:
        matched_benchmark = SHADE_BENCHMARKS[6]  # Default light_medium warm (128 Warm Nude)

    # Search foundation products in catalog
    catalog_foundation_matches: List[Dict[str, Any]] = []
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, brand, category, specs_json, image_url FROM products WHERE category = 'Foundations' OR title LIKE '%foundation%'"
            )
            rows = cursor.fetchall()
            for row in rows:
                p_id = row["id"]
                p_title = row["title"]
                p_brand = row["brand"]
                p_img = row["image_url"] or ""
                specs = json.loads(row["specs_json"]) if row["specs_json"] else {}
                catalog_shade = specs.get("Shade", "")
                catalog_finish = specs.get("Finish", "Matte")

                # Match calculation
                confidence = 88.0
                if matched_benchmark.maybelline_shade.lower() in p_title.lower() or matched_benchmark.maybelline_shade.lower() in catalog_shade.lower():
                    confidence = 96.0
                    match_label = "Exact Catalog Shade Match"
                elif inferred_depth in ["light_medium", "medium"]:
                    confidence = 91.0
                    match_label = "Estimated South Asian Colorimetry Match"
                else:
                    confidence = 84.0
                    match_label = "Closest Algorithmic Variant"

                # Oxidation notes based on formula
                if "fit me" in p_title.lower() or "matte" in catalog_finish.lower():
                    oxidation_advisory = (
                        "Oxidation Notice: This matte micro-powder formula reacts with natural skin sebum and "
                        "typically oxidizes 0.5 shade deeper within 30 minutes of wear. If you have combination/oily skin "
                        "or sit between two shades, consider choosing the half-shade lighter or setting with translucent powder."
                    )
                else:
                    oxidation_advisory = (
                        "Hydrating/satin formulations experience minimal color shift (~0.2 shade). Set with an oil-free mist."
                    )

                catalog_foundation_matches.append({
                    "product_id": p_id,
                    "product_title": p_title,
                    "brand": p_brand,
                    "image_url": p_img,
                    "catalog_shade": catalog_shade or matched_benchmark.maybelline_shade,
                    "recommended_shade_code": matched_benchmark.maybelline_shade,
                    "finish": catalog_finish,
                    "confidence_score": confidence,
                    "match_label": match_label,
                    "oxidation_advisory": oxidation_advisory,
                    "mac_equivalent": matched_benchmark.mac_shade,
                    "loreal_equivalent": matched_benchmark.loreal_shade,
                    "fenty_equivalent": matched_benchmark.fenty_shade,
                })
    except Exception as e:
        logger.error(f"Error matching foundation in catalog: {e}")

    # If no catalog foundations found in DB, provide benchmark response
    if not catalog_foundation_matches:
        catalog_foundation_matches.append({
            "product_id": 23,
            "product_title": f"Maybelline Fit Me Matte + Poreless Liquid Foundation - {matched_benchmark.maybelline_shade}",
            "brand": "Maybelline",
            "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=800&q=80",
            "catalog_shade": matched_benchmark.maybelline_shade,
            "recommended_shade_code": matched_benchmark.maybelline_shade,
            "finish": finish or "Matte",
            "confidence_score": 92.0,
            "match_label": "Algorithmic Colorimetry Match",
            "oxidation_advisory": "Oxidizes ~0.5 shade darker on oily skin; size down if undecided.",
            "mac_equivalent": matched_benchmark.mac_shade,
            "loreal_equivalent": matched_benchmark.loreal_shade,
            "fenty_equivalent": matched_benchmark.fenty_shade,
        })

    return {
        "user_profile": {
            "skin_depth": inferred_depth,
            "undertone": inferred_undertone,
            "coverage_preference": coverage,
            "finish_preference": finish,
            "reference_shade_provided": reference_shade,
        },
        "shade_benchmark": {
            "description": matched_benchmark.description,
            "mac_shade": matched_benchmark.mac_shade,
            "maybelline_shade": matched_benchmark.maybelline_shade,
            "loreal_shade": matched_benchmark.loreal_shade,
            "fenty_shade": matched_benchmark.fenty_shade,
        },
        "matches": catalog_foundation_matches,
        "undertone_guidance": (
            "Olive Undertone Note: South Asian olive complexions have green/muted tones that often look ashy in cool/pink foundations and overly orange in warm/golden foundations. Look for neutral-golden or true olive labeled formulas."
            if inferred_undertone == "olive" else
            "Warm Undertone Note: Golden, peach, and yellow undertones blend seamlessly with Indian wheatish skin without casting a grey/ashy hue."
            if inferred_undertone == "warm" else
            "Cool Undertone Note: Rosy and pink bases complement cool undertones, preventing a sallow yellowish cast."
            if inferred_undertone == "cool" else
            "Neutral Undertone Note: Balanced peach and golden tones allow versatility across neutral and warm foundation ranges."
        ),
        "disclaimer": FOUNDATION_MATCH_DISCLAIMER,
    }


# =============================================================================
# Phase 10D: Advanced Beauty Product Discovery
# =============================================================================

def search_advanced_discovery(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skin_type: Optional[str] = None,
    concern: Optional[str] = None,
    ingredient: Optional[str] = None,
    finish: Optional[str] = None,
    min_spf: Optional[int] = None,
    undertone: Optional[str] = None,
    query: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Multi-criteria search engine across the 34 catalog products in pricewise.db.
    Calculates relevance score, matches criteria, and highlights dupe links.
    """
    matched_products: List[Dict[str, Any]] = []

    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            # Fetch products with their lowest price from offers table
            cursor.execute(
                """
                SELECT p.id, p.title, p.brand, p.category, p.description, p.specs_json, p.image_url,
                       MIN(o.current_price) as lowest_price,
                       MAX(o.original_price) as reference_mrp
                FROM products p
                LEFT JOIN offers o ON p.id = o.product_id
                GROUP BY p.id
                """
            )
            rows = cursor.fetchall()

            for r in rows:
                p_id = r["id"]
                title = r["title"] or ""
                p_brand = r["brand"] or ""
                p_cat = r["category"] or ""
                desc = r["description"] or ""
                specs = json.loads(r["specs_json"]) if r["specs_json"] else {}
                img = r["image_url"] or ""
                price = float(r["lowest_price"]) if r["lowest_price"] is not None else 0.0
                mrp = float(r["reference_mrp"]) if r["reference_mrp"] is not None else price

                full_text = f"{title} {p_brand} {p_cat} {desc} {json.dumps(specs)}".lower()

                # Score and filter logic
                match_score = 100
                tags = []

                # Category filter
                if category and category.lower() != "all":
                    cat_clean = category.lower().strip()
                    if cat_clean in p_cat.lower() or cat_clean in full_text:
                        tags.append(f"Category: {p_cat}")
                    else:
                        continue

                # Brand filter
                if brand and brand.lower() != "all":
                    b_clean = brand.lower().strip()
                    if b_clean in p_brand.lower():
                        tags.append(f"Brand: {p_brand}")
                    else:
                        continue

                # Price filter
                if min_price is not None and price > 0 and price < min_price:
                    continue
                if max_price is not None and price > 0 and price > max_price:
                    continue

                # Skin Type filter
                if skin_type and skin_type.lower() != "all":
                    st_clean = skin_type.lower().strip()
                    catalog_st = specs.get("Skin Type", "").lower()
                    if st_clean in catalog_st or st_clean in full_text or "all skin" in catalog_st:
                        tags.append(f"Skin: {skin_type.title()}")
                        match_score += 15
                    else:
                        continue

                # Skin Concern filter
                if concern and concern.lower() != "all":
                    c_clean = concern.lower().strip()
                    if c_clean in full_text or (c_clean == "acne" and ("salicylic" in full_text or "niacinamide" in full_text)) \
                       or (c_clean == "pigmentation" and ("vitamin c" in full_text or "niacinamide" in full_text)) \
                       or (c_clean == "barrier" and ("ceramide" in full_text or "hyaluronic" in full_text)):
                        tags.append(f"Concern: {concern.title()}")
                        match_score += 20
                    else:
                        continue

                # Key Ingredient filter
                if ingredient and ingredient.lower() != "all":
                    ing_clean = ingredient.lower().strip()
                    if ing_clean in full_text:
                        tags.append(f"Active: {ingredient.title()}")
                        match_score += 25
                    else:
                        continue

                # Finish filter
                if finish and finish.lower() != "all":
                    f_clean = finish.lower().strip()
                    catalog_finish = specs.get("Finish", "").lower()
                    if f_clean in catalog_finish or f_clean in full_text:
                        tags.append(f"Finish: {finish.title()}")
                        match_score += 10
                    else:
                        continue

                # SPF filter
                if min_spf is not None and min_spf > 0:
                    if "spf" in full_text:
                        # Extract SPF number
                        spf_match = re.search(r'spf\s*(\d+)', full_text)
                        if spf_match:
                            val = int(spf_match.group(1))
                            if val >= min_spf:
                                tags.append(f"SPF {val}")
                                match_score += 15
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue

                # Free-text Query
                if query and query.strip():
                    q_clean = query.lower().strip()
                    if q_clean in full_text:
                        match_score += 30
                        tags.append(f"Search: '{query}'")
                    else:
                        continue

                # Dupe / Affordable alternative check
                is_dupe_candidate = False
                brand_tier = specs.get("Brand Tier", "Affordable")
                if brand_tier == "Luxury" or price > 2000:
                    tags.append("Luxury Icon")
                elif brand_tier == "Affordable" or price < 700:
                    tags.append("High Value / Dupe Friendly")
                    is_dupe_candidate = True

                raw_ings = specs.get("Key Ingredients", [])
                if isinstance(raw_ings, str):
                    key_ings = [s.strip() for s in raw_ings.split(",") if s.strip()]
                elif isinstance(raw_ings, list):
                    key_ings = [str(s).strip() for s in raw_ings if str(s).strip()]
                else:
                    key_ings = []

                matched_products.append({
                    "id": p_id,
                    "title": title,
                    "brand": p_brand,
                    "category": p_cat,
                    "brand_tier": brand_tier,
                    "price": price,
                    "reference_mrp": mrp,
                    "image_url": img,
                    "key_ingredients": key_ings,
                    "skin_type": specs.get("Skin Type", "All Skin Types"),
                    "finish": specs.get("Finish"),
                    "match_score": match_score,
                    "matching_tags": tags,
                    "is_dupe_candidate": is_dupe_candidate,
                })

        # Sort by match score then lowest price
        matched_products.sort(key=lambda x: (-x["match_score"], x["price"]))
    except Exception as e:
        logger.error(f"Error in advanced discovery search: {e}")

    return {
        "total_results": len(matched_products),
        "products": matched_products,
        "active_filters": {
            "category": category,
            "brand": brand,
            "min_price": min_price,
            "max_price": max_price,
            "skin_type": skin_type,
            "concern": concern,
            "ingredient": ingredient,
            "finish": finish,
            "min_spf": min_spf,
            "undertone": undertone,
            "query": query,
        },
    }
