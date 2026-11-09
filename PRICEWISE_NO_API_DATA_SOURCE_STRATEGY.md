# PriceWise AI — No-API Data Source Strategy

**Date:** November 9, 2026  
**Repository Root:** `C:\Users\humai\price-comparison-website`  
**Classification:** Strategic Planning Document — No Code Changes

---

## 1. Executive Summary

**Decision:** PriceWise AI will operate as an **API-independent beauty product discovery and price comparison platform**. No official retailer API credentials (Nykaa, Purplle, Tira Beauty, Myntra, Amazon India) are available or expected.

**Implications:**
- No blocking on partner credential acquisition
- No fabricated prices or synthetic data
- Strict compliance with retailer terms, Cloudflare, CAPTCHA, robots.txt
- All live data clearly labelled by verification status
- Manual verification workflow as first-class feature

---

## 2. Retailer Access Method Analysis

### 2.1 Nykaa (`nykaa.com`)

| Access Path | Status | Feasibility |
|-------------|--------|-------------|
| Official Partner API | ❌ Requires approval + credentials | Not available |
| Affiliate Feed (JSON/CSV) | ❌ Requires partner agreement | Not available |
| Public Product Pages | ⚠️ Cloudflare blocks headless | **RESTRICTED** |
| Search Route (`/search/result/?q=`) | ⚠️ Cloudflare Turnstile | **RESTRICTED** |
| JSON-LD Schema (`schema.org/Product`) | ✅ Embedded in pages | Available if page accessible |
| Manual URL Submission | ✅ User-provided links | **MANUAL_VERIFIED** |

**Current Terms Check:** Nykaa ToS prohibits automated scraping without authorization. Cloudflare actively blocks headless Chrome.

**Verdict:** No live automated extraction without official API. Manual URL verification is the only compliant path.

---

### 2.2 Purplle (`purplle.com`)

| Access Path | Status | Feasibility |
|-------------|--------|-------------|
| Official API / Feed | ❌ Not publicly documented | Unknown |
| Affiliate Program | ❌ Requires application | Not available |
| Public Product Pages | ⚠️ Likely Cloudflare/Akamai | Likely RESTRICTED |
| Search/Category Pages | ⚠️ Dynamic rendering | Likely RESTRICTED |
| Structured Data | ✅ JSON-LD often present | If page accessible |
| Manual URL | ✅ Compliant | **MANUAL_VERIFIED** |

**Current Terms Check:** Purplle ToS restricts automated access. No public API documentation.

**Verdict:** Same pattern as Nykaa. Manual verification only.

---

### 2.3 Tira Beauty (`tirabeauty.com`)

| Access Path | Status | Feasibility |
|-------------|--------|-------------|
| Official Partner API | ❌ Requires Reliance Retail partnership | Not available |
| Affiliate Feed | ❌ Internal only | Not available |
| Public Product Pages | ⚠️ Likely protected | Likely RESTRICTED |
| Search | ⚠️ Dynamic | Likely RESTRICTED |
| Manual URL | ✅ Compliant | **MANUAL_VERIFIED** |

**Verdict:** Same pattern. No public API.

---

### 2.4 Myntra (`myntra.com`)

| Access Path | Status | Feasibility |
|-------------|--------|-------------|
| Official API | ❌ Flipkart Group, internal only | Not available |
| Affiliate (Flipkart Affiliate) | ❌ Separate program, limited | Not available |
| Public Product Pages | ⚠️ Heavy bot protection | **RESTRICTED** |
| Search | ⚠️ App-first, web limited | **RESTRICTED** |
| Myntra Studio/Feed | ❌ Internal | Not available |
| Manual URL | ✅ Compliant | **MANUAL_VERIFIED** |

**Verdict:** Heavy anti-bot. Manual only.

---

### 2.5 Amazon India (`amazon.in`)

| Access Path | Status | Feasibility |
|-------------|--------|-------------|
| Product Advertising API (PA-API 5.0) | ⚠️ Requires Associate approval + 3 sales | **Possible but gated** |
| Affiliate Links | ✅ Available via Associates | **LIVE_VERIFIED** (prices) |
| Public Product Pages | ⚠️ CAPTCHA on automated | **RESTRICTED** |
| Structured Data | ✅ Rich JSON-LD | Available if accessible |
| Manual URL | ✅ Compliant | **MANUAL_VERIFIED** |

**Verdict:** PA-API is the only viable live path, but requires 3 qualifying sales + approval. Affiliate links give price access but require Associates membership.

---

## 3. What Works WITHOUT Credentials

