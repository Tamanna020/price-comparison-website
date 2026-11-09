# PriceWise AI — Phase 11B: Hybrid AI + Web Extraction & Price Intelligence Engine Implementation Report

**Project:** PriceWise AI (Academic Skincare & Makeup Intelligence & Price-Comparison Engine)  
**Phase:** 11B (Hybrid AI + Web Extraction & Real Retailer Price Verification System)  
**Execution Timestamp:** 2026-11-09T21:40:00+05:30  
**Environment:** Windows 11, Python 3.14 (`py -3.14`), FastAPI, SQLite, React 19 + TypeScript + Vite, Playwright Chromium  
**Author:** Antigravity AI Pair Programmer  

---

## 1. Executive Summary

In Phase 11B, PriceWise AI successfully deployed a compliant, high-precision **Hybrid AI + Web Extraction & Price Intelligence Engine** designed specifically for the no-mandatory-API environment established in Phase 11A. 

The architecture strictly adheres to three non-negotiable principles:
1. **Zero Paid Retailer APIs / Subscriptions:** No Nykaa, Myntra, Purplle, Tira, or Amazon India API keys are required.
2. **Zero Access Control Bypasses:** The engine respects all perimeter protections (Akamai WAF, Cloudflare challenges, Amazon Robot Check CAPTCHAs) without using proxy rotation, stealth browser plugins, or CAPTCHA bypass services.
3. **Truth in Evidence & Advertising:** Prices are segregated into clear, honest tiers (`LIVE_VERIFIED`, `MANUAL_VERIFIED`, `CACHED`, `HISTORICAL`, `POSSIBLE_MATCH`, `RESTRICTED`, `UNAVAILABLE`, and `DEMO`). DEMO data is never conflated with verified market statistics.

---

## 2. Existing Architecture Inspected & Baseline Status

Prior to implementation, an exhaustive codebase and database audit was conducted:
- **Database (`data/pricewise.db`):** 34 catalog products, 97 baseline offers across 10 store entities, 947 price history rows, 0 evidence references. Database integrity: `ok`.
- **Phase 11A Feasibility Audit Findings:**
  - **Nykaa (`nykaa.com`):** Akamai edge security returns HTTP 403 / HTTP/2 stream reset on automated HTTP requests. Marked `RESTRICTED`.
  - **Tira Beauty (`tirabeauty.com`):** Akamai WAF blocks automated headless navigation. Marked `RESTRICTED`.
  - **Amazon India (`amazon.in`):** Perimeter Robot Check CAPTCHA blocks automated scraping. Marked `RESTRICTED`.
  - **Myntra (`myntra.com`):** Exposes clean Schema.org `Product` & `Offer` JSON-LD in server-rendered HTML, but commercial indexing requires permission review. Marked `PERMISSION_REVIEW_REQUIRED`.
  - **Purplle (`purplle.com`):** Client-side hydrated React SPA; terms of service restrict unauthorized extraction. Marked `PERMISSION_REVIEW_REQUIRED`.

---

## 3. Implemented Hybrid Architecture

The engine coordinates five distinct pipelines:

