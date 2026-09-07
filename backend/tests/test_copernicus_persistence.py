import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from database import SessionLocal, engine
from models.marine import MarineObservation
from connectors.copernicus import CopernicusProvider
from services.marine_data import MarineDataService
from schemas.marine_provider import ProviderStatus


def test_copernicus_postgresql_persistence():
    print("=== STEP 8: COPERNICUS POSTGRESQL PERSISTENCE TEST ===")

    db = SessionLocal()

    lat = 17.6868
    lon = 83.2185
    location_name = "Visakhapatnam"

    try:
        # 1. Clean previous Copernicus test rows for this location
        db.query(MarineObservation).filter(
            MarineObservation.source == "Copernicus Marine"
        ).delete()
        db.commit()
        print("Cleaned prior Copernicus test rows.")

        # 2. Fetch and persist Copernicus real data through MarineDataService
        provider = CopernicusProvider()
        service = MarineDataService(providers={"Copernicus": provider})

        print(f"Executing fetch_marine_intelligence(save_to_db=True) for {location_name} ({lat}, {lon})...")
        res = service.fetch_marine_intelligence(
            latitude=lat,
            longitude=lon,
            db=db,
            save_to_db=True,
            location_name=location_name,
        )
        print(f"Provider Status: {res.provider_statuses.get('Copernicus')}")
        print(f"Normalized records returned: {len(res.records)}")

        assert res.provider_statuses.get("Copernicus") == ProviderStatus.HEALTHY

        # 3. Query PostgreSQL table to verify real persistence
        persisted_rows = (
            db.query(MarineObservation)
            .filter(MarineObservation.source == "Copernicus Marine")
            .all()
        )
        print(f"Records found in marine_observations: {len(persisted_rows)}")
        assert len(persisted_rows) > 0, "No records found in PostgreSQL marine_observations!"
        
        row = persisted_rows[0]
        print("\nPersisted Record Details:")
        print(f"  ID: {row.id}")
        print(f"  Source: {row.source}")
        print(f"  Latitude: {row.latitude}, Longitude: {row.longitude}")
        print(f"  Observed At: {row.observed_at}")
        print(f"  Ocean Current Velocity (km/h): {row.ocean_current_velocity_kmh}")
        print(f"  Ocean Current Direction (deg): {row.ocean_current_direction_deg}")
        print(f"  Data Type: {row.data_type}")
        print(f"  Quality Flag: {row.quality_flag}")

        assert row.ocean_current_velocity_kmh is not None
        assert row.ocean_current_direction_deg is not None
        assert row.source == "Copernicus Marine"

        initial_count = len(persisted_rows)

        # 4. Duplicate Protection Test
        print("\nRunning duplicate ingestion test...")
        res2 = service.fetch_marine_intelligence(
            latitude=lat,
            longitude=lon,
            db=db,
            save_to_db=True,
            location_name=location_name,
        )
        persisted_rows_after = (
            db.query(MarineObservation)
            .filter(MarineObservation.source == "Copernicus Marine")
            .all()
        )
        after_count = len(persisted_rows_after)
        print(f"Row count before: {initial_count}, Row count after second ingestion: {after_count}")
        assert after_count == initial_count, f"Duplicate records were created! ({after_count} != {initial_count})"
        print("Duplicate protection verified: SUCCESS")

        # 5. Retrieval from DB Test
        retrieved_obs = (
            db.query(MarineObservation)
            .filter(
                MarineObservation.id == row.id,
                MarineObservation.source == "Copernicus Marine",
            )
            .first()
        )
        assert retrieved_obs is not None
        assert retrieved_obs.ocean_current_velocity_kmh is not None
        assert retrieved_obs.ocean_current_direction_deg is not None
        print("Retrieval from database test: PASS")

        # 6. Final Report
        print("\n================ FINAL REPORT ================")
        print("STEP 8 COPERNICUS PERSISTENCE")
        print(f"- Existing model/table used: MarineObservation (marine_observations)")
        print(f"- Real records inserted: {initial_count}")
        print(f"- Provider: Copernicus Marine")
        print(f"- Dataset: cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m")
        print(f"- Variables: ocean_current_velocity (km/h), ocean_current_direction (deg), uo, vo")
        print(f"- PostGIS persistence: SUCCESS")
        print(f"- Duplicate protection: SUCCESS")
        print(f"- Retrieval-from-DB test: PASS")
        print(f"- Overall STEP 8 Copernicus status: COMPLETE")

    finally:
        db.close()


if __name__ == "__main__":
    test_copernicus_postgresql_persistence()
