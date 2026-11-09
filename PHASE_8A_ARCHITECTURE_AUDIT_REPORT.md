# Phase 8A — Architecture Audit & Data-Source Strategy Report

**Date:** November 9, 2026  
**Repository Root:** `C:\Users\humai\price-comparison-website`  
**Classification:** Phase 8A — Audit Only (No Implementation)

---

## 1. Executive Summary

PriceWise AI has a **robust architectural foundation** for Phase 8, but the **data layer is demo-only** and the **live retailer pipeline is untested against real sites**. This report documents exactly what exists, what is missing, what is legally/technically risky, and proposes a concrete strategy for Phase 8B–8H.

**Verdict: Foundation is solid. Proceed to Phase 8B only after reviewing the three strategic decisions below.**

---

## 2. Existing Infrastructure Inventory

### 2.1 Backend Architecture (Complete ✅)

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| FastAPI bridge | `src/api/main.py` | ✅ Operational | 35 endpoints, CORS configured |
| SQLite database | `data/pricewise.db` | ✅ Operational | 352 KB, 16 tables |
| Adapter base class | `src/adapters/base_adapter.py` | ✅ Complete | 404 lines, rate limiting, capability status |
| Nykaa adapter | `src/adapters/nykaa_adapter.py` | ⚠️ Stub | Returns fallback when credentials missing |
| Myntra adapter | `src/adapters/myntra_adapter.py` | ⚠️ Stub | Same pattern |
| Purplle adapter | `src/adapters/purplle_adapter.py` | ⚠️ Stub | Same pattern |
| Tira adapter | `src/adapters/tira_adapter.py` | ⚠️ Stub | Same pattern |
| Amazon adapter | `src/adapters/amazon_adapter.py` | ⚠️ Stub | Same pattern |
| Adapter registry | `src/adapters/registry.py` | ✅ Complete | 6 adapters registered |
| Browser manager | `src/workers/browser_manager.py` | ✅ Complete | Playwright headless, resource blocking |
| Security policy | `src/workers/security_policy.py` | ✅ Complete | Domain allowlist, SSRF protection, private IP blocking |
| Live comparison engine | `src/services/live_comparison_engine.py` | ⚠️ Bug present | See §3.3 |
| Gemini service | `src/services/gemini_service.py` | ✅ Operational | `gemini-3.6-flash`, verified working |
| Deal detector | `src/analysis/deal_detector.py` | ✅ Complete | Rule-based scoring (0–100) |
| Price history service | `src/database/price_history_service.py` | ✅ Complete | Observation recording |
| Auth service | `src/services/auth_service.py` | ✅ Complete | PBKDF2, session tokens |
| Profile/routine/watchlist services | `src/services/` | ✅ Complete | All Phase 7 features |

### 2.2 Frontend Architecture (Complete ✅)

| Component | Status |
|-----------|--------|
| React 19 + TypeScript + Vite | ✅ Working |
| Tailwind CSS + framer-motion | ✅ Configured |
| Auth context + modals | ✅ Working |
| Product detail page | ✅ UI ready |
| Watchlist page | ✅ UI ready |
| Profile page | ✅ UI ready |
| Routines page | ✅ UI ready |
| Discovery homepage | ✅ UI ready |
| API client (`src/utils/api.ts`) | ✅ Working with fallbacks |
| Live comparison UI hooks | ⚠️ Not wired to backend yet |

### 2.3 Test Infrastructure (Mostly Complete ✅)

| Suite | Count | Status |
|-------|-------|--------|
| Phase 7 Auth | 8/8 | ✅ Pass |
| Full backend suite | 226/228 | ⚠️ 2 pre-existing failures (unrelated) |
| Frontend lint | 0 errors | ✅ Pass |
| Frontend build | ✅ Success | Built in ~7s |

---

## 3. Critical Findings

### 3.1 Database Contains Tech Products, Not Beauty Products ❗

**Current state:** The active database (`data/pricewise.db`) contains **32 technology products** (MacBook, laptops, etc.) sourced from `DEMO_PRODUCTS` in `seed.py`.

**Beauty seed data exists** in `src/database/beauty_seed_data.py` with ~20 Indian beauty products (sunscreens, serums, lipsticks) across Nykaa/Tira/Purplle/Amazon/Myntra — but it was **never seeded into the active database**.

