"""
chunker.py

Splits large text into smaller chunks for retrieval.
"""


class TextChunker:
    def __init__(self, chunk_size=200, overlap=50):
        """
        chunk_size : Number of words per chunk
        overlap    : Number of overlapping words
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text):
        """
        Split text into overlapping chunks.
        """
        words = text.split()

        chunks = []

        start = 0

        while start < len(words):
            end = start + self.chunk_size

            chunk = " ".join(words[start:end])

            chunks.append(chunk)

            start += self.chunk_size - self.overlap

        return chunks


# -------------------------------
# Example
# -------------------------------
if __name__ == "__main__":

    sample_text = """
    Python is a high-level programming language created by Guido van Rossum.
    It supports object-oriented programming and is widely used for
    Artificial Intelligence, Machine Learning, Web Development,
    Automation, and Data Science.
    """ * 20

    chunker = TextChunker()

    chunks = chunker.chunk_text(sample_text)

    print(f"Total Chunks: {len(chunks)}")

    print("\nFirst Chunk:\n")

    print(chunks[0])