from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from connectors.base import BaseDataConnector
from connectors.earth_observation import EarthObservationConnector
from models.earth_observation import EarthObservation


class EarthObservationIngestionService:
    """
    Service responsible for ingesting, validating, normalizing, and persisting
    Earth Observation (EO) and satellite-derived data into PostgreSQL.

    Decoupled via BaseDataConnector to allow drop-in addition of official
    satellite mission APIs (Copernicus Sentinel Hub, NASA CMR, NOAA CoastWatch, INCOIS).
    """

    def __init__(self, connector: Optional[BaseDataConnector] = None):
        self.connector = connector or EarthObservationConnector()

    def ingest(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        product_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch, normalize, and persist Earth Observation data for given coordinates with duplicate protection.
        """
        raw_data = self.connector.fetch(
            latitude=latitude,
            longitude=longitude,
            product_type=product_type,
        )

        normalized_data = self.connector.normalize(raw_data)

        observed_at_str = normalized_data.get("observed_at")
        if observed_at_str:
            observed_at = datetime.fromisoformat(observed_at_str.replace("Z", "+00:00"))
        else:
            observed_at = datetime.now(timezone.utc)

        retrieved_at_str = normalized_data.get("retrieved_at")
        if retrieved_at_str:
            retrieved_at = datetime.fromisoformat(retrieved_at_str.replace("Z", "+00:00"))
        else:
            retrieved_at = datetime.now(timezone.utc)

        location = normalized_data.get("location", {})
        measurements = normalized_data.get("measurements", {})
        metadata = normalized_data.get("metadata", {})

        obs_lat = location.get("latitude", latitude)
        obs_lon = location.get("longitude", longitude)
        source_name = normalized_data.get("source", self.connector.source_name)
        prod_type = normalized_data.get("product_type", "SST_AND_OPTICAL")

        # Duplicate Protection: Check if identical observation exists
        existing_obs = (
            db.query(EarthObservation)
            .filter(
                EarthObservation.source == source_name,
                EarthObservation.product_type == prod_type,
                EarthObservation.observed_at == observed_at,
                func.abs(EarthObservation.latitude - obs_lat) < 0.05,
                func.abs(EarthObservation.longitude - obs_lon) < 0.05,
            )
            .first()
        )

        if existing_obs:
            # Update values if newer data is retrieved
            existing_obs.retrieved_at = retrieved_at
            if measurements.get("chlorophyll_a_mg_m3") is not None:
                existing_obs.chlorophyll_a_mg_m3 = measurements.get("chlorophyll_a_mg_m3")
            if measurements.get("ocean_colour") is not None:
                existing_obs.ocean_colour = measurements.get("ocean_colour")
            if measurements.get("sea_surface_temperature_c") is not None:
                existing_obs.sea_surface_temperature_c = measurements.get("sea_surface_temperature_c")
            if measurements.get("cloud_cover_percent") is not None:
                existing_obs.cloud_cover_percent = measurements.get("cloud_cover_percent")
            if measurements.get("solar_radiation_w_m2") is not None:
                existing_obs.solar_radiation_w_m2 = measurements.get("solar_radiation_w_m2")
            
            db.commit()
            db.refresh(existing_obs)
            normalized_data["observation_id"] = existing_obs.id
            return normalized_data

        observation = EarthObservation(
            latitude=obs_lat,
            longitude=obs_lon,
            observed_at=observed_at,
            retrieved_at=retrieved_at,
            source=source_name,
            product_type=prod_type,
            satellite_platform=metadata.get("satellite_platform"),
            sensor_instrument=metadata.get("sensor_instrument"),
            sea_surface_temperature_c=measurements.get("sea_surface_temperature_c"),
            chlorophyll_a_mg_m3=measurements.get("chlorophyll_a_mg_m3"),
            ocean_colour=measurements.get("ocean_colour"),
            cloud_cover_percent=measurements.get("cloud_cover_percent"),
            solar_radiation_w_m2=measurements.get("solar_radiation_w_m2"),
            data_type=normalized_data.get("data_type", "OBSERVATION_ASSIMILATION"),
            quality_flag=normalized_data.get("quality_flag", "OPERATIONAL_QUALITY"),
            source_url=metadata.get("source_url"),
            source_timezone=metadata.get("source_timezone"),
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
