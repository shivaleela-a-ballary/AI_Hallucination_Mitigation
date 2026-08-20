from fastapi import APIRouter, Depends, HTTPException
from api.utils.logger import logger
from api.models.request_models import ChatRequest
from api.models.response_models import ChatResponse

from api.db.mongodb import db_manager
from api.dependencies import get_optional_current_user
from api.services.integration_service import IntegrationService
from api.services.history_store import history_store

router = APIRouter(tags=["Chat"])

service = IntegrationService()


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: dict | None = Depends(get_optional_current_user),
):
    try:
        logger.info(f"Received query: {request.query}")
        user_id = current_user.get("id") if current_user else None

        result = service.process_query(request.query)
        result["type"] = "qa_chat"
        saved = db_manager.add_verification_history(result, user_id=user_id)
        history_store.add(request.query, saved)

        logger.info("Response generated successfully.")

        return ChatResponse(**saved)

    except (FileNotFoundError, ValueError) as exc:
        logger.warning("Pipeline is unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=f"Pipeline unavailable: {exc}") from exc
    except Exception as e:

        logger.exception("Error while processing request")

        raise
