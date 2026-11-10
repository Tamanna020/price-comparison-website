-- ==============================================================================
-- PriceWise AI — Rollback 002: Reset Image Metadata Columns
-- Phase 14 Stage 3 Rollback Plan
-- ==============================================================================

-- Reset image metadata to default state if needed
UPDATE products SET 
    image_source_url = NULL,
    image_source_name = NULL,
    image_status = 'placeholder',
    image_last_checked = NULL;
