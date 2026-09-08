import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from connectors.base import BaseMarineDataProvider
from models.weather import WeatherObservation
from schemas.marine_provider import (
    DataFreshnessStatus,
    DataQualityStatus,
    MarineDataType,
    NormalizedMarineRecord,
    ProviderResponse,
    ProviderStatus,
)

logger = logging.getLogger(__name__)

# Ensure backend .env is loaded if present
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


class IMDProvider(BaseMarineDataProvider):
    """
    Official India Meteorological Department (IMD) API Connector.
    Supports official IMD API Portal JWT Bearer authentication and X-API-KEY headers.
    Provides localized coastal weather, Doppler radar observations, and cyclonic alerts.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        if api_key is None and jwt_token is None:
            self.api_key = os.getenv("IMD_API_KEY", "").strip()
            self.jwt_token = os.getenv("IMD_JWT_TOKEN", "").strip()
        else:
            self.api_key = (api_key or "").strip()
            self.jwt_token = (jwt_token or "").strip()
        self.base_url = base_url or os.getenv("IMD_BASE_URL", "https://api.imd.gov.in/api")
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "IMD"

    @property
    def provider_category(self) -> str:
        return "WEATHER_RADAR_AND_ATMOSPHERE"

    @property
    def governing_authority(self) -> str:
        return "India Meteorological Department (IMD) / MoES"

    @property
    def is_configured(self) -> bool:
        """IMD live radar/bulletin API requires an API key or JWT token."""
        return bool(self.api_key and self.api_key.strip()) or bool(self.jwt_token and self.jwt_token.strip())

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Constructs the official IMD API Portal authentication headers:
        - Authorization: Bearer <JWT_TOKEN>
        - X-API-KEY: <API_KEY>
        """
        headers = {
            "Accept": "application/json",
            "User-Agent": "OCEANIS-Intelligence-Platform/1.0",
        }
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        return headers

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
        weather_data = raw_data
        if isinstance(raw_data, dict):
            weather_data = raw_data.get("weather", raw_data)
        elif isinstance(raw_data, list) and len(raw_data) > 0:
            weather_data = raw_data[0]
        return {
            "source": self.provider_name,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "data_type": "OFFICIAL_WARNING",
            "quality_flag": "OFFICIAL_VALIDATED",
            "weather": weather_data,
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
        Retrieves localized atmospheric metrics, squall advisories, and cyclone bulletins
        using official IMD JWT Bearer and API key authentication.
        """
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Step 1: Check configuration
        if not self.is_configured:
            logger.info("IMD provider is not configured with live API credentials.")
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.CONFIGURATION_REQUIRED,
                error_message="IMD live marine/radar feed requires API credentials (IMD_API_KEY / IMD_JWT_TOKEN).",
                records=[],
                retrieved_at=now_iso,
            )

        # Step 2: Query IMD API
        endpoint = f"{self.base_url.rstrip('/')}/v1/marine-coastal"
        headers = self.get_auth_headers()
        params = {
            "latitude": latitude,
            "longitude": longitude,
        }

        try:
            resp = requests.get(endpoint, headers=headers, params=params, timeout=self.timeout)
            resp_text_lower = resp.text.lower()
            
            # Check for server IP whitelisting restrictions
            if resp.status_code == 403 and ("ip" in resp_text_lower and ("whitelist" in resp_text_lower or "allow" in resp_text_lower or "denied" in resp_text_lower)):
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.AUTH_FAILURE,
                    error_message=f"IMD server IP restriction: Server public IP is not whitelisted on IMD API portal (HTTP {resp.status_code}).",
                    records=[],
                    retrieved_at=now_iso,
                )

            # Check for JWT / API key authentication / authorization failures
            if resp.status_code in (401, 403) or (
                resp.status_code == 400 and ("unauthor" in resp_text_lower or "jwt" in resp_text_lower or "invalid" in resp_text_lower or "token" in resp_text_lower)
            ):
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.AUTH_FAILURE,
                    error_message=f"IMD authentication failed (HTTP {resp.status_code}): {resp.text.strip()}",
                    records=[],
                    retrieved_at=now_iso,
                )
            elif resp.status_code in (404, 204):
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
        payload: Any,
        latitude: float,
        longitude: float,
        retrieved_at: str,
    ) -> List[NormalizedMarineRecord]:
        records: List[NormalizedMarineRecord] = []
        if isinstance(payload, list):
            data = payload[0] if payload else {}
            valid_time = retrieved_at
            raw_id = data.get("Station Id") or data.get("Station")
        elif isinstance(payload, dict):
            data = payload.get("data", payload)
            valid_time = payload.get("valid_time") or payload.get("timestamp") or retrieved_at
            raw_id = payload.get("station_id") or payload.get("radar_code") or data.get("Station Id")
        else:
            data = {}
            valid_time = retrieved_at
            raw_id = None

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
            "humidity": ("humidity", "%", MarineDataType.OBSERVED),
            "relative_humidity": ("humidity", "%", MarineDataType.OBSERVED),
            "Temperature": ("temperature", "C", MarineDataType.OBSERVED),
            "Humidity": ("humidity", "%", MarineDataType.OBSERVED),
            "Wind Speed KMPH": ("wind_speed", "km/h", MarineDataType.OBSERVED),
            "Wind Direction": ("wind_direction", "deg", MarineDataType.OBSERVED),
            "Last 24 hrs Rainfall": ("precipitation", "mm", MarineDataType.OBSERVED),
            "Mean Sea Level Pressure": ("pressure", "hPa", MarineDataType.OBSERVED),
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
                            raw_identifier=raw_id,
                        )
                    )
                except (ValueError, TypeError):
                    continue

        return records

    def persist_weather_observation(
        self,
        db: Session,
        records: List[NormalizedMarineRecord],
        latitude: float,
        longitude: float,
        observed_at: Optional[datetime] = None,
    ) -> Optional[WeatherObservation]:
        """
        Persists normalized atmospheric records from IMD into the PostgreSQL weather_observations table.
        """
        if not records:
            return None

        dt = observed_at or datetime.now(timezone.utc)
        metrics: Dict[str, float] = {}
        for r in records:
            metrics[r.parameter] = r.value

        obs = WeatherObservation(
            latitude=latitude,
            longitude=longitude,
            observed_at=dt,
            temperature_c=metrics.get("temperature"),
            humidity_percent=metrics.get("humidity"),
            wind_speed_kmh=metrics.get("wind_speed"),
            wind_direction_deg=metrics.get("wind_direction"),
            precipitation_mm=metrics.get("precipitation"),
            source=self.provider_name,
            source_timezone="Asia/Kolkata",
        )

        try:
            db.add(obs)
            db.commit()
            db.refresh(obs)
            return obs
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to persist IMD weather observation: {exc}")
            raise
