"""
vector_store.py

Handles FAISS indexing and similarity search.
"""

import faiss
import numpy as np

from .embedder import Embedder


class VectorStore:
    def __init__(self):
        self.embedder = Embedder()

        self.dimension = 384

        self.index = faiss.IndexFlatL2(self.dimension)

        self.documents = []

    def add_documents(self, chunks):
        """
        Add document chunks to FAISS.
        """

        embeddings = []

        for chunk in chunks:
            vector = self.embedder.encode(chunk)

            embeddings.append(vector)

            self.documents.append(chunk)

        embeddings = np.array(embeddings).astype("float32")

        self.index.add(embeddings)

        print(f"{len(chunks)} chunks indexed.")

    def search(self, query, top_k=5):
        """
        Search similar chunks.
        """

        query_vector = self.embedder.encode(query)

        query_vector = np.array([query_vector]).astype("float32")

        distances, indices = self.index.search(query_vector, top_k)

        results = []

        for score, idx in zip(distances[0], indices[0]):

            if idx != -1:

                results.append({
                    "text": self.documents[idx],
                    "distance": float(score)
                })

        return results


# --------------------------------
# Example
# --------------------------------

if __name__ == "__main__":

    chunks = [
        "Python was created by Guido van Rossum.",
        "Machine Learning is a branch of Artificial Intelligence.",
        "The Earth revolves around the Sun.",
        "FastAPI is a Python web framework."
    ]

    store = VectorStore()

    store.add_documents(chunks)

    results = store.search("Who invented Python?")

    print("\nSearch Results\n")

    for result in results:

        print(result)