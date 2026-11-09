# PriceWise AI — Manual Price Verification Guide

**Version:** 1.0  
**Platform:** PriceWise AI Beauty  
**Audience:** End Users (Beauty Shoppers)

---

## 📋 Overview

PriceWise AI now lets you **verify prices manually** when automated price checking isn't available. Since many Indian beauty retailers (Nykaa, Purplle, Tira, Myntra) block automated price checking, we've built a **manual verification system** that puts you in control.

> **Key Principle:** You submit the URL → We verify (where permitted) → You get a clear verification status badge.

---

## 🎯 What You Can Do

| Action | When to Use | Result |
|--------|-------------|--------|
| **Verify Price** | You found a product on a retailer site | Get a verified price with status badge |
| **Report Price** | You spotted an incorrect price on PriceWise | Submit correction for review |
| **Check History** | Want to see your past verifications | View all submissions with status |

---

## 🔍 How to Verify a Price

### Step 1: Find the Product on PriceWise
Navigate to any product detail page on PriceWise AI Beauty.

### Step 2: Click "Verify Price"
On the product detail page, you'll see a **"Verify Price"** button in the Live Price Comparison section.

![Verify Price Button](docs/images/verify-price-button.png)

### Step 3: Paste the Retailer URL
A modal will open. Paste the **exact product URL** from the retailer's website.

**Supported Retailers:**
- 🛒 **Nykaa** — `https://www.nykaa.com/...`
- 🛒 **Myntra** — `https://www.myntra.com/...`
- 🛒 **Purplle** — `https://www.purplle.com/...`
- 🛒 **Tira Beauty** — `https://www.tirabeauty.com/...`
- 🛒 **Amazon India** — `https://www.amazon.in/...`

**Example URLs:**
```
✅ https://www.nykaa.com/dot-key-watermelon-cooling-sunscreen-spf-50-pa/p/10204738
✅ https://www.myntra.com/lipstick/lakme/lakme-absolute-matte-revolution-lipstick/12345678/buy
✅ https://www.amazon.in/dp/B08N5WRWNW
```

### Step 4: Add Optional Details
You can optionally provide:
- **Price you saw** (if different from listed)
- **Size/Volume** (e.g., "50ml", "30g")
- **Shade** (e.g., "Ruby Woo", "Cherry Red")
- **Formulation** (e.g., "Matte", "Gel", "Cream")
- **Notes** (any additional context)

### Step 5: Submit
Click **"Check This Product's Price"**. The system will:
1. ✅ Validate the URL format and retailer match
2. 🔍 Attempt to fetch the live product page (where permitted)
3. 📊 Extract price, MRP, discount, size, shade, formulation
4. 📝 Save your verification request with status

---

## 📊 Understanding Verification Statuses

Every verification gets a **status badge** that tells you exactly how the price was verified:

| Badge | Color | Meaning |
|-------|-------|---------|
| 🟢 **LIVE_VERIFIED** | Green | Price fetched live from retailer just now |
| 🔵 **MANUAL_VERIFIED** | Blue | You (or admin) manually confirmed with evidence |
| 🟡 **CACHED** | Yellow | Verified recently (< 10 min ago), served from cache |
| ⚪ **HISTORICAL** | Gray | Older price from our database |
| 🟠 **POSSIBLE_MATCH** | Orange | Product found but variant uncertain (size/shade mismatch) |
| 🔴 **RESTRICTED** | Red | Retailer blocked automated access (Cloudflare, login wall) |
| ⚫ **UNAVAILABLE** | Dark Gray | Could not extract price from page |
| ⚪ **DEMO** | Light Gray | Academic demo data (not real) |

> **⚠️ Important:** A user-submitted price starts as **POSSIBLE_MATCH** or **UNAVAILABLE**. It only becomes **MANUAL_VERIFIED** after admin review with evidence.

---

## 🚨 How to Report an Incorrect Price

Found a wrong price on PriceWise? Help the community by reporting it!

### Step 1: Click "Report Price"
On any product detail page, click the **"Report Price"** button (near the price display).

### Step 2: Fill the Form
| Field | Required? | What to Enter |
|-------|-----------|---------------|
| **Retailer** | ✅ Yes | Nykaa, Myntra, Purplle, Tira, Amazon |
| **Product URL** | ✅ Yes | Exact product page URL |
| **Correct Price** | ✅ Yes | The price you actually see |
| **MRP** | Optional | Maximum Retail Price if visible |
| **Size/Volume** | Optional | e.g., "50ml", "30g" |
| **Shade** | Optional | e.g., "Ruby Woo", "Cherry Red" |
| **Formulation** | Optional | e.g., "Matte", "Gel", "Waterproof" |
| **Evidence URL** | Optional | Screenshot on Imgur, Google Drive, etc. |
| **Notes** | Optional | Any extra context |

