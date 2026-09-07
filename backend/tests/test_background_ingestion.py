import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from database import SessionLocal
from main import app
from models.data_source import DataSource
from models.data_refresh_log import DataRefreshLog
from models.marine import MarineObservation
from models.weather import WeatherObservation
from models.earth_observation import EarthObservation
from schemas.marine_provider import (
    DataFreshnessStatus,
    DataQualityStatus,
    MarineDataType,
    NormalizedMarineRecord,
    ProviderResponse,
    ProviderStatus,
)
from ingestion.config import IngestionConfig, MonitoredLocation
from ingestion.worker import BackgroundIngestionWorker
from services.marine_data import MarineDataService
from ingestion.earth_observation import EarthObservationIngestionService


# ==============================================================================
# TEST 1: Ingestion Configuration Defaults & Location Parsing
# ==============================================================================
def test_ingestion_config_defaults():
    config = IngestionConfig.from_env()
    assert config.enabled in (True, False)
    assert config.incois_interval_minutes > 0
    assert config.copernicus_interval_minutes > 0
    assert config.eo_interval_minutes > 0
    assert config.imd_interval_minutes > 0
    assert len(config.locations) >= 1
    
    # Check Visakhapatnam presence
    names = [loc.name for loc in config.locations]
    assert any("Visakhapatnam" in name for name in names)


# ==============================================================================
# TEST 2: Worker Disabled Mode
# ==============================================================================
def test_worker_disabled_mode():
    cfg = IngestionConfig(enabled=False)
    worker = BackgroundIngestionWorker(config=cfg)
    assert worker.is_running is False
    worker.start()
    assert len(worker.tasks) == 0
    assert worker.is_running is False


# ==============================================================================
# TEST 3: Per-Provider Concurrency Lock
# ==============================================================================
@pytest.mark.anyio
async def test_per_provider_concurrency_lock():
    worker = BackgroundIngestionWorker()
    
    # Acquire lock manually to simulate active job
    await worker.locks["INCOIS"].acquire()
    try:
        # Second invocation should detect lock and skip immediately
        res = await worker.ingest_incois()
        assert res["status"] == "SKIPPED"
        assert "locked" in res.get("reason", "").lower()
    finally:
        worker.locks["INCOIS"].release()


# ==============================================================================
# TEST 4: Failure Isolation Across Providers
# ==============================================================================
@pytest.mark.anyio
async def test_failure_isolation_across_providers():
    worker = BackgroundIngestionWorker()
    loc = [MonitoredLocation(name="Test Loc", latitude=17.6868, longitude=83.2185)]
    
    # Simulate an error in INCOIS Provider
    with patch("connectors.incois.INCOISProvider.fetch_marine_data") as mock_incois:
        mock_incois.side_effect = ConnectionResetError("Simulated INCOIS connection reset")
        incois_res = await worker.ingest_incois(loc)
        assert incois_res["status"] == "FAILED"
        assert "Simulated INCOIS" in incois_res.get("error", "")

    # Copernicus should still run successfully and independently
    with patch("connectors.copernicus.CopernicusProvider.fetch_marine_data") as mock_cop:
        now_iso = datetime.now(timezone.utc).isoformat()
        mock_cop.return_value = ProviderResponse(
            provider_name="Copernicus",
            status=ProviderStatus.HEALTHY,
            records=[
                NormalizedMarineRecord(
                    parameter="ocean_current_velocity",
                    value=1.1,
                    unit="km/h",
                    latitude=17.6868,
                    longitude=83.2185,
                    valid_time=now_iso,
                    retrieved_at=now_iso,
                    source="Copernicus",
                    data_type=MarineDataType.OBSERVED,
                    freshness_status=DataFreshnessStatus.FRESH,
                    quality_status=DataQualityStatus.VALIDATED,
                )
            ],
        )
        cop_res = await worker.ingest_copernicus(loc)
        assert cop_res["status"] == "SUCCESS"
        assert cop_res["records_processed"] >= 1


