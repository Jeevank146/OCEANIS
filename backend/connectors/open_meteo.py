from datetime import datetime, timezone
from typing import Any, Dict

import requests

from connectors.base import BaseDataConnector


class OpenMeteoConnector(BaseDataConnector):
    """
    Connector for retrieving weather data from Open-Meteo.

    This connector is intended for development/fallback weather data.
    Safety-critical decisions should prioritize validated official
    marine/weather sources such as IMD and INCOIS.
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    @property
    def source_name(self) -> str:
        return "Open-Meteo"

    def fetch(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 3,
    ) -> Dict[str, Any]:
        """
        Fetch current and forecast weather data.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": forecast_days,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "wind_speed_10m,"
                "wind_direction_10m,"
                "precipitation"
            ),
            "hourly": (
                "temperature_2m,"
                "precipitation_probability,"
                "wind_speed_10m,"
                "wind_direction_10m"
            ),
            "timezone": "UTC",
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=20,
        )

        response.raise_for_status()

        return response.json()

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Open-Meteo response into a small OCEANIS-compatible structure.
        """
        current = raw_data.get("current", {})

        return {
            "source": self.source_name,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "location": {
                "latitude": raw_data.get("latitude"),
                "longitude": raw_data.get("longitude"),
            },
            "current": {
                "temperature_c": current.get("temperature_2m"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
                "wind_direction_deg": current.get("wind_direction_10m"),
                "precipitation_mm": current.get("precipitation"),
            },
            "raw_timezone": raw_data.get("timezone"),
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Basic connector availability check.
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