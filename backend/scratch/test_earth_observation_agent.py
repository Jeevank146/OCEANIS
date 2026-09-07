import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database import SessionLocal, engine, init_db
from models.earth_observation import EarthObservation

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
    print("OCEANIS Earth Observation Intelligence Agent — Verification Suite")
    print("=" * 80)

    init_db()

    # -------------------------------------------------------------------------
    # 1. Agent Import
    # -------------------------------------------------------------------------
    print("\n[1/20] Testing EarthObservationIntelligenceAgent import...")
    try:
        from agents.earth_observation.agent import EarthObservationIntelligenceAgent
        agent_instance = EarthObservationIntelligenceAgent()
        assert agent_instance is not None
        print("  [OK] EarthObservationIntelligenceAgent imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Agent import failed: {e}")
        raise e

    # -------------------------------------------------------------------------
    # 2. Service Import
    # -------------------------------------------------------------------------
    print("\n[2/20] Testing EarthObservationAgentService import...")
    try:
        from agents.earth_observation.service import EarthObservationAgentService
        service_instance = EarthObservationAgentService()
        assert service_instance is not None
        print("  [OK] EarthObservationAgentService imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Service import failed: {e}")
        raise e

    # -------------------------------------------------------------------------
    # 3. Collector Import
    # -------------------------------------------------------------------------
    print("\n[3/20] Testing EarthObservationDataCollector import...")
    try:
        from agents.earth_observation.collector import EarthObservationDataCollector
        collector_instance = EarthObservationDataCollector()
        assert collector_instance is not None
        print("  [OK] EarthObservationDataCollector imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Collector import failed: {e}")
        raise e

    # -------------------------------------------------------------------------
    # 4. Reasoning Engine Import
    # -------------------------------------------------------------------------
    print("\n[4/20] Testing EarthObservationReasoningEngine & Thresholds import...")
    try:
        from agents.earth_observation.reasoning import (
            EarthObservationReasoningEngine,
            EarthObservationThresholds,
        )
        thresholds = EarthObservationThresholds()
        reasoning_instance = EarthObservationReasoningEngine(thresholds)
        assert reasoning_instance is not None
        print("  [OK] EarthObservationReasoningEngine and Thresholds imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Reasoning engine import failed: {e}")
        raise e

    # Dedicated isolated coordinates for EO tests
    lat_test = 18.2222
    lon_test = 84.4444
    now_utc = datetime.now(timezone.utc)

    # Clean old TEST EO records
    with SessionLocal() as db:
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_EO_%")).delete(synchronize_session=False)
        db.commit()

    # Insert baseline EO satellite observation
    with SessionLocal() as db:
        eo1 = EarthObservation(
            latitude=lat_test,
            longitude=lon_test,
            observed_at=now_utc - timedelta(minutes=45),
            retrieved_at=now_utc - timedelta(minutes=10),
            source="TEST_EO_COPERNICUS_S3",
            product_type="CHL_AND_SST_L3",
            satellite_platform="Sentinel-3B",
            sensor_instrument="OLCI/SLSTR",
            sea_surface_temperature_c=28.6,
            chlorophyll_a_mg_m3=1.45,
            ocean_colour="Light Green-Blue",
            cloud_cover_percent=12.5,
            solar_radiation_w_m2=580.0,
            data_type="OBSERVATION",
            quality_flag="OPERATIONAL_QUALITY",
        )
        db.add(eo1)
        db.commit()

    # -------------------------------------------------------------------------
    # 5. Valid Coordinates Assessment
    # -------------------------------------------------------------------------
    print("\n[5/20] Testing POST /api/v1/agents/earth-observation/assess with valid coordinates...")
    req_payload = {
        "latitude": lat_test,
        "longitude": lon_test,
    }
    status, res5 = request("POST", "/api/v1/agents/earth-observation/assess", req_payload)
    assert status == 200, f"Expected 200, got {status}: {res5}"
    assert res5["agent"] == "earth_observation", f"Expected agent 'earth_observation', got {res5.get('agent')}"
    assert res5["location"]["latitude"] == lat_test
    assert res5["location"]["longitude"] == lon_test
    assert res5["data_freshness"] == "FRESH"
    assert res5["confidence"] >= 0.8
    assert res5["indicators"]["chlorophyll_status"] == "FAVORABLE_INDICATOR"
    assert res5["indicators"]["chlorophyll_gradient_detected"] is True
    print(f"  [OK] Valid assessment received: chl_status={res5['indicators']['chlorophyll_status']}, confidence={res5['confidence']}.")

    # -------------------------------------------------------------------------
    # 6. Invalid Latitude -> HTTP 422
    # -------------------------------------------------------------------------
    print("\n[6/20] Testing invalid latitude (-95.0, 95.0) -> HTTP 422...")
    status, err_lat = request("POST", "/api/v1/agents/earth-observation/assess", {"latitude": 95.0, "longitude": 84.44})
    assert status == 422, f"Expected 422 for latitude=95.0, got {status}"
    status, err_lat2 = request("POST", "/api/v1/agents/earth-observation/assess", {"latitude": -91.0, "longitude": 84.44})
    assert status == 422, f"Expected 422 for latitude=-91.0, got {status}"
    print("  [OK] Invalid latitude correctly rejected with HTTP 422 Unprocessable Entity.")

    # -------------------------------------------------------------------------
    # 7. Invalid Longitude -> HTTP 422
    # -------------------------------------------------------------------------
    print("\n[7/20] Testing invalid longitude (-190.0, 190.0) -> HTTP 422...")
    status, err_lon = request("POST", "/api/v1/agents/earth-observation/assess", {"latitude": 18.22, "longitude": 185.0})
    assert status == 422, f"Expected 422 for longitude=185.0, got {status}"
    status, err_lon2 = request("POST", "/api/v1/agents/earth-observation/assess", {"latitude": 18.22, "longitude": -195.0})
    assert status == 422, f"Expected 422 for longitude=-195.0, got {status}"
    print("  [OK] Invalid longitude correctly rejected with HTTP 422 Unprocessable Entity.")

    # -------------------------------------------------------------------------
    # 8. SST Evidence Retrieval
    # -------------------------------------------------------------------------
    print("\n[8/20] Testing Sea Surface Temperature (SST) evidence retrieval & provenance...")
    sst_ev = [e for e in res5["evidence"] if e["factor"] == "sea_surface_temperature"]
    assert len(sst_ev) == 1, "Missing SST evidence item"
    assert sst_ev[0]["value"] == 28.6
    assert sst_ev[0]["unit"] == "°C"
    assert sst_ev[0]["source"] == "TEST_EO_COPERNICUS_S3"
    assert sst_ev[0]["satellite_platform"] == "Sentinel-3B"
    assert sst_ev[0]["sensor_instrument"] == "OLCI/SLSTR"
    assert sst_ev[0]["observed_at"] is not None
    print(f"  [OK] SST evidence validated: {sst_ev[0]['value']}{sst_ev[0]['unit']} from {sst_ev[0]['satellite_platform']}.")

    # -------------------------------------------------------------------------
    # 9. Chlorophyll Evidence Retrieval
    # -------------------------------------------------------------------------
    print("\n[9/20] Testing Chlorophyll-a evidence retrieval & bio-optical classification...")
    chl_ev = [e for e in res5["evidence"] if e["factor"] == "chlorophyll_a"]
    assert len(chl_ev) == 1, "Missing chlorophyll_a evidence item"
    assert chl_ev[0]["value"] == 1.45
    assert chl_ev[0]["unit"] == "mg/m³"
    assert chl_ev[0]["severity"] == "FAVORABLE_INDICATOR"
    assert "primary biological productivity" in chl_ev[0]["notes"]
    print(f"  [OK] Chlorophyll-a evidence validated: {chl_ev[0]['value']}{chl_ev[0]['unit']} ({chl_ev[0]['severity']}).")

    # -------------------------------------------------------------------------
    # 10. Ocean Colour Evidence Retrieval
    # -------------------------------------------------------------------------
    print("\n[10/20] Testing Ocean Colour classification and optical evidence...")
    col_ev = [e for e in res5["evidence"] if e["factor"] == "ocean_colour"]
    assert len(col_ev) == 1, "Missing ocean_colour evidence item"
    assert col_ev[0]["value"] == "Light Green-Blue"
    assert res5["indicators"]["ocean_colour_status"] == "MESOTROPHIC"
    print(f"  [OK] Ocean colour classified: '{col_ev[0]['value']}' -> status '{res5['indicators']['ocean_colour_status']}'.")

    # -------------------------------------------------------------------------
    # 11. Cloud Cover Evidence & Impact
    # -------------------------------------------------------------------------
    print("\n[11/20] Testing Cloud Cover evidence and optical quality degradation under high cloud cover...")
    # Clean and insert high cloud observation (> 60%)
    with SessionLocal() as db:
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_EO_%")).delete()
        eo_cloudy = EarthObservation(
            latitude=lat_test,
            longitude=lon_test,
            observed_at=now_utc - timedelta(minutes=20),
            retrieved_at=now_utc - timedelta(minutes=5),
            source="TEST_EO_CLOUDY",
            product_type="OPTICAL_L2",
            satellite_platform="MODIS-Aqua",
            sea_surface_temperature_c=28.2,
            chlorophyll_a_mg_m3=1.10,
            ocean_colour="Chlorophyll Green",
            cloud_cover_percent=78.0,  # Heavy cloud cover
            data_type="OBSERVATION",
            quality_flag="OPERATIONAL_QUALITY",
        )
        db.add(eo_cloudy)
        db.commit()

    s, res_cloudy = request("POST", "/api/v1/agents/earth-observation/assess", req_payload)
    assert s == 200
    assert res_cloudy["indicators"]["optical_observability"] == "CLOUD_OBSCURED"
    assert res_cloudy["observation_quality"] == "LOW_QUALITY"
    assert any("Heavy cloud cover" in w for w in res_cloudy["warnings"])
    print(f"  [OK] Cloud cover (78%) correctly triggered CLOUD_OBSCURED and LOW_QUALITY optical state.")

    # -------------------------------------------------------------------------
    # 12. Observation Freshness
    # -------------------------------------------------------------------------
    print("\n[12/20] Testing satellite telemetry freshness categorization (FRESH, AGING, STALE)...")
    # Fresh observation (< 6 hours) -> FRESH
    with SessionLocal() as db:
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_EO_%")).delete()
        eo_fresh = EarthObservation(
            latitude=lat_test,
            longitude=lon_test,
            observed_at=now_utc - timedelta(minutes=30),
            retrieved_at=now_utc - timedelta(minutes=5),
            source="TEST_EO_FRESH",
            product_type="SST_AND_OPTICAL",
            sea_surface_temperature_c=28.0,
            chlorophyll_a_mg_m3=0.8,
            cloud_cover_percent=10.0,
        )
        db.add(eo_fresh)
        db.commit()

    s, res_fresh = request("POST", "/api/v1/agents/earth-observation/assess", req_payload)
    assert res_fresh["data_freshness"] == "FRESH"
    assert res_fresh["confidence"] == 0.95

    # Aging observation (12 hours old) -> AGING
    with SessionLocal() as db:
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_EO_%")).delete()
        eo_aging = EarthObservation(
            latitude=lat_test,
            longitude=lon_test,
            observed_at=now_utc - timedelta(hours=12),
            retrieved_at=now_utc - timedelta(hours=12),
            source="TEST_EO_AGING",
            product_type="SST_AND_OPTICAL",
            sea_surface_temperature_c=28.0,
            chlorophyll_a_mg_m3=0.8,
            cloud_cover_percent=10.0,
        )
        db.add(eo_aging)
        db.commit()

    s, res_aging = request("POST", "/api/v1/agents/earth-observation/assess", req_payload)
    assert res_aging["data_freshness"] == "AGING"
    assert res_aging["confidence"] == 0.75

    # Stale observation (36 hours old) -> STALE
    with SessionLocal() as db:
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_EO_%")).delete()
        eo_stale = EarthObservation(
            latitude=lat_test,
            longitude=lon_test,
            observed_at=now_utc - timedelta(hours=36),
            retrieved_at=now_utc - timedelta(hours=36),
            source="TEST_EO_STALE",
            product_type="SST_AND_OPTICAL",
            sea_surface_temperature_c=28.0,
            chlorophyll_a_mg_m3=0.8,
            cloud_cover_percent=10.0,
        )
        db.add(eo_stale)
        db.commit()

    s, res_stale = request("POST", "/api/v1/agents/earth-observation/assess", req_payload)
    assert res_stale["data_freshness"] == "STALE"
    assert res_stale["confidence"] == 0.35
    print("  [OK] Freshness categories evaluated deterministically (FRESH=0.95, AGING=0.75, STALE=0.35).")

    # -------------------------------------------------------------------------
    # 13. Observation Quality
    # -------------------------------------------------------------------------
    print("\n[13/20] Testing observation quality flags and degraded sensor flags...")
    with SessionLocal() as db:
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_EO_%")).delete()
        eo_qual = EarthObservation(
            latitude=lat_test,
            longitude=lon_test,
            observed_at=now_utc - timedelta(minutes=15),
            retrieved_at=now_utc - timedelta(minutes=5),
            source="TEST_EO_SUSPECT",
            product_type="SST_AND_OPTICAL",
            sea_surface_temperature_c=27.5,
            quality_flag="SUSPECT",
            cloud_cover_percent=10.0,
        )
        db.add(eo_qual)
        db.commit()

    s, res_qual = request("POST", "/api/v1/agents/earth-observation/assess", req_payload)
    assert s == 200
    assert res_qual["observation_quality"] == "SUSPECT"
    assert res_qual["confidence"] <= 0.75  # 0.95 - 0.2 = 0.75
    print("  [OK] SUSPECT quality flag correctly adjusted confidence rating.")

    # -------------------------------------------------------------------------
    # 14. Confidence Calculation
    # -------------------------------------------------------------------------
    print("\n[14/20] Testing confidence calculation strictly bounded in [0.0, 1.0]...")
    for r in [res5, res_cloudy, res_fresh, res_aging, res_stale, res_qual]:
        conf = r["confidence"]
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of bounds"
    print("  [OK] Confidence strictly bounded within [0.0, 1.0].")

    # -------------------------------------------------------------------------
    # 15. Temporal Comparison When Historical Data Exists
    # -------------------------------------------------------------------------
    print("\n[15/20] Testing temporal comparison across sequential satellite passes...")
    with SessionLocal() as db:
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_EO_%")).delete()
        # Pass 1: 12 hours ago (Historical)
        pass1 = EarthObservation(
            latitude=lat_test,
            longitude=lon_test,
            observed_at=now_utc - timedelta(hours=12),
            retrieved_at=now_utc - timedelta(hours=12),
            source="TEST_EO_PASS_1",
            product_type="SST_AND_OPTICAL",
            sea_surface_temperature_c=27.2,
            chlorophyll_a_mg_m3=0.85,
            cloud_cover_percent=40.0,
        )
        # Pass 2: 1 hour ago (Current)
        pass2 = EarthObservation(
            latitude=lat_test,
            longitude=lon_test,
            observed_at=now_utc - timedelta(hours=1),
            retrieved_at=now_utc - timedelta(hours=1),
            source="TEST_EO_PASS_2",
            product_type="SST_AND_OPTICAL",
            sea_surface_temperature_c=28.4,  # +1.2°C -> WARMING
            chlorophyll_a_mg_m3=1.35,        # +0.50 mg/m³ -> INCREASING
            cloud_cover_percent=15.0,        # -25.0% -> DECREASING
        )
        db.add_all([pass1, pass2])
        db.commit()

    s, res_temporal = request("POST", "/api/v1/agents/earth-observation/assess", req_payload)
    assert s == 200
    temp_comp = res_temporal["temporal_comparison"]
    assert temp_comp is not None
    assert temp_comp["has_historical_data"] is True
    assert temp_comp["status"] == "AVAILABLE"
    assert temp_comp["sst_change_c"] == 1.2
    assert temp_comp["sst_trend"] == "WARMING"
    assert temp_comp["chlorophyll_change_mg_m3"] == 0.5
    assert temp_comp["chlorophyll_trend"] == "INCREASING"
    assert temp_comp["cloud_cover_change_percent"] == -25.0
    assert temp_comp["cloud_cover_trend"] == "DECREASING"
    assert temp_comp["time_delta_hours"] == 11.0
    assert "SST: WARMING" in temp_comp["summary"]
    print(f"  [OK] Temporal comparison verified: SST (+1.2°C, WARMING), Chl (+0.5 mg/m³, INCREASING), Cloud (-25%, DECREASING).")

    # -------------------------------------------------------------------------
    # 16. Missing Historical Data Handling
    # -------------------------------------------------------------------------
    print("\n[16/20] Testing single satellite observation without historical prior pass...")
    with SessionLocal() as db:
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_EO_%")).delete()
        single_pass = EarthObservation(
            latitude=lat_test,
            longitude=lon_test,
            observed_at=now_utc - timedelta(hours=1),
            retrieved_at=now_utc - timedelta(hours=1),
            source="TEST_EO_SINGLE",
            product_type="SST_AND_OPTICAL",
            sea_surface_temperature_c=28.0,
            chlorophyll_a_mg_m3=0.9,
            cloud_cover_percent=10.0,
        )
        db.add(single_pass)
        db.commit()

    s, res_single = request("POST", "/api/v1/agents/earth-observation/assess", req_payload)
    assert s == 200
    assert res_single["temporal_comparison"]["has_historical_data"] is False
    assert res_single["temporal_comparison"]["status"] == "INSUFFICIENT_DATA"
    assert "INSUFFICIENT_DATA" in res_single["temporal_comparison"]["summary"]
    print("  [OK] Missing historical satellite passes correctly yield temporal status INSUFFICIENT_DATA.")

    # -------------------------------------------------------------------------
    # 17. Stale EO Data Handling
    # -------------------------------------------------------------------------
    print("\n[17/20] Testing stale satellite telemetry (> 24 hours) handling...")
    assert res_stale["data_freshness"] == "STALE"
    assert res_stale["confidence"] == 0.35
    print("  [OK] Stale EO data correctly tagged with STALE freshness and degraded confidence.")

    # -------------------------------------------------------------------------
    # 18. Insufficient Data Handling (No Data in Remote Location)
    # -------------------------------------------------------------------------
    print("\n[18/20] Testing remote coordinates with no satellite records -> INSUFFICIENT_DATA...")
    remote_payload = {
        "latitude": -55.0,
        "longitude": 110.0,
    }
    s, res_empty = request("POST", "/api/v1/agents/earth-observation/assess", remote_payload)
    assert s == 200
    assert res_empty["observation_quality"] == "UNKNOWN"
    assert res_empty["data_freshness"] == "UNKNOWN"
    assert res_empty["confidence"] == 0.0
    assert res_empty["temporal_comparison"]["status"] == "INSUFFICIENT_DATA"
    assert "INSUFFICIENT DATA" in res_empty["recommendation"].upper()
    print("  [OK] Complete lack of telemetry correctly returns INSUFFICIENT_DATA with confidence=0.0.")

    # -------------------------------------------------------------------------
    # 19. No Misleading Fishing or Safety Guarantees
    # -------------------------------------------------------------------------
    print("\n[19/20] Verifying prohibition of guaranteed fish presence and safety claims...")
    all_responses = [res5, res_cloudy, res_fresh, res_aging, res_stale, res_qual, res_temporal, res_single, res_empty]
    for r in all_responses:
        rec = (r.get("recommendation", "") + " " + r.get("explanation", "")).lower()
        assert "fish definitely exist here" not in rec, "Prohibited phrase 'fish definitely exist here' detected"
        assert "guaranteed fishing zone" not in rec, "Prohibited phrase 'guaranteed fishing zone' detected"
        assert "100% safe" not in rec, "Prohibited phrase '100% safe' detected"
        assert "guaranteed safe" not in rec, "Prohibited phrase 'guaranteed safe' detected"
        assert "completely safe" not in rec, "Prohibited phrase 'completely safe' detected"
        assert "no risk" not in rec, "Prohibited phrase 'no risk' detected"
    print("  [OK] All recommendations strictly adhere to evidence-based ecological reporting without guarantees.")

    # -------------------------------------------------------------------------
    # 20. OpenAPI / Swagger Registration
    # -------------------------------------------------------------------------
    print("\n[20/20] Verifying OpenAPI registration for Earth Observation Agent...")
    s, openapi = request("GET", "/openapi.json")
    assert s == 200
    paths = openapi.get("paths", {})
    assert "/api/v1/agents/earth-observation/assess" in paths, "Missing POST /api/v1/agents/earth-observation/assess in OpenAPI"
    eo_tags = paths["/api/v1/agents/earth-observation/assess"]["post"].get("tags", [])
    assert "Earth Observation" in eo_tags, f"Tag 'Earth Observation' missing: {eo_tags}"
    print("  [OK] Endpoint POST /api/v1/agents/earth-observation/assess registered with tag 'Earth Observation'.")

    # Clean up test observations
    with SessionLocal() as db:
        db.query(EarthObservation).filter(EarthObservation.source.like("TEST_EO_%")).delete()
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
    # Regression: Full Backend Endpoints (18 Endpoints)
    # -------------------------------------------------------------------------
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
    ]

    for meth, ep, payload, exp_status in endpoints:
        s, resp = request(meth, ep, payload)
        assert s == exp_status, f"Regression FAIL on {meth} {ep}: expected {exp_status}, got {s}: {resp}"
        print(f"  [OK] {meth} {ep} -> {s}")

    print("\n" + "=" * 80)
    print("ALL 20 EARTH OBSERVATION AGENT TESTS & FULL REGRESSION SUITES PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