```
                          CUSTOMER SEARCH / PRODUCT DETAIL
                                        │
                                        ▼
                            PRODUCT IDENTITY RESOLUTION
                                        │
                                        ▼
                        AUTHORIZED DATA SOURCE DISCOVERY
                                        │
            ┌───────────────────────────┴───────────────────────────┐
            │                                                       │
            ▼                                                       ▼
   RETAILER ACCESS POLICY                             USER PRICE SUBMISSION
   - Check Rate Limit (60s cooldown)                  - User submits URL & Price
   - Check Circuit Breaker (30m cooldown)             - Uploads Screenshot Proof
   - Respect RESTRICTED Policy                        - Stored in manual_verification_requests
            │                                                       │
            ▼                                                       ▼
   PERMITTED EXTRACTION PIPELINE                            ADMIN REVIEW QUEUE
   1. Schema.org JSON-LD Parser                            - Reviews Screenshot Proof
   2. OpenGraph / Twitter Meta Parser                      - Validates Variant Integrity
   3. BeautifulSoup DOM Parser                             - Confirms Price & MRP
   4. Gemini Structured Fallback (Guardrails)                       │
            │                                                       ▼
            └───────────────────────────┬───────────────────────────┘
                                        │
                                        ▼
                        MULTI-FACTOR PRODUCT MATCHING
                        - Brand Normalization
                        - Active Concentration Check (10% vs 5%)
                        - Formulation Integrity (Waterproof vs Washable)
                        - Makeup Shade Integrity (Ruby Woo vs Velvet Teddy)
                        - Net Quantity Volume Check (30ml vs 60ml)
                        - Unit Price Normalization (₹/ml, ₹/g)
                        - Multi-Pack Bundle Detection (Pack of 2)
                                        │
                                        ▼
                       EVIDENCE & VERIFICATION AUDIT TRAIL
                        - Immutable evidence_references record
                        - Status Classification (LIVE_VERIFIED / MANUAL_VERIFIED)
                        - Append to price_history table
                        - Update offers catalog
                        - Trigger evaluate_tracking_rules (Deal Alerts)
                                        │
                                        ▼
                         PREMIUM FRONTEND PRESENTATION
                        - Clear Truth-in-Advertising Status Badges
                        - Explicit "Restricted Retailer" explanatory notices
                        - Unit price display (₹/ml)
                        - User Price Verification modal
                        - Admin Verification Portal (/admin/verifications)
```

---

## 4. Files Created and Modified

### A. Core Backend Services Created / Enhanced
1. **`src/services/product_matching_service.py`**:
   - Expanded to full 7-tier classification: `EXACT_MATCH`, `SIZE_VARIANT`, `FORMULATION_VARIANT`, `SHADE_VARIANT`, `BUNDLE_MATCH`, `POSSIBLE_MATCH`, `NO_MATCH`.
   - Added unit price normalization (`calculate_unit_price`) returning `₹/ml` and `₹/g`.
   - Added active ingredient concentration parser (`parse_concentration`) catching discrepancies like 10% vs 5% Niacinamide.
   - Added multi-pack bundle detector (`detect_bundle`) recognizing "Pack of 2", "Combo", "Duo", etc.
   - Maintained full backward compatibility with legacy `verified_match` and `incompatible_mismatch` flags.
2. **`src/services/web_extraction_service.py`**:
   - Deterministic Schema.org Product/Offer JSON-LD extractor (`extract_from_json_ld`).
   - OpenGraph and Twitter product meta tag extractor (`extract_from_meta_tags`).
   - BeautifulSoup DOM parser fallback with regex price cleaners (`extract_from_html_dom`).
   - Anti-bot / WAF challenge detector (`detect_waf_challenge`) detecting Akamai 403, Cloudflare turnstiles, and Amazon Robot Check CAPTCHAs.
   - Strict SSRF protection (`safe_fetch_url`) enforcing HTTPS-only, domain allowlisting, private IP blocking (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.169.254), and 5MB payload limits.
   - Gemini AI structured output fallback (`interpret_with_gemini`) with deterministic guardrails (positive price, MRP >= price).
3. **`src/services/price_verification_service.py`**:
   - Evidence reference manager (`record_evidence_reference`, `get_evidence_for_reference`).
   - Verification status constants: `LIVE_VERIFIED`, `MANUAL_VERIFIED`, `CACHED`, `HISTORICAL`, `POSSIBLE_MATCH`, `RESTRICTED`, `UNAVAILABLE`, `DEMO`.
   - Deterministic price validation (`validate_price_observation_data`).
   - Admin verification queue retriever (`get_pending_verification_queue`).
   - Admin approval workflows (`approve_manual_verification`, `approve_price_correction`) updating `offers`, appending to `price_history`, and triggering `evaluate_tracking_rules`.
   - Admin rejection workflows (`reject_manual_verification`, `reject_price_correction`).
4. **`src/services/price_collection_engine.py`**:
   - Multi-source orchestrator with in-memory concurrency locking per `product_id` to prevent duplicate parallel extraction runs.
   - Domain rate limiter enforcing 60-second cooldown per retailer domain.
   - Circuit breaker tripping for 30 minutes on WAF / CAPTCHA blocks.
   - Policy manager returning operational status for all 5 retailers.

