import os
import re
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
import requests
import numpy as np

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


class INCOISProvider(BaseMarineDataProvider):
    """
    Official data provider connector for the Indian National Centre for Ocean Information
    Services (INCOIS), Ministry of Earth Sciences (MoES), Government of India.
    
    Accesses official INCOIS RSMC (Regional Specialized Meteorological Centre)
    operational Ocean State Forecast NetCDF streams:
    - RSMC HYCOM Ocean Model: Surface Currents (UVEL, VVEL), Sea Surface Temperature (TEMP),
      Sea Surface Salinity (SALN), Sea Surface Height (SSH), Mixed Layer Depth (MLD).
    - RSMC WW3 Wave Model: Significant Wave Height (HS), Mean Wave Direction (MWD),
      Peak Wave Period (PWP), Swell Height (PHS00), Swell Period (PTP00), Swell Direction (PDI00).
    """

    RSMC_PORTAL_URL = "https://www.incois.gov.in/oceanservices/rsmc_download.jsp"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: int = 20,
    ):
        self.api_key = api_key or os.getenv("INCOIS_API_KEY")
        self.base_url = base_url or os.getenv("INCOIS_BASE_URL", self.RSMC_PORTAL_URL)
        self.timeout = timeout_seconds
        self.enabled = os.getenv("INCOIS_ENABLED", "true").lower() == "true"
        self._cached_urls: Optional[Tuple[Optional[str], Optional[str]]] = None
        self._cached_time: Optional[datetime] = None

    @property
    def provider_name(self) -> str:
        return "INCOIS"

    @property
    def provider_category(self) -> str:
        return "COASTAL_RADAR_AND_OCEAN_MODEL"

    @property
    def governing_authority(self) -> str:
        return "Indian National Centre for Ocean Information Services (INCOIS), MoES"

    @property
    def is_configured(self) -> bool:
        """
        Returns True if INCOIS is enabled. Official RSMC datasets are open access.
        """
        return self.enabled

    def fetch(self, **kwargs: Any) -> Dict[str, Any]:
        """Legacy BaseDataConnector fetch implementation."""
        lat = kwargs.get("latitude", 0.0)
        lon = kwargs.get("longitude", 0.0)
        res = self.fetch_marine_data(latitude=lat, longitude=lon)
        if res.status != ProviderStatus.HEALTHY and res.status != ProviderStatus.NO_DATA:
            raise requests.RequestException(res.error_message or f"INCOIS error: {res.status}")
        return res.raw_response or {}

    def normalize(self, raw_data: Any) -> Dict[str, Any]:
        """Legacy BaseDataConnector normalize implementation."""
        return {
            "source": self.provider_name,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "data_type": "OBSERVATION",
            "quality_flag": "OFFICIAL_VALIDATED",
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
        Retrieves real-time ocean state and current observations from official INCOIS RSMC NetCDF.
        """
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        if not self.is_configured:
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.CONFIGURATION_REQUIRED,
                error_message="INCOIS provider is disabled in configuration.",
                records=[],
                retrieved_at=now_iso,
            )

        try:
            records, raw_data = self._fetch_from_rsmc_netcdf(latitude, longitude, now, now_iso)
            
            if not records:
                return ProviderResponse(
                    provider_name=self.provider_name,
                    status=ProviderStatus.NO_DATA,
                    error_message=f"No unmasked ocean grid point found near ({latitude}, {longitude}).",
                    records=[],
                    retrieved_at=now_iso,
                )

            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.HEALTHY,
                records=records,
                raw_response=raw_data,
                retrieved_at=now_iso,
            )
        except Exception as e:
            logger.error(f"INCOIS RSMC extraction error: {e}", exc_info=True)
            return ProviderResponse(
                provider_name=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=f"INCOIS RSMC extraction failed: {str(e)}",
                records=[],
                retrieved_at=now_iso,
            )

    def _discover_active_urls(self) -> Tuple[Optional[str], Optional[str]]:
        """Dynamically scans INCOIS download portal for active RSMC NetCDF endpoints."""
        now = datetime.now(timezone.utc)
        if self._cached_urls and self._cached_time and (now - self._cached_time).total_seconds() < 3600:
            return self._cached_urls

        hycom_url = None
        ww3_url = None
        try:
            headers = {"User-Agent": "OCEANIS-Intelligence-Platform/1.0"}
            r = requests.get(self.RSMC_PORTAL_URL, headers=headers, timeout=10, verify=False)
            if r.status_code == 200:
                pattern = r"href=[\x27\x22]?([^\x27\x22 >]+\.nc)"
                matches = re.findall(pattern, r.text, re.IGNORECASE)
                for m in matches:
                    dods_path = m.replace("/thredds/fileServer/", "/thredds/dodsC/")
                    if not dods_path.startswith("http"):
                        dods_path = f"https://www.incois.gov.in{dods_path}"
                    if "hycom" in dods_path.lower() and not hycom_url:
                        hycom_url = dods_path
                    elif "ww3" in dods_path.lower() and not ww3_url:
                        ww3_url = dods_path
        except Exception as e:
            logger.warning(f"Dynamic RSMC URL discovery failed: {e}")

        # Fallback to date-based endpoints if portal scrape fails
        if not hycom_url:
            hycom_url = f"https://www.incois.gov.in/thredds/dodsC/osf/currents2/RSMC_hycom_{now.strftime('%Y%m%d')}.nc"
        if not ww3_url:
            ww3_url = f"https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_{(now - timedelta(days=1)).strftime('%Y%m%d')}.nc"

        self._cached_urls = (hycom_url, ww3_url)
        self._cached_time = now
        return hycom_url, ww3_url

    def _fetch_from_rsmc_netcdf(
        self,
        latitude: float,
        longitude: float,
        now: datetime,
        now_iso: str,
    ) -> Tuple[List[NormalizedMarineRecord], Dict[str, Any]]:
        import netCDF4 as nc

        records: List[NormalizedMarineRecord] = []
        raw_summary: Dict[str, Any] = {}

        hycom_url, ww3_url = self._discover_active_urls()

        valid_forecast_time_str = now_iso

        # 1. Extract HYCOM Currents
        if hycom_url:
            try:
                hycom_ds = nc.Dataset(hycom_url)
                try:
                    lats = hycom_ds.variables["LAT"][:]
                    lons = hycom_ds.variables["LON"][:]
                    times = hycom_ds.variables["TIME"][:]
                    
                    lat_mask = (lats >= latitude - 0.7) & (lats <= latitude + 0.7)
                    lon_mask = (lons >= longitude - 0.7) & (lons <= longitude + 0.7)
                    
                    lat_indices = np.where(lat_mask)[0]
                    lon_indices = np.where(lon_mask)[0]
                    
                    if len(lat_indices) > 0 and len(lon_indices) > 0:
                        u_slice = hycom_ds.variables["UVEL"][0, 0, lat_indices[0]:lat_indices[-1]+1, lon_indices[0]:lon_indices[-1]+1]
                        v_slice = hycom_ds.variables["VVEL"][0, 0, lat_indices[0]:lat_indices[-1]+1, lon_indices[0]:lon_indices[-1]+1]
                        t_slice = hycom_ds.variables["TEMP"][0, 0, lat_indices[0]:lat_indices[-1]+1, lon_indices[0]:lon_indices[-1]+1] if "TEMP" in hycom_ds.variables else None

                        base_time = datetime(1900, 12, 31, tzinfo=timezone.utc)
                        valid_time_obj = base_time + timedelta(days=float(times[0]))
                        valid_forecast_time_str = valid_time_obj.isoformat()

                        sub_lats = lats[lat_indices[0]:lat_indices[-1]+1]
                        sub_lons = lons[lon_indices[0]:lon_indices[-1]+1]

                        best_pt = None
                        min_dist = float("inf")

                        for i, glat in enumerate(sub_lats):
                            for j, glon in enumerate(sub_lons):
                                u_val = u_slice[i, j]
                                v_val = v_slice[i, j]
                                if not np.isnan(u_val) and not np.ma.is_masked(u_val):
                                    dist = (glat - latitude)**2 + (glon - longitude)**2
                                    if dist < min_dist:
                                        min_dist = dist
                                        best_pt = {
                                            "lat": float(glat),
                                            "lon": float(glon),
                                            "uvel": float(u_val),
                                            "vvel": float(v_val),
                                            "sst": float(t_slice[i, j]) if (t_slice is not None and not np.isnan(t_slice[i, j]) and not np.ma.is_masked(t_slice[i, j])) else None,
                                        }

                        if best_pt:
                            dataset_filename = hycom_url.split("/")[-1]
                            raw_summary["hycom_file"] = dataset_filename
                            raw_summary["grid_point"] = best_pt

                            u_val = best_pt["uvel"]
                            v_val = best_pt["vvel"]
                            speed_ms = math.sqrt(u_val**2 + v_val**2)
                            speed_kmh = round(speed_ms * 3.6, 2)
                            direction_deg = round((math.atan2(u_val, v_val) * 180.0 / math.pi + 360.0) % 360.0, 1)

                            records.append(
                                NormalizedMarineRecord(
                                    parameter="ocean_current_u",
                                    value=round(u_val, 4),
                                    unit="m/s",
                                    latitude=best_pt["lat"],
                                    longitude=best_pt["lon"],
                                    valid_time=valid_forecast_time_str,
                                    retrieved_at=now_iso,
                                    source=self.provider_name,
                                    data_type=MarineDataType.MODEL,
                                    freshness_status=DataFreshnessStatus.FRESH,
                                    quality_status=DataQualityStatus.VALIDATED,
                                    confidence=0.95,
                                    raw_identifier=dataset_filename,
                                    metadata={"variable": "UVEL", "model": "INCOIS-HYCOM"},
                                )
                            )

                            records.append(
                                NormalizedMarineRecord(
                                    parameter="ocean_current_v",
                                    value=round(v_val, 4),
                                    unit="m/s",
                                    latitude=best_pt["lat"],
                                    longitude=best_pt["lon"],
                                    valid_time=valid_forecast_time_str,
                                    retrieved_at=now_iso,
                                    source=self.provider_name,
                                    data_type=MarineDataType.MODEL,
                                    freshness_status=DataFreshnessStatus.FRESH,
                                    quality_status=DataQualityStatus.VALIDATED,
                                    confidence=0.95,
                                    raw_identifier=dataset_filename,
                                    metadata={"variable": "VVEL", "model": "INCOIS-HYCOM"},
                                )
                            )

                            records.append(
                                NormalizedMarineRecord(
                                    parameter="ocean_current_velocity",
                                    value=speed_kmh,
                                    unit="km/h",
                                    latitude=best_pt["lat"],
                                    longitude=best_pt["lon"],
                                    valid_time=valid_forecast_time_str,
                                    retrieved_at=now_iso,
                                    source=self.provider_name,
                                    data_type=MarineDataType.MODEL,
                                    freshness_status=DataFreshnessStatus.FRESH,
                                    quality_status=DataQualityStatus.VALIDATED,
                                    confidence=0.95,
                                    raw_identifier=dataset_filename,
                                    metadata={"speed_ms": round(speed_ms, 3), "model": "INCOIS-HYCOM"},
                                )
                            )

                            records.append(
                                NormalizedMarineRecord(
                                    parameter="ocean_current_direction",
                                    value=direction_deg,
                                    unit="deg",
                                    latitude=best_pt["lat"],
                                    longitude=best_pt["lon"],
                                    valid_time=valid_forecast_time_str,
                                    retrieved_at=now_iso,
                                    source=self.provider_name,
                                    data_type=MarineDataType.MODEL,
                                    freshness_status=DataFreshnessStatus.FRESH,
                                    quality_status=DataQualityStatus.VALIDATED,
                                    confidence=0.95,
                                    raw_identifier=dataset_filename,
                                    metadata={"model": "INCOIS-HYCOM"},
                                )
                            )

                            if best_pt["sst"] is not None:
                                records.append(
                                    NormalizedMarineRecord(
                                        parameter="sea_surface_temperature",
                                        value=round(best_pt["sst"], 2),
                                        unit="C",
                                        latitude=best_pt["lat"],
                                        longitude=best_pt["lon"],
                                        valid_time=valid_forecast_time_str,
                                        retrieved_at=now_iso,
                                        source=self.provider_name,
                                        data_type=MarineDataType.MODEL,
                                        freshness_status=DataFreshnessStatus.FRESH,
                                        quality_status=DataQualityStatus.VALIDATED,
                                        confidence=0.95,
                                        raw_identifier=dataset_filename,
                                        metadata={"variable": "TEMP", "model": "INCOIS-HYCOM"},
                                    )
                                )
                finally:
                    hycom_ds.close()
            except Exception as he:
                logger.warning(f"INCOIS HYCOM dataset read error: {he}")

        # 2. Extract WW3 Waves
        if ww3_url:
            try:
                ww3_ds = nc.Dataset(ww3_url)
                try:
                    lats = ww3_ds.variables["IOYAXIS"][:]
                    lons = ww3_ds.variables["IOXAXIS"][:]
                    
                    lat_mask = (lats >= latitude - 0.7) & (lats <= latitude + 0.7)
                    lon_mask = (lons >= longitude - 0.7) & (lons <= longitude + 0.7)
                    
                    lat_indices = np.where(lat_mask)[0]
                    lon_indices = np.where(lon_mask)[0]

                    if len(lat_indices) > 0 and len(lon_indices) > 0:
                        hs_slice = ww3_ds.variables["HS"][0, lat_indices[0]:lat_indices[-1]+1, lon_indices[0]:lon_indices[-1]+1]
                        mwd_slice = ww3_ds.variables["MWD"][0, lat_indices[0]:lat_indices[-1]+1, lon_indices[0]:lon_indices[-1]+1]
                        pwp_slice = ww3_ds.variables["PWP"][0, lat_indices[0]:lat_indices[-1]+1, lon_indices[0]:lon_indices[-1]+1]
                        phs_slice = ww3_ds.variables["PHS00"][0, lat_indices[0]:lat_indices[-1]+1, lon_indices[0]:lon_indices[-1]+1]
                        ptp_slice = ww3_ds.variables["PTP00"][0, lat_indices[0]:lat_indices[-1]+1, lon_indices[0]:lon_indices[-1]+1]
                        pdi_slice = ww3_ds.variables["PDI00"][0, lat_indices[0]:lat_indices[-1]+1, lon_indices[0]:lon_indices[-1]+1]

                        sub_lats = lats[lat_indices[0]:lat_indices[-1]+1]
                        sub_lons = lons[lon_indices[0]:lon_indices[-1]+1]

                        best_ww3 = None
                        min_dist = float("inf")

                        for i, glat in enumerate(sub_lats):
                            for j, glon in enumerate(sub_lons):
                                hs_val = hs_slice[i, j]
                                if not np.isnan(hs_val) and not np.ma.is_masked(hs_val):
                                    dist = (glat - latitude)**2 + (glon - longitude)**2
                                    if dist < min_dist:
                                        min_dist = dist
                                        best_ww3 = {
                                            "lat": float(glat),
                                            "lon": float(glon),
                                            "wave_height_m": float(hs_val),
                                            "wave_direction_deg": float(mwd_slice[i, j]) if not np.ma.is_masked(mwd_slice[i, j]) else None,
                                            "wave_period_s": float(pwp_slice[i, j]) if not np.ma.is_masked(pwp_slice[i, j]) else None,
                                            "swell_height_m": float(phs_slice[i, j]) if not np.ma.is_masked(phs_slice[i, j]) else None,
                                            "swell_period_s": float(ptp_slice[i, j]) if not np.ma.is_masked(ptp_slice[i, j]) else None,
                                            "swell_direction_deg": float(pdi_slice[i, j]) if not np.ma.is_masked(pdi_slice[i, j]) else None,
                                        }

                        if best_ww3:
                            dataset_filename = ww3_url.split("/")[-1]
                            raw_summary["ww3_file"] = dataset_filename
                            raw_summary["wave_grid_point"] = best_ww3

                            if best_ww3["wave_height_m"] is not None:
                                records.append(
                                    NormalizedMarineRecord(
                                        parameter="wave_height",
                                        value=round(best_ww3["wave_height_m"], 2),
                                        unit="m",
                                        latitude=best_ww3["lat"],
                                        longitude=best_ww3["lon"],
                                        valid_time=valid_forecast_time_str,
                                        retrieved_at=now_iso,
                                        source=self.provider_name,
                                        data_type=MarineDataType.MODEL,
                                        freshness_status=DataFreshnessStatus.FRESH,
                                        quality_status=DataQualityStatus.VALIDATED,
                                        confidence=0.95,
                                        raw_identifier=dataset_filename,
                                        metadata={"variable": "HS", "model": "INCOIS-WW3"},
                                    )
                                )

                            if best_ww3["wave_direction_deg"] is not None:
                                records.append(
                                    NormalizedMarineRecord(
                                        parameter="wave_direction",
                                        value=round(best_ww3["wave_direction_deg"], 1),
                                        unit="deg",
                                        latitude=best_ww3["lat"],
                                        longitude=best_ww3["lon"],
                                        valid_time=valid_forecast_time_str,
                                        retrieved_at=now_iso,
                                        source=self.provider_name,
                                        data_type=MarineDataType.MODEL,
                                        freshness_status=DataFreshnessStatus.FRESH,
                                        quality_status=DataQualityStatus.VALIDATED,
                                        confidence=0.95,
                                        raw_identifier=dataset_filename,
                                        metadata={"variable": "MWD", "model": "INCOIS-WW3"},
                                    )
                                )

                            if best_ww3["wave_period_s"] is not None:
                                records.append(
                                    NormalizedMarineRecord(
                                        parameter="wave_period",
                                        value=round(best_ww3["wave_period_s"], 1),
                                        unit="s",
                                        latitude=best_ww3["lat"],
                                        longitude=best_ww3["lon"],
                                        valid_time=valid_forecast_time_str,
                                        retrieved_at=now_iso,
                                        source=self.provider_name,
                                        data_type=MarineDataType.MODEL,
                                        freshness_status=DataFreshnessStatus.FRESH,
                                        quality_status=DataQualityStatus.VALIDATED,
                                        confidence=0.95,
                                        raw_identifier=dataset_filename,
                                        metadata={"variable": "PWP", "model": "INCOIS-WW3"},
                                    )
                                )

                            if best_ww3["swell_height_m"] is not None:
                                records.append(
                                    NormalizedMarineRecord(
                                        parameter="swell_wave_height",
                                        value=round(best_ww3["swell_height_m"], 2),
                                        unit="m",
                                        latitude=best_ww3["lat"],
                                        longitude=best_ww3["lon"],
                                        valid_time=valid_forecast_time_str,
                                        retrieved_at=now_iso,
                                        source=self.provider_name,
                                        data_type=MarineDataType.MODEL,
                                        freshness_status=DataFreshnessStatus.FRESH,
                                        quality_status=DataQualityStatus.VALIDATED,
                                        confidence=0.95,
                                        raw_identifier=dataset_filename,
                                        metadata={"variable": "PHS00", "model": "INCOIS-WW3"},
                                    )
                                )

                            if best_ww3["swell_period_s"] is not None:
                                records.append(
                                    NormalizedMarineRecord(
                                        parameter="swell_wave_period",
                                        value=round(best_ww3["swell_period_s"], 1),
                                        unit="s",
                                        latitude=best_ww3["lat"],
                                        longitude=best_ww3["lon"],
                                        valid_time=valid_forecast_time_str,
                                        retrieved_at=now_iso,
                                        source=self.provider_name,
                                        data_type=MarineDataType.MODEL,
                                        freshness_status=DataFreshnessStatus.FRESH,
                                        quality_status=DataQualityStatus.VALIDATED,
                                        confidence=0.95,
                                        raw_identifier=dataset_filename,
                                        metadata={"variable": "PTP00", "model": "INCOIS-WW3"},
                                    )
                                )
                finally:
                    ww3_ds.close()
            except Exception as we:
                logger.warning(f"INCOIS WW3 dataset read error: {we}")

        return records, raw_summary
