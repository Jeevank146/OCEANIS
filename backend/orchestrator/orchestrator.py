from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from orchestrator.evidence import EvidenceFusionEngine
from orchestrator.executor import AgentExecutor
from orchestrator.planner import OrchestratorPlanner
from orchestrator.reasoning import OrchestratorReasoningEngine
from orchestrator.schemas import (
    ExecutionMetadata,
    OrchestrationQuery,
    OrchestrationResponse,
)


class AgentOrchestrator:
    """
    Central OCEANIS Agent Orchestrator.
    Dynamically receives natural-language user queries, understands context,
    selects required domain agents, coordinates structured execution and evidence fusion,
    enforces deterministic safety overrides, and synthesizes explainable decision responses.
    """

    def __init__(
        self,
        planner: Optional[OrchestratorPlanner] = None,
        executor: Optional[AgentExecutor] = None,
        evidence_engine: Optional[EvidenceFusionEngine] = None,
        reasoning_engine: Optional[OrchestratorReasoningEngine] = None,
    ):
        self.planner = planner or OrchestratorPlanner()
        self.executor = executor or AgentExecutor()
        self.evidence_engine = evidence_engine or EvidenceFusionEngine()
        self.reasoning_engine = reasoning_engine or OrchestratorReasoningEngine()

    def orchestrate(
        self,
        db: Session,
        query: OrchestrationQuery,
        now: Optional[datetime] = None,
    ) -> OrchestrationResponse:
        """
        Executes end-to-end multi-agent orchestration.
        """
        start_time = time.perf_counter()
        now_utc = now or datetime.now(timezone.utc)

        # 1. Query Understanding & Dynamic Agent Selection
        understanding, selected_agents = self.planner.plan(query=query, now=now_utc)

        # 2. Structured Agent Execution
        agent_results = self.executor.execute_selected_agents(
            db=db,
            selected_agents=selected_agents,
            understanding=understanding,
            now=now_utc,
        )

        # 3. Evidence Fusion
        fused_evidence = self.evidence_engine.fuse(agent_results=agent_results)

        # 4. Decision Synthesis & Safety Reasoning
        (
            decision,
            risk_level,
            confidence,
            freshness,
            warnings,
            reasoning_summary,
            agent_contributions,
            comparison_results,
        ) = self.reasoning_engine.synthesize(
            query=query.query,
            understanding=understanding,
            agent_results=agent_results,
            fused_evidence=fused_evidence,
        )

        # 5. Execution Telemetry
        total_duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        successful_agents = [res.agent_id for res in agent_results.values() if res.status == "SUCCESS"]
        failed_agents = [res.agent_id for res in agent_results.values() if res.status == "FAILED"]

        execution_meta = ExecutionMetadata(
            selected_agents=[s.agent_id for s in selected_agents],
            execution_order=[s.agent_id for s in selected_agents],
            execution_duration_ms=total_duration_ms,
            successful_agents=successful_agents,
            failed_agents=failed_agents,
            evidence_count=len(fused_evidence),
        )

        loc_dict = (
            {
                "name": understanding.primary_location.name,
                "latitude": understanding.primary_location.latitude,
                "longitude": understanding.primary_location.longitude,
                "is_port": understanding.primary_location.is_port,
                "port_name": understanding.primary_location.port_name,
            }
            if understanding.primary_location
            else None
        )

        target_time_str = (
            f"{understanding.target_date}T{understanding.target_time}:00Z"
            if understanding.target_date and understanding.target_time
            else (understanding.target_date or understanding.target_time)
        )

        return OrchestrationResponse(
            query=query.query,
            intent=understanding.intent,
            location=loc_dict,
            target_time=target_time_str,
            selected_agents=selected_agents,
            decision=decision,
            risk_level=risk_level,
            confidence=confidence,
            freshness=freshness,
            evidence=fused_evidence,
            warnings=warnings,
            reasoning_summary=reasoning_summary,
            agent_contributions=agent_contributions,
            execution_metadata=execution_meta,
            comparison_results=comparison_results,
            generated_at=now_utc,
        )
