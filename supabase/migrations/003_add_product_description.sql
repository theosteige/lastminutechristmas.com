-- ============================================================================
-- Migration: Add product_description column
-- Description: Adds a column for the original Amazon listing description
-- ============================================================================

-- Add the product_description column (the actual Amazon listing description)
ALTER TABLE products ADD COLUMN IF NOT EXISTS product_description TEXT;
