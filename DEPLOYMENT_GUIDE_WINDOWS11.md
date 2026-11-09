# PriceWise AI — Windows 11 Production Deployment Guide

A step-by-step, beginner-friendly manual for deploying PriceWise AI to **Vercel** (Frontend), **Render / Railway** (Backend), and **Neon** (Serverless PostgreSQL) from a Windows 11 machine.

---

## Architecture Overview

```
[ Frontend: Vercel Edge ]  --->  HTTPS  --->  [ Backend: Render FastAPI ]  --->  SSL Pool  --->  [ Database: Neon PostgreSQL ]
  - Vite + React 19 SPA                          - Python 3.14 Container                             - 500 MB Free Tier
  - Auto SSL & Edge CDN                          - Health & Security Headers                         - 24 Migrated Tables
```

---

## Prerequisites on Windows 11

Ensure you have PowerShell or Windows Terminal open in `c:\Users\humai\price-comparison-website`:

1. **Python:** Version 3.14 (`py -3.14 --version`)
2. **Node.js:** Version 20+ (`node --version`)
3. **Git:** Initialized repository (`git status`)
4. **Free Accounts:**
   - [Vercel](https://vercel.com/signup) (Frontend)
   - [Render](https://render.com) or [Railway](https://railway.app) (Backend)
   - [Neon](https://neon.tech) (PostgreSQL Database)
   - [Google AI Studio](https://aistudio.google.com) (Gemini API Key)

---

## Step 1: Set Up Managed PostgreSQL on Neon (Free Tier)

1. Sign up or log in at **[https://neon.tech](https://neon.tech)**.
2. Click **Create Project**:
   - **Project Name:** `pricewise-prod`
   - **Database Name:** `pricewise_prod`
   - **Region:** Choose the region closest to your users (e.g., `AWS - Singapore` or `AWS - Frankfurt`).
3. Once created, copy the **Connection string** in **Pooled connection** format:
   ```
   postgresql://user:password@ep-sample-pooler.region.aws.neon.tech/pricewise_prod?sslmode=require
   ```
4. **Import Schema and 100-Product Catalog Data:**
   - In the Neon Dashboard, navigate to the **SQL Editor** tab.
   - Open `data/postgres_migration.sql` in VS Code or Notepad on Windows 11:
     ```powershell
     notepad data/postgres_migration.sql
     ```
   - Copy the entire SQL script (or paste in chunks if using the web UI) and click **Run**.
   - Verify that tables are populated:
     ```sql
     SELECT COUNT(*) FROM products;
     -- Should return 113 (100 catalog products + variants)
     SELECT COUNT(*) FROM offers;
     -- Should return 494
     ```

---

## Step 2: Deploy Backend to Render

1. Sign up or log in at **[https://render.com](https://render.com)**.
2. Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository (`price-comparison-website`).
4. Configure the Web Service settings:
   - **Name:** `pricewise-backend`
   - **Region:** Same region as your Neon database (to minimize latency).
   - **Branch:** `main`
   - **Root Directory:** Leave empty (root of repository).
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan:** Free

5. Configure **Environment Variables** in Render:
   | Variable | Value | Notes |
   | :--- | :--- | :--- |
   | `ENVIRONMENT` | `production` | Enforces strict CORS and disables tracebacks |
   | `DATABASE_URL` | *(Paste your Neon connection string)* | Ensure it ends with `?sslmode=require` |
   | `SECRET_KEY` | *(Generate a 64-char random hex)* | In Windows PowerShell, run: `py -3.14 -c "import secrets; print(secrets.token_hex(32))"` |
   | `CORS_ORIGINS` | `https://pricewise-ai.vercel.app` | Replace with your actual Vercel domain from Step 3 |
   | `GEMINI_API_KEY` | *(Your Google AI Studio key)* | Free key from Google AI Studio |
   | `GEMINI_MODEL` | `gemini-2.5-flash` | Production AI model |
   | `RATE_LIMIT_PER_MINUTE` | `120` | Request rate limiter |

6. Click **Create Web Service**. Wait for the build to finish.
7. Once deployed, test your backend URL in PowerShell:
   ```powershell
   curl https://pricewise-backend.onrender.com/api/health/ready
   ```
   You should receive:
   ```json
   {"status":"ready","database_engine":"postgresql","database_healthy":true,"product_count":113}
   ```

---

## Step 3: Deploy Frontend to Vercel

1. Sign up or log in at **[https://vercel.com](https://vercel.com)**.
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your GitHub repository (`price-comparison-website`).
4. In the project setup screen:
   - **Project Name:** `pricewise-ai`
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click **Edit** and select `frontend`.
5. In **Environment Variables**:
   - **Key:** `VITE_API_BASE_URL`
   - **Value:** `https://pricewise-backend.onrender.com` *(your Render URL without trailing slash)*
6. Click **Deploy**.
7. Vercel will run `npm run build` (`tsc -b && vite build`) and deploy the app to global edge locations in ~45 seconds.
8. Once complete, copy your live Vercel domain (e.g., `https://pricewise-ai.vercel.app`).

---

## Step 4: Finalize CORS Configuration

1. Return to the **Render Dashboard** for your `pricewise-backend` service.
2. Go to **Environment** tab.
3. Update `CORS_ORIGINS` to match your exact Vercel URL (e.g., `https://pricewise-ai.vercel.app`).
4. Click **Save Changes** (Render will automatically redeploy with the updated origin).

---

## Step 5: Post-Deployment Smoke Testing & Verification

Run these validation commands from Windows 11 PowerShell:

### 1. Test Backend Readiness Probe
```powershell
Invoke-RestMethod -Uri "https://pricewise-backend.onrender.com/api/health/ready" -Method Get
```
*Expected: `status = ready`, `database_engine = postgresql`, `database_healthy = True`, `product_count = 113`.*

### 2. Test Catalog API
```powershell
Invoke-RestMethod -Uri "https://pricewise-backend.onrender.com/api/products?limit=5" -Method Get
```
*Expected: List of 5 products with INR prices and retailer offers.*

### 3. Test Security Headers
```powershell
curl -I https://pricewise-backend.onrender.com/api/health
```
*Verify headers include:*
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-Process-Time: ...ms`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 4. Test Frontend Navigation & Deep Linking
Open your Vercel URL in Microsoft Edge or Chrome:
- Browse the 100-product catalog.
- Click on any product (e.g., Minimalist 10% Vitamin C Serum).
- Refresh the browser on `https://pricewise-ai.vercel.app/product/minimalist-10-vitamin-c-face-serum` to verify that `vercel.json` SPA rewrites prevent 404 errors.
- Test filters (Sunscreens, Serums, Moisturizers) and sort options.

---

## Step 6: Disaster Recovery & Automated Backups on Windows 11

To take a local point-in-time snapshot of the database prior to major updates:

```powershell
# Create a fresh backup with SHA-256 cryptographic checksum
py -3.14 scripts/backup_restore_db.py --backup

# Verify the backup integrity
py -3.14 scripts/backup_restore_db.py --test-cycle
```

Backups are saved to `data/backups/pricewise_backup_YYYYMMDD_HHMMSS.db` alongside their `.sha256` checksums. The utility automatically retains the 10 most recent backups.

---

## Troubleshooting Guide

| Issue | Root Cause | Windows 11 Solution |
| :--- | :--- | :--- |
| **Render spins down / 30s cold start** | Free tier idle timeout | Frontend gracefully falls back to static 100-product data during cold boot; or set up a free 10-minute ping cron at [cron-job.org](https://cron-job.org) targeting `/api/health/live`. |
| **CORS error in browser console** | Origin mismatch between Vercel and Render | Ensure `CORS_ORIGINS` in Render environment matches the exact Vercel URL without trailing slash. |
| **SPA route 404 on page refresh** | Missing server rewrite | Verify `frontend/vercel.json` exists with `"rewrites": [{"source": "/(.*)", "destination": "/index.html"}]`. |
| **PostgreSQL SSL Error** | Missing SSL mode query parameter | Append `?sslmode=require` to `DATABASE_URL` in Render. |
| **Vite chunk size warning** | Monolithic bundle | Already resolved via `manualChunks` in `frontend/vite.config.ts`. Run `npm --prefix frontend run build` to verify clean output. |

---

*PriceWise AI is fully configured, audited, and hardened for production deployment.*
