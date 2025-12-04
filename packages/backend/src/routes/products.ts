import { Router, Request, Response } from 'express';
import { BrowseRequestSchema, BrowseResponse } from '../types/index.js';
import { browseProducts } from '../services/supabase.js';

const router = Router();

/**
 * GET /api/products
 * Browse products with optional filters (no semantic search)
 *
 * Query parameters:
 *   - age: number (filter by age range)
 *   - gender: 'male' | 'female' | 'any'
 *   - minPrice: number
 *   - maxPrice: number
 *   - primeOnly: boolean
 *   - category: string
 *   - limit: number (default: 20, max: 100)
 *   - offset: number (default: 0)
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    // Parse query parameters
    const params = {
      age: req.query.age ? parseInt(req.query.age as string) : undefined,
      gender: req.query.gender as 'male' | 'female' | 'any' | undefined,
      minPrice: req.query.minPrice ? parseFloat(req.query.minPrice as string) : undefined,
      maxPrice: req.query.maxPrice ? parseFloat(req.query.maxPrice as string) : undefined,
      primeOnly: req.query.primeOnly === 'true',
      category: req.query.category as string | undefined,
      limit: req.query.limit ? parseInt(req.query.limit as string) : undefined,
      offset: req.query.offset ? parseInt(req.query.offset as string) : undefined,
    };

    // Validate
    const parseResult = BrowseRequestSchema.safeParse(params);
    if (!parseResult.success) {
      res.status(400).json({
        error: 'Invalid request',
        details: parseResult.error.errors,
      });
      return;
    }

    const { products, total } = await browseProducts(parseResult.data);

    res.json({
      products,
      total,
      limit: parseResult.data.limit,
      offset: parseResult.data.offset,
    });
  } catch (error) {
    console.error('Browse error:', error);
    res.status(500).json({
      error: 'Failed to browse products',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

export default router;
