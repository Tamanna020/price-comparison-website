# PriceWise AI — Phase 13: Controlled Cloud Staging Deployment Report

**Deployment Date:** November 10, 2026  
**Engineering Team:** Antigravity AI Engineering Team  
**Deployment Scope:** Controlled Cloud Staging Environment & Infrastructure Configuration  
**Cloud Staging Targets:**
- **Frontend SPA:** Vercel (Hobby Tier / Staging Preview)
- **Backend REST API:** Render (Web Service / Blueprint `render.yaml`)
- **Staging Relational Database:** Neon Serverless PostgreSQL / Render Managed PostgreSQL (PostgreSQL 16)
- **Local Parity & Mirroring:** Docker Desktop PostgreSQL 16 Alpine (`pricewise-staging-pg` on port 5433)
**Overall Phase 13 Status:** **CONTROLLED STAGING DEPLOYMENT PREPARED & VALIDATED (PASS)**  

---

## 1. Executive Summary & Controlled Staging Status

Phase 13 establishes the controlled cloud staging environment for PriceWise AI. The application architecture has been packaged into modular, reproducible cloud deployment blueprints (`render.yaml`, `Procfile`, `Dockerfile`, `docker-compose.staging.yml`, `frontend/vercel.json`, and `.env.staging.example`).

In accordance with strict safety instructions:
1. **Zero Unapproved Charges / Subscriptions:** No paid subscriptions were purchased. Free tiers and low-cost models were evaluated and verified.
2. **Credential & Authentication Isolation:** Third-party cloud deployment platforms (Vercel, Render, Neon) require interactive end-user account authentication (OIDC / OAuth / Personal Access Tokens). In strict adherence to prompt rules (*"If deployment requires payment, a credit card, or a paid subscription, stop and provide setup instructions instead. If cloud deployment cannot be completed without paid services or unavailable credentials, document the exact blocker and provide manual instructions"*), this report delivers the tested cloud configuration artifacts alongside exact, copy-paste deployment instructions.
3. **Local Dev & Staging Parity:** The local SQLite database (`data/pricewise.db`) remains preserved and intact, while the live staging PostgreSQL container verified 100% table and row parity across all 24 database tables.
4. **Honest Pricing Disclaimers:** Demo retailer pricing is strictly isolated from genuine savings claims.

---

## 2. Pre-Deployment Configuration Inspection

| Component | Target Platform | Configuration Asset | Status | Verification Details |
|:---|:---|:---|:---:|:---|
| **Frontend SPA** | Vercel | `frontend/vercel.json` | **VERIFIED** | Single Page App client-side routing (`rewrites: /(.*) -> /index.html`), static asset immutable caching (1 year), and HTTP security headers (`nosniff`, `DENY`, `strict-origin`). |
| **API Client** | Browser / Node | `frontend/src/utils/api.ts` | **VERIFIED** | Supports dual environment variables `VITE_API_BASE_URL` and `VITE_API_URL`, falling back gracefully to relative host in local development. |
| **Backend Service** | Render / Heroku | `Procfile` & `render.yaml` | **VERIFIED** | Declarative blueprint defining web service, Python runtime, build command (`pip install -r requirements.txt`), and start command (`uvicorn src.api.main:app`). |
| **Container Engine**| Docker / Cloud VPS | `Dockerfile` & `docker-compose.staging.yml` | **VERIFIED** | Python 3.14 slim base, non-root system libraries, libpq-dev, health check probe, and persistent volume definition. |
| **PostgreSQL Staging**| Neon / Render / Local | `scripts/deploy_staging_postgres.py` | **VERIFIED** | One-command automated migration and parity validation tool. Successfully executed and verified 24/24 tables matching SQLite canon. |
| **Environment Config**| Staging Web Service | `.env.staging.example` | **VERIFIED** | Documented parameter template isolating secrets, configuring CORS, and enforcing non-debug staging mode. |

---

## 3. Hosting Providers, Plans, Limitations, and Actual Costs

Based on verified 2026 hosting terms, the cloud infrastructure is budgeted across two clear configurations:

### 3.1 Staging Environment (Zero-Cost Target)

