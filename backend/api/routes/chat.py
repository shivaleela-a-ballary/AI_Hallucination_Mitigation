from fastapi import APIRouter
from api.utils.logger import logger
from api.models.request_models import ChatRequest
from api.models.response_models import ChatResponse

from api.services.integration_service import IntegrationService

router = APIRouter(tags=["Chat"])

service = IntegrationService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:

        logger.info(f"Received query: {request.query}")

        result = service.process_query(request.query)

        logger.info("Response generated successfully.")

        return ChatResponse(**result)

    except Exception as e:

        logger.exception("Error while processing request")

        raise
