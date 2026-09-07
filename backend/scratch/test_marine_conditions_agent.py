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
from models.marine import MarineObservation

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
    print("OCEANIS Marine Conditions Intelligence Agent — Verification Suite")
    print("=" * 80)

    init_db()

    # -------------------------------------------------------------------------
    # 1. Agent Import
    # -------------------------------------------------------------------------
    print("\n[1/18] Testing MarineConditionsIntelligenceAgent import...")
    try:
        from agents.marine_conditions.agent import MarineConditionsIntelligenceAgent
        agent_instance = MarineConditionsIntelligenceAgent()
        assert agent_instance is not None
        print("  [OK] MarineConditionsIntelligenceAgent imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Agent import failed: {e}")
        raise e

    # -------------------------------------------------------------------------
    # 2. Service Import
    # -------------------------------------------------------------------------
    print("\n[2/18] Testing MarineConditionsAgentService import...")
    try:
        from agents.marine_conditions.service import MarineConditionsAgentService
        service_instance = MarineConditionsAgentService()
        assert service_instance is not None
        print("  [OK] MarineConditionsAgentService imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Service import failed: {e}")
        raise e

    # -------------------------------------------------------------------------
    # 3. Collector Import
    # -------------------------------------------------------------------------
    print("\n[3/18] Testing MarineConditionsDataCollector import...")
    try:
        from agents.marine_conditions.collector import MarineConditionsDataCollector
        collector_instance = MarineConditionsDataCollector()
        assert collector_instance is not None
        print("  [OK] MarineConditionsDataCollector imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Collector import failed: {e}")
        raise e

    # -------------------------------------------------------------------------
    # 4. Reasoning Engine Import
    # -------------------------------------------------------------------------
    print("\n[4/18] Testing MarineConditionsReasoningEngine import...")
    try:
        from agents.marine_conditions.reasoning import (
            MarineConditionsReasoningEngine,
            MarineConditionsThresholds,
        )
        thresholds = MarineConditionsThresholds()
        reasoning_instance = MarineConditionsReasoningEngine(thresholds)
        assert reasoning_instance is not None
        print("  [OK] MarineConditionsReasoningEngine and Thresholds imported and instantiated successfully.")
    except Exception as e:
        print(f"  [FAIL] Reasoning engine import failed: {e}")
        raise e

    # Clean old TEST observations
    with SessionLocal() as db:
        db.query(MarineObservation).filter(MarineObservation.source.like("TEST_MC_%")).delete(synchronize_session=False)
        db.commit()

    lat_test = 19.5555
    lon_test = 86.5555
    now_utc = datetime.now(timezone.utc)

    # Insert baseline marine observation
    with SessionLocal() as db:
        obs1 = MarineObservation(
            latitude=lat_test,
            longitude=lon_test,
            wave_height_m=1.2,
            wave_direction_deg=140.0,
            wave_period_s=6.5,
            swell_wave_height_m=0.8,
            swell_wave_direction_deg=135.0,
            swell_wave_period_s=7.0,
            wind_wave_height_m=0.6,
            wind_wave_direction_deg=145.0,
            wind_wave_period_s=4.2,
            ocean_current_velocity_kmh=1.8,
            ocean_current_direction_deg=45.0,
            sea_surface_temperature_c=28.4,
            observed_at=now_utc - timedelta(minutes=15),
            source="TEST_MC_BUOY_01",
            data_type="OBSERVATION",
            quality_flag="GOOD",
        )
        db.add(obs1)
        db.commit()

    # -------------------------------------------------------------------------
    # 5. Valid Coordinate Request
    # -------------------------------------------------------------------------
    print("\n[5/18] Testing POST /api/v1/agents/marine-conditions/assess with valid coordinates...")
    req_payload = {
        "latitude": lat_test,
        "longitude": lon_test,
    }
    status, res5 = request("POST", "/api/v1/agents/marine-conditions/assess", req_payload)
    assert status == 200, f"Expected 200, got {status}: {res5}"
    assert res5["agent"] == "marine_conditions", f"Expected agent 'marine_conditions', got {res5.get('agent')}"
    assert res5["location"]["latitude"] == lat_test
    assert res5["location"]["longitude"] == lon_test
    assert res5["sea_state"] == "NORMAL"
    assert res5["risk_level"] == "LOW"
    assert res5["confidence"] >= 0.8
    assert len(res5["evidence"]) >= 4
    print(f"  [OK] Valid assessment response received: sea_state={res5['sea_state']}, risk_level={res5['risk_level']}, confidence={res5['confidence']}.")

    # -------------------------------------------------------------------------
    # 6. Invalid Latitude -> HTTP 422
    # -------------------------------------------------------------------------
    print("\n[6/18] Testing invalid latitude (-95.0, 95.0) -> HTTP 422...")
    status, err_lat = request("POST", "/api/v1/agents/marine-conditions/assess", {"latitude": 95.0, "longitude": 82.25})
    assert status == 422, f"Expected 422 for latitude=95.0, got {status}"
    status, err_lat2 = request("POST", "/api/v1/agents/marine-conditions/assess", {"latitude": -91.0, "longitude": 82.25})
    assert status == 422, f"Expected 422 for latitude=-91.0, got {status}"
    print("  [OK] Latitude boundary validation successfully rejected invalid requests with HTTP 422.")

    # -------------------------------------------------------------------------
    # 7. Invalid Longitude -> HTTP 422
    # -------------------------------------------------------------------------
    print("\n[7/18] Testing invalid longitude (-190.0, 190.0) -> HTTP 422...")
    status, err_lon = request("POST", "/api/v1/agents/marine-conditions/assess", {"latitude": 16.98, "longitude": 185.0})
    assert status == 422, f"Expected 422 for longitude=185.0, got {status}"
    status, err_lon2 = request("POST", "/api/v1/agents/marine-conditions/assess", {"latitude": 16.98, "longitude": -195.0})
    assert status == 422, f"Expected 422 for longitude=-195.0, got {status}"
    print("  [OK] Longitude boundary validation successfully rejected invalid requests with HTTP 422.")

    # -------------------------------------------------------------------------
    # 8. Marine Evidence Retrieval
    # -------------------------------------------------------------------------
    print("\n[8/18] Testing structured marine evidence retrieval and provenance fields...")
    evidence_list = res5["evidence"]
    assert len(evidence_list) > 0, "No evidence items returned"
    factors = [e["factor"] for e in evidence_list]
    assert "significant_wave_height" in factors
    assert "swell_wave_height" in factors
    assert "ocean_current_velocity" in factors
    assert "sea_surface_temperature" in factors

    sample_ev = evidence_list[0]
    assert "source" in sample_ev and sample_ev["source"] == "TEST_MC_BUOY_01"
    assert "observed_at" in sample_ev and sample_ev["observed_at"] is not None
    assert "retrieved_at" in sample_ev and sample_ev["retrieved_at"] is not None
    assert "data_type" in sample_ev and sample_ev["data_type"] == "OBSERVATION"
    assert "quality" in sample_ev and sample_ev["quality"] == "GOOD"
    assert "freshness" in sample_ev and sample_ev["freshness"] == "FRESH"
    assert "confidence" in sample_ev and 0.0 <= sample_ev["confidence"] <= 1.0
    print(f"  [OK] Evidence items validated with full provenance: factors={factors}.")

    # -------------------------------------------------------------------------
    # 9. Wave Assessment
    # -------------------------------------------------------------------------
    print("\n[9/18] Testing deterministic wave severity assessment across thresholds...")
    # Test MODERATE wave (1.8m)
    with SessionLocal() as db:
        obs_mod = MarineObservation(
            latitude=lat_test,
            longitude=lon_test,
            wave_height_m=1.8,
            observed_at=now_utc - timedelta(minutes=10),
            source="TEST_MC_MOD_WAVE",
        )
        db.add(obs_mod)
        db.commit()

    s, res_mod = request("POST", "/api/v1/agents/marine-conditions/assess", req_payload)
    assert s == 200
    assert res_mod["sea_state"] == "MODERATE"
    assert res_mod["risk_level"] == "MODERATE"

    # Test ROUGH wave (3.2m)
    with SessionLocal() as db:
        obs_rough = MarineObservation(
            latitude=lat_test,
            longitude=lon_test,
            wave_height_m=3.2,
            observed_at=now_utc - timedelta(minutes=5),
            source="TEST_MC_ROUGH_WAVE",
        )
        db.add(obs_rough)
        db.commit()

    s, res_rough = request("POST", "/api/v1/agents/marine-conditions/assess", req_payload)
    assert s == 200
    assert res_rough["sea_state"] == "ROUGH"
    assert res_rough["risk_level"] == "HIGH"
    assert any("Rough sea state" in w for w in res_rough["warnings"])
    print("  [OK] Wave severity thresholds (NORMAL -> MODERATE -> ROUGH) evaluated accurately.")

    # -------------------------------------------------------------------------
    # 10. Swell Assessment & Long-Period Warning
    # -------------------------------------------------------------------------
    print("\n[10/18] Testing swell height and long-period swell shoaling warnings...")
    with SessionLocal() as db:
        obs_swell = MarineObservation(
            latitude=lat_test,
            longitude=lon_test,
            wave_height_m=1.0,
            swell_wave_height_m=2.8,
            swell_wave_period_s=14.0,  # Long period (> 12s)
            observed_at=now_utc - timedelta(minutes=2),
            source="TEST_MC_SWELL",
        )
        db.add(obs_swell)
        db.commit()

    s, res_swell = request("POST", "/api/v1/agents/marine-conditions/assess", req_payload)
    assert s == 200
    assert res_swell["sea_state"] == "ROUGH"  # Swell 2.8m is ROUGH
    assert any("Heavy swell" in w for w in res_swell["warnings"])
    assert any("Long-period swell" in w for w in res_swell["warnings"])
    print("  [OK] Swell height and long-period swell (14.0s) shoaling warning verified.")

    # -------------------------------------------------------------------------
    # 11. Current Assessment
    # -------------------------------------------------------------------------
    print("\n[11/18] Testing ocean current velocity assessment...")
    with SessionLocal() as db:
        obs_curr = MarineObservation(
            latitude=lat_test,
            longitude=lon_test,
            wave_height_m=1.0,
            swell_wave_height_m=0.8,
            ocean_current_velocity_kmh=6.2,  # Strong current (> 5.0 km/h)
            observed_at=now_utc - timedelta(minutes=1),
            source="TEST_MC_CURRENT",
        )
        db.add(obs_curr)
        db.commit()

    s, res_curr = request("POST", "/api/v1/agents/marine-conditions/assess", req_payload)
    assert s == 200
    assert res_curr["sea_state"] == "ROUGH"
    assert any("Strong current" in w for w in res_curr["warnings"])
    print("  [OK] Ocean current velocity evaluated with strong drift warning.")

    # -------------------------------------------------------------------------
    # 12. Sea Surface Temperature (SST) Retrieval
    # -------------------------------------------------------------------------
    print("\n[12/18] Testing Sea Surface Temperature (SST) telemetry...")
    assert "sea_surface_temperature_c" in res5["conditions"]
    assert res5["conditions"]["sea_surface_temperature_c"] == 28.4
    sst_ev = [e for e in res5["evidence"] if e["factor"] == "sea_surface_temperature"]
    assert len(sst_ev) == 1
    assert sst_ev[0]["unit"] == "°C"
    assert sst_ev[0]["value"] == 28.4
    print("  [OK] SST factor extracted with unit °C and contextual notes.")

    # -------------------------------------------------------------------------
    # 13. Freshness Evaluation
    # -------------------------------------------------------------------------
    print("\n[13/18] Testing telemetry freshness categorization (FRESH, AGING, STALE)...")
    # Fresh observation (< 6 hours) -> FRESH
    with SessionLocal() as db:
        db.query(MarineObservation).filter(MarineObservation.source.like("TEST_MC_%")).delete()
        obs_fresh = MarineObservation(
            latitude=lat_test,
            longitude=lon_test,
            wave_height_m=1.0,
            observed_at=now_utc - timedelta(minutes=30),
            source="TEST_MC_FRESH",
            quality_flag="GOOD",
        )
        db.add(obs_fresh)
        db.commit()

    s, res_fresh = request("POST", "/api/v1/agents/marine-conditions/assess", req_payload)
    assert res_fresh["data_freshness"] == "FRESH"
    assert res_fresh["confidence"] == 0.95

    # Aging observation (12 hours old, > 6.0h & <= 24.0h) -> AGING
    with SessionLocal() as db:
        db.query(MarineObservation).filter(MarineObservation.source.like("TEST_MC_%")).delete()
        obs_aging = MarineObservation(
            latitude=lat_test,
            longitude=lon_test,
            wave_height_m=1.0,
            observed_at=now_utc - timedelta(hours=12),
            source="TEST_MC_AGING",
            quality_flag="GOOD",
        )
        db.add(obs_aging)
        db.commit()

    s, res_aging = request("POST", "/api/v1/agents/marine-conditions/assess", req_payload)
    assert res_aging["data_freshness"] == "AGING"
    assert res_aging["confidence"] == 0.75

    # Stale observation (36 hours old, > 24.0h & <= 72.0h) -> STALE
    with SessionLocal() as db:
        db.query(MarineObservation).filter(MarineObservation.source.like("TEST_MC_%")).delete()
        obs_stale = MarineObservation(
            latitude=lat_test,
            longitude=lon_test,
            wave_height_m=1.0,
            observed_at=now_utc - timedelta(hours=36),
            source="TEST_MC_STALE",
            quality_flag="GOOD",
        )
        db.add(obs_stale)
        db.commit()

    s, res_stale = request("POST", "/api/v1/agents/marine-conditions/assess", req_payload)
    assert res_stale["data_freshness"] == "STALE"
    assert res_stale["confidence"] == 0.35
    print("  [OK] Freshness categories (FRESH=0.95, AGING=0.75, STALE=0.35) evaluated deterministically.")

    # -------------------------------------------------------------------------
    # 14. Confidence Calculation
    # -------------------------------------------------------------------------
    print("\n[14/18] Testing deterministic confidence calculation (0.0 to 1.0)...")
    for r in [res5, res_mod, res_rough, res_swell, res_curr, res_fresh, res_aging, res_stale]:
        conf = r["confidence"]
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of bounds"
    print("  [OK] Confidence strictly bounded within [0.0, 1.0].")

    # -------------------------------------------------------------------------
    # 15. Insufficient Data Handling
    # -------------------------------------------------------------------------
    print("\n[15/18] Testing remote coordinate without data -> INSUFFICIENT_DATA & confidence 0.0...")
    remote_payload = {
        "latitude": -45.0,
        "longitude": 75.0,
    }
    s, res_empty = request("POST", "/api/v1/agents/marine-conditions/assess", remote_payload)
    assert s == 200
    assert res_empty["sea_state"] == "INSUFFICIENT_DATA"
    assert res_empty["risk_level"] == "UNKNOWN"
    assert res_empty["confidence"] == 0.0
    assert "INSUFFICIENT DATA" in res_empty["recommendation"].upper()
    print("  [OK] Missing telemetry correctly returns INSUFFICIENT_DATA, confidence=0.0.")

    # -------------------------------------------------------------------------
    # 16. Severe Sea-State Handling
    # -------------------------------------------------------------------------
    print("\n[16/18] Testing severe sea state (wave >= 4.0m) -> SEVERE & CRITICAL...")
    with SessionLocal() as db:
        obs_severe = MarineObservation(
            latitude=lat_test,
            longitude=lon_test,
            wave_height_m=4.8,
            swell_wave_height_m=4.2,
            ocean_current_velocity_kmh=4.5,
            observed_at=now_utc - timedelta(minutes=5),
            source="TEST_MC_SEVERE",
        )
        db.add(obs_severe)
        db.commit()

    s, res_sev = request("POST", "/api/v1/agents/marine-conditions/assess", req_payload)
    assert s == 200
    assert res_sev["sea_state"] == "SEVERE"
    assert res_sev["risk_level"] == "CRITICAL"
    assert any("HAZARDOUS SEA STATE" in w for w in res_sev["warnings"])
    assert "SEVERE" in res_sev["recommendation"].upper()
    print("  [OK] Severe wave dynamics (4.8m) triggered SEVERE sea state and CRITICAL risk.")

    # -------------------------------------------------------------------------
    # 17. No Misleading Safety Guarantees
    # -------------------------------------------------------------------------
    print("\n[17/18] Verifying prohibition of misleading safety guarantees in narrative...")
    responses_to_check = [res5, res_mod, res_rough, res_swell, res_curr, res_fresh, res_aging, res_stale, res_empty, res_sev]
    for r in responses_to_check:
        rec = (r.get("recommendation", "") + " " + r.get("explanation", "")).lower()
        assert "100% safe" not in rec, "Prohibited phrase '100% safe' detected"
        assert "guaranteed safe" not in rec, "Prohibited phrase 'guaranteed safe' detected"
        assert "completely safe" not in rec, "Prohibited phrase 'completely safe' detected"
        assert "no risk" not in rec, "Prohibited phrase 'no risk' detected"
    print("  [OK] All recommendations and explanations strictly respect safety communication rules.")

    # -------------------------------------------------------------------------
    # 18. API / OpenAPI Registration
    # -------------------------------------------------------------------------
    print("\n[18/18] Verifying OpenAPI registration for Marine Conditions Agent...")
    s, openapi = request("GET", "/openapi.json")
    assert s == 200
    paths = openapi.get("paths", {})
    assert "/api/v1/agents/marine-conditions/assess" in paths, "Missing POST /api/v1/agents/marine-conditions/assess in OpenAPI"
    mc_tags = paths["/api/v1/agents/marine-conditions/assess"]["post"].get("tags", [])
    assert "Marine Conditions Intelligence Agent" in mc_tags, f"Tag missing in OpenAPI: {mc_tags}"
    print("  [OK] Endpoint POST /api/v1/agents/marine-conditions/assess registered with tag 'Marine Conditions Intelligence Agent'.")

    # Clean up test observations
    with SessionLocal() as db:
        db.query(MarineObservation).filter(MarineObservation.source.like("TEST_MC_%")).delete()
        db.commit()

    # -------------------------------------------------------------------------
    # Regression: Fishing Intelligence Agent
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("RUNNING FISHING INTELLIGENCE AGENT REGRESSION (21 TESTS)...")
    print("=" * 80)
    from scratch.test_fishing_agent import run_tests as run_fishing_regression
    run_fishing_regression()
    print("  [OK] All 21 Fishing Intelligence Agent regression tests passed.")

    # -------------------------------------------------------------------------
    # Regression: Full Backend Endpoints
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
    ]

    for meth, ep, payload, exp_status in endpoints:
        s, resp = request(meth, ep, payload)
        assert s == exp_status, f"Regression FAIL on {meth} {ep}: expected {exp_status}, got {s}: {resp}"
        print(f"  [OK] {meth} {ep} -> {s}")

    print("\n" + "=" * 80)
    print("ALL 18 MARINE CONDITIONS AGENT TESTS & FULL REGRESSION SUITES PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