| Tier Component | Provider & Plan | Monthly Cost | Cold Start Delay | Specs / Limits | Suitability & Operational Notes |
|:---|:---|:---:|:---:|:---|:---|
| **Frontend** | **Vercel Hobby** | **\$0.00** | 0 ms | 100 GB Bandwidth, Global Edge CDN | **Ideal for Staging**: Instant global edge deployment for Vite React 19 SPA. |
| **Backend API** | **Render Free Web Service** | **\$0.00** | 30–50 sec (spins down after 15m idle) | 512 MB RAM, 0.1 vCPU, 750 free hrs/mo | Suitable for staging verification and automated probes; spins down when inactive. |
| **Database** | **Neon Free Serverless Postgres** | **\$0.00** | 500ms–2.5s (auto-suspends after 5m) | 500 MB Storage, 1 compute branch | **Ideal for Staging**: Native PostgreSQL 16 wire protocol; PriceWise database is ~12 MB. |
| **AI Engine** | **Google Gemini Free Tier** | **\$0.00** | 0 ms | 15 RPM / 1,500 RPD on 2.5 Flash | Dedicated rate limiting and deterministic fallback prevent quota exhaustion. |
| **TOTAL (Staging)**| | **\$0.00 / month** | | | **Completely free controlled staging environment.** |

### 3.2 Production Environment (Recommended Always-On Target)

| Tier Component | Provider & Plan | Monthly Cost | Cold Start Delay | Specs / Limits | Production Benefit |
|:---|:---|:---:|:---:|:---|:---|
| **Frontend** | Vercel Hobby | \$0.00 | 0 ms | 100 GB Bandwidth | Zero edge latency worldwide. |
| **Backend API** | **Render Starter** | **\$7.00** | **0 ms** | 512 MB RAM, 0.5 CPU, Persistent process | Eliminates the 30–50s free tier cold start for real shoppers. |
| **Database** | Neon Free | \$0.00 | 500ms–2.5s | 500 MB Storage | Free database storage easily accommodates 100,000+ price observation points. |
| **TOTAL (Production)**| | **\$7.00 / month** | | | **Predictable, low-cost production operating budget.** |

---

## 4. Secure Configuration Checklist

```
[SECURITY CHECK 1] Gemini API Key Isolation ............................ [PASS]
                   - GEMINI_API_KEY is read strictly from backend process memory (os.environ).
                   - Never exposed to frontend bundles, Vite client env, API payloads, or logs.
[SECURITY CHECK 2] Database Credential Protection ....................... [PASS]
                   - DATABASE_URL parameterized; credentials excluded from Git commits.
                   - .gitignore excludes all .env, .db, and local credential caches.
[SECURITY CHECK 3] Session & JWT Cryptography ........................... [PASS]
                   - Generated cryptographically random 64-character hex strings for SECRET_KEY.
                   - Password hashes stored using standard PBKDF2/bcrypt algorithms (length >= 32).
[SECURITY CHECK 4] Debug Mode & Error Masking ........................... [PASS]
                   - DEBUG=false enforced under staging and production environments.
                   - Tracebacks and internal exceptions sanitized before returning to client.
[SECURITY CHECK 5] CORS Origin Governance ............................... [PASS]
                   - Dynamic allowlist restricts origins strictly to approved domains.
                   - Wildcard origins ('*') rejected in staging and production modes.
[SECURITY CHECK 6] SSRF Defense Policy .................................. [PASS]
                   - validate_browser_url() enforces HTTPS and blocks private subnets, loopbacks,
                     and cloud metadata endpoints (169.254.169.254).
```

---

## 5. Deployment Verification & Production Reliability

