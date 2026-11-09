# Phase 8C Planning — Nykaa Live Retailer Integration Plan

**Date:** November 9, 2026  
**Repository Root:** `C:\Users\humai\price-comparison-website`  
**Classification:** Planning & Feasibility Report Only (No Live Extraction Implemented)

---

## 1. Executive Summary

This report establishes the technical architecture, security policy, matching rules, failure modes, and test plan for making **Nykaa (`nykaa.com`)** the first verified live retailer in PriceWise AI.

- **Current State:** Nykaa adapter exists (`src/adapters/nykaa_adapter.py`), declares `CapabilityStatus.SUPPORTED`, and has complete HTML/JSON-LD parser methods. When official API keys (`NYKAA_API_KEY`, `NYKAA_PARTNER_SECRET`) are absent, it operates in safe fallback mode.
- **Feasibility:** Public product page parsing is technically designed and supported by Playwright browser automation (`BrowserManager`), but **Cloudflare bot protection on search routes requires careful handling**.
- **Go/No-Go Recommendation:** **GO for Phase 8C implementation**, subject to strict compliance with rule enforcement (no CAPTCHA bypass, no credential forging, graceful degradation to `RESTRICTED` status when blocked).

---

## 2. Review of Baseline Architecture

### 2.1 Verified Component Map

| Component | File Path | Role in Nykaa Integration |
|-----------|-----------|---------------------------|
| Nykaa Adapter | `src/adapters/nykaa_adapter.py` | Specific page parser and API client |
| Base Adapter | `src/adapters/base_adapter.py` | Rate limiter, `ExtractedPriceResult` factory |
| Adapter Registry | `src/adapters/registry.py` | Dispatcher (`get_adapter('nykaa')`) |
| Browser Manager | `src/workers/browser_manager.py` | Playwright Chromium headless worker |
| Security Policy | `src/workers/security_policy.py` | `nykaa.com` domain allowlist + SSRF blocker |
| Live Comparison Engine | `src/services/live_comparison_engine.py` | Coordinates check, caches results, records audit logs |
| Product Matching Service | `src/services/product_matching_service.py` | Multi-factor variant validation (size, shade, formulation) |

### 2.2 Security Domain Allowlist (`src/workers/security_policy.py:20-26`)

```python
ALLOWED_RETAILER_DOMAINS = {
    "nykaa.com",
    "tirabeauty.com",
    "purplle.com",
    "amazon.in",
    "myntra.com",
}
```
`nykaa.com` is explicitly allowed. All loopback, private IP subnets, and non-HTTPS protocols are blocked.

---

## 3. Nykaa Access Investigation

### 3.1 Data Sources & Access Paths

| Source Path | Authorization | Feasibility | Technical Mechanism |
|-------------|---------------|-------------|---------------------|
| **1. Official Nykaa Partner API** | Requires `NYKAA_API_KEY` + `NYKAA_PARTNER_SECRET` | ⚠️ Unconfigured | REST API JSON endpoint (supported in `fetch_product_offer`) |
| **2. Public Product Page (Direct URL)** | None required (permitted public web) | ✅ Feasible | Playwright headless Chromium + JSON-LD `schema.org/Product` extraction |
| **3. Public Search Route** | None required | ⚠️ Cloudflare restricted | `https://www.nykaa.com/search/result/?q=...` |

### 3.2 Access Barriers & Anti-Bot Protections

1. **Cloudflare / Incapsula Protection:** Nykaa uses Cloudflare Turnstile/challenge pages on certain dynamic search routes.
2. **Direct Product Page Access:** Direct URLs (`nykaa.com/*/p/<id>`) are generally accessible via Playwright when using realistic user-agents (`Mozilla/5.0... Chrome/124.0...`).
3. **JSON-LD Schema Availability:** Nykaa embeds standard `<script type="application/ld+json">` containing `schema.org/Product` with `@type`, `name`, `offers.price`, `offers.availability`.

