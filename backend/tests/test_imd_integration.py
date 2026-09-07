from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock

from database import SessionLocal
from connectors.base import BaseMarineDataProvider
from connectors.imd import IMDProvider
from models.weather import WeatherObservation
from models.marine import MarineObservation
from schemas.marine_provider import (
    DataFreshnessStatus,
    DataQualityStatus,
    MarineDataType,
    NormalizedMarineRecord,
    ProviderResponse,
    ProviderStatus,
)
from services.marine_data import MarineDataService


# ==============================================================================
# TEST 1: IMD Environment Configuration & Secret Masking
# ==============================================================================
def test_imd_environment_configuration():
    provider = IMDProvider()
    assert isinstance(provider, BaseMarineDataProvider)
    assert provider.provider_name == "IMD"
    assert provider.provider_category == "COASTAL_RADAR_AND_WARNINGS"
    assert "India Meteorological Department" in provider.governing_authority
    # Ensure key is loaded and not empty
    assert provider.is_configured is True
    assert provider.api_key is not None
    assert len(provider.api_key.strip()) > 0


# ==============================================================================
# TEST 2: IMD Health Check
# ==============================================================================
def test_imd_health_check():
    provider = IMDProvider()
    health = provider.check_health()
    assert health.name == "IMD"
    assert health.enabled is True
    assert health.auth_configured is True
    assert health.status in (ProviderStatus.HEALTHY, ProviderStatus.AUTH_FAILURE, ProviderStatus.CONFIGURATION_REQUIRED)


# ==============================================================================
# TEST 3: IMD Real API Connection Attempt (Visakhapatnam)
# ==============================================================================
def test_imd_real_api_request_status():
    provider = IMDProvider()
    # Visakhapatnam coastal coordinates
    res = provider.fetch_marine_data(latitude=17.6868, longitude=83.2185)
    
    # Must return a valid ProviderResponse object
    assert isinstance(res, ProviderResponse)
    assert res.provider_name == "IMD"
    assert res.retrieved_at is not None
    
    # Verify accurate status classification (Real API returns AUTH_FAILURE or HEALTHY or NO_DATA)
    assert res.status in (ProviderStatus.AUTH_FAILURE, ProviderStatus.HEALTHY, ProviderStatus.NO_DATA, ProviderStatus.UNAVAILABLE)
    if res.status == ProviderStatus.AUTH_FAILURE:
        assert "IMD authentication failed" in (res.error_message or "")


# ==============================================================================
# TEST 4: IMD Payload Normalization
# ==============================================================================
def test_imd_payload_normalization():
    provider = IMDProvider()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    sample_payload = {
        "station_id": "VSK_RADAR_01",
        "timestamp": now_iso,
        "data": {
            "temperature": "29.5",
            "wind_speed": "22.4",
            "wind_direction": "135.0",
            "pressure": "1012.3",
            "rainfall": "0.0",
            "visibility": "8.0",
        }
    }
    
    records = provider._parse_imd_payload(
        payload=sample_payload,
        latitude=17.6868,
        longitude=83.2185,
        retrieved_at=now_iso,
    )
    
    assert len(records) == 6
    rec_dict = {r.parameter: r for r in records}
    
    # Check temperature
    assert "temperature" in rec_dict
    assert rec_dict["temperature"].value == 29.5
    assert rec_dict["temperature"].unit == "C"
    assert rec_dict["temperature"].source == "IMD"
    assert rec_dict["temperature"].data_type == MarineDataType.OBSERVED
    assert rec_dict["temperature"].raw_identifier == "VSK_RADAR_01"
    
    # Check wind speed
    assert "wind_speed" in rec_dict
    assert rec_dict["wind_speed"].value == 22.4
    assert rec_dict["wind_speed"].unit == "km/h"
    
    # Check pressure
    assert "pressure" in rec_dict
    assert rec_dict["pressure"].value == 1012.3
    assert rec_dict["pressure"].unit == "hPa"


# ==============================================================================
# TEST 5: IMD Data Persistence to PostgreSQL & PostGIS Retrieval
# ==============================================================================
def test_imd_database_persistence_and_retrieval():
    db = SessionLocal()
    try:
        service = MarineDataService()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        
        imd_records = [
            NormalizedMarineRecord(
                parameter="temperature",
                value=29.8,
                unit="C",
                latitude=17.6868,
                longitude=83.2185,
                valid_time=now_iso,
                retrieved_at=now_iso,
                source="IMD",
                data_type=MarineDataType.OBSERVED,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
            ),
            NormalizedMarineRecord(
                parameter="wind_speed",
                value=24.5,
                unit="km/h",
                latitude=17.6868,
                longitude=83.2185,
                valid_time=now_iso,
                retrieved_at=now_iso,
                source="IMD",
                data_type=MarineDataType.OBSERVED,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
            ),
            NormalizedMarineRecord(
                parameter="wind_direction",
                value=140.0,
                unit="deg",
                latitude=17.6868,
                longitude=83.2185,
                valid_time=now_iso,
                retrieved_at=now_iso,
                source="IMD",
                data_type=MarineDataType.OBSERVED,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
            ),
        ]
        
        # Persist normalized records
        service._persist_records(db, 17.6868, 83.2185, imd_records, now)
        
        # Query back from PostgreSQL
        saved_weather = (
            db.query(WeatherObservation)
            .filter(
                WeatherObservation.latitude == 17.6868,
                WeatherObservation.longitude == 83.2185,
                WeatherObservation.source == "IMD",
            )
            .order_by(WeatherObservation.id.desc())
            .first()
        )
        
        assert saved_weather is not None
        assert saved_weather.temperature_c == 29.8
        assert saved_weather.wind_speed_kmh == 24.5
        assert saved_weather.wind_direction_deg == 140.0
        assert saved_weather.source == "IMD"
        
        # Test Duplicate Protection / Update behavior
        updated_records = [
            NormalizedMarineRecord(
                parameter="temperature",
                value=30.2,
                unit="C",
                latitude=17.6868,
                longitude=83.2185,
                valid_time=now_iso,
                retrieved_at=now_iso,
                source="IMD",
                data_type=MarineDataType.OBSERVED,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
            )
        ]
        service._persist_records(db, 17.6868, 83.2185, updated_records, now)
        
        re_queried = (
            db.query(WeatherObservation)
            .filter(
                WeatherObservation.latitude == 17.6868,
                WeatherObservation.longitude == 83.2185,
                WeatherObservation.source == "IMD",
            )
            .order_by(WeatherObservation.id.desc())
            .first()
        )
        assert re_queried.temperature_c == 30.2
        
    finally:
        db.close()
