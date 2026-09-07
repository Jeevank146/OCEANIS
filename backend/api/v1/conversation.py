import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from conversation.schemas import (
    ConversationQuery,
    ConversationResponse,
)
from conversation.service import ConversationService
from database import get_db

logger = logging.getLogger("oceanis.api.conversation")

router = APIRouter(prefix="/conversation", tags=["Conversational Intelligence"])


@router.post(
    "/query",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Process natural-language conversational query in English or Indian regional languages",
    description=(
        "Entrypoint for natural-language user messages (voice transcripts or text). "
        "Understands English, Telugu Unicode, Telugu Transliteration, and Hindi. "
        "Maintains multi-turn context for follow-up questions, executes authoritative multi-agent "
        "orchestration across domain agents, and produces localized responses grounded in structured evidence."
    ),
)
def process_conversation_query(
    query: ConversationQuery,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """
    Handles conversational interactions across English and Indian coastal regional languages.
    """
    try:
        service = ConversationService()
        return service.process_message(db=db, query=query)
    except ValueError as ve:
        logger.error(f"Validation error in conversation query: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Unexpected error in conversation query processing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversational processing error: {str(e)}",
        )
