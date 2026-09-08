from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from schemas.agent_contract import (
    AgentResult,
    AgentStatus,
    DataFreshness,
    EvidenceItem,
    ObservationType,
)


class FusedEvidence:
    """
    Consolidated multi-agent evidence container with deduplication,
    provenance tracking, conflict detection, and real vs AI classification.
    """

    def __init__(
        self,
        evidence_items: List[EvidenceItem],
        key_findings: List[str],
        conflicts: List[Dict[str, Any]],
        missing_evidence: List[str],
        source_summary: Dict[str, int],
        overall_evidence_quality: str,
        real_data_count: int,
        ai_assessment_count: int,
    ):
        self.evidence_items = evidence_items
        self.key_findings = key_findings
        self.conflicts = conflicts
        self.missing_evidence = missing_evidence
        self.source_summary = source_summary
        self.overall_evidence_quality = overall_evidence_quality
        self.real_data_count = real_data_count
        self.ai_assessment_count = ai_assessment_count


class EvidenceFusionEngine:
    """
    OCEANIS Evidence Fusion Engine.
    Merges, normalizes, deduplicates, and validates evidence from all six domain agents.
    Maintains rigorous provenance and strictly distinguishes REAL DATA from AI ASSESSMENTS.
    """

    CRITICAL_PARAMETERS = {
        "wave_height",
        "wind_speed",
        "sea_surface_temperature",
        "marine_alert",
        "restricted_zone",
    }

    def fuse(
        self,
        agent_results: Dict[str, AgentResult],
    ) -> FusedEvidence:
        """
        Consolidates evidence from all domain agent results into a unified, conflict-aware FusedEvidence.
        """
        fused_items: List[EvidenceItem] = []
        seen_keys: Set[str] = set()
        key_findings: List[str] = []
        source_summary: Dict[str, int] = {}
        real_data_count = 0
        ai_assessment_count = 0

        # Collect and deduplicate evidence items
        for agent_id, result in agent_results.items():
            if not result:
                continue

            # Gather findings
            for finding in result.findings:
                if finding and finding not in key_findings:
                    key_findings.append(finding)

            # Process evidence items
            for item in result.evidence:
                param = item.parameter
                source = item.source
                ts = item.timestamp or ""
                val_str = str(item.value)

                dedup_key = f"{source}:{param}:{val_str}:{ts}"
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                # Ensure observation type is standardized
                obs_type = self._normalize_observation_type(item.observation_type, source)
                freshness_val = self._normalize_freshness(item.freshness, item.timestamp)

                normalized_item = EvidenceItem(
                    source=source,
                    parameter=param,
                    value=item.value,
                    unit=item.unit,
                    observation_type=obs_type,
                    timestamp=item.timestamp,
                    freshness=freshness_val,
                    location=item.location,
                    provenance=item.provenance,
                )
                fused_items.append(normalized_item)

                # Count sources and data classifications
                source_summary[source] = source_summary.get(source, 0) + 1
                if obs_type == ObservationType.AI_ASSESSMENT.value:
                    ai_assessment_count += 1
                else:
                    real_data_count += 1

        # Conflict Detection
        conflicts = self._detect_conflicts(fused_items)

        # Missing Evidence Identification
        missing_evidence = self._identify_missing_evidence(fused_items, agent_results)

        # Overall Evidence Quality Rating
        evidence_quality = self._evaluate_quality(fused_items, agent_results, conflicts, missing_evidence)

        return FusedEvidence(
            evidence_items=fused_items,
            key_findings=key_findings,
            conflicts=conflicts,
            missing_evidence=missing_evidence,
            source_summary=source_summary,
            overall_evidence_quality=evidence_quality,
            real_data_count=real_data_count,
            ai_assessment_count=ai_assessment_count,
        )

    def _normalize_observation_type(self, raw_type: Optional[str], source: str) -> str:
        if not raw_type:
            if "AI" in source or "Engine" in source or "Model" in source:
                return ObservationType.AI_ASSESSMENT.value
            return ObservationType.OBSERVED.value

        upper = raw_type.upper()
        if "WARN" in upper or "ALERT" in upper:
            return ObservationType.OFFICIAL_WARNING.value
        elif "FORECAST" in upper or "MODEL" in upper:
            return ObservationType.FORECAST.value
        elif "AI" in upper or "REASON" in upper or "SYNTHESIS" in upper:
            return ObservationType.AI_ASSESSMENT.value
        return ObservationType.OBSERVED.value

    def _normalize_freshness(self, raw_freshness: Optional[str], timestamp: Optional[str]) -> str:
        if not timestamp and (not raw_freshness or raw_freshness.upper() == "UNKNOWN"):
            return DataFreshness.UNAVAILABLE.value
        if not raw_freshness:
            return DataFreshness.FRESH.value
        upper = raw_freshness.upper()
        if "FRESH" in upper:
            return DataFreshness.FRESH.value
        elif "AGING" in upper:
            return DataFreshness.AGING.value
        elif "STALE" in upper:
            return DataFreshness.STALE.value
        return DataFreshness.UNAVAILABLE.value

    def _detect_conflicts(self, items: List[EvidenceItem]) -> List[Dict[str, Any]]:
        """
        Identifies factual or operational discrepancies across merged evidence items.
        """
        conflicts: List[Dict[str, Any]] = []

        # Example check: wind speed discrepancies across sources
        wind_readings = [it for it in items if "wind" in it.parameter.lower() and isinstance(it.value, (int, float))]
        if len(wind_readings) >= 2:
            speeds = [it.value for it in wind_readings]
            if max(speeds) - min(speeds) > 25.0:  # > 25 km/h discrepancy
                conflicts.append({
                    "parameter": "wind_speed",
                    "description": f"Significant variance in wind speed observations ({min(speeds)} to {max(speeds)} km/h) across sources",
                    "sources": [it.source for it in wind_readings],
                })

        # Example check: official warning active while sea state reported calm
        warnings = [it for it in items if it.observation_type == ObservationType.OFFICIAL_WARNING.value]
        calm_sea = [it for it in items if it.parameter == "wave_height" and isinstance(it.value, (int, float)) and it.value < 1.0]
        if warnings and calm_sea:
            conflicts.append({
                "parameter": "warning_vs_sea_state",
                "description": "Active official severe weather alert coexists with low in-situ wave measurements",
                "sources": [w.source for w in warnings] + [c.source for c in calm_sea],
            })

        return conflicts

    def _identify_missing_evidence(
        self,
        items: List[EvidenceItem],
        agent_results: Dict[str, AgentResult],
    ) -> List[str]:
        """
        Identifies critical marine or environmental parameters absent from fused evidence.
        """
        present_params = {item.parameter.lower() for item in items}
        missing: List[str] = []

        if not any("wave" in p for p in present_params):
            missing.append("Wave / Swell Height Observations")
        if not any("wind" in p for p in present_params):
            missing.append("Wind Speed / Direction Telemetry")
        if not any("temperature" in p or "sst" in p for p in present_params):
            missing.append("Sea Surface Temperature (SST)")
        if not any("alert" in p or "hazard" in p or "cyclone" in p for p in present_params):
            missing.append("Disaster & Cyclone Tracking Verification")

        for agent_id, res in agent_results.items():
            if res.status in (AgentStatus.UNAVAILABLE.value, AgentStatus.ERROR.value):
                missing.append(f"{res.agent_name} data feed ({res.status})")

        return missing

    def _evaluate_quality(
        self,
        items: List[EvidenceItem],
        agent_results: Dict[str, AgentResult],
        conflicts: List[Dict[str, Any]],
        missing_evidence: List[str],
    ) -> str:
        """
        Evaluates overall evidence quality rating based on coverage, freshness, and conflicts.
        """
        successful_agents = sum(1 for res in agent_results.values() if res.status == AgentStatus.SUCCESS.value)
        total_agents = max(len(agent_results), 1)
        coverage_ratio = successful_agents / total_agents

        stale_items = sum(1 for it in items if it.freshness == DataFreshness.STALE.value)
        stale_ratio = stale_items / max(len(items), 1)

        if coverage_ratio >= 0.8 and not conflicts and len(missing_evidence) == 0 and stale_ratio < 0.2:
            return "HIGH"
        elif coverage_ratio >= 0.5 and len(missing_evidence) <= 2:
            return "MODERATE"
        elif coverage_ratio >= 0.3:
            return "LOW"
        return "INSUFFICIENT"
