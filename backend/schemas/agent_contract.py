from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


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


class EvidenceItem(BaseModel):
    """
    Standardized traceable evidence item with full source provenance, timestamps,
    dynamic freshness, and explicit observation classification.
    """
    model_config = ConfigDict(extra="ignore")

    source: str = Field(..., description="Source authority (e.g. IMD, INCOIS, Copernicus Marine, Copernicus EO, PostGIS GIS Engine)")
    parameter: str = Field(..., description="Observed or predicted marine/weather parameter name")
    value: Any = Field(..., description="Observed, modeled, or evaluated value")
    unit: Optional[str] = Field(None, description="Measurement unit (e.g. m, km/h, °C, mg/m³, NM)")
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

    marine_conditions: List[str] = Field(default_factory=list, description="Marine physics & sea-state findings")
    ocean_conditions: List[str] = Field(default_factory=list, description="Ocean dynamics & hydrographic findings")
    eo_indicators: List[str] = Field(default_factory=list, description="Satellite Earth Observation & bio-optical findings")
    spatial_constraints: List[str] = Field(default_factory=list, description="Geospatial boundaries, zones & distance findings")
    safety_warnings: List[str] = Field(default_factory=list, description="Official disaster alerts & severe weather warnings")
    operational_factors: List[str] = Field(default_factory=list, description="Vessel operations & transit feasibility findings")


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


class FinalDecisionObject(BaseModel):
    """
    Unified Final Decision Object consumed by the OCEANIS frontend and API clients.
    """
    model_config = ConfigDict(extra="ignore")

    decision: str = Field(..., description="Suitable, Caution, Not Recommended, Insufficient Evidence")
    summary: str = Field(..., description="Natural-language explainable decision summary")
    confidence: int = Field(..., ge=0, le=100, description="Overall confidence score (0-100%)")
    confidence_reasons: List[str] = Field(default_factory=list, description="Transparent reasons explaining confidence calculation")
    safety_status: str = Field(..., description="Authoritative safety guardrail status")
    guardrail_actions: List[str] = Field(default_factory=list, description="Actions executed by the safety guardrail layer")
    key_findings: List[str] = Field(default_factory=list, description="Synthesized key factual findings")
    why_decision: WhyDecisionBreakdown = Field(default_factory=WhyDecisionBreakdown, description="Categorized 'Why This Decision?' evidence tracing")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Consolidated deduplicated evidence items with provenance")
    agents_consulted: List[AgentResult] = Field(default_factory=list, description="Structured results from all consulted domain agents")
    freshness_summary: str = Field(DataFreshness.FRESH.value, description="Fresh, Aging, Stale, Unavailable")
    warnings: List[str] = Field(default_factory=list, description="Consolidated official and operational warnings")
    limitations: List[str] = Field(default_factory=list, description="Consolidated data limitations or gaps")
    location: Optional[Dict[str, Any]] = Field(None, description="Resolved geographic context")
    requested_time: Optional[str] = Field(None, description="Requested operational date/time")
    what_if_comparison: Optional[WhatIfComparison] = Field(None, description="Optional what-if scenario comparison")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
