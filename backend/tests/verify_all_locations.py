import sys
import os

# Ensure backend path and UTF-8 stdout
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_suite():
    print("\n=======================================================")
    print("  OCEANIS DYNAMIC LOCATION INTELLIGENCE VERIFICATION  ")
    print("=======================================================\n")

    test_cases = [
        # 1. Indian Coastal Cities
        ("1. Visakhapatnam", {"query": "Visakhapatnam"}, "VALID_COASTAL", True),
        ("2. Kakinada", {"query": "Kakinada"}, "VALID_COASTAL", True),
        ("3. Kochi", {"query": "Kochi"}, "VALID_COASTAL", True),
        ("4. Mumbai", {"query": "Mumbai"}, "VALID_COASTAL", True),
        ("5. Chennai", {"query": "Chennai"}, "VALID_COASTAL", True),
        # 6. International Coastal Locations
        ("6a. Miami (USA)", {"query": "Miami"}, ["VALID_COASTAL", "VALID_MARINE"], True),
        ("6b. Rotterdam (Netherlands)", {"query": "Rotterdam"}, ["VALID_COASTAL", "VALID_MARINE"], True),
        ("6c. Sydney (Australia)", {"query": "Sydney"}, ["VALID_COASTAL", "VALID_MARINE"], True),
        ("6d. Singapore", {"query": "Singapore"}, ["VALID_COASTAL", "VALID_MARINE"], True),
        # 7. Offshore Coordinates
        ("7. Offshore Bay of Bengal (16.5, 83.0)", {"latitude": 16.5, "longitude": 83.0}, ["VALID_COASTAL", "VALID_MARINE"], True),
        # 8. Inland Locations
        ("8a. Hyderabad (Inland)", {"query": "Hyderabad"}, "INLAND", False),
        ("8b. New Delhi (Inland)", {"query": "New Delhi"}, "INLAND", False),
        ("8c. Dallas (Inland USA)", {"query": "Dallas"}, "INLAND", False),
        # 9. Invalid Location Text
        ("9. Invalid Location Text", {"query": "xyz999nonsenseplace"}, "UNRESOLVED", False),
        # 10. Current Location (GPS Reverse Geocode)
        ("10. GPS Reverse Geocode (17.6868, 83.2185)", {"latitude": 17.6868, "longitude": 83.2185}, "VALID_COASTAL", True),
        # 11. Coordinate Input Formats
        ("11a. Decimal (17.6868, 83.2185)", {"query": "17.6868, 83.2185"}, ["VALID_COASTAL", "VALID_MARINE"], True),
        ("11b. Cardinal (25.7617 N, 80.1918 W)", {"query": "25.7617 N, 80.1918 W"}, ["VALID_COASTAL", "VALID_MARINE"], True),
    ]

    all_passed = True
    for label, payload, expected_status, expected_coastal in test_cases:
        if "latitude" in payload and "query" not in payload:
            resp = client.post("/api/v1/location/reverse-geocode", json=payload)
        else:
            resp = client.post("/api/v1/location/validate", json=payload)
        
        if resp.status_code != 200:
            print(f"[FAIL] {label}: HTTP {resp.status_code} - {resp.text}")
            all_passed = False
            continue

        data = resp.json()
        status_ok = data["status"] in expected_status if isinstance(expected_status, list) else data["status"] == expected_status
        coastal_ok = data["is_coastal"] == expected_coastal

        if status_ok and coastal_ok:
            dist_info = f"dist: {data.get('distance_to_coast_km')} km" if data.get('distance_to_coast_km') is not None else ""
            ctx_info = f"ctx: {data.get('marine_context')}" if data.get('marine_context') else ""
            print(f"[PASS] {label:42} => {data['status']:14} | coastal={data['is_coastal']} | {dist_info} | {ctx_info}")
        else:
            print(f"[FAIL] {label:42} => GOT status={data['status']}, is_coastal={data['is_coastal']} (EXPECTED {expected_status}, {expected_coastal})")
            all_passed = False

    print("\n-------------------------------------------------------")
    print("  DYNAMIC MARINE TELEMETRY ENDPOINT CHECKS             ")
    print("-------------------------------------------------------\n")

    # Coastal dynamic conditions
    coastal_marine_resp = client.get("/api/v1/marine/conditions-dynamic?latitude=17.6868&longitude=83.2185&location_name=Visakhapatnam")
    assert coastal_marine_resp.status_code == 200
    cm_data = coastal_marine_resp.json()
    print(f"[PASS] Coastal Dynamic Marine (Vizag): status={cm_data['availability_status']} | wave={cm_data.get('wave_height_m')}m | sea_state={cm_data.get('sea_state')} | risk={cm_data.get('risk_level')}")
    assert cm_data["is_coastal"] is True

    # Inland dynamic conditions (Strictly blocked)
    inland_marine_resp = client.get("/api/v1/marine/conditions-dynamic?latitude=17.3850&longitude=78.4867&location_name=Hyderabad")
    assert inland_marine_resp.status_code == 200
    im_data = inland_marine_resp.json()
    print(f"[PASS] Inland Dynamic Marine (Hyderabad): status={im_data['availability_status']} | is_coastal={im_data['is_coastal']} | message={im_data.get('message')}")
    assert im_data["is_coastal"] is False
    assert im_data["availability_status"] == "INLAND_BLOCKED"
    assert im_data["wave_height_m"] is None

    print("\n=======================================================")
    if all_passed:
        print("  ALL 11 REQUIRED TEST SCENARIOS PASSED WITH SUCCESS! ")
    else:
        print("  SOME TESTS FAILED ")
    print("=======================================================\n")

if __name__ == "__main__":
    run_suite()
