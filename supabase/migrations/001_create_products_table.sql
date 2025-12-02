-- ============================================================================
-- Migration: Create Products Table for Gift Recommendations
-- Description: Sets up the products table with vector embeddings for semantic
--              search and all necessary fields for gift filtering.
-- ============================================================================

-- Enable the pgvector extension (required for embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- PRODUCTS TABLE
-- ============================================================================
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- ═══════════════════════════════════════════════════════════════════════════
  -- BASIC INFO (required when adding a product)
  -- ═══════════════════════════════════════════════════════════════════════════
  name TEXT NOT NULL,
  amazon_url TEXT NOT NULL,
  price DECIMAL(10, 2) NOT NULL,

  -- ═══════════════════════════════════════════════════════════════════════════
  -- FILTERING ATTRIBUTES (required for recommendations)
  -- ═══════════════════════════════════════════════════════════════════════════
  min_age INT NOT NULL DEFAULT 0,
  max_age INT NOT NULL DEFAULT 99,
  gender TEXT NOT NULL DEFAULT 'unisex' CHECK (gender IN ('male', 'female', 'unisex')),
  category TEXT NOT NULL,

  -- ═══════════════════════════════════════════════════════════════════════════
  -- DELIVERY FILTERING
  -- ═══════════════════════════════════════════════════════════════════════════
  prime_eligible BOOLEAN NOT NULL DEFAULT false,

  -- ═══════════════════════════════════════════════════════════════════════════
  -- PRODUCT INFO
  -- ═══════════════════════════════════════════════════════════════════════════
  product_description TEXT,                 -- The actual Amazon listing description

  -- ═══════════════════════════════════════════════════════════════════════════
  -- SEMANTIC SEARCH (for blurb matching)
  -- ═══════════════════════════════════════════════════════════════════════════
  description TEXT NOT NULL,                -- AI-generated semantic description for matching
  tags TEXT[] DEFAULT '{}',                 -- Fallback keywords: ['tech lover', 'outdoorsy']
  embedding VECTOR(1536),                   -- OpenAI text-embedding-3-small dimension

  -- ═══════════════════════════════════════════════════════════════════════════
  -- OPTIONAL METADATA
  -- ═══════════════════════════════════════════════════════════════════════════
  image_url TEXT,
  amazon_asin TEXT,                         -- Extracted from URL for tracking

  -- ═══════════════════════════════════════════════════════════════════════════
  -- HOUSEKEEPING
  -- ═══════════════════════════════════════════════════════════════════════════
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Standard filtering indexes
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_age ON products(min_age, max_age);
CREATE INDEX idx_products_gender ON products(gender);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_prime ON products(prime_eligible);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_tags ON products USING GIN(tags);

-- Vector similarity search index (HNSW is faster for queries than IVFFlat)
-- Note: This index is created on the embedding column for cosine similarity
CREATE INDEX idx_products_embedding ON products
  USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function on every update
CREATE TRIGGER trigger_products_updated_at
  BEFORE UPDATE ON products
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER FUNCTION: Search products by similarity
-- ============================================================================

-- Function to search products with combined filtering and semantic search
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

-- ============================================================================
-- ROW LEVEL SECURITY (optional - enable if needed)
-- ============================================================================

-- Uncomment these lines if you want to enable RLS
-- ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Example policy: Allow public read access to active products
-- CREATE POLICY "Public can view active products" ON products
--   FOR SELECT USING (is_active = true);

-- Example policy: Only authenticated users can insert/update
-- CREATE POLICY "Authenticated users can manage products" ON products
--   FOR ALL USING (auth.role() = 'authenticated');