### 3.1 Manual URL Verification (First-Class Feature)

```
User submits URL → Validation → Extraction → Verification → Display
```

**Supported Retailers:** All 5 (via user-submitted URLs)

**Implementation:**
- User pastes product URL
- Backend validates URL against retailer allowlist
- Playwright navigates (if not restricted) OR manual verification workflow
- Extraction from JSON-LD + DOM fallback
- Result labelled `MANUAL_VERIFIED` with timestamp and source URL

**Compliance:** User-initiated, single request, no automation loop.

---

### 3.2 Cached & Historical Data

**Sources:**
- Previous live extractions (stored in `price_history` / `price_check_logs`)
- Demo seed data (academic prototype)
- Price tracking observations from previous runs

**Label:** `HISTORICAL` or `CACHED` (with freshness timestamp)

**Rule:** Never presented as live. Always show `last_verified` timestamp.

---

### 3.3 Demo / Academic Data

**Source:** `beauty_seed_data.py` — 27 curated beauty products with multi-retailer offers

**Label:** `DEMO`

**Rule:** Clearly marked "Academic Prototype" throughout UI.

---

### 3.4 User-Submitted Price Corrections

**Workflow:**
1. User sees price discrepancy
2. Clicks "Report Price"
3. Submits retailer, URL, observed price, timestamp
4. Stored as `MANUAL_VERIFIED` with user attribution
5. Displayed alongside other sources with clear attribution

---

## 4. What REQUIRES Authorization

| Feature | Required Authorization | Retailer |
|---------|------------------------|----------|
| Automated live price polling | Official API key / Partner secret | All |
| Bulk catalog sync | Partner feed / API | All |
| Affiliate commission tracking | Affiliate program membership | Amazon, Flipkart/Myntra |
| Real-time stock updates | Partner API | Nykaa, Purplle, Tira, Myntra |
| Bulk review aggregation | Partner API / Data license | All |
| Official product feeds | Partner agreement | All |

**Status:** None currently obtained.

---

## 5. Manual Verification Workflow (Core Feature)

### 5.1 User Flow

```
1. User on Product Detail Page
   │
   ├─→ "Verify Price" button
   │    │
   │    ├─→ Paste retailer product URL
   │    │    │
   │    │    ├─→ URL validated (allowlist + HTTPS)
   │    │    │
   │    │    ├─→ If RESTRICTED: "Cannot auto-verify. Manual entry?"
   │    │    │    │
   │    │    │    └─→ User enters: Retailer, Price, MRP, URL, Timestamp
   │    │    │         │
   │    │    │         └─→ Stored as MANUAL_VERIFIED
   │    │    │
   │    │    └─→ If accessible: Auto-extract JSON-LD + DOM
   │    │         │
   │    │         └─→ Stored as MANUAL_VERIFIED (user-initiated)
   │    │
   │    └─→ "Report Incorrect Price" (for existing data)
   │         │
   │         └─→ Form: Retailer, Correct Price, Evidence URL
   │              │
   │              └─→ Stored as MANUAL_VERIFIED (user report)
   │
   └─→ Comparison table shows: LIVE_VERIFIED | CACHED | HISTORICAL | MANUAL_VERIFIED | RESTRICTED | DEMO
```

### 5.2 Data Model for Manual Verification

```python
class ManualVerification:
    user_id: int
    product_id: int
    retailer: str
    product_url: str
    listed_price: float
    mrp: Optional[float]
    observed_at: datetime
    source_type: "MANUAL_VERIFIED"
    verification_notes: str
    submitted_by: int
```

---

## 5. Licensed Data Provider Options

| Provider | Coverage | Cost Estimate | Access Type |
|----------|----------|---------------|-------------|
| **NielsenIQ / Retail Measurement** | PAN-India retail scan | ₹50L–₹2Cr/year | Licensed feed |
| **Euromonitor / Mintel** | Market data, not SKU-level | ₹30L–₹1Cr/year | Licensed reports |
| **DataWeave / Intelligence Node** | Indian e-commerce | ₹20L–₹80L/year | API + feed |
| **Insite / PriceOye** | Indian price comparison | Revenue share | Affiliate + feed |
| **Custom scraper service** | Targeted retailers | ₹10L–₹50L setup + maintenance | Managed service |

**Recommendation:** None viable for academic prototype budget. Prioritize manual + affiliate.

---

## 6. Cost Implications

