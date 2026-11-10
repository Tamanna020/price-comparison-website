# PHASE 13.8 — PRICEWISE AI LIVE WEBSITE REAL DATA AUDIT REPORT

**Audit Date / Time:** 2026-11-09 21:09 – 21:29 UTC  
**Auditor:** Antigravity AI (Read-Only, No Code Modifications)  
**Audit Method:** Live HTTP API calls to deployed endpoints, source-code static inspection, offer-URL verification  
**Screenshots:** NOT CAPTURED — Browser Automation MCP was not enabled during this audit  

---

## DEPLOYED TARGETS

| Component | URL | Status |
|-----------|-----|--------|
| **Frontend** | https://pricewise-staging.vercel.app/ | ✅ HTTP 200 — Vercel serving |
| **Backend** | https://pricewise-backend-staging.onrender.com/ | ✅ HTTP 200 — Render/uvicorn responding |
| **OpenAPI Docs** | /openapi.json | ✅ Available |

---

## PART 1 — DEPLOYMENT STATUS & HEALTH

### 1.1 Vercel Frontend

| Check | Result | Evidence |
|-------|--------|----------|
| HTTP status | **200 OK** | `HTTP/2 200` |
| Response time | **~227ms** | `TIME_TOTAL: 0.226798s` |
| Content type | `text/html; charset=utf-8` | Response header |
| CDN | Vercel Edge (`x-vercel-cache: HIT`) | Response header |
| Security headers | ✅ X-Content-Type-Options, X-Frame-Options, Referrer-Policy set | vercel.json + headers |

**Finding:** Frontend is live and being served from Vercel's CDN edge. Static assets are cached with 1-year immutable headers.

### 1.2 Render Backend — Health Endpoints

| Endpoint | HTTP Status | Response Time | Key Fields |
|----------|------------|---------------|------------|
| `GET /api/health/live` | **200** | 466ms | `{"status":"alive","timestamp":"2026-11-09T21:22:43.451263+00:00"}` |
| `GET /api/health/ready` | **200** | 1,011ms | `{"status":"ready","database_engine":"postgresql","database_healthy":true,"product_count":113,"latency_ms":594.22,"environment":"staging"}` |
| `GET /api/health` | **200** | 1,047ms | `{"status":"ok","app_name":"PriceWise AI Beauty","version":"1.0.0","database":"postgresql","record_count":113}` |

**Findings:**
- Backend is **alive and responsive** (no cold-start penalty observed in these tests).
- PostgreSQL (Neon) is **connected and healthy**, responding in ~594ms.
- `environment: "staging"` is confirmed.
- `record_count: 113` — the backend reports 113 products in its database.
- **CAUTION:** Render's free tier spins down after 15 minutes of inactivity. Cold-start latency for first requests can reach 20–60 seconds. This was not observed during the audit window.

### 1.3 Frontend → Backend Connectivity

**Configuration found in `frontend/.env.production`:**
```
VITE_API_URL=https://pricewise-backend-staging.onrender.com
VITE_API_BASE_URL=https://pricewise-backend-staging.onrender.com
```

**`frontend/src/utils/api.ts` — `getBaseApiUrl()` logic:**
- Reads `VITE_API_BASE_URL` or `VITE_API_URL` from Vite environment.
- These are baked into the Vercel build at deploy time.
- The deployed frontend therefore points to the correct Render backend URL.
- **Fallback mechanism:** If the backend is unreachable, the frontend silently falls back to `frontend/src/data/products.ts` (the static TypeScript catalog) — this means users may see product data even when the backend is offline, with **no visible warning** that the backend is unavailable.

**CORS check:**
- `GET /api/health/live` with `Origin: https://pricewise-staging.vercel.app` returned:
  - `access-control-allow-credentials: true`
  - `access-control-expose-headers: X-Process-Time`
- The CORS origin `https://pricewise-staging.vercel.app` is explicitly listed in `render.yaml` (`CORS_ORIGINS`).
- **Result: CORS is configured correctly for the staging frontend.** ✅

**Verdict: Frontend/backend connectivity: PASS**

---

