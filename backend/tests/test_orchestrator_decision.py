import os
import sys
import pytest
from datetime import datetime, timezone
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from database import SessionLocal
from orchestrator.orchestrator import AgentOrchestrator
from orchestrator.schemas import OrchestrationQuery
from schemas.agent_contract import DecisionType, FinalDecisionObject, WhatIfComparison


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_end_to_end_kakinada_fishing_decision(db_session):
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(
        query="Can I go fishing tomorrow at 6 AM from Kakinada?",
    )

    decision_obj = orchestrator.decide(db=db_session, query=query)

    assert isinstance(decision_obj, FinalDecisionObject)
    assert decision_obj.decision in [
        DecisionType.SUITABLE.value,
        DecisionType.CAUTION.value,
        DecisionType.NOT_RECOMMENDED.value,
        DecisionType.INSUFFICIENT_EVIDENCE.value,
    ]
    assert 0 <= decision_obj.confidence <= 100
    assert len(decision_obj.confidence_reasons) > 0
    assert decision_obj.safety_status is not None
    assert len(decision_obj.guardrail_actions) > 0
    assert len(decision_obj.agents_consulted) == 6
    assert decision_obj.location is not None
    assert "Kakinada" in decision_obj.location.get("name", "")
    assert abs(decision_obj.location["latitude"] - 16.9890) < 0.2

    # Check Why Breakdown
    assert len(decision_obj.why_decision.marine_conditions) > 0
    assert len(decision_obj.why_decision.ocean_conditions) > 0
    assert len(decision_obj.why_decision.eo_indicators) > 0
    assert len(decision_obj.why_decision.spatial_constraints) > 0
    assert len(decision_obj.why_decision.safety_warnings) > 0
    assert len(decision_obj.why_decision.operational_factors) > 0


def test_dynamic_coastal_location_independence_paradip(db_session):
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(
        query="Can I sail from Paradip tomorrow at 8 AM?",
    )

    decision_obj = orchestrator.decide(db=db_session, query=query)
    assert decision_obj.location is not None
    assert "Paradip" in decision_obj.location.get("name", "")
    assert abs(decision_obj.location["latitude"] - 20.2600) < 0.2


def test_inland_protection_blocking_hyderabad(db_session):
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(
        query="Can I go ocean fishing in Hyderabad?",
        latitude=17.3850,
        longitude=78.4867,
    )

    decision_obj = orchestrator.decide(db=db_session, query=query)
    assert decision_obj.decision == DecisionType.INSUFFICIENT_EVIDENCE.value
    assert decision_obj.location["is_inland"] is True
    assert "INLAND" in decision_obj.summary


def test_what_if_scenario_simulation(db_session):
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(
        query="Can I go fishing tomorrow at 6 AM from Kakinada?",
    )

    decision_obj = orchestrator.decide(
        db=db_session,
        query=query,
        what_if_time="09:00",
    )

    assert decision_obj.what_if_comparison is not None
    assert isinstance(decision_obj.what_if_comparison, WhatIfComparison)
    assert decision_obj.what_if_comparison.status == "success"
    assert len(decision_obj.what_if_comparison.changed_factors) > 0
    assert decision_obj.what_if_comparison.base_scenario.departure_time == "06:00"
    assert decision_obj.what_if_comparison.what_if_scenario.departure_time == "09:00"
