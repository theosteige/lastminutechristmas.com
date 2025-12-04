import OpenAI from 'openai';

let openai: OpenAI | null = null;

function getOpenAIClient(): OpenAI {
  if (!openai) {
    openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
  }
  return openai;
}

/**
 * Generate an embedding vector for the given text
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await getOpenAIClient().embeddings.create({
    model: 'text-embedding-3-small',
    input: text,
  });

  return response.data[0].embedding;
}

/**
 * Generate embeddings for multiple texts and average them
 * This is used for the refine feature where multiple blurbs are combined
 */
export async function generateAveragedEmbedding(texts: string[]): Promise<number[]> {
  if (texts.length === 1) {
    return generateEmbedding(texts[0]);
  }

  // Generate embeddings for all texts in parallel
  const embeddings = await Promise.all(texts.map(generateEmbedding));

  // Average the embeddings
  const dimensions = embeddings[0].length;
  const averaged = new Array(dimensions).fill(0);

  for (const embedding of embeddings) {
    for (let i = 0; i < dimensions; i++) {
      averaged[i] += embedding[i];
    }
  }

  for (let i = 0; i < dimensions; i++) {
    averaged[i] /= embeddings.length;
  }

  return averaged;
}