## PART 2 — PRODUCT CATALOGUE AUTHENTICITY

### 2.1 Database vs Frontend Catalogue

| Metric | Backend DB (PostgreSQL/Neon) | Frontend (TypeScript `products.ts`) |
|--------|------------------------------|--------------------------------------|
| Total products | **113** | **~100** (confirmed in source) |
| Non-beauty products | **11** (Laptops, Phones, TVs, etc.) | **0** (all beauty/skincare) |
| Beauty/skincare products | **102** | ~100 |

**Critical Finding — Non-Beauty Products in the Database:**  
The Neon PostgreSQL database contains **11 non-beauty products** seeded from the original pre-beauty `seed.py`:

| ID | Brand | Category | Title |
|----|-------|----------|-------|
| 1 | Apple | Laptops | MacBook Pro 14" (M3 Pro, 18GB RAM, 512GB SSD) |
| 2 | Dell | Laptops | Dell XPS 15 OLED |
| 3 | Samsung | Smartphones | Galaxy S24 Ultra 5G |
| 4 | Apple | Smartphones | iPhone 15 Pro |
| 5 | Sony | Audio | WH-1000XM5 Headphones |
| 6 | Bose | Audio | QuietComfort Ultra |
| 7 | Sony | Gaming | PlayStation 5 Slim |
| 8 | Apple | Wearables | Apple Watch Series 9 |
| 9 | Dell | Monitors | UltraSharp 27 4K |
| 10 | Sony | Cameras | Alpha 7 IV |
| 11 | LG | TVs | C3 Series 65" OLED |

These are **demo electronics products** with USD-denominated prices (`source_type: "demo"`) from stores like `TechMart (Demo)`, `ElectroHub (Demo)`, `Apex Direct (Demo)` — all pointing to fake domains (`techmart-demo.example.com`, etc.).

The seed file explicitly states:
> `"ALL DATA IS DEMO DATA FOR ACADEMIC PROTOTYPE PURPOSES."`

### 2.2 Beauty Product Authenticity

**Products 1001–1112 (102 products):**

| Subcategory | Count |
|------------|-------|
| Sunscreens | 15 |
| Serums | 18 |
| Moisturizers | 15 |
| Face Cleansers | 13 |
| Foundations | 12 |
| Lipsticks | 11 |
| Concealers | 7 |
| Blushes, Lip Care, Mascaras, etc. | ~11 |

**Data authenticity per product record:**
- Product titles correspond to **real, commercially available Indian beauty products** (e.g., Dot & Key Watermelon Sunscreen, Minimalist 10% Niacinamide, The Ordinary Niacinamide 10% + Zinc 1%).
- `dataStatus: "catalog_verified"` and `dataSource: "Manufacturer Official Specification / Open Beauty Facts Reference"` are set in the TypeScript catalog.
- **However**, "catalog_verified" means the brand and product name were cross-referenced against manufacturer websites — it does **not** mean prices, images, or retailer offers were independently verified in real time.
- Ingredients listed in `keyIngredients` are plausible and consistent with publicly known formulations for these products.
- **Classification: PARTIALLY_VERIFIED** — Product identity (brand, name, formulation type) corresponds to real products. Prices, images, and retailer links are NOT independently verified.

| Classification | Count | % |
|---------------|-------|---|
| PARTIALLY_VERIFIED (product identity real, data demo) | 102 | 90.3% |
| DEMO_PRODUCT (non-beauty, fictional stores) | 11 | 9.7% |
| VERIFIED_PRODUCT (live price evidence) | 0 | 0% |
| INVALID_PRODUCT | 0 | 0% |

---

## PART 3 — PRODUCT IMAGE AUDIT

### 3.1 Image Source Analysis

**100% of product images use Unsplash stock photography.**

| Metric | Result |
|--------|--------|
| Total product image slots | 113 |
| Images from `images.unsplash.com` | 111 (98.2%) |
| Missing image (NO_IMAGE) | 2 (1.8%) |
| Unique Unsplash photo IDs used | **22 unique images** across 111 products |

### 3.2 Image Reuse — Critical Finding

