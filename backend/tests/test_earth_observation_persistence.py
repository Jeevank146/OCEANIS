import os
import sys
import pytest
from datetime import datetime, timezone
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from database import SessionLocal
from models.earth_observation import EarthObservation
from connectors.earth_observation import EarthObservationConnector, classify_ocean_colour
from ingestion.earth_observation import EarthObservationIngestionService


def test_classify_ocean_colour():
    """Unit test for bio-optical ocean colour classification."""
    assert classify_ocean_colour(None) is None
    assert "Deep Blue" in classify_ocean_colour(0.05)
    assert "Blue" in classify_ocean_colour(0.3)
    assert "Blue-Green" in classify_ocean_colour(1.0)
    assert "Greenish" in classify_ocean_colour(2.5)
    assert "Turbid" in classify_ocean_colour(6.0)


def test_earth_observation_configuration_status():
    """Verify Earth Observation connector detects configured credentials."""
    connector = EarthObservationConnector()
    assert connector.is_configured is True
    assert connector.source_name == "Copernicus Marine / Sentinel-3 EO"


def test_earth_observation_real_data_retrieval_and_postgres_persistence():
    """
    End-to-end integration test:
    Real satellite Chlorophyll-a retrieval -> Normalization -> PostgreSQL persistence -> Duplicate protection -> DB retrieval.
    """
    db = SessionLocal()
    lat = 17.6868
    lon = 83.2185

    try:
        # 1. Clean prior test rows
        db.query(EarthObservation).filter(
            EarthObservation.source == "Copernicus Marine / Sentinel-3 EO"
        ).delete()
        db.commit()

        connector = EarthObservationConnector()
        service = EarthObservationIngestionService(connector=connector)

        # 2. Ingest real satellite data (1st call)
        res1 = service.ingest(db=db, latitude=lat, longitude=lon)

        assert res1 is not None
        assert res1.get("source") == "Copernicus Marine / Sentinel-3 EO"
        assert res1.get("data_type") == "SATELLITE_DIRECT"
        assert res1.get("quality_flag") == "VALIDATED"

        measurements = res1.get("measurements", {})
        assert measurements.get("chlorophyll_a_mg_m3") is not None
        assert measurements.get("chlorophyll_a_mg_m3") > 0.0
        assert measurements.get("ocean_colour") is not None

        metadata = res1.get("metadata", {})
        assert metadata.get("dataset_id") == "cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D"
        assert "Sentinel-3" in metadata.get("satellite_platform", "")

        obs_id_1 = res1.get("observation_id")
        assert obs_id_1 is not None

        # 3. Verify PostgreSQL Persistence
        persisted = (
            db.query(EarthObservation)
            .filter(EarthObservation.source == "Copernicus Marine / Sentinel-3 EO", EarthObservation.latitude >= 17.0, EarthObservation.latitude <= 18.0)
            .all()
        )
        assert len(persisted) == 1
        row = persisted[0]
        assert row.id == obs_id_1
        assert row.chlorophyll_a_mg_m3 == measurements.get("chlorophyll_a_mg_m3")
        assert row.ocean_colour == measurements.get("ocean_colour")
        assert row.satellite_platform is not None
        assert row.sensor_instrument == "OLCI, VIIRS, MODIS"

        # 4. Duplicate Protection Verification (2nd call)
        res2 = service.ingest(db=db, latitude=lat, longitude=lon)
        obs_id_2 = res2.get("observation_id")
        assert obs_id_2 == obs_id_1

        persisted_after = (
            db.query(EarthObservation)
            .filter(
                EarthObservation.source == "Copernicus Marine / Sentinel-3 EO",
                EarthObservation.latitude >= 17.0, EarthObservation.latitude <= 18.0,
            )
            .all()
        )
        assert len(persisted_after) == 1, f"Duplicate rows created! ({len(persisted_after)} != 1)"

        # 5. Database Retrieval Test
        retrieved_row = (
            db.query(EarthObservation)
            .filter(EarthObservation.id == obs_id_1)
            .first()
        )
        assert retrieved_row is not None
        assert retrieved_row.chlorophyll_a_mg_m3 > 0.0
        assert retrieved_row.source == "Copernicus Marine / Sentinel-3 EO"

    finally:
        db.close()


def test_earth_observation_invalid_coordinates():
    """Verify connector and validation properly handle out-of-range coordinates."""
    connector = EarthObservationConnector()
    # Invalid latitude
    with pytest.raises(Exception):
        connector.fetch(latitude=120.0, longitude=83.2185)


if __name__ == "__main__":
    test_classify_ocean_colour()
    test_earth_observation_configuration_status()
    test_earth_observation_real_data_retrieval_and_postgres_persistence()
    print("ALL EARTH OBSERVATION TESTS PASSED!")
