"""
retriever.py

Complete Retrieval Pipeline
"""

from .wikipedia_loader import WikipediaLoader
from .chunker import TextChunker
from .vector_store import VectorStore


class Retriever:

    def __init__(self):

        self.loader = WikipediaLoader()

        self.chunker = TextChunker()

        self.store = VectorStore()

    def retrieve(self, article_title, query, top_k=5):
        """
        Retrieve top-k relevant chunks from Wikipedia.

        Args:
            article_title (str): Wikipedia article name
            query (str): User question
            top_k (int): Number of results

        Returns:
            list
        """

        print("Loading article...")

        article = self.loader.load_article(article_title)

        if article is None:
            return []

        print("Chunking article...")

        chunks = self.chunker.chunk_text(article)

        print(f"Total Chunks: {len(chunks)}")

        print("Building FAISS index...")

        self.store.add_documents(chunks)

        print("Searching...")

        results = self.store.search(query, top_k)

        return results


# ---------------------------------
# Example
# ---------------------------------

if __name__ == "__main__":

    retriever = Retriever()

    results = retriever.retrieve(
        article_title="Python (programming language)",
        query="Who invented Python?",
        top_k=5
    )

    print("\nTop Results\n")

    for i, item in enumerate(results, start=1):

        print(f"{i}. Distance = {item['distance']:.4f}")

        print(item["text"][:300])

        print("-" * 60)