The 102 beauty products are covered by only **~16 distinct Unsplash stock photos**, with the same images reused heavily across unrelated products:

| Unsplash Photo ID (abbreviated) | Used by X Products | What it shows |
|---|---|---|
| `1598440947619-2c35fc9aa908` | **19 products** | Generic skincare/cream product |
| `1556228720-195a672e8a03` | **18 products** | Generic beauty product |
| `1522335789203-aabd1fc54bc9` | **16 products** | Makeup/cosmetics |
| `1586495777744-4413f21062fa` | **9 products** | Generic lipstick/beauty |
| `1620916566398-39f1143ab7be` | **8 products** | Serum/dropper bottle |
| `1608248597359-25f0376ef79d` | **7 products** | Skincare |

**Examples of incorrect image assignment:**
- Nykaa Niacinamide Foundation and Cetaphil Cleanser share the same stock makeup photo.
- Lipsticks, serums, sunscreens, and concealers frequently share the same image.
- Dot & Key Barrier Repair Lip Butter and Laneige Lip Mask share the same image.

**No product image has been verified to show the actual product, its packaging, its shade, or its size.**

### 3.3 Image Classification

| Classification | Count | % |
|---------------|-------|---|
| PLACEHOLDER (generic stock photo, not product-specific) | 111 | 98.2% |
| NO_IMAGE | 2 | 1.8% |
| VERIFIED_MATCH | 0 | 0% |
| POSSIBLE_MATCH | 0 | 0% |

---

## PART 4 — RETAILER PRICE AUTHENTICITY

### 4.1 Source Type Distribution

**Frontend static catalog (`products.ts`):**

| Source Type | Offer Count | % of Total |
|-------------|-------------|------------|
| `demo` | 440 | 98.2% |
| `partner_feed` | 8 | 1.8% |
| `live` / `verified_live` | **0** | **0%** |
| `manual_verified` | **0** | **0%** |
| `cached` | **0** | **0%** |

> Note: The `partner_feed` entries are for Purplle on product `prod-01` only — no evidence of an actual active partner feed was found in the codebase.

**Backend database (Neon PostgreSQL) — sampled detail endpoints:**

All 5 retailer offers for every inspected beauty product carry `source_type: "demo"`.  
Store names confirm this: `"Nykaa (Demo)"`, `"Amazon India (Demo)"`, `"Tira (Demo)"`, `"Myntra (Demo)"`, `"Purplle (Demo)"`.

Example — Product 1001 (Aqualogica Glow+ Dewy Sunscreen):
```json
{ "store_name": "Nykaa (Demo)", "current_price": 399.0, "source_type": "demo",
  "offer_url": "https://www.nykaa.com/beauty-aqual-glow-sun-50/p/1001",
  "last_checked": "2026-11-09 16:51:12+00:00" }
```

| Classification | Count (estimated from sampling) | % |
|---------------|--------------------------------|---|
| DEMO | ~565 (all beauty offers) | ~100% |
| LIVE_VERIFIED | 0 | 0% |
| MANUAL_VERIFIED | 0 | 0% |
| CACHED | 0 | 0% |
| HISTORICAL | 0 | 0% |

### 4.2 Last-Checked Timestamps

The `last_checked` timestamps in the database are set to a single ingestion time (approximately `2026-11-09 16:51:12+00:00` for beauty products), indicating they were created when the expanded catalog was seeded — **not updated since then**.

### 4.3 Price Accuracy Assessment

