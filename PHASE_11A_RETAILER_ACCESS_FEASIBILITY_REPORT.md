# PriceWise AI — Phase 11A: No-API Retailer Price Access & Feasibility Audit Report

**Project:** PriceWise AI Beauty Intelligence & Price Comparison  
**Phase:** Phase 11A (No-API Retailer Price Access & Feasibility Audit)  
**Execution Date:** November 9, 2026  
**Auditor:** Antigravity Autonomous Agent  
**Environment:** Windows 11, Python 3.14, Playwright Chromium, SQLite 3  
**Status:** COMPLETED & AUDITED  

---

## 1. Executive Summary & Objective

The objective of **Phase 11A** is to determine with strict, empirical evidence how PriceWise AI can obtain genuine skincare and makeup product prices across Indian retailers **without depending on paid retailer APIs or purchasing five separate commercial API subscriptions**.

### Verified Starting Context & Constraints:
1. **Zero Retailer API Keys Available:** The project administrator does not possess API credentials for Nykaa, Myntra, Purplle, Tira, or Amazon India.
2. **Zero Paid Subscriptions Approved:** The project must operate without recurring fees for third-party commercial scraping proxies or retailer enterprise licenses.
3. **Database Integrity Preserved:** All 34 catalog products, 97 retailer offers (96 DEMO, 1 UNAVAILABLE, 0 LIVE_VERIFIED), and 947 historical price records remain intact. `PRAGMA integrity_check` passed: `ok`.
4. **Compliance & Sanctioned Boundary:** No security controls, Web Application Firewalls (WAFs), Akamai Bot Managers, Cloudflare Turnstiles, or CAPTCHA challenges were bypassed during this investigation. Where restrictions were observed, they were recorded and automated requests stopped immediately.

---

## 2. Retailer Feasibility Matrix

The following matrix synthesizes the empirical findings from direct network, protocol, and DOM audits conducted on November 9, 2026:

| Retailer | Public Page Access | Price in HTML | Structured Data (JSON-LD / OG) | Variant Extraction | Automated Access Permission | Final Classification | Primary Access Barrier | Compliant Verification Path |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Nykaa** (`nykaa.com`) | ❌ **Blocked** (HTTP 403 Forbidden) | ❌ Blocked by WAF | ❌ Blocked by WAF | ❌ Blocked by WAF | ❌ Prohibited by ToS; blocked by Akamai | **`RESTRICTED`** | Akamai Edge WAF (`Access Denied` / HTTP/2 Reset) | **Manual Verification** (Screenshot + URL Snapshot) |
| **Myntra** (`myntra.com`) | ⚠️ **Partial** (HTTP 200 in HTTP GET; Playwright blocked) | ✅ Yes (in static server HTML) | ✅ Yes (Schema.org `Product` JSON-LD & OG tags) | ⚠️ Partial (base SKU only; dynamic JS for stock) | ❌ Prohibited by ToS; `robots.txt` disallows widgets | **`PUBLIC_DATA_ONLY`** | Terms of Use prohibit scraping; Akamai blocks headless browsers | **Manual Verification**; optional free Affiliate Feed in future |
| **Purplle** (`purplle.com`) | ✅ **Yes** (HTTP 200 in Playwright) | ⚠️ Client-side rendered (SPA hydration) | ⚠️ OpenGraph only; JSON-LD absent in static HTML | ⚠️ Requires full SPA execution | ❌ Prohibited by ToS; `/product/productfeed/` Disallowed | **`PUBLIC_DATA_ONLY`** | Terms of Use forbid data gathering; dynamic client-side hydration | **Manual Verification**; optional partner feed |
| **Tira Beauty** (`tirabeauty.com`) | ❌ **Blocked** (HTTP 403 Forbidden) | ❌ Blocked by WAF | ❌ Blocked by WAF | ❌ Blocked by WAF | ❌ Prohibited by ToS; blocked by Akamai | **`RESTRICTED`** | Akamai Edge WAF (`Access Denied` / Perimeter block) | **Manual Verification** (Screenshot + URL Snapshot) |
| **Amazon India** (`amazon.in`) | ❌ **Blocked** (CAPTCHA / 404 API Notice) | ❌ Blocked by Robot Check | ❌ Blocked by Robot Check | ❌ Blocked by Robot Check | ❌ Prohibited by Conditions of Use | **`RESTRICTED`** | Automated access detection / Robot Check CAPTCHA / PA-API gate | **Manual Verification**; optional free Amazon Associates PA-API |

