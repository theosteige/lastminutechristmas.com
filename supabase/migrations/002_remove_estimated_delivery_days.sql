-- ============================================================================
-- Migration: Remove estimated_delivery_days column
-- Description: Removes the estimated_delivery_days column from products table
-- ============================================================================

-- Drop the index first
DROP INDEX IF EXISTS idx_products_delivery;

-- Remove the column
ALTER TABLE products DROP COLUMN IF EXISTS estimated_delivery_days;

-- Update the search_products function to remove the parameter
CREATE OR REPLACE FUNCTION search_products(
  query_embedding VECTOR(1536),
  target_age INT DEFAULT NULL,
  target_gender TEXT DEFAULT NULL,
  min_price DECIMAL DEFAULT NULL,
  max_price DECIMAL DEFAULT NULL,
  require_prime BOOLEAN DEFAULT FALSE,
  result_limit INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  name TEXT,
  amazon_url TEXT,
  price DECIMAL,
  description TEXT,
  category TEXT,
  image_url TEXT,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.name,
    p.amazon_url,
    p.price,
    p.description,
    p.category,
    p.image_url,
    1 - (p.embedding <=> query_embedding) AS similarity
  FROM products p
  WHERE p.is_active = true
    AND (target_age IS NULL OR (p.min_age <= target_age AND p.max_age >= target_age))
    AND (target_gender IS NULL OR p.gender IN (target_gender, 'unisex'))
    AND (min_price IS NULL OR p.price >= min_price)
    AND (max_price IS NULL OR p.price <= max_price)
    AND (require_prime = FALSE OR p.prime_eligible = TRUE)
    AND p.embedding IS NOT NULL
  ORDER BY p.embedding <=> query_embedding
  LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;
