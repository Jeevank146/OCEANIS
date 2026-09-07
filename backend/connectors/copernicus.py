import os
import math
import logging
from datetime import datetime, timezone, timedelta
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


class CopernicusProvider(BaseMarineDataProvider):
    """
    Provider connector for Copernicus Marine Environment Monitoring Service (CMEMS)
    and European Space Agency (ESA) Sentinel Satellite missions.
    
    Supports:
    - CMEMS Global Ocean Physics Analysis and Forecast: Sea Surface Current (uo, vo),
      Sea Surface Temperature (SST), Salinity, Sea Surface Height.
    - Sentinel-3 SLSTR & OLCI: Bio-optical and thermal measurements.
    
    Uses official `copernicusmarine` Python client when username/password credentials
    are provided in configuration, with fallback to REST API endpoints.
    """

    DATASET_CURRENTS = "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m"

    def __init__(
        self,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: int = 20,
    ):
        self.api_key = api_key or os.getenv("COPERNICUS_API_KEY")
        self.username = username or os.getenv("COPERNICUS_USERNAME")
        self.password = password or os.getenv("COPERNICUS_PASSWORD")
        self.base_url = base_url or os.getenv("COPERNICUS_BASE_URL", "https://marine.copernicus.eu/api")
        self.timeout = timeout_seconds
        self._toolbox_authenticated = False

    @property
    def provider_name(self) -> str:
        return "Copernicus Marine"

    @property
    def provider_category(self) -> str:
        return "SATELLITE_EO_AND_BIO_OPTICS"

    @property
    def governing_authority(self) -> str:
        return "Copernicus Marine Service / European Space Agency (ESA)"

    @property
    def is_configured(self) -> bool:
        """
        Returns True if Copernicus credentials (API key or username+password)
        are present.
        """
        has_token = bool(self.api_key and len(self.api_key.strip()) > 0)
        has_userpass = bool(
            self.username
            and len(self.username.strip()) > 0
            and self.password
            and len(self.password.strip()) > 0
        )
        return has_token or has_userpass

    def fetch(self, **kwargs: Any) -> Dict[str, Any]:
        """Legacy BaseDataConnector fetch implementation."""
        lat = kwargs.get("latitude", 0.0)
        lon = kwargs.get("longitude", 0.0)
        res = self.fetch_marine_data(latitude=lat, longitude=lon)
        if res.status != ProviderStatus.HEALTHY and res.status != ProviderStatus.NO_DATA:
            raise requests.RequestException(res.error_message or f"Copernicus error: {res.status}")
        return res.raw_response or {}

    def normalize(self, raw_data: Any) -> Dict[str, Any]:
        """Legacy BaseDataConnector normalize implementation."""
        return {
            "source": self.provider_name,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "data_type": "OBSERVATION_ASSIMILATION",
            "quality_flag": "OPERATIONAL_QUALITY",
            "measurements": raw_data.get("measurements", {}),
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
        Queries Copernicus Marine Service for ocean dynamics and bio-optical data.
        Attempts official copernicusmarine toolbox extraction first when credentials exist.
        """
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Step 1: Check configuration
        if not self.is_configured:
            logger.info("Copernicus provider is not configured with live API credentials.")
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.CONFIGURATION_REQUIRED,
                error_message="Copernicus Marine access requires institutional credentials (COPERNICUS_USERNAME / COPERNICUS_PASSWORD or COPERNICUS_API_KEY).",
                records=[],
                retrieved_at=now_iso,
            )

        # Step 2: Try official copernicusmarine Python Toolbox
        if self.username and self.password:
            try:
                import copernicusmarine
                return self._fetch_via_toolbox(
                    latitude=latitude,
                    longitude=longitude,
                    variables=variables or ["uo", "vo"],
                    now=now,
                )
            except ImportError:
                logger.debug("copernicusmarine package not installed, falling back to REST endpoint.")
            except Exception as e:
                logger.warning(f"Copernicus Toolbox query encountered error: {e}", exc_info=True)
                # If toolbox fails on auth, return AUTH_FAILURE
                if "credentials" in str(e).lower() or "unauthorized" in str(e).lower() or "401" in str(e):
                    return ProviderResponse(
                        provider_name=self.provider_name,
                        status=ProviderStatus.AUTH_FAILURE,
                        error_message="Copernicus Marine authentication failed. Please check credentials.",
                        records=[],
                        retrieved_at=now_iso,
                    )

        # Step 3: REST API Fallback
        return self._fetch_via_rest(latitude=latitude, longitude=longitude, now_iso=now_iso)

    def _fetch_via_toolbox(
        self,
        latitude: float,
        longitude: float,
        variables: List[str],
        now: datetime,
    ) -> ProviderResponse:
        """
        Retrieves real-time ocean current data using official copernicusmarine Python package.
        """
        import copernicusmarine

        now_iso = now.isoformat()
        
        # Authenticate if needed
        try:
            copernicusmarine.login(
                username=self.username,
                password=self.password,
                force_overwrite=True,
            )
            self._toolbox_authenticated = True
        except Exception as auth_err:
            logger.error(f"Copernicus toolbox login failed: {auth_err}")
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.AUTH_FAILURE,
                error_message=f"Copernicus Marine authentication failed: {str(auth_err)}",
                records=[],
                retrieved_at=now_iso,
            )

        # Query a small bounding box around requested point
        delta = 0.15
        min_lon = round(longitude - delta, 4)
        max_lon = round(longitude + delta, 4)
        min_lat = round(latitude - delta, 4)
        max_lat = round(latitude + delta, 4)

        start_date = (now - timedelta(days=2)).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        try:
            df = copernicusmarine.read_dataframe(
                dataset_id=self.DATASET_CURRENTS,
                variables=variables,
                minimum_longitude=min_lon,
                maximum_longitude=max_lon,
                minimum_latitude=min_lat,
                maximum_latitude=max_lat,
                start_datetime=start_date,
                end_datetime=end_date,
                minimum_depth=0.5,
                maximum_depth=1.0,
            )

            if df is None or df.empty:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.NO_DATA,
                    error_message=f"No Copernicus grid cell or observation available for ({latitude}, {longitude}).",
                    records=[],
                    retrieved_at=now_iso,
                )

            # Get the latest timestamp row closest to the requested lat/lon
            df_reset = df.reset_index()
            # Sort by time descending
            if "time" in df_reset.columns:
                df_reset = df_reset.sort_values(by="time", ascending=False)

            # Find closest row by Euclidean distance
            df_reset["dist"] = (df_reset["latitude"] - latitude)**2 + (df_reset["longitude"] - longitude)**2
            closest = df_reset.sort_values(by=["dist"]).iloc[0]

            obs_lat = float(closest["latitude"])
            obs_lon = float(closest["longitude"])
            obs_time = str(closest["time"]) if "time" in closest else now_iso
            
            records: List[NormalizedMarineRecord] = []
            
            uo_val = float(closest["uo"]) if "uo" in closest and not math.isnan(closest["uo"]) else None
            vo_val = float(closest["vo"]) if "vo" in closest and not math.isnan(closest["vo"]) else None

            if uo_val is not None:
                records.append(
                    NormalizedMarineRecord(
                        parameter="ocean_current_u",
                        value=round(uo_val, 4),
                        unit="m/s",
                        latitude=obs_lat,
                        longitude=obs_lon,
                        valid_time=obs_time,
                        retrieved_at=now_iso,
                        source=self.provider_name,
                        data_type=MarineDataType.MODEL,
                        freshness_status=DataFreshnessStatus.FRESH,
                        quality_status=DataQualityStatus.VALIDATED,
                        confidence=0.92,
                        raw_identifier=self.DATASET_CURRENTS,
                        metadata={"variable": "uo", "depth_m": 0.494},
                    )
                )

            if vo_val is not None:
                records.append(
                    NormalizedMarineRecord(
                        parameter="ocean_current_v",
                        value=round(vo_val, 4),
                        unit="m/s",
                        latitude=obs_lat,
                        longitude=obs_lon,
                        valid_time=obs_time,
                        retrieved_at=now_iso,
                        source=self.provider_name,
                        data_type=MarineDataType.MODEL,
                        freshness_status=DataFreshnessStatus.FRESH,
                        quality_status=DataQualityStatus.VALIDATED,
                        confidence=0.92,
                        raw_identifier=self.DATASET_CURRENTS,
                        metadata={"variable": "vo", "depth_m": 0.494},
                    )
                )

            if uo_val is not None and vo_val is not None:
                # Calculate speed and direction
                speed_ms = math.sqrt(uo_val**2 + vo_val**2)
                speed_kmh = round(speed_ms * 3.6, 2)
                # Direction to which current flows (oceanographic convention)
                direction_deg = round((math.atan2(uo_val, vo_val) * 180.0 / math.pi + 360.0) % 360.0, 1)

                records.append(
                    NormalizedMarineRecord(
                        parameter="ocean_current_velocity",
                        value=speed_kmh,
                        unit="km/h",
                        latitude=obs_lat,
                        longitude=obs_lon,
                        valid_time=obs_time,
                        retrieved_at=now_iso,
                        source=self.provider_name,
                        data_type=MarineDataType.MODEL,
                        freshness_status=DataFreshnessStatus.FRESH,
                        quality_status=DataQualityStatus.VALIDATED,
                        confidence=0.92,
                        raw_identifier=self.DATASET_CURRENTS,
                        metadata={"speed_ms": round(speed_ms, 3), "depth_m": 0.494},
                    )
                )

                records.append(
                    NormalizedMarineRecord(
                        parameter="ocean_current_direction",
                        value=direction_deg,
                        unit="deg",
                        latitude=obs_lat,
                        longitude=obs_lon,
                        valid_time=obs_time,
                        retrieved_at=now_iso,
                        source=self.provider_name,
                        data_type=MarineDataType.MODEL,
                        freshness_status=DataFreshnessStatus.FRESH,
                        quality_status=DataQualityStatus.VALIDATED,
                        confidence=0.92,
                        raw_identifier=self.DATASET_CURRENTS,
                        metadata={"depth_m": 0.494},
                    )
                )

            raw_summary = {
                "dataset_id": self.DATASET_CURRENTS,
                "grid_lat": obs_lat,
                "grid_lon": obs_lon,
                "uo": uo_val,
                "vo": vo_val,
                "time": obs_time,
                "samples_count": len(df_reset),
            }

            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.HEALTHY,
                records=records,
                raw_response=raw_summary,
                retrieved_at=now_iso,
            )

        except Exception as e:
            logger.error(f"Copernicus data extraction error: {e}", exc_info=True)
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=f"Copernicus data query failed: {str(e)}",
                records=[],
                retrieved_at=now_iso,
            )

    def _fetch_via_rest(
        self,
        latitude: float,
        longitude: float,
        now_iso: str,
    ) -> ProviderResponse:
        """Fallback REST API point extract."""
        endpoint = f"{self.base_url.rstrip('/')}/v1/point-extract"
        headers = {
            "Accept": "application/json",
            "User-Agent": "OCEANIS-Intelligence-Platform/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        params = {
            "latitude": latitude,
            "longitude": longitude,
        }

        try:
            auth = (self.username, self.password) if (self.username and self.password and not self.api_key) else None
            resp = requests.get(endpoint, headers=headers, auth=auth, params=params, timeout=self.timeout)

            if resp.status_code == 401 or resp.status_code == 403:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.AUTH_FAILURE,
                    error_message=f"Copernicus authentication failed (HTTP {resp.status_code}). Check API credentials.",
                    records=[],
                    retrieved_at=now_iso,
                )
            elif resp.status_code == 404 or resp.status_code == 204:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.NO_DATA,
                    error_message=f"No Copernicus grid cell or satellite coverage for ({latitude}, {longitude}).",
                    records=[],
                    retrieved_at=now_iso,
                )

            resp.raise_for_status()
            payload = resp.json()
            records = self._parse_copernicus_payload(payload, latitude, longitude, now_iso)

            if not records:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.NO_DATA,
                    error_message="Copernicus response contained no valid measurement records.",
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
        except Exception as exc:
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=f"Copernicus REST fallback unavailable: {str(exc)}",
                records=[],
                retrieved_at=now_iso,
            )

    def _parse_copernicus_payload(
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
            "sea_surface_temperature": ("sea_surface_temperature", "C", MarineDataType.MODEL),
            "sst": ("sea_surface_temperature", "C", MarineDataType.MODEL),
            "chlorophyll_a": ("chlorophyll_a", "mg/m3", MarineDataType.MODEL),
            "chl": ("chlorophyll_a", "mg/m3", MarineDataType.MODEL),
            "salinity": ("salinity", "PSU", MarineDataType.MODEL),
            "sea_surface_salinity": ("salinity", "PSU", MarineDataType.MODEL),
            "sea_level_anomaly": ("sea_level_anomaly", "m", MarineDataType.MODEL),
            "current_velocity_u": ("ocean_current_u", "m/s", MarineDataType.MODEL),
            "current_velocity_v": ("ocean_current_v", "m/s", MarineDataType.MODEL),
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
                            confidence=0.88,
                            raw_identifier=payload.get("product_id") or "CMEMS_GLOBAL_ANALYSIS_FORECAST",
                        )
                    )
                except (ValueError, TypeError):
                    continue

        return records
