from datetime import datetime, timezone, timedelta
from typing import Any, Dict
import pytest
import requests
from unittest.mock import MagicMock, patch


from connectors.base import BaseMarineDataProvider
from connectors.copernicus import CopernicusProvider
from connectors.fallback import FallbackMarineProvider
from connectors.imd import IMDProvider
from connectors.incois import INCOISProvider
from database import SessionLocal
from models.marine import MarineObservation
from schemas.marine_provider import (
    DataFreshnessStatus,
    DataQualityStatus,
    MarineDataType,
    NormalizedMarineRecord,
    ProviderHealthResponse,
    ProviderResponse,
    ProviderStatus,
)
from services.freshness import (
    FreshnessCategory,
    evaluate_freshness,
    evaluate_parameter_freshness,
)
from services.marine_data import MarineDataService
from services.validation import DataValidator, PHYSICAL_BOUNDS


# ==============================================================================
# TEST 1: Provider Interface Compliance
# ==============================================================================
def test_provider_interface_compliance():
    providers = [
        INCOISProvider(),
        IMDProvider(),
        CopernicusProvider(),
        FallbackMarineProvider(),
    ]

    for p in providers:
        assert isinstance(p, BaseMarineDataProvider)
        assert isinstance(p.provider_name, str) and len(p.provider_name) > 0
        assert isinstance(p.provider_category, str)
        assert isinstance(p.governing_authority, str)
        assert isinstance(p.is_configured, bool)

        health: ProviderHealthResponse = p.check_health()
        assert health.name == p.provider_name
        assert health.status in ProviderStatus


# ==============================================================================
# TEST 2: Normalized Marine Data Structure & Metadata
# ==============================================================================
def test_normalized_marine_data_structure():
    now_iso = datetime.now(timezone.utc).isoformat()
    record = NormalizedMarineRecord(
        parameter="wave_height",
        value=1.85,
        unit="m",
        latitude=16.9891,
        longitude=82.2475,
        valid_time=now_iso,
        retrieved_at=now_iso,
        source="INCOIS",
        data_type=MarineDataType.OBSERVED,
        freshness_status=DataFreshnessStatus.FRESH,
        quality_status=DataQualityStatus.VALIDATED,
        confidence=0.95,
        raw_identifier="BUOY_BD09",
    )

    assert record.parameter == "wave_height"
    assert record.value == 1.85
    assert record.unit == "m"
    assert record.source == "INCOIS"
    assert record.data_type == MarineDataType.OBSERVED
    assert record.quality_status == DataQualityStatus.VALIDATED
    assert record.confidence == 0.95


# ==============================================================================
# TEST 3: Coordinate Validation
# ==============================================================================
def test_coordinate_validation():
    # Valid coordinates
    valid, err = DataValidator.validate_coordinates(16.9891, 82.2475)
    assert valid is True
    assert err is None

    # Invalid latitude
    valid, err = DataValidator.validate_coordinates(95.0, 82.2475)
    assert valid is False
    assert "Latitude" in err

    # Invalid longitude
    valid, err = DataValidator.validate_coordinates(16.9891, -195.0)
    assert valid is False
    assert "Longitude" in err

    # Non-numeric
    valid, err = DataValidator.validate_coordinates("invalid", 82.2475)  # type: ignore
    assert valid is False


# ==============================================================================
# TEST 4: Physical Numerical Range Validation
# ==============================================================================
def test_numerical_range_validation():
    # Valid wave height
    valid, err = DataValidator.validate_numerical_range("wave_height", 2.4, "m")
    assert valid is True
    assert err is None

    # Impossible wave height (e.g. 50m)
    valid, err = DataValidator.validate_numerical_range("wave_height", 50.0, "m")
    assert valid is False
    assert "Physical range violation" in err

    # Impossible SST (e.g. 60°C)
    valid, err = DataValidator.validate_numerical_range("sea_surface_temperature", 60.0, "C")
    assert valid is False

    # Impossible wind speed (e.g. 500 km/h)
    valid, err = DataValidator.validate_numerical_range("wind_speed", 500.0, "km/h")
    assert valid is False

    # NaN / Inf detection
    valid, err = DataValidator.validate_numerical_range("wave_height", float("nan"), "m")
    assert valid is False


