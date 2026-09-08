from typing import Any, Dict, List, Tuple
from orchestrator.evidence import FusedEvidence
from schemas.agent_contract import (
    AgentResult,
    AgentStatus,
    DataFreshness,
    EvidenceItem,
)


class ConfidenceEngine:
    """
    Explainable, deterministic confidence calculation engine for OCEANIS decisions.
    Produces a composite score (0-100%) and transparent diagnostic justification
    based on agent execution success, multi-source telemetry freshness,
    observational completeness, and absence of contradictory signals.
    """

    def calculate(
        self,
        fused_evidence: FusedEvidence,
        agent_results: Dict[str, AgentResult],
        is_inland: bool = False,
    ) -> Tuple[int, List[str]]:
        """
        Computes the composite confidence score and explainable reasons.
        Returns:
            confidence_score: int (0 to 100)
            confidence_reasons: List[str]
        """
        if is_inland:
            return 0, ["Inland location: Marine oceanographic confidence not applicable."]

        reasons: List[str] = []
        score = 0.0

        # -------------------------------------------------------------
        # 1. AGENT EXECUTION COVERAGE (Max 40 Points)
        # -------------------------------------------------------------
        total_agents = len(agent_results)
        successful_agents = sum(
            1 for res in agent_results.values()
            if res and res.status in (AgentStatus.SUCCESS.value, AgentStatus.PARTIAL.value)
        )

        agent_ratio = (successful_agents / total_agents) if total_agents > 0 else 0.0
        agent_points = agent_ratio * 40.0
        score += agent_points

        if successful_agents == total_agents and total_agents >= 6:
            reasons.append(f"Full multi-domain consensus across all {successful_agents}/{total_agents} domain agents (+{int(agent_points)}%).")
        elif successful_agents > 0:
            reasons.append(f"Partial agent coverage: {successful_agents}/{total_agents} domain agents responded (+{int(agent_points)}%).")
        else:
            reasons.append("Zero domain agents succeeded; confidence degraded.")

        # -------------------------------------------------------------
        # 2. DATA FRESHNESS RATING (Max 25 Points)
        # -------------------------------------------------------------
        items = fused_evidence.evidence_items
        if items:
            fresh_count = sum(1 for it in items if it.freshness == DataFreshness.FRESH.value)
            aging_count = sum(1 for it in items if it.freshness == DataFreshness.AGING.value)
            stale_count = sum(1 for it in items if it.freshness == DataFreshness.STALE.value)
            total_items = len(items)

            freshness_score = ((fresh_count * 1.0) + (aging_count * 0.5) + (stale_count * 0.1)) / total_items
            freshness_points = freshness_score * 25.0
            score += freshness_points

            if fresh_count / total_items >= 0.7:
                reasons.append(f"High observational freshness: {fresh_count}/{total_items} evidence records are Fresh (+{int(freshness_points)}%).")
            elif stale_count > 0:
                reasons.append(f"Data freshness degradation: {stale_count}/{total_items} records are Stale (+{int(freshness_points)}%).")
            else:
                reasons.append(f"Moderate freshness coverage across {total_items} evidence records (+{int(freshness_points)}%).")
        else:
            reasons.append("No telemetry evidence available to evaluate freshness (0%).")

        # -------------------------------------------------------------
        # 3. DATA COMPLETENESS (Max 25 Points)
        # -------------------------------------------------------------
        present_params = {it.parameter.lower() for it in items}
        completeness_checks = [
            ("wave", any("wave" in p for p in present_params)),
            ("wind", any("wind" in p for p in present_params)),
            ("sst", any("temperature" in p or "sst" in p for p in present_params)),
            ("alerts", any("alert" in p or "warning" in p or "hazard" in p or "cyclone" in p for p in present_params)),
            ("spatial", any("zone" in p or "port" in p or "boundary" in p for p in present_params)),
        ]
        passed_checks = sum(1 for _, ok in completeness_checks if ok)
        completeness_points = (passed_checks / len(completeness_checks)) * 25.0
        score += completeness_points

        if passed_checks == len(completeness_checks):
            reasons.append(f"Comprehensive environmental telemetry verified across wave, wind, SST, alerts, and spatial zones (+{int(completeness_points)}%).")
        else:
            missing_names = [name.upper() for name, ok in completeness_checks if not ok]
            reasons.append(f"Telemetry missing key parameters ({', '.join(missing_names)}) (+{int(completeness_points)}%).")

        # -------------------------------------------------------------
        # 4. OFFICIAL SOURCE PROVENANCE (Max 10 Points)
        # -------------------------------------------------------------
        sources = fused_evidence.source_summary
        official_sources = [s for s in sources if any(k in s.upper() for k in ("IMD", "INCOIS", "COPERNICUS", "POSTGIS"))]
        if official_sources:
            prov_points = min(len(official_sources) * 2.5, 10.0)
            score += prov_points
            reasons.append(f"Backed by official authoritative sources: {', '.join(official_sources[:4])} (+{int(prov_points)}%).")

        # -------------------------------------------------------------
        # 5. PENALTIES (Conflicts & Missing Evidence)
        # -------------------------------------------------------------
        if fused_evidence.conflicts:
            score = max(score - 15.0, 5.0)
            reasons.append(f"Deducted 15% due to {len(fused_evidence.conflicts)} conflicting evidence signals across sources.")

        if fused_evidence.missing_evidence:
            penalty = min(len(fused_evidence.missing_evidence) * 5.0, 20.0)
            score = max(score - penalty, 5.0)
            reasons.append(f"Deducted {int(penalty)}% due to critical missing evidence ({len(fused_evidence.missing_evidence)} gaps).")

        final_score = int(round(max(min(score, 100.0), 0.0)))
        return final_score, reasons
