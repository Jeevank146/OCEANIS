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


def run_tests():
    print("=" * 80)
    print("OCEANIS Marine Operations Intelligence Agent — Verification Suite")
    print("=" * 80)

    init_db()

    # 1. Agent Import
    print("\n[1/22] Testing MarineOperationsIntelligenceAgent import...")
    from agents.marine_operations.agent import MarineOperationsIntelligenceAgent
    agent = MarineOperationsIntelligenceAgent()
    assert agent is not None
    print("  [OK] MarineOperationsIntelligenceAgent imported and instantiated successfully.")

    # 2. Service Import
    print("\n[2/22] Testing MarineOperationsAgentService import...")
    from agents.marine_operations.service import MarineOperationsAgentService
    service = MarineOperationsAgentService()
    assert service is not None
    print("  [OK] MarineOperationsAgentService imported and instantiated successfully.")

    # 3. Collector Import
    print("\n[3/22] Testing MarineOperationsDataCollector import...")
    from agents.marine_operations.collector import MarineOperationsDataCollector
    collector = MarineOperationsDataCollector()
    assert collector is not None
    print("  [OK] MarineOperationsDataCollector imported and instantiated successfully.")

    # 4. Reasoning Engine Import
    print("\n[4/22] Testing MarineOperationsReasoningEngine import...")
    from agents.marine_operations.reasoning import MarineOperationsReasoningEngine
    reasoning = MarineOperationsReasoningEngine()
    assert reasoning is not None
    print("  [OK] MarineOperationsReasoningEngine imported and instantiated successfully.")

    # 5. POST /api/v1/agents/marine-operations/assess with valid coordinates
    print("\n[5/22] Testing POST /api/v1/agents/marine-operations/assess with valid coordinates...")
    status, res = request(
        "POST",
        "/api/v1/agents/marine-operations/assess",
        {
            "origin_latitude": 16.9890,
            "origin_longitude": 82.2474,
            "destination_latitude": 17.6868,
            "destination_longitude": 83.2185,
            "speed_kmh": 25.0,
            "vessel_type": "FISHING_VESSEL",
        },
    )
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["agent"] == "marine_operations"
    assert "operational_status" in res
    assert "operational_risk" in res
    assert "route" in res
    assert "confidence" in res
    assert "evidence" in res
    assert "recommendation" in res
    assert "explanation" in res
    print(f"  [OK] Valid assessment received: operational_status={res['operational_status']}, risk={res['operational_risk']}, dist={res['route']['distance_km']} km, duration={res['route']['estimated_duration_minutes']} min.")

    # 6. Invalid origin latitude -> HTTP 422
    print("\n[6/22] Testing invalid origin latitude (-95.0, 95.0) -> HTTP 422...")
    status_high, _ = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 95.0, "origin_longitude": 82.25,
        "destination_latitude": 17.68, "destination_longitude": 83.21
    })
    assert status_high == 422
    status_low, _ = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": -95.0, "origin_longitude": 82.25,
        "destination_latitude": 17.68, "destination_longitude": 83.21
    })
    assert status_low == 422
    print("  [OK] Invalid origin latitude correctly rejected with HTTP 422.")

    # 7. Invalid origin longitude -> HTTP 422
    print("\n[7/22] Testing invalid origin longitude (-190.0, 190.0) -> HTTP 422...")
    status_high, _ = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 16.98, "origin_longitude": 190.0,
        "destination_latitude": 17.68, "destination_longitude": 83.21
    })
    assert status_high == 422
    status_low, _ = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 16.98, "origin_longitude": -190.0,
        "destination_latitude": 17.68, "destination_longitude": 83.21
    })
    assert status_low == 422
    print("  [OK] Invalid origin longitude correctly rejected with HTTP 422.")

    # 8. Invalid destination latitude -> HTTP 422
    print("\n[8/22] Testing invalid destination latitude (-95.0, 95.0) -> HTTP 422...")
    status_high, _ = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 16.98, "origin_longitude": 82.25,
        "destination_latitude": 95.0, "destination_longitude": 83.21
    })
    assert status_high == 422
    print("  [OK] Invalid destination latitude correctly rejected with HTTP 422.")

    # 9. Invalid destination longitude -> HTTP 422
    print("\n[9/22] Testing invalid destination longitude (-190.0, 190.0) -> HTTP 422...")
    status_high, _ = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 16.98, "origin_longitude": 82.25,
        "destination_latitude": 17.68, "destination_longitude": 190.0
    })
    assert status_high == 422
    print("  [OK] Invalid destination longitude correctly rejected with HTTP 422.")

    # 10. Distance and Travel Duration Calculation
    print("\n[10/22] Testing distance and duration calculations...")
    route_info = res["route"]
    assert route_info["distance_km"] > 0.0
    assert route_info["distance_nautical_miles"] > 0.0
    assert route_info["estimated_duration_minutes"] > 0.0
    assert route_info["estimated_duration_hours"] > 0.0
    expected_duration = round((route_info["distance_km"] / 25.0) * 60.0, 2)
    assert abs(route_info["estimated_duration_minutes"] - expected_duration) < 0.1
    print(f"  [OK] Distance verified: {route_info['distance_km']} km ({route_info['distance_nautical_miles']} NM), duration: {route_info['estimated_duration_minutes']} min at 25 km/h.")

    # 11. Departure timestamp and estimated arrival calculation
    print("\n[11/22] Testing departure and estimated arrival calculation...")
    now_utc = datetime.now(timezone.utc)
    dep_str = (now_utc + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    status, dep_res = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 16.9890,
        "origin_longitude": 82.2474,
        "destination_latitude": 17.6868,
        "destination_longitude": 83.2185,
        "speed_kmh": 20.0,
        "planned_departure_at": dep_str,
    })
    assert status == 200
    dep_route = dep_res["route"]
    assert dep_route["planned_departure_at"] is not None
    assert dep_route["estimated_arrival_at"] is not None
    dep_time = datetime.fromisoformat(dep_route["planned_departure_at"])
    arr_time = datetime.fromisoformat(dep_route["estimated_arrival_at"])
    assert arr_time > dep_time
    print(f"  [OK] Scheduled departure {dep_route['planned_departure_at']} -> estimated arrival {dep_route['estimated_arrival_at']}.")

    # 12. Restricted-zone route intersection -> deterministic BLOCKED
    print("\n[12/22] Testing route intersecting restricted zone -> deterministic BLOCKED...")
    db = SessionLocal()
    # Insert test restricted zone intersecting trajectory (17.0, 82.5) -> (17.5, 83.0)
    db.query(RestrictedZone).filter(RestrictedZone.name == "TEST_OPS_MILITARY_CORRIDOR").delete()
    wkt_poly = "POLYGON((82.60 17.10, 82.90 17.10, 82.90 17.40, 82.60 17.40, 82.60 17.10))"
    res_zone = RestrictedZone(
        name="TEST_OPS_MILITARY_CORRIDOR",
        zone_type="MILITARY_EXCLUSION",
        geometry=WKTElement(wkt_poly, srid=4326),
        authority="Indian Navy",
        is_active=True,
    )
    db.add(res_zone)
    db.commit()

    status, blocked_res = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 17.00,
        "origin_longitude": 82.50,
        "destination_latitude": 17.50,
        "destination_longitude": 83.00,
        "speed_kmh": 20.0,
    })
    assert status == 200
    assert blocked_res["operational_status"] == "BLOCKED"
    assert blocked_res["operational_risk"] == "CRITICAL"
    assert blocked_res["route"]["restricted_zone_intersection"] is True
    assert "VOYAGE BLOCKED" in blocked_res["recommendation"]
    print(f"  [OK] Restricted zone intersection correctly triggered operational_status=BLOCKED, risk=CRITICAL.")

    # 13. Protected-zone route intersection -> CAUTION & alternative route guidance
    print("\n[13/22] Testing protected-zone route intersection -> CAUTION...")
    db.query(RestrictedZone).filter(RestrictedZone.name == "TEST_OPS_MILITARY_CORRIDOR").delete()
    db.query(ProtectedZone).filter(ProtectedZone.name == "TEST_OPS_CORINGA_SANCTUARY").delete()
    wkt_prot = "POLYGON((82.15 16.85, 82.35 16.85, 82.35 17.05, 82.15 17.05, 82.15 16.85))"
    prot_zone = ProtectedZone(
        name="TEST_OPS_CORINGA_SANCTUARY",
        zone_type="MARINE_PROTECTED_AREA",
        geometry=WKTElement(wkt_prot, srid=4326),
        authority="Wildlife Department",
        is_active=True,
    )

    db.add(prot_zone)
    db.commit()

    status, caution_res = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 16.80,
        "origin_longitude": 82.10,
        "destination_latitude": 17.10,
        "destination_longitude": 82.40,
        "speed_kmh": 20.0,
    })
    assert status == 200
    assert caution_res["operational_status"] in ("CAUTION", "WARNING", "BLOCKED")
    assert caution_res["route"]["protected_zone_intersection"] is True
    assert caution_res["route"]["alternative_route_available"] is True
    print(f"  [OK] Protected zone intersection yielded status='{caution_res['operational_status']}', alternative_route_available={caution_res['route']['alternative_route_available']}.")

    # 14. Hazard-zone route intersection -> BLOCKED / WARNING
    print("\n[14/22] Testing hazard-zone route intersection...")
    db.query(HazardZone).filter(HazardZone.name == "TEST_OPS_SURGE_HAZARD").delete()
    wkt_hazard = "POLYGON((82.40 17.00, 82.80 17.00, 82.80 17.40, 82.40 17.40, 82.40 17.00))"
    hz_obj = HazardZone(
        name="TEST_OPS_SURGE_HAZARD",
        hazard_type="STORM_SURGE_ZONE",
        severity="CRITICAL",
        description="Dangerous storm surge corridor.",
        geometry=func.ST_GeomFromText(wkt_hazard, 4326),
        source="INCOIS",
        source_category="OFFICIAL",
        effective_from=now_utc - timedelta(hours=1),
        effective_until=now_utc + timedelta(hours=24),
        is_active=True,
    )
    db.add(hz_obj)
    db.commit()

    status, hz_res = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 16.90,
        "origin_longitude": 82.30,
        "destination_latitude": 17.50,
        "destination_longitude": 82.90,
        "speed_kmh": 20.0,
    })
    assert status == 200
    assert hz_res["route"]["hazard_zone_intersection"] is True
    assert hz_res["operational_status"] == "BLOCKED"
    print("  [OK] Critical hazard zone intersection properly evaluated to BLOCKED.")

    # 15. Active disaster alert along corridor -> WARNING / BLOCKED
    print("\n[15/22] Testing active disaster alert along operational corridor...")
    db.query(HazardZone).filter(HazardZone.name == "TEST_OPS_SURGE_HAZARD").delete()
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_OPS_ALERT_01").delete()
    test_alert = MarineAlert(
        alert_id="TEST_OPS_ALERT_01",
        title="TEST: Gale Wind & Squally Weather",
        alert_type="GALE_WIND",
        severity="WARNING",
        status="ACTIVE",
        description="Gale winds 55-65 km/h along operational transit route.",
        source="INCOIS",
        source_category="OFFICIAL",
        issued_at=now_utc - timedelta(hours=1),
        effective_from=now_utc - timedelta(hours=1),
        effective_until=now_utc + timedelta(hours=24),
        latitude=17.20,
        longitude=82.60,
        geometry=func.ST_SetSRID(func.ST_MakePoint(82.60, 17.20), 4326),
        is_active=True,
    )
    db.add(test_alert)
    db.commit()

    status, alert_op_res = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 17.00,
        "origin_longitude": 82.40,
        "destination_latitude": 17.40,
        "destination_longitude": 82.80,
        "speed_kmh": 20.0,
    })
    assert status == 200
    assert alert_op_res["operational_status"] in ("WARNING", "BLOCKED")
    print(f"  [OK] Alert impact evaluated: status='{alert_op_res['operational_status']}'.")

    # 16. Tropical Cyclone Proximity Evaluation
    print("\n[16/22] Testing cyclone proximity evaluation...")
    db.query(CycloneTrack).filter(CycloneTrack.cyclone_id == "TEST_OPS_CYCLONE_01").delete()
    cyc_obj = CycloneTrack(
        cyclone_id="TEST_OPS_CYCLONE_01",
        name="TEST_CYCLONE_GULAB",
        basin="BAY_OF_BENGAL",
        classification="VERY_SEVERE_CYCLONIC_STORM",
        latitude=17.25,
        longitude=82.65,
        geometry=func.ST_SetSRID(func.ST_MakePoint(82.65, 17.25), 4326),
        wind_speed_kmh=125.0,
        pressure_hpa=978.0,
        observed_at=now_utc - timedelta(hours=1),
        source="IMD",
        source_category="OFFICIAL",
        data_type="OBSERVED",
        is_active=True,
    )
    db.add(cyc_obj)
    db.commit()

    status, cyc_op_res = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 17.00,
        "origin_longitude": 82.40,
        "destination_latitude": 17.40,
        "destination_longitude": 82.80,
        "speed_kmh": 20.0,
    })
    assert status == 200
    assert cyc_op_res["operational_status"] == "BLOCKED"
    assert cyc_op_res["operational_risk"] == "CRITICAL"
    print("  [OK] Severe cyclone in route corridor triggered operational_status=BLOCKED.")

    # 17. Weather & Marine Condition Threshold Limits
    print("\n[17/22] Testing weather and marine condition thresholds in operations...")
    db.query(CycloneTrack).filter(CycloneTrack.cyclone_id == "TEST_OPS_CYCLONE_01").delete()
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_OPS_ALERT_01").delete()
    db.commit()

    status, cond_res = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": 16.9890,
        "origin_longitude": 82.2474,
        "destination_latitude": 17.6868,
        "destination_longitude": 83.2185,
        "speed_kmh": 25.0,
    })
    assert status == 200
    assert "marine_conditions" in cond_res
    assert "weather_conditions" in cond_res
    print("  [OK] Marine & weather condition indicators successfully integrated into operation assessment.")

    # 18. Safe Port Refuge Recommendations
    print("\n[18/22] Testing safe port refuge recommendations...")
    assert len(cond_res["safe_ports"]) >= 1
    safe_port = cond_res["safe_ports"][0]
    assert "name" in safe_port
    assert "distance_km" in safe_port
    print(f"  [OK] Safe refuge port identified: '{safe_port['name']}' ({safe_port['distance_km']} km).")

    # 19. Missing Environmental Telemetry -> INSUFFICIENT_DATA
    print("\n[19/22] Testing remote ocean coordinates -> INSUFFICIENT_DATA...")
    status, remote_res = request("POST", "/api/v1/agents/marine-operations/assess", {
        "origin_latitude": -50.0,
        "origin_longitude": -100.0,
        "destination_latitude": -50.5,
        "destination_longitude": -100.5,
        "speed_kmh": 20.0,
    })
    assert status == 200
    assert remote_res["operational_status"] == "INSUFFICIENT_DATA"
    assert remote_res["operational_risk"] == "UNKNOWN"
    assert remote_res["confidence"] == 0.0
    assert remote_res["data_freshness"] == "UNAVAILABLE"
    assert "INSUFFICIENT_DATA" in remote_res["recommendation"]
    print("  [OK] Remote location with no telemetry safely yielded operational_status=INSUFFICIENT_DATA with confidence=0.0.")

    # 20. Confidence Score Strictly Bounded in [0.0, 1.0]
    print("\n[20/22] Testing confidence scores bounded in [0.0, 1.0]...")
    for res_obj in [res, blocked_res, caution_res, remote_res]:
        conf = res_obj["confidence"]
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of bounds"
    print("  [OK] Confidence score strictly bounded within [0.0, 1.0].")

    # 21. No Misleading 100%-Safe Claims
    print("\n[21/22] Verifying prohibition of misleading 100%-safe claims...")
    prohibited_phrases = ["100% safe", "guaranteed safe", "risk-free", "completely safe", "zero risk"]
    for res_obj in [res, blocked_res, caution_res, remote_res]:
        rec = res_obj["recommendation"].lower()
        exp = res_obj["explanation"].lower()
        for phrase in prohibited_phrases:
            assert phrase not in rec, f"Prohibited phrase '{phrase}' found in recommendation: {rec}"
            assert phrase not in exp, f"Prohibited phrase '{phrase}' found in explanation: {exp}"
    print("  [OK] All recommendations strictly adhere to evidence-based conservative voyage directives without absolute claims.")

    # 22. OpenAPI Registration
    print("\n[22/22] Verifying OpenAPI registration for Marine Operations Agent...")
    status, openapi = request("GET", "/openapi.json")
    assert status == 200
    paths = openapi.get("paths", {})
    endpoint = "/api/v1/agents/marine-operations/assess"
    assert endpoint in paths, f"Missing endpoint {endpoint} in OpenAPI paths"
    post_op = paths[endpoint].get("post", {})
    tags = post_op.get("tags", [])
    assert "Marine Operations" in tags, f"Expected tag 'Marine Operations', got {tags}"
    print(f"  [OK] Endpoint {endpoint} registered with tag 'Marine Operations'.")

    # Clean up test records
    db.query(RestrictedZone).filter(RestrictedZone.name == "TEST_OPS_MILITARY_CORRIDOR").delete()
    db.query(ProtectedZone).filter(ProtectedZone.name == "TEST_OPS_CORINGA_SANCTUARY").delete()
    db.query(HazardZone).filter(HazardZone.name == "TEST_OPS_SURGE_HAZARD").delete()
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_OPS_ALERT_01").delete()
    db.query(CycloneTrack).filter(CycloneTrack.cyclone_id == "TEST_OPS_CYCLONE_01").delete()
    db.commit()
    db.close()


def run_regressions():
    print("\n" + "=" * 80)
    print("RUNNING FISHING, MARINE CONDITIONS, EO, GEOSPATIAL & DISASTER REGRESSIONS...")
    print("=" * 80)
    from scratch.test_disaster_safety_agent import run_disaster_safety_agent_tests, run_regressions as run_prior_regressions
    run_disaster_safety_agent_tests()
    run_prior_regressions()
    print("  [OK] All prior domain agent regressions (Fishing, Marine, EO, GeoSpatial, Disaster) passed.")

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
        ("POST", "/api/v1/agents/marine-operations/assess", {
            "origin_latitude": 16.9890,
            "origin_longitude": 82.2474,
            "destination_latitude": 17.6868,
            "destination_longitude": 83.2185,
        }, 200),
    ]

    for method, path, data, expected_status in endpoints:
        status, _ = request(method, path, data)
        assert status == expected_status, f"Endpoint {method} {path} returned {status}, expected {expected_status}"
        print(f"  [OK] {method} {path} -> {status}")

    print("\n" + "=" * 80)
    print("ALL 22 MARINE OPERATIONS AGENT TESTS & FULL REGRESSION SUITES PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
    run_regressions()
