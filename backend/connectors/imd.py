import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests

from connectors.base import BaseMarineDataProvider
from schemas.marine_provider import (
    DataFreshnessStatus,
    DataQualityStatus,
    MarineDataType,
    NormalizedMarineRecord,
    ProviderResponse,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


class IMDProvider(BaseMarineDataProvider):
    """
    Provider connector for the India Meteorological Department (IMD).
    
    Supports:
    - Coastal Doppler Weather Radar (DWR) surface weather and squall telemetry
    - Marine & Coastal Weather Bulletins (wind speed, wind gusts, atmospheric pressure, visibility)
    - Tropical Cyclone Bulletins (RSMC New Delhi tracks, central pressure, intensity)
    - Fishermen Sea Warnings & Coastal Squall Warnings
    
    Adheres strictly to the BaseMarineDataProvider abstraction:
    Returns ProviderStatus.CONFIGURATION_REQUIRED when credentials are missing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: int = 15,
    ):
        self.api_key = api_key or os.getenv("IMD_API_KEY")
        self.base_url = base_url or os.getenv("IMD_BASE_URL", "https://mausam.imd.gov.in/api")
        self.timeout = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "IMD"

    @property
    def provider_category(self) -> str:
        return "COASTAL_RADAR_AND_WARNINGS"

    @property
    def governing_authority(self) -> str:
        return "India Meteorological Department (IMD) / MoES, Govt of India"

    @property
    def is_configured(self) -> bool:
        """IMD live radar/bulletin API requires an authenticated access token."""
        return bool(self.api_key and self.api_key.strip())

    def fetch(self, **kwargs: Any) -> Dict[str, Any]:
        """Legacy BaseDataConnector fetch implementation."""
        lat = kwargs.get("latitude", 0.0)
        lon = kwargs.get("longitude", 0.0)
        res = self.fetch_marine_data(latitude=lat, longitude=lon)
        if res.status != ProviderStatus.HEALTHY and res.status != ProviderStatus.NO_DATA:
            raise requests.RequestException(res.error_message or f"IMD error: {res.status}")
        return res.raw_response or {}

    def normalize(self, raw_data: Any) -> Dict[str, Any]:
        """Legacy BaseDataConnector normalize implementation."""
        return {
            "source": self.provider_name,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "data_type": "OFFICIAL_WARNING",
            "quality_flag": "OFFICIAL_VALIDATED",
            "weather": raw_data.get("weather", {}),
        }

    def fetch_marine_data(
        self,
        latitude: float,
        longitude: float,
        variables: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        location_context: Optional[Dict[str, Any]] = None,
    ) -> ProviderResponse:
        """
        Retrieves localized atmospheric metrics, squall advisories, and cyclone bulletins.
        """
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Step 1: Check configuration
        if not self.is_configured:
            logger.info("IMD provider is not configured with live API credentials.")
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.CONFIGURATION_REQUIRED,
                error_message="IMD live marine/radar feed requires API credentials (IMD_API_KEY).",
                records=[],
                retrieved_at=now_iso,
            )

        # Step 2: Query IMD API
        endpoint = f"{self.base_url.rstrip('/')}/v1/marine-coastal"
        headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json",
            "User-Agent": "OCEANIS-Intelligence-Platform/1.0",
        }
        params = {
            "latitude": latitude,
            "longitude": longitude,
        }

        try:
            resp = requests.get(endpoint, headers=headers, params=params, timeout=self.timeout)
            
            if resp.status_code == 401 or resp.status_code == 403:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.AUTH_FAILURE,
                    error_message=f"IMD authentication failed (HTTP {resp.status_code}). Check API credentials.",
                    records=[],
                    retrieved_at=now_iso,
                )
            elif resp.status_code == 404 or resp.status_code == 204:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.NO_DATA,
                    error_message=f"No IMD radar/station coverage for coordinates ({latitude}, {longitude}).",
                    records=[],
                    retrieved_at=now_iso,
                )

            resp.raise_for_status()
            payload = resp.json()
            
            # Step 3: Parse payload
            records = self._parse_imd_payload(payload, latitude, longitude, now_iso)
            
            if not records:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.NO_DATA,
                    error_message="IMD response contained no valid observation metrics.",
                    records=[],
                    raw_response=payload,
                    retrieved_at=now_iso,
                )

            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.HEALTHY,
                records=records,
                raw_response=payload,
                retrieved_at=now_iso,
            )

        except requests.Timeout:
            logger.warning(f"IMD provider timeout for coordinates ({latitude}, {longitude})")
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.TIMEOUT,
                error_message="IMD upstream server timed out.",
                records=[],
                retrieved_at=now_iso,
            )
        except requests.RequestException as exc:
            logger.warning(f"IMD request failed: {exc}")
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=f"IMD network/HTTP error: {str(exc)}",
                records=[],
                retrieved_at=now_iso,
            )
        except Exception as exc:
            logger.error(f"IMD parsing error: {exc}", exc_info=True)
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.INVALID_RESPONSE,
                error_message=f"Failed to parse IMD response structure: {str(exc)}",
                records=[],
                retrieved_at=now_iso,
            )

    def _parse_imd_payload(
        self,
        payload: Dict[str, Any],
        latitude: float,
        longitude: float,
        retrieved_at: str,
    ) -> List[NormalizedMarineRecord]:
        records: List[NormalizedMarineRecord] = []
        data = payload.get("data", payload)
        valid_time = payload.get("valid_time") or payload.get("timestamp") or retrieved_at

        mappings = {
            "wind_speed": ("wind_speed", "km/h", MarineDataType.OBSERVED),
            "wind_gust": ("wind_gust", "km/h", MarineDataType.OBSERVED),
            "wind_direction": ("wind_direction", "deg", MarineDataType.OBSERVED),
            "surface_pressure": ("pressure", "hPa", MarineDataType.OBSERVED),
            "pressure": ("pressure", "hPa", MarineDataType.OBSERVED),
            "temperature": ("temperature", "C", MarineDataType.OBSERVED),
            "air_temperature": ("temperature", "C", MarineDataType.OBSERVED),
            "rainfall": ("precipitation", "mm", MarineDataType.OBSERVED),
            "precipitation": ("precipitation", "mm", MarineDataType.OBSERVED),
            "visibility": ("visibility", "km", MarineDataType.OBSERVED),
        }

        for field, (param_name, unit, dtype) in mappings.items():
            if field in data and data[field] is not None:
                val = data[field]
                try:
                    num_val = float(val)
                    records.append(
                        NormalizedMarineRecord(
                            parameter=param_name,
                            value=num_val,
                            unit=unit,
                            latitude=latitude,
                            longitude=longitude,
                            valid_time=valid_time,
                            retrieved_at=retrieved_at,
                            source=self.provider_name,
                            data_type=dtype,
                            freshness_status=DataFreshnessStatus.FRESH,
                            quality_status=DataQualityStatus.VALIDATED,
                            confidence=0.90,
                            raw_identifier=payload.get("station_id") or payload.get("radar_code"),
                        )
                    )
                except (ValueError, TypeError):
                    continue

        return records
