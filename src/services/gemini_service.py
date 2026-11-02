"""Google Gemini API Service for Semantic SKU Identification (Phase 6A).

Uses the official google-genai SDK to extract structured beauty attributes
(Brand, Product Name, Net Quantity/Volume, Shade, Formulation) from unstructured
retailer page titles and HTML snippets.

IMPORTANT ARCHITECTURAL RULE:
Gemini is used STRICTLY for semantic entity extraction and variant parsing.
It is NEVER used to generate, predict, or fabricate retailer prices or stock status.
"""

from dataclasses import dataclass, field
import json
import logging
import os
import re
from typing import Any, Optional
from src.services.product_matching_service import (
    parse_quantity_volume,
    parse_shade,
    parse_formulation,
)

logger = logging.getLogger("pricewise.gemini")


@dataclass
class GeminiSKUExtractionResult:
    """Structured entity extraction result from Gemini or heuristic fallback."""
    brand: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    size_volume: Optional[str] = None
    shade: Optional[str] = None
    formulation: Optional[str] = None
    confidence_score: float = 0.0
    extraction_source: str = "heuristic_fallback"  # "gemini_model" or "heuristic_fallback"
    error_message: Optional[str] = None


class GeminiService:
    """Backend service for semantic entity recognition using Google GenAI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 6.0,
    ):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.timeout_seconds = timeout_seconds
        self._client = None

    @property
    def is_configured(self) -> bool:
        """Check whether GEMINI_API_KEY is available in the environment."""
        key = self._api_key or os.getenv("GEMINI_API_KEY")
        return bool(key and key.strip())

    def _get_client(self):
        """Lazy-initialize google-genai client."""
        if self._client is None and self.is_configured:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key or os.getenv("GEMINI_API_KEY"))
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")
                self._client = None
        return self._client

    def parse_sku_entities(
        self,
        raw_text: str,
        context_hint: Optional[str] = None,
    ) -> GeminiSKUExtractionResult:
        """
        Extract brand, name, volume, shade, and formulation from raw product title.
        If Gemini is unconfigured or encounters a network error, falls back to
        deterministic regex heuristics so the system never crashes.
        """
        if not raw_text or not raw_text.strip():
            return GeminiSKUExtractionResult(error_message="Empty input text")

        # 1. Fallback heuristic extraction
        val, unit = parse_quantity_volume(raw_text)
        size_str = f"{val}{unit}" if val is not None else None
        shade_str = parse_shade(raw_text)
        form_str = parse_formulation(raw_text)

        fallback_result = GeminiSKUExtractionResult(
            brand=None,
            product_name=raw_text.strip(),
            category=context_hint,
            size_volume=size_str,
            shade=shade_str,
            formulation=form_str,
            confidence_score=0.60,
            extraction_source="heuristic_fallback",
        )

        # 2. If Gemini is not configured, return safe fallback
        if not self.is_configured:
            fallback_result.error_message = (
                "Gemini API key not configured. Set GEMINI_API_KEY in backend environment to enable LLM extraction."
            )
            return fallback_result

        # 3. Live Gemini call via google-genai SDK
        client = self._get_client()
        if not client:
            return fallback_result

        prompt = f"""
You are an expert Indian beauty catalog parser. Extract structured entities from the following retailer product title.
Return a valid JSON object only with exactly these keys:
- "brand": string or null
- "product_name": core product title without size/shade
- "category": skincare or makeup or null
- "size_volume": normalized quantity (e.g. "50ml", "30g") or null
- "shade": color shade name or null
- "formulation": e.g. "Gel", "Cream", "Waterproof", "Washable" or null

Retailer Product Title: "{raw_text}"
"""

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            text_out = response.text or ""
            # Strip markdown json codeblock if present
            cleaned_json = re.sub(r"^```json\s*|\s*```$", "", text_out.strip(), flags=re.MULTILINE)
            data = json.loads(cleaned_json)

            return GeminiSKUExtractionResult(
                brand=data.get("brand"),
                product_name=data.get("product_name") or raw_text.strip(),
                category=data.get("category") or context_hint,
                size_volume=data.get("size_volume") or size_str,
                shade=data.get("shade") or shade_str,
                formulation=data.get("formulation") or form_str,
                confidence_score=0.95,
                extraction_source="gemini_model",
            )
        except Exception as e:
            logger.warning(f"Gemini entity extraction failed: {e}. Reverting to heuristics.")
            fallback_result.error_message = f"Gemini extraction error: {str(e)}"
            return fallback_result

    def generate_search_query(
        self,
        brand: str,
        product_name: str,
        size_volume: Optional[str] = None,
        retailer_name: Optional[str] = None,
    ) -> str:
        """
        Generate a concise, high-precision search query for locating the product on retailer sites.
        Deterministic and safe; never hallucinates prices or unverified URLs.
        """
        parts = []
        clean_brand = (brand or "").strip()
        clean_name = (product_name or "").strip()

        if clean_brand and clean_brand.lower() not in clean_name.lower():
            parts.append(clean_brand)
        if clean_name:
            parts.append(clean_name)
        if size_volume and size_volume.lower() not in clean_name.lower():
            parts.append(size_volume.strip())

        query = " ".join(parts).strip()
        query = re.sub(r"[^\w\s%+.-]", " ", query)
        query = re.sub(r"\s+", " ", query).strip()
        return query or product_name


# Global singleton instance
_gemini_service = GeminiService()


def get_gemini_service() -> GeminiService:
    """Get global GeminiService instance."""
    return _gemini_service