# ==============================================================================
# TEST 5: Timestamp Validation
# ==============================================================================
def test_timestamp_validation():
    now_iso = datetime.now(timezone.utc).isoformat()
    valid, dt, err = DataValidator.validate_timestamp(now_iso)
    assert valid is True
    assert dt is not None
    assert err is None

    # Invalid timestamp string
    valid, dt, err = DataValidator.validate_timestamp("not-a-timestamp")
    assert valid is False
    assert "Invalid ISO 8601" in err

    # Ancient timestamp (> 30 days old)
    ancient = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    valid, dt, err = DataValidator.validate_timestamp(ancient)
    assert valid is False
    assert "older than" in err


# ==============================================================================
# TEST 6: Parameter-Specific Freshness Calculation
# ==============================================================================
def test_parameter_specific_freshness():
    now = datetime.now(timezone.utc)

    # 1. High frequency wave buoy (age = 2 hours) -> AGING for buoy
    buoy_2h = now - timedelta(hours=2)
    buoy_freshness = evaluate_parameter_freshness(buoy_2h, parameter="wave_height", provider="INCOIS", current_time=now)
    assert buoy_freshness == DataFreshnessStatus.AGING

    # 2. Satellite EO product (age = 18 hours) -> FRESH for satellite pass
    sat_18h = now - timedelta(hours=18)
    sat_freshness = evaluate_parameter_freshness(sat_18h, parameter="chlorophyll_a", provider="Copernicus", current_time=now)
    assert sat_freshness == DataFreshnessStatus.FRESH

    # 3. Forecast model (age = 10 hours) -> STALE
    model_10h = now - timedelta(hours=10)
    model_freshness = evaluate_parameter_freshness(model_10h, parameter="wave_height", provider="Fallback", current_time=now)
    assert model_freshness == DataFreshnessStatus.STALE


# ==============================================================================
# TEST 7: Provider Failure Handling (No Fake Data)
# ==============================================================================
def test_provider_failure_handling():
    # 1. INCOIS Provider: Disabled/unconfigured provider returns CONFIGURATION_REQUIRED
    incois_disabled = INCOISProvider()
    incois_disabled.enabled = False
    assert incois_disabled.is_configured is False
    resp_incois = incois_disabled.fetch_marine_data(latitude=16.9891, longitude=82.2475)
    assert resp_incois.status == ProviderStatus.CONFIGURATION_REQUIRED
    assert len(resp_incois.records) == 0

    # 2. INCOIS Provider: Extraction/network exception returns UNAVAILABLE
    incois_enabled = INCOISProvider()
    incois_enabled.enabled = True
    with patch.object(incois_enabled, "_fetch_from_rsmc_netcdf", side_effect=requests.RequestException("INCOIS RSMC network connection failed")):
        err_resp_incois = incois_enabled.fetch_marine_data(latitude=16.9891, longitude=82.2475)
        assert err_resp_incois.status == ProviderStatus.UNAVAILABLE
        assert len(err_resp_incois.records) == 0

    # 3. IMD Provider: Unconfigured provider (missing key) returns CONFIGURATION_REQUIRED
    imd_unconfigured = IMDProvider(api_key="   ")
    resp_imd = imd_unconfigured.fetch_marine_data(latitude=16.9891, longitude=82.2475)
    assert resp_imd.status == ProviderStatus.CONFIGURATION_REQUIRED
    assert len(resp_imd.records) == 0

    # 4. IMD Provider: Upstream 502 error returns UNAVAILABLE
    imd_cfg = IMDProvider(api_key="mock_valid_token")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 502
        mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("502 Bad Gateway")
        err_resp_imd = imd_cfg.fetch_marine_data(latitude=16.9891, longitude=82.2475)
        assert err_resp_imd.status == ProviderStatus.UNAVAILABLE
        assert len(err_resp_imd.records) == 0


