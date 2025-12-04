import { createClient, SupabaseClient } from '@supabase/supabase-js';
import type { Product, BrowseProduct } from '../types/index.js';

let supabase: SupabaseClient | null = null;

function getSupabaseClient(): SupabaseClient {
  if (!supabase) {
    const supabaseUrl = process.env.SUPABASE_URL!;
    const supabaseKey = process.env.SUPABASE_SERVICE_KEY!;
    supabase = createClient(supabaseUrl, supabaseKey);
  }
  return supabase;
}

interface SearchParams {
  embedding: number[];
  age?: number;
  gender?: 'male' | 'female' | 'any';
  minPrice?: number;
  maxPrice?: number;
  primeOnly?: boolean;
  limit?: number;
  excludeIds?: string[];
}

/**
 * Search products using the search_products RPC function
 */
export async function searchProducts(params: SearchParams): Promise<Product[]> {
  const {
    embedding,
    age,
    gender,
    minPrice,
    maxPrice,
    primeOnly = false,
    limit = 10,
    excludeIds = [],
  } = params;

  // Map 'any' to null for the database query (matches all genders)
  const targetGender = gender === 'any' ? null : gender;

  const { data, error } = await getSupabaseClient().rpc('search_products', {
    query_embedding: embedding,
    target_age: age ?? null,
    target_gender: targetGender,
    min_price: minPrice ?? null,
    max_price: maxPrice ?? null,
    require_prime: primeOnly,
    result_limit: limit + excludeIds.length, // Fetch extra to account for exclusions
  });

  if (error) {
    console.error('Supabase search error:', error);
    throw new Error(`Search failed: ${error.message}`);
  }

  // Filter out excluded IDs and map to Product type
  const products: Product[] = (data || [])
    .filter((row: any) => !excludeIds.includes(row.id))
    .slice(0, limit)
    .map((row: any) => ({
      id: row.id,
      name: row.name,
      amazonUrl: row.amazon_url,
      price: parseFloat(row.price),
      description: row.description,
      category: row.category,
      imageUrl: row.image_url,
      similarity: row.similarity,
    }));

  return products;
}

interface BrowseParams {
  age?: number;
  gender?: 'male' | 'female' | 'any';
  minPrice?: number;
  maxPrice?: number;
  primeOnly?: boolean;
  category?: string;
  limit?: number;
  offset?: number;
}

/**
 * Browse products with filters (no embedding/semantic search)
 */
export async function browseProducts(params: BrowseParams): Promise<{ products: BrowseProduct[]; total: number }> {
  const {
    age,
    gender,
    minPrice,
    maxPrice,
    primeOnly = false,
    category,
    limit = 20,
    offset = 0,
  } = params;

  let query = getSupabaseClient()
    .from('products')
    .select('*', { count: 'exact' })
    .eq('is_active', true);

  // Apply filters
  if (age !== undefined) {
    query = query.lte('min_age', age).gte('max_age', age);
  }

  if (gender && gender !== 'any') {
    query = query.or(`gender.eq.${gender},gender.eq.unisex`);
  }

  if (minPrice !== undefined) {
    query = query.gte('price', minPrice);
  }

  if (maxPrice !== undefined) {
    query = query.lte('price', maxPrice);
  }

  if (primeOnly) {
    query = query.eq('prime_eligible', true);
  }

  if (category) {
    query = query.eq('category', category);
  }

  // Apply pagination and ordering
  query = query
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1);

  const { data, error, count } = await query;

  if (error) {
    console.error('Supabase browse error:', error);
    throw new Error(`Browse failed: ${error.message}`);
  }

  const products: BrowseProduct[] = (data || []).map((row: any) => ({
    id: row.id,
    name: row.name,
    amazonUrl: row.amazon_url,
    price: parseFloat(row.price),
    description: row.description,
    category: row.category,
    imageUrl: row.image_url,
    primeEligible: row.prime_eligible,
    minAge: row.min_age,
    maxAge: row.max_age,
    gender: row.gender,
  }));

  return { products, total: count || 0 };
}
