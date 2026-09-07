from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from agents.marine_conditions.collector import MarineConditionsDataCollector
from agents.marine_conditions.reasoning import MarineConditionsReasoningEngine
from agents.marine_conditions.schemas import (
    MarineConditionsAssessmentResponse,
    MarineConditionsQuery,
    MarineConditionsSummary,
)


class MarineConditionsIntelligenceAgent:
    """
    OCEANIS Marine Conditions Intelligence Domain Agent.
    Owns the complete marine-conditions domain:
    - Wave dynamics (height, direction, period)
    - Swell dynamics (height, direction, period)
    - Wind-wave metrics (height, direction, period)
    - Ocean current velocity and direction
    - Sea Surface Temperature (SST)
    - Marine data type, quality, and freshness
    """

    def __init__(
        self,
        data_collector: Optional[MarineConditionsDataCollector] = None,
        reasoning_engine: Optional[MarineConditionsReasoningEngine] = None,
    ):
        self.collector = data_collector or MarineConditionsDataCollector()
        self.reasoning = reasoning_engine or MarineConditionsReasoningEngine()

    def assess(
        self,
        db: Session,
        query: MarineConditionsQuery,
        now: Optional[datetime] = None,
    ) -> MarineConditionsAssessmentResponse:
        """
        Gathers localized marine oceanographic telemetry and applies deterministic
        reasoning to assess sea state, physical risks, confidence, and provenance evidence.
        """
        current_time = now or datetime.now(timezone.utc)
        lat = query.latitude
        lon = query.longitude

        # 1. Retrieve structured marine telemetry from Marine Conditions layer
        marine_data = self.collector.get_marine_evidence(
            db=db,
            latitude=lat,
            longitude=lon,
            current_time=current_time,
        )

        # 2. Perform deterministic marine condition and sea state reasoning
        (
            sea_state,
            risk_level,
            confidence,
            data_freshness,
            evidence_items,
            warnings,
            recommendation,
            explanation,
        ) = self.reasoning.assess_conditions(marine_data=marine_data)

        # 3. Format structured conditions summary
        conditions_summary: Dict[str, Any] = {}
        if marine_data:
            conditions_summary = {
                "wave_height_m": marine_data.get("wave_height_m"),
                "wave_direction_deg": marine_data.get("wave_direction_deg"),
                "wave_period_s": marine_data.get("wave_period_s"),
                "swell_wave_height_m": marine_data.get("swell_wave_height_m"),
                "swell_wave_direction_deg": marine_data.get("swell_wave_direction_deg"),
                "swell_wave_period_s": marine_data.get("swell_wave_period_s"),
                "wind_wave_height_m": marine_data.get("wind_wave_height_m"),
                "wind_wave_direction_deg": marine_data.get("wind_wave_direction_deg"),
                "wind_wave_period_s": marine_data.get("wind_wave_period_s"),
                "ocean_current_velocity_kmh": marine_data.get("ocean_current_velocity_kmh"),
                "ocean_current_direction_deg": marine_data.get("ocean_current_direction_deg"),
                "sea_surface_temperature_c": marine_data.get("sea_surface_temperature_c"),
                "observed_at": marine_data.get("observed_at"),
                "source": marine_data.get("source"),
                "data_type": marine_data.get("data_type"),
                "quality_flag": marine_data.get("quality_flag"),
            }

        return MarineConditionsAssessmentResponse(
            agent="marine_conditions",
            location={"latitude": lat, "longitude": lon},
            conditions=conditions_summary,
            sea_state=sea_state,
            risk_level=risk_level,
            confidence=confidence,
            data_freshness=data_freshness,
            evidence=evidence_items,
            warnings=warnings,
            recommendation=recommendation,
            explanation=explanation,
            generated_at=current_time,
        )