| Approach | Setup Cost | Ongoing Cost | Scalability |
|----------|------------|--------------|-------------|
| Manual URL + Affiliate | ₹0 | ₹0 (dev time only) | Low (manual) |
| Affiliate Programs | ₹0 | Revenue share | Medium |
| Licensed Data Feed | ₹20L–₹2Cr/yr | ₹20L–₹2Cr/yr | High |
| Managed Scraper Service | ₹10L–₹50L setup | ₹5L–₹20L/yr | Medium-High |
| Official Partner APIs | Application effort | Usually free (quota) | High |

**Recommended for Prototype:** Manual URL + Affiliate (Amazon Associates) = ₹0 cost.

---

## 7. Technical Architecture

### 7.1 Adapter Status Independence

Each retailer adapter maintains independent status:

```python
CapabilityStatus:
    SUPPORTED          # Technical capability exists
    RESTRICTED         # Access blocked (Cloudflare, CAPTCHA)
    UNSUPPORTED        # No extraction method
    TEMPORARILY_UNAVAILABLE  # Transient failure
```

**Key:** Failure of Nykaa ≠ failure of Amazon or Manual.

---

### 7.2 Verification Status Hierarchy (Display Order)

```
1. LIVE_VERIFIED       ← Fresh extraction (< 10 min)
2. MANUAL_VERIFIED     ← User-initiated, URL provided
3. CACHED              ← < 10 min old, from memory cache
4. HISTORICAL          ← From DB price_history
5. POSSIBLE_MATCH      ← Variant match < 95% confidence
6. RESTRICTED          ← Cloudflare/CAPTCHA blocked
7. UNAVAILABLE         ← No price found
8. DEMO                ← Academic seed data
```

**UI Rule:** Never show DEMO/HISTORICAL/RESTRICTED as "Live Price".

---

### 7.3 Database Schema (No Changes Required)

Existing tables support all statuses:

| Table | Purpose |
|-------|---------|
| `price_check_logs` | Audit trail of every extraction attempt |
| `price_history` | Timestamped observations |
| `offers` | Current best price per store |
| `price_tracking` | User target prices |
| `price_alerts` | Notification history |

**Addition:** `manual_verifications` table (new) for user submissions.

---

## 8. Recommended Next Phase: Phase 8D — Manual Verification & Affiliate Foundation

### 8D.1 Core Deliverables

1. **Manual URL Verification Endpoint**
   - `POST /api/compare/manual` — Accept URL, return extraction
   - Rate limited (5/min per user)
   - Returns `MANUAL_VERIFIED` result

2. **Price Reporting Form**
   - "Report Price" button on product detail
   - Stores user correction as `MANUAL_VERIFIED`

2. **Amazon Associates Integration**
   - Affiliate link generation for `amazon.in`
   - Price extraction via PA-API (if approved) or affiliate redirect

3. **Frontend Status Badges**
   - Clear visual distinction for all 8 statuses
   - Timestamp display for cached/historical/manual

4. **Documentation**
   - User guide: "How to verify prices"
   - Contributor guide: "Adding manual prices"

### 8D.2 Non-Goals (Deferred)

- Purplle/Tira/Myntra automated extraction
- Nykaa live browser extraction
- Licensed data feeds
- Real-time stock sync

---

## 9. Summary Matrix

| Retailer | Live API | Browser Access | Manual URL | Affiliate | Status |
|----------|----------|----------------|------------|-----------|--------|
| Nykaa | ❌ | RESTRICTED | ✅ | ❌ | MANUAL_VERIFIED only |
| Purplle | ❌ | Likely RESTRICTED | ✅ | ❌ | MANUAL_VERIFIED only |
| Tira | ❌ | Likely RESTRICTED | ✅ | ❌ | MANUAL_VERIFIED only |
| Myntra | ❌ | RESTRICTED | ✅ | Flipkart Affiliate | MANUAL_VERIFIED + Affiliate |
| Amazon India | PA-API (gated) | RESTRICTED | ✅ | Associates | LIVE_VERIFIED (if PA-API) / MANUAL_VERIFIED |

---

## 10. Next Action

**Proceed to Phase 8D — Manual Verification & Affiliate Foundation**

Scope:
- Implement `POST /api/compare/manual` endpoint
- Add "Verify Price" button to Product Detail Page
- Add "Report Price" correction flow
- Amazon Associates integration (apply for PA-API)
- Status badges for all 8 verification states
- User guide for manual verification

**Do NOT begin:**
- Purplle/Tira/Myntra scrapers
- Licensed data procurement
- Nykaa browser automation workarounds

---

*Strategy document complete. Awaiting approval for Phase 8D implementation.*