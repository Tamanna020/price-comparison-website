# PriceWise AI — Phase 8G.1 Price Status Audit & Evidence Verification

**Audit Date:** November 9, 2026  
**Scope:** Complete inspection of all 97 database offers in `data/pricewise.db`  
**Methodology:** Strict evidence-based verification. No heuristic assumptions based on URL strings.

---

## 1. Executive Summary & Status Transition

In the initial Phase 8G report, 43 offers were erroneously classified as `LIVE_VERIFIED` because an audit script checked whether the retailer URL string contained `'amazon'`, `'nykaa'`, or `'tira'`. In reality, the PriceWise AI project currently possesses **no official retailer API credentials**, and automated scraping against major Indian beauty platforms encountered access restrictions (Cloudflare bot detection, HTTP/2 protocol blocks, and rate limits).

The database table `evidence_references` contains **0 rows**. Furthermore, all 10 stores in the database are explicitly designated as `(Demo)` (e.g. `Nykaa (Demo)`, `Amazon India (Demo)`, `Tira (Demo)`).

Under strict evidence verification, all 43 unsupported `LIVE_VERIFIED` claims have been downgraded to **`DEMO`**.

### Before vs. After Offer Status Counts

| Status Classification | Phase 8G (Previous) | Phase 8G.1 (Audited) | Change | Status Definition & Evidence Rule |
| :--- | :---: | :---: | :---: | :--- |
| **LIVE_VERIFIED** | 43 | **0** | -43 | Strictly requires verifiable evidence in `evidence_references` or authenticated API ingestion. None exists. |
| **DEMO** | 53 | **96** | +43 | Seeded catalog comparison data across demo stores for algorithm & UI demonstration. |
| **UNAVAILABLE** | 1 | **1** | 0 | Offer explicitly marked Out of Stock / Discontinued (Offer ID 41). |
| **MANUAL_VERIFIED** | 0 | **0** | 0 | Reserved for admin-verified user submitted price corrections. |
| **CACHED** | 0 | **0** | 0 | Expired live scraping observations. |
| **HISTORICAL** | 0 | **0** | 0 | Deprecated price points stored in `price_history`. |
| **POSSIBLE_MATCH** | 0 | **0** | 0 | Ambiguous SKU matches requiring human review. |
| **RESTRICTED** | 0 | **0** | 0 | Active bot-blocked requests (logged in `price_check_logs`, not offers table). |
| **TOTAL** | **97** | **97** | **0** | **100% of offers audited without database modification** |

---

## 2. Complete Inventory Audit: All 97 Database Offers

