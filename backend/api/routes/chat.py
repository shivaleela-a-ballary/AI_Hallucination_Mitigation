from fastapi import APIRouter, HTTPException
from api.utils.logger import logger
from api.models.request_models import ChatRequest
from api.models.response_models import ChatResponse

from api.services.integration_service import IntegrationService
from api.services.history_store import history_store

router = APIRouter(tags=["Chat"])

service = IntegrationService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:

        logger.info(f"Received query: {request.query}")

        result = service.process_query(request.query)
        result = history_store.add(request.query, result)

        logger.info("Response generated successfully.")

        return ChatResponse(**result)

    except (FileNotFoundError, ValueError) as exc:
        logger.warning("Pipeline is unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=f"Pipeline unavailable: {exc}") from exc
    except Exception as e:

        logger.exception("Error while processing request")

        raise
