from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FishingLocationInput(BaseModel):
    name: Optional[str] = Field(None, description="Optional label or harbor name (e.g. Kakinada Offshore)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to 180)")


class FishingQuery(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Origin/fishing location latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Origin/fishing location longitude (-180 to 180)")
    destination_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Optional target fishing ground latitude")
    destination_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Optional target fishing ground longitude")
    date: Optional[str] = Field(None, description="Target fishing date (YYYY-MM-DD)")
    departure_time: Optional[str] = Field(None, description="Planned departure time (HH:MM or ISO timestamp)")
    duration_hours: Optional[float] = Field(None, gt=0.0, description="Expected voyage duration in hours")
    vessel_type: Optional[str] = Field("small_boat", description="Vessel class: small_boat, motorized_boat, trawler, traditional_craft")
    fishing_method: Optional[str] = Field(None, description="Fishing technique: gillnet, longline, trolling, hook_and_line, trawling")
    target_species: Optional[str] = Field(None, description="Target fish species: tuna, mackerel, sardine, seerfish, hilsa, etc.")
    question: Optional[str] = Field(None, description="Optional natural language inquiry from fisherman or operator")
    language: Optional[str] = Field("en", description="Preferred output response language code (e.g. en, te, ta, ml, hi)")


class EvidenceItem(BaseModel):
    factor: str = Field(..., description="Measurement or safety attribute (e.g. wave_height, sst, active_warnings)")
    value: Optional[Any] = Field(None, description="Recorded numerical or descriptive value")
    unit: Optional[str] = Field(None, description="Unit of measurement (°C, m, km/h, mg/m3, etc.)")
    source: str = Field(..., description="Issuing system or data provider")
    data_type: str = Field("OBSERVATION", description="OBSERVATION, FORECAST, MODEL, OFFICIAL, DEMO/TEST, UNKNOWN")
    observed_at: Optional[str] = Field(None, description="ISO timestamp of observation/bulletin")
    freshness: str = Field("UNKNOWN", description="FRESH, AGING, STALE, EXPIRED, UNKNOWN")
    assessment: str = Field(..., description="FAVORABLE, NEUTRAL, UNFAVORABLE, UNKNOWN, CRITICAL_HAZARD, RESTRICTED")
    notes: Optional[str] = None


class FishingSuitabilityFactor(BaseModel):
    name: str = Field(..., description="Factor name (e.g. SST Gradient, Sea State, Wind Speed, Navigation Path)")
    status: str = Field(..., description="FAVORABLE, NEUTRAL, UNFAVORABLE, UNKNOWN")
    impact: str = Field("NEUTRAL", description="POSITIVE, NEUTRAL, NEGATIVE, BLOCKING")
    summary: str = Field(..., description="Concise explanation based on evidence")


class FishingSuitability(BaseModel):
    status: str = Field(..., description="Overall suitability: FAVORABLE, NEUTRAL, UNFAVORABLE, CAUTION, BLOCKED, INSUFFICIENT_DATA")
    score: Optional[float] = Field(None, description="Optional deterministic suitability index (0.0 to 1.0) if factors present")
    factors: List[FishingSuitabilityFactor] = Field(default_factory=list, description="Breakdown of individual assessment factors")


class PFZAssessment(BaseModel):
    status: str = Field("UNAVAILABLE", description="AVAILABLE, UNAVAILABLE, UNKNOWN")
    zones: List[Dict[str, Any]] = Field(default_factory=list, description="Official Potential Fishing Zone coordinates if available")
    notes: str = Field(
        "Official INCOIS PFZ advisory data is currently unavailable for this sector; assessment relies on direct satellite SST, ocean current, and chlorophyll indicators.",
        description="Explaining PFZ availability status",
    )


class ConfidenceAssessment(BaseModel):
    level: str = Field(..., description="Confidence ranking: HIGH, MEDIUM, LOW, UNKNOWN")
    reasons: List[str] = Field(default_factory=list, description="Factors supporting the confidence level")


class FishingAssessment(BaseModel):
    query: Dict[str, Any] = Field(..., description="Normalized input query")
    location: Dict[str, float] = Field(..., description="Target coordinate latitude and longitude")
    overall_suitability: FishingSuitability = Field(..., description="Deterministic fishing suitability assessment")
    fishing_suitability: FishingSuitability = Field(..., description="Alias for overall_suitability")
    safety_status: str = Field(..., description="Deterministic safety classification (SAFE, CAUTION, WARNING, CRITICAL, BLOCKED, INSUFFICIENT_DATA)")
    risk_level: str = Field(..., description="Evaluated operational risk level (LOW, MODERATE, HIGH, CRITICAL, UNKNOWN)")
    confidence: ConfidenceAssessment = Field(..., description="Confidence level with diagnostic justification")
    key_conditions: Dict[str, Any] = Field(default_factory=dict, description="Summary of key marine, weather, and EO environmental metrics")
    evidence_used: List[EvidenceItem] = Field(default_factory=list, description="Structured traceable evidence items used for decision support")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Alias for evidence_used")
    domain_contributions: Dict[str, Any] = Field(default_factory=dict, description="Breakdown of contributions from individual OCEANIS backend layers")
    agent_contributions: Dict[str, Any] = Field(default_factory=dict, description="Alias for domain_contributions")
    recommendation: str = Field(..., description="Actionable fishing guidance and operational advice")
    explanation: str = Field(..., description="Comprehensive evidence-based reasoning narrative")
    reasons: List[str] = Field(default_factory=list, description="Diagnostic reasons justifying the recommendation")
    data_quality: Dict[str, Any] = Field(default_factory=dict, description="Telemetry freshness, coverage completeness, and quality flags")
    freshness: str = Field("FRESH", description="Overall freshness category of ingested observations")
    warnings_and_overrides: List[str] = Field(default_factory=list, description="List of active warnings and safety overrides applied")
    warnings: List[str] = Field(default_factory=list, description="Alias for warnings_and_overrides")
    pfz: PFZAssessment = Field(default_factory=PFZAssessment, description="Potential Fishing Zone advisory status")
    marine_conditions: Optional[Dict[str, Any]] = None
    weather: Optional[Dict[str, Any]] = None
    earth_observation: Optional[Dict[str, Any]] = None
    safety: Dict[str, Any] = Field(..., description="Deterministic safety evaluation result from Disaster & Safety layer")
    operations: Optional[Dict[str, Any]] = None
    generated_at: datetime = Field(..., description="UTC timestamp of assessment generation")

    model_config = ConfigDict(from_attributes=True)


class LocationComparisonQuery(BaseModel):
    location_a: FishingLocationInput
    location_b: FishingLocationInput
    date: Optional[str] = None
    departure_time: Optional[str] = None
    vessel_type: Optional[str] = "small_boat"
    target_species: Optional[str] = None
    language: Optional[str] = "en"


class LocationComparisonResponse(BaseModel):
    location_a_assessment: FishingAssessment
    location_b_assessment: FishingAssessment
    comparison_summary: Dict[str, Any] = Field(..., description="Key comparison metrics between location A and B")
    recommended_option: Optional[str] = Field(None, description="location_a, location_b, neither, or undetermined")
    reasons: List[str] = Field(default_factory=list, description="Reasons for comparative recommendation")
    confidence: str = Field(..., description="Comparative confidence level")

    model_config = ConfigDict(from_attributes=True)


class WhatIfQuery(BaseModel):
    baseline_query: FishingQuery
    modified_departure_time: Optional[str] = Field(None, description="Alternative departure time (e.g. '09:00')")
    modified_date: Optional[str] = Field(None, description="Alternative date (YYYY-MM-DD)")
    modified_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Alternative fishing latitude")
    modified_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Alternative fishing longitude")
    modified_duration_hours: Optional[float] = Field(None, gt=0.0, description="Alternative voyage duration in hours")
    scenario_description: Optional[str] = Field(None, description="User question or scenario label (e.g. 'What if I leave at 9 AM?')")


class WhatIfResponse(BaseModel):
    baseline: FishingAssessment
    scenario: FishingAssessment
    changes: List[str] = Field(default_factory=list, description="List of parameters modified in scenario")
    safety_change: str = Field(..., description="IMPROVED, UNCHANGED, DEGRADED, BLOCKED")
    suitability_change: str = Field(..., description="IMPROVED, UNCHANGED, DEGRADED")
    confidence: str = Field(..., description="Scenario confidence level")
    recommendation: str = Field(..., description="Recommendation comparing scenario vs baseline")
    summary: str = Field(..., description="Summary of what-if scenario outcome")

    model_config = ConfigDict(from_attributes=True)
