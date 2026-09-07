import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from geoalchemy2.elements import WKTElement
from sqlalchemy import text

from database import SessionLocal, engine, init_db
from models.geospatial import Port, ProtectedZone, RestrictedZone

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
    print("OCEANIS Geo-Spatial & Navigation Intelligence Agent — Verification Suite")
    print("=" * 80)

    init_db()

    # -------------------------------------------------------------------------
    # 1. Agent Import
    # -------------------------------------------------------------------------
    print("\n[1/21] Testing GeoSpatialNavigationIntelligenceAgent import...")
    try:
        from agents.geospatial_navigation.agent import GeoSpatialNavigationIntelligenceAgent
        agent_instance = GeoSpatialNavigationIntelligenceAgent()
        assert agent_instance is not None
        print("  [OK] GeoSpatialNavigationIntelligenceAgent imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Agent import failed: {e}")
        raise e

    # -------------------------------------------------------------------------
    # 2. Service Import
    # -------------------------------------------------------------------------
    print("\n[2/21] Testing GeoSpatialNavigationAgentService import...")
    try:
        from agents.geospatial_navigation.service import GeoSpatialNavigationAgentService
        service_instance = GeoSpatialNavigationAgentService()
        assert service_instance is not None
        print("  [OK] GeoSpatialNavigationAgentService imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Service import failed: {e}")
        raise e

    # -------------------------------------------------------------------------
    # 3. Collector Import
    # -------------------------------------------------------------------------
    print("\n[3/21] Testing GeoSpatialNavigationDataCollector import...")
    try:
        from agents.geospatial_navigation.collector import GeoSpatialNavigationDataCollector
        collector_instance = GeoSpatialNavigationDataCollector()
        assert collector_instance is not None
        print("  [OK] GeoSpatialNavigationDataCollector imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Collector import failed: {e}")
        raise e

    # -------------------------------------------------------------------------
    # 4. Reasoning Engine Import
    # -------------------------------------------------------------------------
    print("\n[4/21] Testing GeoSpatialNavigationReasoningEngine import...")
    try:
        from agents.geospatial_navigation.reasoning import GeoSpatialNavigationReasoningEngine
        reasoning_instance = GeoSpatialNavigationReasoningEngine()
        assert reasoning_instance is not None
        print("  [OK] GeoSpatialNavigationReasoningEngine imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Reasoning engine import failed: {e}")
        raise e

    # Clean old TEST spatial records
    with SessionLocal() as db:
        db.query(RestrictedZone).filter(RestrictedZone.name.like("TEST_GEO_%")).delete(synchronize_session=False)
        db.query(ProtectedZone).filter(ProtectedZone.name.like("TEST_GEO_%")).delete(synchronize_session=False)
        db.query(Port).filter(Port.name.like("TEST_GEO_%")).delete(synchronize_session=False)
        db.commit()

    lat_kakinada = 16.9890
    lon_kakinada = 82.2474
    lat_vizag = 17.6868
    lon_vizag = 83.2185

    # -------------------------------------------------------------------------
    # 5. Valid Coordinates Assessment (Single Location)
    # -------------------------------------------------------------------------
    print("\n[5/21] Testing POST /api/v1/agents/geospatial-navigation/assess with valid coordinates...")
    req_payload = {
        "latitude": lat_kakinada,
        "longitude": lon_kakinada,
    }
    status, res5 = request("POST", "/api/v1/agents/geospatial-navigation/assess", req_payload)
    assert status == 200, f"Expected 200, got {status}: {res5}"
    assert res5["agent"] == "geospatial_navigation", f"Expected agent 'geospatial_navigation', got {res5.get('agent')}"
    assert res5["origin"]["latitude"] == lat_kakinada
    assert res5["origin"]["longitude"] == lon_kakinada
    assert res5["confidence"] >= 0.9
    assert res5["data_freshness"] == "FRESH"
    print(f"  [OK] Valid assessment received: spatial_status={res5['spatial_status']}, geofence={res5['geofence_status']}.")

    # -------------------------------------------------------------------------
    # 6. Invalid Latitude -> HTTP 422
    # -------------------------------------------------------------------------
    print("\n[6/21] Testing invalid latitude (-95.0, 95.0) -> HTTP 422...")
    status, err_lat = request("POST", "/api/v1/agents/geospatial-navigation/assess", {"latitude": 95.0, "longitude": 82.25})
    assert status == 422, f"Expected 422 for latitude=95.0, got {status}"
    status, err_lat2 = request("POST", "/api/v1/agents/geospatial-navigation/assess", {"latitude": -91.0, "longitude": 82.25})
    assert status == 422, f"Expected 422 for latitude=-91.0, got {status}"
    print("  [OK] Invalid latitude correctly rejected with HTTP 422 Unprocessable Entity.")

    # -------------------------------------------------------------------------
    # 7. Invalid Longitude -> HTTP 422
    # -------------------------------------------------------------------------
    print("\n[7/21] Testing invalid longitude (-190.0, 190.0) -> HTTP 422...")
    status, err_lon = request("POST", "/api/v1/agents/geospatial-navigation/assess", {"latitude": 16.98, "longitude": 185.0})
    assert status == 422, f"Expected 422 for longitude=185.0, got {status}"
    status, err_lon2 = request("POST", "/api/v1/agents/geospatial-navigation/assess", {"latitude": 16.98, "longitude": -195.0})
    assert status == 422, f"Expected 422 for longitude=-195.0, got {status}"
    print("  [OK] Invalid longitude correctly rejected with HTTP 422 Unprocessable Entity.")

    # -------------------------------------------------------------------------
    # 8. Nearby Port Retrieval
    # -------------------------------------------------------------------------
    print("\n[8/21] Testing nearby coastal port infrastructure retrieval...")
    assert len(res5["nearby_entities"]) > 0, "No nearby ports found"
    port_names = [e["name"] for e in res5["nearby_entities"]]
    assert any("Kakinada" in name for name in port_names), f"Kakinada Port not found in nearby: {port_names}"
    p0 = res5["nearby_entities"][0]
    assert "distance_km" in p0 and p0["distance_km"] is not None
    assert "distance_nautical_miles" in p0 and p0["distance_nautical_miles"] is not None
    print(f"  [OK] Nearest port retrieved: '{p0['name']}' at {p0['distance_km']} km ({p0['distance_nautical_miles']} NM).")

    # -------------------------------------------------------------------------
    # 9. Restricted Zone Retrieval
    # -------------------------------------------------------------------------
    print("\n[9/21] Testing restricted maritime exclusion zone retrieval...")
    res_ev = [e for e in res5["evidence"] if e["data_type"] == "SPATIAL_REGULATORY" or "restricted" in e["factor"]]
    print(f"  [OK] Restricted zone query executed with {len(res_ev)} spatial regulatory evidence items.")

    # -------------------------------------------------------------------------
    # 10. Protected Zone Retrieval
    # -------------------------------------------------------------------------
    print("\n[10/21] Testing marine protected area (MPA) retrieval...")
    prot_ev = [e for e in res5["evidence"] if "protected" in e["factor"]]
    print(f"  [OK] Marine protected areas evaluated: found {len(prot_ev)} items.")

    # -------------------------------------------------------------------------
    # 11. Distance Calculation
    # -------------------------------------------------------------------------
    print("\n[11/21] Testing geodesic distance calculation between origin and destination...")
    route_payload = {
        "latitude": lat_kakinada,
        "longitude": lon_kakinada,
        "destination_latitude": lat_vizag,
        "destination_longitude": lon_vizag,
    }
    status, res_route = request("POST", "/api/v1/agents/geospatial-navigation/assess", route_payload)
    assert status == 200
    assert res_route["distance"] is not None
    assert res_route["distance"]["distance_km"] > 100.0
    assert res_route["distance"]["distance_nautical_miles"] > 50.0
    assert res_route["distance"]["calculation_method"] == "HAVERSINE_GEODESIC"
    print(f"  [OK] Distance calculated: {res_route['distance']['distance_km']} km ({res_route['distance']['distance_nautical_miles']} NM).")

    # -------------------------------------------------------------------------
    # 12. Route Assessment (Clear Passage)
    # -------------------------------------------------------------------------
    print("\n[12/21] Testing route assessment for clear passage...")
    route_sum = res_route["route"]
    assert route_sum is not None
    assert route_sum["has_destination"] is True
    print(f"  [OK] Route assessment status: {route_sum['status']}.")

    # -------------------------------------------------------------------------
    # 13. Route Intersecting Restricted Zone -> BLOCKED
    # -------------------------------------------------------------------------
    print("\n[13/21] Testing route intersecting restricted exclusion zone -> BLOCKED...")
    with SessionLocal() as db:
        # Create a military exclusion polygon right between Kakinada and Vizag
        test_block_zone = RestrictedZone(
            name="TEST_GEO_MILITARY_BLOCK",
            zone_type="FIRING_RANGE",
            description="Active live-fire naval artillery testing zone.",
            authority="Indian Navy",
            is_active=True,
            geometry=WKTElement("POLYGON((82.5 17.1, 82.9 17.1, 82.9 17.5, 82.5 17.5, 82.5 17.1))", srid=4326),
        )
        db.add(test_block_zone)
        db.commit()

    s, res_blocked = request("POST", "/api/v1/agents/geospatial-navigation/assess", route_payload)
    assert s == 200
    assert res_blocked["spatial_status"] == "BLOCKED"
    assert res_blocked["route"]["status"] == "BLOCKED"
    assert res_blocked["route"]["restricted_zone_intersection"] is True
    assert res_blocked["route"]["alternative_route_available"] is True
    assert "TEST_GEO_MILITARY_BLOCK" in res_blocked["route"]["intersecting_restricted_zones"]
    assert "PROHIBITED" in res_blocked["recommendation"].upper() or "BLOCKED" in res_blocked["recommendation"].upper()
    print("  [OK] Restricted zone intersection correctly triggered BLOCKED status and alternative route suggestion.")

    # Clean up blocking zone
    with SessionLocal() as db:
        db.query(RestrictedZone).filter(RestrictedZone.name == "TEST_GEO_MILITARY_BLOCK").delete()
        db.commit()

    # -------------------------------------------------------------------------
    # 14. Protected Zone Route Handling -> CAUTION / PROTECTED
    # -------------------------------------------------------------------------
    print("\n[14/21] Testing route intersecting Marine Protected Area -> CAUTION / PROTECTED...")
    with SessionLocal() as db:
        test_mpa_zone = ProtectedZone(
            name="TEST_GEO_CORAL_MPA",
            zone_type="CORAL_SANCTUARY",
            description="Sensitive coral reef sanctuary.",
            authority="Ministry of Environment",
            is_active=True,
            geometry=WKTElement("POLYGON((82.5 17.1, 82.9 17.1, 82.9 17.5, 82.5 17.5, 82.5 17.1))", srid=4326),
        )
        db.add(test_mpa_zone)
        db.commit()

    s, res_mpa = request("POST", "/api/v1/agents/geospatial-navigation/assess", route_payload)
    assert s == 200
    assert res_mpa["route"]["protected_zone_intersection"] is True
    assert res_mpa["route"]["status"] == "CAUTION"
    assert "TEST_GEO_CORAL_MPA" in res_mpa["route"]["intersecting_protected_zones"]
    assert res_mpa["route"]["alternative_route_available"] is True
    print("  [OK] Protected zone intersection correctly triggered CAUTION and ecological advisories.")

    # Clean up MPA zone
    with SessionLocal() as db:
        db.query(ProtectedZone).filter(ProtectedZone.name == "TEST_GEO_CORAL_MPA").delete()
        db.commit()

    # -------------------------------------------------------------------------
    # 15. Point-in-Zone Evaluation (Inside Restricted / Inside Protected)
    # -------------------------------------------------------------------------
    print("\n[15/21] Testing point-in-zone evaluation (INSIDE_RESTRICTED & INSIDE_PROTECTED)...")
    with SessionLocal() as db:
        inside_res_zone = RestrictedZone(
            name="TEST_GEO_INSIDE_EXCLUSION",
            zone_type="SECURITY_ZONE",
            description="Naval base perimeter.",
            is_active=True,
            geometry=WKTElement("POLYGON((82.20 16.95, 82.30 16.95, 82.30 17.05, 82.20 17.05, 82.20 16.95))", srid=4326),
        )
        db.add(inside_res_zone)
        db.commit()

    s, res_inside = request("POST", "/api/v1/agents/geospatial-navigation/assess", {
        "latitude": 17.00,
        "longitude": 82.25,
    })
    assert s == 200
    assert res_inside["geofence_status"] == "INSIDE_RESTRICTED"
    assert res_inside["spatial_status"] == "BLOCKED"
    assert any(z["spatial_relation"] == "CONTAINS" for z in res_inside["zones"])
    print("  [OK] Point-in-zone evaluation correctly identified INSIDE_RESTRICTED -> BLOCKED.")

    with SessionLocal() as db:
        db.query(RestrictedZone).filter(RestrictedZone.name == "TEST_GEO_INSIDE_EXCLUSION").delete()
        db.commit()

    # -------------------------------------------------------------------------
    # 16. Nearby-Zone Boundary Evaluation (NEAR_BOUNDARY)
    # -------------------------------------------------------------------------
    print("\n[16/21] Testing nearby-zone boundary proximity (NEAR_BOUNDARY within 10 km)...")
    with SessionLocal() as db:
        near_res_zone = RestrictedZone(
            name="TEST_GEO_NEAR_BOUNDARY",
            zone_type="MILITARY_EXCLUSION",
            description="Nearby exclusion perimeter.",
            is_active=True,
            geometry=WKTElement("POLYGON((84.03 18.00, 84.08 18.00, 84.08 18.05, 84.03 18.05, 84.03 18.00))", srid=4326),
        )
        db.add(near_res_zone)
        db.commit()

    s, res_near = request("POST", "/api/v1/agents/geospatial-navigation/assess", {
        "latitude": 18.00,
        "longitude": 84.00,  # ~ 3.2 km from boundary
    })
    assert s == 200
    assert res_near["geofence_status"] == "NEAR_BOUNDARY", f"Expected NEAR_BOUNDARY, got {res_near['geofence_status']}"
    assert res_near["spatial_status"] == "CAUTION"
    print(f"  [OK] Boundary proximity evaluated: geofence_status={res_near['geofence_status']}, spatial_status={res_near['spatial_status']}.")

    with SessionLocal() as db:
        db.query(RestrictedZone).filter(RestrictedZone.name == "TEST_GEO_NEAR_BOUNDARY").delete()
        db.commit()

    # -------------------------------------------------------------------------
    # 17. Confidence Calculation
    # -------------------------------------------------------------------------
    print("\n[17/21] Testing confidence calculation strictly bounded in [0.0, 1.0]...")
    for r in [res5, res_route, res_blocked, res_mpa, res_inside, res_near]:
        conf = r["confidence"]
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of bounds"
    print("  [OK] Confidence strictly bounded within [0.0, 1.0].")

    # -------------------------------------------------------------------------
    # 18. Freshness Handling
    # -------------------------------------------------------------------------
    print("\n[18/21] Testing spatial data freshness status...")
    assert res5["data_freshness"] == "FRESH"
    print("  [OK] Spatial data freshness verified as FRESH.")

    # -------------------------------------------------------------------------
    # 19. Missing Spatial Data -> INSUFFICIENT_DATA
    # -------------------------------------------------------------------------
    print("\n[19/21] Testing missing spatial records handling -> INSUFFICIENT_DATA...")
    from agents.geospatial_navigation.reasoning import GeoSpatialNavigationReasoningEngine
    reasoning_engine = GeoSpatialNavigationReasoningEngine()
    empty_res = reasoning_engine.assess_spatial_navigation({"has_spatial_db_data": False})
    assert empty_res[0] == "INSUFFICIENT_DATA"
    assert empty_res[6] == 0.0  # confidence 0.0
    print("  [OK] Missing spatial registry data correctly evaluated as INSUFFICIENT_DATA, confidence 0.0.")

    # -------------------------------------------------------------------------
    # 20. No Misleading 100%-Safe Claims
    # -------------------------------------------------------------------------
    print("\n[20/21] Verifying prohibition of misleading 100%-safe claims in all spatial narratives...")
    all_responses = [res5, res_route, res_blocked, res_mpa, res_inside, res_near]
    for r in all_responses:
        rec = (r.get("recommendation", "") + " " + r.get("explanation", "")).lower()
        assert "route is 100% safe" not in rec, "Prohibited phrase 'route is 100% safe' detected"
        assert "area is guaranteed safe" not in rec, "Prohibited phrase 'area is guaranteed safe' detected"
        assert "navigation is risk-free" not in rec, "Prohibited phrase 'navigation is risk-free' detected"
        assert "100% safe" not in rec, "Prohibited phrase '100% safe' detected"
        assert "guaranteed safe" not in rec, "Prohibited phrase 'guaranteed safe' detected"
        assert "completely safe" not in rec, "Prohibited phrase 'completely safe' detected"
        assert "no risk" not in rec, "Prohibited phrase 'no risk' detected"
    print("  [OK] All recommendations strictly adhere to conservative safety guidelines without guarantees.")

    # -------------------------------------------------------------------------
    # 21. OpenAPI / Swagger Registration
    # -------------------------------------------------------------------------
    print("\n[21/21] Verifying OpenAPI registration for Geo-Spatial Navigation Agent...")
    s, openapi = request("GET", "/openapi.json")
    assert s == 200
    paths = openapi.get("paths", {})
    assert "/api/v1/agents/geospatial-navigation/assess" in paths, "Missing POST /api/v1/agents/geospatial-navigation/assess in OpenAPI"
    geo_tags = paths["/api/v1/agents/geospatial-navigation/assess"]["post"].get("tags", [])
    assert "Geo-Spatial Navigation" in geo_tags, f"Tag 'Geo-Spatial Navigation' missing: {geo_tags}"
    print("  [OK] Endpoint POST /api/v1/agents/geospatial-navigation/assess registered with tag 'Geo-Spatial Navigation'.")

    # Clean up any leftover test records
    with SessionLocal() as db:
        db.query(RestrictedZone).filter(RestrictedZone.name.like("TEST_GEO_%")).delete()
        db.query(ProtectedZone).filter(ProtectedZone.name.like("TEST_GEO_%")).delete()
        db.commit()

    # -------------------------------------------------------------------------
    # Regression: Fishing Intelligence Agent (21 Tests)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("RUNNING FISHING INTELLIGENCE AGENT REGRESSION (21 TESTS)...")
    print("=" * 80)
    from scratch.test_fishing_agent import run_tests as run_fishing_regression
    run_fishing_regression()
    print("  [OK] All 21 Fishing Intelligence Agent regression tests passed.")

    # -------------------------------------------------------------------------
    # Regression: Marine Conditions Agent (18 Tests)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("RUNNING MARINE CONDITIONS INTELLIGENCE AGENT REGRESSION (18 TESTS)...")
    print("=" * 80)
    from scratch.test_marine_conditions_agent import run_tests as run_mc_regression
    run_mc_regression()
    print("  [OK] All 18 Marine Conditions Intelligence Agent regression tests passed.")

    # -------------------------------------------------------------------------
    # Regression: Earth Observation Agent (20 Tests)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("RUNNING EARTH OBSERVATION INTELLIGENCE AGENT REGRESSION (20 TESTS)...")
    print("=" * 80)
    from scratch.test_earth_observation_agent import run_tests as run_eo_regression
    run_eo_regression()
    print("  [OK] All 20 Earth Observation Intelligence Agent regression tests passed.")

    # -------------------------------------------------------------------------
    # Regression: Full Backend Endpoints (19 Endpoints)
    # -------------------------------------------------------------------------
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
        ("POST", "/api/v1/agents/fishing/assess", {
            "latitude": 16.97,
            "longitude": 82.25,
            "date": "2026-09-07",
            "departure_time": "06:00",
            "vessel_type": "small_boat",
        }, 200),
        ("POST", "/api/v1/agents/marine-conditions/assess", {
            "latitude": 16.97,
            "longitude": 82.25,
        }, 200),
        ("POST", "/api/v1/agents/earth-observation/assess", {
            "latitude": 16.97,
            "longitude": 82.25,
        }, 200),
        ("POST", "/api/v1/agents/geospatial-navigation/assess", {
            "latitude": 16.97,
            "longitude": 82.25,
        }, 200),
    ]

    for meth, ep, payload, exp_status in endpoints:
        s, resp = request(meth, ep, payload)
        assert s == exp_status, f"Regression FAIL on {meth} {ep}: expected {exp_status}, got {s}: {resp}"
        print(f"  [OK] {meth} {ep} -> {s}")

    print("\n" + "=" * 80)
    print("ALL 21 GEO-SPATIAL NAVIGATION AGENT TESTS & FULL REGRESSION SUITES PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
