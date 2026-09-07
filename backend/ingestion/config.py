import os
import json
from dataclasses import dataclass, field
from typing import List, Tuple
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MonitoredLocation:
    name: str
    latitude: float
    longitude: float


@dataclass
class IngestionConfig:
    """
    Configuration settings for OCEANIS automated background ingestion and caching.
    Reads environment variables with production-grade sensible defaults.
    """
    enabled: bool = field(
        default_factory=lambda: os.getenv("OCEANIS_INGESTION_ENABLED", "true").lower() in ("true", "1", "yes")
    )
    
    # Provider-specific ingestion intervals (in minutes)
    incois_interval_minutes: int = field(
        default_factory=lambda: int(os.getenv("OCEANIS_INCOIS_INTERVAL_MINUTES", "60"))
    )
    copernicus_interval_minutes: int = field(
        default_factory=lambda: int(os.getenv("OCEANIS_COPERNICUS_INTERVAL_MINUTES", "180"))
    )
    eo_interval_minutes: int = field(
        default_factory=lambda: int(os.getenv("OCEANIS_EO_INTERVAL_MINUTES", "360"))
    )
    imd_interval_minutes: int = field(
        default_factory=lambda: int(os.getenv("OCEANIS_IMD_INTERVAL_MINUTES", "60"))
    )
    
    # Default monitored coastal stations
    locations: List[MonitoredLocation] = field(
        default_factory=lambda: [
            MonitoredLocation(name="Visakhapatnam Coast", latitude=17.6868, longitude=83.2185),
            MonitoredLocation(name="Kakinada Coast", latitude=16.9891, longitude=82.2475),
            MonitoredLocation(name="Chennai Coast", latitude=13.0827, longitude=80.2707),
            MonitoredLocation(name="Mumbai Coast", latitude=18.9220, longitude=72.8347),
            MonitoredLocation(name="Kochi Coast", latitude=9.9312, longitude=76.2673),
        ]
    )

    @classmethod
    def from_env(cls) -> "IngestionConfig":
        config = cls()
        custom_locs = os.getenv("OCEANIS_MONITORED_LOCATIONS")
        if custom_locs:
            try:
                parsed = json.loads(custom_locs)
                if isinstance(parsed, list):
                    config.locations = [
                        MonitoredLocation(
                            name=item.get("name", f"Loc_{idx}"),
                            latitude=float(item["latitude"]),
                            longitude=float(item["longitude"]),
                        )
                        for idx, item in enumerate(parsed)
                    ]
            except Exception:
                pass
        return config
