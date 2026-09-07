from datetime import datetime, timedelta, timezone
import json
import os
import sys
import urllib.error
import urllib.request

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from geoalchemy2.elements import WKTElement
from sqlalchemy import func

from conversation.context import ConversationContextManager
from conversation.language import LanguageDetector
from conversation.llm_client import DeterministicRuleLLMClient, LLMClientFactory
from conversation.query_parser import ConversationalQueryParser
from conversation.response_generator import ConversationalResponseGenerator
from conversation.schemas import ConversationQuery
from conversation.service import ConversationService
from database import SessionLocal
from models.disaster import HazardZone, MarineAlert
from models.geospatial import RestrictedZone
from orchestrator.service import OrchestratorService

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


def test_conversational_intelligence():
    print("=" * 80)
    print("OCEANIS Conversational Intelligence & LLM Layer -- Verification Suite")
    print("=" * 80)

    # 1. English query parsing
    print("\n[1/23] Testing English query parsing: 'Can I go fishing tomorrow at 6 AM from Kakinada?'...")
    status, res_en = request("POST", "/api/v1/conversation/query", {
        "message": "Can I go fishing tomorrow at 6 AM from Kakinada?",
    })
    assert status == 200, f"Expected 200, got {status}: {res_en}"
    assert res_en["language"] == "en"
    assert res_en["input_mode"] == "standard"
    assert res_en["parsed_query"]["intent"] == "FISHING_ASSESSMENT"
    assert res_en["parsed_query"]["location"]["name"] == "Kakinada Port"
    assert res_en["parsed_query"]["target_time"] == "06:00"
    print(f"  [OK] English parsed: intent={res_en['parsed_query']['intent']}, loc={res_en['parsed_query']['location']['name']}, time={res_en['parsed_query']['target_time']}.")

    # 2. Telugu transliteration parsing
    print("\n[2/23] Testing Telugu transliteration parsing: 'Repu morning 6 ki Kakinada nunchi fishing ki vellacha?'...")
    status, res_te_trans = request("POST", "/api/v1/conversation/query", {
        "message": "Repu morning 6 ki Kakinada nunchi fishing ki vellacha?",
    })
    assert status == 200
    assert res_te_trans["language"] == "te"
    assert res_te_trans["input_mode"] == "transliterated"
    assert res_te_trans["parsed_query"]["intent"] == "FISHING_ASSESSMENT"
    assert res_te_trans["parsed_query"]["location"]["name"] == "Kakinada Port"
    assert res_te_trans["parsed_query"]["target_time"] == "06:00"
    print(f"  [OK] Telugu transliteration detected: lang={res_te_trans['language']}, mode={res_te_trans['input_mode']}, loc={res_te_trans['parsed_query']['location']['name']}.")

    # 3. Telugu Unicode query parsing
    print("\n[3/23] Testing Telugu Unicode parsing (native Telugu script)...")
    status, res_te_uni = request("POST", "/api/v1/conversation/query", {
        "message": "రేపు ఉదయం 6 గంటలకు కాకినాడ నుంచి fishing కి వెళ్లవచ్చా?",
    })
    assert status == 200
    assert res_te_uni["language"] == "te"
    assert res_te_uni["input_mode"] == "standard"
    assert res_te_uni["parsed_query"]["intent"] == "FISHING_ASSESSMENT"
    assert res_te_uni["parsed_query"]["location"]["name"] == "Kakinada Port"
    print(f"  [OK] Telugu Unicode script parsed: lang={res_te_uni['language']}, mode={res_te_uni['input_mode']}.")

    # 4. Hindi query handling
    print("\n[4/23] Testing Hindi query parsing (Devanagari script)...")
    status, res_hi = request("POST", "/api/v1/conversation/query", {
        "message": "क्या कल सुबह काकीनाडा से मछली पकड़ने जा सकते हैं?",
    })
    assert status == 200
    assert res_hi["language"] == "hi"
    assert res_hi["parsed_query"]["intent"] == "FISHING_ASSESSMENT"
    assert res_hi["parsed_query"]["location"]["name"] == "Kakinada Port"
    print(f"  [OK] Hindi query parsed: lang={res_hi['language']}, intent={res_hi['parsed_query']['intent']}.")

    # 5. Fishing assessment conversational flow
    print("\n[5/23] Testing fishing assessment conversational response...")
    assert res_en["safety_status"] in ("CLEAR", "CAUTION", "FAVORABLE", "WARNING", "BLOCKED")
    assert len(res_en["response"]) > 20
    assert len(res_en["evidence"]) > 0
    print(f"  [OK] Fishing response generated: safety={res_en['safety_status']}, risk={res_en['risk_level']}, response_length={len(res_en['response'])} chars.")

    # 6. Fishing comparison conversation
    print("\n[6/23] Testing fishing comparison: 'Which is better for fishing tomorrow morning, Kakinada or Vizag?'...")
    status, res_comp = request("POST", "/api/v1/conversation/query", {
        "message": "Which is better for fishing tomorrow morning, Kakinada or Vizag?",
    })
    assert status == 200
    assert res_comp["parsed_query"]["intent"] == "FISHING_COMPARISON"
    assert res_comp["parsed_query"]["is_comparison"] is True
    assert len(res_comp["parsed_query"]["comparison_locations"]) >= 2
    assert res_comp["orchestration"]["comparison_results"] is not None
    print(f"  [OK] Comparative query processed: compared {len(res_comp['parsed_query']['comparison_locations'])} locations.")

    # 7. Route operation conversation
    print("\n[7/23] Testing route operations: 'Is it safe to travel from Kakinada Port to Visakhapatnam Port?'...")
    status, res_route = request("POST", "/api/v1/conversation/query", {
        "message": "Is it safe to travel from Kakinada Port to Visakhapatnam Port?",
    })
    assert status == 200
    assert res_route["parsed_query"]["intent"] == "ROUTE_OPERATION"
    assert res_route["parsed_query"]["location"]["name"] == "Kakinada Port"
    assert res_route["parsed_query"]["destination_location"]["name"] == "Visakhapatnam Port"
    assert "marine_operations" in [s["agent_id"] for s in res_route["orchestration"]["selected_agents"]]
    print(f"  [OK] Route operation conversation: origin={res_route['parsed_query']['location']['name']}, dest={res_route['parsed_query']['destination_location']['name']}.")

    # 8. Marine safety conversation
    print("\n[8/23] Testing marine safety query: 'Vizag daggara active cyclone warnings unnaya?'...")
    status, res_safety = request("POST", "/api/v1/conversation/query", {
        "message": "Vizag daggara active cyclone warnings unnaya?",
    })
    assert status == 200
    assert res_safety["parsed_query"]["intent"] == "MARINE_SAFETY"
    assert res_safety["language"] == "te"
    assert res_safety["input_mode"] == "transliterated"
    assert res_safety["parsed_query"]["location"]["name"] == "Visakhapatnam Port"
    print(f"  [OK] Marine safety query: intent={res_safety['parsed_query']['intent']}, loc={res_safety['parsed_query']['location']['name']}.")

    # 9. Marine conditions conversation
    print("\n[9/23] Testing marine environmental inquiry: 'What are the current sea state and wave conditions near Kakinada?'...")
    status, res_marine = request("POST", "/api/v1/conversation/query", {
        "message": "What are the current sea state and wave conditions near Kakinada?",
    })
    assert status == 200
    assert res_marine["parsed_query"]["intent"] == "MARINE_CONDITIONS"
    print(f"  [OK] Marine conditions inquiry: intent={res_marine['parsed_query']['intent']}.")

    # 10. Earth observation conversation
    print("\n[10/23] Testing earth observation inquiry: 'What is the satellite chlorophyll condition near 16.97, 82.25?'...")
    status, res_eo = request("POST", "/api/v1/conversation/query", {
        "message": "What is the satellite chlorophyll condition near 16.97, 82.25?",
    })
    assert status == 200
    assert res_eo["parsed_query"]["intent"] == "EARTH_OBSERVATION"
    print(f"  [OK] Earth observation inquiry: intent={res_eo['parsed_query']['intent']}.")

    # 11. Location extraction
    print("\n[11/23] Testing port location extraction across multiple coastal nodes...")
    ports_to_test = [
        ("Machilipatnam", "Machilipatnam Port"),
        ("Krishnapatnam", "Krishnapatnam Port"),
        ("Bhavanapadu", "Bhavanapadu Harbor"),
        ("Gangavaram", "Gangavaram Port"),
    ]
    for port_kw, expected_name in ports_to_test:
        _, p_res = request("POST", "/api/v1/conversation/query", {
            "message": f"How are fishing conditions near {port_kw}?",
        })
        assert p_res["parsed_query"]["location"]["name"] == expected_name
    print("  [OK] Coastal ports accurately identified.")

    # 12. Coordinate extraction
    print("\n[12/23] Testing coordinate parsing...")
    _, c_res = request("POST", "/api/v1/conversation/query", {
        "message": "What are the sea conditions at lat 17.50 lon 83.10?",
    })
    assert c_res["parsed_query"]["location"]["latitude"] == 17.50
    assert c_res["parsed_query"]["location"]["longitude"] == 83.10
    print("  [OK] Geographic coordinates extracted: (17.50, 83.10).")

    # 13. Temporal extraction
    print("\n[13/23] Testing temporal extraction ('tomorrow at 6 AM')...")
    assert res_en["parsed_query"]["target_time"] == "06:00"
    assert res_en["parsed_query"]["target_date"] is not None
    print(f"  [OK] Target date/time: {res_en['parsed_query']['target_date']} at {res_en['parsed_query']['target_time']}.")

    # 14. Follow-up context memory resolution
    print("\n[14/23] Testing multi-turn context memory and follow-up query resolution...")
    # Turn 1: Establish context
    status, turn1 = request("POST", "/api/v1/conversation/query", {
        "message": "Can I go fishing tomorrow at 6 AM from Kakinada?",
    })
    cid = turn1["conversation_id"]
    assert cid is not None
    assert turn1["parsed_query"]["location"]["name"] == "Kakinada Port"
    assert turn1["parsed_query"]["target_time"] == "06:00"

    # Turn 2: Follow-up time shift with NO location mentioned
    status, turn2 = request("POST", "/api/v1/conversation/query", {
        "conversation_id": cid,
        "message": "What if I go at 9 AM instead?",
    })
    assert status == 200
    assert turn2["conversation_id"] == cid
    assert turn2["parsed_query"]["is_follow_up"] is True
    # Inherited location Kakinada from Turn 1
    assert turn2["parsed_query"]["location"]["name"] == "Kakinada Port"
    # Updated time to 09:00
    assert turn2["parsed_query"]["target_time"] == "09:00"
    # Preserved intent
    assert turn2["parsed_query"]["intent"] == "FISHING_ASSESSMENT"
    print(f"  [OK] Multi-turn session memory verified: Turn 2 inherited location={turn2['parsed_query']['location']['name']} and updated time to {turn2['parsed_query']['target_time']}.")

    # 15. Orchestrator integration (non-bypassed)
    print("\n[15/23] Testing Orchestrator integration & execution metadata...")
    assert "orchestration" in res_en
    assert "execution_metadata" in res_en["orchestration"]
    exec_meta = res_en["orchestration"]["execution_metadata"]
    assert len(exec_meta["successful_agents"]) >= 5
    assert exec_meta["execution_duration_ms"] > 0.0
    print(f"  [OK] Orchestrator integration verified: executed {len(exec_meta['successful_agents'])} domain agents in {exec_meta['execution_duration_ms']} ms.")

    # 16. Evidence provenance preservation
    print("\n[16/23] Testing evidence provenance preservation...")
    assert len(res_en["evidence"]) > 0
    for ev in res_en["evidence"]:
        assert ev["factor"] is not None
        assert ev["source"] is not None
        assert ev["source_category"] is not None
        assert ev["data_type"] is not None
        assert ev["originating_agent"] is not None
    print(f"  [OK] Verified {len(res_en['evidence'])} evidence items with complete source provenance.")

    # 17. CRITICAL safety preservation (BLOCKED)
    print("\n[17/23] Testing deterministic CRITICAL safety preservation (BLOCKED)...")
    db = SessionLocal()
    now_utc = datetime.now(timezone.utc)
    db.query(HazardZone).filter(HazardZone.name == "TEST_CONV_CRITICAL_SURGE").delete()
    wkt_crit = "POLYGON((82.10 16.80, 82.40 16.80, 82.40 17.10, 82.10 17.10, 82.10 16.80))"
    crit_zone = HazardZone(
        name="TEST_CONV_CRITICAL_SURGE",
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

    status, blocked_conv = request("POST", "/api/v1/conversation/query", {
        "message": "Can I go fishing tomorrow at 6 AM from Kakinada?",
    })
    assert status == 200
    assert blocked_conv["safety_status"] == "BLOCKED"
    assert blocked_conv["risk_level"] == "CRITICAL"
    assert "BLOCKED" in blocked_conv["response"]
    print(f"  [OK] Critical hazard strictly preserved in conversational response: safety_status='{blocked_conv['safety_status']}', risk='{blocked_conv['risk_level']}'.")

    # 18. WARNING preservation
    print("\n[18/23] Testing deterministic WARNING preservation...")
    db.query(HazardZone).filter(HazardZone.name == "TEST_CONV_CRITICAL_SURGE").delete()
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_CONV_ALERT_WARN").delete()
    warn_alert = MarineAlert(
        alert_id="TEST_CONV_ALERT_WARN",
        title="TEST: Severe Gale Warning for Kakinada Coast",
        alert_type="GALE_WIND",
        severity="WARNING",
        status="ACTIVE",
        description="Gale winds 60 km/h.",
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

    status, warn_conv = request("POST", "/api/v1/conversation/query", {
        "message": "Can I go fishing tomorrow at 6 AM from Kakinada?",
    })
    assert status == 200
    assert warn_conv["safety_status"] in ("WARNING", "BLOCKED")
    assert warn_conv["risk_level"] in ("HIGH", "CRITICAL")
    assert "WARNING" in warn_conv["response"] or "BLOCKED" in warn_conv["response"]
    print(f"  [OK] Warning advisory strictly preserved: safety='{warn_conv['safety_status']}', risk='{warn_conv['risk_level']}'.")

    # 19. INSUFFICIENT_DATA preservation
    print("\n[19/23] Testing INSUFFICIENT_DATA preservation on remote coordinates...")
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_CONV_ALERT_WARN").delete()
    db.commit()

    status, remote_conv = request("POST", "/api/v1/conversation/query", {
        "message": "What are the fishing conditions near lat -50.0 lon -100.0?",
    })
    assert status == 200
    assert remote_conv["safety_status"] == "INSUFFICIENT_DATA"
    assert remote_conv["confidence"] == "INSUFFICIENT_DATA"
    assert "INSUFFICIENT" in remote_conv["response"].upper()
    print(f"  [OK] Missing telemetry strictly preserved: safety='{remote_conv['safety_status']}'.")

    # 20. No unsafe guarantee generation
    print("\n[20/23] Verifying prohibition of misleading 100%-safe claims...")
    prohibited_phrases = ["100% safe", "guaranteed safe", "risk-free", "completely safe", "zero risk", "absolute safety"]
    for res_obj in [res_en, res_te_trans, res_te_uni, res_hi, res_comp, res_route, res_safety, res_marine, res_eo, blocked_conv, warn_conv, remote_conv]:
        resp_text = res_obj["response"].lower()
        for phrase in prohibited_phrases:
            assert phrase not in resp_text, f"Prohibited phrase '{phrase}' found in response: {resp_text}"
    print("  [OK] All conversational responses strictly adhere to evidence-grounded non-absolute phrasing.")

    # 21. Missing LLM API key fallback
    print("\n[21/23] Testing missing LLM API key deterministic fallback mode...")
    llm_client = LLMClientFactory.get_client()
    assert isinstance(llm_client, DeterministicRuleLLMClient)
    assert llm_client.provider_name == "deterministic_rule_engine"
    print(f"  [OK] Deterministic fallback provider active: {llm_client.provider_name}.")

    # 22. OpenAPI Registration
    print("\n[22/23] Verifying OpenAPI registration for Conversational Intelligence...")
    status, openapi = request("GET", "/openapi.json")
    assert status == 200
    paths = openapi.get("paths", {})
    endpoint = "/api/v1/conversation/query"
    assert endpoint in paths, f"Missing endpoint {endpoint} in OpenAPI paths"
    post_op = paths[endpoint].get("post", {})
    tags = post_op.get("tags", [])
    assert "Conversational Intelligence" in tags, f"Expected tag 'Conversational Intelligence', got {tags}"
    print(f"  [OK] Endpoint {endpoint} registered with tag 'Conversational Intelligence'.")

    # Clean up DB
    db.query(HazardZone).filter(HazardZone.name == "TEST_CONV_CRITICAL_SURGE").delete()
    db.query(MarineAlert).filter(MarineAlert.alert_id == "TEST_CONV_ALERT_WARN").delete()
    db.commit()
    db.close()

    print("\n  [OK] All 22 Conversational Intelligence functional tests passed.")


def run_regressions():
    print("\n" + "=" * 80)
    print("RUNNING COMPLETE DOMAIN AGENT & ORCHESTRATOR REGRESSION SUITES...")
    print("=" * 80)

    from scratch.test_orchestrator import test_orchestrator, run_regressions as run_all_prior_regressions
    test_orchestrator()
    run_all_prior_regressions()
    print("  [OK] All 6 domain agent & orchestrator regressions passed.")

    print("\n" + "=" * 80)
    print("RUNNING ALL EXISTING BACKEND ENDPOINTS REGRESSION (28 ENDPOINTS)...")
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
        ("POST", "/api/v1/conversation/query", {"message": "Can I go fishing tomorrow at 6 AM from Kakinada?"}, 200),
    ]

    for method, path, data, expected_status in endpoints:
        status, _ = request(method, path, data)
        assert status == expected_status, f"Endpoint {method} {path} returned {status}, expected {expected_status}"
        print(f"  [OK] {method} {path} -> {status}")

    print("\n" + "=" * 80)
    print("ALL CONVERSATION TESTS, ORCHESTRATOR TESTS & ALL 6 DOMAIN AGENT REGRESSIONS PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    test_conversational_intelligence()
    run_regressions()
