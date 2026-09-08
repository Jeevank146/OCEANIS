import re
from typing import Any, Dict, List, Tuple
from orchestrator.evidence import FusedEvidence
from schemas.agent_contract import (
    AgentResult,
    AgentStatus,
    DataFreshness,
    DecisionType,
    EvidenceItem,
    ObservationType,
)


class SafetyGuardrailEngine:
    """
    Authoritative Safety Guardrail Layer for OCEANIS.
    Enforces non-negotiable maritime safety policies, verifies official regulatory warnings,
    enforces spatial exclusion zones, and strictly sanitizes decision summaries
    against ungrounded claims or false safety guarantees.
    """

    PROHIBITED_SAFETY_CLAIMS = re.compile(
        r"(100%\s*safe|guaranteed\s*safe|completely\s*safe|risk[-\s]*free|zero\s*risk|absolute\s*safety|never\s*in\s*danger)",
        re.IGNORECASE,
    )

    PROHIBITED_FISHING_CLAIMS = re.compile(
        r"(guaranteed\s*catch|100%\s*catch|guaranteed\s*fish|certain\s*catch|guaranteed\s*bounty)",
        re.IGNORECASE,
    )

    def apply_guardrails(
        self,
        raw_decision: str,
        summary: str,
        fused_evidence: FusedEvidence,
        agent_results: Dict[str, AgentResult],
        confidence_score: int,
    ) -> Tuple[str, str, int, str, List[str]]:
        """
        Applies safety guardrail policies.
        Returns:
            final_decision: (Guaranteed non-overridden decision)
            sanitized_summary: (Sanitized natural language narrative)
            adjusted_confidence: (Confidence adjusted for safety/staleness)
            safety_status: (Overall safety guardrail state)
            guardrail_actions: (List of actions applied by guardrails)
        """
        guardrail_actions: List[str] = []
        final_decision = raw_decision
        sanitized_summary = summary
        adjusted_confidence = confidence_score

        # -------------------------------------------------------------
        # 1. OFFICIAL WARNING VETO POLICY
        # -------------------------------------------------------------
        disaster_result = agent_results.get("disaster_safety")
        official_warnings = [
            it for it in fused_evidence.evidence_items
            if it.observation_type == ObservationType.OFFICIAL_WARNING.value
        ]

        if disaster_result and disaster_result.warnings:
            has_severe_warning = any(
                any(k in w.upper() for k in ("CYCLONE", "STORM", "RED ALERT", "ORANGE ALERT", "EMERGENCY", "BLOCKED"))
                for w in disaster_result.warnings
            )
            if has_severe_warning:
                final_decision = DecisionType.NOT_RECOMMENDED.value
                guardrail_actions.append("Official severe weather warning detected — Deterministic NOT_RECOMMENDED enforced (LLM override prohibited).")

        # -------------------------------------------------------------
        # 2. SPATIAL RESTRICTION ENFORCEMENT
        # -------------------------------------------------------------
        geospatial_result = agent_results.get("geospatial_navigation")
        if geospatial_result and geospatial_result.warnings:
            has_barrier = any(
                any(k in w.upper() for k in ("RESTRICTED", "EXCLUSION", "MILITARY", "PROHIBITED", "BARRIER"))
                for w in geospatial_result.warnings
            )
            if has_barrier:
                final_decision = DecisionType.NOT_RECOMMENDED.value
                guardrail_actions.append("Maritime restricted exclusion zone intersection detected — Deterministic NOT_RECOMMENDED enforced.")

        # -------------------------------------------------------------
        # 3. CRITICAL STALENESS CONFIDENCE ADJUSTMENT
        # -------------------------------------------------------------
        stale_critical = [
            it for it in fused_evidence.evidence_items
            if it.freshness == DataFreshness.STALE.value and any(k in it.parameter.lower() for k in ("wave", "wind", "cyclone", "alert"))
        ]
        if stale_critical:
            adjusted_confidence = max(adjusted_confidence - 10, 5)
            guardrail_actions.append(f"Reduced confidence by 10% due to {len(stale_critical)} stale critical safety parameters.")

        # -------------------------------------------------------------
        # 4. SANITIZE UNGROUNDED CLAIMS (Absolute Safety & Guaranteed Fishing)
        # -------------------------------------------------------------
        if self.PROHIBITED_SAFETY_CLAIMS.search(sanitized_summary):
            sanitized_summary = self.PROHIBITED_SAFETY_CLAIMS.sub("normal operational parameters", sanitized_summary)
            guardrail_actions.append("Sanitized prohibited absolute safety claim into standard operational terminology.")

        if self.PROHIBITED_FISHING_CLAIMS.search(sanitized_summary):
            sanitized_summary = self.PROHIBITED_FISHING_CLAIMS.sub("favorable bio-optical potential", sanitized_summary)
            guardrail_actions.append("Sanitized prohibited guaranteed fishing catch claim into bio-optical indicator terminology.")

        # -------------------------------------------------------------
        # 5. DETERMINE SAFETY STATUS
        # -------------------------------------------------------------
        if final_decision == DecisionType.NOT_RECOMMENDED.value:
            safety_status = "RESTRICTED / HIGH HAZARD"
        elif final_decision == DecisionType.CAUTION.value:
            safety_status = "CAUTION / HEIGHTENED VIGILANCE"
        elif final_decision == DecisionType.INSUFFICIENT_EVIDENCE.value:
            safety_status = "UNVERIFIED / INSUFFICIENT DATA"
        else:
            safety_status = "NORMAL OPERATIONAL PARAMETERS"

        if not guardrail_actions:
            guardrail_actions.append("No overriding official warnings or spatial barriers detected; operational parameters validated.")

        return (
            final_decision,
            sanitized_summary,
            adjusted_confidence,
            safety_status,
            guardrail_actions,
        )
