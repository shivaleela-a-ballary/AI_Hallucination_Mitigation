from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request model for chat queries.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's question or prompt."
    )