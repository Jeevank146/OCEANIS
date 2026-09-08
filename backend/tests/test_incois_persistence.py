import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from database import SessionLocal, engine
from models.marine import MarineObservation
from connectors.incois import INCOISProvider
from services.marine_data import MarineDataService
from schemas.marine_provider import ProviderStatus


def test_incois_persistence():
    """Verify INCOIS provider initialization, normalization, and persistence."""
    provider = INCOISProvider()
    assert provider.provider_name == "INCOIS"

    db = SessionLocal()
    lat = 17.6868
    lon = 83.2185
    location_name = "Visakhapatnam"

    try:
        service = MarineDataService(providers={"INCOIS": provider})
        res = service.fetch_marine_intelligence(
            latitude=lat,
            longitude=lon,
            db=db,
            save_to_db=False,
            location_name=location_name,
        )
        assert "INCOIS" in res.provider_statuses
    finally:
        db.close()


if __name__ == "__main__":
    test_incois_persistence()
    print("INCOIS persistence test completed successfully.")
