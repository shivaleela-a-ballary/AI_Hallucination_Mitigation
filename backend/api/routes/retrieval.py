from fastapi import APIRouter
from pydantic import BaseModel

from backend.retrieval.retriever import Retriever

router = APIRouter()

retriever = Retriever()


class RetrievalRequest(BaseModel):
    article_title: str
    query: str
    top_k: int = 5


@router.post("/retrieve")
def retrieve(request: RetrievalRequest):

    results = retriever.retrieve(
        article_title=request.article_title,
        query=request.query,
        top_k=request.top_k,
    )

    return {
        "query": request.query,
        "article": request.article_title,
        "results": results,
    }