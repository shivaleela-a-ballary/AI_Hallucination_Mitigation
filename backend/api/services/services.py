"""
Service Connector

Acts as a bridge between the API layer
and backend modules developed by other team members.
"""

from typing import Dict, List


class BackendServices:
    """
    Wrapper around all backend modules.
    """

    def preprocess(self, query: str) -> str:
        """
        Calls preprocessing module.
        """

        # TODO:
        # Replace with teammate's preprocessing module
        return query

    def retrieve(self, query: str) -> List[Dict]:
        """
        Calls retrieval module.
        """

        # TODO:
        # Replace with teammate's retrieval module

        return [
            {
                "title": "Sample Document",
                "content": "Retrieved document."
            }
        ]

    def verify(self, query: str, documents: List[Dict]) -> Dict:
        """
        Calls verification module.
        """

        # TODO:
        # Replace with teammate's verification module

        return {
            "status": "SUPPORTED",
            "confidence": 0.97
        }