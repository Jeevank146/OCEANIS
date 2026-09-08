import os
import sys
import pytest
from datetime import datetime, timezone
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from database import SessionLocal
from orchestrator.executor import AgentExecutor
from orchestrator.schemas import AgentSelection, LocationContext, QueryUnderstanding
from schemas.agent_contract import AgentResult, AgentStatus, DataFreshness, EvidenceItem


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_agent_executor_executes_all_six_domain_agents(db_session):
    executor = AgentExecutor()
    understanding = QueryUnderstanding(
        intent="FISHING_ASSESSMENT",
        primary_location=LocationContext(
            name="Kakinada Port",
            latitude=16.9890,
            longitude=82.2474,
            is_port=True,
        ),
        target_date="2026-09-09",
        target_time="06:00",
        vessel_type="MOTORIZED_BOAT",
        operation_type="FISHING_TRIP",
        is_comparison=False,
    )

    all_six_selections = [
        AgentSelection(agent_id="disaster_safety", agent_name="Disaster & Safety", domain="Safety", selection_reason="Alerts", priority=1, execution_order=1),
        AgentSelection(agent_id="geospatial_navigation", agent_name="Geo-Spatial & Navigation", domain="GIS", selection_reason="Boundaries", priority=2, execution_order=2),
        AgentSelection(agent_id="marine_conditions", agent_name="Marine Conditions", domain="Physics", selection_reason="Waves", priority=3, execution_order=3),
        AgentSelection(agent_id="earth_observation", agent_name="Earth Observation", domain="Satellite", selection_reason="Chlorophyll", priority=4, execution_order=4),
        AgentSelection(agent_id="marine_operations", agent_name="Marine Operations", domain="Voyage", selection_reason="Transit", priority=5, execution_order=5),
        AgentSelection(agent_id="fishing", agent_name="Fishing Intelligence", domain="Fisheries", selection_reason="Suitability", priority=6, execution_order=6),
    ]

    results = executor.execute_selected_agents(
        db=db_session,
        selected_agents=all_six_selections,
        understanding=understanding,
    )

    assert len(results) == 6
    assert "disaster_safety" in results
    assert "geospatial_navigation" in results
    assert "marine_conditions" in results
    assert "earth_observation" in results
    assert "marine_operations" in results
    assert "fishing" in results

    for agent_id, res in results.items():
        assert isinstance(res, AgentResult)
        assert res.agent_name is not None
        assert res.status in [AgentStatus.SUCCESS.value, AgentStatus.PARTIAL.value, AgentStatus.UNAVAILABLE.value, AgentStatus.ERROR.value]
        assert isinstance(res.findings, list)
        assert isinstance(res.evidence, list)
        assert 0.0 <= res.confidence <= 1.0
        assert isinstance(res.warnings, list)
        assert isinstance(res.limitations, list)


def test_individual_agent_evidence_contract(db_session):
    executor = AgentExecutor()
    understanding = QueryUnderstanding(
        intent="MARINE_CONDITIONS",
        primary_location=LocationContext(
            name="Visakhapatnam Coast",
            latitude=17.6868,
            longitude=83.2185,
            is_port=True,
        ),
        target_date="2026-09-09",
        target_time="06:00",
    )

    sel = [AgentSelection(agent_id="marine_conditions", agent_name="Marine Conditions", domain="Physics", selection_reason="Waves", priority=1, execution_order=1)]
    results = executor.execute_selected_agents(db=db_session, selected_agents=sel, understanding=understanding)

    mc_res = results["marine_conditions"]
    assert mc_res.status == AgentStatus.SUCCESS.value
    assert len(mc_res.evidence) > 0
    for item in mc_res.evidence:
        assert isinstance(item, EvidenceItem)
        assert item.source is not None
        assert item.parameter is not None
        assert item.observation_type in ["Observed", "Forecast", "Official Warning", "AI Assessment"]
        assert item.freshness in ["Fresh", "Aging", "Stale", "Unavailable"]
