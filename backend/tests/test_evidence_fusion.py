import os
import sys
import pytest
from datetime import datetime, timezone
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from orchestrator.evidence import EvidenceFusionEngine
from schemas.agent_contract import (
    AgentResult,
    AgentStatus,
    DataFreshness,
    EvidenceItem,
    ObservationType,
)


def test_evidence_fusion_deduplication():
    engine = EvidenceFusionEngine()

    item1 = EvidenceItem(
        source="INCOIS",
        parameter="wave_height",
        value=1.5,
        unit="m",
        observation_type=ObservationType.OBSERVED.value,
        timestamp="2026-09-08T12:00:00Z",
        freshness=DataFreshness.FRESH.value,
    )
    # Duplicate item with same parameter, value, timestamp, source
    item2 = EvidenceItem(
        source="INCOIS",
        parameter="wave_height",
        value=1.5,
        unit="m",
        observation_type=ObservationType.OBSERVED.value,
        timestamp="2026-09-08T12:00:00Z",
        freshness=DataFreshness.FRESH.value,
    )
    item3 = EvidenceItem(
        source="IMD",
        parameter="wind_speed",
        value=22.0,
        unit="km/h",
        observation_type=ObservationType.OBSERVED.value,
        timestamp="2026-09-08T12:00:00Z",
        freshness=DataFreshness.FRESH.value,
    )

    agent_a = AgentResult(
        agent_name="Marine Conditions",
        status=AgentStatus.SUCCESS.value,
        summary="Marine physics",
        findings=["Wave height 1.5m", "Wind speed 22 km/h"],
        evidence=[item1, item3],
        confidence=0.9,
    )
    agent_b = AgentResult(
        agent_name="Fishing Intelligence",
        status=AgentStatus.SUCCESS.value,
        summary="Fisheries",
        findings=["Good wave state"],
        evidence=[item2],
        confidence=0.85,
    )

    fused = engine.fuse({"marine_conditions": agent_a, "fishing": agent_b})

    # Deduplication must reduce 3 input items to 2 unique items
    assert len(fused.evidence_items) == 2
    params = [it.parameter for it in fused.evidence_items]
    assert "wave_height" in params
    assert "wind_speed" in params
    assert fused.real_data_count == 2
    assert fused.ai_assessment_count == 0


def test_evidence_fusion_conflict_detection():
    engine = EvidenceFusionEngine()

    # Conflicting wind speeds across sources (15 km/h vs 50 km/h)
    item_calm = EvidenceItem(
        source="Source A",
        parameter="wind_speed",
        value=15.0,
        unit="km/h",
        observation_type=ObservationType.OBSERVED.value,
        timestamp="2026-09-08T12:00:00Z",
        freshness=DataFreshness.FRESH.value,
    )
    item_storm = EvidenceItem(
        source="Source B",
        parameter="wind_speed",
        value=52.0,
        unit="km/h",
        observation_type=ObservationType.OBSERVED.value,
        timestamp="2026-09-08T12:00:00Z",
        freshness=DataFreshness.FRESH.value,
    )

    agent_calm = AgentResult(
        agent_name="Agent Calm",
        status=AgentStatus.SUCCESS.value,
        summary="Calm",
        findings=["Wind 15 km/h"],
        evidence=[item_calm],
        confidence=0.9,
    )
    agent_storm = AgentResult(
        agent_name="Agent Storm",
        status=AgentStatus.SUCCESS.value,
        summary="Storm",
        findings=["Wind 52 km/h"],
        evidence=[item_storm],
        confidence=0.9,
    )

    fused = engine.fuse({"calm": agent_calm, "storm": agent_storm})
    assert len(fused.conflicts) > 0
    assert any("wind_speed" in str(c.get("parameter")) for c in fused.conflicts)