---

## 3. Individual Retailer Investigation Findings

### 3.1 Retailer 1: Nykaa (`nykaa.com`)

#### A. Public Website Access & Network Protocol
- **Robots.txt Probe:** `https://www.nykaa.com/robots.txt` returned **HTTP 403 Forbidden** (381 bytes).
- **Product Page Probe:** Tested with URL `https://www.nykaa.com/dot-key-watermelon-cooling-sunscreen-spf-50-pa/p/7382216`.
  - HTTP Status: **403 Forbidden**.
  - Server Payload: `<HTML><HEAD> <TITLE>Access Denied</TITLE> </HEAD><BODY> <H1>Access Denied</H1> You don't have permission to access "http://www.nykaa.com/..." on this server. Reference #18.xxxx</BODY></HTML>`.
  - Playwright Headless Probe: Execution resulted in `net::ERR_HTTP2_PROTOCOL_ERROR` (immediate TCP stream termination by Akamai edge).
- **Conclusion:** While public consumers using standard desktop browsers can browse Nykaa freely, automated HTTP requests and headless browser automation are completely blocked at the perimeter edge.

#### B. Automated Extraction Permission & Terms of Service
- **robots.txt:** Blocked from automated programmatic reading.
- **Published Terms & Conditions (Section 4 — User Conduct):**
  > *"You shall not use any 'deep-link', 'page-scrape', 'robot', 'spider' or other automatic device, program, algorithm or methodology, or any similar or equivalent manual process, to access, acquire, copy or monitor any portion of the Website or any Content, or in any way reproduce or circumvent the navigational structure or presentation of the Website or any Content..."*
- **Anti-Bot Infrastructure:** Akamai Bot Manager with behavioral fingerprinting and HTTP/2 stream inspection.

#### C. Price Data Quality & Technical Feasibility
- In a human consumer session, Nykaa renders selling price, MRP, discount percentage, pack size (50g, 100g), pincode delivery fees (free above ₹299), and coupon codes.
- In automated contexts, **0 fields are obtainable without attempting to bypass perimeter security controls**.
- Under PriceWise AI behavioral guidelines, bypass techniques (rotating proxies, header spoofing) are strictly prohibited.
- **Final Classification:** **`RESTRICTED`** (Automated collection blocked; **`MANUAL_ONLY`** for operational price tracking).

---

### 3.2 Retailer 2: Myntra (`myntra.com`)

#### A. Public Website Access & Network Protocol
- **Robots.txt Probe:** `https://www.myntra.com/robots.txt` returned **HTTP 200 OK** (24,173 bytes, 729 granular `Disallow` rules for user-agent `*`).
- **Product Page Probe:** Tested with URL `https://www.myntra.com/sunscreen/dot--key/dot--key-watermelon-cooling-sunscreen-spf-50-pa/23577782/buy`.
  - Standard HTTP GET with desktop User-Agent returned **HTTP 200 OK** (437,767 bytes).
  - Headless Playwright Probe: Resulted in `net::ERR_HTTP2_PROTOCOL_ERROR` (Akamai blocks headless browser TLS fingerprints).
- **Embedded Structured Data:**
  - Standard HTTP GET contains Schema.org `Product` JSON-LD:
    - `"name"`: Product title
    - `"offers"`: `{"@type": "Offer", "price": 465, "priceCurrency": "INR", "availability": "https://schema.org/InStock"}`
    - OpenGraph tags: `og:title`, `og:image`, `og:price:amount`, `og:price:currency`.

#### B. Automated Extraction Permission & Terms of Service
- **robots.txt:** Allows generic root `/`, but explicitly disallows critical pricing and stock sub-endpoints:
  - `Disallow: */filters*`
  - `Disallow: *ajaxPDPCouponWidget*` (disallows coupon automation)
  - `Disallow: *ajaxPincodeWidget.php*` (disallows delivery fee calculation)
  - `Disallow: *captcha*`
- **Published Terms of Use (Section 3 — Platform Use):**
  > *"You agree not to use any robot, spider, scraper or other automated means to access the Platform for any purpose without our express written permission."*

