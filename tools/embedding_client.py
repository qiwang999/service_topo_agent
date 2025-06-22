import openai
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmbeddingClient:
    """
    Client for OpenAI embedding API with vector operations.
    """

    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Initialize the embedding client.

        Args:
            model_name (str): OpenAI embedding model name
        """
        self.model_name = model_name
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.

        Args:
            text (str): Text to embed

        Returns:
            List[float]: Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batch.

        Args:
            texts (List[str]): List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Error getting batch embeddings: {e}")
            return [[] for _ in texts]

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1 (List[float]): First vector
            vec2 (List[float]): Second vector

        Returns:
            float: Cosine similarity score (0-1)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_most_similar(self, query_embedding: List[float],
                          candidate_embeddings: List[List[float]],
                          top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Find the most similar embeddings to the query.

        Args:
            query_embedding (List[float]): Query embedding
            candidate_embeddings (List[List[float]]): Candidate embeddings
            top_k (int): Number of top results to return

        Returns:
            List[Tuple[int, float]]: List of (index, similarity_score) tuples
        """
        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            if candidate:  # Skip empty embeddings
                similarity = self.cosine_similarity(query_embedding, candidate)
                similarities.append((i, similarity))

        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def semantic_search(self, query: str, candidates: List[str],
                        top_k: int = 5) -> List[Tuple[int, float, str]]:
        """
        Perform semantic search on a list of candidate texts.

        Args:
            query (str): Search query
            candidates (List[str]): Candidate texts
            top_k (int): Number of top results to return

        Returns:
            List[Tuple[int, float, str]]: List of (index, similarity_score, text) tuples
        """
        # Get embeddings
        query_embedding = self.get_embedding(query)
        candidate_embeddings = self.get_embeddings_batch(candidates)

        if not query_embedding:
            return []

        # Find most similar
        similar_indices = self.find_most_similar(
            query_embedding, candidate_embeddings, top_k)

        # Return results with text
        results = []
        for idx, similarity in similar_indices:
            if idx < len(candidates):
                results.append((idx, similarity, candidates[idx]))

        return results
