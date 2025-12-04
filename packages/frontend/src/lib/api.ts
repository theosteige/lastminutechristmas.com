const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

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

export interface RecommendRequest {
  age: number;
  gender: 'male' | 'female' | 'any';
  minPrice?: number;
  maxPrice?: number;
  primeOnly?: boolean;
  blurb: string;
}

export interface RefineRequest {
  age: number;
  gender: 'male' | 'female' | 'any';
  minPrice?: number;
  maxPrice?: number;
  primeOnly?: boolean;
  blurbs: string[];
  excludeIds?: string[];
}

export interface RecommendResponse {
  products: Product[];
}

export async function getRecommendations(request: RecommendRequest): Promise<RecommendResponse> {
  const response = await fetch(`${API_URL}/api/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to get recommendations');
  }

  return response.json();
}

export async function refineRecommendations(request: RefineRequest): Promise<RecommendResponse> {
  const response = await fetch(`${API_URL}/api/recommend/refine`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to refine recommendations');
  }

  return response.json();
}