#### C. Price Data Quality & Technical Feasibility
- While base selling price and MRP are present in static JSON-LD for simple items, real-time coupons and pin-code-specific shipping fees require dynamic AJAX calls that are explicitly disallowed by `robots.txt`.
- Headless browser automation is blocked at the protocol level.
- **Final Classification:** **`PUBLIC_DATA_ONLY`** (Public structured data exists in static HTML, but automated commercial extraction is unauthorized by Terms of Use; **`MANUAL_ONLY`** is the compliant operating path).

---

### 3.3 Retailer 3: Purplle (`purplle.com`)

#### A. Public Website Access & Network Protocol
- **Robots.txt Probe:** `https://www.purplle.com/robots.txt` returned **HTTP 200 OK** (1,106 bytes, 50 `Disallow` rules).
- **Product Page Probe:** Tested via Playwright Chromium.
  - HTTP Status: **200 OK**.
  - Title: `Purplle.com: Buy Cosmetic Products & Beauty Products Online in India`.
  - Architecture: Client-side rendered Single Page Application (SPA) powered by OpenResty / Nginx.
  - Static HTML contains minimal product content; DOM is hydrated dynamically via JavaScript calling Purplle backend microservices (`media6.ppl-media.com`).

#### B. Automated Extraction Permission & Terms of Service
- **robots.txt:** Explicitly disallows automated feeds:
  - `Disallow: /admin/`
  - `Disallow: /order/`
  - `Disallow: /cart*`
  - `Disallow: /checkout/`
  - `Disallow: /product/productfeed/` ⚠️ (Explicitly disallows product feeds!)
  - `Disallow: /listing/`
- **Published Terms & Conditions:**
  > *"This license does not include any resale or commercial use of this site or its contents; any collection and use of any product listings, descriptions, or prices; any derivative use of this site or its contents; or any use of data mining, robots, or similar data gathering and extraction tools."*

#### C. Price Data Quality & Technical Feasibility
- Browser automation can technically load the SPA shell, but static HTTP scraping yields empty containers because JSON-LD is not pre-rendered in initial HTML.
- Commercial data gathering is expressly forbidden under Purplle's Terms of Use.
- **Final Classification:** **`PUBLIC_DATA_ONLY`** (Technically loads in browser, but Terms of Use forbid automated price harvesting and `productfeed` is disallowed in `robots.txt`; **`MANUAL_ONLY`** is required).

---

### 3.4 Retailer 4: Tira Beauty (`tirabeauty.com`)

#### A. Public Website Access & Network Protocol
- **Robots.txt Probe:** `https://www.tirabeauty.com/robots.txt` returned **HTTP 200 OK** (2,034 bytes, 39 `Disallow` rules).
- **Product Page Probe:** Tested with URL `https://www.tirabeauty.com/product/dot-key-watermelon-cooling-sunscreen-spf-50-pa-50g-1087095`.
  - Standard HTTP GET: **HTTP 403 Forbidden** (`Access Denied`).
  - Playwright Headless Probe: **HTTP 403 Forbidden** (`Access Denied`, length 472 bytes).
  - WAF Signature: Reliance Retail Akamai Edge perimeter block.

#### B. Automated Extraction Permission & Terms of Service
- **robots.txt:** Disallows search and category listing paths:
  - `Disallow: /products/?l3*`
  - `Disallow: /products/?l2*`
  - `Disallow: /products/?l1*`
  - `Disallow: /*?q*`
  - `Disallow: /auth/login/`
  - `Disallow: /cart/`
- **Published Terms of Use (Reliance Retail Limited):**
  > *"You shall not use any automated device, program, tool, algorithm, methodology, or any similar manual process to access, acquire, copy, or monitor any portion of the Website or Content..."*

#### C. Price Data Quality & Technical Feasibility
- Automated retrieval fails immediately with HTTP 403.
- Zero price or variant fields can be extracted programmatically without attempting access control bypass.
- **Final Classification:** **`RESTRICTED`** (Automated requests blocked at edge; **`MANUAL_ONLY`** for verified price tracking).

---

### 3.5 Retailer 5: Amazon India (`amazon.in`)