### 3.3 Strict Rule Compliance Guarantees
- ❌ **NEVER** bypass CAPTCHAs, Cloudflare challenges, or login walls
- ❌ **NEVER** forge partner API credentials or signatures
- ❌ **NEVER** exceed rate limit of 30 requests/minute (enforced in `BaseRetailerAdapter`)
- ✅ When Cloudflare blocks access, the adapter returns `verification_status="restricted"` with source `source_type="unavailable"`

---

## 4. Exact Product Matching Design

To prevent comparing incompatible items (e.g., 30ml vs 50ml, or Ruby Woo vs Velvet Teddy), the Nykaa integration delegates to `evaluate_product_match()` in `src/services/product_matching_service.py`.

### 4.1 Required Variant Dimension Validations

```
Target Product (Catalog)                  Nykaa Offer (Extracted)
────────────────────────                 ────────────────────────
Brand: "Dot & Key"               <===>   Brand: "Dot & Key"              (Must match)
Name:  "Watermelon Sunscreen"    <===>   Name:  "Watermelon Cooling..."  (Title similarity > 0.70)
Size:  "50ml"                    <===>   Size:  "50ml"                   (30ml vs 50ml -> INCOMPATIBLE_MISMATCH)
Shade: "Ruby Woo"                <===>   Shade: "Ruby Woo"               (Cherry Red vs Ruby Woo -> MISMATCH)
Form:  "Waterproof"              <===>   Form:  "Waterproof"             (Washable vs Waterproof -> MISMATCH)
```

### 4.2 Classification Rules
1. **`VERIFIED_MATCH`** (Confidence ≥ 0.95) — Brand, size/volume, shade, and formulation match exactly. Only verified matches are marked `is_lowest_listed` or `is_lowest_total`.
2. **`POSSIBLE_MATCH`** (Confidence 0.60–0.85) — High title similarity but net quantity or shade is ambiguous. Excluded from direct price arbitrage; flagged for review.
3. **`INCOMPATIBLE_MISMATCH`** (Confidence 0.20) — Contradictory variant attributes. Excluded from comparison.

---

## 5. Price Verification & Status Classification Design

### 5.1 Captured Attributes per Verified Offer

| Field | Type | Description |
|-------|------|-------------|
| `retailer_name` | `str` | `"Nykaa"` |
| `store_id` | `str` | `"nykaa"` |
| `product_url` | `str` | Canonical product page URL |
| `listed_price` | `float` | Current selling price on page (e.g., `465.0`) |
| `mrp` | `Optional[float]` | Maximum Retail Price before discount (e.g., `595.0`) |
| `discount_pct` | `float` | Calculated percentage discount |
| `shipping_fee` | `Optional[float]` | `0.0` if price ≥ ₹299, else `₹49.0` (disclosed) |
| `total_cost` | `Optional[float]` | `listed_price + shipping_fee` (landed cost) |
| `variant_detected` | `str` | e.g., `"50 g / Standard"` |
| `retrieved_at` | `str` | ISO 8601 UTC timestamp |
| `source_type` | `str` | See status enum below |
| `verification_status` | `str` | See status enum below |

### 5.2 Verification Status Hierarchy

| Status Enum | Meaning | Trigger Condition |
|-------------|---------|-------------------|
| `LIVE_VERIFIED` | Fresh price extracted from live page within last 10 minutes | Successful Playwright extraction |
| `CACHED` | Valid result served from in-memory TTL cache (< 10 minutes old) | Cache hit in `LiveComparisonEngine` |
| `HISTORICAL` | Observation recorded in SQLite `price_history` table from previous run | Previous observation in DB |
| `POSSIBLE_MATCH` | Extracted price exists but variant match confidence is < 0.95 | `MatchClassification.POSSIBLE_MATCH` |
| `UNAVAILABLE` | Product page not found or price elements missing | 404 or empty DOM selectors |
| `RESTRICTED` | Request blocked by Cloudflare or bot protection | `detect_access_restrictions()` triggered |
| `DEMO` | Preloaded academic seed dataset | Default state when unconfigured |

**Strict Rule:** Demo or historical prices are **NEVER** presented as live verified prices.

---

## 6. Failure & Resilience Handling Design

