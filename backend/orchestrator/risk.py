from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from orchestrator.evidence import FusedEvidence
from schemas.agent_contract import (
    AgentResult,
    AgentStatus,
    DecisionType,
    EvidenceItem,
    ObservationType,
)


class RiskDecisionEngine:
    """
    Deterministic Multi-Tier Decision Engine for OCEANIS.
    Evaluates fused evidence strictly according to the hierarchical safety priority:
    
    1. OFFICIAL WARNING / RESTRICTION (Highest Authority - Strict Veto)
           ↓
    2. CRITICAL SAFETY HAZARD (Physical Sea-State / Storm Danger)
           ↓
    3. INSUFFICIENT CRITICAL EVIDENCE (Data Gaps / Unresolved Ocean Telemetry)
           ↓
    4. MARINE CONDITIONS (Wind, Swell, Currents, Sea State)
           ↓
    5. OPERATIONAL CONDITIONS (Transit, Refuges, Vessel Constraints)
           ↓
    6. OTHER SUPPORTING EVIDENCE (EO Indices, PFZ Dynamics)
    """

    # Thresholds for physical marine risk
    CRITICAL_WAVE_HEIGHT_M = 3.5
    CAUTION_WAVE_HEIGHT_M = 2.0

    CRITICAL_WIND_SPEED_KMH = 55.0
    CAUTION_WIND_SPEED_KMH = 35.0

    CRITICAL_CURRENT_SPEED_KMH = 6.0
    CAUTION_CURRENT_SPEED_KMH = 3.5

    def evaluate(
        self,
        fused_evidence: FusedEvidence,
        agent_results: Dict[str, AgentResult],
        is_inland: bool = False,
        intent: Optional[str] = None,
    ) -> Tuple[str, str, List[str], List[str]]:
        """
        Executes deterministic multi-tier risk evaluation.
        Returns:
            decision: "Suitable", "Caution", "Not Recommended", "Insufficient Evidence"
            risk_level: "LOW", "MODERATE", "HIGH", "CRITICAL", "UNKNOWN"
            risk_factors: List of identified risk triggers
            recommendation_points: Concrete operational guidelines
        """
        risk_factors: List[str] = []
        recommendation_points: List[str] = []

        # -------------------------------------------------------------
        # TIER 0: INLAND PROTECTION CHECK
        # -------------------------------------------------------------
        if is_inland:
            return (
                DecisionType.INSUFFICIENT_EVIDENCE.value,
                "UNKNOWN",
                ["Selected coordinates are inland; marine navigation and ocean telemetry are not applicable."],
                ["Please select a coastal port or offshore marine location."],
            )

        # -------------------------------------------------------------
        # TIER 1: OFFICIAL WARNINGS & SPATIAL RESTRICTIONS (VETO POWER)
        # -------------------------------------------------------------
        official_warnings = [
            it for it in fused_evidence.evidence_items
            if it.observation_type == ObservationType.OFFICIAL_WARNING.value
            or "warning" in it.parameter.lower()
            or "alert" in it.parameter.lower()
        ]

        # Check for active cyclone / severe storm alerts
        disaster_result = agent_results.get("disaster_safety")
        if disaster_result and disaster_result.warnings:
            for w in disaster_result.warnings:
                if any(k in w.upper() for k in ("CYCLONE", "STORM", "RED ALERT", "ORANGE ALERT", "EMERGENCY", "BLOCKED")):
                    risk_factors.append(f"Official Warning: {w}")

        # Check for spatial military / restricted exclusion zones
        geospatial_result = agent_results.get("geospatial_navigation")
        if geospatial_result and geospatial_result.warnings:
            for w in geospatial_result.warnings:
                if any(k in w.upper() for k in ("RESTRICTED", "EXCLUSION", "MILITARY", "PROHIBITED", "BARRIER")):
                    risk_factors.append(f"Spatial Restriction: {w}")

        if risk_factors:
            recommendation_points.append("All maritime operations must be suspended due to official government alerts or spatial exclusion.")
            return (
                DecisionType.NOT_RECOMMENDED.value,
                "CRITICAL",
                risk_factors,
                recommendation_points,
            )

        # -------------------------------------------------------------
        # TIER 2: CRITICAL PHYSICAL SAFETY HAZARDS
        # -------------------------------------------------------------
        for item in fused_evidence.evidence_items:
            # Wave height check
            if "wave_height" in item.parameter.lower() and isinstance(item.value, (int, float)):
                if item.value >= self.CRITICAL_WAVE_HEIGHT_M:
                    risk_factors.append(f"Dangerous Wave Height: {item.value} m (Critical threshold >= {self.CRITICAL_WAVE_HEIGHT_M} m)")
            # Wind speed check
            elif "wind_speed" in item.parameter.lower() and isinstance(item.value, (int, float)):
                if item.value >= self.CRITICAL_WIND_SPEED_KMH:
                    risk_factors.append(f"Dangerous Wind Speed: {item.value} km/h (Critical threshold >= {self.CRITICAL_WIND_SPEED_KMH} km/h)")
            # Current speed check
            elif "current" in item.parameter.lower() and "speed" in item.parameter.lower() and isinstance(item.value, (int, float)):
                if item.value >= self.CRITICAL_CURRENT_SPEED_KMH:
                    risk_factors.append(f"Dangerous Ocean Current: {item.value} km/h (Critical threshold >= {self.CRITICAL_CURRENT_SPEED_KMH} km/h)")

        if risk_factors:
            recommendation_points.append("Hazardous physical sea state detected. Postpone small-craft operations and non-essential transits.")
            return (
                DecisionType.NOT_RECOMMENDED.value,
                "CRITICAL",
                risk_factors,
                recommendation_points,
            )

        # -------------------------------------------------------------
        # TIER 3: INSUFFICIENT CRITICAL EVIDENCE CHECK
        # -------------------------------------------------------------
        # If we have 0 real data items or critical parameters are missing
        if fused_evidence.real_data_count == 0 or fused_evidence.overall_evidence_quality == "INSUFFICIENT":
            return (
                DecisionType.INSUFFICIENT_EVIDENCE.value,
                "UNKNOWN",
                ["Insufficient verified observations or active forecast telemetry to safely authorize operation."],
                ["Verify local harbor radar and maritime VHF broadcasts before departure."],
            )

        # -------------------------------------------------------------
        # TIER 4: MODERATE MARINE CONDITIONS (CAUTION TIER)
        # -------------------------------------------------------------
        caution_factors: List[str] = []
        for item in fused_evidence.evidence_items:
            if "wave_height" in item.parameter.lower() and isinstance(item.value, (int, float)):
                if self.CAUTION_WAVE_HEIGHT_M <= item.value < self.CRITICAL_WAVE_HEIGHT_M:
                    caution_factors.append(f"Moderate Sea State: Wave height {item.value} m ({self.CAUTION_WAVE_HEIGHT_M}-{self.CRITICAL_WAVE_HEIGHT_M} m caution band)")
            elif "wind_speed" in item.parameter.lower() and isinstance(item.value, (int, float)):
                if self.CAUTION_WIND_SPEED_KMH <= item.value < self.CRITICAL_WIND_SPEED_KMH:
                    caution_factors.append(f"Fresh Breeze: Wind speed {item.value} km/h ({self.CAUTION_WIND_SPEED_KMH}-{self.CRITICAL_WIND_SPEED_KMH} km/h caution band)")
            elif "current" in item.parameter.lower() and "speed" in item.parameter.lower() and isinstance(item.value, (int, float)):
                if self.CAUTION_CURRENT_SPEED_KMH <= item.value < self.CRITICAL_CURRENT_SPEED_KMH:
                    caution_factors.append(f"Strong Tidal Current: {item.value} km/h ({self.CAUTION_CURRENT_SPEED_KMH}-{self.CAUTION_CURRENT_SPEED_KMH} km/h caution band)")

        # Check for marine protected area proximity
        if geospatial_result and geospatial_result.warnings:
            for w in geospatial_result.warnings:
                if any(k in w.upper() for k in ("PROTECTED", "SANCTUARY", "BUFFER", "ECOLOGICALLY SENSITIVE")):
                    caution_factors.append(f"Environmental Buffer: {w}")

        if caution_factors:
            recommendation_points.append("Conditions permissible with heightened operational vigilance and active safety gear.")
            return (
                DecisionType.CAUTION.value,
                "MODERATE",
                caution_factors,
                recommendation_points,
            )

        # -------------------------------------------------------------
        # TIER 5: FAVORABLE OPERATIONAL & SUPPORTING CONDITIONS
        # -------------------------------------------------------------
        recommendation_points.append("All observed marine, atmospheric, and spatial parameters are within normal operational clearance thresholds.")
        return (
            DecisionType.SUITABLE.value,
            "LOW",
            ["Calm to moderate sea state", "No active official warnings", "Clear spatial passage"],
            recommendation_points,
        )