#### A. Public Website Access & Network Protocol
- **Robots.txt Probe:** `https://www.amazon.in/robots.txt` returned **HTTP 200 OK** (9,320 bytes, 82 `Disallow` rules).
- **Product Page Probe:** Tested with ASIN `B0B5D982K5` (`https://www.amazon.in/dp/B0B5D982K5`).
  - Standard HTTP GET: Serves HTTP 404 or lightweight challenge page (length ~2,186 bytes) with explicit automated access comments:
    ```html
    <!--
    To discuss automated access to Amazon data please contact api-services-support@amazon.com.
    For information about migrating to our APIs refer to our Marketplace APIs at https://developer.amazonservices.com/ref=rm_5_sv, 
    or our Product Advertising API at https://affiliate-program.amazon.com/gp/advertising/api/detail/main.html/ref=rm_5_ac for advertising use cases.
    -->
    ```
  - Playwright Headless Probe: Triggers Amazon's Robot Check / CAPTCHA challenge page.

#### B. Automated Extraction Permission & Terms of Service
- **Amazon Conditions of Use (Section 4 — License and Access):**
  > *"You may not frame or utilize framing techniques to enclose any trademark, logo, or other proprietary information of Amazon... You may not use any meta tags or any other 'hidden text' utilizing Amazon's names or trademarks without the express written consent of Amazon... You may not use data mining, robots, or similar data gathering and extraction tools without express written consent."*
- Amazon explicitly gates automated product and price data behind the **Amazon Associates Product Advertising API (PA-API)**.

#### C. Price Data Quality & Technical Feasibility
- Automated scraping is blocked by anti-bot CAPTCHA challenges.
- Amazon's official stance mandates using PA-API. (Note: Amazon Associates PA-API provides structured JSON with real-time selling price, MRP, and availability free of charge for approved affiliate associates, requiring zero paid subscriptions).
- **Final Classification:** **`RESTRICTED`** / **`PARTNER_ACCESS_REQUIRED`** (Direct scraping is restricted and blocked; manual price verification or free Amazon Associates PA-API is required).

---

## 4. Synthesis of Technical Feasibility Findings

```mermaid
flowchart TD
    A["5 Target Indian Retailers"] --> B{"WAF & Perimeter Status"}
    B -->|"Akamai / Edge Block (HTTP 403)"| C["Nykaa & Tira"]
    B -->|"Robot Check / CAPTCHA"| D["Amazon India"]
    B -->|"HTML Accessible / Playwright Blocked"| E["Myntra & Purplle"]
    
    C --> F["Result: RESTRICTED"]
    D --> G["Result: RESTRICTED / PA-API REQUIRED"]
    E --> H["Terms of Use Prohibit Scraping"]
    H --> I["Result: PUBLIC_DATA_ONLY"]
    
    F --> J["Compliant Solution: Manual Evidence Verification Workflow"]
    G --> J
    I --> J
    
    J --> K["Evidence Storage in SQLite"]
    K --> L["Status: MANUAL_VERIFIED"]
```

### Key Insights:
1. **The "Scraping Without APIs" Myth for Major Indian E-Commerce:**
   - In 2026, major Indian e-commerce portals (Nykaa, Reliance Tira, Amazon, Myntra) utilize enterprise edge firewalls (Akamai, Cloudflare, Amazon WAF) that actively identify and terminate automated scripts.
   - Any attempt to bypass these blocks using proxy networks, fingerprint spoofing, or CAPTCHA solvers violates Antigravity Behavioral Guidelines, retailer terms of service, and website security perimeters.
2. **Why Paid Scraping Subscriptions Are Unnecessary & Fragile:**
   - Even if third-party commercial scrapers were purchased, their scrapers break constantly upon minor DOM/class obfuscation changes (e.g. Nykaa's randomized `css-1d0jf8e` class names) and present serious compliance liabilities.
3. **The Sustainable Path Forward:**
   - The user's directive is strictly upheld: **No paid APIs, no fake live prices, no security bypasses.**
   - PriceWise AI must deploy a robust **No-API Verified Intelligence Architecture** relying on:
     1. High-confidence **Manual Price Verification Workflow** with user-submitted proof and cryptographic URL/time hashes.
     2. Structured **Schema.org Microdata Parsers** for authorized / local / staging environments.
     3. Free **Affiliate Network Aggregator Feeds** (CueLinks, EarnKaro, Amazon Associates PA-API) as zero-cost future opportunities that require zero API subscription fees.

---

## 5. Next Steps

- Proceed to review [`PHASE_11A_NO_API_ARCHITECTURE_PLAN.md`](file:///c:/Users/humai/price-comparison-website/PHASE_11A_NO_API_ARCHITECTURE_PLAN.md).
- Phase 11A is strictly an audit and planning phase. **Phase 11B has NOT been started.**

