from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from agents.fishing.collector import FishingDataCollector
from agents.fishing.prompts import generate_deterministic_narrative
from agents.fishing.reasoning import FishingReasoningEngine
from agents.fishing.schemas import (
    ConfidenceAssessment,
    FishingAssessment,
    FishingQuery,
    FishingSuitability,
    LocationComparisonQuery,
    LocationComparisonResponse,
    PFZAssessment,
    WhatIfQuery,
    WhatIfResponse,
)


class FishingIntelligenceAgent:
    """
    OCEANIS Fishing Intelligence Domain Agent.
    Coordinates evidence collection across Weather, Marine, Earth Observation,
    Geo-Spatial, Disaster & Safety, and Marine Operations backend layers to produce
    deterministic, explainable, safety-governed fishing decision support.
    """

    def __init__(self, data_collector: Optional[FishingDataCollector] = None, reasoning_engine: Optional[FishingReasoningEngine] = None):
        self.collector = data_collector or FishingDataCollector()
        self.reasoning = reasoning_engine or FishingReasoningEngine()

    def assess(
        self,
        db: Session,
        query: FishingQuery,
        now: Optional[datetime] = None,
    ) -> FishingAssessment:
        """
        Executes complete multi-layer evidence fusion and deterministic suitability assessment.
        """
        current_time = now or datetime.now(timezone.utc)
        lat = query.latitude
        lon = query.longitude
        dest_lat = query.destination_latitude
        dest_lon = query.destination_longitude

        # 1. Collect multi-domain evidence from existing backend layers
        weather_data = self.collector.get_weather_evidence(db, lat, lon, current_time=current_time)
        marine_data = self.collector.get_marine_evidence(db, lat, lon, current_time=current_time)
        eo_data = self.collector.get_earth_observation_evidence(db, lat, lon, current_time=current_time)
        geo_data = self.collector.get_geospatial_evidence(db, lat, lon, dest_lat, dest_lon)
        safety_data = self.collector.get_disaster_safety_evidence(db, lat, lon, radius_km=50.0, current_time=current_time)
        operations_data = self.collector.get_operations_evidence(
            db=db,
            origin_lat=lat,
            origin_lon=lon,
            destination_lat=dest_lat,
            destination_lon=dest_lon,
            speed_kmh=20.0,
            current_time=current_time,
        )

        # 2. Fuse evidence into standardized items
        evidence_items = self.reasoning.fuse_evidence(
            weather=weather_data,
            marine=marine_data,
            eo=eo_data,
            safety=safety_data,
            geospatial=geo_data,
            operations=operations_data,
        )

        # 3. Evaluate deterministic suitability, safety override, risk level, and warnings
        suitability, diag_reasons, risk_level, warnings_and_overrides = self.reasoning.evaluate_suitability(
            evidence=evidence_items,
            safety=safety_data,
            geospatial=geo_data,
            target_species=query.target_species,
            vessel_type=query.vessel_type,
        )

        # 4. Evaluate confidence level
        confidence = self.reasoning.evaluate_confidence(
            evidence=evidence_items,
            safety=safety_data,
            suitability_status=suitability.status,
        )

        # 5. Build domain contributions, key conditions, and data quality metrics
        domain_contributions = self.reasoning.build_domain_contributions(
            weather=weather_data,
            marine=marine_data,
            eo=eo_data,
            safety=safety_data,
            geospatial=geo_data,
            operations=operations_data,
        )
        key_conditions = self.reasoning.build_key_conditions(
            weather=weather_data,
            marine=marine_data,
            eo=eo_data,
        )
        data_quality_info, overall_freshness = self.reasoning.build_data_quality(evidence_items)

        # 6. Generate actionable recommendation narrative and explanation
        recommendation_text = generate_deterministic_narrative(
            suitability_status=suitability.status,
            safety_status=safety_data.get("status", "UNKNOWN"),
            reasons=diag_reasons,
            confidence_level=confidence.level,
            target_species=query.target_species,
            vessel_type=query.vessel_type,
        )
        explanation_text = " | ".join(diag_reasons) if diag_reasons else "Standard operational baseline conditions."

        # 7. PFZ metadata (Strictly UNAVAILABLE unless official INCOIS feed connected)
        pfz_info = PFZAssessment(
            status="UNAVAILABLE",
            zones=[],
            notes="Official INCOIS Potential Fishing Zone (PFZ) advisory data is currently unavailable for this sector; assessment relies on direct satellite SST, ocean current, and chlorophyll indicators.",
        )

        safety_status_val = safety_data.get("status", "UNKNOWN")

        return FishingAssessment(
            query=query.model_dump(),
            location={"latitude": lat, "longitude": lon},
            overall_suitability=suitability,
            fishing_suitability=suitability,
            safety_status=safety_status_val,
            risk_level=risk_level,
            confidence=confidence,
            key_conditions=key_conditions,
            evidence_used=evidence_items,
            evidence=evidence_items,
            domain_contributions=domain_contributions,
            agent_contributions=domain_contributions,
            recommendation=recommendation_text,
            explanation=explanation_text,
            reasons=diag_reasons,
            data_quality=data_quality_info,
            freshness=overall_freshness,
            warnings_and_overrides=warnings_and_overrides,
            warnings=warnings_and_overrides,
            pfz=pfz_info,
            marine_conditions=marine_data,
            weather=weather_data,
            earth_observation=eo_data,
            safety=safety_data,
            operations=operations_data,
            generated_at=current_time,
        )

    def compare(
        self,
        db: Session,
        query: LocationComparisonQuery,
        now: Optional[datetime] = None,
    ) -> LocationComparisonResponse:
        """
        Compares two distinct fishing locations using identical evidence frameworks.
        """
        current_time = now or datetime.now(timezone.utc)

        query_a = FishingQuery(
            latitude=query.location_a.latitude,
            longitude=query.location_a.longitude,
            date=query.date,
            departure_time=query.departure_time,
            vessel_type=query.vessel_type,
            target_species=query.target_species,
            language=query.language,
        )
        query_b = FishingQuery(
            latitude=query.location_b.latitude,
            longitude=query.location_b.longitude,
            date=query.date,
            departure_time=query.departure_time,
            vessel_type=query.vessel_type,
            target_species=query.target_species,
            language=query.language,
        )

        assessment_a = self.assess(db, query_a, now=current_time)
        assessment_b = self.assess(db, query_b, now=current_time)

        name_a = query.location_a.name or f"Location A ({query.location_a.latitude}, {query.location_a.longitude})"
        name_b = query.location_b.name or f"Location B ({query.location_b.latitude}, {query.location_b.longitude})"

        return self.reasoning.compare_locations(
            assessment_a=assessment_a,
            assessment_b=assessment_b,
            name_a=name_a,
            name_b=name_b,
        )

    def what_if(
        self,
        db: Session,
        query: WhatIfQuery,
        now: Optional[datetime] = None,
    ) -> WhatIfResponse:
        """
        Recomputes operational evidence across modified parameters to evaluate what-if scenarios.
        """
        current_time = now or datetime.now(timezone.utc)

        # 1. Evaluate baseline assessment
        baseline_assessment = self.assess(db, query.baseline_query, now=current_time)

        # 2. Build scenario query by overlaying modifications
        scenario_data = query.baseline_query.model_dump()
        changes: List[str] = []

        if query.modified_latitude is not None:
            scenario_data["latitude"] = query.modified_latitude
            changes.append(f"Latitude: {query.baseline_query.latitude} -> {query.modified_latitude}")
        if query.modified_longitude is not None:
            scenario_data["longitude"] = query.modified_longitude
            changes.append(f"Longitude: {query.baseline_query.longitude} -> {query.modified_longitude}")
        if query.modified_departure_time is not None:
            scenario_data["departure_time"] = query.modified_departure_time
            changes.append(f"Departure Time: {query.baseline_query.departure_time} -> {query.modified_departure_time}")
        if query.modified_date is not None:
            scenario_data["date"] = query.modified_date
            changes.append(f"Date: {query.baseline_query.date} -> {query.modified_date}")
        if query.modified_duration_hours is not None:
            scenario_data["duration_hours"] = query.modified_duration_hours
            changes.append(f"Duration: {query.baseline_query.duration_hours}h -> {query.modified_duration_hours}h")

        scenario_query = FishingQuery(**scenario_data)

        # 3. Evaluate scenario assessment with updated parameters
        scenario_assessment = self.assess(db, scenario_query, now=current_time)

        # 4. Compare baseline and scenario
        return self.reasoning.evaluate_what_if(
            baseline=baseline_assessment,
            scenario=scenario_assessment,
            changes=changes if changes else ["No specific parameters modified"],
            scenario_description=query.scenario_description,
        )
