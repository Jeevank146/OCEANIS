from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.orm import Session

from connectors.open_meteo import OpenMeteoConnector
from models.weather import WeatherObservation


class WeatherIngestionService:
    """
    Fetches weather data through an OCEANIS connector and prepares
    normalized data for persistence and downstream agents.
    """

    def __init__(self, connector: OpenMeteoConnector | None = None):
        self.connector = connector or OpenMeteoConnector()

    def ingest(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        forecast_days: int = 3,
    ) -> Dict[str, Any]:
        """
        Fetch, normalize, and persist weather data.

        Accepts a database session to record the weather observation
        in PostgreSQL before returning the normalized structure.
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
        current = normalized_data.get("current", {})

        observation = WeatherObservation(
            latitude=location.get("latitude", latitude),
            longitude=location.get("longitude", longitude),
            observed_at=observed_at,
            temperature_c=current.get("temperature_c"),
            humidity_percent=current.get("humidity_percent"),
            wind_speed_kmh=current.get("wind_speed_kmh"),
            wind_direction_deg=current.get("wind_direction_deg"),
            precipitation_mm=current.get("precipitation_mm"),
            source=normalized_data.get("source", self.connector.source_name),
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