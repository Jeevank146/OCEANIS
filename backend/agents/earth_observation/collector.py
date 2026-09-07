from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from geoalchemy2 import Geography
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.earth_observation import EarthObservation
from services.freshness import FreshnessCategory, evaluate_freshness


class EarthObservationDataCollector:
    """
    Retrieves and normalizes satellite-derived Earth observations from the
    existing OCEANIS Earth Observation data layer.
    Preserves satellite platform, sensor payload, optical parameters, SST,
    cloud cover, provenance, quality flags, timestamps, and freshness.
    """

    @staticmethod
    def get_earth_observation_evidence(
        db: Session,
        latitude: float,
        longitude: float,
        current_time: Optional[datetime] = None,
        radius_m: float = 100000.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Queries the latest EarthObservation record in proximity to the specified coordinates.
        """
        now = current_time or datetime.now(timezone.utc)
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)

        eo_geom = func.ST_SetSRID(
            func.ST_MakePoint(EarthObservation.longitude, EarthObservation.latitude), 4326
        )
        latest_eo = (
            db.query(EarthObservation)
            .filter(func.ST_DWithin(func.cast(eo_geom, Geography), point_geog, radius_m))
            .order_by(EarthObservation.observed_at.desc())
            .first()
        )

        if not latest_eo:
            return None

        freshness = evaluate_freshness(latest_eo.observed_at, current_time=now)
        retrieved_at_str = latest_eo.retrieved_at.isoformat() if latest_eo.retrieved_at else (
            latest_eo.created_at.isoformat() if latest_eo.created_at else now.isoformat()
        )

        return {
            "id": latest_eo.id,
            "latitude": latest_eo.latitude,
            "longitude": latest_eo.longitude,
            "sea_surface_temperature_c": latest_eo.sea_surface_temperature_c,
            "chlorophyll_a_mg_m3": latest_eo.chlorophyll_a_mg_m3,
            "ocean_colour": latest_eo.ocean_colour,
            "cloud_cover_percent": latest_eo.cloud_cover_percent,
            "solar_radiation_w_m2": latest_eo.solar_radiation_w_m2,
            "satellite_platform": latest_eo.satellite_platform,
            "sensor_instrument": latest_eo.sensor_instrument,
            "product_type": latest_eo.product_type,
            "observed_at": latest_eo.observed_at.isoformat(),
            "observed_at_dt": latest_eo.observed_at,
            "retrieved_at": retrieved_at_str,
            "source": latest_eo.source,
            "source_url": latest_eo.source_url,
            "data_type": latest_eo.data_type or "OBSERVATION_ASSIMILATION",
            "quality_flag": latest_eo.quality_flag or "OPERATIONAL_QUALITY",
            "freshness": freshness,
        }

    @staticmethod
    def get_previous_observation(
        db: Session,
        latitude: float,
        longitude: float,
        current_observed_at: datetime,
        radius_m: float = 100000.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves the prior historical EarthObservation record before the given timestamp
        for temporal comparison.
        """
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)

        eo_geom = func.ST_SetSRID(
            func.ST_MakePoint(EarthObservation.longitude, EarthObservation.latitude), 4326
        )
        prev_eo = (
            db.query(EarthObservation)
            .filter(
                func.ST_DWithin(func.cast(eo_geom, Geography), point_geog, radius_m),
                EarthObservation.observed_at < current_observed_at,
            )
            .order_by(EarthObservation.observed_at.desc())
            .first()
        )

        if not prev_eo:
            return None

        retrieved_at_str = prev_eo.retrieved_at.isoformat() if prev_eo.retrieved_at else (
            prev_eo.created_at.isoformat() if prev_eo.created_at else ""
        )

        return {
            "id": prev_eo.id,
            "latitude": prev_eo.latitude,
            "longitude": prev_eo.longitude,
            "sea_surface_temperature_c": prev_eo.sea_surface_temperature_c,
            "chlorophyll_a_mg_m3": prev_eo.chlorophyll_a_mg_m3,
            "ocean_colour": prev_eo.ocean_colour,
            "cloud_cover_percent": prev_eo.cloud_cover_percent,
            "solar_radiation_w_m2": prev_eo.solar_radiation_w_m2,
            "satellite_platform": prev_eo.satellite_platform,
            "sensor_instrument": prev_eo.sensor_instrument,
            "product_type": prev_eo.product_type,
            "observed_at": prev_eo.observed_at.isoformat(),
            "observed_at_dt": prev_eo.observed_at,
            "retrieved_at": retrieved_at_str,
            "source": prev_eo.source,
            "data_type": prev_eo.data_type,
            "quality_flag": prev_eo.quality_flag,
        }
