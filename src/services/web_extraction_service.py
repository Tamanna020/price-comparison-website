"""Hybrid Web Extraction Service for PriceWise AI Beauty (Phase 11B).

Coordinates deterministic extraction from permitted sources:
1. Schema.org Product & Offer JSON-LD parsing
2. OpenGraph / Twitter meta product metadata parsing
3. BeautifulSoup DOM extraction with regex price cleaners
4. Anti-Bot / WAF challenge detection (Akamai, Cloudflare, Amazon Robot Check)
5. Strict SSRF protection (HTTPS-only, approved domains, private IP blocking)
6. Gemini AI structured interpretation fallback for ambiguous content
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import re
from typing import Any, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from src.services.gemini_service import get_gemini_service
from src.services.product_matching_service import parse_quantity_volume, parse_shade, parse_formulation
from src.workers.security_policy import validate_browser_url, is_ip_blocked

logger = logging.getLogger("pricewise.extraction")

# Max allowable page size to prevent memory exhaustion (5 MB)
MAX_RESPONSE_BYTES = 5 * 1024 * 1024


@dataclass
class WebExtractionResult:
    """Standardized result from web extraction and semantic interpretation."""
    url: str
    retailer_name: str
    extraction_method: str  # "json_ld", "opengraph_meta", "html_dom", "gemini_interpretation", "heuristic_fallback", "waf_blocked"
    status: str = "extracted"  # "extracted", "restricted", "uncertain", "blocked", "error"
    title: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    currency: str = "INR"
    discount_pct: float = 0.0
    size_volume: Optional[str] = None
    shade: Optional[str] = None
    formulation: Optional[str] = None
    in_stock: bool = True
    stock_status: str = "In Stock"
    is_blocked: bool = False
    block_type: Optional[str] = None  # "akamai_waf", "cloudflare_challenge", "amazon_captcha", "http_403", "rate_limited"
    confidence_score: float = 0.0
    raw_evidence_snippet: Optional[str] = None
    error_message: Optional[str] = None
    extracted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def has_valid_price(self) -> bool:
        return self.price is not None and self.price > 0


def detect_waf_challenge(html_content: str, status_code: int = 200) -> tuple[bool, Optional[str]]:
    """
    Detect anti-bot, WAF, or CAPTCHA challenges without bypassing them.
    Returns (is_blocked, block_type).
    """
    if status_code in (403, 429):
        return True, "http_403_or_429"

    if not html_content:
        return False, None

    lower = html_content.lower()

    # Akamai WAF
    if "access denied" in lower and ("you don't have permission to access" in lower or "reference #" in lower):
        return True, "akamai_waf"

    # Amazon Robot Check CAPTCHA
    if "robot check" in lower or "enter the characters you see below" in lower or "/errors/validatecaptcha" in lower:
        return True, "amazon_captcha"

    # Cloudflare Challenge / Turnstile
    if "attention required! | cloudflare" in lower or "cf-browser-verification" in lower or "challenge-running" in lower:
        return True, "cloudflare_challenge"

    # Generic bot block
    if "unusual traffic from your computer network" in lower or "bot detected" in lower:
        return True, "bot_detected"

    return False, None


def clean_price_string(price_str: Any) -> Optional[float]:
    """Parse numeric price from string with currency symbols or commas."""
    if price_str is None:
        return None
    if isinstance(price_str, (int, float)):
        return round(float(price_str), 2) if price_str > 0 else None

    text = str(price_str).replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d{1,2})?)", text)
    if match:
        try:
            val = float(match.group(1))
            return round(val, 2) if val > 0 else None
        except ValueError:
            return None
    return None


def extract_from_json_ld(html_content: str) -> Optional[dict[str, Any]]:
    """
    Extract Schema.org Product / Offer structured JSON-LD.
    Returns dictionary of extracted fields if successful, else None.
    """
    if not html_content or "<script" not in html_content:
        return None

    soup = BeautifulSoup(html_content, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        try:
            text = script.string or script.text or ""
            if not text.strip():
                continue
            data = json.loads(text.strip())

            # Handle @graph or list of items
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if "@graph" in data and isinstance(data["@graph"], list):
                    items = data["@graph"]
                else:
                    items = [data]

            for item in items:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("@type") or item.get("type") or ""
                # Could be string or list of strings
                types = [item_type] if isinstance(item_type, str) else item_type
                if any("product" in str(t).lower() for t in types):
                    # Found Schema.org Product!
                    title = item.get("name") or item.get("title")
                    brand_info = item.get("brand")
                    brand = brand_info.get("name") if isinstance(brand_info, dict) else (brand_info if isinstance(brand_info, str) else None)

                    offers = item.get("offers")
                    price = None
                    mrp = None
                    currency = "INR"
                    in_stock = True
                    stock_status = "In Stock"

                    if isinstance(offers, dict):
                        price = clean_price_string(offers.get("price") or offers.get("lowPrice"))
                        mrp = clean_price_string(offers.get("highPrice") or offers.get("listPrice") or offers.get("priceValidUntil"))
                        currency = offers.get("priceCurrency") or currency
                        avail = str(offers.get("availability") or "").lower()
                        if "outofstock" in avail or "discontinued" in avail:
                            in_stock = False
                            stock_status = "Out of Stock"
                    elif isinstance(offers, list) and len(offers) > 0:
                        first_offer = offers[0]
                        if isinstance(first_offer, dict):
                            price = clean_price_string(first_offer.get("price") or first_offer.get("lowPrice"))
                            mrp = clean_price_string(first_offer.get("highPrice") or first_offer.get("listPrice"))
                            currency = first_offer.get("priceCurrency") or currency
                            avail = str(first_offer.get("availability") or "").lower()
                            if "outofstock" in avail:
                                in_stock = False
                                stock_status = "Out of Stock"

                    sku = item.get("sku")
                    description = item.get("description")

                    if price is not None and price > 0:
                        return {
                            "title": title,
                            "brand": brand,
                            "price": price,
                            "mrp": mrp,
                            "currency": currency,
                            "in_stock": in_stock,
                            "stock_status": stock_status,
                            "sku": sku,
                            "description": description,
                        }
        except Exception as e:
            logger.debug(f"JSON-LD parsing exception: {e}")
            continue

    return None


def extract_from_meta_tags(html_content: str) -> Optional[dict[str, Any]]:
    """Extract OpenGraph and Twitter product meta tags."""
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, "html.parser")
    meta_tags = {}
    for meta in soup.find_all("meta"):
        prop = meta.get("property") or meta.get("name")
        content = meta.get("content")
        if prop and content:
            meta_tags[prop.lower()] = content.strip()

    title = meta_tags.get("og:title") or meta_tags.get("twitter:title")
    price_val = (
        meta_tags.get("og:price:amount")
        or meta_tags.get("product:price:amount")
        or meta_tags.get("price")
    )
    mrp_val = meta_tags.get("product:original_price:amount")
    currency = meta_tags.get("og:price:currency") or meta_tags.get("product:price:currency") or "INR"
    availability = meta_tags.get("og:availability") or meta_tags.get("product:availability")

    price = clean_price_string(price_val)
    mrp = clean_price_string(mrp_val)

    if price is not None and price > 0:
        in_stock = True
        stock_status = "In Stock"
        if availability and ("out" in availability.lower() or "oos" in availability.lower()):
            in_stock = False
            stock_status = "Out of Stock"

        return {
            "title": title,
            "brand": meta_tags.get("product:brand") or meta_tags.get("brand"),
            "price": price,
            "mrp": mrp,
            "currency": currency,
            "in_stock": in_stock,
            "stock_status": stock_status,
        }

    return None


def extract_from_html_dom(html_content: str) -> Optional[dict[str, Any]]:
    """Deterministic DOM extraction using common Indian beauty retailer patterns."""
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, "html.parser")

    # Product Title
    title = None
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)

    # Search for price patterns
    price = None
    mrp = None

    # Price classes commonly used
    price_nodes = soup.find_all(
        attrs={"class": re.compile(r"(post-discount|price|selling-price|final-price|discounted-price)", re.I)}
    )
    for node in price_nodes:
        text = node.get_text()
        p = clean_price_string(text)
        if p and p > 10:  # Avoid single-digit counts
            price = p
            break

    # MRP classes commonly used
    mrp_nodes = soup.find_all(
        attrs={"class": re.compile(r"(mrp|original-price|strike|cross-price)", re.I)}
    )
    for node in mrp_nodes:
        text = node.get_text()
        m = clean_price_string(text)
        if m and price and m >= price:
            mrp = m
            break

    # If class matching failed, try regex on text content
    if price is None:
        raw_text = soup.get_text(separator=" ")
        # Match '₹ 599' or 'Rs. 599'
        price_match = re.search(r"(?:₹|rs\.?)\s*([0-9,]+(?:\.[0-9]{1,2})?)", raw_text, re.I)
        if price_match:
            price = clean_price_string(price_match.group(1))

    if price is not None and price > 0:
        return {
            "title": title,
            "brand": None,
            "price": price,
            "mrp": mrp,
            "currency": "INR",
            "in_stock": True,
            "stock_status": "In Stock",
        }

    return None


def interpret_with_gemini(
    html_snippet: str,
    context_hint: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Interpret ambiguous or unstructured product HTML using Gemini AI structured output.
    Follows strict guardrails: deterministic validation must verify positive price and MRP >= price.
    """
    gemini = get_gemini_service()
    if not gemini.is_configured:
        logger.info("Gemini not configured; skipping AI interpretation.")
        return None

    client = gemini._get_client()
    if not client:
        return None

    # Truncate snippet to avoid quota bloat
    truncated_snippet = html_snippet[:4000]

    prompt = f"""
You are a precision beauty product and price extractor for an Indian shopping platform.
Extract accurate product details from this webpage HTML snippet.

Return ONLY a valid JSON object with these exact keys:
- "title": product title (string or null)
- "brand": brand name (string or null)
- "selling_price": actual discounted price to pay in INR (float/int or null)
- "mrp": maximum retail price / list price in INR before discount (float/int or null)
- "currency": "INR"
- "size_volume": size or volume (e.g. "30ml", "50g", or null)
- "shade": color shade name or null
- "formulation": e.g. "Serum", "Cream", "Waterproof" or null
- "in_stock": boolean (true or false)

NEVER hallucinate or invent prices. If price is not explicitly present in the snippet, return null for selling_price.
Context Hint: {context_hint or 'None'}

HTML Snippet:
{truncated_snippet}
"""

    try:
        response = client.models.generate_content(
            model=gemini.model_name,
            contents=prompt,
        )
        text_out = response.text or ""
        cleaned_json = re.sub(r"^```json\s*|\s*```$", "", text_out.strip(), flags=re.MULTILINE)
        data = json.loads(cleaned_json)

        selling_price = clean_price_string(data.get("selling_price"))
        mrp = clean_price_string(data.get("mrp"))

        # Guardrail: Selling price must be positive
        if selling_price is None or selling_price <= 0:
            return None

        # Guardrail: MRP must be >= selling_price if provided
        if mrp is not None and mrp < selling_price:
            mrp = None  # Invalidate impossible MRP

        return {
            "title": data.get("title"),
            "brand": data.get("brand"),
            "price": selling_price,
            "mrp": mrp,
            "currency": data.get("currency") or "INR",
            "size_volume": data.get("size_volume"),
            "shade": data.get("shade"),
            "formulation": data.get("formulation"),
            "in_stock": bool(data.get("in_stock", True)),
            "stock_status": "In Stock" if data.get("in_stock", True) else "Out of Stock",
        }
    except Exception as e:
        logger.warning(f"Gemini interpretation error: {e}")
        return None


