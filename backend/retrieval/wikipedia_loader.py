"""
wikipedia_loader.py

Loads Wikipedia articles using wikipedia-api.
"""

import wikipediaapi


class WikipediaLoader:
    def __init__(self):
        self.wiki = wikipediaapi.Wikipedia(
            language="en",
            user_agent="AIHallucinationMitigation/1.0 (student-project)"
        )

    def load_article(self, title):
        """
        Load a Wikipedia article.

        Args:
            title (str): Article title

        Returns:
            str: Article text
        """

        page = self.wiki.page(title)

        if not page.exists():
            print("Article not found.")
            return None

        return page.text


# -------------------------
# Example
# -------------------------
if __name__ == "__main__":

    loader = WikipediaLoader()

    article = loader.load_article("Python (programming language)")

    if article:
        print(article[:1000])