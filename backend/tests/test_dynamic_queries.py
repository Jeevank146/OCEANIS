import os
import sys
from datetime import datetime, timezone
import pytest
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from database import SessionLocal
from orchestrator.orchestrator import AgentOrchestrator
from orchestrator.planner import OrchestratorPlanner
from orchestrator.schemas import OrchestrationQuery
from schemas.agent_contract import DecisionType, QueryIntent


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_information_query_ocean_conditions(db_session):
    """
    Test: 'What are the ocean conditions near Chennai tomorrow?'
    Intent: INFORMATION
    Expected Agents: 3 (Marine Conditions, Earth Observation, Geo-Spatial)
    Decision: Information (not forced to Suitable/Caution)
    """
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(query="What are the ocean conditions near Chennai tomorrow?")
    result = orchestrator.decide(db=db_session, query=query)

    assert result.query_intent == QueryIntent.INFORMATION.value
    assert result.decision == DecisionType.INFORMATION_ONLY.value
    assert result.location is not None
    assert "chennai" in result.location.get("name", "").lower()
    assert result.agents_consulted_count >= 2
    assert result.agents_consulted_count < 6  # Selective invocation
    assert result.primary_answer is not None
    assert len(result.primary_answer) > 20


def test_safety_query_cyclone_warning(db_session):
    """
    Test: 'Is there any cyclone warning near Visakhapatnam?'
    Intent: SAFETY
    Expected: Disaster & Safety agent consulted with active warning evaluation.
    """
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(query="Is there any cyclone warning near Visakhapatnam?")
    result = orchestrator.decide(db=db_session, query=query)

    assert result.query_intent == QueryIntent.SAFETY.value
    assert result.location is not None
    assert "visakhapatnam" in result.location.get("name", "").lower()
    agent_names = [ag.agent_name for ag in result.agents_consulted]
    assert "Disaster & Safety" in agent_names
    assert result.primary_answer is not None
    assert "warning" in result.primary_answer.lower() or "cyclone" in result.primary_answer.lower() or "clear" in result.primary_answer.lower()


def test_remote_sensing_query_sst_chlorophyll(db_session):
    """
    Test: 'Show SST and chlorophyll near Paradip'
    Intent: INFORMATION (Earth Observation focus)
    """
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(query="Show SST and chlorophyll near Paradip")
    result = orchestrator.decide(db=db_session, query=query)

    assert result.query_intent == QueryIntent.INFORMATION.value
    assert result.location is not None
    assert "paradip" in result.location.get("name", "").lower()
    agent_names = [ag.agent_name for ag in result.agents_consulted]
    assert "Earth Observation" in agent_names
    assert result.primary_answer is not None
    assert "temperature" in result.primary_answer.lower() or "chlorophyll" in result.primary_answer.lower() or "paradip" in result.primary_answer.lower()


def test_comparison_query_ports(db_session):
    """
    Test: 'Which is better for fishing, Kakinada or Visakhapatnam?'
    Intent: COMPARISON
    Expected: ComparisonResult populated with both candidate locations and recommendation.
    """
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(query="Which is better for fishing, Kakinada or Visakhapatnam?")
    result = orchestrator.decide(db=db_session, query=query)

    assert result.query_intent == QueryIntent.COMPARISON.value
    assert result.comparison_data is not None
    assert len(result.comparison_data.target_locations) == 2
    assert result.comparison_data.recommended_location is not None
    assert result.primary_answer is not None
    assert "comparing" in result.primary_answer.lower()


def test_what_if_query_dynamic(db_session):
    """
    Test: 'What if I leave at 9 AM instead?' with coordinates provided in payload.
    Intent: WHAT_IF
    """
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(
        query="What if I leave at 9 AM instead?",
        latitude=16.9891,
        longitude=82.2475,
    )
    result = orchestrator.decide(db=db_session, query=query)

    assert result.query_intent == QueryIntent.WHAT_IF.value
    assert result.what_if_comparison is not None
    assert result.what_if_comparison.what_if_scenario is not None
    assert result.what_if_comparison.what_if_scenario.departure_time == "09:00"


def test_missing_location_handling(db_session):
    """
    Test: 'What is the SST?' without specifying a city or coordinates.
    Expected: Insufficient Evidence with prompt to specify location, NO hardcoded Visakhapatnam/Kakinada fallback.
    """
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(query="What is the SST?")
    result = orchestrator.decide(db=db_session, query=query)

    assert result.decision == DecisionType.INSUFFICIENT_EVIDENCE.value
    assert result.confidence == 0
    assert result.location is None
    assert "specify a coastal location" in result.primary_answer.lower()


def test_inland_protection(db_session):
    """
    Test: 'Can I go ocean fishing in New Delhi?'
    Expected: Not Recommended or Insufficient Evidence, 0% confidence, inland protection explanation.
    """
    orchestrator = AgentOrchestrator()
    query = OrchestrationQuery(query="Can I go ocean fishing in New Delhi?")
    result = orchestrator.decide(db=db_session, query=query)

    assert result.decision in [DecisionType.NOT_RECOMMENDED.value, DecisionType.INSUFFICIENT_EVIDENCE.value]
    assert result.confidence == 0
    assert result.location is not None
    assert result.location.get("is_inland") is True
    assert "inland" in result.primary_answer.lower()
