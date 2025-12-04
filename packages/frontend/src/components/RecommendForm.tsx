'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Gift, Loader2 } from 'lucide-react';

export interface FormData {
  age: number;
  gender: 'male' | 'female' | 'any';
  minPrice: number;
  maxPrice: number;
  primeOnly: boolean;
  blurb: string;
}

interface RecommendFormProps {
  onSubmit: (data: FormData) => void;
  isLoading: boolean;
}

export function RecommendForm({ onSubmit, isLoading }: RecommendFormProps) {
  const [age, setAge] = useState(30);
  const [gender, setGender] = useState<'male' | 'female' | 'any'>('any');
  const [priceRange, setPriceRange] = useState([0, 200]);
  const [primeOnly, setPrimeOnly] = useState(false);
  const [blurb, setBlurb] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      age,
      gender,
      minPrice: priceRange[0],
      maxPrice: priceRange[1],
      primeOnly,
      blurb,
    });
  };

  return (
    <Card className="w-full max-w-xl mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="flex items-center justify-center gap-2 text-2xl">
          <Gift className="h-6 w-6 text-red-600" />
          Find the Perfect Gift
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="age">Recipient&apos;s Age</Label>
              <Input
                id="age"
                type="number"
                min={0}
                max={120}
                value={age}
                onChange={(e) => setAge(parseInt(e.target.value) || 0)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="gender">Gender</Label>
              <Select value={gender} onValueChange={(v) => setGender(v as typeof gender)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Any</SelectItem>
                  <SelectItem value="male">Male</SelectItem>
                  <SelectItem value="female">Female</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-3">
            <Label>
              Price Range: ${priceRange[0]} - ${priceRange[1]}
              {priceRange[1] >= 500 && '+'}
            </Label>
            <Slider
              value={priceRange}
              onValueChange={setPriceRange}
              min={0}
              max={500}
              step={10}
              className="w-full"
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="prime"
              checked={primeOnly}
              onChange={(e) => setPrimeOnly(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="prime" className="text-sm font-normal">
              Only show Prime-eligible items (faster delivery)
            </Label>
          </div>

          <div className="space-y-2">
            <Label htmlFor="blurb">Tell us about the recipient</Label>
            <Textarea
              id="blurb"
              placeholder="e.g., My dad loves woodworking, craft beer, and watching football. He's always tinkering with stuff in his garage..."
              value={blurb}
              onChange={(e) => setBlurb(e.target.value)}
              rows={4}
              className="resize-none"
            />
            <p className="text-xs text-gray-500">
              The more details you provide, the better the recommendations!
            </p>
          </div>

          <Button
            type="submit"
            className="w-full bg-red-600 hover:bg-red-700"
            disabled={isLoading || !blurb.trim()}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Finding gifts...
              </>
            ) : (
              <>
                <Gift className="mr-2 h-4 w-4" />
                Get Recommendations
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
