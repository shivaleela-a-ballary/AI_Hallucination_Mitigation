"""
embedder.py

This module generates embeddings for user queries and documents
using the Sentence Transformer model.

Model:
    all-MiniLM-L6-v2
"""

from sentence_transformers import SentenceTransformer
import numpy as np


class Embedder:
    """
    Handles text embedding generation.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Load the embedding model once.
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str) -> np.ndarray:
        """
        Convert text into an embedding vector.

        Args:
            text (str): Input sentence or paragraph.

        Returns:
            np.ndarray: Embedding vector.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding


# ----------------------------
# Example Usage
# ----------------------------
if __name__ == "__main__":
    embedder = Embedder()

    query = "Who invented Python?"

    vector = embedder.encode(query)

    print("Query:", query)
    print("Embedding Shape:", vector.shape)
    print(vector[:10])  # Display first 10 values