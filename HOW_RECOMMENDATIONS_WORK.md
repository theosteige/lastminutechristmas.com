# How Gift Recommendations Work

This document explains the complete recommendation pipeline from user input to ranked gift suggestions.

---

## Overview

The recommendation system uses **semantic search** powered by OpenAI embeddings and PostgreSQL vector similarity. Instead of matching keywords, it understands the *meaning* behind descriptions to find gifts that match a person's interests and personality.

```
User Input → Embedding → Vector Search → Ranked Results
```

---

## Step-by-Step Breakdown

### 1. User Submits a Request

The user provides:

| Field | Example | Purpose |
|-------|---------|---------|
| Age | `35` | Filter products by appropriate age range |
| Gender | `male` | Filter to male/unisex products |
| Price Range | `$20 - $100` | Filter by budget |
| Prime Only | `false` | Optionally require fast shipping |
| Blurb | `"My dad loves woodworking and craft beer. He spends weekends in his garage building furniture."` | **The key input** - used for semantic matching |

### 2. Generate an Embedding

The backend sends the blurb to OpenAI's embedding API:

```typescript
// packages/backend/src/services/embedding.ts

const response = await openai.embeddings.create({
  model: 'text-embedding-3-small',
  input: "My dad loves woodworking and craft beer..."
});

// Returns a 1536-dimensional vector like:
// [0.023, -0.041, 0.018, 0.099, -0.033, ...]
```

**What is an embedding?**

An embedding is a list of 1,536 numbers that represents the *semantic meaning* of text. Similar concepts have similar vectors:

- "woodworking tools" → `[0.12, -0.08, 0.23, ...]`
- "carpentry equipment" → `[0.11, -0.09, 0.22, ...]` (very similar!)
- "video games" → `[-0.45, 0.67, -0.12, ...]` (very different)

### 3. Search the Database

The embedding is sent to Supabase, which runs a vector similarity search:

```sql
-- supabase/migrations/001_create_products_table.sql

SELECT
  id, name, amazon_url, price, description, category, image_url,
  1 - (embedding <=> query_embedding) AS similarity
FROM products
WHERE
  is_active = true
  AND (min_age <= 35 AND max_age >= 35)      -- Age filter
  AND gender IN ('male', 'unisex')            -- Gender filter
  AND price >= 20 AND price <= 100            -- Price filter
  AND embedding IS NOT NULL
ORDER BY embedding <=> query_embedding        -- Sort by similarity
LIMIT 10;
```

**The `<=>` Operator**

This is PostgreSQL's cosine distance operator (from pgvector). It measures how "far apart" two vectors are:

- `0.0` = identical (perfect match)
- `1.0` = completely opposite
- `2.0` = maximally different

We convert distance to similarity: `similarity = 1 - distance`

### 4. Return Ranked Products

Products are returned sorted by similarity score:

```json
{
  "products": [
    {
      "id": "abc-123",
      "name": "Professional Woodworking Chisel Set",
      "price": 67.99,
      "similarity": 0.89,  // 89% match
      "category": "tools",
      "amazonUrl": "https://amazon.com/dp/..."
    },
    {
      "id": "def-456",
      "name": "Craft Beer Brewing Kit",
      "price": 54.99,
      "similarity": 0.84,  // 84% match
      "category": "kitchen",
      "amazonUrl": "https://amazon.com/dp/..."
    }
  ]
}
```

---

## How Products Get Their Embeddings

When products are added via the data pipeline (`scripts/pipeline.py`):

### 1. Scrape Amazon
```
URL → Product name, price, description, image
```

### 2. Enrich with AI
ChatGPT generates metadata based on the product:
```json
{
  "min_age": 25,
  "max_age": 65,
  "gender": "male",
  "category": "tools",
  "description": "Perfect for DIY enthusiasts and woodworking hobbyists who love creating things with their hands...",
  "tags": ["woodworking", "DIY", "craftsman", "tools"]
}
```

