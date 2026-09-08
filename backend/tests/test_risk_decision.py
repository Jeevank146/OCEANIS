import os
import sys
import pytest
from datetime import datetime, timezone
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from orchestrator.confidence import ConfidenceEngine
from orchestrator.evidence import EvidenceFusionEngine
from orchestrator.guardrails import SafetyGuardrailEngine
from orchestrator.risk import RiskDecisionEngine
from schemas.agent_contract import (
    AgentResult,
    AgentStatus,
    DataFreshness,
    DecisionType,
    EvidenceItem,
    ObservationType,
)


def test_official_warning_forces_not_recommended_veto():
    risk_engine = RiskDecisionEngine()
    guardrails = SafetyGuardrailEngine()

    warning_item = EvidenceItem(
        source="IMD Cyclone Warning Center",
        parameter="cyclone_track_warning",
        value="Very Severe Cyclonic Storm Alert - Red Warning for East Coast",
        observation_type=ObservationType.OFFICIAL_WARNING.value,
        timestamp="2026-09-08T12:00:00Z",
        freshness=DataFreshness.FRESH.value,
    )

    disaster_res = AgentResult(
        agent_name="Disaster & Safety",
        status=AgentStatus.SUCCESS.value,
        summary="Active cyclone warning",
        findings=["Severe storm track approaching"],
        evidence=[warning_item],
        confidence=0.98,
        warnings=["RED ALERT: Cyclone warning active within 50 km"],
    )

    fusion = EvidenceFusionEngine()
    fused = fusion.fuse({"disaster_safety": disaster_res})

    raw_decision, risk_level, risk_factors, rec_points = risk_engine.evaluate(
        fused_evidence=fused,
        agent_results={"disaster_safety": disaster_res},
        is_inland=False,
    )

    assert raw_decision == DecisionType.NOT_RECOMMENDED.value
    assert risk_level == "CRITICAL"
    assert len(risk_factors) > 0

    # Test safety guardrails cannot override warning
    final_dec, sanitized, conf, safety_status, actions = guardrails.apply_guardrails(
        raw_decision=raw_decision,
        summary="AI assessed the voyage as possible.",
        fused_evidence=fused,
        agent_results={"disaster_safety": disaster_res},
        confidence_score=85,
    )

    assert final_dec == DecisionType.NOT_RECOMMENDED.value
    assert "RESTRICTED" in safety_status
    assert any("NOT_RECOMMENDED enforced" in a for a in actions)


def test_calm_conditions_produce_suitable():
    risk_engine = RiskDecisionEngine()

    calm_wave = EvidenceItem(
        source="INCOIS",
        parameter="wave_height",
        value=0.8,
        unit="m",
        observation_type=ObservationType.OBSERVED.value,
        timestamp="2026-09-08T12:00:00Z",
        freshness=DataFreshness.FRESH.value,
    )
    calm_wind = EvidenceItem(
        source="IMD",
        parameter="wind_speed",
        value=14.0,
        unit="km/h",
        observation_type=ObservationType.OBSERVED.value,
        timestamp="2026-09-08T12:00:00Z",
        freshness=DataFreshness.FRESH.value,
    )

    agent_mc = AgentResult(
        agent_name="Marine Conditions",
        status=AgentStatus.SUCCESS.value,
        summary="Calm conditions",
        findings=["Wave 0.8m", "Wind 14 km/h"],
        evidence=[calm_wave, calm_wind],
        confidence=0.92,
        warnings=[],
    )

    fusion = EvidenceFusionEngine()
    fused = fusion.fuse({"marine_conditions": agent_mc})

    raw_decision, risk_level, risk_factors, rec = risk_engine.evaluate(
        fused_evidence=fused,
        agent_results={"marine_conditions": agent_mc},
        is_inland=False,
    )

    assert raw_decision == DecisionType.SUITABLE.value
    assert risk_level == "LOW"


def test_confidence_engine_scoring_and_penalties():
    conf_engine = ConfidenceEngine()
    fusion = EvidenceFusionEngine()

    fresh_item = EvidenceItem(
        source="IMD",
        parameter="wind_speed",
        value=15.0,
        unit="km/h",
        observation_type=ObservationType.OBSERVED.value,
        timestamp="2026-09-08T12:00:00Z",
        freshness=DataFreshness.FRESH.value,
    )

    agent_res = AgentResult(
        agent_name="Marine Conditions",
        status=AgentStatus.SUCCESS.value,
        summary="OK",
        findings=["Wind 15 km/h"],
        evidence=[fresh_item],
        confidence=0.9,
    )

    fused = fusion.fuse({"marine_conditions": agent_res})
    score, reasons = conf_engine.calculate(
        fused_evidence=fused,
        agent_results={"marine_conditions": agent_res},
        is_inland=False,
    )

    assert 0 <= score <= 100
    assert len(reasons) > 0
    assert any("Domain Agents" in r or "domain agents" in r for r in reasons)
