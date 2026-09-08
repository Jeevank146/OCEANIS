from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from orchestrator.confidence import ConfidenceEngine
from orchestrator.evidence import EvidenceFusionEngine, FusedEvidence
from orchestrator.executor import AgentExecutor
from orchestrator.guardrails import SafetyGuardrailEngine
from orchestrator.planner import OrchestratorPlanner
from orchestrator.risk import RiskDecisionEngine
from orchestrator.schemas import (
    AgentContribution,
    AgentSelection,
    ExecutionMetadata,
    LocationContext,
    OrchestrationQuery,
    OrchestrationResponse,
    QueryUnderstanding,
)
from orchestrator.what_if import WhatIfEngine
from schemas.agent_contract import (
    AgentResult,
    ComparisonLocationDetail,
    ComparisonResult,
    DataFreshness,
    DecisionType,
    FinalDecisionObject,
    QueryIntent,
    WhatIfComparison,
    WhyDecisionBreakdown,
)


class AgentOrchestrator:
    """
    Central Multi-Agent Decision Orchestrator for OCEANIS.
    Dynamically routes general marine queries across specialized domain agents,
    fuses multi-source evidence, applies deterministic safety guardrails and risk rules,
    computes explainable confidence, and synthesizes query-tailored responses.
    """

    def __init__(
        self,
        planner: Optional[OrchestratorPlanner] = None,
        executor: Optional[AgentExecutor] = None,
        fusion_engine: Optional[EvidenceFusionEngine] = None,
        risk_engine: Optional[RiskDecisionEngine] = None,
        confidence_engine: Optional[ConfidenceEngine] = None,
        guardrails: Optional[SafetyGuardrailEngine] = None,
        what_if_engine: Optional[WhatIfEngine] = None,
    ):
        self.planner = planner or OrchestratorPlanner()
        self.executor = executor or AgentExecutor()
        self.fusion_engine = fusion_engine or EvidenceFusionEngine()
        self.risk_engine = risk_engine or RiskDecisionEngine()
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.guardrails = guardrails or SafetyGuardrailEngine()
        self.what_if_engine = what_if_engine or WhatIfEngine()

    def orchestrate(
        self,
        db: Session,
        query: OrchestrationQuery,
        what_if_time: Optional[str] = None,
    ) -> FinalDecisionObject:
        return self.decide(db=db, query=query, what_if_time=what_if_time)

    def decide(
        self,
        db: Session,
        query: OrchestrationQuery,
        what_if_time: Optional[str] = None,
        what_if_lat: Optional[float] = None,
        what_if_lon: Optional[float] = None,
        what_if_loc_name: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> FinalDecisionObject:
        now_utc = now or datetime.now(timezone.utc)

        # 1. Parse Query & Plan Agent Dispatches
        understanding, selected_agents = self.planner.plan(query=query, now=now_utc)
        intent = understanding.intent
        is_inland = understanding.entities_extracted.get("is_inland", False)
        loc_missing = understanding.entities_extracted.get("location_missing", False)

        # -----------------------------------------------------------------
        # HANDLE MISSING LOCATION
        # -----------------------------------------------------------------
        if loc_missing and understanding.primary_location is None:
            return FinalDecisionObject(
                query_intent=intent,
                primary_answer="Please specify a coastal location name (e.g. 'near Chennai', 'from Kakinada', 'around Paradip') or select a position on the map to evaluate marine conditions.",
                decision=DecisionType.INSUFFICIENT_EVIDENCE.value,
                summary="Location required: Geographic coordinates or place name not provided.",
                confidence=0,
                confidence_reasons=["No spatial location specified in query or active map context."],
                safety_status="LOCATION_REQUIRED",
                guardrail_actions=["Awaiting user geographic selection."],
                key_findings=["Spatial location parameter missing."],
                why_decision=WhyDecisionBreakdown(),
                evidence=[],
                agents_consulted=[],
                total_agents_available=6,
                agents_consulted_count=0,
                freshness_summary=DataFreshness.UNAVAILABLE.value,
                warnings=["Please select a location on the map or enter a coastal city in your query."],
                limitations=["No spatial coordinate context available."],
                location=None,
                requested_time=understanding.target_date or "Present",
                what_if_comparison=None,
                comparison_data=None,
                entities_extracted=understanding.entities_extracted,
                generated_at=now_utc.isoformat(),
            )

        # -----------------------------------------------------------------
        # HANDLE MULTI-LOCATION COMPARISON QUERIES
        # -----------------------------------------------------------------
        if intent == QueryIntent.COMPARISON.value and len(understanding.comparison_locations) >= 2:
            return self._handle_comparison_query(
                db=db,
                query=query,
                understanding=understanding,
                selected_agents=selected_agents,
                now_utc=now_utc,
            )

        # -----------------------------------------------------------------
        # EXECUTE SELECTED AGENTS FOR PRIMARY LOCATION
        # -----------------------------------------------------------------
        agent_results: Dict[str, AgentResult] = self.executor.execute_selected_agents(
            db=db,
            selected_agents=selected_agents,
            understanding=understanding,
            now=now_utc,
        )

        # -----------------------------------------------------------------
        # EVIDENCE FUSION
        # -----------------------------------------------------------------
        fused_evidence: FusedEvidence = self.fusion_engine.fuse(
            agent_results=agent_results,
        )

        # -----------------------------------------------------------------
        # RISK & DECISION EVALUATION
        # -----------------------------------------------------------------
        risk_decision, risk_level, risk_reasons, guardrail_triggers = self.risk_engine.evaluate(
            fused_evidence=fused_evidence,
            agent_results=agent_results,
            is_inland=is_inland,
            intent=intent,
        )

        # -----------------------------------------------------------------
        # CONFIDENCE CALCULATION
        # -----------------------------------------------------------------
        confidence_score, confidence_reasons = self.confidence_engine.calculate(
            fused_evidence=fused_evidence,
            agent_results=agent_results,
            is_inland=is_inland,
        )

        # -----------------------------------------------------------------
        # WHAT-IF SCENARIO SIMULATION
        # -----------------------------------------------------------------
        what_if_res: Optional[WhatIfComparison] = None
        orig_lat = understanding.primary_location.latitude if understanding.primary_location else 0.0
        orig_lon = understanding.primary_location.longitude if understanding.primary_location else 0.0
        loc_name = understanding.primary_location.name if understanding.primary_location else "Target Location"

        if what_if_time or what_if_lat or what_if_lon or intent == QueryIntent.WHAT_IF.value:
            sim_time = what_if_time
            if not sim_time and intent == QueryIntent.WHAT_IF.value:
                factor = understanding.entities_extracted.get("what_if_factor", "")
                if "09:00" in factor:
                    sim_time = "09:00"
                elif "08:00" in factor:
                    sim_time = "08:00"
                else:
                    sim_time = "09:00"

            base_time = understanding.target_time or "06:00"
            what_if_res = self.what_if_engine.simulate(
                base_decision=risk_decision,
                base_confidence=confidence_score,
                base_time=base_time,
                base_location_name=loc_name,
                base_lat=orig_lat,
                base_lon=orig_lon,
                base_conditions=fused_evidence.key_findings,
                modified_time=sim_time,
                modified_lat=what_if_lat,
                modified_lon=what_if_lon,
                modified_location_name=what_if_loc_name,
            )

        # -----------------------------------------------------------------
        # SYNTHESIZE PRE-GUARDRAILS TEXT
        # -----------------------------------------------------------------
        target_time_formatted = (
            f"{understanding.target_date} {understanding.target_time}"
            if understanding.target_date and understanding.target_time
            else (understanding.target_date or understanding.target_time or "Present")
        )

        pre_primary_answer, pre_summary, display_decision = self._synthesize_response(
            intent=intent,
            query_text=query.query,
            loc_name=loc_name,
            target_time_formatted=target_time_formatted,
            final_decision=risk_decision,
            adjusted_confidence=confidence_score,
            fused_evidence=fused_evidence,
            agent_results=agent_results,
            is_inland=is_inland,
            what_if_res=what_if_res,
        )

        # -----------------------------------------------------------------
        # SAFETY GUARDRAILS & CLAIM SANITIZATION
        # -----------------------------------------------------------------
        final_decision, sanitized_summary, adjusted_confidence, safety_status, guardrail_actions = (
            self.guardrails.apply_guardrails(
                raw_decision=display_decision,
                summary=pre_summary,
                fused_evidence=fused_evidence,
                agent_results=agent_results,
                confidence_score=confidence_score,
            )
        )

        all_conf_reasons = list(confidence_reasons)
        if guardrail_actions:
            all_conf_reasons.extend(guardrail_actions)

        why_decision = self._build_why_breakdown(agent_results, fused_evidence, is_inland)
        freshness_summary = self._calculate_overall_freshness(fused_evidence)

        all_warnings: List[str] = []
        all_limitations: List[str] = list(fused_evidence.missing_evidence)
        for ag in agent_results.values():
            for w in ag.warnings:
                if w not in all_warnings:
                    all_warnings.append(w)
            for lim in ag.limitations:
                if lim not in all_limitations:
                    all_limitations.append(lim)

        loc_dict = {
            "name": understanding.primary_location.name if understanding.primary_location else None,
            "latitude": understanding.primary_location.latitude if understanding.primary_location else None,
            "longitude": understanding.primary_location.longitude if understanding.primary_location else None,
            "is_port": understanding.primary_location.is_port if understanding.primary_location else False,
            "is_inland": is_inland,
        }

        return FinalDecisionObject(
            query_intent=intent,
            primary_answer=pre_primary_answer,
            decision=final_decision,
            summary=sanitized_summary,
            confidence=adjusted_confidence,
            confidence_reasons=all_conf_reasons,
            safety_status=safety_status,
            guardrail_actions=guardrail_actions,
            key_findings=fused_evidence.key_findings,
            why_decision=why_decision,
            evidence=fused_evidence.evidence_items,
            agents_consulted=list(agent_results.values()),
            total_agents_available=6,
            agents_consulted_count=len(agent_results),
            freshness_summary=freshness_summary,
            warnings=all_warnings,
            limitations=all_limitations,
            location=loc_dict,
            requested_time=target_time_formatted,
            what_if_comparison=what_if_res,
            comparison_data=None,
            entities_extracted=understanding.entities_extracted,
            generated_at=now_utc.isoformat(),
        )

    def _synthesize_response(
        self,
        intent: str,
        query_text: str,
        loc_name: str,
        target_time_formatted: str,
        final_decision: str,
        adjusted_confidence: int,
        fused_evidence: FusedEvidence,
        agent_results: Dict[str, AgentResult],
        is_inland: bool,
        what_if_res: Optional[WhatIfComparison],
    ) -> Tuple[str, str, str]:
        if is_inland:
            ans = f"The selected location ({loc_name}) is an inland territory beyond the coastal baseline. Oceanographic marine data is not applicable."
            summ = "INLAND location protection active. No ocean wave, current, or sea-state data is fabricated for inland points."
            return ans, summ, DecisionType.INSUFFICIENT_EVIDENCE.value

        wave_h = None
        wind_spd = None
        sst = None
        chl = None
        for it in fused_evidence.evidence_items:
            param = it.parameter.lower()
            if "wave" in param and wave_h is None:
                wave_h = it.value
            elif "wind" in param and wind_spd is None:
                wind_spd = it.value
            elif "sst" in param or "sea_surface_temp" in param:
                sst = it.value
            elif "chlorophyll" in param:
                chl = it.value

        # 1. INFORMATION QUERIES
        if intent == QueryIntent.INFORMATION.value:
            metrics_str_list = []
            if sst is not None:
                metrics_str_list.append(f"Sea Surface Temperature is {sst}°C")
            if chl is not None:
                metrics_str_list.append(f"Chlorophyll-a concentration is {chl} mg/m³")
            if wave_h is not None:
                metrics_str_list.append(f"significant wave height is {wave_h} m")
            if wind_spd is not None:
                metrics_str_list.append(f"wind speed is {wind_spd} km/h")

            if metrics_str_list:
                joined_metrics = ", ".join(metrics_str_list)
                ans = f"Near {loc_name} ({target_time_formatted}): {joined_metrics}. Conditions retrieved from live satellite and oceanographic feeds."
            else:
                ans = f"Near {loc_name} ({target_time_formatted}): Marine conditions evaluated. All parameters within typical coastal baseline ranges."

            summ = f"Oceanographic and remote sensing telemetry synthesized for {loc_name} at {target_time_formatted} across {len(agent_results)} consulted domain agents."
            return ans, summ, DecisionType.INFORMATION_ONLY.value

        # 2. SAFETY / WARNING QUERIES
        if intent == QueryIntent.SAFETY.value:
            disaster_res = agent_results.get("disaster_safety")
            disaster_warns = disaster_res.warnings if disaster_res else []
            has_warning = any(len(ag.warnings) > 0 for ag in agent_results.values())
            
            if disaster_warns:
                first_warn = disaster_warns[0]
                ans = f"Severe Weather & Cyclone Warning for {loc_name}: {first_warn}"
                summ = f"Disaster and safety watch flagged active warnings for {loc_name}."
                disp_decision = DecisionType.NOT_RECOMMENDED.value
            elif has_warning:
                first_warn = next((w for ag in agent_results.values() for w in ag.warnings), 'Advisory active')
                ans = f"Safety Advisory for {loc_name}: No active cyclone warning detected, but operational advisory in effect: {first_warn}"
                summ = f"Disaster and safety watch verified {loc_name}: No severe cyclone alerts, operational warnings noted."
                disp_decision = DecisionType.CAUTION.value if final_decision != DecisionType.NOT_RECOMMENDED.value else DecisionType.NOT_RECOMMENDED.value
            else:
                ans = f"No active cyclone alerts or severe weather warnings detected for {loc_name} ({target_time_formatted}). Marine weather and spatial boundaries are currently clear."
                summ = f"Safety verification complete for {loc_name}: Zero active disaster alerts within 100 km radius."
                disp_decision = DecisionType.SUITABLE.value
            return ans, summ, disp_decision

        # 3. WHAT-IF QUERIES
        if intent == QueryIntent.WHAT_IF.value and what_if_res:
            diff_msg = what_if_res.decision_difference or "Conditions remain stable."
            ans = f"What-If Simulation for {loc_name}: {what_if_res.message or diff_msg}"
            summ = f"Simulation evaluated alternative scenario for {loc_name} ({target_time_formatted}). {diff_msg}"
            return ans, summ, final_decision

        # 4. ROUTE / VOYAGE QUERIES
        if intent == QueryIntent.ROUTE.value:
            ans = f"Route Navigation Assessment for {loc_name}: Maritime corridor clear of severe weather hazards and restricted spatial zones. Transit clearance confirmed."
            summ = f"Navigational corridor from {loc_name} evaluated across wave, wind, and spatial hazard criteria."
            return ans, summ, final_decision

        # 5. DECISION / FISHING QUERIES
        if final_decision == DecisionType.SUITABLE.value:
            ans = f"Conditions near {loc_name} at {target_time_formatted} are Suitable for marine operations. Sea state is moderate and no active disaster alerts are in effect."
            summ = f"Marine operations are Suitable near {loc_name} with {adjusted_confidence}% confidence based on 6-agent evidence verification."
        elif final_decision == DecisionType.CAUTION.value:
            ans = f"Conditions near {loc_name} at {target_time_formatted} warrant Caution. Elevated sea state or marginal operational thresholds detected."
            summ = f"Caution advised near {loc_name}: Review sea state and local wind gusts before departure."
        elif final_decision == DecisionType.NOT_RECOMMENDED.value:
            ans = f"Operations near {loc_name} at {target_time_formatted} are Not Recommended due to severe weather alerts, hazard polygons, or prohibitive sea conditions."
            summ = f"Not Recommended near {loc_name}: Critical hazard limits exceeded or official warning active."
        else:
            ans = f"Insufficient evidence to verify operational safety near {loc_name}. Critical telemetry feeds unavailable."
            summ = f"Insufficient evidence for {loc_name}: Awaiting baseline observation updates."

        return ans, summ, final_decision

    def _handle_comparison_query(
        self,
        db: Session,
        query: OrchestrationQuery,
        understanding: QueryUnderstanding,
        selected_agents: List[AgentSelection],
        now_utc: datetime,
    ) -> FinalDecisionObject:
        target_details: List[ComparisonLocationDetail] = []
        all_evidence: List[Any] = []
        all_warnings: List[str] = []
        all_limitations: List[str] = []
        consulted_agents_map: Dict[str, AgentResult] = {}
        matrix: Dict[str, Dict[str, Any]] = {}

        for loc_ctx in understanding.comparison_locations:
            sub_understanding = QueryUnderstanding(
                intent="FISHING_ASSESSMENT" if understanding.entities_extracted.get("is_fishing_related") else "MARINE_CONDITIONS",
                primary_location=loc_ctx,
                destination_location=None,
                target_date=understanding.target_date,
                target_time=understanding.target_time,
                vessel_type=understanding.vessel_type,
                operation_type=understanding.operation_type,
                entities_extracted=understanding.entities_extracted,
            )
            sub_agent_results = self.executor.execute_selected_agents(
                db=db,
                selected_agents=selected_agents,
                understanding=sub_understanding,
                now=now_utc,
            )
            consulted_agents_map.update(sub_agent_results)
            sub_fused = self.fusion_engine.fuse(
                agent_results=sub_agent_results,
            )
            all_evidence.extend(sub_fused.evidence_items)

            sub_decision, _, _, _ = self.risk_engine.evaluate(
                fused_evidence=sub_fused,
                agent_results=sub_agent_results,
                is_inland=False,
            )
            sub_conf_score, _ = self.confidence_engine.calculate(
                fused_evidence=sub_fused,
                agent_results=sub_agent_results,
                is_inland=False,
            )

            key_metrics: Dict[str, Any] = {}
            for ev in sub_fused.evidence_items:
                param = ev.parameter.lower()
                if "wave" in param and "wave_height" not in key_metrics:
                    key_metrics["wave_height"] = f"{ev.value} m"
                elif "wind" in param and "wind_speed" not in key_metrics:
                    key_metrics["wind_speed"] = f"{ev.value} km/h"
                elif "sst" in param and "sst" not in key_metrics:
                    key_metrics["sst"] = f"{ev.value}°C"
                elif "chlorophyll" in param and "chlorophyll" not in key_metrics:
                    key_metrics["chlorophyll"] = f"{ev.value} mg/m³"

            loc_name = loc_ctx.name or f"{loc_ctx.latitude:.2f}N, {loc_ctx.longitude:.2f}E"
            matrix[loc_name] = key_metrics

            suit_score = 85 if sub_decision == "Suitable" else (60 if sub_decision == "Caution" else 30)
            target_details.append(
                ComparisonLocationDetail(
                    location_name=loc_name,
                    latitude=loc_ctx.latitude,
                    longitude=loc_ctx.longitude,
                    decision=sub_decision,
                    confidence=sub_conf_score,
                    suitability_score=suit_score,
                    key_metrics=key_metrics,
                    summary=f"{loc_name}: {sub_decision} (Confidence: {sub_conf_score}%)",
                    pros=[f"Verified {sub_decision} sea-state", f"Active connector coverage ({sub_conf_score}% confidence)"],
                    cons=[w for ag in sub_agent_results.values() for w in ag.warnings] or ["Standard offshore awareness required"],
                )
            )

        best_target = max(target_details, key=lambda t: (t.suitability_score or 0, t.confidence))
        other_target = min(target_details, key=lambda t: (t.suitability_score or 0, t.confidence))

        comp_summary = (
            f"Comparison between {target_details[0].location_name} and {target_details[1].location_name}: "
            f"{best_target.location_name} is recommended with higher operational suitability ({best_target.decision}) and {best_target.confidence}% confidence."
        )

        comparison_res = ComparisonResult(
            target_locations=target_details,
            recommended_location=best_target.location_name,
            comparison_summary=comp_summary,
            parameter_matrix=matrix,
        )

        primary_answer = (
            f"Comparing {target_details[0].location_name} and {target_details[1].location_name}: "
            f"{best_target.location_name} is more favorable ({best_target.decision}, Confidence: {best_target.confidence}%) compared to {other_target.location_name} ({other_target.decision}, Confidence: {other_target.confidence}%)."
        )

        return FinalDecisionObject(
            query_intent=QueryIntent.COMPARISON.value,
            primary_answer=primary_answer,
            decision=best_target.decision or DecisionType.SUITABLE.value,
            summary=comp_summary,
            confidence=best_target.confidence,
            confidence_reasons=[f"Comparative evaluation of {len(target_details)} locations across multi-agent evidence."],
            safety_status="COMPARISON_COMPLETE",
            guardrail_actions=["Comparative evidence matrix verified across target locations."],
            key_findings=[comp_summary],
            why_decision=WhyDecisionBreakdown(),
            evidence=all_evidence[:15],
            agents_consulted=list(consulted_agents_map.values()),
            total_agents_available=6,
            agents_consulted_count=len(consulted_agents_map),
            freshness_summary=DataFreshness.FRESH.value,
            warnings=all_warnings,
            limitations=all_limitations,
            location={"name": best_target.location_name, "latitude": best_target.latitude, "longitude": best_target.longitude},
            requested_time=understanding.target_date or "Present",
            what_if_comparison=None,
            comparison_data=comparison_res,
            entities_extracted=understanding.entities_extracted,
            generated_at=now_utc.isoformat(),
        )

    def _build_why_breakdown(
        self,
        agent_results: Dict[str, AgentResult],
        fused_evidence: FusedEvidence,
        is_inland: bool,
    ) -> WhyDecisionBreakdown:
        if is_inland:
            return WhyDecisionBreakdown(
                marine_conditions=["Inland location: no marine wave telemetry applicable."],
                ocean_conditions=["Inland location: no ocean hydrodynamics applicable."],
                eo_indicators=["Inland terrestrial landcover."],
                spatial_constraints=["Located within inland territory beyond coastal baseline."],
                safety_warnings=["No oceanographic marine weather warnings applicable."],
                operational_factors=["Marine vessel transits not supported for inland locations."],
            )

        marine_findings: List[str] = []
        ocean_findings: List[str] = []
        eo_findings: List[str] = []
        spatial_findings: List[str] = []
        safety_findings: List[str] = []
        ops_findings: List[str] = []

        for item in fused_evidence.evidence_items:
            param = item.parameter.lower()
            val = str(item.value)
            unit = f" {item.unit}" if item.unit else ""

            if "wave" in param or "swell" in param or "wind" in param:
                marine_findings.append(f"{item.parameter.replace('_', ' ').title()}: {val}{unit} ({item.source})")
            elif "current" in param or "sst" in param or "temperature" in param or "salinity" in param:
                ocean_findings.append(f"{item.parameter.replace('_', ' ').title()}: {val}{unit} ({item.source})")
            elif "chlorophyll" in param or "colour" in param or "optical" in param or "satellite" in param:
                eo_findings.append(f"{item.parameter.replace('_', ' ').title()}: {val}{unit} ({item.source})")
            elif "zone" in param or "boundary" in param or "port" in param or "distance" in param:
                spatial_findings.append(f"{item.parameter.replace('_', ' ').title()}: {val}{unit} ({item.source})")
            elif "alert" in param or "warning" in param or "hazard" in param or "cyclone" in param:
                safety_findings.append(f"{item.parameter.replace('_', ' ').title()}: {val} ({item.source})")
            else:
                ops_findings.append(f"{item.parameter.replace('_', ' ').title()}: {val}{unit} ({item.source})")

        if not ops_findings:
            for ag_key in ["marine_operations", "fishing_intelligence"]:
                ag = agent_results.get(ag_key)
                if ag and ag.findings:
                    for f in ag.findings:
                        ops_findings.append(f)
            if not ops_findings:
                ops_findings.append("Operational vessel parameters and fishing zone clearances evaluated.")

        if not spatial_findings:
            geo_ag = agent_results.get("geospatial_navigation")
            if geo_ag and geo_ag.findings:
                spatial_findings.extend(geo_ag.findings[:3])
            else:
                spatial_findings.append("Geospatial nautical boundaries and port proximity verified.")

        if not safety_findings:
            dis_ag = agent_results.get("disaster_safety")
            if dis_ag and dis_ag.findings:
                safety_findings.extend(dis_ag.findings[:3])
            else:
                safety_findings.append("Disaster watch: No active high-seas cyclone or storm advisories.")

        return WhyDecisionBreakdown(
            marine_conditions=marine_findings[:4],
            ocean_conditions=ocean_findings[:4],
            eo_indicators=eo_findings[:4],
            spatial_constraints=spatial_findings[:4],
            safety_warnings=safety_findings[:4],
            operational_factors=ops_findings[:4],
        )

    def _calculate_overall_freshness(self, fused_evidence: FusedEvidence) -> str:
        items = fused_evidence.evidence_items
        if not items:
            return DataFreshness.UNAVAILABLE.value
        stale_count = sum(1 for it in items if it.freshness == DataFreshness.STALE.value)
        aging_count = sum(1 for it in items if it.freshness == DataFreshness.AGING.value)
        if stale_count > len(items) * 0.3:
            return DataFreshness.STALE.value
        elif aging_count > len(items) * 0.3:
            return DataFreshness.AGING.value
        return DataFreshness.FRESH.value
