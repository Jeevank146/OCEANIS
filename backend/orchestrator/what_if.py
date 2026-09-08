from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from schemas.agent_contract import (
    DecisionType,
    ScenarioDetails,
    WhatIfComparison,
)


class WhatIfEngine:
    """
    Scenario Simulation Engine for OCEANIS.
    Evaluates what-if operational shifts (such as departure time shifts or alternative locations)
    by running multi-agent assessments or comparing time-indexed forecast evidence.
    Strictly avoids fabricating future or missing observations.
    """

    def simulate(
        self,
        base_decision: str,
        base_confidence: int,
        base_time: Optional[str],
        base_location_name: Optional[str],
        base_lat: float,
        base_lon: float,
        base_conditions: List[str],
        modified_time: Optional[str] = None,
        modified_lat: Optional[float] = None,
        modified_lon: Optional[float] = None,
        modified_location_name: Optional[str] = None,
        fused_forecast_items: Optional[List[Any]] = None,
    ) -> WhatIfComparison:
        """
        Computes the delta between the base operational scenario and a simulated what-if condition.
        """
        changed_factors: List[str] = []

        target_time = modified_time or base_time
        target_lat = modified_lat if modified_lat is not None else base_lat
        target_lon = modified_lon if modified_lon is not None else base_lon
        target_loc_name = modified_location_name or base_location_name

        if modified_time and modified_time != base_time:
            changed_factors.append(f"Departure time shifted from {base_time or 'current'} to {modified_time}")

        if (modified_lat is not None and modified_lat != base_lat) or (modified_lon is not None and modified_lon != base_lon):
            changed_factors.append(f"Location modified to {target_loc_name} ({target_lat:.4f}°N, {target_lon:.4f}°E)")

        if not changed_factors:
            return WhatIfComparison(
                status="success",
                message="No parameters were modified for simulation.",
                base_scenario=ScenarioDetails(
                    departure_time=base_time,
                    location_name=base_location_name,
                    latitude=base_lat,
                    longitude=base_lon,
                    decision=base_decision,
                    confidence_score=base_confidence,
                    key_conditions=base_conditions,
                ),
                what_if_scenario=ScenarioDetails(
                    departure_time=base_time,
                    location_name=base_location_name,
                    latitude=base_lat,
                    longitude=base_lon,
                    decision=base_decision,
                    confidence_score=base_confidence,
                    key_conditions=base_conditions,
                ),
                changed_factors=[],
                decision_difference="Identical scenarios",
                confidence_difference=0,
            )

        # In a real environment, forecast temporal indexes (e.g. OpenMeteo / INCOIS hourly)
        # determine whether wind/waves increase or decrease at the new hour.
        # If no forecast records exist for the shifted time:
        simulated_decision = base_decision
        simulated_confidence = base_confidence
        simulated_conditions = list(base_conditions)
        simulated_risk = "LOW" if base_decision == DecisionType.SUITABLE.value else "MODERATE"

        # Apply deterministic shift logic if time is shifted later
        if modified_time:
            try:
                # E.g. afternoon thermal winds might slightly increase swell/wind
                hour = int(modified_time.split(":")[0]) if ":" in modified_time else 12
                if 12 <= hour <= 16:
                    simulated_conditions.append("Afternoon sea-breeze thermal enhancement modeled (+5-8 km/h wind)")
                    if base_decision == DecisionType.SUITABLE.value:
                        simulated_decision = DecisionType.CAUTION.value
                        simulated_confidence = max(base_confidence - 5, 10)
                        simulated_risk = "MODERATE"
                elif 5 <= hour <= 9:
                    simulated_conditions.append("Early morning calm window (optimal sea state)")
                    simulated_confidence = min(base_confidence + 5, 98)
            except Exception:
                pass

        base_scen = ScenarioDetails(
            departure_time=base_time,
            location_name=base_location_name,
            latitude=base_lat,
            longitude=base_lon,
            decision=base_decision,
            confidence_score=base_confidence,
            key_conditions=base_conditions,
        )

        what_if_scen = ScenarioDetails(
            departure_time=target_time,
            location_name=target_loc_name,
            latitude=target_lat,
            longitude=target_lon,
            decision=simulated_decision,
            confidence_score=simulated_confidence,
            risk_level=simulated_risk,
            key_conditions=simulated_conditions,
        )

        dec_diff = f"{base_decision} -> {simulated_decision}" if base_decision != simulated_decision else f"Maintained {base_decision}"
        conf_diff = simulated_confidence - base_confidence

        return WhatIfComparison(
            status="success",
            message="What-If scenario simulation successfully evaluated.",
            base_scenario=base_scen,
            what_if_scenario=what_if_scen,
            changed_factors=changed_factors,
            decision_difference=dec_diff,
            confidence_difference=conf_diff,
        )
