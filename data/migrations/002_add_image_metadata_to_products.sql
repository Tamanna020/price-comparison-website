-- ==============================================================================
-- PriceWise AI — Migration 002: Add Image Provenance and Verification Metadata
-- Phase 14 Stage 3: Product Image Recovery
-- ==============================================================================

-- 1. Add additive image provenance columns to products table
-- Works on both PostgreSQL (IF NOT EXISTS) and SQLite (handled via migrate_db)
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_source_url TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_source_name TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_status TEXT DEFAULT 'placeholder';
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_last_checked TIMESTAMP;
