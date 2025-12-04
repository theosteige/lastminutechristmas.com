import { Router, Request, Response } from 'express';
import { RecommendRequestSchema, RefineRequestSchema } from '../types/index.js';
import { generateEmbedding, generateAveragedEmbedding } from '../services/embedding.js';
import { searchProducts } from '../services/supabase.js';

const router = Router();

/**
 * POST /api/recommend
 * Get gift recommendations based on recipient info and a blurb
 */
router.post('/', async (req: Request, res: Response) => {
  try {
    // Validate request body
    const parseResult = RecommendRequestSchema.safeParse(req.body);
    if (!parseResult.success) {
      res.status(400).json({
        error: 'Invalid request',
        details: parseResult.error.errors,
      });
      return;
    }

    const { age, gender, minPrice, maxPrice, primeOnly, blurb } = parseResult.data;

    // Generate embedding from blurb
    const embedding = await generateEmbedding(blurb);

    // Search for products
    const products = await searchProducts({
      embedding,
      age,
      gender,
      minPrice,
      maxPrice,
      primeOnly,
    });

    res.json({ products });
  } catch (error) {
    console.error('Recommend error:', error);
    res.status(500).json({
      error: 'Failed to get recommendations',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * POST /api/recommend/refine
 * Refine recommendations with multiple blurbs
 */
router.post('/refine', async (req: Request, res: Response) => {
  try {
    // Validate request body
    const parseResult = RefineRequestSchema.safeParse(req.body);
    if (!parseResult.success) {
      res.status(400).json({
        error: 'Invalid request',
        details: parseResult.error.errors,
      });
      return;
    }

    const { age, gender, minPrice, maxPrice, primeOnly, blurbs, excludeIds } = parseResult.data;

    // Generate averaged embedding from all blurbs
    const embedding = await generateAveragedEmbedding(blurbs);

    // Search for products
    const products = await searchProducts({
      embedding,
      age,
      gender,
      minPrice,
      maxPrice,
      primeOnly,
      excludeIds,
    });

    res.json({ products });
  } catch (error) {
    console.error('Refine error:', error);
    res.status(500).json({
      error: 'Failed to refine recommendations',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

export default router;
