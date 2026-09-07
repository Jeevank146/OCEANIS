from datetime import datetime, timezone
import logging
from typing import Optional

from sqlalchemy.orm import Session

from conversation.context import (
    ConversationContextManager,
    default_context_manager,
)
from conversation.query_parser import ConversationalQueryParser
from conversation.response_generator import ConversationalResponseGenerator
from conversation.schemas import (
    ConversationQuery,
    ConversationResponse,
)
from orchestrator.service import OrchestratorService

logger = logging.getLogger("oceanis.conversation.service")


class ConversationService:
    """
    Service gateway for the OCEANIS Conversational Intelligence Layer.
    Coordinates multilingual natural-language understanding, multi-turn session memory,
    authoritative Agent Orchestrator invocation, evidence-grounded response generation,
    and strict safety decision preservation.
    """

    def __init__(
        self,
        query_parser: Optional[ConversationalQueryParser] = None,
        response_generator: Optional[ConversationalResponseGenerator] = None,
        orchestrator_service: Optional[OrchestratorService] = None,
        context_manager: Optional[ConversationContextManager] = None,
    ):
        self.context_manager = context_manager or default_context_manager
        self.query_parser = query_parser or ConversationalQueryParser(context_manager=self.context_manager)
        self.response_generator = response_generator or ConversationalResponseGenerator()
        self.orchestrator_service = orchestrator_service or OrchestratorService()

    def process_message(
        self,
        db: Session,
        query: ConversationQuery,
        now: Optional[datetime] = None,
    ) -> ConversationResponse:
        """
        End-to-end processing pipeline for conversational maritime queries.
        """
        now_utc = now or datetime.now(timezone.utc)

        # 1. Parse natural language into normalized intent & structured context
        parsed_query, orch_query = self.query_parser.parse(
            message=query.message,
            conversation_id=query.conversation_id,
            explicit_language=query.language,
            explicit_mode=query.input_mode,
            explicit_location=query.location,
            context_overrides=query.context,
            now=now_utc,
        )

        # 2. Invoke authoritative Agent Orchestrator (Multi-Agent Decision Support)
        orchestration_response = self.orchestrator_service.process_query(
            db=db,
            query=orch_query,
            now=now_utc,
        )

        # 3. Generate localized natural-language response strictly grounded in backend evidence
        response_text = self.response_generator.generate_response(
            orchestration=orchestration_response,
            parsed_query=parsed_query,
        )

        # 4. Update multi-turn session context memory
        session_context = self.context_manager.get_or_create_context(
            conversation_id=query.conversation_id or orch_query.context.get("conversation_id"),
            language=parsed_query.language,
            input_mode=parsed_query.input_mode,
        )
        self.context_manager.update_context(
            context=session_context,
            user_message=query.message,
            parsed_query=parsed_query,
            orchestration=orchestration_response,
            response_text=response_text,
        )

        # 5. Return complete typed ConversationResponse
        return ConversationResponse(
            conversation_id=session_context.conversation_id,
            language=parsed_query.language,
            input_mode=parsed_query.input_mode,
            parsed_query=parsed_query,
            orchestration=orchestration_response,
            response=response_text,
            safety_status=orchestration_response.decision,
            risk_level=orchestration_response.risk_level,
            confidence=orchestration_response.confidence,
            freshness=orchestration_response.freshness,
            evidence=orchestration_response.evidence,
            warnings=orchestration_response.warnings,
            generated_at=now_utc,
        )
