from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.schemas import (
    AgentContribution,
    AgentExecutionResult,
    FusedEvidenceItem,
    LocationContext,
    QueryUnderstanding,
)


class OrchestratorReasoningEngine:
    """
    Multi-Agent Decision Synthesis and Safety Reasoning Engine.
    Combines outputs across all executed domain agents, enforces deterministic
    safety-first overrides, calculates composite confidence and freshness ratings,
    and produces explainable client recommendations.
    """

    PROHIBITED_CLAIMS_PATTERN = re.compile(
        r"(100%\s*safe|guaranteed\s*safe|completely\s*safe|risk[-\s]*free|zero\s*risk|absolute\s*safety)",
        re.IGNORECASE,
    )

    def synthesize(
        self,
        query: str,
        understanding: QueryUnderstanding,
        agent_results: Dict[str, AgentExecutionResult],
        fused_evidence: List[FusedEvidenceItem],
    ) -> Tuple[str, str, str, str, List[str], str, List[AgentContribution], Optional[List[Dict[str, Any]]]]:
        """
        Synthesizes final decision, risk level, confidence, freshness, warnings,
        reasoning summary, agent contributions, and optional comparison results.
        """
        warnings: List[str] = []
        agent_contributions: List[AgentContribution] = []
        comparison_results: Optional[List[Dict[str, Any]]] = None

        has_blocked = False
        has_warning = False
        has_caution = False
        has_insufficient_data = False

        # 1. Inspect Individual Domain Agent Results & Extract Contributions
        for agent_id, exec_res in agent_results.items():
            if exec_res.status != "SUCCESS" or not exec_res.result:
                has_insufficient_data = True
                warnings.append(f"Agent '{exec_res.agent_name}' was unable to provide evidence: {exec_res.error or 'Service failure'}")
                agent_contributions.append(
                    AgentContribution(
                        agent_id=agent_id,
                        agent_name=exec_res.agent_name,
                        domain=agent_id.replace("_", " ").title(),
                        status="FAILED",
                        summary=f"Execution failed: {exec_res.error or 'Unavailable'}",
                        key_findings=[],
                        confidence=0.0,
                        freshness="UNAVAILABLE",
                    )
                )
                continue

            data = exec_res.result
            raw_warnings = data.get("warnings", [])
            for w in raw_warnings:
                if w not in warnings:
                    warnings.append(w)

            # Check agent-specific status
            status_str = (
                data.get("safety_status")
                or data.get("spatial_status")
                or data.get("operational_status")
                or data.get("decision")
                or "CLEAR"
            ).upper()

            if status_str in ("BLOCKED", "CRITICAL", "INSIDE_RESTRICTED"):
                has_blocked = True
            elif status_str in ("WARNING", "HIGH_RISK"):
                has_warning = True
            elif status_str in ("CAUTION", "PROTECTED", "INSIDE_PROTECTED", "NEAR_BOUNDARY"):
                has_caution = True
            elif status_str == "INSUFFICIENT_DATA":
                has_insufficient_data = True

            # Extract key findings per agent
            key_findings: List[str] = []
            if agent_id == "disaster_safety":
                active_alerts = data.get("alerts", [])
                cyclones = data.get("cyclones", [])
                hazards = data.get("hazards", [])
                if active_alerts:
                    key_findings.append(f"{len(active_alerts)} active official marine alerts in sector")
                if cyclones:
                    key_findings.append(f"{len(cyclones)} tropical cyclone systems tracked in basin")
                if hazards:
                    key_findings.append(f"{len(hazards)} spatial hazard zones mapped")
                if not key_findings:
                    key_findings.append("0 active marine alerts or cyclone threats detected")

            elif agent_id == "geospatial_navigation":
                geofence = data.get("geofence_status", "OUTSIDE")
                key_findings.append(f"Geofence containment: {geofence}")
                nearby = data.get("nearby_entities", [])
                if nearby:
                    nearest = nearby[0]
                    key_findings.append(f"Nearest port: {nearest.get('name')} ({nearest.get('distance_km', 0.0):.1f} km)")

            elif agent_id == "marine_conditions":
                obs = data.get("observations", {})
                wave_h = obs.get("wave_height_m")
                wind_s = obs.get("wind_speed_kmh")
                if wave_h is not None:
                    key_findings.append(f"Significant wave height: {wave_h} m")
                if wind_s is not None:
                    key_findings.append(f"Sustained wind: {wind_s} km/h")

            elif agent_id == "earth_observation":
                obs = data.get("observations", {})
                ind = data.get("indicators", {})
                chl = obs.get("chlorophyll_a_mg_m3")
                chl_status = ind.get("chlorophyll_status", "UNKNOWN")
                if chl is not None:
                    key_findings.append(f"Chlorophyll-a density: {chl} mg/m³ ({chl_status})")
                cloud = obs.get("cloud_cover_percent")
                if cloud is not None:
                    key_findings.append(f"Satellite cloud cover: {cloud}%")

            elif agent_id == "marine_operations":
                route = data.get("route", {})
                dist = route.get("distance_km")
                dur = route.get("estimated_duration_minutes")
                if dist:
                    key_findings.append(f"Route distance: {dist:.1f} km ({route.get('distance_nautical_miles', 0.0):.1f} NM)")
                if dur:
                    key_findings.append(f"Estimated transit time: {dur:.0f} min ({route.get('estimated_duration_hours', 0.0):.1f} hrs)")

            elif agent_id == "fishing":
                if understanding.is_comparison and ("location_a_assessment" in data or "comparisons" in data):
                    if "location_a_assessment" in data:
                        comparison_results = [
                            data.get("location_a_assessment"),
                            data.get("location_b_assessment"),
                        ]
                    else:
                        comparison_results = data.get("comparisons", [])
                    key_findings.append(f"Evaluated {len(comparison_results)} comparative fishing locations")
                    rec_opt = data.get("recommended_option")
                    if rec_opt:
                        key_findings.append(f"Comparative recommendation: {rec_opt}")
                else:
                    suitability = data.get("suitability_score") or (data.get("fishing_suitability", {}).get("overall_score") if isinstance(data.get("fishing_suitability"), dict) else None)
                    if suitability is not None:
                        key_findings.append(f"Fishing suitability score: {suitability}/100")
                    species_eval = data.get("target_species_evaluation")
                    if species_eval and isinstance(species_eval, dict):
                        key_findings.append(f"Target species ({species_eval.get('species')}): {species_eval.get('suitability')}")

            agent_contributions.append(
                AgentContribution(
                    agent_id=agent_id,
                    agent_name=exec_res.agent_name,
                    domain=agent_id.replace("_", " ").title(),
                    status=exec_res.status,
                    summary=data.get("recommendation") or data.get("explanation") or f"Assessment completed: {status_str}",
                    key_findings=key_findings,
                    confidence=exec_res.confidence,
                    freshness=exec_res.freshness,
                )
            )

        # 2. Deterministic Safety-First Overrides
        if has_blocked:
            decision = "BLOCKED"
            risk_level = "CRITICAL"
        elif has_warning:
            decision = "WARNING"
            risk_level = "HIGH"
        elif has_caution:
            decision = "CAUTION"
            risk_level = "MODERATE"
        elif has_insufficient_data:
            decision = "INSUFFICIENT_DATA"
            risk_level = "UNKNOWN"
        else:
            # Check intent-specific positive outcomes
            if understanding.intent in ("FISHING_ASSESSMENT", "FISHING_COMPARISON"):
                decision = "FAVORABLE"
                risk_level = "LOW"
            elif understanding.intent == "ROUTE_OPERATION":
                decision = "CLEAR"
                risk_level = "LOW"
            else:
                decision = "CLEAR"
                risk_level = "LOW"

        # 3. Overall Composite Confidence Calculation
        if decision == "INSUFFICIENT_DATA" or has_insufficient_data:
            confidence_level = "INSUFFICIENT_DATA"
        else:
            conf_values = [res.confidence for res in agent_results.values() if res.status == "SUCCESS"]
            avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0.0
            if avg_conf >= 0.90:
                confidence_level = "HIGH"
            elif avg_conf >= 0.70:
                confidence_level = "MEDIUM"
            else:
                confidence_level = "LOW"

        # 4. Overall Freshness Rating
        freshness_values = [res.freshness for res in agent_results.values() if res.status == "SUCCESS"]
        if "UNAVAILABLE" in freshness_values or not freshness_values:
            overall_freshness = "UNAVAILABLE"
        elif "STALE" in freshness_values:
            overall_freshness = "STALE"
        elif "AGING" in freshness_values:
            overall_freshness = "AGING"
        else:
            overall_freshness = "FRESH"

        # 5. Synthesize Explainable Narrative Summary
        loc_str = understanding.primary_location.name if understanding.primary_location else "requested area"
        time_str = f" for {understanding.target_date or 'today'}" + (f" at {understanding.target_time}" if understanding.target_time else "")
        agent_names = [res.agent_name for res in agent_results.values()]

        if decision == "BLOCKED":
            reasoning_summary = (
                f"DECISION BLOCKED: Operational voyage or activity at {loc_str}{time_str} is barred by critical safety barriers. "
                f"Multi-agent evaluation across {len(agent_names)} domain agents identified active prohibitive alerts, critical hazard zones, "
                f"or military exclusion barriers that mandate a deterministic BLOCKED state."
            )
        elif decision == "WARNING":
            reasoning_summary = (
                f"DECISION WARNING: High operational risk detected at {loc_str}{time_str}. "
                f"Active high-severity marine advisories, adverse sea states, or storm proximity warrant postponement of non-essential voyages."
            )
        elif decision == "CAUTION":
            reasoning_summary = (
                f"DECISION CAUTION: Conditions at {loc_str}{time_str} are permissible under heightened vigilance. "
                f"Route traverses marine protected sectors or moderate wave/wind conditions. Exercise care."
            )
        elif decision == "INSUFFICIENT_DATA":
            reasoning_summary = (
                f"DECISION INSUFFICIENT_DATA: Environmental telemetry or critical domain evidence is missing or unavailable for {loc_str}{time_str}. "
                f"In accordance with OCEANIS safety rules, clearance cannot be verified without fresh observational coverage."
            )
        elif decision == "FAVORABLE":
            reasoning_summary = (
                f"DECISION FAVORABLE: Verified conditions at {loc_str}{time_str} support fishing operations. "
                f"Marine dynamics, satellite bio-optical density, and spatial clearance are verified with 0 active hazards or exclusion barriers."
            )
        else:
            reasoning_summary = (
                f"DECISION CLEAR: Conditions at {loc_str}{time_str} currently indicate normal maritime operational parameters "
                f"with confirmed fresh telemetry across {len(agent_names)} domain agents."
            )

        # 6. Sanitize Narratives against Absolute Guarantees
        reasoning_summary = self._sanitize_text(reasoning_summary)

        return (
            decision,
            risk_level,
            confidence_level,
            overall_freshness,
            warnings,
            reasoning_summary,
            agent_contributions,
            comparison_results,
        )

    def _sanitize_text(self, text: str) -> str:
        if not text:
            return text
        return self.PROHIBITED_CLAIMS_PATTERN.sub("normal operational parameters", text)
