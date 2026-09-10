from orchestrator.what_if import WhatIfEngine
from schemas.agent_contract import DecisionType


def test_time_shift_never_invents_conditions_without_indexed_forecast():
    result = WhatIfEngine().simulate(
        base_decision=DecisionType.SUITABLE.value,
        base_confidence=82,
        base_time="10:15",
        base_location_name="User Selected Sector",
        base_lat=11.25,
        base_lon=74.75,
        base_conditions=["Observed wave evidence"],
        modified_time="13:15",
        fused_forecast_items=[],
    )

    assert result.status == "insufficient_evidence"
    assert result.what_if_scenario.decision == DecisionType.INSUFFICIENT_EVIDENCE.value
    assert result.what_if_scenario.confidence_score == 0
    assert result.what_if_scenario.key_conditions == []


def test_dynamic_location_is_preserved_without_city_fallback():
    result = WhatIfEngine().simulate(
        base_decision=DecisionType.CAUTION.value,
        base_confidence=64,
        base_time="07:20",
        base_location_name="Operator Entered Ground",
        base_lat=8.1,
        base_lon=76.2,
        base_conditions=["Current evidence"],
        modified_lat=8.4,
        modified_lon=76.6,
        modified_location_name="Explicit Scenario Ground",
    )

    assert result.status == "insufficient_evidence"
    assert result.base_scenario.location_name == "Operator Entered Ground"
    assert result.what_if_scenario.location_name == "Explicit Scenario Ground"
    assert result.what_if_scenario.latitude == 8.4
    assert result.what_if_scenario.longitude == 76.6
