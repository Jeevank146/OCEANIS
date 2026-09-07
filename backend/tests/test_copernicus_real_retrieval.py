import os
import sys
import math
from datetime import datetime, timezone
from dotenv import load_dotenv

backend_dir = r"C:\Users\jeeva\Projects\OCEANIS\backend"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from connectors.copernicus import CopernicusProvider
from schemas.marine_provider import ProviderStatus, NormalizedMarineRecord, DataFreshnessStatus, DataQualityStatus
from services.marine_data import MarineDataService
from models.marine import MarineObservation


def test_copernicus_real_data_retrieval():
    print("================ COPERNICUS REAL DATA TEST ================")
    
    # 1. Provider configuration & initialization
    provider = CopernicusProvider()
    print(f"Provider: {provider.provider_name}")
    print(f"Configured: {provider.is_configured}")
    assert provider.is_configured, "Copernicus credentials must be detected in .env"

    # 2. Query small real sample around Visakhapatnam / Bay of Bengal
    lat = 17.6868
    lon = 83.2185
    print(f"Query coordinates: lat={lat}, lon={lon} (Visakhapatnam / Bay of Bengal)")

    resp = provider.fetch_marine_data(latitude=lat, longitude=lon)

    print(f"Provider Response Status: {resp.status}")
    print(f"Number of Records: {len(resp.records)}")

    assert resp.status == ProviderStatus.HEALTHY, f"Expected HEALTHY, got {resp.status}: {resp.error_message}"
    assert len(resp.records) > 0, "Expected at least one real record from Copernicus"

    # 3. Parameter validation & provenance
    variables_retrieved = []
    sample_val = None
    sample_unit = None

    for r in resp.records:
        variables_retrieved.append(r.parameter)
        print(f"  * Parameter: {r.parameter} | Value: {r.value} {r.unit} | Valid Time: {r.valid_time} | Source: {r.source}")
        if r.parameter == "ocean_current_u":
            sample_val = f"uo = {r.value}"
            sample_unit = r.unit

    # Verify provenance
    for r in resp.records:
        assert r.source == "Copernicus Marine", f"Unexpected source: {r.source}"
        assert r.raw_identifier == provider.DATASET_CURRENTS, f"Unexpected product: {r.raw_identifier}"
        assert r.valid_time is not None, "valid_time missing"
        assert r.freshness_status == DataFreshnessStatus.FRESH, "Freshness should be FRESH"
        assert r.quality_status == DataQualityStatus.VALIDATED, "Quality should be VALIDATED"

    # 4. Passage through MarineDataService (Normalized OCEANIS data layer)
    print("\nValidating through MarineDataService orchestration...")
    service = MarineDataService(providers={"Copernicus": provider})
    
    # Provider health check
    health_list = service.get_provider_health()
    cop_health = next((h for h in health_list if h.name == "Copernicus Marine"), None)
    assert cop_health is not None, "Copernicus health response missing"
    assert cop_health.status == ProviderStatus.HEALTHY, f"Copernicus health status: {cop_health.status}"
    print(f"MarineDataService Provider Health: {cop_health.status}")

    # Fetch multi-source intelligence (save_to_db=False for fast in-memory verification)
    multi_resp = service.fetch_marine_intelligence(
        latitude=lat,
        longitude=lon,
        location_name="Visakhapatnam",
        save_to_db=False,
    )
    print(f"MultiSourceMarineResponse records count: {len(multi_resp.records)}")
    print(f"MultiSourceMarineResponse statuses: {multi_resp.provider_statuses}")
    assert multi_resp.provider_statuses.get("Copernicus") == ProviderStatus.HEALTHY

    # 5. Database model validation
    print("\nValidating MarineObservation SQLAlchemy database model instantiation...")
    uo_rec = next((r for r in resp.records if r.parameter == "ocean_current_u"), resp.records[0])
    current_vel_rec = next((r for r in resp.records if r.parameter == "ocean_current_velocity"), None)
    current_dir_rec = next((r for r in resp.records if r.parameter == "ocean_current_direction"), None)
    
    obs_time = datetime.fromisoformat(uo_rec.valid_time) if "T" in uo_rec.valid_time else datetime.now(timezone.utc)
    
    db_obs = MarineObservation(
        latitude=uo_rec.latitude,
        longitude=uo_rec.longitude,
        observed_at=obs_time,
        ocean_current_velocity_kmh=current_vel_rec.value if current_vel_rec else None,
        ocean_current_direction_deg=current_dir_rec.value if current_dir_rec else None,
        source="Copernicus Marine",
        data_type="MODEL",
        quality_flag="VALIDATED",
    )
    print("Database observation object:", repr(db_obs))
    assert db_obs.source == "Copernicus Marine"
    assert db_obs.ocean_current_velocity_kmh is not None

    # 6. Summary Report Output
    print("\n================ FINAL REPORT ================")
    print("COPERNICUS REAL DATA TEST")
    print(f"- Authentication: SUCCESS")
    print(f"- Dataset: {provider.DATASET_CURRENTS}")
    print(f"- Variables retrieved: {', '.join(variables_retrieved)}")
    print(f"- Geographic area: Visakhapatnam / Bay of Bengal (lat {lat}, lon {lon})")
    print(f"- Time range: Latest operational analysis (valid {uo_rec.valid_time})")
    print(f"- Real data retrieved: YES")
    print(f"- Sample value: {sample_val}")
    print(f"- Units: {sample_unit}")
    print(f"- Provenance preserved: YES")
    print(f"- Normalized OCEANIS data layer: SUCCESS")
    print(f"- Database persistence: NOT REQUIRED (In-memory normalized pipeline verified)")
    print(f"- Test result: PASS")


if __name__ == "__main__":
    test_copernicus_real_data_retrieval()