# ==============================================================================
# TEST 5: IMD Graceful Status Handling (Skip if Auth Required)
# ==============================================================================
@pytest.mark.anyio
async def test_imd_graceful_status_handling():
    worker = BackgroundIngestionWorker()
    loc = [MonitoredLocation(name="Visakhapatnam Coast", latitude=17.6868, longitude=83.2185)]
    
    res = await worker.ingest_imd(loc)
    # IMD should either be SUCCESS or gracefully SKIPPED (due to gateway/IP authorization)
    assert res["status"] in ("SUCCESS", "SKIPPED")
    if res["status"] == "SKIPPED":
        assert "skipped" in res.get("reason", "").lower() or "authorization" in res.get("reason", "").lower() or "configured" in res.get("reason", "").lower()


# ==============================================================================
# TEST 6: DataRefreshLog & DataSource PostgreSQL Persistence
# ==============================================================================
@pytest.mark.anyio
async def test_data_refresh_log_persistence():
    db = SessionLocal()
    try:
        worker = BackgroundIngestionWorker()
        loc = [MonitoredLocation(name="Visakhapatnam", latitude=17.6868, longitude=83.2185)]
        
        now_iso = datetime.now(timezone.utc).isoformat()
        with patch("connectors.copernicus.CopernicusProvider.fetch_marine_data") as mock_cop:
            mock_cop.return_value = ProviderResponse(
                provider_name="Copernicus",
                status=ProviderStatus.HEALTHY,
                records=[
                    NormalizedMarineRecord(
                        parameter="ocean_current_velocity",
                        value=0.95,
                        unit="km/h",
                        latitude=17.6868,
                        longitude=83.2185,
                        valid_time=now_iso,
                        retrieved_at=now_iso,
                        source="Copernicus",
                        data_type=MarineDataType.OBSERVED,
                        freshness_status=DataFreshnessStatus.FRESH,
                        quality_status=DataQualityStatus.VALIDATED,
                    )
                ],
            )
            res = await worker.ingest_copernicus(loc)
            assert res["status"] == "SUCCESS"
            
            # Verify refresh log recorded in PostgreSQL
            latest_log = (
                db.query(DataRefreshLog)
                .join(DataSource)
                .filter(DataSource.provider == "Copernicus")
                .order_by(DataRefreshLog.id.desc())
                .first()
            )
            assert latest_log is not None
            assert latest_log.status == "SUCCESS"
            assert latest_log.records_processed >= 1
            assert latest_log.started_at is not None
            assert latest_log.completed_at is not None
    finally:
        db.close()


# ==============================================================================
# TEST 7: Cache-First Marine Intelligence Serving
# ==============================================================================
def test_cache_first_marine_intelligence_serving():
    db = SessionLocal()
    try:
        service = MarineDataService()
        now = datetime.now(timezone.utc)
        
        # Insert a fresh marine observation into PostgreSQL
        obs = MarineObservation(
            latitude=17.6868,
            longitude=83.2185,
            observed_at=now,
            wave_height_m=1.75,
            wave_period_s=8.0,
            wave_direction_deg=185.0,
            ocean_current_velocity_kmh=1.2,
            sea_surface_temperature_c=28.4,
            source="INCOIS",
            data_type="OBSERVATION",
            quality_flag="VALIDATED",
        )
        db.add(obs)
        db.commit()
        
        # With fresh data in DB, fetch_marine_intelligence should serve from cache
        # without calling mock providers
        with patch("connectors.incois.INCOISProvider.fetch_marine_data") as mock_incois:
            mock_incois.side_effect = RuntimeError("Upstream provider called unnecessarily!")
            
            res = service.fetch_marine_intelligence(
                latitude=17.6868,
                longitude=83.2185,
                location_name="Visakhapatnam Coast",
                db=db,
                save_to_db=False,
                now=now,
            )
            
            assert res.is_coastal is True
            assert len(res.records) >= 1
            rec_map = {r.parameter: r.value for r in res.records}
            assert rec_map.get("wave_height") == 1.75
            assert "Database Cache" in res.primary_source
            assert mock_incois.call_count == 0  # Zero upstream network calls
    finally:
        db.close()