### B. Backend API Endpoints & Schemas
1. **`src/api/schemas.py`**:
   - Added `PriceCollectionResponseSchema`, `RetailerPolicyStatusSchema`, `RetailerPolicyListResponse`, `ProductRetailerSourceItemSchema`, `ProductRetailerSourcesResponse`, `AdminVerificationApprovalRequest`, `AdminVerificationRejectionRequest`, `AdminVerificationQueueResponse`, `EvidenceUploadResponse`.
   - Updated `ManualVerificationRequest` to support optional `evidence_url`.
2. **`src/api/main.py`**:
   - Registered `POST /api/verification/upload-evidence` (safe multipart image upload <5MB with UUID naming).
   - Registered `GET /api/verification/evidence/{filename}` (safe FileResponse with `os.path.basename` path traversal protection).
   - Registered `GET /api/admin/verifications` (requires admin privileges).
   - Registered `POST /api/admin/verifications/{id}/approve` & `reject`.
   - Registered `POST /api/admin/price-corrections/{id}/approve` & `reject`.
   - Registered `GET /api/prices/retailer-status`.
   - Registered `GET /api/prices/sources/{product_id}`.
   - Registered `POST /api/prices/collect/{product_id}`.
   - Registered `GET /api/prices/collection-status/{product_id}`.
   - Registered `POST /api/prices/refresh/{product_id}`.

### C. Frontend Enhancements
1. **`frontend/src/utils/api.ts`**:
   - Added TypeScript interfaces: `RetailerPolicyStatus`, `ProductRetailerSource`, `AdminVerificationItem`.
   - Added client functions: `getRetailerPolicies`, `getProductRetailerSources`, `collectProductPrices`, `uploadEvidenceFile`, `submitProductManualVerification`, `getAdminVerificationQueue`, `approveManualVerificationRequest`, `rejectManualVerificationRequest`, `approvePriceCorrectionSubmission`, `rejectPriceCorrectionSubmission`.
2. **`frontend/src/components/LiveRetailerPriceComparison.tsx`**:
   - Rendered 7 truth-in-advertising verification badges (`LIVE VERIFIED`, `MANUALLY VERIFIED`, `CACHED PRICE`, `HISTORICAL PRICE`, `POSSIBLE MATCH`, `DEMO PRICE (Simulated)`, `UNAVAILABLE`).
   - Integrated unit price display (`₹/ml`, `₹/g`).
   - Displayed required restricted retailer notice: *"Automatic price checking is currently unavailable for this retailer. Visit the retailer website to check its latest price."*
   - Added direct retailer outbound link buttons.
   - Added "Verify Retailer Price" button and modal allowing users to submit price, URL, and upload screenshot proof.
   - Added shortcut link to Admin Verification Queue for admin users.
3. **`frontend/src/pages/AdminVerificationPage.tsx`**:
   - New admin portal rendering pending manual verifications and price corrections.
   - Integrated screenshot proof viewer modal.
   - One-click approval and rejection controls with audit trail notes.
4. **`frontend/src/App.tsx`**:
   - Registered route `/admin/verifications`.

### D. Test Fixtures and Automation Suites
1. **`tests/fixtures/`**:
   - `myntra_sample.html`: Schema.org Product/Offer JSON-LD.
   - `purplle_sample.html`: OpenGraph and meta tag product HTML.
   - `size_variant_sample.html`: 60ml jumbo size variant.
   - `formulation_variant_sample.html`: 5% Niacinamide variant.
   - `shade_variant_sample.html`: M.A.C Velvet Teddy lipstick variant.
   - `bundle_sample.html`: Pack of 2 combo pack.
   - `akamai_blocked.html`: HTTP 403 "Access Denied" Akamai challenge.
   - `amazon_captcha.html`: "Robot Check" CAPTCHA form.
2. **`tests/test_phase11b_hybrid_intelligence.py`**:
   - 29 unit & integration tests covering extraction, WAF detection, SSRF, Gemini fallback, product matching, price verification, evidence persistence, and admin workflows.
