from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from connectors.base import BaseDataConnector
from connectors.open_meteo_marine import OpenMeteoMarineConnector
from models.marine import MarineObservation


class MarineIngestionService:
    """
    Service responsible for ingesting, validating, normalizing, and persisting
    marine and oceanographic observation data into the OCEANIS database.

    Modularly accepts any connector adhering to BaseDataConnector (e.g. OpenMeteoMarineConnector,
    or future INCOIS / IMD marine connectors).
    """

    def __init__(self, connector: Optional[BaseDataConnector] = None):
        self.connector = connector or OpenMeteoMarineConnector()

    def ingest(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        forecast_days: int = 1,
    ) -> Dict[str, Any]:
        """
        Fetch, normalize, and persist marine conditions data for given coordinates.
        """
        raw_data = self.connector.fetch(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
        )

        normalized_data = self.connector.normalize(raw_data)

        retrieved_at_str = normalized_data.get("retrieved_at")
        if retrieved_at_str:
            observed_at = datetime.fromisoformat(retrieved_at_str)
        else:
            observed_at = datetime.now(timezone.utc)

        location = normalized_data.get("location", {})
        conditions = normalized_data.get("conditions", {})
        waves = conditions.get("waves", {})
        swell = conditions.get("swell", {})
        wind_waves = conditions.get("wind_waves", {})
        ocean_current = conditions.get("ocean_current", {})

        observation = MarineObservation(
            latitude=location.get("latitude", latitude),
            longitude=location.get("longitude", longitude),
            observed_at=observed_at,
            wave_height_m=waves.get("wave_height_m"),
            wave_direction_deg=waves.get("wave_direction_deg"),
            wave_period_s=waves.get("wave_period_s"),
            swell_wave_height_m=swell.get("swell_wave_height_m"),
            swell_wave_direction_deg=swell.get("swell_wave_direction_deg"),
            swell_wave_period_s=swell.get("swell_wave_period_s"),
            wind_wave_height_m=wind_waves.get("wind_wave_height_m"),
            wind_wave_direction_deg=wind_waves.get("wind_wave_direction_deg"),
            wind_wave_period_s=wind_waves.get("wind_wave_period_s"),
            ocean_current_velocity_kmh=ocean_current.get("velocity_kmh"),
            ocean_current_direction_deg=ocean_current.get("direction_deg"),
            sea_surface_temperature_c=conditions.get("sea_surface_temperature_c"),
            source=normalized_data.get("source", self.connector.source_name),
            data_type=normalized_data.get("data_type", "OBSERVATION"),
            quality_flag=normalized_data.get("quality_flag", "REALTIME"),
            source_timezone=normalized_data.get("raw_timezone"),
        )

        try:
            db.add(observation)
            db.commit()
            db.refresh(observation)
            normalized_data["observation_id"] = observation.id
        except Exception:
            db.rollback()
            raise

        return normalized_data
