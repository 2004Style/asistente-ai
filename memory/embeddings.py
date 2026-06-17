"""
Generates embeddings for text chunks to support semantic search.
"""
from typing import List

class EmbeddingService:
    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions

    def get_embedding(self, text: str) -> List[float]:
        """Generate a deterministic mock embedding vector based on the string hash."""
        val = hash(text)
        vector = []
        for i in range(self.dimensions):
            # Deterministic pseudo-random values
            val = (val * 1103515245 + 12345) & 0x7fffffff
            vector.append(float(val) / float(0x7fffffff) * 2.0 - 1.0)
        return vector
