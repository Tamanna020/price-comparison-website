-- ==============================================================================
-- PriceWise AI — Rollback 001: Restore Non-Beauty Products to Active
-- Phase 14 Stage 2 Rollback Plan
-- ==============================================================================

-- Re-activate all products including legacy demo products if needed
UPDATE products SET is_active = TRUE;
