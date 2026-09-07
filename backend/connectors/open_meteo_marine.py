from datetime import datetime, timezone
from typing import Any, Dict

import requests

from connectors.base import BaseDataConnector


class OpenMeteoMarineConnector(BaseDataConnector):
    """
    Connector for retrieving marine, wave, and oceanographic data
    from Open-Meteo Marine API.

    Designed following the BaseDataConnector architecture so that official
    marine data sources (such as INCOIS or IMD marine bulletins) can be
    plugged in seamlessly alongside or in place of this connector.
    """

    BASE_URL = "http://marine-api.open-meteo.com/v1/marine"

    @property
    def source_name(self) -> str:
        return "Open-Meteo Marine"

    def fetch(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 1,
    ) -> Dict[str, Any]:
        """
        Fetch real marine observation and forecast data for the given coordinates.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": forecast_days,
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

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=15,
        )

        response.raise_for_status()
        return response.json()

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert upstream marine response into the standardized OCEANIS
        marine condition structure.
        """
        current = raw_data.get("current", {})

        return {
            "source": self.source_name,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "location": {
                "latitude": raw_data.get("latitude"),
                "longitude": raw_data.get("longitude"),
            },
            "data_type": "OBSERVATION",
            "quality_flag": "REALTIME",
            "conditions": {
                "waves": {
                    "wave_height_m": current.get("wave_height"),
                    "wave_direction_deg": current.get("wave_direction"),
                    "wave_period_s": current.get("wave_period"),
                },
                "swell": {
                    "swell_wave_height_m": current.get("swell_wave_height"),
                    "swell_wave_direction_deg": current.get("swell_wave_direction"),
                    "swell_wave_period_s": current.get("swell_wave_period"),
                },
                "wind_waves": {
                    "wind_wave_height_m": current.get("wind_wave_height"),
                    "wind_wave_direction_deg": current.get("wind_wave_direction"),
                    "wind_wave_period_s": current.get("wind_wave_period"),
                },
                "ocean_current": {
                    "velocity_kmh": current.get("ocean_current_velocity"),
                    "direction_deg": current.get("ocean_current_direction"),
                },
                "sea_surface_temperature_c": current.get("sea_surface_temperature"),
            },
            "raw_timezone": raw_data.get("timezone"),
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a live health check on the marine data provider.
        """
        try:
            self.fetch(
                latitude=16.9891,
                longitude=82.2475,
                forecast_days=1,
            )
            return {
                "source": self.source_name,
                "status": "healthy",
            }
        except Exception as exc:
            return {
                "source": self.source_name,
                "status": "unavailable",
                "error": str(exc),
            }
