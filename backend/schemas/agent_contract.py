from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QueryIntent(str, Enum):
    DECISION = "DECISION"
    INFORMATION = "INFORMATION"
    SAFETY = "SAFETY"
    COMPARISON = "COMPARISON"
    WHAT_IF = "WHAT_IF"
    ROUTE = "ROUTE"
    GENERAL = "GENERAL"


class ObservationType(str, Enum):
    OBSERVED = "Observed"
    FORECAST = "Forecast"
    OFFICIAL_WARNING = "Official Warning"
    AI_ASSESSMENT = "AI Assessment"


class DataFreshness(str, Enum):
    FRESH = "Fresh"
    AGING = "Aging"
    STALE = "Stale"
    UNAVAILABLE = "Unavailable"


class AgentStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class DecisionType(str, Enum):
    SUITABLE = "Suitable"
    CAUTION = "Caution"
    NOT_RECOMMENDED = "Not Recommended"
    INSUFFICIENT_EVIDENCE = "Insufficient Evidence"
    INFORMATION_ONLY = "Information"


class EvidenceItem(BaseModel):
    """
    Standardized traceable evidence item with full source provenance, timestamps,
    dynamic freshness, and explicit observation classification.
    """
    model_config = ConfigDict(extra="ignore")

    source: str = Field(..., description="Source authority (e.g. IMD, INCOIS, Copernicus Marine, Copernicus EO, PostGIS GIS Engine)")
    parameter: str = Field(..., description="Observed or predicted marine/weather parameter name")
    value: Any = Field(..., description="Observed, modeled, or evaluated value")
    unit: Optional[str] = Field(None, description="Measurement unit (e.g. m, km/h, deg C, mg/m3, NM)")
    observation_type: str = Field(ObservationType.OBSERVED.value, description="Observed, Forecast, Official Warning, AI Assessment")
    timestamp: Optional[str] = Field(None, description="Observation or forecast valid ISO timestamp")
    freshness: str = Field(DataFreshness.FRESH.value, description="Fresh, Aging, Stale, Unavailable")
    location: Optional[Dict[str, Any]] = Field(None, description="Spatial coordinates or port location")
    provenance: Optional[Dict[str, Any]] = Field(None, description="Additional provenance metadata (station ID, product ID, sensor, dataset)")


class AgentResult(BaseModel):
    """
    Standardized result contract returned by all six OCEANIS domain agents.
    """
    model_config = ConfigDict(extra="ignore")

    agent_name: str = Field(..., description="Human-readable name of the domain agent")
    status: str = Field(AgentStatus.SUCCESS.value, description="success, partial, unavailable, error")
    summary: str = Field(..., description="Domain-specific assessment summary")
    findings: List[str] = Field(default_factory=list, description="Key domain factual findings")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Structured traceable evidence items")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    warnings: List[str] = Field(default_factory=list, description="Domain-specific warnings or hazards")
    limitations: List[str] = Field(default_factory=list, description="Known domain data limitations or gaps")


class WhyDecisionBreakdown(BaseModel):
    """
    Structured explainability breakdown tracing decisions to specific evidence domains.
    """
    model_config = ConfigDict(extra="ignore")

    marine_conditions: List[str] = Field(default_factory=list, description="Marine physics and sea-state findings")
    ocean_conditions: List[str] = Field(default_factory=list, description="Ocean dynamics and hydrographic findings")
    eo_indicators: List[str] = Field(default_factory=list, description="Satellite Earth Observation and bio-optical findings")
    spatial_constraints: List[str] = Field(default_factory=list, description="Geospatial boundaries, zones and distance findings")
    safety_warnings: List[str] = Field(default_factory=list, description="Official disaster alerts and severe weather warnings")
    operational_factors: List[str] = Field(default_factory=list, description="Vessel operations and transit feasibility findings")


class ScenarioDetails(BaseModel):
    """
    Scenario specification for What-If simulation.
    """
    model_config = ConfigDict(extra="ignore")

    departure_time: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    decision: Optional[str] = None
    confidence_score: Optional[int] = None
    risk_level: Optional[str] = None
    key_conditions: List[str] = Field(default_factory=list)


