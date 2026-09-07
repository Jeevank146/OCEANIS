from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from agents.earth_observation.collector import EarthObservationDataCollector
from agents.earth_observation.reasoning import EarthObservationReasoningEngine
from agents.earth_observation.schemas import (
    EarthObservationAssessmentResponse,
    EarthObservationQuery,
)


class EarthObservationIntelligenceAgent:
    """
    OCEANIS Earth Observation Intelligence Domain Agent.
    Owns the satellite and Earth-observation intelligence domain:
    - Satellite observations (optical, thermal, multi-spectral)
    - Sea Surface Temperature (SST) & thermal front dynamics
    - Ocean colour & chlorophyll-a biological productivity indicators
    - Cloud cover & sensor optical observability
    - Temporal trend comparison across satellite passes
    - Data quality, freshness, and full satellite/sensor provenance
    """

    def __init__(
        self,
        data_collector: Optional[EarthObservationDataCollector] = None,
        reasoning_engine: Optional[EarthObservationReasoningEngine] = None,
    ):
        self.collector = data_collector or EarthObservationDataCollector()
        self.reasoning = reasoning_engine or EarthObservationReasoningEngine()

    def assess(
        self,
        db: Session,
        query: EarthObservationQuery,
        now: Optional[datetime] = None,
    ) -> EarthObservationAssessmentResponse:
        """
        Gathers localized satellite Earth Observation telemetry, performs temporal
        trend comparison, and applies deterministic reasoning to produce structured
        EO intelligence, bio-optical indicators, and provenance evidence.
        """
        current_time = now or datetime.now(timezone.utc)
        lat = query.latitude
        lon = query.longitude

        # 1. Retrieve latest satellite Earth Observation telemetry
        current_data = self.collector.get_earth_observation_evidence(
            db=db,
            latitude=lat,
            longitude=lon,
            current_time=current_time,
        )

        # 2. Retrieve prior historical observation for temporal comparison
        previous_data = None
        if current_data and current_data.get("observed_at_dt"):
            previous_data = self.collector.get_previous_observation(
                db=db,
                latitude=lat,
                longitude=lon,
                current_observed_at=current_data["observed_at_dt"],
            )

        # 3. Perform deterministic reasoning and indicator evaluation
        (
            observations_dict,
            indicators,
            temporal_comp,
            observation_quality,
            data_freshness,
            confidence,
            evidence_items,
            warnings,
            recommendation,
            explanation,
        ) = self.reasoning.assess_conditions(
            current_data=current_data,
            previous_data=previous_data,
        )

        return EarthObservationAssessmentResponse(
            agent="earth_observation",
            location={"latitude": lat, "longitude": lon},
            observations=observations_dict,
            indicators=indicators.model_dump(),
            temporal_comparison=temporal_comp,
            observation_quality=observation_quality,
            data_freshness=data_freshness,
            confidence=confidence,
            evidence=evidence_items,
            warnings=warnings,
            recommendation=recommendation,
            explanation=explanation,
            generated_at=current_time,
        )
