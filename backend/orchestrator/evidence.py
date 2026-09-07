from typing import Any, Dict, List, Optional, Set

from orchestrator.schemas import AgentExecutionResult, FusedEvidenceItem


class EvidenceFusionEngine:
    """
    Evidence Fusion Engine for OCEANIS Agent Orchestrator.
    Consolidates, normalizes, and deduplicates evidence items across all executed
    domain agents while rigorously preserving full source provenance, timestamps,
    confidence ratings, and freshness flags.
    """

    def fuse(
        self,
        agent_results: Dict[str, AgentExecutionResult],
    ) -> List[FusedEvidenceItem]:
        """
        Consolidates evidence from all successful domain agents into a unified list.
        """
        fused_items: List[FusedEvidenceItem] = []
        seen_keys: Set[str] = set()

        for agent_id, exec_result in agent_results.items():
            if exec_result.status != "SUCCESS" or not exec_result.result:
                continue

            raw_data = exec_result.result
            raw_evidence = raw_data.get("evidence") or raw_data.get("evidence_used") or []
            if not raw_evidence and "location_a_assessment" in raw_data:
                loc_a_ev = (raw_data.get("location_a_assessment") or {}).get("evidence") or (raw_data.get("location_a_assessment") or {}).get("evidence_used") or []
                loc_b_ev = (raw_data.get("location_b_assessment") or {}).get("evidence") or (raw_data.get("location_b_assessment") or {}).get("evidence_used") or []
                raw_evidence = list(loc_a_ev) + list(loc_b_ev)

            for ev in raw_evidence:
                if isinstance(ev, dict):
                    factor = ev.get("factor") or ev.get("metric") or "general_evidence"
                    title = ev.get("title") or ev.get("name") or factor
                    source = ev.get("source") or exec_result.agent_name
                    source_category = ev.get("source_category") or "OFFICIAL"
                    data_type = ev.get("data_type") or "OBSERVED"
                    observed_at = ev.get("observed_at") or ev.get("timestamp")
                    confidence = float(ev.get("confidence", 1.0))
                    freshness = str(ev.get("freshness", "FRESH"))
                    severity = str(ev.get("severity", "NORMAL"))
                    notes = ev.get("notes")
                    dist = ev.get("distance_km")

                    # Deduplication key based on factor, source, title
                    dedup_key = f"{factor}:{source}:{title}:{observed_at}"
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    fused_items.append(
                        FusedEvidenceItem(
                            factor=factor,
                            title=title,
                            value=ev.get("value"),
                            unit=ev.get("unit"),
                            source=source,
                            source_category=source_category,
                            data_type=data_type,
                            observed_at=observed_at,
                            latitude=ev.get("latitude"),
                            longitude=ev.get("longitude"),
                            distance_km=dist,
                            confidence=confidence,
                            freshness=freshness,
                            severity=severity,
                            originating_agent=agent_id,
                            notes=notes,
                        )
                    )

        return fused_items