### 3. Generate Product Embedding
The AI-generated description + tags are embedded:
```typescript
const embeddingText = [
  product.description,
  `Category: ${product.category}`,
  `Good for ages ${product.min_age} to ${product.max_age}`,
  `Keywords: ${product.tags.join(', ')}`
].join('. ');

const embedding = await generateEmbedding(embeddingText);
```

### 4. Store in Database
```sql
INSERT INTO products (name, embedding, ...)
VALUES ('Woodworking Chisel Set', '[0.023, -0.041, ...]', ...);
```

---

## The Refine Feature

When users add more context, we **average multiple embeddings**:

### Initial Search
```
Blurb 1: "My dad loves woodworking"
         ↓
    Embedding A: [0.12, -0.08, 0.23, ...]
```

### Refined Search
```
Blurb 1: "My dad loves woodworking"     → Embedding A
Blurb 2: "He also enjoys craft beer"    → Embedding B

Combined = (A + B) / 2 = [0.09, -0.02, 0.18, ...]
```

This averaged vector captures *both* interests, finding products that match the complete picture rather than just one aspect.

```typescript
// packages/backend/src/services/embedding.ts

export async function generateAveragedEmbedding(texts: string[]): Promise<number[]> {
  const embeddings = await Promise.all(texts.map(generateEmbedding));

  // Average each dimension across all embeddings
  const averaged = new Array(1536).fill(0);
  for (const embedding of embeddings) {
    for (let i = 0; i < 1536; i++) {
      averaged[i] += embedding[i];
    }
  }
  for (let i = 0; i < 1536; i++) {
    averaged[i] /= embeddings.length;
  }

  return averaged;
}
```

---

## Why This Works

### Traditional Search (Keywords)
```
Query: "dad woodworking"
Match: Products containing "dad" OR "woodworking"
Problem: Misses "carpentry tools", "DIY kits", "workshop equipment"
```

### Semantic Search (Embeddings)
```
Query: "dad woodworking"
Embedding: [0.12, -0.08, 0.23, ...]
Match: Products with similar embeddings
Finds: "Carpentry chisel set", "Workshop organizer", "DIY workbench plans"
```

The embedding model understands that:
- "woodworking" ≈ "carpentry" ≈ "DIY" ≈ "craftsman"
- "dad" implies adult male, practical gifts
- Context matters: "loves woodworking" suggests hobby-level, not professional

---

## Database Schema

```sql
CREATE TABLE products (
  id UUID PRIMARY KEY,

  -- Basic info
  name TEXT NOT NULL,
  amazon_url TEXT NOT NULL,
  price DECIMAL(10, 2) NOT NULL,

  -- Filtering attributes
  min_age INT DEFAULT 0,
  max_age INT DEFAULT 99,
  gender TEXT CHECK (gender IN ('male', 'female', 'unisex')),
  category TEXT NOT NULL,
  prime_eligible BOOLEAN DEFAULT false,

  -- Semantic search
  description TEXT NOT NULL,           -- AI-generated, used for embedding
  tags TEXT[] DEFAULT '{}',            -- Keywords for embedding
  embedding VECTOR(1536),              -- The actual vector

  -- Display
  image_url TEXT,
  product_description TEXT             -- Original Amazon description
);

-- Vector similarity index (HNSW algorithm)
CREATE INDEX idx_products_embedding ON products
  USING hnsw (embedding vector_cosine_ops);
```

---

## Performance

| Component | Time |
|-----------|------|
| Generate embedding (OpenAI API) | ~200-400ms |
| Vector search (Supabase) | ~10-50ms |
| Total request | ~300-500ms |

The HNSW index makes vector search extremely fast even with thousands of products.

---

## Summary

1. **User describes recipient** → natural language blurb
2. **Blurb → Embedding** → 1536-dimensional vector via OpenAI
3. **Vector search** → find products with similar embeddings
4. **Filter & rank** → apply age/gender/price filters, sort by similarity
5. **Refine** → average multiple blurbs for better matching

The magic is in the embeddings: they capture *meaning*, not just words, enabling the system to understand that someone who "loves tinkering in the garage" would appreciate the same gifts as someone who "enjoys DIY woodworking projects."
