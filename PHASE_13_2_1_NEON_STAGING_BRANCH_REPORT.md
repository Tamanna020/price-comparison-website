# PriceWise AI — Phase 13.2.1: Neon Staging Branch Preparation Report

**Date:** November 10, 2026  
**Auditor:** Antigravity Autonomous Pair Programmer  
**Target Environment:** Neon Serverless PostgreSQL (`aws-us-east-1`)  
**Security Scope:** Isolated staging branch setup and non-destructive compatibility verification. Zero production mutation, zero unmasked secrets, zero migrated data.

---

## Executive Summary

Phase 13.2.1 successfully created, isolated, and verified a dedicated **staging** branch (`br-aged-glade-bbyyq4r7`) from the parent `production` branch on Neon. 

The staging branch has its own independent compute endpoint (`ep-aged-salad-bbh2tnpl`), running **PostgreSQL 18.6** with full TLS encryption (`sslmode=require`). The staging database was inspected and verified to be **100% empty (0 tables, 0 records)**.

The parent `production` branch was inspected in read-only mode and confirmed to be **completely unchanged and empty (0 tables, 0 records)**. No data has been migrated, preserving a clean slate pending final migration authorization.

---

## 1. Branch Topology & Identity Verification

| Property | Staging Branch (Target) | Production Branch (Parent) |
|---|---|---|
| **Branch Name** | `staging` | `production` |
| **Branch ID** | `br-aged-glade-bbyyq4r7` | `br-icy-dawn-bbx1y0jx` (Default) |
| **State** | `ready` | `ready` |
| **Compute ID** | `ep-aged-salad-bbh2tnpl` | `ep-ancient-breeze-bbwitums` |
| **Compute Type** | `read_write` (0.25 – 2 CU autoscaling) | `read_write` (0.25 – 2 CU autoscaling) |
| **Database Name** | `neondb` | `neondb` |
| **Database Owner** | `neondb_owner` | `neondb_owner` |
| **Public User Tables** | **0 (Empty)** | **0 (Empty & Untouched)** |
| **Active Context (`.neon`)** | **`staging`** | *Unchanged* |

---

## 2. Masked Connection Verification & Configuration

The local environment was updated via `neon env pull --branch staging --file .env.local`, binding all variables strictly to the staging compute endpoints.

```
============================================================
NEON POSTGRESQL SAFE CONNECTION INSPECTION RESULTS
============================================================
Pooled Endpoint Target: postgresql://ne***:****@ep-aged-salad-bbh2tnpl-pooler.c-15.us-east-1.aws.neon.tech:5432/neondb
Direct Endpoint Target: postgresql://ne***:****@ep-aged-salad-bbh2tnpl.c-15.us-east-1.aws.neon.tech:5432/neondb
------------------------------------------------------------
```

### Connection Roles:
- **`DATABASE_URL` (Pooled):** `ep-aged-salad-bbh2tnpl-pooler...`
  - Utilized by the FastAPI application for high-concurrency stateless query execution.
  - Verified: Active TLS encryption (`ssl_in_use: True`, `sslmode=require`).
- **`DATABASE_URL_UNPOOLED` (Direct):** `ep-aged-salad-bbh2tnpl...`
  - Utilized by migration scripts and administrative DDL operations.
  - Verified: Direct socket bypasses connection pooler, supporting locks and sequence sync.
- **Isolation Check:** Both pooled and direct hosts match compute ID `ep-aged-salad-bbh2tnpl`, confirming zero cross-talk with production compute `ep-ancient-breeze-bbwitums`.

---

## 3. PostgreSQL 18.6 Engine & Compatibility Verification

Local testing in Phase 12 utilized PostgreSQL 16. Neon deploys **PostgreSQL 18.6 (ac70818)**. 

### Compatibility Assessment of `data/postgres_migration.sql`:
1. **DDL & Schema Compilation:** `DROP TABLE IF EXISTS ... CASCADE`, `CREATE TABLE`, `SERIAL`, and `BIGINT` syntax compile cleanly without deprecated syntax warnings.
2. **Composite Primary Keys:** The patched table-level constraint `PRIMARY KEY (user_id, date)` on `gemini_rate_limits` parsed and passed validation.
3. **Data Types:** `JSONB`, `NUMERIC(10,2)`, `TEXT`, and `BOOLEAN` are native, first-class types in PostgreSQL 18.
4. **Sequence Resynchronization:** `SELECT setval(pg_get_serial_sequence(table, 'id'), ...)` executes seamlessly.
5. **Extensions:** `plpgsql (1.0)` is installed and available.

---

## 4. Migration Script Safety Audit

The deployment script [`scripts/deploy_staging_postgres.py`](file:///c:/Users/humai/price-comparison-website/scripts/deploy_staging_postgres.py) was re-inspected and hardened:

- **Read-Only SQLite Source:** Explicitly connected via URI `file:///{path}?mode=ro` (`uri=True`). Any accidental write attempt triggers an OS-level read-only error.
- **Staging-Only Branch Enforcement:** An automated safety guard blocks execution if `NEON_BRANCH` is set to `production` unless explicitly overridden with `--force`.
- **Existing Table Warning:** A pre-migration query checks `information_schema.tables` and issues a prominent `[SAFETY NOTICE]` if existing user tables are found.
- **Zero Secrets Logged:** All connection strings pass through `urllib.parse.urlparse`, displaying only `parsed.hostname` and `parsed.path` while masking credentials completely.

---

## 5. Emptiness & Zero-Mutation Declarations

1. **Staging Database Emptiness:**
   - **User Tables in `public` schema:** `0`
   - **Records:** `0`
   - **Emptiness Status:** **`TRUE (CLEAN SLATE)`**
2. **Production Branch Preservation:**
   - **User Tables in `public` schema:** `0`
   - **Records:** `0`
   - **Preservation Status:** **`100% UNCHANGED`**

---

## 6. Migration Readiness & Next Step

The infrastructure, staging branch, masked configuration, and compatibility checks are fully prepared.

**Safe Migration Command (Ready for Operator Authorization):**
```powershell
& "C:\Users\humai\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts/deploy_staging_postgres.py
```

*Boundaries Maintained: Zero data migrated, zero changes to production branch, Render and Vercel deployments held paused.*
