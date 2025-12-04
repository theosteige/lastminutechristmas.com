'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Sparkles, X } from 'lucide-react';

interface RefineFormProps {
  previousBlurbs: string[];
  onRefine: (newBlurb: string) => void;
  onReset: () => void;
  isLoading: boolean;
}

export function RefineForm({ previousBlurbs, onRefine, onReset, isLoading }: RefineFormProps) {
  const [newBlurb, setNewBlurb] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newBlurb.trim()) {
      onRefine(newBlurb.trim());
      setNewBlurb('');
    }
  };

  return (
    <Card className="w-full max-w-xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            Refine Recommendations
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onReset}>
            <X className="h-4 w-4 mr-1" />
            Start Over
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm text-gray-600">
            Previous descriptions ({previousBlurbs.length}):
          </p>
          <div className="space-y-1">
            {previousBlurbs.map((blurb, i) => (
              <div key={i} className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                {blurb.length > 100 ? `${blurb.slice(0, 100)}...` : blurb}
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <Textarea
            placeholder="Add more details to improve recommendations... (e.g., They also love cooking and recently got into yoga)"
            value={newBlurb}
            onChange={(e) => setNewBlurb(e.target.value)}
            rows={3}
            className="resize-none"
          />
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !newBlurb.trim()}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Updating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Update Recommendations
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
