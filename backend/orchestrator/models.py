from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from agents.fishing.schemas import ConfidenceAssessment, EvidenceItem


class AgentQueryRequest(BaseModel):
    """
    Natural-language or structured query submitted to the OCEANIS Agent Orchestrator.
    """
    query: str = Field(..., min_length=2, description="Natural-language question or operational request from user")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Optional explicit origin latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Optional explicit origin longitude")
    destination_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Optional destination latitude")
    destination_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Optional destination longitude")
    target_datetime: Optional[str] = Field(None, description="Optional target date or ISO timestamp (e.g. '2026-09-07T06:00:00Z')")
    vessel_type: Optional[str] = Field(None, description="Optional vessel class (e.g. small_boat, trawler, cargo, container)")
    target_species: Optional[str] = Field(None, description="Optional target fish species (e.g. mackerel, tuna, sardine)")
    language: Optional[str] = Field("en", description="Output response language code (e.g. en, te, ta, ml, hi)")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional session or conversational context")


class LocationEntity(BaseModel):
    name: Optional[str] = None
    latitude: float
    longitude: float
    is_port: bool = False
    port_name: Optional[str] = None


class ExtractedEntities(BaseModel):
    locations: List[LocationEntity] = Field(default_factory=list, description="Extracted geographic coordinates and ports")
    origin_location: Optional[LocationEntity] = None
    destination_location: Optional[LocationEntity] = None
    target_date: Optional[str] = None
    target_time: Optional[str] = None
    duration_hours: Optional[float] = None
    activity_type: Optional[str] = None
    target_species: Optional[str] = None
    vessel_type: Optional[str] = None
    comparison_mode: bool = False


class AgentSelection(BaseModel):
    agent_id: str = Field(..., description="Unique identifier of selected domain agent")
    agent_name: str = Field(..., description="Human-readable name of domain agent")
    domain: str = Field(..., description="Primary domain responsibility")
    selection_reason: str = Field(..., description="Explainable reason justifying why this agent was selected")
    priority: int = Field(..., description="Execution priority (1 = highest, executed first)")
    execution_order: int = Field(..., description="Order of agent execution in workflow")


class ExecutionPlan(BaseModel):
    plan_id: str = Field(..., description="Unique plan identifier")
    primary_intent: str = Field(..., description="Identified primary user intent")
    detected_intents: List[str] = Field(default_factory=list, description="Secondary or supporting intents detected")
    selected_agents: List[AgentSelection] = Field(default_factory=list, description="List of domain agents to execute")
    execution_steps: List[str] = Field(default_factory=list, description="Sequential steps in the orchestrator plan")
    planner_type: str = Field("DETERMINISTIC_RULES", description="Planner mechanism (DETERMINISTIC_RULES or HYBRID_LLM)")
    notes: Optional[str] = None


class AgentExecutionResult(BaseModel):
    agent_id: str
    status: str = Field("SUCCESS", description="SUCCESS, FAILED, SKIPPED")
    summary: str
    data: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0
    error: Optional[str] = None


class OrchestratorQueryResponse(BaseModel):
    query: str = Field(..., description="Original user natural language query")
    interpreted_query: str = Field(..., description="Normalized interpretation of the query")
    detected_intent: str = Field(..., description="Primary classified intent")
    extracted_entities: ExtractedEntities = Field(..., description="Entities extracted from query and payload")
    location: Dict[str, Any] = Field(default_factory=dict, description="Primary coordinate or port evaluated")
    target_time: Optional[str] = Field(None, description="Target timestamp or operational window")
    selected_agents: List[AgentSelection] = Field(default_factory=list, description="Agents selected with explainable reasons")
    execution_plan: ExecutionPlan = Field(..., description="Orchestration plan executed")
    agent_results: Dict[str, Any] = Field(default_factory=dict, description="Structured outputs per domain agent")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Traceable evidence collected across all layers")
    safety_status: str = Field(..., description="Deterministic safety classification (SAFE, CAUTION, WARNING, CRITICAL, BLOCKED, INSUFFICIENT_DATA)")
    risk_level: str = Field(..., description="Evaluated operational risk level (LOW, MODERATE, HIGH, CRITICAL, UNKNOWN)")
    confidence: ConfidenceAssessment = Field(..., description="Confidence ranking and diagnostic reasons")
    recommendation: str = Field(..., description="Actionable synthesized operational recommendation")
    explanation: str = Field(..., description="Comprehensive explanation justifying the recommendation")
    warnings: List[str] = Field(default_factory=list, description="Active official warnings and safety overrides applied")
    data_freshness: str = Field("FRESH", description="Aggregated freshness rating (FRESH, AGING, STALE, UNKNOWN)")
    generated_at: datetime = Field(..., description="UTC timestamp of response synthesis")

    model_config = ConfigDict(from_attributes=True)
