# PriceWise AI — Phase 13.4: Render Backend Deployment Preparation Report

**Date:** November 10, 2026  
**Auditor:** Antigravity Autonomous Pair Programmer  
**Target Environment:** Render Web Service (FastAPI / Uvicorn) connected to Neon Staging PostgreSQL (`aws-us-east-1`)  
**Status:** **AWAITING EXTERNAL RENDER AUTHORIZATION (SAFETY HALT PER INSTRUCTIONS)**

---

## Executive Summary

Phase 13.3 successfully migrated and verified all 24 canonical tables and 3,125 rows into the Neon PostgreSQL staging branch (`br-aged-glade-bbyyq4r7`).

All backend deployment artifacts for Render have been prepared, hardened, and verified locally:
1. `render.yaml` Blueprint configured for FastAPI on Python 3 with zero-redundancy external Neon database binding.
2. `Procfile` configured with `web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`.
3. `Dockerfile` multi-stage container configured with health checks on `/api/health/ready` and `.dockerignore` shielding all secrets and SQLite files.
4. FastAPI application configured for staging mode (`ENVIRONMENT=staging`), strict CORS, and automatic fail-safe heuristic fallback for Gemini queries.

Inspection confirmed that no Render CLI or Render API credentials exist in the local development environment. Per the explicit rules of Phase 13.4, automated execution is halted to provide the operator with the exact account setup and deployment instructions.

---

## 1. Backend Configuration & Hardening Checklist

| Component | Configuration | Verification Finding | Status |
|---|---|---|:---:|
| **Startup Command** | `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT` | Verified in `Procfile`, `render.yaml`, and `Dockerfile`. | **`PASS`** |
| **PostgreSQL Driver** | `psycopg[binary]>=3.1.0` & `psycopg2-binary>=2.9.9` | Verified in `requirements.txt` with native C-extensions. | **`PASS`** |
| **Health Check Path** | `/api/health/ready` | Active DB readiness probe querying engine and latency. | **`PASS`** |
| **Database Binding** | Neon Staging Pooled Connection | `DATABASE_URL` connects to `ep-aged-salad-bbh2tnpl-pooler`. | **`PASS`** |
| **CORS Lockdown** | Restricted to Vercel staging & local ports | No wildcard `*` allowed in staging/production mode. | **`PASS`** |
| **Environment Mode** | `ENVIRONMENT=staging` | `IS_PRODUCTION=False`, `DEBUG=False`. | **`PASS`** |
| **Secret Protection** | Zero credentials in repo or container | Shielded via `.gitignore` and `.dockerignore`. | **`PASS`** |

---

## 2. Operator Setup & Authorization Runbook

To deploy the backend to Render without incurring any costs:

### Step 1: Sign In or Create a Free Account on Render
1. Navigate to **[Render Dashboard](https://dashboard.render.com)**.
2. Sign in with GitHub (using your authenticated GitHub account `humaidmalik63-png`).

### Step 2: Create a New Web Service
1. Click **New +** $\rightarrow$ **Web Service**.
2. Connect your GitHub repository (`price-comparison-website`).
3. Fill in the service configuration:
   - **Name:** `pricewise-backend-staging`
   - **Region:** `Frankfurt (EU Central)` or `Oregon (US West)` (free tier eligible)
   - **Branch:** `main` (or your current working branch)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** **Free** (0.1 CPU, 512 MB RAM — $0/month)
   - **Health Check Path:** `/api/health/ready`

### Step 3: Configure Environment Variables in Render Dashboard
Under **Environment Variables**, add the following:
- `ENVIRONMENT` = `staging`
- `DATABASE_URL` = *(Copy the pooled `DATABASE_URL` from your local `.env.local`)*
- `CORS_ORIGINS` = `https://pricewise-staging.vercel.app,http://localhost:5173`
- `SECRET_KEY` = *(Enter a secure 32+ character random string)*
- `GEMINI_MODEL` = `gemini-2.5-flash`
- `GEMINI_API_KEY` = *(Optional: your Gemini API key)*
- `RATE_LIMIT_PER_MINUTE` = `120`

### Step 4: Deploy and Record the Backend URL
1. Click **Create Web Service**.
2. Render will build the service and deploy it to a URL like:
   `https://pricewise-backend-staging.onrender.com`
3. Confirm the service is live by visiting `/api/health/ready` in your browser.

---

## 3. Post-Deployment Verification Commands

Once your Render service is deployed, inform Antigravity or provide the URL, and the automated suite will execute the full end-to-end verification:
```powershell
& "C:\Users\humai\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/verify_cloud_deployment.py --backend-url "https://<your-render-service>.onrender.com"
```

*Boundaries Maintained: Stopped per execution strategy. Awaiting operator Render backend deployment.*