Prices in the database appear to be **internally consistent** (Purplle is typically cheapest, Myntra most expensive, with ~5–10% spread), but they are:
- **Not sourced from any retailer API.**
- **Not scraped from any retailer website** (retailer policy status shows all 5 retailers are RESTRICTED or pending permission review).
- **Not manually verified** (no manual verification records found).
- **Arithmetically generated** (each product's 5 retailer prices follow a fixed percentage pattern relative to a base price).

---

## PART 5 — AUTOMATIC PRICE UPDATE MECHANISM

### 5.1 Scheduler / Background Worker

**Finding: NO automated price scheduler exists in the deployed application.**

Evidence:
- `Procfile`: `web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
  — Only a single web process. No `worker:` or `scheduler:` process type.
- `render.yaml`: Only one service defined (`type: web`). No background worker, cron job, or scheduled job service.
- Source code search: `scheduler`, `APScheduler`, `Celery`, `crontab`, `cron` — found **only in** `src/database/seed.py` and `src/database/price_history_service.py` as reference comments, **not in any deployed process**.
- No `requirements.txt` entries for Celery, APScheduler, RQ, or any task queue.

### 5.2 `/api/prices/retailer-status` Endpoint — Live API Response

All 5 retailers are either **RESTRICTED** or **PERMISSION_REVIEW_REQUIRED**:

| Retailer | Policy Status | Permitted Methods | Automated Collection? |
|----------|--------------|-------------------|-----------------------|
| Nykaa | **RESTRICTED** | `manual_verification`, `partner_feed` | ❌ No |
| Tira Beauty | **RESTRICTED** | `manual_verification`, `partner_feed` | ❌ No |
| Purplle | **PERMISSION_REVIEW_REQUIRED** | `manual_verification`, `public_meta_tags` | ❌ No |
| Amazon India | **RESTRICTED** | `manual_verification` | ❌ No |
| Myntra | **PERMISSION_REVIEW_REQUIRED** | `structured_json_ld`, `manual_verification` | ❌ No |

### 5.3 `/api/compare/auto` — Live Comparison Engine Result

Tested for Product ID 1 (MacBook Pro) and Product ID 1001 (Aqualogica Sunscreen):

**Both returned:**
```json
{
  "retailers_checked": 5,
  "retailers_retrieved": 0,
  "retailers_unavailable": 5,
  "source_type": "unavailable",
  "validation_notes": "Retailer feed currently unavailable (Error)"
}
```

The live comparison engine:
1. Calls `GeminiService.generate_search_query()` — requires `GEMINI_API_KEY` env var.
2. Attempts to use each retailer adapter.
3. Each adapter checks for API credentials (`NYKAA_API_KEY`, `NYKAA_PARTNER_SECRET`, etc.) — none are configured in the staging environment.
4. Each adapter returns `source_type: "unavailable"` with the error message.

**Conclusion: Real-time price collection is NOT running. Automated price updates do NOT occur.**

---

## PART 6 — BUY NOW LINK AUDIT

### 6.1 Frontend Static Catalog Links (448 total purchase URLs)

| Classification | Count | % |
|---------------|-------|---|
| **GENERIC_SEARCH_LINK** (bare homepage: `https://www.nykaa.com`, etc.) | **63** | 14.1% |
| **SYNTHETIC_LINK** (fake/constructed product paths) — Amazon `/dp/BEAUTY-*` | **77** | 17.2% |
| **SYNTHETIC_LINK** — Nykaa `/beauty-*/p/1001` | **77** | 17.2% |
| **SYNTHETIC_LINK** — Tira `/product/beauty-*` | **77** | 17.2% |
| **SYNTHETIC_LINK** — Myntra `/beauty-*/buy` | **77** | 17.2% |
| **SYNTHETIC_LINK** — Purplle `/product/beauty-*` | **77** | 17.2% |
| **EXACT_PRODUCT_LINK** (real ASIN or real product slug) | **0** | **0%** |

**Total EXACT_PRODUCT_LINK: 0 out of 448 (0%)**

### 6.2 Link Verification Tests

| URL Tested | HTTP Response | Classification |
|-----------|--------------|----------------|
| `https://www.amazon.in/dp/BEAUTY-DOTKEY-VITC-20-30` | **HTTP 405** | BROKEN_LINK / SYNTHETIC |
| `https://www.nykaa.com/beauty-dotkey-vitc-20-30/p/1001` | **HTTP 403** (Akamai WAF) | BROKEN_LINK / SYNTHETIC |
| `https://www.purplle.com/product/beauty-dotkey-vitc-20-30` | **HTTP 404** | BROKEN_LINK / SYNTHETIC |
| `https://www.myntra.com/beauty-dotkey-vitc-20-30/buy` | No response / timeout | BROKEN_LINK / SYNTHETIC |

### 6.3 Backend Database Links (sampled from API)

The backend also uses the same synthetic URL patterns in its offer records:
- `https://www.nykaa.com/beauty-aqual-glow-sun-50/p/1001` (all Nykaa offers share `/p/1001`)
- `https://www.amazon.in/dp/BEAUTY-AQUAL-GLOW-SUN-50`
- `https://www.tirabeauty.com/product/beauty-aqual-glow-sun-50`

None of these are real product URLs. All would return 403, 404, or 405.

---

## PART 7 — DEAL CALCULATION ACCURACY

### 7.1 Discount Arithmetic

The arithmetic of discounts is internally consistent (e.g., Purplle's total cost = listed_price + ₹49 shipping). However:

- **MRP values are demo data**, not verified against any manufacturer or retailer.
- **Coupon codes** (e.g., `NYKBEAUTY10`) are simulated — the test suite explicitly labels them `is_simulated: True`, `source: "simulated"`, with disclaimers such as "has not been verified."
- **Deal scoring** is explicitly labeled `is_simulated_deal: True`, `source_status: "DEMO"`, `verified_deal_eligible: False` in the backend logic.
- **Deal expiry tags** (e.g., `dealExpiresAt: '15 Nov 2026'`) are static hardcoded strings, not driven by any live data feed.

### 7.2 Price History Endpoint

`GET /api/products/1001/price-history` → **HTTP 500 Internal Server Error**

The price history endpoint is broken in the deployed environment. This means:
- Historical price charts cannot be displayed.
- "Lowest in 30 Days" and "30-day price trend" labels shown in the frontend have no live data backing them.

### 7.3 Deal Intelligence Endpoint

`GET /api/products/1001/deal-intelligence` → **HTTP 500 Internal Server Error**

The deal intelligence endpoint is also broken in deployment.

---

## PART 8 — REVIEWS AND ALTERNATIVES

### 8.1 Reviews

**Classification: DEMO**

Evidence:
- All reviews in `frontend/src/data/reviews.ts` have no `sourceUrl` with a real deep link to a verified review page — they link only to retailer homepages.
- All reviews in `frontend/src/data/products.ts` carry `dataStatus: 'demo'`.
- No backend review API endpoint exists (`/api/reviews` is not in the OpenAPI spec).
- Review authors are fictional composite personas (e.g., "Ananya Sharma," "Dr. Neha Saxena").
- Dates are within the Oct–Nov 2026 timeframe (consistent with project creation).

| Classification | Count |
|---------------|-------|
| DEMO / Simulated | 100% |
| Genuine external reviews | 0% |

### 8.2 Platform Ratings

`platformRatings` entries in the catalog carry `dataSource: "Retailer Feed (Demo)"` — confirming they are not from real retailer APIs.

### 8.3 Alternatives / Dupes

The `alternatives.ts` data contains curated product comparisons (e.g., Charlotte Tilbury Hollywood Flawless Filter vs Maybelline Age Rewind Glow). These:
- Reference real products and plausible ingredient overlap.
- Use Unsplash stock photos (not real product images).
- Prices are hardcoded demo values.
- **Classification: PARTIALLY_VERIFIED** — Product comparisons are conceptually valid (real brands, real products) but prices and images are not verified.

---

## PART 9 — UI AND USER JOURNEY TESTING

> **⚠ NOTE: Browser Automation MCP was not available during this audit.**  
> Desktop and mobile screenshots could not be captured. The findings below are based on HTTP responses, source code, and API payloads.

### 9.1 Backend API Timing

| Endpoint | Response Time | Note |
|----------|--------------|------|
| `/api/health/live` | 466ms | ✅ |
| `/api/health/ready` | 1,011ms | ✅ |
| `/api/health` | 1,047ms | ✅ |
| `/api/products` (all 113) | **8,579ms** | ⚠ SLOW — will hit frontend's 4s timeout |
| `/api/products/1001` | 1,429ms | ✅ |
| `/api/prices/retailer-status` | ~2,000ms | ✅ |
| `/api/compare/auto?product_id=1001` | **~28,430ms** | ❌ Exceeds all browser timeouts |

### 9.2 Frontend Fallback Behaviour

The frontend is coded with a **silent fallback**: if the backend `/api/products` call fails or times out, it uses the local TypeScript `PRODUCTS_DATA`. This means users will see beauty product data even if the backend is down — but the displayed data is the static demo catalog (which may be inconsistent with what the database actually contains).

---

## PART 10 — AUTOMATIC UPDATE CAPABILITY SUMMARY

| Check | Finding | Status |
|-------|---------|--------|
| Background worker process | None defined in `Procfile` or `render.yaml` | ❌ NOT IMPLEMENTED |
| Scheduler (APScheduler, Celery, etc.) | Not in `requirements.txt`, not in codebase | ❌ NOT IMPLEMENTED |
| Cron job on Render | No cron service defined in `render.yaml` | ❌ NOT IMPLEMENTED |
| Nykaa API credentials | `NYKAA_API_KEY` / `NYKAA_PARTNER_SECRET` not set | ❌ NOT CONFIGURED |
| Amazon PAAPI credentials | No Amazon affiliate API env vars | ❌ NOT CONFIGURED |
| Tira partner feed | No credentials | ❌ NOT CONFIGURED |
| Purplle permission review | Pending, no approval received | ❌ PENDING |
| Myntra structured data | Pending permission review | ❌ PENDING |
| Last automated price collection | Never (all timestamps are from seed ingestion) | ❌ |

**Conclusion: Automatic price collection is NOT running and has NEVER run on the deployed platform.**

---

## PART 11 — FINAL DATA AUTHENTICITY SCORECARD

### 11.1 Product Authenticity

| Metric | Count | % |
|--------|-------|---|
| Total products in database | 113 | 100% |
| Beauty/skincare products (real brand/product identity) | 102 | 90.3% |
| Non-beauty demo products (electronics, fictional stores) | 11 | 9.7% |
| Products with live/verified prices | **0** | **0%** |
| Products with manually verified prices | **0** | **0%** |

### 11.2 Product Images

| Metric | Count | % |
|--------|-------|---|
| Total image slots | 113 | 100% |
| Generic Unsplash stock photos (not product-specific) | 111 | 98.2% |
| Missing image | 2 | 1.8% |
| Verified correct product image | **0** | **0%** |
| Unique images for 111 products | **22** | — |

### 11.3 Retailer Offers

| Metric | Count | % |
|--------|-------|---|
| Total retailer offer records (estimated 113 × avg 4.5) | ~565 | 100% |
| `source_type: "demo"` | ~565 | ~100% |
| `source_type: "live"` or `"verified_live"` | **0** | **0%** |
| `source_type: "manual_verified"` | **0** | **0%** |
| `source_type: "partner_feed"` | ~8 (Purplle on prod-01 only) | ~1.4% |

### 11.4 Retailer Links

| Metric | Count | % |
|--------|-------|---|
| Total purchaseUrl entries in frontend catalog | 448 | 100% |
| Generic homepage URLs (no product path) | 63 | 14.1% |
| Synthetic constructed URLs (all retailers) | 385 | 85.9% |
| Real, verified exact-product URLs | **0** | **0%** |

---

## PART 12 — FEATURE-BY-FEATURE STATUS

| Feature | Status | Evidence |
|---------|--------|----------|
| Frontend deployment (Vercel) | ✅ FULLY WORKING | HTTP 200, CDN HIT |
| Backend deployment (Render) | ✅ FULLY WORKING | Health endpoints returning 200 |
| PostgreSQL (Neon) connectivity | ✅ FULLY WORKING | `database_healthy: true`, 594ms latency |
| CORS configuration | ✅ FULLY WORKING | Headers verified |
| Frontend → Backend URL config | ✅ FULLY WORKING | `.env.production` correct |
| Product catalogue (113 products) | ⚠ WORKING WITH DEMO DATA | Beauty products real identity, demo prices |
| Product images | ⚠ WORKING WITH DEMO DATA | Generic Unsplash stock photos |
| Retailer price comparison display | ⚠ WORKING WITH DEMO DATA | Prices shown but all `source_type: "demo"` |
| Live price comparison engine | ❌ NOT WORKING | All retailers "unavailable" (Error) |
| Retailer API integration (Nykaa) | ❌ NOT IMPLEMENTED | No credentials, no live calls |
| Retailer API integration (Amazon) | ❌ NOT IMPLEMENTED | No credentials, bot-blocked |
| Retailer API integration (Tira) | ❌ NOT IMPLEMENTED | RESTRICTED (Akamai WAF) |
| Retailer API integration (Purplle) | ❌ NOT IMPLEMENTED | Permission review pending |
| Retailer API integration (Myntra) | ❌ NOT IMPLEMENTED | Permission review pending |
| Buy Now links | ❌ ALL BROKEN (all synthetic) | 0/448 real product URLs |
| Price history charts | ❌ BROKEN | HTTP 500 |
| Deal intelligence | ❌ BROKEN | HTTP 500 |
| Automated price updates / scheduler | ❌ NOT IMPLEMENTED | No worker, no cron |
| Coupon codes | ⚠ SIMULATED | Explicitly marked `is_simulated: True` |
| Reviews | ⚠ WORKING WITH DEMO DATA | All `dataStatus: "demo"` |
| Alternatives / Dupes | ⚠ WORKING WITH DEMO DATA | Conceptually valid, prices demo |
| Auth (register/login) | ✅ PARTIALLY WORKING | Endpoints exist, not load-tested |
| Wishlist | ✅ PARTIALLY WORKING | Endpoints exist |
| Price alerts | ⚠ PARTIALLY WORKING | No live trigger mechanism |
| Ingredient analysis | ✅ PARTIALLY WORKING | Endpoints exist, real ingredient data |
| Gemini Beauty Assistant | NOT VERIFIED | Requires auth + GEMINI_API_KEY |
| Mobile layout | NOT VERIFIED | Browser Automation MCP unavailable |
| Desktop layout | NOT VERIFIED | Browser Automation MCP unavailable |

---

## PART 13 — CRITICAL FAILURES AND WARNINGS

### 🔴 Critical Failures

1. **ALL BUY NOW LINKS ARE SYNTHETIC/BROKEN** — Not one of the 448 retailer purchase URLs in the system points to a real product page. Amazon URLs use fake ASIN-format strings (`BEAUTY-*`). Nykaa URLs use a constant product ID `/p/1001`. Purplle and Myntra URLs return 404.

2. **LIVE PRICE COMPARISON ENGINE RETURNS NO DATA** — `/api/compare/auto` returns `"unavailable"` for all 5 retailers on every product tested. Users clicking "Compare Live Prices" will see no results.

3. **PRICE HISTORY AND DEAL INTELLIGENCE ENDPOINTS RETURN HTTP 500** — Two core features (price charts, deal scoring) are broken in the deployed environment.

4. **ALL RETAILER PRICES ARE DEMO DATA** — No price in the system has been sourced from a real retailer API, real web extraction, or verified manual check. All offers show `source_type: "demo"` or store names with `(Demo)` suffix.

5. **ALL PRODUCT IMAGES ARE GENERIC STOCK PHOTOS** — 22 Unsplash images are reused across 111 products. The same photo appears for sunscreens, foundations, serums, and lipsticks simultaneously.

6. **11 NON-BEAUTY PRODUCTS IN DATABASE** — Electronics (MacBook Pro, iPhone, Sony headphones, etc.) with USD prices and fake store domains are present in the production database.

### 🟡 Warnings

7. **Backend cold-start latency (Render free tier)** — First request after 15 minutes idle can take 20–60+ seconds, causing the frontend's 4-second timeout to fire, forcing fallback to static demo data.

8. **`/api/products` endpoint too slow (8.5 seconds)** — Will reliably cause frontend timeout under normal load.

9. **Silent fallback masks backend failures** — Frontend falls back to static demo data with no visible warning to the user.

10. **Coupon codes are simulated** — `NYKBEAUTY10`, `PURPLLE50`, etc. are not real coupon codes and are explicitly flagged `is_simulated: True` in the backend service layer, but this disclaimer may not be visible to end users.

11. **`dealExpiresAt` is a hardcoded static string** — Not driven by any real data feed.

12. **Reviews are entirely fictional** — Authors, dates, and content are not from verified real purchases.

---

## PART 14 — RECOMMENDED FIXES (PRIORITY ORDER)

| Priority | Issue | Recommended Action |
|----------|-------|-------------------|
| **P0** | Buy Now links are all synthetic | Replace all purchaseUrls with real product URLs from each retailer. Requires manual curation for each of the 102 beauty products × 5 retailers. |
| **P0** | `/api/products/{id}/price-history` returns 500 | Identify and fix the exception being thrown. Add error logging to pinpoint the root cause. |
| **P0** | `/api/products/{id}/deal-intelligence` returns 500 | Same as above. |
| **P1** | Live comparison engine returns "unavailable" for all retailers | Either configure real API credentials (Nykaa partner API, Amazon PAAPI) or implement a manual price verification workflow that populates real prices before launch. |
| **P1** | All product images are generic stock photos | Source and license real product images from manufacturer media kits or use official retailer CDN images with appropriate attribution. |
| **P1** | Product prices are entirely demo data | Conduct a manual verification campaign: visit each retailer, record real prices, and seed the database with verified data marked `source_type: "manual_verified"`. |
| **P2** | 11 non-beauty products in database | Delete or archive IDs 1–11 from the Neon staging database. |
| **P2** | `/api/products` takes 8.5 seconds | Profile the query. Add database indices, implement pagination, or add server-side caching. |
| **P2** | No automated price update mechanism | Implement a background worker (Render background worker or Render cron job) that periodically triggers price collection for each product via the existing `/api/prices/collect/{id}` endpoint, once real retailer access is established. |
| **P2** | Reviews are all demo | Either remove review section until real reviews can be integrated, or clearly label the review section "Sample Reviews" to avoid misleading users. |
| **P3** | Frontend silent fallback with no warning | Show a visible banner when backend is unreachable and static data is being used. |
| **P3** | Coupon codes simulated | Remove coupon display from UI or add prominent "Simulated — verify at checkout" label. |

---

## FINAL VERDICT

> ### **Verdict: B — Working product comparison website with mostly demo prices**
>
> *With strong caveats that make it closer to D (Not ready for customer use) in practice.*

**What works:**
- ✅ The frontend is deployed and accessible on Vercel.
- ✅ The backend is deployed on Render and connected to a real PostgreSQL database (Neon).
- ✅ 102 beauty products have correct brand identities and product names corresponding to real Indian beauty products.
- ✅ The technical architecture (FastAPI, PostgreSQL, React, Vite) is sound and deployable.
- ✅ Feature endpoints (auth, wishlist, routines, ingredient analysis) are defined and reachable.

**What does NOT work for a customer-facing deployment:**

- ❌ **Every single Buy Now link is synthetic and broken** — clicking "Buy Now" on Nykaa leads to a 403/404 non-existent product page.
- ❌ **All 448+ retailer price offers are demo data** — no price in the system is sourced from a real retailer.
- ❌ **The live comparison engine is non-functional** — all 5 retailers return "unavailable."
- ❌ **Price history and deal intelligence are broken** (HTTP 500).
- ❌ **All product images are generic stock photos** — users cannot visually identify any product.
- ❌ **No automated price updates exist** — prices will never change without manual intervention.
- ❌ **Coupon codes are simulated** — applying them at checkout would fail.

**The application is a well-structured technical demonstration** of a beauty price comparison platform, but it is **not ready for customer use**. The core value proposition — showing real, current prices from multiple retailers so customers can find the cheapest option — cannot be delivered with any of the data currently in the system.

---

*Audit completed: 2026-11-09 21:29 UTC*  
*Report saved to: `PHASE_13_8_LIVE_WEBSITE_REAL_DATA_AUDIT_REPORT.md`*  
*Next step: Await user review and approval before proceeding to any corrective phase.*