### Step 3: Submit
Click **"Submit Correction"**. Your submission enters the review queue.

---

## 📋 What Happens After You Submit?

### For Verifications:
| Status | What It Means | Next Steps |
|--------|---------------|------------|
| **pending** | Submitted, awaiting check | System will attempt live check |
| **verified** | Price confirmed | You'll see `MANUAL_VERIFIED` badge |
| **restricted** | Retailer blocked access | Shows `RESTRICTED` badge |
| **unavailable** | Could not extract price | Shows `UNAVAILABLE` badge |

### For Price Corrections:
| Status | What It Means |
|--------|---------------|
| **pending** | Under review |
| **approved** | Verified & merged into database |
| **rejected** | Evidence insufficient or incorrect |
| **merged** | Integrated into live data |

> **🔔 Notifications:** Currently, you'll need to check back on the page for status updates. Email notifications coming in Phase 8E.

---

## 🔒 Privacy & Security

| Protection | How It Works |
|------------|--------------|
| **Your Data** | Only you can see your submissions (user-isolated) |
| **No PII in URLs** | We never store personal info in URLs |
| **SSRF Protection** | Blocks localhost, private IPs, cloud metadata |
| **Domain Allowlist** | Only 5 approved retailers accepted |
| **Rate Limiting** | Max 30 requests/minute per retailer |

---

## ❓ Frequently Asked Questions

### Q: Why can't you check Nykaa/Purplle/Tira prices automatically?
**A:** These retailers use Cloudflare bot protection that blocks automated browsers. We respect their terms of service and don't bypass protection. Manual verification is the compliant alternative.

### Q: My submitted price was marked "POSSIBLE_MATCH". Why?
**A:** The product was found but variant details (size, shade, formulation) don't perfectly match our catalog. An admin needs to review before upgrading to `MANUAL_VERIFIED`.

### Q: Can I verify prices without an account?
**A:** No. You must be logged in to submit verifications or corrections. This prevents spam and ensures accountability.

### Q: How long does verification take?
- **Live check:** Usually < 10 seconds (if retailer permits)
- **Manual review:** Up to 24 hours for admin review
- **Cached results:** Instant (< 1 second)

### Q: What if the retailer price changed since I submitted?
The system records the **timestamp** of each verification. You can re-submit anytime to get fresh data.

### Q: Can I edit or delete my submission?
Currently, only admins can modify status. Contact support if you made an error.

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid URL format" | Ensure URL starts with `https://` and includes full path |
| "Retailer domain mismatch" | URL must match the selected retailer (e.g., nykaa.com for Nykaa) |
| "RESTRICTED" status | Retailer blocks bots. Try manual verification instead |
| "UNAVAILABLE" status | Price element not found on page. Try a different product URL |
| Submission failed | Check internet connection, try again in 30 seconds |

---

## 📞 Support

| Channel | For |
|---------|-----|
| **In-app Feedback** | Bug reports, feature requests |
| **Email** | `support@pricewise.ai` (manual verification issues) |
| **Documentation** | This guide + API docs at `/docs` |

---

## 📝 Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│  QUICK VERIFICATION CHEAT SHEET                        │
├─────────────────────────────────────────────────────────┤
│  1. Go to product page → Click "Verify Price"          │
│  2. Paste retailer URL (Nykaa, Myntra, Purplle, etc.)  │
│  3. Add price/size/shade if you know them              │
│  4. Click "Check This Product's Price"                 │
│  5. Wait for status badge:                             │
│     🟢 LIVE_VERIFIED    = Real-time confirmed          │
│     🔵 MANUAL_VERIFIED  = Confirmed with evidence      │
│     🟡 CACHED           = Recent cached result         │
│     🟠 POSSIBLE_MATCH   = Variant uncertain            │
│     🔴 RESTRICTED       = Retailer blocked bots        │
│     ⚫ UNAVAILABLE       = Could not extract price      │
│     ⚪ DEMO             = Sample data only             │
│                                                         │
│  Found wrong price? → Click "Report Price"             │
└─────────────────────────────────────────────────────────┘
```

---

## 📄 Document Info

| Field | Value |
|-------|-------|
| **Document** | `PRICEWISE_MANUAL_PRICE_VERIFICATION_GUIDE.md` |
| **Version** | 1.0 |
| **Last Updated** | November 9, 2026 |
| **Platform** | PriceWise AI Beauty |
| **Related** | `PHASE_8D_MANUAL_VERIFICATION_IMPLEMENTATION_REPORT.md` |

---

*PriceWise AI — Shop smarter. Save strategically.*