3. **`scripts/test_phase11b_e2e_suite.py`**:
   - 5 Playwright end-to-end browser journeys saving 7 screenshots in `screenshots/phase11b/`.

---

## 5. Retailer Connector Status Matrix

| Retailer | Domain | Store ID | Phase 11B Operational Status | Permitted Methods | Perimeter Protection Handled |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Nykaa** | `nykaa.com` | 6 | `RESTRICTED` | Manual Verification, Partner Feed | Akamai WAF (HTTP 403 / RST) halts automation; trips circuit breaker; redirects to manual verification |
| **Tira Beauty** | `tirabeauty.com` | 7 | `RESTRICTED` | Manual Verification, Partner Feed | Akamai edge security halts automation; redirects to manual verification |
| **Purplle** | `purplle.com` | 8 | `PERMISSION_REVIEW_REQUIRED` | Manual Verification, Public Meta | React SPA hydration & ToS restrict automated extraction; manual verification workflow enabled |
| **Amazon India** | `amazon.in` | 9 | `RESTRICTED` | Manual Verification | Robot Check CAPTCHA halts automation; trips circuit breaker; redirects to manual verification |
| **Myntra** | `myntra.com` | 10 | `PERMISSION_REVIEW_REQUIRED` | Structured JSON-LD, Manual Verification | Schema.org JSON-LD extraction verified on permitted fixtures; live crawling paused pending permission review |

---

## 6. Data Classification & Strict Separation

In compliance with Phase 11B requirements, all data types are strictly separated across database tables and frontend displays:

| Data Classification | Source | Presentation Badge | Included in Genuine Market Statistics? | Evidence Stored? |
| :--- | :--- | :--- | :---: | :---: |
| **Genuine Extracted Data** | Permitted JSON-LD / HTML from authorized sources | `LIVE VERIFIED` (Emerald) | Yes | Yes (raw DOM snippet / URL) |
| **Manually Verified Data** | Admin-approved user submissions | `MANUALLY VERIFIED` (Sky Blue) | Yes | Yes (immutable screenshot / receipt in `evidence_references`) |
| **Cached Data** | Historical observation within TTL | `CACHED PRICE` (Amber) | Yes (with timestamp) | Yes |
| **Historical Data** | Past verified observations in `price_history` | `HISTORICAL PRICE` (Slate) | Yes | Yes |
| **Possible Match** | Mismatched size or shade without exact match | `POSSIBLE MATCH` (Purple) | No | Yes |
| **Restricted / Unavailable** | WAF-blocked or OOS retailer | `UNAVAILABLE` / Notice | No | Yes (block reason recorded) |
| **Demo Data** | Seed records from early development | `DEMO PRICE (Simulated)` (Orange) | **Strictly Excluded** | No |
| **Test Fixture Data** | Local HTML files in `tests/fixtures/` | Used strictly in automated tests | **Excluded from Production DB** | Test assertions |

---

## 7. Verification & Test Results

