'use client';

import Image from 'next/image';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ExternalLink } from 'lucide-react';
import type { Product } from '@/lib/api';

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const matchPercentage = Math.round(product.similarity * 100);

  return (
    <Card className="flex flex-col overflow-hidden">
      <div className="relative aspect-square bg-gray-100">
        {product.imageUrl ? (
          <Image
            src={product.imageUrl}
            alt={product.name}
            fill
            className="object-contain p-4"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            No image
          </div>
        )}
        <div className="absolute top-2 right-2 bg-green-600 text-white text-xs font-bold px-2 py-1 rounded">
          {matchPercentage}% match
        </div>
      </div>

      <CardContent className="flex-1 p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
          {product.category}
        </div>
        <h3 className="font-semibold text-sm line-clamp-2 mb-2">
          {product.name}
        </h3>
        <p className="text-xs text-gray-600 line-clamp-3">
          {product.description}
        </p>
      </CardContent>

      <CardFooter className="p-4 pt-0 flex items-center justify-between">
        <span className="text-lg font-bold text-green-700">
          ${product.price.toFixed(2)}
        </span>
        <Button asChild size="sm">
          <a
            href={product.amazonUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1"
          >
            Buy on Amazon
            <ExternalLink className="h-3 w-3" />
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
}