```
                     ┌─────────────────────────────┐
                     │ Execute Nykaa Comparison    │
                     └──────────────┬──────────────┘
                                    │
                         Is URL in Cache (<10m)?
                         ├── YES ──> Return CACHED
                         └── NO
                                    │
                         Is Rate Limit Exceeded?
                         ├── YES ──> Return UNAVAILABLE (rate limit note)
                         └── NO
                                    │
                         Navigate with Playwright (timeout 8s)
                         ├── Timeout / Error ──> Return UNAVAILABLE (logged)
                         └── Page Loaded
                                    │
                         Detect Cloudflare / CAPTCHA?
                         ├── YES ──> Return RESTRICTED (logged in price_check_logs)
                         └── NO
                                    │
                         Extract JSON-LD / DOM Pricing
                         ├── Failed ──> Return UNAVAILABLE
                         └── Price Extracted
                                    │
                         Evaluate Variant Match
                         ├── Mismatch ──> Return MISMATCH
                         └── Match ──> Return LIVE_VERIFIED + Persist Observation
```

---

## 7. Comprehensive Test Plan for Phase 8C

### 7.1 Unit & Integration Tests (`tests/test_phase8c_nykaa.py`)

| Test Case | Objective | Assertions |
|-----------|-----------|------------|
| `test_nykaa_exact_match` | Valid Nykaa product page HTML with JSON-LD | `status == "retrieved"`, `listed_price == 465.0`, `source_type == "verified_live"` |
| `test_nykaa_wrong_product` | HTML for different product title | `status == "mismatch"`, `match_classification == "incompatible_mismatch"` |
| `test_nykaa_wrong_size` | HTML for 30ml when target is 50ml | `status == "mismatch"`, size mismatch reason included |
| `test_nykaa_wrong_shade` | HTML for Ruby Woo when target is Velvet Teddy | `status == "mismatch"`, shade mismatch reason included |
| `test_nykaa_missing_price` | Page HTML missing price spans/JSON-LD | `status == "unavailable"`, clear validation note |
| `test_nykaa_restricted_cloudflare` | HTML containing Cloudflare challenge text | `status == "restricted"`, audit log recorded |
| `test_nykaa_timeout_handling` | Browser navigation timeout simulation | `status == "unavailable"`, no crash, no hang |
| `test_nykaa_cached_result` | Second request within 10-minute TTL | `is_cached == True`, no duplicate browser launch |
| `test_nykaa_historical_fallback` | Live check unavailable but history exists | Historical observation retrieved from SQLite |
| `test_nykaa_price_change_detection` | Price changes from ₹465 to ₹425 | Fresh observation recorded in `price_history` table |

### 7.2 Safety Distinction
- Tests in `test_phase8c_nykaa.py` will use **mock HTML fixtures** (`NYKAA_SAMPLE_HTML`) for deterministic, fast unit testing.
- Real live network calls will be gated behind an explicit `--run-live-retailers` pytest flag.

---

## 8. Expected Files & Database Changes in Phase 8C

### Files to Modify / Create in Implementation
1. `src/adapters/nykaa_adapter.py` — Refine DOM regex patterns for latest Nykaa page layout
2. `src/services/live_comparison_engine.py` — Ensure `source_type` mappings map cleanly
3. `tests/test_phase8c_nykaa.py` — Create comprehensive unit test suite

### Database Schema Impact
- **No schema changes required.** All records fit into existing tables:
  - `price_check_logs` (audit log of every check attempt)
  - `price_history` (timestamped observations)
  - `offers` (latest verified offer state)

---

## 9. Go / No-Go Recommendation

### Verdict: **GO for Phase 8C Implementation**

**Justification:**
1. Nykaa adapter structure, security policy, and browser manager are already built and tested.
2. JSON-LD extraction (`schema.org/Product`) provides a clean, standardized data source.
3. Multi-factor variant matching (`evaluate_product_match`) prevents misidentifying sizes or shades.
4. Fallback architecture guarantees PriceWise AI remains 100% operational even if Nykaa blocks requests.

**Prerequisites for Implementation:**
- Approval of this plan
- No modifications to Purplle, Tira, Myntra, or Amazon adapters during 8C
- No Gemini model changes

---

*Report ready for review and approval.*