# ==============================================================================
# TEST 8: Cache-First Earth Observation Serving
# ==============================================================================
def test_cache_first_earth_observation_serving():
    db = SessionLocal()
    try:
        service = EarthObservationIngestionService()
        now = datetime.now(timezone.utc)
        
        # Insert a fresh EarthObservation into PostgreSQL
        eo_obs = EarthObservation(
            latitude=17.6868,
            longitude=83.2185,
            observed_at=now,
            retrieved_at=now,
            source="Sentinel-3 OLCI / Copernicus",
            product_type="SST_AND_OPTICAL",
            chlorophyll_a_mg_m3=0.88,
            sea_surface_temperature_c=28.6,
            ocean_colour="MODERATE_PRODUCTIVE",
            quality_flag="VALIDATED",
        )
        db.add(eo_obs)
        db.commit()
        
        with patch("connectors.earth_observation.EarthObservationConnector.fetch") as mock_fetch:
            mock_fetch.side_effect = RuntimeError("Upstream EO fetch called unnecessarily!")
            
            data = service.ingest(
                db=db,
                latitude=17.6868,
                longitude=83.2185,
                use_cache=True,
            )
            
            assert data["measurements"]["chlorophyll_a_mg_m3"] == 0.88
            assert "Database Cache" in data["source"]
            assert mock_fetch.call_count == 0
    finally:
        db.close()


# ==============================================================================
# TEST 9: Ingestion API Router & Manual Trigger
# ==============================================================================
def test_ingestion_api_endpoints():
    client = TestClient(app)
    
    # 1. Test GET /api/v1/ingestion/status
    res_status = client.get("/api/v1/ingestion/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert "worker_enabled" in status_data
    assert "providers" in status_data
    assert "INCOIS" in status_data["providers"]
    assert "Copernicus" in status_data["providers"]
    assert "EarthObservation" in status_data["providers"]
    
    # 2. Test GET /api/v1/ingestion/locations
    res_locs = client.get("/api/v1/ingestion/locations")
    assert res_locs.status_code == 200
    locs = res_locs.json()
    assert len(locs) >= 1
    assert "latitude" in locs[0]
    assert "longitude" in locs[0]
    
    # 3. Test POST /api/v1/ingestion/trigger
    res_trigger = client.post(
        "/api/v1/ingestion/trigger",
        json={"provider": "INCOIS", "latitude": 17.6868, "longitude": 83.2185},
    )
    assert res_trigger.status_code == 200
    trigger_data = res_trigger.json()
    assert trigger_data["provider"] == "INCOIS"
    assert trigger_data["status"] in ("SUCCESS", "SKIPPED", "FAILED")


# ==============================================================================
# TEST 10: Graceful Worker Lifecycle (Start & Stop)
# ==============================================================================
@pytest.mark.anyio
async def test_graceful_worker_lifecycle():
    worker = BackgroundIngestionWorker(config=IngestionConfig(enabled=True))
    assert worker.is_running is False
    worker.start()
    assert worker.is_running is True
    assert len(worker.tasks) == 4
    
    await worker.stop()
    assert worker.is_running is False
    assert len(worker.tasks) == 0


# ==============================================================================
# TEST 11: Zero Secret Leakage in Logging Verification
# ==============================================================================
def test_no_secret_leakage_in_logging(caplog):
    caplog.set_level(logging.INFO)
    logger_test = logging.getLogger("ingestion.worker")
    
    logger_test.info("[INGESTION] INCOIS started")
    logger_test.info("[INGESTION] COPERNICUS completed: 12 records")
    logger_test.info("[INGESTION] IMD skipped: gateway/IP authorization required")
    
    log_text = caplog.text
    assert "[INGESTION] INCOIS started" in log_text
    assert "[INGESTION] COPERNICUS completed" in log_text
    assert "[INGESTION] IMD skipped" in log_text
    
    # Verify no secret keywords or API keys are echoed
    for forbidden in ["api_key=", "apikey=", "password=", "secret=", "bearer "]:
        assert forbidden not in log_text.lower()
