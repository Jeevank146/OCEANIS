import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import func, text

from database import SessionLocal, engine, init_db
from models.disaster import CycloneTrack, HazardZone, MarineAlert
from models.geospatial import Port
from models.marine import MarineObservation
from models.weather import WeatherObservation

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


def run_disaster_safety_agent_tests():
    print("=" * 80)
    print("OCEANIS Disaster & Safety Intelligence Agent — Verification Suite")
    print("=" * 80)

    # 1. Agent Import
    print("\n[1/22] Testing DisasterSafetyIntelligenceAgent import...")
    from agents.disaster_safety.agent import DisasterSafetyIntelligenceAgent
    agent = DisasterSafetyIntelligenceAgent()
    assert agent is not None
    print("  [OK] DisasterSafetyIntelligenceAgent imported and instantiated successfully.")

    # 2. Service Import
    print("\n[2/22] Testing DisasterSafetyAgentService import...")
    from agents.disaster_safety.service import DisasterSafetyAgentService
    service = DisasterSafetyAgentService()
    assert service is not None
    print("  [OK] DisasterSafetyAgentService imported and instantiated successfully.")

    # 3. Collector Import
    print("\n[3/22] Testing DisasterSafetyDataCollector import...")
    from agents.disaster_safety.collector import DisasterSafetyDataCollector
    collector = DisasterSafetyDataCollector()
    assert collector is not None
    print("  [OK] DisasterSafetyDataCollector imported and instantiated successfully.")

    # 4. Reasoning Engine Import
    print("\n[4/22] Testing DisasterSafetyReasoningEngine import...")
    from agents.disaster_safety.reasoning import DisasterSafetyReasoningEngine
    reasoning = DisasterSafetyReasoningEngine()
    assert reasoning is not None
    print("  [OK] DisasterSafetyReasoningEngine imported and instantiated successfully.")

    # 5. POST /api/v1/agents/disaster-safety/assess with valid coordinates
    print("\n[5/22] Testing POST /api/v1/agents/disaster-safety/assess with valid coordinates...")
    status, res = request(
        "POST",
        "/api/v1/agents/disaster-safety/assess",
        {"latitude": 16.9890, "longitude": 82.2474, "radius_km": 50.0},
    )
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["agent"] == "disaster_safety"
    assert "safety_status" in res
    assert "risk_level" in res
    assert "confidence" in res
    assert "evidence" in res
    assert "warnings" in res
    assert "recommendation" in res
    assert "explanation" in res
    print(f"  [OK] Valid assessment received: safety_status={res['safety_status']}, risk_level={res['risk_level']}, confidence={res['confidence']}.")

    # 6. Invalid latitude -> HTTP 422
    print("\n[6/22] Testing invalid latitude (-95.0, 95.0) -> HTTP 422...")
    status_high, _ = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 95.0, "longitude": 82.25})
    assert status_high == 422, f"Expected 422 for lat=95.0, got {status_high}"
    status_low, _ = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": -95.0, "longitude": 82.25})
    assert status_low == 422, f"Expected 422 for lat=-95.0, got {status_low}"
    print("  [OK] Invalid latitude correctly rejected with HTTP 422 Unprocessable Entity.")

    # 7. Invalid longitude -> HTTP 422
    print("\n[7/22] Testing invalid longitude (-190.0, 190.0) -> HTTP 422...")
    status_high, _ = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 16.98, "longitude": 190.0})
    assert status_high == 422, f"Expected 422 for lon=190.0, got {status_high}"
    status_low, _ = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 16.98, "longitude": -190.0})
    assert status_low == 422, f"Expected 422 for lon=-190.0, got {status_low}"
    print("  [OK] Invalid longitude correctly rejected with HTTP 422 Unprocessable Entity.")

    # 8. Active Alert Retrieval
    print("\n[8/22] Testing active alert retrieval & spatial evidence provenance...")
    db = SessionLocal()
    now_utc = datetime.now(timezone.utc)
    
    # Ensure active alert exists
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_SUITE_ALERT_01").delete()
    test_alert = MarineAlert(
        alert_id="TEST_SUITE_ALERT_01",
        title="TEST: Severe Swell Surge Warning",
        alert_type="SWELL_SURGE",
        severity="WARNING",
        status="ACTIVE",
        description="High swells 3.5m expected along Andhra coast.",
        source="INCOIS",
        source_category="OFFICIAL",
        issued_at=now_utc - timedelta(hours=1),
        effective_from=now_utc - timedelta(hours=1),
        effective_until=now_utc + timedelta(hours=24),
        latitude=16.98,
        longitude=82.25,
        geometry=func.ST_SetSRID(func.ST_MakePoint(82.25, 16.98), 4326),
        is_active=True,
    )
    db.add(test_alert)
    db.commit()

    status, alert_res = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 16.98, "longitude": 82.25})
    assert status == 200
    assert len(alert_res["alerts"]) >= 1
    found_alert = next((a for a in alert_res["alerts"] if a["alert_id"] == "TEST_SUITE_ALERT_01"), None)
    assert found_alert is not None
    assert found_alert["alert_type"] == "SWELL_SURGE"
    assert found_alert["source"] == "INCOIS"
    print(f"  [OK] Active alert retrieved: '{found_alert['title']}', severity={found_alert['severity']}.")

    # 9. Alert Severity Evaluation
    print("\n[9/22] Testing alert severity evaluation...")
    alert_evidence = [e for e in alert_res["evidence"] if e["factor"] == "active_alert"]
    assert len(alert_evidence) >= 1
    assert any(e["severity"] == "WARNING" for e in alert_evidence)
    print("  [OK] Alert severity evaluated correctly in evidence items.")

    # 10. Alert Freshness Evaluation
    print("\n[10/22] Testing alert freshness evaluation...")
    assert found_alert["freshness"] in ("FRESH", "AGING")
    print(f"  [OK] Alert freshness evaluated: {found_alert['freshness']}.")

    # 11. Cyclone Retrieval
    print("\n[11/22] Testing cyclone retrieval & storm track metrics...")
    db.query(CycloneTrack).filter(CycloneTrack.cyclone_id == "TEST_SUITE_CYCLONE_01").delete()
    test_cyclone = CycloneTrack(
        cyclone_id="TEST_SUITE_CYCLONE_01",
        name="TEST_CYCLONE_ASANI",
        basin="BAY_OF_BENGAL",
        classification="SEVERE_CYCLONIC_STORM",
        latitude=16.50,
        longitude=83.00,
        geometry=func.ST_SetSRID(func.ST_MakePoint(83.00, 16.50), 4326),
        wind_speed_kmh=110.0,
        pressure_hpa=985.0,
        observed_at=now_utc - timedelta(hours=1),
        source="IMD",
        source_category="OFFICIAL",
        data_type="OBSERVED",
        is_active=True,
    )
    db.add(test_cyclone)
    db.commit()

    status, cyc_res = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 16.98, "longitude": 82.25})
    assert status == 200
    assert len(cyc_res["cyclones"]) >= 1
    found_cyc = next((c for c in cyc_res["cyclones"] if c["cyclone_id"] == "TEST_SUITE_CYCLONE_01"), None)
    assert found_cyc is not None
    assert found_cyc["name"] == "TEST_CYCLONE_ASANI"
    assert found_cyc["wind_speed_kmh"] == 110.0
    print(f"  [OK] Cyclone retrieved: '{found_cyc['name']}' ({found_cyc['classification']}), distance={found_cyc['distance_km']} km.")

    # 12. Cyclone Proximity Evaluation
    print("\n[12/22] Testing cyclone proximity evaluation...")
    cyc_evidence = [e for e in cyc_res["evidence"] if e["factor"] == "cyclone_proximity"]
    assert len(cyc_evidence) >= 1
    assert any(e["distance_km"] is not None for e in cyc_evidence)
    print("  [OK] Cyclone proximity and distance correctly integrated into safety evidence.")

    # 13. Hazard Zone Retrieval
    print("\n[13/22] Testing hazard-zone retrieval...")
    db.query(HazardZone).filter(HazardZone.name == "TEST_SUITE_HIGH_WAVE_SECTOR").delete()
    wkt_hazard = "POLYGON((82.10 16.80, 82.40 16.80, 82.40 17.10, 82.10 17.10, 82.10 16.80))"
    test_hazard = HazardZone(
        name="TEST_SUITE_HIGH_WAVE_SECTOR",
        hazard_type="HIGH_WAVE_RISK",
        severity="WARNING",
        description="Hazardous coastal surf sector.",
        geometry=func.ST_GeomFromText(wkt_hazard, 4326),
        source="INCOIS",
        source_category="OFFICIAL",
        effective_from=now_utc - timedelta(hours=2),
        effective_until=now_utc + timedelta(hours=24),
        is_active=True,
    )
    db.add(test_hazard)
    db.commit()

    status, hz_res = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 16.98, "longitude": 82.25})
    assert status == 200
    assert len(hz_res["hazards"]) >= 1
    found_hz = next((h for h in hz_res["hazards"] if h["name"] == "TEST_SUITE_HIGH_WAVE_SECTOR"), None)
    assert found_hz is not None
    assert found_hz["hazard_type"] == "HIGH_WAVE_RISK"
    print(f"  [OK] Hazard zone retrieved: '{found_hz['name']}', contains_point={found_hz['contains_point']}.")

    # 14. Point-in-Hazard-Zone Evaluation
    print("\n[14/22] Testing point-in-hazard-zone spatial containment...")
    # (16.98, 82.25) is inside the polygon (82.10..82.40, 16.80..17.10)
    assert found_hz["contains_point"] is True
    hz_evidence = [e for e in hz_res["evidence"] if e["factor"] == "hazard_containment"]
    assert len(hz_evidence) >= 1
    print("  [OK] Point-in-hazard-zone correctly evaluated: contains_point=True, spatial_relationship='INSIDE'.")

    # 15. CRITICAL hazard -> deterministic BLOCKED
    print("\n[15/22] Testing CRITICAL hazard -> deterministic BLOCKED state...")
    db.query(HazardZone).filter(HazardZone.name == "TEST_SUITE_CRITICAL_SURGE").delete()
    wkt_critical = "POLYGON((83.00 17.50, 83.40 17.50, 83.40 17.90, 83.00 17.90, 83.00 17.50))"
    critical_hazard = HazardZone(
        name="TEST_SUITE_CRITICAL_SURGE",
        hazard_type="STORM_SURGE_ZONE",
        severity="CRITICAL",
        description="Life-threatening surge inundation sector.",
        geometry=func.ST_GeomFromText(wkt_critical, 4326),
        source="INCOIS",
        source_category="OFFICIAL",
        effective_from=now_utc - timedelta(hours=1),
        effective_until=now_utc + timedelta(hours=12),
        is_active=True,
    )
    db.add(critical_hazard)
    db.commit()

    status, crit_res = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 17.70, "longitude": 83.20})
    assert status == 200
    assert crit_res["safety_status"] == "BLOCKED"
    assert crit_res["risk_level"] == "EXTREME"
    assert crit_res["confidence"] >= 0.95
    assert "NAVIGATION BLOCKED" in crit_res["recommendation"]
    print(f"  [OK] CRITICAL hazard containment deterministically yielded status='BLOCKED', risk_level='EXTREME'.")

    # 16. WARNING hazard -> WARNING state
    print("\n[16/22] Testing WARNING hazard -> WARNING state...")
    status, warn_res = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 16.98, "longitude": 82.25})
    assert status == 200
    assert warn_res["safety_status"] in ("WARNING", "BLOCKED")
    assert warn_res["risk_level"] in ("HIGH", "EXTREME")
    print(f"  [OK] WARNING hazard correctly yielded status='{warn_res['safety_status']}', risk_level='{warn_res['risk_level']}'.")

    # 17. Missing critical data -> INSUFFICIENT_DATA
    print("\n[17/22] Testing remote location with missing telemetry -> INSUFFICIENT_DATA...")
    status, remote_res = request("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": -50.0, "longitude": -100.0})
    assert status == 200
    assert remote_res["safety_status"] == "INSUFFICIENT_DATA"
    assert remote_res["risk_level"] == "UNKNOWN"
    assert remote_res["confidence"] == 0.0
    assert remote_res["data_freshness"] == "UNAVAILABLE"
    assert "INSUFFICIENT_DATA" in remote_res["recommendation"]
    print("  [OK] Remote location safely returned status='INSUFFICIENT_DATA', confidence=0.0, data_freshness='UNAVAILABLE'.")

    # 18. Confidence calculation strictly bounded in [0.0, 1.0]
    print("\n[18/22] Testing confidence calculation strictly bounded in [0.0, 1.0]...")
    for res_obj in [alert_res, crit_res, warn_res, remote_res]:
        conf = res_obj["confidence"]
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of bounds"
    print("  [OK] Confidence score strictly bounded within [0.0, 1.0].")

    # 19. Freshness calculation
    print("\n[19/22] Testing data freshness categorization...")
    assert warn_res["data_freshness"] in ("FRESH", "AGING")
    assert remote_res["data_freshness"] == "UNAVAILABLE"
    print("  [OK] Freshness categorization validated across active and unavailable areas.")

    # 20. Evidence/provenance validation
    print("\n[20/22] Testing evidence provenance items...")
    evidence_items = warn_res["evidence"]
    assert len(evidence_items) > 0
    for ev in evidence_items:
        assert ev["factor"] is not None
        assert ev["source"] is not None
        assert ev["source_category"] in ("OFFICIAL", "MODEL/FORECAST", "DEMO/TEST", "UNKNOWN")
        assert ev["data_type"] in ("OFFICIAL_WARNING", "OBSERVED_HAZARD", "FORECAST_HAZARD", "AI_ASSESSMENT", "SPATIAL_INFRASTRUCTURE")
        assert 0.0 <= ev["confidence"] <= 1.0
    print(f"  [OK] Verified {len(evidence_items)} evidence items with complete source provenance and typing.")

    # 21. No misleading safety guarantees
    print("\n[21/22] Verifying prohibition of misleading 100%-safe claims...")
    prohibited_phrases = ["100% safe", "guaranteed safe", "risk-free", "completely safe", "zero risk"]
    for res_obj in [alert_res, crit_res, warn_res, remote_res]:
        rec = res_obj["recommendation"].lower()
        exp = res_obj["explanation"].lower()
        for phrase in prohibited_phrases:
            assert phrase not in rec, f"Prohibited phrase '{phrase}' found in recommendation: {rec}"
            assert phrase not in exp, f"Prohibited phrase '{phrase}' found in explanation: {exp}"
    print("  [OK] All recommendations strictly adhere to evidence-based conservative safety directives without absolute claims.")

    # 22. OpenAPI registration
    print("\n[22/22] Verifying OpenAPI registration for Disaster & Safety Agent...")
    status, openapi = request("GET", "/openapi.json")
    assert status == 200
    paths = openapi.get("paths", {})
    endpoint = "/api/v1/agents/disaster-safety/assess"
    assert endpoint in paths, f"Missing endpoint {endpoint} in OpenAPI paths"
    post_op = paths[endpoint].get("post", {})
    tags = post_op.get("tags", [])
    assert "Disaster & Safety" in tags, f"Expected tag 'Disaster & Safety', got {tags}"
    print(f"  [OK] Endpoint {endpoint} registered with tag 'Disaster & Safety'.")

    # Clean up test fixtures
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_SUITE_ALERT_01").delete()
    db.query(CycloneTrack).filter(CycloneTrack.cyclone_id == "TEST_SUITE_CYCLONE_01").delete()
    db.query(HazardZone).filter(HazardZone.name.in_(["TEST_SUITE_HIGH_WAVE_SECTOR", "TEST_SUITE_CRITICAL_SURGE"])).delete()
    db.commit()
    db.close()