This means the entire current catalog is **mismatched with the project's stated purpose** (Indian beauty & skincare price comparison).

**Impact:** Phase 8 cannot proceed with meaningful live product discovery until the database is repopulated with beauty products.

### 3.2 All Retailer Adapters Return Demo/Fallback Data

Every adapter reports `credentials=MISSING`:

| Retailer | Required Credentials | Current State |
|----------|---------------------|---------------|
| Nykaa | `NYKAA_API_KEY`, `NYKAA_PARTNER_SECRET` | Missing → demo fallback |
| Tira Beauty | `TIRA_PARTNER_TOKEN` | Missing → demo fallback |
| Purplle | `PURPLLE_FEED_URL`, `PURPLLE_API_KEY` | Missing → demo fallback |
| Amazon India | `AMAZON_PAAPI_KEY`, `AMAZON_PAAPI_SECRET` | Missing → demo fallback |
| Myntra | `MYNTRA_PARTNER_KEY`, `MYNTRA_AFFILIATE_ID` | Missing → demo fallback |

Without partner API credentials, adapters fall back to static demo prices that **do not reflect live market data**.

### 3.3 Live Comparison Engine Has a Bug

```
ERROR: AttributeError: 'LiveComparisonResult' object has no attribute 'status'
```

The engine's result dataclass does not expose a `.status` property that callers expect. This needs fixing before any live comparison can be tested end-to-end.

### 3.4 No Live Retailer Scraping Has Been Tested

While `BrowserManager` and `security_policy.py` are implemented, **no adapter has ever successfully navigated a real retailer page**. The adapters contain placeholder search URLs and DOM selectors that have not been validated against live Nykaa/Myntra/Purplle pages.

### 3.5 Frontend Uses Static Demo Data

The frontend's `PRODUCTS_DATA` in `src/data/products.ts` contains hardcoded tech products with static offers. The live comparison API endpoint (`/api/compare/auto`) works at the backend level but the frontend may not display results correctly if the `LiveComparisonResult` bug is unresolved.

---

## 4. Strategic Decisions Required Before Phase 8B

### Decision 1: How to Obtain Live Retailer Product Data

Three approaches are available. Each has different trade-offs:

| Approach | Effort | Legal Risk | Data Quality | Ongoing Cost |
|----------|--------|-----------|-------------|-------------|
| **A. Official Partner APIs** | Medium | None | High (authorized pricing) | API quotas, possible fees |
| **B. Permitted Web Scraping** | High | Moderate (ToS review needed) | Medium (DOM-dependent, fragile) | Maintenance as sites update |
| **C. Aggregator Feeds** | Low | Low (if using compliant source) | High | License fees |

**Recommendation:** Pursue **Approach A first** (partner/affiliate programs) for Nykaa and Amazon India PA-API 5.0. These have documented affiliate programs. Use **Approach B selectively** only for retailers without APIs, and only after legal review of their ToS.

### Decision 2: Whether to Repopulate the Database with Beauty Products

The current tech-product catalog makes the platform feel like a generic electronics comparer, not a beauty intelligence dashboard. Two options:

- **Option A:** Re-seed with beauty products from `beauty_seed_data.py` + add more products manually. Faster, keeps existing test structure intact.
- **Option B:** Build a beauty-first catalog from scratch with richer specs, ingredients, and skin-type tagging. Higher quality, more time.

**Recommendation:** Start with Option A (re-seed existing beauty data), then expand incrementally during Phase 8B–8D.

### Decision 3: Scope of Live Scraping in Phase 8B–8C

Given that all five retailers require either API credentials or careful scraping implementation, Phase 8B should **focus on one retailer as a proof-of-concept** rather than attempting all five simultaneously.

**Recommendation:** Start with **Nykaa** (largest Indian beauty retailer, most likely to have an affiliate program) and implement one working live flow end-to-end before scaling to other retailers.

---

## 5. Proposed Phase 8 Sub-Phase Plan

### Phase 8A — Architecture Audit & Data-Source Strategy *(THIS PHASE)*
- ✅ Complete this report
- Awaiting your approval on the three strategic decisions above

### Phase 8B — Database Migration & Catalog Foundation
- Re-seed database with beauty products from `beauty_seed_data.py`
- Add 10–15 additional high-demand beauty products with full spec sheets
- Verify all Phase 1–7 tests still pass after re-seeding
- Output: Updated `pricewise.db` with beauty-first catalog (~50 products)

