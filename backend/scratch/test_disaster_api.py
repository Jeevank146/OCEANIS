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
from services.freshness import FreshnessCategory, evaluate_freshness, is_record_expired

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
    print("OCEANIS Disaster & Safety Data Layer - Test & Verification Suite")
    print("=" * 70)

    # 1. Module imports & DB initialization
    print("\n[1/16] Verifying module imports & database schema...")
    init_db()
    with engine.connect() as conn:
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = [r[0] for r in res]
        assert "marine_alerts" in tables, "marine_alerts table missing"
        assert "cyclone_tracks" in tables, "cyclone_tracks table missing"
        assert "hazard_zones" in tables, "hazard_zones table missing"
        print("  [OK] Tables marine_alerts, cyclone_tracks, hazard_zones exist in PostGIS database.")

    # 2. Verify PostGIS Geometry columns & Spatial Indexes
    print("\n[2/16] Verifying PostGIS geometry columns and spatial indexes...")
    with engine.connect() as conn:
        geo_cols = conn.execute(text("""
            SELECT f_table_name, f_geometry_column, type, srid 
            FROM geometry_columns 
            WHERE f_table_name IN ('marine_alerts', 'cyclone_tracks', 'hazard_zones');
        """)).fetchall()
        for gc in geo_cols:
            print(f"  [OK] Geometry column: table={gc[0]}, col={gc[1]}, type={gc[2]}, srid={gc[3]}")
        assert len(geo_cols) >= 3, "Missing geometry column registrations"

    # 3. Test Freshness Evaluation Logic
    print("\n[3/16] Testing Freshness Evaluation logic...")
    now = datetime.now(timezone.utc)
    fresh_ts = now - timedelta(hours=2)
    aging_ts = now - timedelta(hours=12)
    stale_ts = now - timedelta(hours=36)
    expired_ts = now - timedelta(hours=90)
    past_effective = now - timedelta(hours=1)
    future_effective = now + timedelta(hours=10)

    assert evaluate_freshness(fresh_ts, current_time=now) == FreshnessCategory.FRESH
    assert evaluate_freshness(aging_ts, current_time=now) == FreshnessCategory.AGING
    assert evaluate_freshness(stale_ts, current_time=now) == FreshnessCategory.STALE
    assert evaluate_freshness(expired_ts, current_time=now) == FreshnessCategory.EXPIRED
    assert evaluate_freshness(fresh_ts, effective_until=past_effective, current_time=now) == FreshnessCategory.EXPIRED
    assert evaluate_freshness(None, current_time=now) == FreshnessCategory.UNKNOWN
    assert is_record_expired(past_effective, current_time=now) is True
    assert is_record_expired(future_effective, current_time=now) is False
    print("  [OK] All freshness and expiry rules passed successfully.")

    # 4. Test Empty Data Queries
    print("\n[4/16] Testing empty queries for disaster endpoints...")
    # Clean test fixtures if any exist from previous runs
    db = SessionLocal()
    db.query(MarineAlert).filter(MarineAlert.source_category == "DEMO/TEST").delete()
    db.query(CycloneTrack).filter(CycloneTrack.source_category == "DEMO/TEST").delete()
    db.query(HazardZone).filter(HazardZone.source_category == "DEMO/TEST").delete()
    db.commit()

    status, alerts_res = request("GET", "/api/v1/disaster/alerts")
    assert status == 200
    print(f"  [OK] GET /api/v1/disaster/alerts returned {status}, count={len(alerts_res)}")

    status, cyclones_res = request("GET", "/api/v1/disaster/cyclones")
    assert status == 200
    print(f"  [OK] GET /api/v1/disaster/cyclones returned {status}, count={len(cyclones_res)}")

    status, hazards_res = request("GET", "/api/v1/disaster/hazard-zones")
    assert status == 200
    print(f"  [OK] GET /api/v1/disaster/hazard-zones returned {status}, count={len(hazards_res)}")

    # 5. Test Safety Assessment with no active hazards/telemetry -> INSUFFICIENT_DATA
    print("\n[5/16] Testing safety assessment without data...")
    status, data = request("GET", "/api/v1/disaster/safety-assessment?latitude=0.0&longitude=0.0")
    assert status == 200
    assert data["status"] == "INSUFFICIENT_DATA"
    print(f"  [OK] Remote coordinates with no data safely returned status='{data['status']}', confidence='{data['confidence']}'")

    # 6. Test Invalid Coordinates Validation (HTTP 422)
    print("\n[6/16] Testing coordinate boundary validation (HTTP 422)...")
    invalid_coords = [
        {"lat": 95.0, "lon": 82.0},
        {"lat": -95.0, "lon": 82.0},
        {"lat": 16.0, "lon": 185.0},
        {"lat": 16.0, "lon": -185.0},
    ]
    for c in invalid_coords:
        status, err = request("GET", f"/api/v1/disaster/safety-assessment?latitude={c['lat']}&longitude={c['lon']}")
        assert status == 422, f"Expected 422 for lat={c['lat']}, lon={c['lon']}, got {status}"
    print("  [OK] Invalid latitudes/longitudes properly rejected with HTTP 422 Unprocessable Entity.")

    # 7. Insert DEMO/TEST Records
    print("\n[7/16] Inserting DEMO/TEST disaster fixtures...")
    now_utc = datetime.now(timezone.utc)
    
    # Active Warning Alert around Kakinada Port (lat 16.98, lon 82.25)
    demo_alert = MarineAlert(
        alert_id="DEMO_ALERT_KAKINADA_HIGH_WAVE",
        title="DEMO: High Wave & Rough Sea Warning for Kakinada Coast",
        alert_type="HIGH_WAVES",
        severity="WARNING",
        status="ACTIVE",
        description="High waves in the range of 3.0-3.8 meters forecast along the coast.",
        source="INCOIS",
        source_category="DEMO/TEST",
        issued_at=now_utc - timedelta(hours=1),
        effective_from=now_utc - timedelta(hours=1),
        effective_until=now_utc + timedelta(hours=24),
        latitude=16.98,
        longitude=82.25,
        geometry=func.ST_SetSRID(func.ST_MakePoint(82.25, 16.98), 4326),
        source_url="https://incois.gov.in/portal/osf/osf.jsp",
        is_active=True,
    )

    # Expired Alert (Should NOT be active)
    demo_expired_alert = MarineAlert(
        alert_id="DEMO_ALERT_EXPIRED_01",
        title="DEMO: Expired Gale Warning",
        alert_type="GALE_WIND",
        severity="CRITICAL",
        status="ACTIVE",
        description="Past advisory that is now expired.",
        source="IMD",
        source_category="DEMO/TEST",
        issued_at=now_utc - timedelta(days=5),
        effective_from=now_utc - timedelta(days=5),
        effective_until=now_utc - timedelta(days=2),
        latitude=16.98,
        longitude=82.25,
        geometry=func.ST_SetSRID(func.ST_MakePoint(82.25, 16.98), 4326),
        is_active=True,
    )

    # Cyclone Track Point (Cyclonic storm 80 km SE of Kakinada)
    demo_cyclone = CycloneTrack(
        cyclone_id="DEMO_BOB_01_2026",
        name="TEST_STORM_A",
        basin="BAY_OF_BENGAL",
        classification="CYCLONIC_STORM",
        latitude=16.40,
        longitude=82.70,
        geometry=func.ST_SetSRID(func.ST_MakePoint(82.70, 16.40), 4326),
        wind_speed_kmh=85.0,
        pressure_hpa=992.0,
        movement_direction_deg=315.0,
        movement_speed_kmh=18.0,
        observed_at=now_utc - timedelta(hours=2),
        source="IMD",
        source_category="DEMO/TEST",
        data_type="OBSERVED",
        is_active=True,
    )

    # Hazard Zone Polygon enclosing Kakinada coastal waters
    wkt_hazard = "POLYGON((82.15 16.85, 82.40 16.85, 82.40 17.10, 82.15 17.10, 82.15 16.85))"
    demo_hazard_zone = HazardZone(
        name="DEMO Kakinada Storm Surge & Wave Risk Zone",
        hazard_type="STORM_SURGE_ZONE",
        severity="WARNING",
        description="Low-lying coastal waters vulnerable to surge inundation during storm passage.",
        geometry=func.ST_GeomFromText(wkt_hazard, 4326),
        source="INCOIS",
        source_category="DEMO/TEST",
        effective_from=now_utc - timedelta(hours=3),
        effective_until=now_utc + timedelta(hours=48),
        is_active=True,
    )

    db.add(demo_alert)
    db.add(demo_expired_alert)
    db.add(demo_cyclone)
    db.add(demo_hazard_zone)
    db.commit()
    print("  [OK] Inserted DEMO/TEST fixtures into database.")

    # 8. Test GET /api/v1/disaster/alerts with spatial proximity
    print("\n[8/16] Testing GET /api/v1/disaster/alerts...")
    status, alerts_data = request("GET", "/api/v1/disaster/alerts?latitude=16.98&longitude=82.25&radius_km=50")
    assert status == 200
    assert len(alerts_data) >= 1
    kakinada_alert = next((a for a in alerts_data if a["alert_id"] == "DEMO_ALERT_KAKINADA_HIGH_WAVE"), None)
    assert kakinada_alert is not None
    assert kakinada_alert["severity"] == "WARNING"
    assert kakinada_alert["freshness"] in (FreshnessCategory.FRESH, FreshnessCategory.AGING)
    print(f"  [OK] Active alert retrieved: '{kakinada_alert['title']}', distance_km={kakinada_alert['distance_km']}, freshness={kakinada_alert['freshness']}")

    # 9. Test GET /api/v1/disaster/alerts/{alert_id}
    print("\n[9/16] Testing GET /api/v1/disaster/alerts/{alert_id}...")
    status, single_alert = request("GET", "/api/v1/disaster/alerts/DEMO_ALERT_KAKINADA_HIGH_WAVE")
    assert status == 200
    assert single_alert["alert_id"] == "DEMO_ALERT_KAKINADA_HIGH_WAVE"

    status_404, _ = request("GET", "/api/v1/disaster/alerts/NON_EXISTENT_ID")
    assert status_404 == 404
    print("  [OK] Alert retrieval by ID and 404 response verified.")

    # 10. Verify Expired Alert is Excluded from active queries
    print("\n[10/16] Verifying expired alert is filtered out when active_only=True...")
    status, active_alerts = request("GET", "/api/v1/disaster/alerts?active_only=true")
    assert status == 200
    active_ids = [a["alert_id"] for a in active_alerts]
    assert "DEMO_ALERT_EXPIRED_01" not in active_ids, "Expired alert must not appear in active queries"

    status, all_alerts = request("GET", "/api/v1/disaster/alerts?active_only=false")
    assert status == 200
    all_ids = [a["alert_id"] for a in all_alerts]
    assert "DEMO_ALERT_EXPIRED_01" in all_ids
    expired_item = next(a for a in all_alerts if a["alert_id"] == "DEMO_ALERT_EXPIRED_01")
    assert expired_item["freshness"] == FreshnessCategory.EXPIRED
    print(f"  [OK] Expired alert is properly excluded from active queries and marked freshness='{expired_item['freshness']}'.")

    # 11. Test GET /api/v1/disaster/cyclones
    print("\n[11/16] Testing GET /api/v1/disaster/cyclones...")
    status, cyclones_data = request("GET", "/api/v1/disaster/cyclones?latitude=16.98&longitude=82.25&radius_km=300")
    assert status == 200
    assert len(cyclones_data) >= 1
    cyc = next((c for c in cyclones_data if c["cyclone_id"] == "DEMO_BOB_01_2026"), None)
    assert cyc is not None
    assert cyc["name"] == "TEST_STORM_A"
    assert cyc["distance_km"] is not None
    print(f"  [OK] Cyclone track retrieved: name='{cyc['name']}', class='{cyc['classification']}', distance_km={cyc['distance_km']}")

    # 12. Test GET /api/v1/disaster/hazard-zones with containment
    print("\n[12/16] Testing GET /api/v1/disaster/hazard-zones with containment...")
    # Point inside polygon: lat 16.98, lon 82.25
    status, hz_data = request("GET", "/api/v1/disaster/hazard-zones?latitude=16.98&longitude=82.25&radius_km=50")
    assert status == 200
    assert len(hz_data) >= 1
    hz = next((h for h in hz_data if "DEMO Kakinada" in h["name"]), None)
    assert hz is not None
    assert hz["contains_point"] is True, "Point must be contained in hazard polygon"
    print(f"  [OK] Hazard zone retrieved: name='{hz['name']}', contains_point={hz['contains_point']}, distance_km={hz['distance_km']}")

    # Point outside polygon: lat 18.0, lon 84.0
    status_out, hz_out_data = request("GET", "/api/v1/disaster/hazard-zones?latitude=18.0&longitude=84.0&radius_km=500")
    assert status_out == 200
    hz_out = next((h for h in hz_out_data if "DEMO Kakinada" in h["name"]), None)
    if hz_out:
        assert hz_out["contains_point"] is False

    # 13. Test GET /api/v1/disaster/safety-assessment for hazardous location
    print("\n[13/16] Testing deterministic safety assessment for hazardous location...")
    status, assessment = request("GET", "/api/v1/disaster/safety-assessment?latitude=16.98&longitude=82.25&radius_km=50")
    assert status == 200
    assert assessment["status"] in ("WARNING", "CRITICAL"), f"Expected WARNING/CRITICAL, got {assessment['status']}"
    assert len(assessment["active_alerts"]) >= 1
    assert len(assessment["nearby_hazards"]) >= 1
    assert len(assessment["nearby_cyclones"]) >= 1
    assert len(assessment["reasons"]) >= 1
    print(f"  [OK] Deterministic Safety Status: {assessment['status']}")
    print(f"  [OK] Confidence: {assessment['confidence']}")
    print(f"  [OK] Data Freshness: {assessment['data_freshness']}")
    print(f"  [OK] Nearest Safe Port: {assessment.get('nearest_safe_port', {}).get('name')} ({assessment.get('nearest_safe_port', {}).get('distance_km')} km)")
    print(f"  [OK] Assessment Reasons:")
    for r in assessment["reasons"]:
        print(f"     - {r}")

    # 14. Verify OpenAPI Swagger registration
    print("\n[14/16] Verifying Swagger OpenAPI schema registration...")
    status, openapi = request("GET", "/openapi.json")
    assert status == 200
    paths = openapi.get("paths", {})
    assert "/api/v1/disaster/alerts" in paths
    assert "/api/v1/disaster/alerts/{alert_id}" in paths
    assert "/api/v1/disaster/cyclones" in paths
    assert "/api/v1/disaster/hazard-zones" in paths
    assert "/api/v1/disaster/safety-assessment" in paths

    disaster_tag_found = False
    for path, methods in paths.items():
        if path.startswith("/api/v1/disaster"):
            for m, spec in methods.items():
                if "Disaster & Safety" in spec.get("tags", []):
                    disaster_tag_found = True
                    break
    assert disaster_tag_found, "Disaster & Safety tag missing from OpenAPI spec"
    print("  [OK] All Disaster & Safety endpoints and OpenAPI tags properly registered.")

    # 15. Run Regression Tests for ALL existing endpoints
    print("\n[15/16] Running full regression test suite across all existing API endpoints...")
    
    # Root & Health
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
    print("  [OK] All existing backend endpoints are passing with zero regression.")

    # 16. Clean up DEMO/TEST fixtures
    print("\n[16/16] Cleaning up test fixtures...")
    db.query(MarineAlert).filter(MarineAlert.source_category == "DEMO/TEST").delete()
    db.query(CycloneTrack).filter(CycloneTrack.source_category == "DEMO/TEST").delete()
    db.query(HazardZone).filter(HazardZone.source_category == "DEMO/TEST").delete()
    db.commit()
    db.close()
    print("  [OK] Test cleanup completed.")

    print("\n" + "=" * 70)
    print("ALL DISASTER & SAFETY DATA LAYER VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_suite()