| ID | Product Name | Retailer Store | Price (₹) | Phase 8G Claim | Final Status | Evidence Source | Verification Timestamp | Reason for Status Change |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| 1 | Apple MacBook Pro 14" (M3 Pro, 1... | TechMart (Demo) | ₹1,799 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 2 | Apple MacBook Pro 14" (M3 Pro, 1... | ElectroHub (Demo) | ₹1,849 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 3 | Apple MacBook Pro 14" (M3 Pro, 1... | Apex Direct (Demo) | ₹1,899 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 4 | Apple MacBook Pro 14" (M3 Pro, 1... | DigitalBay (Demo) | ₹1,949 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 5 | Dell XPS 15 OLED (Intel Core i7-... | Apex Direct (Demo) | ₹1,900 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 6 | Dell XPS 15 OLED (Intel Core i7-... | TechMart (Demo) | ₹1,949 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 7 | Dell XPS 15 OLED (Intel Core i7-... | PrimeGear (Demo) | ₹2,049 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 8 | Samsung Galaxy S24 Ultra 5G (256... | ElectroHub (Demo) | ₹1,050 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 9 | Samsung Galaxy S24 Ultra 5G (256... | TechMart (Demo) | ₹1,150 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 10 | Samsung Galaxy S24 Ultra 5G (256... | Apex Direct (Demo) | ₹1,199 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 11 | Samsung Galaxy S24 Ultra 5G (256... | DigitalBay (Demo) | ₹1,279 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 12 | Apple iPhone 15 Pro (128GB, Natu... | TechMart (Demo) | ₹929 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 13 | Apple iPhone 15 Pro (128GB, Natu... | Apex Direct (Demo) | ₹949 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 14 | Apple iPhone 15 Pro (128GB, Natu... | PrimeGear (Demo) | ₹989 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 15 | Sony WH-1000XM5 Wireless Noise-C... | ElectroHub (Demo) | ₹328 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 16 | Sony WH-1000XM5 Wireless Noise-C... | TechMart (Demo) | ₹348 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 17 | Sony WH-1000XM5 Wireless Noise-C... | DigitalBay (Demo) | ₹389 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 18 | Sony WH-1000XM5 Wireless Noise-C... | PrimeGear (Demo) | ₹359 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 19 | Bose QuietComfort Ultra Wireless... | Apex Direct (Demo) | ₹379 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 20 | Bose QuietComfort Ultra Wireless... | TechMart (Demo) | ₹399 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 21 | Bose QuietComfort Ultra Wireless... | ElectroHub (Demo) | ₹429 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 22 | PlayStation 5 Slim Console (Disc... | TechMart (Demo) | ₹450 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 23 | PlayStation 5 Slim Console (Disc... | Apex Direct (Demo) | ₹469 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 24 | PlayStation 5 Slim Console (Disc... | PrimeGear (Demo) | ₹500 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 25 | PlayStation 5 Slim Console (Disc... | DigitalBay (Demo) | ₹519 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 26 | Apple Watch Series 9 GPS 45mm (M... | ElectroHub (Demo) | ₹329 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 27 | Apple Watch Series 9 GPS 45mm (M... | TechMart (Demo) | ₹349 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 28 | Apple Watch Series 9 GPS 45mm (M... | Apex Direct (Demo) | ₹379 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 29 | Dell UltraSharp 27 4K USB-C Hub ... | Apex Direct (Demo) | ₹539 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 30 | Dell UltraSharp 27 4K USB-C Hub ... | TechMart (Demo) | ₹579 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 31 | Dell UltraSharp 27 4K USB-C Hub ... | PrimeGear (Demo) | ₹630 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 32 | Sony Alpha 7 IV Full-Frame Mirro... | DigitalBay (Demo) | ₹2,199 | UNAVAILABLE | **UNAVAILABLE** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Catalog item marked Out of Stock |
| 33 | Sony Alpha 7 IV Full-Frame Mirro... | TechMart (Demo) | ₹2,298 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 34 | Sony Alpha 7 IV Full-Frame Mirro... | Apex Direct (Demo) | ₹2,398 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 35 | LG C3 Series 65-Inch Class OLED ... | ElectroHub (Demo) | ₹1,597 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 36 | Dot & Key Watermelon Cooling Sun... | Nykaa (Demo) | ₹465 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 37 | Dot & Key Watermelon Cooling Sun... | Tira (Demo) | ₹495 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 38 | Dot & Key Watermelon Cooling Sun... | Purplle (Demo) | ₹489 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 39 | Dot & Key Watermelon Cooling Sun... | Amazon India (Demo) | ₹380 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 13:38:10 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 40 | The Derma Co 1% Hyaluronic Sunsc... | Nykaa (Demo) | ₹449 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 41 | The Derma Co 1% Hyaluronic Sunsc... | Amazon India (Demo) | ₹469 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 42 | The Derma Co 1% Hyaluronic Sunsc... | Purplle (Demo) | ₹479 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 43 | Minimalist 10% Niacinamide Face ... | Nykaa (Demo) | ₹569 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 44 | Minimalist 10% Niacinamide Face ... | Purplle (Demo) | ₹599 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 45 | Minimalist 10% Niacinamide Face ... | Tira (Demo) | ₹569 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 46 | Minimalist 10% Niacinamide Face ... | Amazon India (Demo) | ₹559 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 47 | Plum 15% Vitamin C Glow Face Ser... | Nykaa (Demo) | ₹675 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 48 | Plum 15% Vitamin C Glow Face Ser... | Tira (Demo) | ₹710 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 49 | Plum 15% Vitamin C Glow Face Ser... | Purplle (Demo) | ₹690 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 50 | COSRX Advanced Snail 96 Mucin Po... | Nykaa (Demo) | ₹1,450 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 51 | COSRX Advanced Snail 96 Mucin Po... | Tira (Demo) | ₹1,375 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 52 | COSRX Advanced Snail 96 Mucin Po... | Myntra (Demo) | ₹1,410 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 53 | Cetaphil Gentle Skin Cleanser Hy... | Nykaa (Demo) | ₹333 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 54 | Cetaphil Gentle Skin Cleanser Hy... | Amazon India (Demo) | ₹349 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 55 | Cetaphil Gentle Skin Cleanser Hy... | Purplle (Demo) | ₹355 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 56 | Forest Essentials Delicate Facia... | Nykaa (Demo) | ₹1,550 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 57 | Forest Essentials Delicate Facia... | Tira (Demo) | ₹1,475 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 58 | Clinique Moisture Surge 100H Aut... | Nykaa (Demo) | ₹2,950 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 59 | Clinique Moisture Surge 100H Aut... | Tira (Demo) | ₹2,790 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 60 | Clinique Moisture Surge 100H Aut... | Myntra (Demo) | ₹2,850 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 61 | Dot & Key Ceramides & Hyaluronic... | Nykaa (Demo) | ₹395 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 62 | Dot & Key Ceramides & Hyaluronic... | Amazon India (Demo) | ₹420 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 63 | Dot & Key Ceramides & Hyaluronic... | Purplle (Demo) | ₹415 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 64 | M.A.C Retro Matte Lipstick - Rub... | Nykaa (Demo) | ₹2,300 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 65 | M.A.C Retro Matte Lipstick - Rub... | Tira (Demo) | ₹2,185 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 66 | M.A.C Retro Matte Lipstick - Rub... | Myntra (Demo) | ₹2,300 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 67 | Kay Beauty Matteinee Matte Lipst... | Nykaa (Demo) | ₹799 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 68 | Kay Beauty Matteinee Matte Lipst... | Amazon India (Demo) | ₹849 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 69 | Maybelline Fit Me Matte + Porele... | Nykaa (Demo) | ₹549 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 70 | Maybelline Fit Me Matte + Porele... | Purplle (Demo) | ₹579 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 71 | Maybelline Fit Me Matte + Porele... | Amazon India (Demo) | ₹535 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 72 | Maybelline Fit Me Matte + Porele... | Myntra (Demo) | ₹599 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 73 | Rare Beauty Soft Pinch Liquid Bl... | Tira (Demo) | ₹2,400 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 74 | Rare Beauty Soft Pinch Liquid Bl... | Nykaa (Demo) | ₹2,400 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 75 | Kay Beauty Creme Blush - Sweethe... | Nykaa (Demo) | ₹799 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 76 | Kay Beauty Creme Blush - Sweethe... | Amazon India (Demo) | ₹820 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 77 | Maybelline Lash Sensational Sky ... | Nykaa (Demo) | ₹799 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 78 | Maybelline Lash Sensational Sky ... | Amazon India (Demo) | ₹749 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 79 | Maybelline Lash Sensational Sky ... | Purplle (Demo) | ₹820 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 80 | Kay Beauty 24HR Waterproof Metal... | Nykaa (Demo) | ₹299 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 81 | Kay Beauty 24HR Waterproof Metal... | Purplle (Demo) | ₹320 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 82 | Laneige Lip Sleeping Mask Berry | Nykaa (Demo) | ₹600 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 83 | Laneige Lip Sleeping Mask Berry | Tira (Demo) | ₹570 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 84 | Laneige Lip Sleeping Mask Berry | Myntra (Demo) | ₹585 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 85 | Dot & Key Vitamin C + E Lip Slee... | Nykaa (Demo) | ₹275 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 86 | Dot & Key Vitamin C + E Lip Slee... | Amazon India (Demo) | ₹290 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 87 | Simple Kind to Skin Micellar Cle... | Nykaa (Demo) | ₹385 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 88 | Simple Kind to Skin Micellar Cle... | Amazon India (Demo) | ₹399 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 89 | Simple Kind to Skin Micellar Cle... | Purplle (Demo) | ₹410 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 90 | Minimalist Maleic Bond Repair Co... | Nykaa (Demo) | ₹599 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 91 | Minimalist Maleic Bond Repair Co... | Amazon India (Demo) | ₹569 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 92 | Minimalist Maleic Bond Repair Co... | Purplle (Demo) | ₹599 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 93 | Chemist at Play Exfoliating Lact... | Nykaa (Demo) | ₹399 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 94 | Chemist at Play Exfoliating Lact... | Amazon India (Demo) | ₹419 | LIVE_VERIFIED | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Downgraded: Seeded demo record; no live API credentials or evidence reference. |
| 95 | Chemist at Play Exfoliating Lact... | Purplle (Demo) | ₹429 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 07:09:25 | Confirmed demo store catalog offer. |
| 998 | Cheaper Vitamin C Serum | TechMart (Demo) | ₹800 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 13:44:57 | Confirmed demo store catalog offer. |
| 999 | Test Vitamin C Serum | TechMart (Demo) | ₹1,500 | DEMO | **DEMO** | None (`evidence_references` = 0) | 2026-11-09 13:44:59 | Confirmed demo store catalog offer. |

---

## 3. Transparency & Presentation Safeguards

1. **Frontend Badges:** In `LiveRetailerPriceComparison.tsx`, all demo store offers now display the explicit badge `Demo Price (Simulated)` with an amber indicator rather than the ambiguous `Feed Active` label.
2. **Savings & Deals:** Deal sections in `DealSection.tsx` have been updated with `Catalog Demo Deals` and `Featured Beauty Deals (DEMO)` badges, explicitly clarifying to users that price drops are illustrative algorithms rather than verified market arbitrage.
3. **Product Detail Baseline:** The product detail price box is clearly labelled `Catalog Baseline Offer (Demo Price)`.
4. **Zero Fabrication Policy:** PriceWise AI never fabricates retailer API responses, timestamps, or verified checkmarks.