def extract_product_data(
    html_content: str,
    url: str = "",
    retailer_name: str = "",
    allow_gemini: bool = True,
    status_code: int = 200,
) -> WebExtractionResult:
    """
    Complete hybrid extraction pipeline:
    1. Check WAF / Anti-bot / CAPTCHA block
    2. Deterministic JSON-LD
    3. Deterministic OpenGraph / Meta
    4. Deterministic HTML DOM
    5. Gemini-assisted interpretation fallback
    """
    # 1. Anti-Bot / WAF challenge check
    is_blocked, block_type = detect_waf_challenge(html_content, status_code=status_code)
    if is_blocked:
        return WebExtractionResult(
            url=url,
            retailer_name=retailer_name,
            extraction_method="waf_blocked",
            status="restricted",
            is_blocked=True,
            block_type=block_type,
            confidence_score=0.0,
            error_message=f"Access blocked by retailer security ({block_type}). Automated access restricted.",
        )

    # 2. Schema.org JSON-LD (Priority 1)
    json_ld_data = extract_from_json_ld(html_content)
    if json_ld_data and json_ld_data.get("price"):
        title = json_ld_data.get("title")
        p_val, p_unit = parse_quantity_volume(title or "")
        size_str = f"{p_val}{p_unit}" if p_val is not None else None
        shade_str = parse_shade(title or "")
        form_str = parse_formulation(title or "")

        price = json_ld_data["price"]
        mrp = json_ld_data.get("mrp")
        disc = round(((mrp - price) / mrp) * 100, 1) if (mrp and mrp > price and mrp > 0) else 0.0

        return WebExtractionResult(
            url=url,
            retailer_name=retailer_name,
            extraction_method="json_ld",
            status="extracted",
            title=title,
            brand=json_ld_data.get("brand"),
            price=price,
            mrp=mrp,
            currency=json_ld_data.get("currency") or "INR",
            discount_pct=disc,
            size_volume=size_str,
            shade=shade_str,
            formulation=form_str,
            in_stock=json_ld_data.get("in_stock", True),
            stock_status=json_ld_data.get("stock_status", "In Stock"),
            confidence_score=0.98,
            raw_evidence_snippet=str(json_ld_data)[:500],
        )

    # 3. OpenGraph / Twitter Meta Tags (Priority 2)
    meta_data = extract_from_meta_tags(html_content)
    if meta_data and meta_data.get("price"):
        title = meta_data.get("title")
        p_val, p_unit = parse_quantity_volume(title or "")
        size_str = f"{p_val}{p_unit}" if p_val is not None else None
        shade_str = parse_shade(title or "")
        form_str = parse_formulation(title or "")

        price = meta_data["price"]
        mrp = meta_data.get("mrp")
        disc = round(((mrp - price) / mrp) * 100, 1) if (mrp and mrp > price and mrp > 0) else 0.0

        return WebExtractionResult(
            url=url,
            retailer_name=retailer_name,
            extraction_method="opengraph_meta",
            status="extracted",
            title=title,
            brand=meta_data.get("brand"),
            price=price,
            mrp=mrp,
            currency=meta_data.get("currency") or "INR",
            discount_pct=disc,
            size_volume=size_str,
            shade=shade_str,
            formulation=form_str,
            in_stock=meta_data.get("in_stock", True),
            stock_status=meta_data.get("stock_status", "In Stock"),
            confidence_score=0.92,
            raw_evidence_snippet=str(meta_data)[:500],
        )

    # 4. HTML DOM Parsing (Priority 3)
    dom_data = extract_from_html_dom(html_content)
    if dom_data and dom_data.get("price"):
        title = dom_data.get("title")
        p_val, p_unit = parse_quantity_volume(title or "")
        size_str = f"{p_val}{p_unit}" if p_val is not None else None
        shade_str = parse_shade(title or "")
        form_str = parse_formulation(title or "")

        price = dom_data["price"]
        mrp = dom_data.get("mrp")
        disc = round(((mrp - price) / mrp) * 100, 1) if (mrp and mrp > price and mrp > 0) else 0.0

        return WebExtractionResult(
            url=url,
            retailer_name=retailer_name,
            extraction_method="html_dom",
            status="extracted",
            title=title,
            brand=dom_data.get("brand"),
            price=price,
            mrp=mrp,
            currency=dom_data.get("currency") or "INR",
            discount_pct=disc,
            size_volume=size_str,
            shade=shade_str,
            formulation=form_str,
            in_stock=dom_data.get("in_stock", True),
            stock_status=dom_data.get("stock_status", "In Stock"),
            confidence_score=0.80,
            raw_evidence_snippet=str(dom_data)[:500],
        )

    # 5. Gemini-Assisted Interpretation (Priority 4)
    if allow_gemini:
        ai_data = interpret_with_gemini(html_content, context_hint=retailer_name)
        if ai_data and ai_data.get("price"):
            price = ai_data["price"]
            mrp = ai_data.get("mrp")
            disc = round(((mrp - price) / mrp) * 100, 1) if (mrp and mrp > price and mrp > 0) else 0.0

            return WebExtractionResult(
                url=url,
                retailer_name=retailer_name,
                extraction_method="gemini_interpretation",
                status="extracted",
                title=ai_data.get("title"),
                brand=ai_data.get("brand"),
                price=price,
                mrp=mrp,
                currency=ai_data.get("currency") or "INR",
                discount_pct=disc,
                size_volume=ai_data.get("size_volume"),
                shade=ai_data.get("shade"),
                formulation=ai_data.get("formulation"),
                in_stock=ai_data.get("in_stock", True),
                stock_status=ai_data.get("stock_status", "In Stock"),
                confidence_score=0.88,
                raw_evidence_snippet=str(ai_data)[:500],
            )

    # Price could not be confidently identified
    return WebExtractionResult(
        url=url,
        retailer_name=retailer_name,
        extraction_method="heuristic_fallback",
        status="uncertain",
        confidence_score=0.20,
        error_message="Price or product details could not be confidently extracted from page content.",
    )


def safe_fetch_url(
    url: str,
    timeout_seconds: float = 10.0,
    allow_test_fixtures: bool = False,
) -> tuple[Optional[str], int, Optional[str]]:
    """
    Safely fetch webpage content over HTTPS with strict SSRF protection and response size limits.
    Returns (html_content, status_code, error_message).
    """
    if not allow_test_fixtures:
        is_safe, reason = validate_browser_url(url)
        if not is_safe:
            return None, 400, f"SSRF Security Violation: {reason}"

    try:
        import httpx

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Follow redirects with limit
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True, max_redirects=3) as client:
            response = client.get(url, headers=headers)

            # SSRF check on final redirected URL
            if not allow_test_fixtures:
                final_safe, final_reason = validate_browser_url(str(response.url))
                if not final_safe:
                    return None, 400, f"Redirected to forbidden destination: {final_reason}"

            # Check response size limit
            content_bytes = response.content
            if len(content_bytes) > MAX_RESPONSE_BYTES:
                return None, 413, f"Response size exceeded limit ({len(content_bytes)} bytes > {MAX_RESPONSE_BYTES})"

            return response.text, response.status_code, None
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None, 500, str(e)
