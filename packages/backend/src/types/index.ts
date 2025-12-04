import { z } from 'zod';

// Request validation schemas
export const RecommendRequestSchema = z.object({
  age: z.number().int().min(0).max(120),
  gender: z.enum(['male', 'female', 'any']),
  minPrice: z.number().min(0).optional(),
  maxPrice: z.number().min(0).optional(),
  primeOnly: z.boolean().optional().default(false),
  blurb: z.string().min(1).max(2000),
});

export const RefineRequestSchema = z.object({
  age: z.number().int().min(0).max(120),
  gender: z.enum(['male', 'female', 'any']),
  minPrice: z.number().min(0).optional(),
  maxPrice: z.number().min(0).optional(),
  primeOnly: z.boolean().optional().default(false),
  blurbs: z.array(z.string().min(1).max(2000)).min(1).max(10),
  excludeIds: z.array(z.string().uuid()).optional(),
});

export const BrowseRequestSchema = z.object({
  age: z.number().int().min(0).max(120).optional(),
  gender: z.enum(['male', 'female', 'any']).optional(),
  minPrice: z.number().min(0).optional(),
  maxPrice: z.number().min(0).optional(),
  primeOnly: z.boolean().optional().default(false),
  category: z.string().optional(),
  limit: z.number().int().min(1).max(100).optional().default(20),
  offset: z.number().int().min(0).optional().default(0),
});

export type RecommendRequest = z.infer<typeof RecommendRequestSchema>;
export type RefineRequest = z.infer<typeof RefineRequestSchema>;
export type BrowseRequest = z.infer<typeof BrowseRequestSchema>;

// Product types
export interface Product {
  id: string;
  name: string;
  amazonUrl: string;
  price: number;
  description: string;
  category: string;
  imageUrl: string | null;
  similarity: number;
}

export interface BrowseProduct {
  id: string;
  name: string;
  amazonUrl: string;
  price: number;
  description: string;
  category: string;
  imageUrl: string | null;
  primeEligible: boolean;
  minAge: number;
  maxAge: number;
  gender: string;
}

export interface RecommendResponse {
  products: Product[];
}

export interface BrowseResponse {
  products: BrowseProduct[];
  total: number;
  limit: number;
  offset: number;
}
