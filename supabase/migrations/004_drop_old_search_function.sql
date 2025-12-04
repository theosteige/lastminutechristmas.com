-- ============================================================================
-- Migration: Drop old search_products function overload
-- Description: Removes the old function signature that included max_delivery_days
--              This fixes the "Could not choose the best candidate function" error
-- ============================================================================

-- Drop the old function with max_delivery_days parameter
DROP FUNCTION IF EXISTS search_products(
  VECTOR(1536),  -- query_embedding
  INT,           -- target_age
  TEXT,          -- target_gender
  DECIMAL,       -- min_price
  DECIMAL,       -- max_price
  INT,           -- max_delivery_days (old parameter)
  BOOLEAN,       -- require_prime
  INT            -- result_limit
);
