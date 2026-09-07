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
from models.geospatial import Port, ProtectedZone, RestrictedZone
from models.marine_operations import MarineOperation

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


def test_suite():
    print("=" * 70)
    print("OCEANIS Marine Operations Data Layer - Test & Verification Suite")
    print("=" * 70)

    # 1. Module imports & Database table verification
    print("\n[1/19] Verifying module imports & database table structure...")
    init_db()
    with engine.connect() as conn:
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = [r[0] for r in res]
        assert "marine_operations" in tables, "marine_operations table missing"
        print("  [OK] marine_operations table exists in PostgreSQL database.")

    # Clean previous test records if any
    with SessionLocal() as db:
        db.query(MarineOperation).filter(MarineOperation.operation_id.like("TEST_%")).delete(synchronize_session=False)
        db.commit()

    # 2. Distance Calculation Endpoint
    print("\n[2/19] Testing GET /api/v1/operations/distance...")
    status, dist_res = request("GET", "/api/v1/operations/distance?origin_latitude=16.9890&origin_longitude=82.2474&destination_latitude=17.6868&destination_longitude=83.2185")
    assert status == 200
    assert 120.0 < dist_res["distance_km"] < 150.0
    assert dist_res["distance_nautical_miles"] > 0
    assert dist_res["calculation_method"] == "HAVERSINE_GEODESIC"
    print(f"  [OK] Distance: {dist_res['distance_km']} km ({dist_res['distance_nautical_miles']} NM)")

    # 3. Transit Duration Estimation Endpoint
    print("\n[3/19] Testing GET /api/v1/operations/estimate-time...")
    status, time_res = request("GET", "/api/v1/operations/estimate-time?origin_latitude=16.9890&origin_longitude=82.2474&destination_latitude=17.6868&destination_longitude=83.2185&speed_kmh=25.0")
    assert status == 200
    assert time_res["speed_kmh"] == 25.0
    assert time_res["estimated_duration_minutes"] > 0
    assert time_res["estimated_duration_hours"] > 0
    print(f"  [OK] Time Estimate: {time_res['estimated_duration_minutes']} mins ({time_res['estimated_duration_hours']} hrs) at {time_res['speed_kmh']} km/h")

    # 4. Coordinate Boundary Validation (HTTP 422)
    print("\n[4/19] Testing coordinate boundary validation (HTTP 422)...")
    invalid_coords = [
        {"origin_lat": 95.0, "origin_lon": 82.0, "dest_lat": 17.0, "dest_lon": 83.0},
        {"origin_lat": 16.0, "origin_lon": 195.0, "dest_lat": 17.0, "dest_lon": 83.0},
        {"origin_lat": 16.0, "origin_lon": 82.0, "dest_lat": -95.0, "dest_lon": 83.0},
    ]
    for c in invalid_coords:
        status, err = request("GET", f"/api/v1/operations/distance?origin_latitude={c['origin_lat']}&origin_longitude={c['origin_lon']}&destination_latitude={c['dest_lat']}&destination_longitude={c['dest_lon']}")
        assert status == 422, f"Expected 422, got {status}"
    print("  [OK] Invalid coordinates rejected with HTTP 422 Unprocessable Entity.")

    # 5. Invalid Speed Validation (HTTP 422)
    print("\n[5/19] Testing invalid speed validation (HTTP 422)...")
    status, err = request("GET", "/api/v1/operations/estimate-time?origin_latitude=16.98&origin_longitude=82.25&destination_latitude=17.68&destination_longitude=83.21&speed_kmh=-10.0")
    assert status == 422
    status, err = request("GET", "/api/v1/operations/estimate-time?origin_latitude=16.98&origin_longitude=82.25&destination_latitude=17.68&destination_longitude=83.21&speed_kmh=0.0")
    assert status == 422
    print("  [OK] Non-positive speeds properly rejected with HTTP 422.")

    # 6. Same Origin and Destination Handling
    print("\n[6/19] Testing same origin and destination handling...")
    status, zero_dist = request("GET", "/api/v1/operations/distance?origin_latitude=16.98&origin_longitude=82.25&destination_latitude=16.98&destination_longitude=82.25")
    assert status == 200
    assert zero_dist["distance_km"] == 0.0
    assert zero_dist["distance_nautical_miles"] == 0.0
    print("  [OK] Zero-distance stationary origin/destination handled correctly.")

    # 7. Create Marine Operation (POST /api/v1/operations)
    print("\n[7/19] Testing POST /api/v1/operations (Creating operation)...")
    op_payload = {
        "operation_id": "TEST_OP_KAKINADA_VIZAG_01",
        "operation_type": "FISHING_TRIP",
        "vessel_type": "TRAWLER",
        "vessel_name": "SEA_EXPLORER_IV",
        "origin_latitude": 16.9891,
        "origin_longitude": 82.2475,
        "destination_latitude": 17.6868,
        "destination_longitude": 83.2185,
        "planned_departure_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "estimated_speed_kmh": 22.0,
        "notes": "Coastal pelagic fishing operation and port transfer.",
        "source": "MANUAL_INPUT",
        "data_type": "PLANNED",
    }
    status, created_op = request("POST", "/api/v1/operations", op_payload)
    assert status == 201, f"Expected 201, got {status}: {created_op}"
    assert created_op["operation_id"] == "TEST_OP_KAKINADA_VIZAG_01"
    assert created_op["estimated_distance_km"] > 100.0
    assert created_op["estimated_duration_minutes"] is not None
    assert created_op["operational_status"] == "PLANNED"
    print(f"  [OK] Operation created: ID='{created_op['operation_id']}', Distance={created_op['estimated_distance_km']}km, Duration={created_op['estimated_duration_minutes']}mins")

    # 8. Retrieve Marine Operation (GET /api/v1/operations/{operation_id})
    print("\n[8/19] Testing GET /api/v1/operations/{operation_id}...")
    status, fetched_op = request("GET", f"/api/v1/operations/{created_op['operation_id']}")
    assert status == 200
    assert fetched_op["operation_id"] == created_op["operation_id"]
    assert fetched_op["vessel_name"] == "SEA_EXPLORER_IV"

    status_404, _ = request("GET", "/api/v1/operations/NON_EXISTENT_OP_ID")
    assert status_404 == 404
    print("  [OK] Operation retrieval by ID and 404 response verified.")

    # 9. List Marine Operations (GET /api/v1/operations)
    print("\n[9/19] Testing GET /api/v1/operations (List operations)...")
    status, ops_list = request("GET", "/api/v1/operations?limit=10")
    assert status == 200
    assert len(ops_list) >= 1
    found = any(op["operation_id"] == "TEST_OP_KAKINADA_VIZAG_01" for op in ops_list)
    assert found
    print(f"  [OK] Listed operations count: {len(ops_list)}")

    # 10. Update Marine Operation (PATCH /api/v1/operations/{operation_id})
    print("\n[10/19] Testing PATCH /api/v1/operations/{operation_id}...")
    update_payload = {
        "estimated_speed_kmh": 30.0,
        "notes": "Updated operational speed for fast transit.",
        "operational_status": "ASSESSED",
    }
    status, updated_op = request("PATCH", f"/api/v1/operations/{created_op['operation_id']}", update_payload)
    assert status == 200
    assert updated_op["estimated_speed_kmh"] == 30.0
    assert updated_op["operational_status"] == "ASSESSED"
    assert updated_op["estimated_duration_minutes"] < created_op["estimated_duration_minutes"]
    print(f"  [OK] Operation updated: speed={updated_op['estimated_speed_kmh']} km/h, duration={updated_op['estimated_duration_minutes']} mins")

    # 11. Run Saved Operation Assessment (GET /api/v1/operations/{operation_id}/assessment)
    print("\n[11/19] Testing GET /api/v1/operations/{operation_id}/assessment...")
    status, op_assessment = request("GET", f"/api/v1/operations/{created_op['operation_id']}/assessment")
    assert status == 200
    assert op_assessment["operation_id"] == created_op["operation_id"]
    assert "route_assessment" in op_assessment
    assert "operational_status" in op_assessment
    assert "confidence" in op_assessment
    assert len(op_assessment["reasons"]) >= 1
    print(f"  [OK] Saved operation assessed: status={op_assessment['operational_status']}, confidence={op_assessment['confidence']}")

    # 12. Ad-hoc Route Assessment (GET /api/v1/operations/assess-route)
    print("\n[12/19] Testing GET /api/v1/operations/assess-route (Clear Corridor)...")
    status, route_assess = request("GET", "/api/v1/operations/assess-route?origin_latitude=16.9891&origin_longitude=82.2475&destination_latitude=17.6868&destination_longitude=83.2185&speed_kmh=25.0")
    assert status == 200
    assert route_assess["distance_km"] > 100.0
    assert route_assess["estimated_duration_minutes"] is not None
    assert route_assess["operational_status"] in ("ASSESSED", "CAUTION", "WARNING", "BLOCKED", "INSUFFICIENT_DATA")
    print(f"  [OK] Route assessment returned status='{route_assess['operational_status']}', reasons={len(route_assess['reasons'])}")

    # 13. Route Assessment with Missing Speed (Explicit Missing Data handling)
    print("\n[13/19] Testing route assessment without speed parameter...")
    status, no_speed_assess = request("GET", "/api/v1/operations/assess-route?origin_latitude=16.9891&origin_longitude=82.2475&destination_latitude=17.6868&destination_longitude=83.2185")
    assert status == 200
    assert no_speed_assess["estimated_speed_kmh"] is None
    assert no_speed_assess["estimated_duration_minutes"] is None
    assert any("cruising speed was not specified" in r for r in no_speed_assess["reasons"])
    print("  [OK] Missing vessel speed safely produces None duration and explicit informational reason.")

    # 14. Route Assessment Intersecting Restricted Zone -> BLOCKED
    print("\n[14/19] Testing operational assessment through Restricted Zone (Expecting BLOCKED)...")
    # Path passing directly through demo naval firing exclusion zone (lat 17.35, lon 83.55)
    status, blocked_assess = request("GET", "/api/v1/operations/assess-route?origin_latitude=17.1&origin_longitude=83.3&destination_latitude=17.6&destination_longitude=83.8&speed_kmh=20.0")
    assert status == 200
    assert blocked_assess["operational_status"] == "BLOCKED"
    assert blocked_assess["route_assessment"]["restricted_zone_intersection"] is True
    print(f"  [OK] Restricted zone intersection correctly evaluated as status='{blocked_assess['operational_status']}'")

    # 15. Route Assessment with Active Hazard Zone & Cyclone
    print("\n[15/19] Testing operational assessment in presence of Hazard Zone / Warning...")
    db = SessionLocal()
    now_utc = datetime.now(timezone.utc)
    wkt_hazard = "POLYGON((82.10 16.80, 82.50 16.80, 82.50 17.20, 82.10 17.20, 82.10 16.80))"
    demo_hz = HazardZone(
        name="DEMO Operations Coastal Risk Zone",
        hazard_type="CYCLONE_IMPACT_ZONE",
        severity="WARNING",
        description="Demo hazard zone for operations evaluation.",
        geometry=func.ST_GeomFromText(wkt_hazard, 4326),
        source="INCOIS",
        source_category="DEMO/TEST",
        effective_from=now_utc - timedelta(hours=1),
        effective_until=now_utc + timedelta(hours=24),
        is_active=True,
    )
    db.add(demo_hz)
    db.commit()

    status, hz_assess = request("GET", "/api/v1/operations/assess-route?origin_latitude=16.98&origin_longitude=82.25&destination_latitude=17.05&destination_longitude=82.35&speed_kmh=20.0")
    assert status == 200
    assert hz_assess["operational_status"] in ("WARNING", "BLOCKED", "CAUTION")
    assert hz_assess["route_assessment"]["hazard_intersection"] is True
    print(f"  [OK] Hazard zone intersection detected: status='{hz_assess['operational_status']}', intersecting hazards={hz_assess['route_assessment']['intersecting_hazard_zones']}")

    db.query(HazardZone).filter(HazardZone.source_category == "DEMO/TEST").delete()
    db.commit()

    # 16. Departure Assessment Endpoint (GET /api/v1/operations/departure-assessment)
    print("\n[16/19] Testing GET /api/v1/operations/departure-assessment...")
    dep_time = (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    status, dep_assess = request("GET", f"/api/v1/operations/departure-assessment?origin_latitude=16.9891&origin_longitude=82.2475&destination_latitude=17.6868&destination_longitude=83.2185&departure_at={dep_time}&speed_kmh=25.0")
    if status != 200:
        print(f"  [FAIL] Departure assessment returned {status}: {dep_assess}")
    assert status == 200, f"Expected 200, got {status}: {dep_assess}"
    assert "departure_at" in dep_assess
    assert dep_assess["estimated_arrival_at"] is not None
    assert "operational_status" in dep_assess
    print(f"  [OK] Departure assessment: departure='{dep_assess['departure_at']}', arrival='{dep_assess['estimated_arrival_at']}', status='{dep_assess['operational_status']}'")

    # 17. OpenAPI Swagger Schema Registration Check
    print("\n[17/19] Verifying Swagger OpenAPI schema registration for Marine Operations...")
    status, openapi = request("GET", "/openapi.json")
    assert status == 200
    paths = openapi.get("paths", {})
    for expected_path in [
        "/api/v1/operations",
        "/api/v1/operations/distance",
        "/api/v1/operations/estimate-time",
        "/api/v1/operations/assess-route",
        "/api/v1/operations/departure-assessment",
        "/api/v1/operations/{operation_id}",
        "/api/v1/operations/{operation_id}/assessment",
    ]:
        assert expected_path in paths, f"Missing route in OpenAPI: {expected_path}"
        print(f"  [OK] Route registered in OpenAPI: {expected_path}")

    # 18. Full Regression Test across all backend endpoints
    print("\n[18/19] Running full regression test suite across all previous layers...")
    
    # System & Health
    status, r = request("GET", "/")
    assert status == 200 and r["project"] == "OCEANIS"
    status, r = request("GET", "/health")
    assert status == 200 and r["status"] == "healthy"
    status, r = request("GET", "/api/v1/system/health")
    assert status == 200 and r["status"] == "healthy"

    # Data Sources
    status, r = request("GET", "/api/v1/data-sources")
    assert status == 200

    # Weather
    status, r = request("GET", "/api/v1/weather/current?latitude=16.9890&longitude=82.2474")
    assert status == 200

    # Marine
    status, r = request("GET", "/api/v1/marine/conditions?latitude=16.9890&longitude=82.2474")
    assert status == 200

    # Earth Observation
    status, r = request("GET", "/api/v1/earth-observation/observations?latitude=16.9890&longitude=82.2474")
    assert status == 200

    # Geospatial
    status, r = request("GET", "/api/v1/geospatial/ports")
    assert status == 200
    status, r = request("GET", "/api/v1/geospatial/restricted-zones")
    assert status == 200
    status, r = request("GET", "/api/v1/geospatial/protected-zones")
    assert status == 200
    status, r = request("GET", "/api/v1/geospatial/nearby-zones?latitude=16.9890&longitude=82.2474")
    assert status == 200
    status, r = request("GET", "/api/v1/geospatial/distance?origin_latitude=16.98&origin_longitude=82.25&destination_latitude=17.68&destination_longitude=83.21")
    assert status == 200
    status, r = request("GET", "/api/v1/geospatial/assess-route?origin_latitude=16.98&origin_longitude=82.25&destination_latitude=17.68&destination_longitude=83.21")
    assert status == 200

    # Disaster & Safety
    status, r = request("GET", "/api/v1/disaster/alerts")
    assert status == 200
    status, r = request("GET", "/api/v1/disaster/cyclones")
    assert status == 200
    status, r = request("GET", "/api/v1/disaster/hazard-zones")
    assert status == 200
    status, r = request("GET", "/api/v1/disaster/safety-assessment?latitude=16.9890&longitude=82.2474")
    assert status == 200

    print("  [OK] All 15 existing backend endpoints passed with zero regression.")

    # 19. Clean up test records
    print("\n[19/19] Cleaning up test operations...")
    db.query(MarineOperation).filter(MarineOperation.operation_id == "TEST_OP_KAKINADA_VIZAG_01").delete()
    db.commit()
    db.close()
    print("  [OK] Test cleanup completed.")

    print("\n" + "=" * 70)
    print("ALL MARINE OPERATIONS DATA LAYER VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_suite()
