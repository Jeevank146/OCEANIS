import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from connectors.base import BaseMarineDataProvider
from connectors.copernicus import CopernicusProvider
from connectors.fallback import FallbackMarineProvider
from connectors.imd import IMDProvider
from connectors.incois import INCOISProvider
from models.earth_observation import EarthObservation
from models.marine import MarineObservation
from models.weather import WeatherObservation
from schemas.marine_provider import (
    DataFreshnessStatus,
    DataQualityStatus,
    MarineDataType,
    MultiSourceMarineResponse,
    NormalizedMarineRecord,
    ProviderHealthResponse,
    ProviderResponse,
    ProviderStatus,
)
from services.freshness import evaluate_parameter_freshness
from services.location import LocationService
from services.validation import DataValidator

logger = logging.getLogger(__name__)


class MarineDataService:
    """
    Unified, provider-independent Marine Data Foundation Service for OCEANIS.
    
    Responsibilities:
    1. Multi-source provider orchestration (INCOIS, IMD, Copernicus, Fallback).
    2. Physical validation gatekeeping (DataValidator) before database storage.
    3. Fine-grained parameter freshness evaluation.
    4. Provenance preservation: Every observation retains source attribution and validity window.
    5. Clean separation between live telemetry, models, warnings, and demo data.
    6. Downstream agent integration gateway.
    """

    def __init__(
        self,
        providers: Optional[Dict[str, BaseMarineDataProvider]] = None,
    ):
        self.providers: Dict[str, BaseMarineDataProvider] = providers or {
            "INCOIS": INCOISProvider(),
            "IMD": IMDProvider(),
            "Copernicus": CopernicusProvider(),
            "Fallback": FallbackMarineProvider(),
        }

    def get_provider_health(self) -> List[ProviderHealthResponse]:
        """
        Reports status, credentials readiness, and health for all registered data providers.
        """
        results: List[ProviderHealthResponse] = []
        for name, provider in self.providers.items():
            results.append(provider.check_health())
        return results

    def fetch_marine_intelligence(
        self,
        latitude: float,
        longitude: float,
        variables: Optional[List[str]] = None,
        db: Optional[Session] = None,
        save_to_db: bool = True,
        now: Optional[datetime] = None,
        location_name: Optional[str] = None,
    ) -> MultiSourceMarineResponse:
        """
        Queries registered marine providers for coordinates, validates physics,
        evaluates freshness, optionally persists observations, and returns
        the normalized multi-source payload.
        """
        current_time = now or datetime.now(timezone.utc)
        current_iso = current_time.isoformat()

        # Step 1: Geographic & Coastal Bound Verification
        location_val = LocationService.validate_coordinates(
            latitude, longitude, custom_name=location_name
        )
        resolved_name = location_name or location_val.location_name
        is_coastal = location_val.is_coastal or location_val.is_marine

        if not is_coastal or location_val.status == "INLAND":
            logger.info(f"Coordinates ({latitude}, {longitude}) are inland ({location_val.distance_to_coast_km:.1f} km from coast). Blocking marine data.")
            return MultiSourceMarineResponse(
                latitude=latitude,
                longitude=longitude,
                location_name=resolved_name,
                is_coastal=False,
                primary_source="OCEANIS PostGIS Boundary Engine",
                records=[],
                provider_statuses={"ALL": ProviderStatus.NO_DATA},
                generated_at=current_iso,
                warnings=[
                    f"Inland location detected ({location_val.distance_to_coast_km:.0f} km from nearest coast). "
                    "Physical oceanographic parameters are blocked to prevent false marine readings."
                ],
            )

        # Step 2: Query Providers
        collected_records: List[NormalizedMarineRecord] = []
        provider_statuses: Dict[str, ProviderStatus] = {}
        primary_source: Optional[str] = None

        # Preferred order: INCOIS -> Copernicus -> IMD -> Fallback
        priority_keys = ["INCOIS", "Copernicus", "IMD", "Fallback"]

        for key in priority_keys:
            provider = self.providers.get(key)
            if not provider:
                continue

            try:
                res: ProviderResponse = provider.fetch_marine_data(
                    latitude=latitude,
                    longitude=longitude,
                    variables=variables,
                )
                provider_statuses[key] = res.status

                if res.status == ProviderStatus.HEALTHY and res.records:
                    # Validate incoming records
                    valid_recs, rejected = DataValidator.filter_and_validate_records(res.records)
                    
                    if rejected:
                        for rec, reason in rejected:
                            logger.warning(
                                f"Rejected record from {rec.source} for {rec.parameter}={rec.value}: {reason}"
                            )

                    # Update freshness for validated records
                    for rec in valid_recs:
                        valid_dt = datetime.fromisoformat(rec.valid_time.replace("Z", "+00:00"))
                        rec.freshness_status = evaluate_parameter_freshness(
                            timestamp=valid_dt,
                            parameter=rec.parameter,
                            provider=rec.source,
                            current_time=current_time,
                        )

                    if valid_recs:
                        collected_records.extend(valid_recs)
                        if not primary_source:
                            primary_source = provider.provider_name

            except Exception as exc:
                logger.error(f"Provider {key} encountered unhandled exception: {exc}", exc_info=True)
                provider_statuses[key] = ProviderStatus.UNAVAILABLE

        # Step 3: Persist Validated Records to PostgreSQL (if DB session provided)
        if db is not None and save_to_db and collected_records:
            self._persist_records(db, latitude, longitude, collected_records, current_time)

        return MultiSourceMarineResponse(
            latitude=latitude,
            longitude=longitude,
            location_name=resolved_name,
            is_coastal=True,
            primary_source=primary_source or "Fallback (Open-Meteo / GFS)",
            records=collected_records,
            provider_statuses=provider_statuses,
            generated_at=current_iso,
            warnings=[] if collected_records else ["No live marine telemetry available for active coordinates."],
        )

    def _persist_records(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        records: List[NormalizedMarineRecord],
        current_time: datetime,
    ) -> None:
        """Groups normalized records by domain model and stores them in PostgreSQL with de-duplication."""
        wave_map: Dict[str, Any] = {}
        weather_map: Dict[str, Any] = {}
        eo_map: Dict[str, Any] = {}
        source_name = records[0].source if records else "OCEANIS Marine Data Service"
        valid_time = current_time

        for rec in records:
            if rec.valid_time:
                try:
                    if "T" in str(rec.valid_time):
                        valid_time = datetime.fromisoformat(str(rec.valid_time))
                    elif len(str(rec.valid_time).split()) == 2:
                        valid_time = datetime.strptime(str(rec.valid_time), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except Exception:
                    pass

            if rec.parameter == "wave_height":
                wave_map["wave_height_m"] = rec.value
            elif rec.parameter == "wave_direction":
                wave_map["wave_direction_deg"] = rec.value
            elif rec.parameter == "wave_period":
                wave_map["wave_period_s"] = rec.value
            elif rec.parameter == "swell_wave_height":
                wave_map["swell_wave_height_m"] = rec.value
            elif rec.parameter == "swell_wave_direction":
                wave_map["swell_wave_direction_deg"] = rec.value
            elif rec.parameter == "swell_wave_period":
                wave_map["swell_wave_period_s"] = rec.value
            elif rec.parameter == "wind_wave_height":
                wave_map["wind_wave_height_m"] = rec.value
            elif rec.parameter == "ocean_current_velocity":
                wave_map["ocean_current_velocity_kmh"] = rec.value
            elif rec.parameter == "ocean_current_direction":
                wave_map["ocean_current_direction_deg"] = rec.value
            elif rec.parameter == "sea_surface_temperature":
                wave_map["sea_surface_temperature_c"] = rec.value
                eo_map["sea_surface_temperature_c"] = rec.value
            elif rec.parameter == "salinity":
                wave_map["salinity_psu"] = rec.value
            elif rec.parameter == "chlorophyll_a":
                eo_map["chlorophyll_a_mg_m3"] = rec.value

            # Weather parameters
            if rec.parameter == "temperature":
                weather_map["temperature_c"] = rec.value
            elif rec.parameter == "relative_humidity":
                weather_map["humidity_percent"] = rec.value
            elif rec.parameter == "wind_speed":
                weather_map["wind_speed_kmh"] = rec.value
            elif rec.parameter == "wind_direction":
                weather_map["wind_direction_deg"] = rec.value
            elif rec.parameter == "precipitation":
                weather_map["precipitation_mm"] = rec.value

        try:
            # 1. Save / Update MarineObservation (with duplicate protection)
            if wave_map:
                primary_src = source_name
                # Check for existing record at same location, time, and source
                existing_marine = (
                    db.query(MarineObservation)
                    .filter(
                        MarineObservation.latitude == latitude,
                        MarineObservation.longitude == longitude,
                        MarineObservation.observed_at == valid_time,
                        MarineObservation.source == primary_src,
                    )
                    .first()
                )

                if existing_marine:
                    for k, v in wave_map.items():
                        if v is not None:
                            setattr(existing_marine, k, v)
                    existing_marine.updated_at = datetime.now(timezone.utc)
                else:
                    marine_obs = MarineObservation(
                        latitude=latitude,
                        longitude=longitude,
                        observed_at=valid_time,
                        wave_height_m=wave_map.get("wave_height_m"),
                        wave_direction_deg=wave_map.get("wave_direction_deg"),
                        wave_period_s=wave_map.get("wave_period_s"),
                        swell_wave_height_m=wave_map.get("swell_wave_height_m"),
                        swell_wave_direction_deg=wave_map.get("swell_wave_direction_deg"),
                        swell_wave_period_s=wave_map.get("swell_wave_period_s"),
                        wind_wave_height_m=wave_map.get("wind_wave_height_m"),
                        ocean_current_velocity_kmh=wave_map.get("ocean_current_velocity_kmh"),
                        ocean_current_direction_deg=wave_map.get("ocean_current_direction_deg"),
                        sea_surface_temperature_c=wave_map.get("sea_surface_temperature_c"),
                        salinity_psu=wave_map.get("salinity_psu"),
                        source=primary_src,
                        data_type="OBSERVATION",
                        quality_flag="VALIDATED",
                    )
                    db.add(marine_obs)

            # 2. Save / Update WeatherObservation
            if weather_map:
                existing_weather = (
                    db.query(WeatherObservation)
                    .filter(
                        WeatherObservation.latitude == latitude,
                        WeatherObservation.longitude == longitude,
                        WeatherObservation.observed_at == valid_time,
                        WeatherObservation.source == (records[0].source if records else "OCEANIS Weather"),
                    )
                    .first()
                )
                if existing_weather:
                    for k, v in weather_map.items():
                        if v is not None:
                            setattr(existing_weather, k, v)
                    existing_weather.updated_at = datetime.now(timezone.utc)
                else:
                    weather_obs = WeatherObservation(
                        latitude=latitude,
                        longitude=longitude,
                        observed_at=valid_time,
                        temperature_c=weather_map.get("temperature_c"),
                        humidity_percent=weather_map.get("humidity_percent"),
                        wind_speed_kmh=weather_map.get("wind_speed_kmh"),
                        wind_direction_deg=weather_map.get("wind_direction_deg"),
                        precipitation_mm=weather_map.get("precipitation_mm"),
                        source=records[0].source if records else "OCEANIS Weather",
                    )
                    db.add(weather_obs)

            # 3. Save / Update EarthObservation
            if eo_map and (eo_map.get("chlorophyll_a_mg_m3") or eo_map.get("sea_surface_temperature_c")):
                existing_eo = (
                    db.query(EarthObservation)
                    .filter(
                        EarthObservation.latitude == latitude,
                        EarthObservation.longitude == longitude,
                        EarthObservation.observed_at == valid_time,
                        EarthObservation.source == (records[0].source if records else "Copernicus"),
                    )
                    .first()
                )
                if existing_eo:
                    for k, v in eo_map.items():
                        if v is not None:
                            setattr(existing_eo, k, v)
                    existing_eo.updated_at = datetime.now(timezone.utc)
                else:
                    eo_obs = EarthObservation(
                        latitude=latitude,
                        longitude=longitude,
                        observed_at=valid_time,
                        retrieved_at=current_time,
                        source=records[0].source if records else "Copernicus",
                        product_type="BIO_OPTICS_AND_THERMAL",
                        satellite_platform="Sentinel-3 / CMEMS",
                        sensor_instrument="OLCI / SLSTR / NRT-Model",
                        sea_surface_temperature_c=eo_map.get("sea_surface_temperature_c"),
                        chlorophyll_a_mg_m3=eo_map.get("chlorophyll_a_mg_m3"),
                        data_type="OBSERVATION",
                        quality_flag="VALIDATED",
                    )
                    db.add(eo_obs)

            db.commit()
        except Exception as err:
            db.rollback()
            logger.error(f"Failed to persist marine records: {err}", exc_info=True)
