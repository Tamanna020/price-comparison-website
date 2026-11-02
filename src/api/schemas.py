"""API Response and Request Schemas for PriceWise AI Beauty (Phase 6A)."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str
    database: str
    record_count: int


class OfferSchema(BaseModel):
    id: int
    product_id: int
    store_id: int
    store_name: str
    store_rating: float
    current_price: float
    original_price: Optional[float] = None
    shipping_cost: Optional[float] = None
    is_shipping_disclosed: bool = True
    currency: str = "INR"
    availability: str = "In Stock"
    variant_name: str = "Standard"
    condition: str = "Brand New"
    offer_url: str = ""
    coupon_code: Optional[str] = None
    coupon_discount: float = 0.0
    total_cost: Optional[float] = None
    source_type: str = "demo"
    last_checked: Optional[str] = None


class ProductListItemSchema(BaseModel):
    id: int
    sku: str
    slug: str
    title: str
    brand: str
    category: str
    description: str
    image_url: str
    lowest_price: Optional[float] = None
    highest_price: Optional[float] = None
    lowest_total_cost: Optional[float] = None
    currency_symbol: str = "₹"
    available_offer_count: int = 0
    specs: dict[str, Any] = Field(default_factory=dict)


class ProductDetailSchema(ProductListItemSchema):
    offers: list[OfferSchema] = Field(default_factory=list)
    created_at: Optional[str] = None


class LiveRetailerOfferSchema(BaseModel):
    retailer_name: str
    store_id: str
    status: str
    listed_price: Optional[float] = None
    mrp: Optional[float] = None
    discount_pct: float = 0.0
    shipping_fee: Optional[float] = None
    is_shipping_disclosed: bool = True
    coupon_code: Optional[str] = None
    coupon_discount: float = 0.0
    total_cost: Optional[float] = None
    stock_status: str = "In Stock"
    in_stock: bool = True
    purchase_url: str = ""
    variant_detected: Optional[str] = None
    match_classification: str = "verified_match"
    is_lowest_listed: bool = False
    is_lowest_total: bool = False
    source_type: str = "verified_live"
    retrieved_at: str
    validation_notes: Optional[str] = None


class LiveComparisonSummarySchema(BaseModel):
    lowest_listed_price: Optional[float] = None
    lowest_listed_retailer: Optional[str] = None
    lowest_total_cost: Optional[float] = None
    lowest_total_retailer: Optional[str] = None
    retailers_checked: int = 0
    retailers_retrieved: int = 0
    retailers_unavailable: int = 0
    retailers_unsupported: int = 0
    retailers_restricted: int = 0
    cheapest_savings_amount: float = 0.0
    cheapest_savings_percent: float = 0.0


class LiveComparisonResponse(BaseModel):
    product_id: Optional[int] = None
    product_title: str
    brand: str
    target_variant: str
    is_cached: bool = False
    freshness_seconds: int = 0
    retrieval_timestamp: str
    offers: list[LiveRetailerOfferSchema] = Field(default_factory=list)
    summary: LiveComparisonSummarySchema


class ManualUrlCheckRequest(BaseModel):
    url: str


class ManualUrlCheckResponse(BaseModel):
    retailer_name: str
    store_id: str
    product_url: str
    verification_status: str
    listed_price: Optional[float] = None
    mrp: Optional[float] = None
    shipping_fee: Optional[float] = None
    is_shipping_disclosed: bool = True
    total_cost: Optional[float] = None
    in_stock: bool = True
    stock_status: str = "In Stock"
    product_name: Optional[str] = None
    retrieved_at: str
    validation_notes: Optional[str] = None


# =====================================================================
# Phase 7: Authentication, User Profiles, Routines & Watchlist Schemas
# =====================================================================

class UserSchema(BaseModel):
    id: int
    display_name: str
    name: Optional[str] = None
    email: str
    created_at: str
    status: str = "active"


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[UserSchema] = None


class UserProfileSchema(BaseModel):
    user_id: int
    display_name: str
    preferred_name: Optional[str] = None
    skin_type: str = "unsure"
    skin_concerns: list[str] = Field(default_factory=list)
    preferred_categories: list[str] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    makeup_preferences: Any = Field(default_factory=list)
    ingredient_preferences: list[str] = Field(default_factory=list)
    ingredient_avoidance: list[str] = Field(default_factory=list)
    ingredient_avoidances: list[str] = Field(default_factory=list)
    updated_at: str
    medical_disclaimer: str


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    preferred_name: Optional[str] = None
    skin_type: Optional[str] = None
    skin_concerns: Optional[list[str]] = None
    preferred_categories: Optional[list[str]] = None
    preferred_brands: Optional[list[str]] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    makeup_preferences: Optional[Any] = None
    ingredient_preferences: Optional[list[str]] = None
    ingredient_avoidance: Optional[list[str]] = None
    ingredient_avoidances: Optional[list[str]] = None


class RoutineItemSchema(BaseModel):
    id: int
    routine_id: int
    step_number: int
    step_name: str
    product_id: Optional[int] = None
    custom_product_name: Optional[str] = None
    usage_instructions: Optional[str] = None
    precautions: Optional[str] = None
    category: Optional[str] = None
    product_title: Optional[str] = None
    product_brand: Optional[str] = None
    product_image_url: Optional[str] = None
    product_price: Optional[float] = None
    product_slug: Optional[str] = None


class RoutineSchema(BaseModel):
    id: int
    user_id: int
    routine_type: str
    title: str
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: str
    updated_at: str
    items: list[RoutineItemSchema] = Field(default_factory=list)
    conflict_warnings: list[str] = Field(default_factory=list)
    conflicts: list[Any] = Field(default_factory=list)
    medical_disclaimer: str
    disclaimer: Optional[str] = None


class CreateRoutineRequest(BaseModel):
    routine_type: str
    title: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class UpdateRoutineRequest(BaseModel):
    title: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AddRoutineItemRequest(BaseModel):
    step_name: str
    category: Optional[str] = None
    product_id: Optional[int] = None
    custom_product_name: Optional[str] = None
    usage_instructions: Optional[str] = None
    precautions: Optional[str] = None
    step_number: Optional[int] = None


class ReorderRoutineRequest(BaseModel):
    item_ids_in_order: list[int] = Field(default_factory=list)
    item_order: list[int] = Field(default_factory=list)


class WatchlistItemSchema(BaseModel):
    id: int
    user_id: int
    product_id: int
    title: str
    brand: str
    category: str
    image_url: Optional[str] = None
    slug: str
    current_lowest_price: Optional[float] = None
    original_price: Optional[float] = None
    created_at: str
    note: Optional[str] = None


class AddWatchlistRequest(BaseModel):
    product_id: int
    note: Optional[str] = None
    notes: Optional[str] = None
    target_price: Optional[float] = None


class SyncWatchlistRequest(BaseModel):
    product_ids: list[Any] = Field(default_factory=list)
    items: list[Any] = Field(default_factory=list)


class RecommendedProductSchema(BaseModel):
    product_id: int
    title: str
    name: Optional[str] = None
    brand: str
    category: str
    price: Optional[float] = None
    image_url: Optional[str] = None
    image: Optional[str] = None
    slug: str
    match_score: int
    recommendation_score: Optional[int] = None
    match_reasons: list[str] = Field(default_factory=list)
    matched_reasons: list[str] = Field(default_factory=list)
    key_ingredients: Optional[str] = None
    skin_type_suitability: Optional[str] = None


class PersonalizedRecommendationsResponse(BaseModel):
    user_id: int
    skin_type: str
    skin_concerns: list[str] = Field(default_factory=list)
    max_budget: Optional[float] = None
    products: list[RecommendedProductSchema] = Field(default_factory=list)
    recommendations: list[RecommendedProductSchema] = Field(default_factory=list)
    has_profile: bool
    medical_disclaimer: str
    disclaimer: Optional[str] = None



