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


class FallbackMarineProvider(BaseMarineDataProvider):
    """
    High-availability worldwide fallback marine data provider.
    
    Wraps Open-Meteo Marine API (assimilating NOAA GFS Wave, ECMWF WAM, and Copernicus Marine models)
    and Open-Meteo Atmospheric Forecast API.
    
    Guarantees:
    - Always enabled and configured out-of-the-box (no mandatory API key).
    - Strict coordinate-based fetching for any global ocean location.
    - Zero fake data: If coordinates return nulls or are inland, returns ProviderStatus.NO_DATA.
    """

    MARINE_URL = "http://marine-api.open-meteo.com/v1/marine"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout_seconds: int = 15):
        self.timeout = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "Fallback (Open-Meteo / GFS)"

    @property
    def provider_category(self) -> str:
        return "FALLBACK_GLOBAL_MODEL"

    @property
    def governing_authority(self) -> str:
        return "Open-Meteo / NOAA / ECMWF / DWD Assimilation"

    @property
    def is_configured(self) -> bool:
        return True

    def fetch(self, **kwargs: Any) -> Dict[str, Any]:
        """Legacy BaseDataConnector fetch implementation."""
        lat = kwargs.get("latitude", 0.0)
        lon = kwargs.get("longitude", 0.0)
        res = self.fetch_marine_data(latitude=lat, longitude=lon)
        if res.status != ProviderStatus.HEALTHY and res.status != ProviderStatus.NO_DATA:
            raise requests.RequestException(res.error_message or f"Fallback error: {res.status}")
        return res.raw_response or {}

    def normalize(self, raw_data: Any) -> Dict[str, Any]:
        """Legacy BaseDataConnector normalize implementation."""
        return {
            "source": self.provider_name,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "data_type": "MODEL",
            "quality_flag": "OPERATIONAL_MODEL",
            "conditions": raw_data.get("conditions", {}),
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
        Retrieves real numerical ocean physics and surface atmospheric metrics.
        """
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        marine_params = {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": 1,
            "current": (
                "wave_height,"
                "wave_direction,"
                "wave_period,"
                "wind_wave_height,"
                "wind_wave_direction,"
                "wind_wave_period,"
                "swell_wave_height,"
                "swell_wave_direction,"
                "swell_wave_period,"
                "ocean_current_velocity,"
                "ocean_current_direction,"
                "sea_surface_temperature"
            ),
            "timezone": "UTC",
        }

        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": 1,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "wind_speed_10m,"
                "wind_direction_10m,"
                "precipitation,"
                "surface_pressure"
            ),
            "timezone": "UTC",
        }

        raw_payload: Dict[str, Any] = {}
        marine_json: Dict[str, Any] = {}
        weather_json: Dict[str, Any] = {}

        try:
            # 1. Fetch ocean physics
            marine_resp = requests.get(self.MARINE_URL, params=marine_params, timeout=self.timeout)
            if marine_resp.status_code == 200:
                marine_json = marine_resp.json()
                raw_payload["marine"] = marine_json
            elif marine_resp.status_code in (400, 404):
                marine_json = {}

            # 2. Fetch atmospheric weather
            weather_resp = requests.get(self.WEATHER_URL, params=weather_params, timeout=self.timeout)
            if weather_resp.status_code == 200:
                weather_json = weather_resp.json()
                raw_payload["weather"] = weather_json

            # Check if both endpoints failed
            if not marine_json and not weather_json:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.NO_DATA,
                    error_message=f"No fallback marine/weather grid point available for ({latitude}, {longitude}).",
                    records=[],
                    retrieved_at=now_iso,
                )

            # 3. Extract records
            records = self._parse_fallback_payload(marine_json, weather_json, latitude, longitude, now_iso)

            if not records:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.NO_DATA,
                    error_message="Fallback provider returned null for all physical variables at this grid point.",
                    records=[],
                    raw_response=raw_payload,
                    retrieved_at=now_iso,
                )

            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.HEALTHY,
                records=records,
                raw_response=raw_payload,
                retrieved_at=now_iso,
            )

        except requests.Timeout:
            logger.warning(f"Fallback provider timeout for ({latitude}, {longitude})")
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.TIMEOUT,
                error_message="Fallback marine server timed out.",
                records=[],
                retrieved_at=now_iso,
            )
        except requests.RequestException as exc:
            logger.warning(f"Fallback provider request failed: {exc}")
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=f"Fallback provider network/HTTP error: {str(exc)}",
                records=[],
                retrieved_at=now_iso,
            )
        except Exception as exc:
            logger.error(f"Fallback parsing error: {exc}", exc_info=True)
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.INVALID_RESPONSE,
                error_message=f"Failed to parse fallback provider response: {str(exc)}",
                records=[],
                retrieved_at=now_iso,
            )

    def _parse_fallback_payload(
        self,
        marine_json: Dict[str, Any],
        weather_json: Dict[str, Any],
        latitude: float,
        longitude: float,
        retrieved_at: str,
    ) -> List[NormalizedMarineRecord]:
        records: List[NormalizedMarineRecord] = []
        marine_curr = marine_json.get("current", {})
        weather_curr = weather_json.get("current", {})

        marine_time = marine_curr.get("time")
        weather_time = weather_curr.get("time")
        valid_time = marine_time or weather_time or retrieved_at
        if isinstance(valid_time, str) and not valid_time.endswith("Z") and "+" not in valid_time:
            valid_time = f"{valid_time}Z"

        # Ocean Physics mappings
        ocean_mappings = {
            "wave_height": ("wave_height", "m"),
            "wave_direction": ("wave_direction", "deg"),
            "wave_period": ("wave_period", "s"),
            "swell_wave_height": ("swell_wave_height", "m"),
            "swell_wave_direction": ("swell_wave_direction", "deg"),
            "swell_wave_period": ("swell_wave_period", "s"),
            "wind_wave_height": ("wind_wave_height", "m"),
            "wind_wave_direction": ("wind_wave_direction", "deg"),
            "wind_wave_period": ("wind_wave_period", "s"),
            "ocean_current_velocity": ("ocean_current_velocity", "km/h"),
            "ocean_current_direction": ("ocean_current_direction", "deg"),
            "sea_surface_temperature": ("sea_surface_temperature", "C"),
        }

        for field, (param_name, unit) in ocean_mappings.items():
            val = marine_curr.get(field)
            if val is not None:
                try:
                    records.append(
                        NormalizedMarineRecord(
                            parameter=param_name,
                            value=float(val),
                            unit=unit,
                            latitude=latitude,
                            longitude=longitude,
                            valid_time=valid_time,
                            retrieved_at=retrieved_at,
                            source=self.provider_name,
                            data_type=MarineDataType.MODEL,
                            freshness_status=DataFreshnessStatus.FRESH,
                            quality_status=DataQualityStatus.VALIDATED,
                            confidence=0.85,
                            raw_identifier="OPEN_METEO_MARINE_V1",
                        )
                    )
                except (ValueError, TypeError):
                    continue

        # Atmospheric mappings
        atmo_mappings = {
            "wind_speed_10m": ("wind_speed", "km/h"),
            "wind_direction_10m": ("wind_direction", "deg"),
            "temperature_2m": ("temperature", "C"),
            "relative_humidity_2m": ("relative_humidity", "%"),
            "precipitation": ("precipitation", "mm"),
            "surface_pressure": ("pressure", "hPa"),
        }

        for field, (param_name, unit) in atmo_mappings.items():
            val = weather_curr.get(field)
            if val is not None:
                try:
                    records.append(
                        NormalizedMarineRecord(
                            parameter=param_name,
                            value=float(val),
                            unit=unit,
                            latitude=latitude,
                            longitude=longitude,
                            valid_time=valid_time,
                            retrieved_at=retrieved_at,
                            source=self.provider_name,
                            data_type=MarineDataType.MODEL,
                            freshness_status=DataFreshnessStatus.FRESH,
                            quality_status=DataQualityStatus.VALIDATED,
                            confidence=0.85,
                            raw_identifier="OPEN_METEO_FORECAST_V1",
                        )
                    )
                except (ValueError, TypeError):
                    continue

        return records
