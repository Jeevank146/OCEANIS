from datetime import datetime, timezone
import re
from typing import Dict, Optional
import uuid

from conversation.schemas import (
    ConversationContext,
    ConversationTurn,
    LocationEntity,
    ParsedQuery,
)
from orchestrator.schemas import OrchestrationResponse


class ConversationContextManager:
    """
    Session and multi-turn conversational context manager.
    Maintains active operational parameters across follow-up queries and resolves ellipsis.
    Modular design ready for future PostgreSQL persistence without changing callers.
    """

    def __init__(self):
        self._sessions: Dict[str, ConversationContext] = {}

    def get_or_create_context(
        self,
        conversation_id: Optional[str] = None,
        language: str = "en",
        input_mode: str = "standard",
    ) -> ConversationContext:
        """
        Retrieves existing conversation context or initializes a fresh session.
        """
        cid = conversation_id or str(uuid.uuid4())
        if cid not in self._sessions:
            self._sessions[cid] = ConversationContext(
                conversation_id=cid,
                language=language,
                input_mode=input_mode,
            )
        return self._sessions[cid]

    def resolve_follow_up_context(
        self,
        context: ConversationContext,
        parsed_query: ParsedQuery,
    ) -> ParsedQuery:
        """
        Merges existing session state into new parsed query if it represents a follow-up inquiry.
        Handles time shifts ("What if I go at 9 AM?"), location shifts ("How about Vizag instead?"),
        or parameter modifications.
        """
        if not context.turns:
            # First turn, no historical context to merge
            return parsed_query

        # Check if the query is an ellipsis or follow-up question
        is_follow_up = parsed_query.is_follow_up or self._is_follow_up_expression(parsed_query.original_query)

        # If location is missing in current turn but present in active context, inherit it
        inherited_location = parsed_query.location
        if not inherited_location and context.active_location:
            inherited_location = context.active_location
            is_follow_up = True

        # If date is missing in current turn but present in active context, inherit it
        inherited_date = parsed_query.target_date
        if not inherited_date and context.active_target_date:
            inherited_date = context.active_target_date
            is_follow_up = True

        # If intent is generic or fishing follow-up, inherit active intent
        inherited_intent = parsed_query.intent
        if (inherited_intent in ("GENERAL_INQUIRY", "UNKNOWN") or is_follow_up) and context.active_intent:
            inherited_intent = context.active_intent

        # Inherit vessel & species
        inherited_species = parsed_query.target_species or context.active_target_species
        inherited_vessel = parsed_query.vessel_type or context.active_vessel_type

        # Reconstruct normalized orchestrator query if follow-up values were inherited
        reconstructed_query = parsed_query.orchestrator_query
        if is_follow_up and inherited_location and inherited_location.name:
            loc_name = inherited_location.name
            time_part = f"at {parsed_query.target_time or context.active_target_time}" if (parsed_query.target_time or context.active_target_time) else ""
            date_part = f"on {inherited_date}" if inherited_date else "tomorrow"

            if inherited_intent == "FISHING_ASSESSMENT":
                reconstructed_query = f"Can I go fishing {date_part} {time_part} from {loc_name}?"
            elif inherited_intent == "ROUTE_OPERATION" and context.active_destination:
                reconstructed_query = f"Is it safe to travel from {loc_name} to {context.active_destination.name}?"

        return parsed_query.model_copy(
            update={
                "intent": inherited_intent,
                "location": inherited_location,
                "target_date": inherited_date,
                "target_species": inherited_species,
                "vessel_type": inherited_vessel,
                "is_follow_up": is_follow_up,
                "orchestrator_query": reconstructed_query,
            }
        )

    def update_context(
        self,
        context: ConversationContext,
        user_message: str,
        parsed_query: ParsedQuery,
        orchestration: OrchestrationResponse,
        response_text: str,
    ) -> None:
        """
        Updates session context with the completed turn and new active operational state.
        """
        turn_id = len(context.turns) + 1
        turn = ConversationTurn(
            turn_id=turn_id,
            user_message=user_message,
            parsed_query=parsed_query,
            decision=orchestration.decision,
            risk_level=orchestration.risk_level,
            assistant_response=response_text,
            timestamp=datetime.now(timezone.utc),
        )
        context.turns.append(turn)

        # Update active state
        if parsed_query.intent and parsed_query.intent != "GENERAL_INQUIRY":
            context.active_intent = parsed_query.intent
        if parsed_query.location:
            context.active_location = parsed_query.location
        if parsed_query.destination_location:
            context.active_destination = parsed_query.destination_location
        if parsed_query.comparison_locations:
            context.active_comparison_locations = parsed_query.comparison_locations
        if parsed_query.target_date:
            context.active_target_date = parsed_query.target_date
        if parsed_query.target_time:
            context.active_target_time = parsed_query.target_time
        if parsed_query.target_species:
            context.active_target_species = parsed_query.target_species
        if parsed_query.vessel_type:
            context.active_vessel_type = parsed_query.vessel_type

        context.language = parsed_query.language
        context.input_mode = parsed_query.input_mode
        context.updated_at = datetime.now(timezone.utc)

    def _is_follow_up_expression(self, text: str) -> bool:
        """
        Checks if query is structured as a follow-up / modification question.
        """
        lower = text.lower()
        patterns = [
            r"what if",
            r"how about",
            r"what about",
            r"pothe ela",
            r"vellithe ela",
            r"at \d{1,2}(:\d{2})?\s*(am|pm)?",
            r"^\d{1,2}(:\d{2})?\s*(am|pm)?\s*(ki|ku|ke)?\??$",
            r"instead",
            r"maristhe",
            r"change to",
            r"next day",
            r"day after",
        ]
        return any(re.search(p, lower) for p in patterns)

    def clear(self, conversation_id: str) -> None:
        """
        Clears session memory for a given conversation.
        """
        if conversation_id in self._sessions:
            del self._sessions[conversation_id]


# Process-wide singleton instance for in-memory session persistence
default_context_manager = ConversationContextManager()
