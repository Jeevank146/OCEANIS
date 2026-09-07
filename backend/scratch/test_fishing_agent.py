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
from models.earth_observation import EarthObservation
from models.geospatial import Port, ProtectedZone, RestrictedZone
from models.marine import MarineObservation
from models.marine_operations import MarineOperation
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
    print("=" * 75)
    print("OCEANIS Fishing Intelligence Agent - Comprehensive Verification Suite")
    print("=" * 75)

    init_db()

    # 1. Test Agent Module Imports
    print("\n[1/21] Verifying Agent module imports...")
    try:
        from agents.fishing import (
            ConfidenceAssessment,
            EvidenceItem,
            FishingAgentService,
            FishingAssessment,
            FishingDataCollector,
            FishingIntelligenceAgent,
            FishingLocationInput,
            FishingQuery,
            FishingReasoningEngine,
            FishingSuitability,
            FishingSuitabilityFactor,
            LocationComparisonQuery,
            LocationComparisonResponse,
            PFZAssessment,
            WhatIfQuery,
            WhatIfResponse,
        )
        from agents.fishing.collector import FishingDataCollector as FDC
        from agents.fishing.prompts import generate_deterministic_narrative
        from agents.fishing.reasoning import FishingThresholds
        from api.v1.fishing import router as fishing_api_router

        print("  [OK] All Fishing Intelligence Agent modules and collector imported cleanly.")
    except Exception as e:
        print(f"  [FAIL] Import failed: {e}")
        raise e

    # Clean previous TEST/DEMO records
    with SessionLocal() as db:
        db.query(MarineAlert).filter(MarineAlert.alert_id.like("TEST_%")).delete(synchronize_session=False)
        db.query(HazardZone).filter(HazardZone.name.like("TEST_%")).delete(synchronize_session=False)
        db.query(CycloneTrack).filter(CycloneTrack.cyclone_id.like("TEST_%")).delete(synchronize_session=False)
        db.query(RestrictedZone).filter(RestrictedZone.name.like("TEST_%")).delete(synchronize_session=False)
        db.query(ProtectedZone).filter(ProtectedZone.name.like("TEST_%")).delete(synchronize_session=False)
        db.query(MarineObservation).filter(MarineObservation.source.like("TEST_%")).delete(synchronize_session=False)
        db.query(WeatherObservation).filter(WeatherObservation.source.like("TEST_%")).delete(synchronize_session=False)
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_%")).delete(synchronize_session=False)
        db.commit()

    # Coordinates for testing
    lat_kakinada = 16.97
    lon_kakinada = 82.25

    # Seed baseline telemetry around Kakinada for tests
    now_utc = datetime.now(timezone.utc)
    with SessionLocal() as db:
        marine_obs = MarineObservation(
            latitude=lat_kakinada,
            longitude=lon_kakinada,
            wave_height_m=0.8,
            wave_direction_deg=140.0,
            wave_period_s=6.5,
            swell_wave_height_m=0.5,
            swell_wave_direction_deg=135.0,
            swell_wave_period_s=7.0,
            wind_wave_height_m=0.4,
            ocean_current_velocity_kmh=1.2,
            ocean_current_direction_deg=45.0,
            sea_surface_temperature_c=28.2,
            observed_at=now_utc - timedelta(minutes=30),
            source="TEST_MARINE_SERVICE",
            data_type="OBSERVATION",
            quality_flag="GOOD",
        )
        weather_obs = WeatherObservation(
            latitude=lat_kakinada,
            longitude=lon_kakinada,
            temperature_c=29.0,
            humidity_percent=75.0,
            wind_speed_kmh=15.0,
            wind_direction_deg=110.0,
            precipitation_mm=0.0,
            observed_at=now_utc - timedelta(minutes=30),
            source="TEST_WEATHER_SERVICE",
        )
        eo_obs = EarthObservation(
            latitude=lat_kakinada,
            longitude=lon_kakinada,
            sea_surface_temperature_c=28.4,
            chlorophyll_a_mg_m3=0.45,
            cloud_cover_percent=10.0,
            satellite_platform="Sentinel-3",
            sensor_instrument="OLCI",
            product_type="CHL_OC4ME",
            observed_at=now_utc - timedelta(hours=2),
            retrieved_at=now_utc,
            source="TEST_COPERNICUS",
        )
        db.add_all([marine_obs, weather_obs, eo_obs])
        db.commit()

    # 2. Test Valid FishingQuery
    print("\n[2/21] Testing valid FishingQuery via POST /api/v1/agents/fishing/assess...")
    query_payload = {
        "latitude": lat_kakinada,
        "longitude": lon_kakinada,
        "date": "2026-09-07",
        "departure_time": "06:00",
        "vessel_type": "small_boat",
        "target_species": "mackerel",
        "question": "Can I go fishing tomorrow morning?",
    }
    status, data = request("POST", "/api/v1/agents/fishing/assess", query_payload)
    assert status == 200, f"Expected 200, got {status}: {data}"
    assert "overall_suitability" in data, "Missing overall_suitability"
    assert "safety_status" in data, "Missing safety_status"
    assert "risk_level" in data, "Missing risk_level"
    assert "key_conditions" in data, "Missing key_conditions"
    assert "evidence_used" in data, "Missing evidence_used"
    assert "domain_contributions" in data, "Missing domain_contributions"
    assert "recommendation" in data, "Missing recommendation"
    assert "explanation" in data, "Missing explanation"
    assert "data_quality" in data, "Missing data_quality"
    print(f"  [OK] Valid assessment returned suitability: {data['overall_suitability']['status']}, risk: {data['risk_level']}, confidence: {data['confidence']['level']}")

    # 3. Test Invalid Latitude -> 422
    print("\n[3/21] Testing invalid latitude (>90) validation...")
    status, data_err = request("POST", "/api/v1/agents/fishing/assess", {
        "latitude": 95.0,
        "longitude": 82.25,
    })
    assert status == 422, f"Expected 422, got {status}: {data_err}"
    print("  [OK] Invalid latitude rejected with HTTP 422 Unprocessable Entity.")

    # 4. Test Invalid Longitude -> 422
    print("\n[4/21] Testing invalid longitude (>180) validation...")
    status, data_err = request("POST", "/api/v1/agents/fishing/assess", {
        "latitude": 16.97,
        "longitude": 185.0,
    })
    assert status == 422, f"Expected 422, got {status}: {data_err}"
    print("  [OK] Invalid longitude rejected with HTTP 422 Unprocessable Entity.")

    # 5. Basic Fishing Assessment Structure
    print("\n[5/21] Testing basic fishing assessment response structure...")
    assert data["location"]["latitude"] == lat_kakinada
    assert data["location"]["longitude"] == lon_kakinada
    assert isinstance(data["reasons"], list) and len(data["reasons"]) > 0
    assert "wave_height_m" in data["key_conditions"] or "wind_speed_kmh" in data["key_conditions"]
    assert "weather" in data["domain_contributions"] and "marine_conditions" in data["domain_contributions"]
    print("  [OK] Assessment structure verified (query, location, overall_suitability, key_conditions, domain_contributions, reasons, evidence).")

    # 6. Weather Evidence Retrieval
    print("\n[6/21] Verifying Weather evidence retrieval...")
    weather_ev = [e for e in data["evidence_used"] if "wind" in e["factor"] or "temperature" in e["factor"]]
    assert len(weather_ev) > 0, "No weather evidence found"
    assert any("TEST" in e["source"] or "Open-Meteo" in e["source"] or "Weather" in e["source"] for e in weather_ev)
    print(f"  [OK] Weather evidence successfully retrieved ({len(weather_ev)} factors).")

    # 7. Marine Evidence Retrieval
    print("\n[7/21] Verifying Marine Conditions evidence retrieval...")
    marine_ev = [e for e in data["evidence_used"] if "wave" in e["factor"] or "current" in e["factor"] or e["factor"] == "sea_surface_temperature"]
    assert len(marine_ev) > 0, "No marine evidence found"
    assert any("TEST" in e["source"] or "Open-Meteo" in e["source"] or "Marine" in e["source"] for e in marine_ev)
    print(f"  [OK] Marine evidence successfully retrieved ({len(marine_ev)} factors).")

    # 8. Earth Observation Evidence Retrieval
    print("\n[8/21] Verifying Earth Observation evidence retrieval...")
    eo_ev = [e for e in data["evidence_used"] if "chlorophyll" in e["factor"] or "cloud" in e["factor"]]
    assert len(eo_ev) > 0, "No EO evidence found"
    assert any("TEST" in e["source"] or "Copernicus" in e["source"] or "Sentinel" in e["source"] for e in eo_ev)
    print(f"  [OK] EO evidence successfully retrieved ({len(eo_ev)} factors).")

    # 9. Geo-Spatial Evidence Retrieval
    print("\n[9/21] Verifying Geo-Spatial regulatory evidence retrieval...")
    geo_factors = [f for f in data["overall_suitability"]["factors"] if "Navigability" in f["name"] or "Zoning" in f["name"] or "Protected" in f["name"]]
    assert len(geo_factors) > 0, "No geospatial factors evaluated"
    print(f"  [OK] Geo-spatial factor evaluated: '{geo_factors[0]['name']}' = {geo_factors[0]['status']}.")

    # 10. Disaster/Safety Evidence Retrieval
    print("\n[10/21] Verifying Disaster & Safety evidence retrieval...")
    assert "safety" in data and "status" in data["safety"]
    print(f"  [OK] Disaster/Safety assessment integrated: safety status = {data['safety']['status']}.")

    # 11. Safety CRITICAL -> BLOCKED Fishing Decision
    print("\n[11/21] Testing Safety CRITICAL -> BLOCKED fishing decision override...")
    with SessionLocal() as db:
        crit_alert = MarineAlert(
            alert_id="TEST_CRIT_01",
            title="TEST Extreme Cyclone Warning",
            description="Severe cyclonic storm crossing coast. Complete suspension of fishing.",
            severity="CRITICAL",
            alert_type="CYCLONE",
            status="ACTIVE",
            issued_at=now_utc - timedelta(hours=1),
            effective_from=now_utc - timedelta(hours=1),
            effective_until=now_utc + timedelta(hours=24),
            source="IMD / INCOIS",
            source_category="OFFICIAL",
            geometry=WKTElement("POLYGON((82.0 16.5, 82.5 16.5, 82.5 17.5, 82.0 17.5, 82.0 16.5))", srid=4326),
        )
        db.add(crit_alert)
        db.commit()

    status, data_crit = request("POST", "/api/v1/agents/fishing/assess", query_payload)
    assert status == 200
    assert data_crit["overall_suitability"]["status"] == "BLOCKED", f"Expected BLOCKED, got {data_crit['overall_suitability']['status']}"
    assert data_crit["safety_status"] == "CRITICAL"
    assert data_crit["risk_level"] == "CRITICAL"
    assert "OPERATIONS BLOCKED" in data_crit["recommendation"]
    print("  [OK] Safety CRITICAL override verified: suitability = BLOCKED, risk = CRITICAL, departure prohibited.")

    # 12. Safety WARNING -> Warning Recommendation
    print("\n[12/21] Testing Safety WARNING -> Warning recommendation override...")
    with SessionLocal() as db:
        db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_CRIT_01").delete()
        warn_alert = MarineAlert(
            alert_id="TEST_WARN_01",
            title="TEST High Wave Alert",
            description="Rough sea conditions with swell waves up to 3.5m expected.",
            severity="WARNING",
            alert_type="HIGH_WAVES",
            status="ACTIVE",
            issued_at=now_utc - timedelta(hours=1),
            effective_from=now_utc - timedelta(hours=1),
            effective_until=now_utc + timedelta(hours=24),
            source="INCOIS",
            source_category="OFFICIAL",
            geometry=WKTElement("POLYGON((82.0 16.5, 82.5 16.5, 82.5 17.5, 82.0 17.5, 82.0 16.5))", srid=4326),
        )
        db.add(warn_alert)
        db.commit()

    status, data_warn = request("POST", "/api/v1/agents/fishing/assess", query_payload)
    assert status == 200
    assert data_warn["overall_suitability"]["status"] == "WARNING", f"Expected WARNING, got {data_warn['overall_suitability']['status']}"
    assert data_warn["risk_level"] == "HIGH"
    assert "WARNING" in data_warn["recommendation"]
    print("  [OK] Safety WARNING override verified: suitability = WARNING, risk = HIGH.")

    # 13. Restricted Zone -> BLOCKED Decision
    print("\n[13/21] Testing Restricted Zone -> BLOCKED fishing decision...")
    with SessionLocal() as db:
        db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_WARN_01").delete()
        rest_zone = RestrictedZone(
            name="TEST Naval Firing Range",
            zone_type="MILITARY_EXCLUSION",
            authority="Indian Navy",
            is_active=True,
            geometry=WKTElement("POLYGON((82.0 16.5, 82.5 16.5, 82.5 17.5, 82.0 17.5, 82.0 16.5))", srid=4326),
        )
        db.add(rest_zone)
        db.commit()

    status, data_rest = request("POST", "/api/v1/agents/fishing/assess", query_payload)
    assert status == 200
    assert data_rest["overall_suitability"]["status"] == "BLOCKED"
    assert data_rest["risk_level"] == "CRITICAL"
    assert "RESTRICTED" in [e["assessment"] for e in data_rest["evidence_used"]]
    print("  [OK] Restricted zone override verified: suitability = BLOCKED, risk = CRITICAL.")

    # Clean restricted zone
    with SessionLocal() as db:
        db.query(RestrictedZone).filter(RestrictedZone.name == "TEST Naval Firing Range").delete()
        db.commit()

    # 14. Missing PFZ -> PFZ UNAVAILABLE
    print("\n[14/21] Testing missing PFZ advisory handling...")
    status, data = request("POST", "/api/v1/agents/fishing/assess", query_payload)
    assert status == 200
    assert data["pfz"]["status"] == "UNAVAILABLE"
    assert data["pfz"]["zones"] == []
    assert "UNAVAILABLE" in data["pfz"]["status"]
    print(f"  [OK] Missing PFZ handled strictly: pfz.status = '{data['pfz']['status']}' without fabricating fake zones.")

    # 15. Missing Critical Safety Data -> INSUFFICIENT_DATA
    print("\n[15/21] Testing remote/isolated location with no telemetry -> INSUFFICIENT_DATA...")
    remote_payload = {
        "latitude": -25.0,
        "longitude": 65.0,  # Remote southern Indian Ocean coordinate with no telemetry
    }
    status, data_remote = request("POST", "/api/v1/agents/fishing/assess", remote_payload)
    assert status == 200
    assert data_remote["overall_suitability"]["status"] == "INSUFFICIENT_DATA"
    assert data_remote["confidence"]["level"] == "LOW"
    assert data_remote["risk_level"] == "UNKNOWN"
    assert "INSUFFICIENT DATA" in data_remote["recommendation"]
    print("  [OK] Missing telemetry correctly yields INSUFFICIENT_DATA, risk = UNKNOWN, and LOW confidence.")

    # 16. Freshness Affects Confidence
    print("\n[16/21] Testing telemetry freshness effect on confidence...")
    assert data["confidence"]["level"] in ("HIGH", "MEDIUM")
    assert data_remote["confidence"]["level"] == "LOW"
    print(f"  [OK] Fresh telemetry confidence = {data['confidence']['level']}, Missing telemetry confidence = {data_remote['confidence']['level']}.")

    # 17. Low Confidence Does Not Claim Certainty / Guarantees
    print("\n[17/21] Verifying no prohibited safety claims ('100% safe', 'guaranteed safe', 'no risk')...")
    for resp_data in [data, data_crit, data_warn, data_remote]:
        rec = resp_data["recommendation"].lower()
        assert "100% safe" not in rec, "Found prohibited phrase '100% safe'"
        assert "guaranteed safe" not in rec, "Found prohibited phrase 'guaranteed safe'"
        assert "no risk" not in rec, "Found prohibited phrase 'no risk'"
    print("  [OK] All recommendations are strictly evidence-based; no certainty/safety guarantees found.")

    # 18. Location Comparison Endpoint
    print("\n[18/21] Testing Location Comparison via POST /api/v1/agents/fishing/compare...")
    compare_payload = {
        "location_a": {
            "name": "Kakinada Inshore",
            "latitude": 16.97,
            "longitude": 82.25,
        },
        "location_b": {
            "name": "Remote Deep Sea",
            "latitude": -25.0,
            "longitude": 65.0,
        },
        "date": "2026-09-07",
        "departure_time": "06:00",
        "vessel_type": "small_boat",
    }
    status, comp_data = request("POST", "/api/v1/agents/fishing/compare", compare_payload)
    assert status == 200, f"Expected 200, got {status}: {comp_data}"
    assert "location_a_assessment" in comp_data
    assert "location_b_assessment" in comp_data
    assert "comparison_summary" in comp_data
    assert comp_data["recommended_option"] == "location_a"
    print(f"  [OK] Location comparison executed cleanly: recommended_option = '{comp_data['recommended_option']}'.")

    # 19. What-If Departure Time Scenario
    print("\n[19/21] Testing What-If Scenario via POST /api/v1/agents/fishing/what-if...")
    what_if_payload = {
        "baseline_query": {
            "latitude": 16.97,
            "longitude": 82.25,
            "date": "2026-09-07",
            "departure_time": "06:00",
            "vessel_type": "small_boat",
        },
        "modified_departure_time": "09:00",
        "scenario_description": "What if I leave at 9 AM?",
    }
    status, whatif_data = request("POST", "/api/v1/agents/fishing/what-if", what_if_payload)
    assert status == 200, f"Expected 200, got {status}: {whatif_data}"
    assert "baseline" in whatif_data
    assert "scenario" in whatif_data
    assert "changes" in whatif_data
    assert len(whatif_data["changes"]) > 0
    assert "departure" in whatif_data["changes"][0].lower()
    print(f"  [OK] What-if evaluation returned changes: {whatif_data['changes']}, safety: {whatif_data['safety_change']}.")

    # 20. Existing API Regression Check (All Previous Layers)
    print("\n[20/21] Running full regression on all existing backend endpoints...")
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
    ]

    for meth, ep, payload, exp_status in endpoints:
        s, resp = request(meth, ep, payload)
        assert s == exp_status, f"Regression FAIL on {meth} {ep}: expected {exp_status}, got {s}: {resp}"
        print(f"  [OK] {meth} {ep} -> {s}")

    # 21. Swagger OpenAPI Registration Verification
    print("\n[21/21] Verifying Swagger OpenAPI schema registration...")
    status, openapi = request("GET", "/openapi.json")
    assert status == 200
    paths = openapi.get("paths", {})
    assert "/api/v1/agents/fishing/assess" in paths, "/api/v1/agents/fishing/assess missing in OpenAPI"
    assert "/api/v1/agents/fishing/compare" in paths, "/api/v1/agents/fishing/compare missing in OpenAPI"
    assert "/api/v1/agents/fishing/what-if" in paths, "/api/v1/agents/fishing/what-if missing in OpenAPI"

    tags = [t.get("name") for t in openapi.get("tags", [])]
    assess_tags = paths["/api/v1/agents/fishing/assess"]["post"].get("tags", [])
    assert "Fishing Intelligence Agent" in assess_tags, f"Swagger tag 'Fishing Intelligence Agent' not found in assess tags: {assess_tags}"
    print("  [OK] OpenAPI schema contains all 3 fishing agent endpoints tagged with 'Fishing Intelligence Agent'.")

    print("\n" + "=" * 75)
    print("ALL 21 VERIFICATION TESTS PASSED SUCCESSFULLY! ZERO ERRORS.")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
