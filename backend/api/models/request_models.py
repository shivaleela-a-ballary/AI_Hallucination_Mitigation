from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request model for chat queries.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's question or prompt."
    )

    @property
    def query(self) -> str:
        """Compatibility accessor for the existing service layer."""
        return self.question


class VerifyRequest(BaseModel):
    """A claim and optional user-supplied evidence for direct verification."""

    claim: str = Field(..., min_length=1, max_length=2000)
    evidence: str = Field(default="", max_length=20000)