### A. Backend Unit & Integration Tests
Command: `py -3.14 -m pytest tests/test_phase11b_hybrid_intelligence.py -v`
```
tests/test_phase11b_hybrid_intelligence.py::TestWebExtraction::test_json_ld_extraction PASSED
tests/test_phase11b_hybrid_intelligence.py::TestWebExtraction::test_opengraph_meta_extraction PASSED
tests/test_phase11b_hybrid_intelligence.py::TestWebExtraction::test_html_dom_extraction PASSED
tests/test_phase11b_hybrid_intelligence.py::TestWebExtraction::test_full_pipeline_extracted_result PASSED
tests/test_phase11b_hybrid_intelligence.py::TestWafAndSecurityProtection::test_akamai_waf_detection PASSED
tests/test_phase11b_hybrid_intelligence.py::TestWafAndSecurityProtection::test_amazon_robot_check_captcha PASSED
tests/test_phase11b_hybrid_intelligence.py::TestWafAndSecurityProtection::test_ssrf_blocking_private_ip PASSED
tests/test_phase11b_hybrid_intelligence.py::TestWafAndSecurityProtection::test_ssrf_blocking_localhost PASSED
tests/test_phase11b_hybrid_intelligence.py::TestWafAndSecurityProtection::test_ssrf_blocking_unauthorized_domain PASSED
tests/test_phase11b_hybrid_intelligence.py::TestGeminiInterpretation::test_gemini_structured_interpretation PASSED
tests/test_phase11b_hybrid_intelligence.py::TestGeminiInterpretation::test_gemini_quota_error_fallback PASSED
tests/test_phase11b_hybrid_intelligence.py::TestGeminiInterpretation::test_gemini_impossible_price_guardrail PASSED
tests/test_phase11b_hybrid_intelligence.py::TestProductMatchingSevenTiers::test_exact_match PASSED
tests/test_phase11b_hybrid_intelligence.py::TestProductMatchingSevenTiers::test_size_variant_with_unit_price PASSED
tests/test_phase11b_hybrid_intelligence.py::TestProductMatchingSevenTiers::test_formulation_variant_concentration_difference PASSED
tests/test_phase11b_hybrid_intelligence.py::TestProductMatchingSevenTiers::test_shade_variant_difference PASSED
tests/test_phase11b_hybrid_intelligence.py::TestProductMatchingSevenTiers::test_bundle_match_detection PASSED
tests/test_phase11b_hybrid_intelligence.py::TestProductMatchingSevenTiers::test_no_match_brand_conflict PASSED
tests/test_phase11b_hybrid_intelligence.py::TestPriceVerificationService::test_deterministic_validation_guardrails PASSED
tests/test_phase11b_hybrid_intelligence.py::TestPriceVerificationService::test_evidence_reference_recording_and_retrieval PASSED
tests/test_phase11b_hybrid_intelligence.py::TestPriceVerificationService::test_admin_approval_and_rejection_workflow PASSED
tests/test_phase11b_hybrid_intelligence.py::TestRetailerAccessPolicies::test_all_five_retailers_configured PASSED
tests/test_phase11b_hybrid_intelligence.py::TestRetailerAccessPolicies::test_restricted_retailer_blocks_automated_collection PASSED
tests/test_phase11b_hybrid_intelligence.py::TestRetailerAccessPolicies::test_circuit_breaker_trips_on_block PASSED
tests/test_phase11b_hybrid_intelligence.py::TestRetailerAccessPolicies::test_domain_rate_limiter PASSED
tests/test_phase11b_hybrid_intelligence.py::TestApiEndpoints::test_get_retailer_status_endpoint PASSED
tests/test_phase11b_hybrid_intelligence.py::TestApiEndpoints::test_get_product_sources_endpoint PASSED
tests/test_phase11b_hybrid_intelligence.py::TestApiEndpoints::test_collect_prices_endpoint PASSED
tests/test_phase11b_hybrid_intelligence.py::TestApiEndpoints::test_admin_queue_requires_auth PASSED
======================= 29 passed, 2 warnings in 2.85s ========================
```

### B. Core Beauty Intelligence & Regression Suite
Command: `py -3.14 -m pytest tests/test_phase11b_hybrid_intelligence.py tests/test_phase10_beauty_intelligence.py tests/test_phase8e_beauty_intelligence.py -v`
```
======================= 69 passed, 3 warnings in 56.94s =======================
```
- **Phase 11B Hybrid Intelligence:** 29 passed.
- **Phase 10 Beauty Intelligence (Clash Matrix, Climate Advisor, Shade Matcher):** 22 passed.
- **Phase 8E Beauty Intelligence (Gemini Ingredient Analysis & Caching):** 18 passed.

### C. Frontend Build & Linter Checks
1. **TypeScript Production Build (`npm run build`):**
   ```
   ✓ 2517 modules transformed.
   dist/index.html                   1.60 kB
   dist/assets/index-DPbgi_UK.css   60.09 kB
   dist/assets/index-Bju0rCnD.js   867.24 kB
   ✓ built in 3.01s
   ```
2. **Frontend Linter (`npx oxlint`):**
   ```
   Found 16 warnings and 0 errors.
   Finished in 140ms on 54 files using 8 threads.
   ```

