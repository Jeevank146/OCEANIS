from datetime import datetime, timezone
from typing import Any, Dict, Optional

from geoalchemy2 import Geography
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.marine import MarineObservation
from services.freshness import FreshnessCategory, evaluate_freshness


class MarineConditionsDataCollector:
    """
    Retrieves and normalizes marine oceanographic observations from the
    existing OCEANIS Marine Conditions data layer.
    Preserves provenance, quality flags, timestamps, and freshness.
    """

    @staticmethod
    def get_marine_evidence(
        db: Session,
        latitude: float,
        longitude: float,
        current_time: Optional[datetime] = None,
        radius_m: float = 100000.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Queries persistent marine observations in proximity to the specified coordinate.
        """
        now = current_time or datetime.now(timezone.utc)
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)

        marine_geom = func.ST_SetSRID(
            func.ST_MakePoint(MarineObservation.longitude, MarineObservation.latitude), 4326
        )
        latest_marine = (
            db.query(MarineObservation)
            .filter(func.ST_DWithin(func.cast(marine_geom, Geography), point_geog, radius_m))
            .order_by(MarineObservation.observed_at.desc())
            .first()
        )

        if not latest_marine:
            return None

        freshness = evaluate_freshness(latest_marine.observed_at, current_time=now)
        retrieved_at_str = latest_marine.created_at.isoformat() if latest_marine.created_at else now.isoformat()

        return {
            "latitude": latest_marine.latitude,
            "longitude": latest_marine.longitude,
            "wave_height_m": latest_marine.wave_height_m,
            "wave_direction_deg": latest_marine.wave_direction_deg,
            "wave_period_s": latest_marine.wave_period_s,
            "swell_wave_height_m": latest_marine.swell_wave_height_m,
            "swell_wave_direction_deg": latest_marine.swell_wave_direction_deg,
            "swell_wave_period_s": latest_marine.swell_wave_period_s,
            "wind_wave_height_m": latest_marine.wind_wave_height_m,
            "wind_wave_direction_deg": latest_marine.wind_wave_direction_deg,
            "wind_wave_period_s": latest_marine.wind_wave_period_s,
            "ocean_current_velocity_kmh": latest_marine.ocean_current_velocity_kmh,
            "ocean_current_direction_deg": latest_marine.ocean_current_direction_deg,
            "sea_surface_temperature_c": latest_marine.sea_surface_temperature_c,
            "observed_at": latest_marine.observed_at.isoformat(),
            "retrieved_at": retrieved_at_str,
            "source": latest_marine.source,
            "data_type": latest_marine.data_type or "OBSERVATION",
            "quality_flag": latest_marine.quality_flag or "GOOD",
            "freshness": freshness,
        }
