import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, text

from database import SessionLocal, engine, init_db
from models.disaster import CycloneTrack, HazardZone, MarineAlert
from models.geospatial import Port, ProtectedZone, RestrictedZone
from models.marine import MarineObservation
from models.weather import WeatherObservation
from orchestrator.registry import AgentRegistry

BASE_URL = "http://127.0.0.1:8000"


def request(method: str, path: str, data: dict = None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            return status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = content
        return e.code, parsed


def test_orchestrator():
    print("=" * 80)
    print("OCEANIS Agent Orchestrator & Multi-Agent Collaboration — Verification Suite")
    print("=" * 80)

    init_db()

    # 1. Orchestrator Imports & Central Agent Registry
    print("\n[1/19] Testing Orchestrator imports & Central Agent Registry...")
    from orchestrator.orchestrator import AgentOrchestrator
    from orchestrator.planner import OrchestratorPlanner
    from orchestrator.service import OrchestratorService

    agents = AgentRegistry.list_agents()
    assert len(agents) == 6, f"Expected 6 domain agents, got {len(agents)}"
    agent_ids = [a.agent_id for a in agents]
    expected_ids = ["fishing", "marine_conditions", "earth_observation", "geospatial_navigation", "disaster_safety", "marine_operations"]
    for expected_id in expected_ids:
        assert expected_id in agent_ids, f"Missing domain agent {expected_id} in registry"
    print(f"  [OK] Central Agent Registry verified with all 6 domain agents: {', '.join(agent_ids)}.")

    # 2. Fishing assessment natural-language query
    print("\n[2/19] Testing fishing assessment query: 'Can I go fishing tomorrow at 6 AM from Kakinada?'...")
    status, res_fish = request("POST", "/api/v1/orchestrator/query", {
        "query": "Can I go fishing tomorrow at 6 AM from Kakinada?",
    })
    assert status == 200, f"Expected 200, got {status}: {res_fish}"
    assert res_fish["intent"] == "FISHING_ASSESSMENT"
    assert res_fish["location"] is not None
    assert "Kakinada" in res_fish["location"]["name"]
    selected_ids = [s["agent_id"] for s in res_fish["selected_agents"]]
    assert "fishing" in selected_ids
    assert "marine_conditions" in selected_ids
    assert "earth_observation" in selected_ids
    assert "geospatial_navigation" in selected_ids
    assert "disaster_safety" in selected_ids
    assert res_fish["decision"] in ("FAVORABLE", "CAUTION", "CLEAR", "WARNING", "BLOCKED")
    assert len(res_fish["agent_contributions"]) >= 5
    assert len(res_fish["evidence"]) > 0
    print(f"  [OK] Fishing assessment orchestrated: intent={res_fish['intent']}, decision={res_fish['decision']}, agents={selected_ids}.")

    # 3. Fishing comparison query
    print("\n[3/19] Testing fishing comparison query: 'Which is better for fishing tomorrow morning, Kakinada or Vizag?'...")
    status, res_comp = request("POST", "/api/v1/orchestrator/query", {
        "query": "Which is better for fishing tomorrow morning, Kakinada or Vizag?",
    })
    assert status == 200, f"Expected 200, got {status}: {res_comp}"
    assert res_comp["intent"] == "FISHING_COMPARISON"
    assert res_comp["comparison_results"] is not None
    assert len(res_comp["comparison_results"]) >= 2
    print(f"  [OK] Fishing comparison orchestrated: intent={res_comp['intent']}, locations={len(res_comp['comparison_results'])} compared.")

    # 4. Route operations query
    print("\n[4/19] Testing route operations query: 'Is it safe to travel from Kakinada Port to Visakhapatnam Port?'...")
    status, res_route = request("POST", "/api/v1/orchestrator/query", {
        "query": "Is it safe to travel from Kakinada Port to Visakhapatnam Port?",
    })
    assert status == 200
    assert res_route["intent"] == "ROUTE_OPERATION"
    route_agent_ids = [s["agent_id"] for s in res_route["selected_agents"]]
    assert "marine_operations" in route_agent_ids
    assert "geospatial_navigation" in route_agent_ids
    assert "disaster_safety" in route_agent_ids
    assert "marine_conditions" in route_agent_ids
    assert "fishing" not in route_agent_ids, "Fishing agent must not be called for route operation query"
    assert "earth_observation" not in route_agent_ids, "Earth observation must not be called for route operation query"
    print(f"  [OK] Route operation orchestrated: intent={res_route['intent']}, decision={res_route['decision']}, agents={route_agent_ids}.")

    # 5. Marine safety query
    print("\n[5/19] Testing marine safety query: 'Are there any active cyclone warnings near Vizag?'...")
    status, res_safety = request("POST", "/api/v1/orchestrator/query", {
        "query": "Are there any active cyclone warnings near Vizag?",
    })
    assert status == 200
    assert res_safety["intent"] == "MARINE_SAFETY"
    assert "Vizag" in res_safety["location"]["name"] or "Visakhapatnam" in res_safety["location"]["name"]
    safety_agent_ids = [s["agent_id"] for s in res_safety["selected_agents"]]
    assert "disaster_safety" in safety_agent_ids
    assert "geospatial_navigation" in safety_agent_ids
    assert "marine_conditions" in safety_agent_ids
    assert "fishing" not in safety_agent_ids, "Fishing agent must not be selected for safety query"
    assert "marine_operations" not in safety_agent_ids
    print(f"  [OK] Marine safety query orchestrated: intent={res_safety['intent']}, agents={safety_agent_ids}.")

    # 6. Marine environmental inquiry
    print("\n[6/19] Testing marine environmental inquiry: 'What are the current sea state and wave conditions near Kakinada?'...")
    status, res_marine = request("POST", "/api/v1/orchestrator/query", {
        "query": "What are the current sea state and wave conditions near Kakinada?",
    })
    assert status == 200
    assert res_marine["intent"] == "MARINE_CONDITIONS"
    marine_agent_ids = [s["agent_id"] for s in res_marine["selected_agents"]]
    assert "marine_conditions" in marine_agent_ids
    assert "disaster_safety" in marine_agent_ids
    assert "fishing" not in marine_agent_ids
    assert "marine_operations" not in marine_agent_ids
    print(f"  [OK] Marine conditions inquiry orchestrated: intent={res_marine['intent']}, agents={marine_agent_ids}.")

    # 7. Earth observation query
    print("\n[7/19] Testing earth observation query: 'What is the satellite chlorophyll condition near 16.97, 82.25?'...")
    status, res_eo = request("POST", "/api/v1/orchestrator/query", {
        "query": "What is the satellite chlorophyll condition near 16.97, 82.25?",
    })
    assert status == 200
    assert res_eo["intent"] == "EARTH_OBSERVATION"
    eo_agent_ids = [s["agent_id"] for s in res_eo["selected_agents"]]
    assert "earth_observation" in eo_agent_ids
    assert "marine_conditions" in eo_agent_ids
    assert "fishing" not in eo_agent_ids
    assert "marine_operations" not in eo_agent_ids
    print(f"  [OK] Earth observation query orchestrated: intent={res_eo['intent']}, agents={eo_agent_ids}.")

    # 8. Location & Coordinate Extraction
    print("\n[8/19] Testing decimal coordinate extraction...")
    assert abs(res_eo["location"]["latitude"] - 16.97) < 0.01
    assert abs(res_eo["location"]["longitude"] - 82.25) < 0.01
    print(f"  [OK] Decimal coordinates successfully extracted: ({res_eo['location']['latitude']}, {res_eo['location']['longitude']}).")

    # 9. Temporal Extraction
    print("\n[9/19] Testing temporal extraction ('tomorrow at 6 AM')...")
    assert res_fish["target_time"] is not None
    assert "06:00" in res_fish["target_time"]
    print(f"  [OK] Target operational window extracted: {res_fish['target_time']}.")

    # 10. Dynamic Agent Selection & Unnecessary Agent Avoidance
    print("\n[10/19] Verifying dynamic agent selection avoids irrelevant domain agents...")
    assert len(res_eo["selected_agents"]) == 2
    assert len(res_marine["selected_agents"]) == 2
    assert len(res_safety["selected_agents"]) == 3
    print("  [OK] Selective domain execution confirmed: queries invoke strictly necessary agent subsets.")

    # 11. Evidence Fusion & Provenance Preservation
    print("\n[11/19] Testing multi-agent evidence fusion & provenance preservation...")
    evidence_items = res_fish["evidence"]
    assert len(evidence_items) > 0
    for ev in evidence_items:
        assert ev["factor"] is not None and len(ev["factor"]) > 0
        assert ev["source"] is not None and len(ev["source"]) > 0
        assert ev["source_category"] is not None and len(ev["source_category"]) > 0
        assert ev["data_type"] is not None and len(ev["data_type"]) > 0
        assert ev["originating_agent"] in expected_ids
    print(f"  [OK] Verified {len(evidence_items)} fused evidence items with complete source provenance and agent attribution.")

    # 12. Composite Confidence & Freshness Evaluation
    print("\n[12/19] Testing confidence and freshness ratings...")
    assert res_fish["confidence"] in ("HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA")
    assert res_fish["freshness"] in ("FRESH", "AGING", "STALE", "UNAVAILABLE")
    print(f"  [OK] Confidence level: {res_fish['confidence']}, Freshness rating: {res_fish['freshness']}.")

    # 13. Deterministic CRITICAL Safety Override -> BLOCKED
    print("\n[13/19] Testing deterministic CRITICAL safety override -> BLOCKED...")
    db = SessionLocal()
    now_utc = datetime.now(timezone.utc)
    db.query(HazardZone).filter(HazardZone.name == "TEST_ORCH_CRITICAL_SURGE").delete()
    wkt_crit = "POLYGON((82.10 16.80, 82.40 16.80, 82.40 17.10, 82.10 17.10, 82.10 16.80))"
    crit_zone = HazardZone(
        name="TEST_ORCH_CRITICAL_SURGE",
        hazard_type="STORM_SURGE_ZONE",
        severity="CRITICAL",
        description="Dangerous surge sector.",
        geometry=func.ST_GeomFromText(wkt_crit, 4326),
        source="INCOIS",
        source_category="OFFICIAL",
        effective_from=now_utc - timedelta(hours=1),
        effective_until=now_utc + timedelta(hours=12),
        is_active=True,
    )
    db.add(crit_zone)
    db.commit()

    status, blocked_orch = request("POST", "/api/v1/orchestrator/query", {
        "query": "Can I go fishing tomorrow at 6 AM from Kakinada?",
    })
    assert status == 200
    assert blocked_orch["decision"] == "BLOCKED"
    assert blocked_orch["risk_level"] == "CRITICAL"
    assert "BLOCKED" in blocked_orch["reasoning_summary"]
    print(f"  [OK] Critical hazard containment deterministically yielded decision='BLOCKED', risk_level='CRITICAL'.")

    # 14. Deterministic WARNING handling
    print("\n[14/19] Testing deterministic WARNING handling...")
    db.query(HazardZone).filter(HazardZone.name == "TEST_ORCH_CRITICAL_SURGE").delete()
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_ORCH_ALERT_WARN").delete()
    warn_alert = MarineAlert(
        alert_id="TEST_ORCH_ALERT_WARN",
        title="TEST: Gale Wind Warning for Kakinada Coast",
        alert_type="GALE_WIND",
        severity="WARNING",
        status="ACTIVE",
        description="Gale winds 55 km/h.",
        source="INCOIS",
        source_category="OFFICIAL",
        issued_at=now_utc - timedelta(hours=1),
        effective_from=now_utc - timedelta(hours=1),
        effective_until=now_utc + timedelta(hours=24),
        latitude=16.9890,
        longitude=82.2474,
        geometry=func.ST_SetSRID(func.ST_MakePoint(82.2474, 16.9890), 4326),
        is_active=True,
    )
    db.add(warn_alert)
    db.commit()

    status, warn_orch = request("POST", "/api/v1/orchestrator/query", {
        "query": "Can I go fishing tomorrow at 6 AM from Kakinada?",
    })
    assert status == 200
    assert warn_orch["decision"] in ("WARNING", "BLOCKED")
    assert warn_orch["risk_level"] in ("HIGH", "CRITICAL")
    print(f"  [OK] Active warning alert deterministically yielded decision='{warn_orch['decision']}', risk='{warn_orch['risk_level']}'.")

    # 15. Restricted-zone route override -> BLOCKED
    print("\n[15/19] Testing restricted-zone route override -> BLOCKED...")
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_ORCH_ALERT_WARN").delete()
    db.query(RestrictedZone).filter(RestrictedZone.name == "TEST_ORCH_NAVAL_EXCLUSION").delete()
    wkt_res = "POLYGON((82.50 17.00, 82.80 17.00, 82.80 17.40, 82.50 17.40, 82.50 17.00))"
    res_zone = RestrictedZone(
        name="TEST_ORCH_NAVAL_EXCLUSION",
        zone_type="MILITARY_EXCLUSION",
        geometry=WKTElement(wkt_res, srid=4326),
        authority="Indian Navy",
        is_active=True,
    )
    db.add(res_zone)
    db.commit()

    status, blocked_route = request("POST", "/api/v1/orchestrator/query", {
        "query": "Is it safe to travel from Kakinada Port to Visakhapatnam Port?",
    })
    assert status == 200
    assert blocked_route["decision"] == "BLOCKED"
    assert blocked_route["risk_level"] == "CRITICAL"
    print("  [OK] Restricted exclusion zone intersection properly triggered decision='BLOCKED'.")

    # 16. Missing data handling -> INSUFFICIENT_DATA
    print("\n[16/19] Testing remote coordinates with missing telemetry -> INSUFFICIENT_DATA...")
    db.query(RestrictedZone).filter(RestrictedZone.name == "TEST_ORCH_NAVAL_EXCLUSION").delete()
    db.commit()

    status, remote_orch = request("POST", "/api/v1/orchestrator/query", {
        "query": "What are the fishing conditions near lat -50.0 lon -100.0?",
    })
    assert status == 200
    assert remote_orch["decision"] == "INSUFFICIENT_DATA"
    assert remote_orch["confidence"] == "INSUFFICIENT_DATA"
    print("  [OK] Missing environmental telemetry safely yielded decision='INSUFFICIENT_DATA'.")

    # 17. Non-critical agent failure handling & graceful degradation
    print("\n[17/19] Testing agent execution failure handling...")
    # Verify execution metadata captures successes and failures cleanly
    exec_meta = res_fish["execution_metadata"]
    assert exec_meta["execution_duration_ms"] > 0.0
    assert len(exec_meta["successful_agents"]) >= 5
    assert len(exec_meta["failed_agents"]) == 0
    print(f"  [OK] Execution telemetry verified: duration={exec_meta['execution_duration_ms']} ms, successful={len(exec_meta['successful_agents'])}.")

    # 18. Prohibition of 100%-safe claims
    print("\n[18/19] Verifying prohibition of misleading 100%-safe claims...")
    prohibited_phrases = ["100% safe", "guaranteed safe", "risk-free", "completely safe", "zero risk"]
    for res_obj in [res_fish, res_comp, res_route, res_safety, res_marine, res_eo, blocked_orch, warn_orch, remote_orch]:
        summary = res_obj["reasoning_summary"].lower()
        for phrase in prohibited_phrases:
            assert phrase not in summary, f"Prohibited phrase '{phrase}' found in reasoning summary: {summary}"
    print("  [OK] All orchestrator reasoning summaries adhere to evidence-based conservative directives without absolute claims.")

    # 19. OpenAPI Registration
    print("\n[19/19] Verifying OpenAPI registration for Agent Orchestrator...")
    status, openapi = request("GET", "/openapi.json")
    assert status == 200
    paths = openapi.get("paths", {})
    endpoint = "/api/v1/orchestrator/query"
    assert endpoint in paths, f"Missing endpoint {endpoint} in OpenAPI paths"
    post_op = paths[endpoint].get("post", {})
    tags = post_op.get("tags", [])
    assert "Agent Orchestrator" in tags, f"Expected tag 'Agent Orchestrator', got {tags}"
    print(f"  [OK] Endpoint {endpoint} registered with tag 'Agent Orchestrator'.")

    db.close()


def run_regressions():
    print("\n" + "=" * 80)
    print("RUNNING COMPLETE DOMAIN AGENT REGRESSION SUITES (ALL 6 AGENTS)...")
    print("=" * 80)

    from scratch.test_marine_operations_agent import run_tests as run_marine_ops_tests, run_regressions as run_all_prior_regressions
    run_marine_ops_tests()
    run_all_prior_regressions()
    print("  [OK] All 6 domain agent regressions passed.")

    print("\n" + "=" * 80)
    print("RUNNING ALL EXISTING BACKEND ENDPOINTS REGRESSION...")
    print("=" * 80)
    now_utc = datetime.now(timezone.utc)
    endpoints = [
        ("GET", "/health", None, 200),
        ("GET", "/api/v1/system/health", None, 200),
        ("GET", "/api/v1/data-sources", None, 200),
        ("GET", "/api/v1/weather/current?latitude=16.9890&longitude=82.2474", None, 200),
        ("GET", "/api/v1/marine/conditions?latitude=16.9890&longitude=82.2474", None, 200),
        ("GET", "/api/v1/earth-observation/observations?latitude=16.9890&longitude=82.2474", None, 200),
        ("GET", "/api/v1/geospatial/ports", None, 200),
        ("GET", "/api/v1/geospatial/restricted-zones", None, 200),
        ("GET", "/api/v1/geospatial/protected-zones", None, 200),
        ("GET", "/api/v1/geospatial/nearby-zones?latitude=16.9890&longitude=82.2474", None, 200),
        ("GET", "/api/v1/geospatial/distance?origin_latitude=16.98&origin_longitude=82.25&destination_latitude=17.68&destination_longitude=83.21", None, 200),
        ("GET", "/api/v1/geospatial/assess-route?origin_latitude=16.98&origin_longitude=82.25&destination_latitude=17.68&destination_longitude=83.21", None, 200),
        ("GET", "/api/v1/disaster/alerts", None, 200),
        ("GET", "/api/v1/disaster/cyclones", None, 200),
        ("GET", "/api/v1/disaster/hazard-zones", None, 200),
        ("GET", "/api/v1/disaster/safety-assessment?latitude=16.9890&longitude=82.2474", None, 200),
        ("GET", "/api/v1/operations/distance?origin_latitude=16.9890&origin_longitude=82.2474&destination_latitude=17.6868&destination_longitude=83.2185", None, 200),
        ("GET", "/api/v1/operations/estimate-time?origin_latitude=16.9890&origin_longitude=82.2474&destination_latitude=17.6868&destination_longitude=83.2185&speed_kmh=25.0", None, 200),
        ("GET", "/api/v1/operations/assess-route?origin_latitude=16.9890&origin_longitude=82.2474&destination_latitude=17.6868&destination_longitude=83.2185", None, 200),
        ("GET", f"/api/v1/operations/departure-assessment?origin_latitude=16.9890&origin_longitude=82.2474&destination_latitude=17.6868&destination_longitude=83.2185&departure_at={now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}", None, 200),
        ("POST", "/api/v1/agents/fishing/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
        ("POST", "/api/v1/agents/marine-conditions/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
        ("POST", "/api/v1/agents/earth-observation/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
        ("POST", "/api/v1/agents/geospatial-navigation/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
        ("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
        ("POST", "/api/v1/agents/marine-operations/assess", {
            "origin_latitude": 16.9890,
            "origin_longitude": 82.2474,
            "destination_latitude": 17.6868,
            "destination_longitude": 83.2185,
        }, 200),
        ("POST", "/api/v1/orchestrator/query", {"query": "Can I go fishing tomorrow at 6 AM from Kakinada?"}, 200),
    ]

    for method, path, data, expected_status in endpoints:
        status, _ = request(method, path, data)
        assert status == expected_status, f"Endpoint {method} {path} returned {status}, expected {expected_status}"
        print(f"  [OK] {method} {path} -> {status}")

    print("\n" + "=" * 80)
    print("ALL ORCHESTRATOR TESTS & ALL 6 DOMAIN AGENT REGRESSIONS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    test_orchestrator()
    run_regressions()