# ==============================================================================
# TEST 8: Missing Data Handling
# ==============================================================================
def test_missing_data_handling():
    # 1. INCOIS Provider: Masked/land grid point or empty extraction returns NO_DATA
    incois_provider = INCOISProvider()
    with patch.object(incois_provider, "_fetch_from_rsmc_netcdf", return_value=([], {})):
        resp_incois = incois_provider.fetch_marine_data(latitude=16.9891, longitude=82.2475)
        assert resp_incois.status == ProviderStatus.NO_DATA
        assert len(resp_incois.records) == 0

    # 2. IMD Provider: 404 endpoint returns NO_DATA
    imd_cfg = IMDProvider(api_key="mock_valid_token")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        resp_imd = imd_cfg.fetch_marine_data(latitude=16.9891, longitude=82.2475)
        assert resp_imd.status == ProviderStatus.NO_DATA
        assert len(resp_imd.records) == 0


# ==============================================================================
# TEST 9: Invalid Provider Response Handling
# ==============================================================================
def test_invalid_provider_response_handling():
    # 1. INCOIS Provider: RSMC extraction unexpected error returns UNAVAILABLE
    incois_provider = INCOISProvider()
    with patch.object(incois_provider, "_fetch_from_rsmc_netcdf", side_effect=RuntimeError("Corrupted NetCDF structure")):
        resp_incois = incois_provider.fetch_marine_data(latitude=16.9891, longitude=82.2475)
        assert resp_incois.status == ProviderStatus.UNAVAILABLE
        assert len(resp_incois.records) == 0

    # 2. IMD Provider: Malformed JSON returns INVALID_RESPONSE
    imd_cfg = IMDProvider(api_key="mock_valid_token")
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = ValueError("Malformed JSON string")
        resp_imd = imd_cfg.fetch_marine_data(latitude=16.9891, longitude=82.2475)
        assert resp_imd.status == ProviderStatus.INVALID_RESPONSE
        assert len(resp_imd.records) == 0


# ==============================================================================
# TEST 10: Database Persistence with Validation
# ==============================================================================
def test_database_persistence_with_validation():
    db = SessionLocal()
    try:
        service = MarineDataService()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        records = [
            NormalizedMarineRecord(
                parameter="wave_height",
                value=1.45,
                unit="m",
                latitude=17.6868,
                longitude=83.2185,
                valid_time=now_iso,
                retrieved_at=now_iso,
                source="Fallback (Open-Meteo / GFS)",
                data_type=MarineDataType.MODEL,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
            ),
            NormalizedMarineRecord(
                parameter="sea_surface_temperature",
                value=28.2,
                unit="C",
                latitude=17.6868,
                longitude=83.2185,
                valid_time=now_iso,
                retrieved_at=now_iso,
                source="Fallback (Open-Meteo / GFS)",
                data_type=MarineDataType.MODEL,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
            ),
        ]

        service._persist_records(db, 17.6868, 83.2185, records, now)

        # Query back from DB
        obs = (
            db.query(MarineObservation)
            .filter(MarineObservation.latitude == 17.6868, MarineObservation.longitude == 83.2185)
            .order_by(MarineObservation.id.desc())
            .first()
        )
        assert obs is not None
        assert obs.wave_height_m == 1.45
        assert obs.sea_surface_temperature_c == 28.2
    finally:
        db.close()