class WhatIfComparison(BaseModel):
    """
    Comparison output between a base scenario and a simulated what-if scenario.
    """
    model_config = ConfigDict(extra="ignore")

    status: str = Field("success", description="success or insufficient_evidence")
    message: Optional[str] = None
    base_scenario: Optional[ScenarioDetails] = None
    what_if_scenario: Optional[ScenarioDetails] = None
    changed_factors: List[str] = Field(default_factory=list, description="List of parameters that changed between scenarios")
    decision_difference: Optional[str] = Field(None, description="Difference in final operational decision")
    confidence_difference: Optional[int] = Field(None, description="Difference in confidence percentage points")


class ComparisonLocationDetail(BaseModel):
    """
    Evaluation details for a specific location in a multi-location comparison query.
    """
    model_config = ConfigDict(extra="ignore")

    location_name: str
    latitude: float
    longitude: float
    decision: Optional[str] = None
    confidence: int = 0
    suitability_score: Optional[float] = None
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    """
    Structured result for comparison queries (e.g. Location A vs Location B).
    """
    model_config = ConfigDict(extra="ignore")

    target_locations: List[ComparisonLocationDetail] = Field(default_factory=list)
    recommended_location: Optional[str] = None
    comparison_summary: str = ""
    parameter_matrix: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class FinalDecisionObject(BaseModel):
    @property
    def agent_contributions(self) -> List[AgentResult]:
        return self.agents_consulted

    """
    Unified Final Decision Object consumed by the OCEANIS frontend and API clients.
    Supports general query types: DECISION, INFORMATION, SAFETY, COMPARISON, WHAT_IF, ROUTE.
    """
    model_config = ConfigDict(extra="ignore")

    query_intent: str = Field(QueryIntent.DECISION.value, description="DECISION, INFORMATION, SAFETY, COMPARISON, WHAT_IF, ROUTE, GENERAL")
    primary_answer: Optional[str] = Field(None, description="Direct natural-language answer to user query")
    decision: str = Field(..., description="Suitable, Caution, Not Recommended, Insufficient Evidence, Information")
    summary: str = Field(..., description="Natural-language explainable decision or information summary")
    confidence: int = Field(..., ge=0, le=100, description="Overall confidence score (0-100%)")
    confidence_reasons: List[str] = Field(default_factory=list, description="Transparent reasons explaining confidence calculation")
    safety_status: str = Field(..., description="Authoritative safety guardrail status")
    guardrail_actions: List[str] = Field(default_factory=list, description="Actions executed by the safety guardrail layer")
    key_findings: List[str] = Field(default_factory=list, description="Synthesized key factual findings")
    why_decision: WhyDecisionBreakdown = Field(default_factory=WhyDecisionBreakdown, description="Categorized Why This Decision evidence tracing")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Consolidated deduplicated evidence items with provenance")
    agents_consulted: List[AgentResult] = Field(default_factory=list, description="Structured results from all consulted domain agents")
    total_agents_available: int = Field(6, description="Total number of domain agents in the system")
    agents_consulted_count: int = Field(6, description="Number of agents actually consulted for this query")
    freshness_summary: str = Field(DataFreshness.FRESH.value, description="Fresh, Aging, Stale, Unavailable")
    warnings: List[str] = Field(default_factory=list, description="Consolidated official and operational warnings")
    limitations: List[str] = Field(default_factory=list, description="Consolidated data limitations or gaps")
    location: Optional[Dict[str, Any]] = Field(None, description="Resolved geographic context")
    requested_time: Optional[str] = Field(None, description="Requested operational date/time")
    what_if_comparison: Optional[WhatIfComparison] = Field(None, description="Optional what-if scenario comparison")
    comparison_data: Optional[ComparisonResult] = Field(None, description="Optional comparative location data")
    entities_extracted: Dict[str, Any] = Field(default_factory=dict, description="Dynamically extracted query entities")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