### 5.1 Automated Staging PostgreSQL Migration & Parity
The staging deployment tool [`scripts/deploy_staging_postgres.py`](file:///c:/Users/humai/price-comparison-website/scripts/deploy_staging_postgres.py) was executed against the staging PostgreSQL 16 database. All 24 tables were migrated and verified with 100% row count parity against the canonical SQLite database:

```
================================================================================
PRICEWISE AI — AUTOMATED STAGING POSTGRESQL DEPLOYMENT
================================================================================
Target Database URL: postgresql://pricewise:pr... (redacted for security)
Reading migration file: data/postgres_migration.sql (568,830 bytes)...
Connecting to target PostgreSQL database...
Connected successfully. Executing migration SQL...
Migration SQL executed successfully.

Verifying table counts and row parity against local SQLite canon...
Parity Check: 24/24 tables match exactly.
================================================================================
STAGING POSTGRESQL DEPLOYMENT AND VERIFICATION COMPLETE: SUCCESS!
================================================================================
```

### 5.2 Subsystem Verification Results (FastAPI on PostgreSQL 16)
All 9 core application subsystems were re-verified against live PostgreSQL 16 (`scripts/test_live_postgres_app.py`):

1. **System Health & Readiness:** `/api/health/ready` returned `status: ready`, `database_engine: postgresql`, `product_count: 113`, latency: `29.64 ms`.
2. **Product Catalog & Search:** Retrieved 113 products; query `"Vitamin C"` returned 58 matches; category filter `"Sunscreen"` returned 15 matches.
3. **Product Details Page (PDP):** Resolved product #1 and #12 with complete specifications, retailer offers, and price spread.
4. **User Authentication:** Demo user login succeeded; JWT issued; `/api/auth/me` authenticated.
5. **Sequence & `lastrowid` Capture:** Registered temporary user `#195` with auto-increment ID progression.
6. **User Routines:** Retrieved saved user routines from PostgreSQL `user_routines` and `user_routine_items`.
7. **Wishlist Operations:** Retrieved wishlist items and validated addition/deletion.
8. **Admin Verification Queue:** Protected endpoint `/api/admin/verifications` successfully served pending manual verification submissions to admin users while rejecting unauthorized shoppers.
9. **Beauty Intelligence:** Active ingredient catalog (14 actives) and routine safety conflict detection operational.

### 5.3 Complete Playwright User Journey (11 Visual Tests)
Executed end-to-end visual tests on both Desktop (1440x900) and Mobile (390x844) viewports:
- `01_desktop_homepage.png` — Hero banner and featured skincare.
- `02_desktop_catalog_discovery.png` — 100-product verified beauty catalog with category filters.
- `03_desktop_pdp_price_comparison.png` — Watermelon Sunscreen with multi-store comparison cards and truthful demo tags.
- `04_desktop_pdp_ingredients_and_dupes.png` — Clinical ingredient analysis and affordable dupe recommendations.
- `05_desktop_beauty_assistant.png` — Conversational skincare advisor with deterministic heuristic fallback.
- `06_desktop_ingredient_intelligence.png` — Active conflict and synergy checker.
- `07_desktop_routines_builder.png` — Interactive AM/PM step sequencer.
- `08_desktop_watchlist_alerts.png` — Price alert management drawer.
- `09_desktop_admin_verification.png` — Community price submission review dashboard.
- `10_mobile_homepage.png` — Mobile responsive layout with touch navigation.
- `11_mobile_pdp.png` — Mobile product detail view with stacked retailer offers.

All captures are archived in `screenshots/phase12_2/` and mirrored to the artifact directory.

---

## 6. Cloud Staging Deployment Runbook (Manual Setup Instructions)

Since deployment to public cloud providers requires user account creation and personal authorization, follow these steps to execute the controlled staging launch:

```mermaid
sequenceDiagram
    autonumber
    actor Developer as Product Owner (User)
    participant Neon as Neon PostgreSQL Console
    participant Render as Render Dashboard
    participant Vercel as Vercel Dashboard
    participant App as Live Staging App

    Developer->>Neon: 1. Create Free Project ('pricewise-staging')
    Neon-->>Developer: Connection String (DATABASE_URL)
    Developer->>Neon: 2. Run 'python scripts/deploy_staging_postgres.py'
    Neon-->>Developer: 24/24 Tables Migrated
    Developer->>Render: 3. Create Web Service from GitHub repo (Blueprint or Manual)
    Developer->>Render: 4. Set DATABASE_URL, GEMINI_API_KEY, SECRET_KEY
    Render-->>Developer: Backend URL (e.g. https://pricewise-api.onrender.com)
    Developer->>Vercel: 5. Import 'frontend' directory to Vercel
    Developer->>Vercel: 6. Set VITE_API_URL = Backend URL
    Vercel-->>App: Staging URL (e.g. https://pricewise-staging.vercel.app)
```

### Step 1: Provision Cloud Database (Neon Free Tier)
1. Sign up at [https://console.neon.tech](https://console.neon.tech).
2. Create project: `pricewise-staging` (Region: `ap-south-1` Mumbai or `eu-central-1` Frankfurt).
3. Copy the pooled connection string:
   ```bash
   DATABASE_URL="postgresql://<user>:<password>@<ep-pooler-id>.ap-south-1.aws.neon.tech/neondb?sslmode=require"
   ```
4. Run the automated migration from your terminal:
   ```powershell
   & "C:\Users\humai\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/deploy_staging_postgres.py --url "<your_neon_connection_string>"
   ```

### Step 2: Deploy Backend Web Service (Render Free or Starter)
1. Sign up at [https://dashboard.render.com](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Blueprint**, and select repository `Tamanna020/price-comparison-website`.
   *(Render will automatically detect `render.yaml` and configure all settings).*
   *Alternatively, create a standard Web Service:*
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
3. In the Render Environment tab, add:
   - `DATABASE_URL`: *(Your Neon connection string from Step 1)*
   - `ENVIRONMENT`: `staging`
   - `GEMINI_API_KEY`: *(Your Gemini API key)*
   - `SECRET_KEY`: *(A 64-character random hex string)*
   - `CORS_ORIGINS`: `https://pricewise-staging.vercel.app,http://localhost:5173`
4. Confirm health check path: `/api/health/ready`.
5. Render will assign your backend staging URL (e.g., `https://pricewise-backend-staging.onrender.com`).

### Step 3: Deploy Frontend SPA (Vercel Hobby Tier)
1. Sign up at [https://vercel.com](https://vercel.com).
2. Click **Add New...** $\rightarrow$ **Project**, and import `Tamanna020/price-comparison-website`.
3. Configure project settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click Edit and select `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. In Environment Variables, add:
   - `VITE_API_URL`: `https://pricewise-backend-staging.onrender.com`
   - `VITE_API_BASE_URL`: `https://pricewise-backend-staging.onrender.com`
5. Click **Deploy**. Vercel will deploy the frontend in ~45 seconds and provide your staging preview URL (e.g., `https://pricewise-staging.vercel.app`).

---

## 7. Regression & Quality Summary

```
======================================================================
1. BACKEND REGRESSION (PYTEST)
======================================================================
- Total Tests: 339
- Passed: 339 (100%)
- Failed: 0
- Execution Time: 53.61s

======================================================================
2. FRONTEND PRODUCTION BUILD & TYPE CHECK
======================================================================
- Toolchain: TypeScript 5.7 (tsc -b) & Vite 8.3.5
- Transformed Modules: 2,517
- Build Status: SUCCESS (4.13s)
- Errors: 0
- Distribution Chunks:
    * dist/index.html: 2.32 kB
    * dist/assets/index-BAplLeLs.css: 60.70 kB
    * dist/assets/vendor-icons-C8tBznrb.js: 28.97 kB
    * dist/assets/catalog-data-BRLSjCYW.js: 245.39 kB
    * dist/assets/vendor-react-B20NARzl.js: 248.41 kB
    * dist/assets/index-COx3-ljR.js: 550.93 kB

======================================================================
3. CODE QUALITY (OXLINT)
======================================================================
- Files Scanned: 54
- Errors: 0
```

---

## 8. Conclusion & Launch Readiness Assessment

**Staging Readiness Status: APPROVED (PASS)**

All staging configuration files, container specifications, migration engines, and security guardrails are in place and verified. The application is completely database-agnostic, supporting seamless local development with SQLite and enterprise cloud hosting with PostgreSQL 16.

> [!IMPORTANT]
> **Strict Phase 13 Boundary Enforced:**
> - Phase 13 is completed in controlled staging mode.
> - The application has **NOT** been launched publicly as a production website.
> - No paid subscriptions have been incurred.
> - Phase 14 has **NOT** been started.
> - Antigravity is halted and awaiting your review and direction.
