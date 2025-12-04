'use client';

import { useState } from 'react';
import { RecommendForm, FormData } from '@/components/RecommendForm';
import { RefineForm } from '@/components/RefineForm';
import { ProductCard } from '@/components/ProductCard';
import { getRecommendations, refineRecommendations, Product } from '@/lib/api';
import { TreePine, Snowflake } from 'lucide-react';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [blurbs, setBlurbs] = useState<string[]>([]);
  const [formData, setFormData] = useState<FormData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: FormData) => {
    setIsLoading(true);
    setError(null);
    setFormData(data);

    try {
      const response = await getRecommendations({
        age: data.age,
        gender: data.gender,
        minPrice: data.minPrice,
        maxPrice: data.maxPrice,
        primeOnly: data.primeOnly,
        blurb: data.blurb,
      });
      setProducts(response.products);
      setBlurbs([data.blurb]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setProducts([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefine = async (newBlurb: string) => {
    if (!formData) return;

    setIsLoading(true);
    setError(null);

    const updatedBlurbs = [...blurbs, newBlurb];

    try {
      const response = await refineRecommendations({
        age: formData.age,
        gender: formData.gender,
        minPrice: formData.minPrice,
        maxPrice: formData.maxPrice,
        primeOnly: formData.primeOnly,
        blurbs: updatedBlurbs,
      });
      setProducts(response.products);
      setBlurbs(updatedBlurbs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setProducts([]);
    setBlurbs([]);
    setFormData(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-red-50 to-green-50">
      <header className="py-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <TreePine className="h-8 w-8 text-green-600" />
          <h1 className="text-4xl font-bold text-gray-900">
            Last Minute Christmas
          </h1>
          <Snowflake className="h-8 w-8 text-blue-400" />
        </div>
        <p className="text-gray-600">
          AI-powered gift recommendations for everyone on your list
        </p>
      </header>

      <main className="container mx-auto px-4 pb-16">
        {products.length === 0 ? (
          <RecommendForm onSubmit={handleSubmit} isLoading={isLoading} />
        ) : (
          <div className="space-y-8">
            <RefineForm
              previousBlurbs={blurbs}
              onRefine={handleRefine}
              onReset={handleReset}
              isLoading={isLoading}
            />

            {error && (
              <div className="max-w-xl mx-auto p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-center">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>

            {products.length === 0 && !isLoading && (
              <div className="text-center text-gray-500 py-8">
                No products found matching your criteria. Try adjusting the filters.
              </div>
            )}
          </div>
        )}

        {error && products.length === 0 && (
          <div className="max-w-xl mx-auto mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-center">
            {error}
          </div>
        )}
      </main>

      <footer className="py-6 text-center text-gray-500 text-sm">
        <p>Made with ❤️ for last-minute gift givers everywhere</p>
      </footer>
    </div>
  );
}
