from fastapi import APIRouter
from api.utils.logger import logger
from api.models.request_models import ChatRequest
from api.models.response_models import ChatResponse, Source

from api.services.integration_service import IntegrationService

router = APIRouter(tags=["Chat"])

service = IntegrationService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:

        logger.info(f"Received query: {request.query}")

        result = service.process_query(request.query)

        logger.info("Response generated successfully.")

        return ChatResponse(
            answer=result["answer"],
            verification_status=result["verification"]["status"],
            confidence_score=result["verification"]["confidence"],
            sources=result["documents"]
        )

    except Exception as e:

        logger.exception("Error while processing request")

        raise e