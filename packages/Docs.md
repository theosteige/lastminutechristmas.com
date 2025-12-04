# Last Minute Christmas - Packages

This directory contains the backend and frontend applications for the gift recommendation website.

## Architecture Overview

```
packages/
├── backend/           # Express.js API server
└── frontend/          # Next.js web application
```

The system uses a simple request flow:

1. **User** enters recipient info + description in the frontend
2. **Frontend** sends request to backend API
3. **Backend** generates an embedding using OpenAI
4. **Backend** queries Supabase using vector similarity search
5. **Backend** returns ranked products
6. **Frontend** displays results

---

## Backend (`packages/backend`)

An Express.js API server written in TypeScript that handles gift recommendations.

### Structure

```
backend/
├── src/
│   ├── index.ts              # Express app entry point
│   ├── routes/
│   │   └── recommend.ts      # Recommendation endpoints
│   ├── services/
│   │   ├── embedding.ts      # OpenAI embedding generation
│   │   └── supabase.ts       # Database queries
│   └── types/
│       └── index.ts          # TypeScript types & Zod schemas
├── package.json
└── tsconfig.json
```

### API Endpoints

#### `GET /api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-12-02T12:00:00.000Z"
}
```

#### `POST /api/recommend`

Get gift recommendations based on recipient information and a description.

**Request Body:**
```json
{
  "age": 35,
  "gender": "male",
  "minPrice": 20,
  "maxPrice": 100,
  "primeOnly": false,
  "blurb": "My dad loves woodworking and craft beer. He spends weekends in his garage building furniture."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `age` | number | Yes | Recipient's age (0-120) |
| `gender` | string | Yes | `"male"`, `"female"`, or `"any"` |
| `minPrice` | number | No | Minimum price filter |
| `maxPrice` | number | No | Maximum price filter |
| `primeOnly` | boolean | No | Only show Prime-eligible items |
| `blurb` | string | Yes | Description of the recipient (1-2000 chars) |

**Response:**
```json
{
  "products": [
    {
      "id": "uuid",
      "name": "Product Name",
      "amazonUrl": "https://amazon.com/dp/...",
      "price": 49.99,
      "description": "AI-generated description for matching",
      "category": "tools",
      "imageUrl": "https://...",
      "similarity": 0.87
    }
  ]
}
```

#### `POST /api/recommend/refine`

Refine recommendations by providing additional descriptions. The embeddings from all blurbs are averaged together for better matching.

**Request Body:**
```json
{
  "age": 35,
  "gender": "male",
  "minPrice": 20,
  "maxPrice": 100,
  "primeOnly": false,
  "blurbs": [
    "My dad loves woodworking and craft beer.",
    "He also enjoys watching football and grilling."
  ],
  "excludeIds": ["uuid-1", "uuid-2"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `blurbs` | string[] | Yes | Array of all descriptions (1-10 items) |
| `excludeIds` | string[] | No | Product IDs to exclude from results |

**Response:** Same as `/api/recommend`

### How Embeddings Work

1. The user's blurb is sent to OpenAI's `text-embedding-3-small` model
2. This returns a 1536-dimensional vector representing the semantic meaning
3. For refinement, multiple blurbs are embedded and averaged together
4. The vector is used in Supabase's `search_products` RPC function
5. Products are ranked by cosine similarity to the query vector

### Environment Variables

The backend uses these variables from the root `.env` file:

| Variable | Description |
|----------|-------------|
| `PORT` | Server port (default: 3001) |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `OPENAI_API_KEY` | OpenAI API key for embeddings |

---

## Frontend (`packages/frontend`)

A Next.js 14 application with shadcn/ui components for the user interface.

### Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx        # Root layout
│   │   ├── page.tsx          # Main recommendation page
│   │   └── globals.css       # Global styles
│   ├── components/
│   │   ├── ui/               # shadcn/ui components
│   │   ├── RecommendForm.tsx # Initial search form
│   │   ├── RefineForm.tsx    # Add more blurbs form
│   │   └── ProductCard.tsx   # Product display card
│   └── lib/
│       ├── api.ts            # Backend API client
│       └── utils.ts          # Utility functions
├── package.json
├── tailwind.config.ts
└── next.config.ts
```

### Components

#### `RecommendForm`

The main form for entering recipient information:
- Age input (number)
- Gender select (Male/Female/Any)
- Price range slider ($0-$500)
- Prime-only checkbox
- Blurb textarea for describing the recipient

#### `RefineForm`

Shown after initial results, allows users to:
- See their previous descriptions
- Add additional context to improve recommendations
- Start over with a new search

#### `ProductCard`

Displays a single product with:
- Product image (from Amazon)
- Match percentage badge
- Category label
- Product name and description
- Price
- "Buy on Amazon" button

### User Flow

1. **Landing**: User sees the recommendation form
2. **Input**: User fills in recipient details and description
3. **Loading**: Form shows loading state while API processes
4. **Results**: Grid of product cards sorted by similarity
5. **Refine** (optional): User adds more context to improve results
6. **Purchase**: Clicking a product opens Amazon in new tab

### Environment Variables

Create `.env.local` in the frontend directory:

```
NEXT_PUBLIC_API_URL=http://localhost:3001
```

### Styling

- **Tailwind CSS v4** for utility classes
- **shadcn/ui** for accessible, pre-built components
- **Festive theme**: Red/green gradient background, Christmas icons

---

## Development

### Running Locally

From the project root:

```bash
# Install all dependencies
npm install

# Run both backend and frontend
npm run dev

# Or run individually
npm run dev:backend   # Starts backend on http://localhost:3001
npm run dev:frontend  # Starts frontend on http://localhost:3000
```

### Adding shadcn Components

```bash
cd packages/frontend
npx shadcn@latest add [component-name]
```

### Type Checking

```bash
# Backend
cd packages/backend && npx tsc --noEmit

# Frontend
cd packages/frontend && npm run lint
```

---

## Database Integration

The backend uses Supabase's `search_products` RPC function defined in the migrations. This function:

1. Takes a query embedding vector
2. Filters by age range, gender, price, and Prime eligibility
3. Returns products ordered by cosine similarity
4. Limits results to top 10 matches

See `supabase/migrations/001_create_products_table.sql` for the full function definition.