### D. Playwright E2E Browser Test Journeys
Command: `py -3.14 scripts/test_phase11b_e2e_suite.py`
```
[Journey 1] Testing Product Detail Page & Retailer Price Badges...
  [OK] Live price comparison section loaded.
  [OK] Restricted retailer warning message displayed clearly.
  [OK] Screenshot saved: screenshots/phase11b/01_product_price_comparison_badges.png

[Journey 2] Testing User Price Verification Submission Modal...
  [OK] Price verification modal opened.
  [OK] Screenshot saved: screenshots/phase11b/02_user_price_verification_modal.png
  [OK] Price verification submitted and confirmed.
  [OK] Screenshot saved: screenshots/phase11b/03_price_verification_submitted_success.png

[Journey 3] Testing Admin Price Verification Queue...
  [OK] Admin verification queue portal rendered.
  [OK] Screenshot saved: screenshots/phase11b/04_admin_verification_queue.png

[Journey 4] Testing Admin Approval Workflow...
  [OK] Admin approval modal opened.
  [OK] Screenshot saved: screenshots/phase11b/05_admin_approval_modal.png
  [OK] Price approved and published live!
  [OK] Screenshot saved: screenshots/phase11b/06_admin_queue_post_approval.png

[Journey 5] Verifying Updated Status on Product Detail Page...
  [OK] MANUALLY VERIFIED badge confirmed on product detail comparison table.
  [OK] Screenshot saved: screenshots/phase11b/07_product_manually_verified_badge.png
======================================================================
ALL 5 PHASE 11B E2E BROWSER JOURNEYS COMPLETED SUCCESSFULLY!
======================================================================
```

### E. Database Integrity Check
```
Integrity check: ok
Products count: 34
Offers count: 98
Price history rows: 948
Evidence references: 1
```

---

## 8. Captured Screenshots Index

All 7 browser journey screenshots have been persisted to `screenshots/phase11b/`:
1. `screenshots/phase11b/01_product_price_comparison_badges.png`: Retailer comparison section showing badges, unit prices (₹/ml), and the restricted retailer explanatory warning.
2. `screenshots/phase11b/02_user_price_verification_modal.png`: User price verification submission modal with inputs for Retailer, URL, Price, MRP, Size, and Screenshot upload.
3. `screenshots/phase11b/03_price_verification_submitted_success.png`: User submission success message and audit notice.
4. `screenshots/phase11b/04_admin_verification_queue.png`: Admin verification portal at `/admin/verifications` showing pending items, user submissions, and evidence links.
5. `screenshots/phase11b/05_admin_approval_modal.png`: Admin modal confirming verified selling price, MRP, and audit log notes.
6. `screenshots/phase11b/06_admin_queue_post_approval.png`: Admin queue showing item approved and removed from pending review.
7. `screenshots/phase11b/07_product_manually_verified_badge.png`: Product detail page displaying the `MANUALLY VERIFIED` badge with verified date.

---

## 9. Remaining Limitations & Next Phase Recommendations

1. **Automated Live Access Still Restricted for Certain Retailers:** Nykaa, Tira, and Amazon actively deploy perimeter WAFs and CAPTCHAs. As required, no bypass was attempted; the manual verification workflow and genuine direct retailer links serve as the compliant bridge.
2. **Permission Review for Feeds:** While Myntra exposes clean Schema.org JSON-LD and Purplle exposes OpenGraph metadata, commercial indexing without explicit partnership agreements requires ongoing compliance oversight.
3. **Database Records Preserved:** All 34 catalog products, historical price rows, and beauty intelligence features remain completely functional.

---

## 10. Conclusion & Stop Boundary

Phase 11B is **100% complete**. All non-negotiable requirements have been strictly met:
- Zero paid API subscriptions required.
- Zero WAF or security bypasses implemented.
- Hybrid architecture cleanly operational.
- Deterministic 7-tier product matching and unit price normalization active.
- Evidence references and admin audit workflow fully functioning.
- Frontend transparently distinguishes DEMO vs LIVE_VERIFIED and MANUAL_VERIFIED offers.

**In accordance with instructions, Phase 11C has NOT been started. Development is stopped here for your review and approval.**
