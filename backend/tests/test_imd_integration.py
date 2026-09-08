import os
from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock, patch
import requests

from database import SessionLocal
from connectors.imd import IMDProvider
from models.weather import WeatherObservation
from schemas.marine_provider import (
    DataFreshnessStatus,
    DataQualityStatus,
    MarineDataType,
    NormalizedMarineRecord,
    ProviderResponse,
    ProviderStatus,
)


def test_imd_environment_configuration():
    """Verify that IMDProvider correctly loads configuration from env or constructor."""
    provider = IMDProvider(api_key="mock_test_key", jwt_token="mock_test_jwt")
    assert provider.is_configured is True
    assert provider.provider_name == "IMD"
    assert "Authorization" in provider.get_auth_headers()
    assert "X-API-KEY" in provider.get_auth_headers()


def test_imd_auth_headers_generation():
    """Verify that Authorization: Bearer <JWT> and X-API-KEY headers are generated."""
    provider = IMDProvider(api_key="secret_key_123", jwt_token="jwt_token_456")
    headers = provider.get_auth_headers()
    
    assert headers["Authorization"] == "Bearer jwt_token_456"
    assert headers["X-API-KEY"] == "secret_key_123"
    assert headers["Accept"] == "application/json"


def test_imd_jwt_invalid_or_expired_handling():
    """Verify that 401 Invalid or expired JWT token is properly handled as AUTH_FAILURE."""
    provider = IMDProvider(api_key="mock_key", jwt_token="mock_jwt")

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = '{"error":"Invalid or expired JWT token"}'

    with patch("requests.get", return_value=mock_resp):
        res = provider.fetch_marine_data(latitude=17.6868, longitude=83.2185)
        assert res.status == ProviderStatus.AUTH_FAILURE
        assert "authentication failed" in res.error_message.lower()
        assert len(res.records) == 0


def test_imd_ip_whitelisting_detection():
    """Verify that 403 server IP restriction is detected and reported clearly."""
    provider = IMDProvider(api_key="mock_key", jwt_token="mock_jwt")

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = '{"error":"Server IP not allowed / IP not in whitelist"}'

    with patch("requests.get", return_value=mock_resp):
        res = provider.fetch_marine_data(latitude=17.6868, longitude=83.2185)
        assert res.status == ProviderStatus.AUTH_FAILURE
        assert "ip" in res.error_message.lower()
        assert "whitelist" in res.error_message.lower() or "restriction" in res.error_message.lower()


def test_imd_payload_normalization():
    """Verify that IMD observation JSON is accurately normalized into NormalizedMarineRecord list."""
    provider = IMDProvider(api_key="mock_key", jwt_token="mock_jwt")

    sample_payload = {
        "station_id": "IMD_VSK_01",
        "valid_time": "2026-09-07T12:00:00Z",
        "data": {
            "temperature": 29.5,
            "humidity": 78.0,
            "wind_speed": 22.4,
            "wind_direction": 140.0,
            "surface_pressure": 1011.2,
            "rainfall": 1.5,
            "visibility": 10.0,
        }
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = sample_payload

    with patch("requests.get", return_value=mock_resp):
        res = provider.fetch_marine_data(latitude=17.6868, longitude=83.2185)
        assert res.status == ProviderStatus.HEALTHY
        assert len(res.records) >= 6

        param_dict = {r.parameter: r.value for r in res.records}
        assert param_dict["temperature"] == 29.5
        assert param_dict["humidity"] == 78.0
        assert param_dict["wind_speed"] == 22.4
        assert param_dict["pressure"] == 1011.2
        assert param_dict["precipitation"] == 1.5


def test_imd_database_persistence_and_retrieval():
    """Verify that normalized IMD records persist to the PostgreSQL weather_observations table."""
    db = SessionLocal()
    try:
        provider = IMDProvider(api_key="mock_key", jwt_token="mock_jwt")

        records = [
            NormalizedMarineRecord(
                parameter="temperature",
                value=28.5,
                unit="C",
                latitude=17.6868,
                longitude=83.2185,
                valid_time="2026-09-07T12:00:00Z",
                retrieved_at="2026-09-07T12:05:00Z",
                source="IMD",
                data_type=MarineDataType.OBSERVED,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
                confidence=0.90,
            ),
            NormalizedMarineRecord(
                parameter="humidity",
                value=80.0,
                unit="%",
                latitude=17.6868,
                longitude=83.2185,
                valid_time="2026-09-07T12:00:00Z",
                retrieved_at="2026-09-07T12:05:00Z",
                source="IMD",
                data_type=MarineDataType.OBSERVED,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
                confidence=0.90,
            ),
            NormalizedMarineRecord(
                parameter="wind_speed",
                value=18.0,
                unit="km/h",
                latitude=17.6868,
                longitude=83.2185,
                valid_time="2026-09-07T12:00:00Z",
                retrieved_at="2026-09-07T12:05:00Z",
                source="IMD",
                data_type=MarineDataType.OBSERVED,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
                confidence=0.90,
            ),
        ]

        obs = provider.persist_weather_observation(
            db=db,
            records=records,
            latitude=17.6868,
            longitude=83.2185,
        )

        assert obs is not None
        assert obs.id is not None
        assert obs.source == "IMD"
        assert obs.temperature_c == 28.5
        assert obs.humidity_percent == 80.0
        assert obs.wind_speed_kmh == 18.0

        # Query back from DB
        db_obs = db.query(WeatherObservation).filter(WeatherObservation.id == obs.id).first()
        assert db_obs is not None
        assert db_obs.temperature_c == 28.5
    finally:
        db.close()


def test_imd_real_api_request_status():
    """
    Makes a live call to the configured IMD API endpoint using dynamic user coordinates.
    Validates that the connector gracefully receives and classifies the server response
    (e.g., AUTH_FAILURE if JWT needs activation on portal, or HEALTHY if live).
    """
    provider = IMDProvider()
    if not provider.is_configured:
        pytest.skip("IMD credentials not configured in environment.")

    # Use dynamic coastal testing coordinates (e.g. 17.6868, 83.2185)
    lat, lon = 17.6868, 83.2185
    res = provider.fetch_marine_data(latitude=lat, longitude=lon)

    assert isinstance(res, ProviderResponse)
    assert res.provider_name == "IMD"
    assert res.status in (
        ProviderStatus.HEALTHY,
        ProviderStatus.AUTH_FAILURE,
        ProviderStatus.NO_DATA,
        ProviderStatus.UNAVAILABLE,
        ProviderStatus.TIMEOUT,
    )
