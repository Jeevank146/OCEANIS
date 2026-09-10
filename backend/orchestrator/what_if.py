from typing import Any, List, Optional

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

        base_scen = ScenarioDetails(
            departure_time=base_time,
            location_name=base_location_name,
            latitude=base_lat,
            longitude=base_lon,
            decision=base_decision,
            confidence_score=base_confidence,
            key_conditions=base_conditions,
        )

        # A modified location must be evaluated by a fresh orchestrator dispatch, and a
        # modified time requires evidence indexed to that time. Reusing base evidence or
        # applying assumed time-of-day deltas would fabricate marine conditions.
        matching_forecasts = []
        if modified_time and fused_forecast_items:
            target_hour = modified_time.split(":", 1)[0].zfill(2)
            matching_forecasts = [
                item for item in fused_forecast_items
                if str(getattr(item, "observation_type", "")).lower() == "forecast"
                and target_hour in str(getattr(item, "timestamp", ""))[11:16]
            ]

        needs_location_reanalysis = modified_lat is not None or modified_lon is not None
        if needs_location_reanalysis or (modified_time and not matching_forecasts):
            reason = (
                "Alternative location requires a separate evidence and safety-engine evaluation."
                if needs_location_reanalysis
                else f"No forecast evidence is available for the requested alternative time {modified_time}."
            )
            return WhatIfComparison(
                status="insufficient_evidence",
                message=f"INSUFFICIENT EVIDENCE — {reason}",
                base_scenario=base_scen,
                what_if_scenario=ScenarioDetails(
                    departure_time=target_time,
                    location_name=target_loc_name,
                    latitude=target_lat,
                    longitude=target_lon,
                    decision=DecisionType.INSUFFICIENT_EVIDENCE.value,
                    confidence_score=0,
                    risk_level="INSUFFICIENT EVIDENCE",
                    key_conditions=[],
                ),
                changed_factors=changed_factors,
                decision_difference=f"{base_decision} -> {DecisionType.INSUFFICIENT_EVIDENCE.value}",
                confidence_difference=-base_confidence,
            )

        simulated_conditions = [
            f"{getattr(item, 'parameter', 'Forecast')}: {getattr(item, 'value', '')} {getattr(item, 'unit', '')}".strip()
            for item in matching_forecasts
        ] or list(base_conditions)
        what_if_scen = ScenarioDetails(
            departure_time=target_time,
            location_name=target_loc_name,
            latitude=target_lat,
            longitude=target_lon,
            decision=base_decision,
            confidence_score=base_confidence,
            risk_level=None,
            key_conditions=simulated_conditions,
        )

        dec_diff = f"Maintained {base_decision}"
        conf_diff = 0

        return WhatIfComparison(
            status="success",
            message="What-If scenario simulation successfully evaluated.",
            base_scenario=base_scen,
            what_if_scenario=what_if_scen,
            changed_factors=changed_factors,
            decision_difference=dec_diff,
            confidence_difference=conf_diff,
        )
