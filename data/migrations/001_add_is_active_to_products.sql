-- ==============================================================================
-- PriceWise AI — Migration 001: Soft-Archive Non-Beauty Products
-- Phase 14 Stage 2: Database & Product Catalogue Recovery
-- ==============================================================================

-- 1. Add is_active column to products if not exists
-- Works on both PostgreSQL (IF NOT EXISTS) and SQLite (handled via migrate_db)
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 2. Soft-archive legacy technology demo products (IDs 1-11)
-- Preserves all foreign keys (offers, price history, watchlists, etc.) without deletion
UPDATE products SET is_active = FALSE WHERE id <= 11;

-- 3. Soft-archive test fixtures if present in catalog (IDs 998, 999)
UPDATE products SET is_active = FALSE WHERE id IN (998, 999);

-- 4. Ensure all genuine beauty products (IDs 12-32 and 1000+) are active
UPDATE products SET is_active = TRUE WHERE id >= 12 AND id NOT IN (998, 999);