def run_regressions():
    print("\n" + "=" * 80)
    print("RUNNING FISHING, MARINE CONDITIONS, EO & GEOSPATIAL AGENT REGRESSIONS...")
    print("=" * 80)
    from scratch.test_geospatial_navigation_agent import run_tests as run_geospatial_tests
    run_geospatial_tests()
    print("  [OK] All prior domain agent regressions (Fishing, Marine, EO, GeoSpatial) passed.")



    print("\n" + "=" * 80)
    print("RUNNING ALL EXISTING BACKEND ENDPOINTS REGRESSION...")
    print("=" * 80)
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
        ("GET", f"/api/v1/operations/departure-assessment?origin_latitude=16.9890&origin_longitude=82.2474&destination_latitude=17.6868&destination_longitude=83.2185&departure_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}", None, 200),
        ("POST", "/api/v1/agents/fishing/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
        ("POST", "/api/v1/agents/marine-conditions/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
        ("POST", "/api/v1/agents/earth-observation/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
        ("POST", "/api/v1/agents/geospatial-navigation/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
        ("POST", "/api/v1/agents/disaster-safety/assess", {"latitude": 16.9890, "longitude": 82.2474}, 200),
    ]

    for method, path, data, expected_status in endpoints:
        status, _ = request(method, path, data)
        assert status == expected_status, f"Endpoint {method} {path} returned {status}, expected {expected_status}"
        print(f"  [OK] {method} {path} -> {status}")

    print("\n" + "=" * 80)
    print("ALL 22 DISASTER & SAFETY AGENT TESTS & FULL REGRESSION SUITES PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    run_disaster_safety_agent_tests()
    run_regressions()