### Phase 8C — Nykaa Live Integration (Single Retailer POC)
- Research Nykaa affiliate/partner program eligibility
- Implement Nykaa adapter with real Playwright navigation to nykaa.com
- Extract: product title, price, MRP, discount %, shipping, stock status, URL
- Store results in `price_check_logs` with source_type=`verified_live`
- Handle: CAPTCHA detection, 403 blocks, rate limits gracefully
- Output: One fully working live retailer pipeline

### Phase 8D — Multi-Retailer Expansion
- Replicate Nykaa pattern for Myntra and Amazon India
- Skip Tira/Purplle unless affiliate APIs are obtainable (document why)
- Implement cross-retailer deduplication (same product, different SKU formats)
- Output: 3 live retailer pipelines

### Phase 8E — Reviews & Deal Intelligence
- Enrich product data with cross-platform ratings where available
- Implement deal confidence scoring (historical price + current discount)
- Add "Best Deal" badge logic to frontend
- Output: Review aggregation + deal detection pipeline

### Phase 8F — Alternatives & Gemini-Powered Beauty Intelligence
- Implement dupe/alternative recommendation engine using ingredient overlap
- Wire Gemini into product detail pages for ingredient education
- Add natural-language search ("find me a sunscreen for oily acne-prone skin under ₹500")
- Output: AI-powered discovery features

### Phase 8G — Premium Frontend Integration
- Redesign product detail pages with live comparison results
- Add deal badges, dupe cards, ingredient callouts
- Optimize for performance (lazy loading, virtual scrolling for comparisons)
- Output: Polished beauty-commerce frontend

### Phase 8H — Full Integration & Acceptance Testing
- End-to-end flow: search → discover → compare → track → alert
- Load testing with realistic product volumes
- Final regression suite
- Output: Production-ready Phase 8

---

## 6. Known Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Nykaa blocks headless Chrome | High | Blocker for 8C | Rotate user-agents, add delays, detect CAPTCHA, degrade to demo |
| Amazon PA-API requires approved associate account | High | Blocks live Amazon data | Use demo data with clear labeling; apply for PA-API separately |
| Myntra/Purplle terms prohibit scraping | Medium | Legal risk | Consult legal; limit to public product pages only; respect robots.txt |
| Playwright maintenance overhead | High | Ongoing cost | Abstract selectors into config files; version-lock Chromium |
| Rate limits on live requests | Medium | Slow comparisons | Implement caching (already have 10-min TTL); batch requests |
| Beauty seed data incomplete | Medium | Limited catalog | Augment during 8B with manual product entry |

---

## 7. Files That Will Be Created or Modified

| Phase | Files Changed/Created |
|-------|----------------------|
| 8B | `src/database/beauty_seed_data.py` (expand), `src/database/seed.py` (update), new test file |
| 8C | `src/adapters/nykaa_adapter.py` (rewrite live logic), `tests/test_phase8_nykaa.py` |
| 8D | `src/adapters/myntra_adapter.py`, `src/adapters/amazon_adapter.py` (live implementations) |
| 8E | `src/services/review_aggregation.py`, `src/analysis/deal_detector.py` (enhanced) |
| 8F | `src/services/alternative_service.py` (enhanced), `src/services/gemini_service.py` (new prompts) |
| 8G | `frontend/src/pages/ProductDetailPage.tsx`, `frontend/src/components/*` (multiple) |
| 8H | `tests/test_phase8_integration.py` (expanded) |

**No database schema changes are required** — all Phase 8 data fits within existing tables.

---

## 8. Next Action

Please confirm or modify the following before Phase 8B begins:

1. **Strategic Decision 1:** Which data-source approach? (Recommended: Partner APIs first, selective scraping second)
2. **Strategic Decision 2:** Re-seed with existing beauty data or build new catalog? (Recommended: Re-seed existing)
3. **Strategic Decision 3:** Single-retailer POC first? (Recommended: Nykaa only for 8C)
4. **Any retailers to exclude** from Phase 8? (e.g., if Amazon PA-API is unavailable, deprioritize)
5. **Priority order** if scope must be trimmed (e.g., skip reviews, focus on price comparison only)

Once approved, Phase 8B (database migration) will begin immediately.

---

*Phase 8A completed. Awaiting user approval before proceeding.*
