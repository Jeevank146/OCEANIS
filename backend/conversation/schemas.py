from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from orchestrator.schemas import FusedEvidenceItem, OrchestrationResponse


class ConversationQuery(BaseModel):
    """
    Inbound conversational request from client application.
    Supports English and Indian regional language / transliterated natural text.
    """
    message: str = Field(..., min_length=1, description="User natural language message or voice transcript")
    conversation_id: Optional[str] = Field(None, description="Optional existing session ID for multi-turn context tracking")
    language: Optional[str] = Field(None, description="Optional explicit language code (e.g. en, te, hi). If omitted, auto-detected.")
    input_mode: Optional[str] = Field(None, description="Optional input script mode: 'standard' or 'transliterated'")
    location: Optional[Dict[str, Any]] = Field(None, description="Optional client-provided device location coordinates")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional user or session parameters (e.g. vessel_type)")


class LocationEntity(BaseModel):
    """
    Extracted geographic location entity.
    """
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_port: bool = False
    port_name: Optional[str] = None


class ExtractedEntity(BaseModel):
    """
    General semantic entity extracted from natural language.
    """
    entity_type: str = Field(..., description="LOCATION, SPECIES, VESSEL, TIME, DATE, PHENOMENON, HAZARD")
    value: str = Field(..., description="Normalized entity value")
    raw_text: Optional[str] = Field(None, description="Original token text from message")
    confidence: float = 1.0


class ParsedQuery(BaseModel):
    """
    Normalized structured representation of a conversational user inquiry.
    Directly bridges conversational input to the OCEANIS Agent Orchestrator.
    """
    original_query: str = Field(..., description="Original user input message")
    language: str = Field("en", description="Detected or requested language code (en, te, hi, etc.)")
    input_mode: str = Field("standard", description="Input mode: 'standard' or 'transliterated'")
    intent: str = Field(..., description="Classified intent (FISHING_ASSESSMENT, FISHING_COMPARISON, ROUTE_OPERATION, MARINE_SAFETY, MARINE_CONDITIONS, EARTH_OBSERVATION, GENERAL_INQUIRY)")
    location: Optional[LocationEntity] = Field(None, description="Primary origin / operating location")
    destination_location: Optional[LocationEntity] = Field(None, description="Destination location if route operation")
    comparison_locations: List[LocationEntity] = Field(default_factory=list, description="Multiple locations if comparative inquiry")
    datetime_context: Optional[str] = Field(None, description="Extracted ISO timestamp or human date/time string")
    target_date: Optional[str] = Field(None, description="Extracted date (YYYY-MM-DD)")
    target_time: Optional[str] = Field(None, description="Extracted time (HH:MM)")
    target_species: Optional[str] = Field(None, description="Target marine species if fishing")
    vessel_type: Optional[str] = Field(None, description="Target vessel class")
    operation_type: Optional[str] = Field(None, description="Target operational category")
    is_comparison: bool = False
    is_follow_up: bool = False
    entities: List[ExtractedEntity] = Field(default_factory=list, description="List of recognized named entities")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="Session and context attributes merged from history")
    orchestrator_query: str = Field(..., description="Normalized, orchestrator-compatible English/standard query string")


class ConversationTurn(BaseModel):
    """
    A single turn record in an active conversation session.
    """
    turn_id: int
    user_message: str
    parsed_query: ParsedQuery
    decision: str
    risk_level: str
    assistant_response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationContext(BaseModel):
    """
    Multi-turn conversation session memory.
    Maintains context across sequential turns to resolve follow-up inquiries.
    """
    conversation_id: str
    turns: List[ConversationTurn] = Field(default_factory=list)
    active_intent: Optional[str] = None
    active_location: Optional[LocationEntity] = None
    active_destination: Optional[LocationEntity] = None
    active_comparison_locations: List[LocationEntity] = Field(default_factory=list)
    active_target_date: Optional[str] = None
    active_target_time: Optional[str] = None
    active_target_species: Optional[str] = None
    active_vessel_type: Optional[str] = None
    language: str = "en"
    input_mode: str = "standard"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationResponse(BaseModel):
    """
    Complete conversational response returned to the client.
    Combines natural-language localized response text with structured decision evidence.
    """
    conversation_id: str = Field(..., description="Unique conversational session identifier")
    language: str = Field("en", description="Output language code")
    input_mode: str = Field("standard", description="Output script style: 'standard' or 'transliterated'")
    parsed_query: ParsedQuery = Field(..., description="Structured interpretation of user message")
    orchestration: OrchestrationResponse = Field(..., description="Authoritative backend orchestration output")
    response: str = Field(..., description="Conversational, natural-language explanation generated from structured evidence")
    safety_status: str = Field(..., description="Deterministic safety classification: CLEAR, CAUTION, WARNING, BLOCKED, INSUFFICIENT_DATA")
    risk_level: str = Field(..., description="Operational risk level: LOW, MODERATE, HIGH, CRITICAL, UNKNOWN")
    confidence: str = Field(..., description="Composite confidence rating: HIGH, MEDIUM, LOW, INSUFFICIENT_DATA")
    freshness: str = Field(..., description="Environmental data freshness: FRESH, AGING, STALE, UNAVAILABLE")
    evidence: List[FusedEvidenceItem] = Field(default_factory=list, description="Preserved multi-agent evidence items with source provenance")
    warnings: List[str] = Field(default_factory=list, description="Safety warnings, active marine alerts, and operational constraints")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC response generation timestamp")

    model_config = ConfigDict(from_attributes=True)