# ==============================================================================
# TEST 11: Marine Intelligence API Multi-Source Response
# ==============================================================================
def test_marine_intelligence_service_multi_source():
    # Mock fallback provider
    mock_fallback = MagicMock(spec=FallbackMarineProvider)
    now_iso = datetime.now(timezone.utc).isoformat()
    mock_fallback.provider_name = "Fallback (Open-Meteo / GFS)"
    mock_fallback.fetch_marine_data.return_value = ProviderResponse(
        provider_name="Fallback (Open-Meteo / GFS)",
        status=ProviderStatus.HEALTHY,
        records=[
            NormalizedMarineRecord(
                parameter="wave_height",
                value=1.6,
                unit="m",
                latitude=17.6868,
                longitude=83.2185,
                valid_time=now_iso,
                retrieved_at=now_iso,
                source="Fallback (Open-Meteo / GFS)",
                data_type=MarineDataType.MODEL,
                freshness_status=DataFreshnessStatus.FRESH,
                quality_status=DataQualityStatus.VALIDATED,
            )
        ],
    )

    service = MarineDataService(providers={"Fallback": mock_fallback})
    res = service.fetch_marine_intelligence(
        latitude=17.6868,
        longitude=83.2185,
        location_name="Visakhapatnam Coast",
        save_to_db=False,
    )

    assert res.is_coastal is True
    assert res.latitude == 17.6868
    assert res.longitude == 83.2185
    assert len(res.records) >= 1
    assert res.records[0].parameter == "wave_height"
    assert res.records[0].value == 1.6
    assert res.records[0].source == "Fallback (Open-Meteo / GFS)"


# ==============================================================================
# TEST 12: Source Provenance Preservation
# ==============================================================================
def test_source_provenance_preservation():
    now_iso = datetime.now(timezone.utc).isoformat()
    
    incois_rec = NormalizedMarineRecord(
        parameter="wave_height",
        value=1.8,
        unit="m",
        latitude=16.9891,
        longitude=82.2475,
        valid_time=now_iso,
        retrieved_at=now_iso,
        source="INCOIS",
        data_type=MarineDataType.OBSERVED,
        freshness_status=DataFreshnessStatus.FRESH,
        quality_status=DataQualityStatus.VALIDATED,
    )

    fallback_rec = NormalizedMarineRecord(
        parameter="wave_height",
        value=1.5,
        unit="m",
        latitude=16.9891,
        longitude=82.2475,
        valid_time=now_iso,
        retrieved_at=now_iso,
        source="Fallback (Open-Meteo / GFS)",
        data_type=MarineDataType.MODEL,
        freshness_status=DataFreshnessStatus.FRESH,
        quality_status=DataQualityStatus.VALIDATED,
    )

    # Provenance retains individual source attribution and data types
    assert incois_rec.source == "INCOIS"
    assert incois_rec.data_type == MarineDataType.OBSERVED
    assert incois_rec.value == 1.8

    assert fallback_rec.source == "Fallback (Open-Meteo / GFS)"
    assert fallback_rec.data_type == MarineDataType.MODEL
    assert fallback_rec.value == 1.5


# ==============================================================================
# TEST 13: Demo / Seed Data Isolation (Inland Blocking)
# ==============================================================================
def test_demo_data_isolation_inland():
    service = MarineDataService()
    # New Delhi (Inland)
    res = service.fetch_marine_intelligence(
        latitude=28.6139,
        longitude=77.2090,
        location_name="New Delhi",
        save_to_db=False,
    )

    # Must be blocked: no fake wave numbers
    assert res.is_coastal is False
    assert len(res.records) == 0
    assert len(res.warnings) > 0
    assert "Inland location detected" in res.warnings[0]


# ==============================================================================
# TEST 14: Agent Consumption of Normalized Data
# ==============================================================================
def test_agent_consumption_of_normalized_data():
    from agents.marine_conditions.agent import MarineConditionsIntelligenceAgent
    from agents.marine_conditions.schemas import MarineConditionsQuery

    db = SessionLocal()
    try:
        agent = MarineConditionsIntelligenceAgent()
        query = MarineConditionsQuery(latitude=17.6868, longitude=83.2185)
        assessment = agent.assess(db=db, query=query)

        assert assessment.agent == "marine_conditions"
        assert assessment.location["latitude"] == 17.6868
        assert assessment.sea_state is not None
        assert assessment.risk_level in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    finally:
        db.close()
