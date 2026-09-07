from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from geoalchemy2 import Geography
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models.earth_observation import EarthObservation
from models.geospatial import Port, ProtectedZone, RestrictedZone
from models.marine import MarineObservation
from models.weather import WeatherObservation
from services.disaster import DisasterService
from services.freshness import FreshnessCategory, evaluate_freshness
from services.geospatial import GeoSpatialService, haversine_distance, km_to_nautical_miles
from services.marine_operations import MarineOperationsService
from services.navigation import NavigationService


class FishingDataCollector:
    """
    Retrieves and normalizes evidence from existing OCEANIS backend layers
    (Weather, Marine, Earth Observation, Geo-Spatial, Disaster & Safety, Operations).
    Does not make raw third-party external API requests directly.
    """

    @staticmethod
    def get_weather_evidence(
        db: Session,
        latitude: float,
        longitude: float,
        current_time: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves local atmospheric telemetry for the specified coordinates.
        """
        now = current_time or datetime.now(timezone.utc)
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)

        weather_point = func.ST_SetSRID(
            func.ST_MakePoint(WeatherObservation.longitude, WeatherObservation.latitude), 4326
        )
        latest_weather = (
            db.query(WeatherObservation)
            .filter(func.ST_DWithin(func.cast(weather_point, Geography), point_geog, 100000.0))
            .order_by(WeatherObservation.observed_at.desc())
            .first()
        )

        if not latest_weather:
            return None

        freshness = evaluate_freshness(latest_weather.observed_at, current_time=now)
        return {
            "temperature_c": latest_weather.temperature_c,
            "humidity_percent": latest_weather.humidity_percent,
            "wind_speed_kmh": latest_weather.wind_speed_kmh,
            "wind_direction_deg": latest_weather.wind_direction_deg,
            "precipitation_mm": latest_weather.precipitation_mm,
            "observed_at": latest_weather.observed_at.isoformat(),
            "source": latest_weather.source,
            "source_timezone": latest_weather.source_timezone,
            "freshness": freshness,
            "latitude": latest_weather.latitude,
            "longitude": latest_weather.longitude,
        }

    @staticmethod
    def get_marine_evidence(
        db: Session,
        latitude: float,
        longitude: float,
        current_time: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves local oceanographic/wave telemetry for the specified coordinates.
        """
        now = current_time or datetime.now(timezone.utc)
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)

        marine_geom = func.ST_SetSRID(
            func.ST_MakePoint(MarineObservation.longitude, MarineObservation.latitude), 4326
        )
        latest_marine = (
            db.query(MarineObservation)
            .filter(func.ST_DWithin(func.cast(marine_geom, Geography), point_geog, 100000.0))
            .order_by(MarineObservation.observed_at.desc())
            .first()
        )

        if not latest_marine:
            return None

        freshness = evaluate_freshness(latest_marine.observed_at, current_time=now)
        return {
            "wave_height_m": latest_marine.wave_height_m,
            "wave_direction_deg": latest_marine.wave_direction_deg,
            "wave_period_s": latest_marine.wave_period_s,
            "swell_wave_height_m": latest_marine.swell_wave_height_m,
            "swell_wave_direction_deg": latest_marine.swell_wave_direction_deg,
            "swell_wave_period_s": latest_marine.swell_wave_period_s,
            "wind_wave_height_m": latest_marine.wind_wave_height_m,
            "ocean_current_velocity_kmh": latest_marine.ocean_current_velocity_kmh,
            "ocean_current_direction_deg": latest_marine.ocean_current_direction_deg,
            "sea_surface_temperature_c": latest_marine.sea_surface_temperature_c,
            "observed_at": latest_marine.observed_at.isoformat(),
            "source": latest_marine.source,
            "data_type": latest_marine.data_type,
            "quality_flag": latest_marine.quality_flag,
            "freshness": freshness,
            "latitude": latest_marine.latitude,
            "longitude": latest_marine.longitude,
        }

    @staticmethod
    def get_earth_observation_evidence(
        db: Session,
        latitude: float,
        longitude: float,
        current_time: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves satellite-derived ocean colour, SST, and optical observations.
        """
        now = current_time or datetime.now(timezone.utc)
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)

        eo_geom = func.ST_SetSRID(
            func.ST_MakePoint(EarthObservation.longitude, EarthObservation.latitude), 4326
        )
        latest_eo = (
            db.query(EarthObservation)
            .filter(func.ST_DWithin(func.cast(eo_geom, Geography), point_geog, 100000.0))
            .order_by(EarthObservation.observed_at.desc())
            .first()
        )

        if not latest_eo:
            return None

        freshness = evaluate_freshness(latest_eo.observed_at, current_time=now)
        return {
            "sea_surface_temperature_c": latest_eo.sea_surface_temperature_c,
            "chlorophyll_a_mg_m3": latest_eo.chlorophyll_a_mg_m3,
            "ocean_colour": latest_eo.ocean_colour,
            "cloud_cover_percent": latest_eo.cloud_cover_percent,
            "solar_radiation_w_m2": latest_eo.solar_radiation_w_m2,
            "satellite_platform": latest_eo.satellite_platform,
            "sensor_instrument": latest_eo.sensor_instrument,
            "product_type": latest_eo.product_type,
            "observed_at": latest_eo.observed_at.isoformat(),
            "source": latest_eo.source,
            "source_url": latest_eo.source_url,
            "freshness": freshness,
            "latitude": latest_eo.latitude,
            "longitude": latest_eo.longitude,
        }

    @staticmethod
    def get_geospatial_evidence(
        db: Session,
        latitude: float,
        longitude: float,
        destination_lat: Optional[float] = None,
        destination_lon: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves nearby ports, containing marine protected areas and restricted naval sectors.
        """
        nearby_ports = GeoSpatialService.get_nearby_ports(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=150.0,
            active_only=True,
        )
        containing_restricted = GeoSpatialService.get_containing_restricted_zones(
            db=db,
            latitude=latitude,
            longitude=longitude,
            active_only=True,
        )
        containing_protected = GeoSpatialService.get_containing_protected_zones(
            db=db,
            latitude=latitude,
            longitude=longitude,
            active_only=True,
        )

        route_info = None
        if destination_lat is not None and destination_lon is not None:
            route_info = NavigationService.assess_route(
                db=db,
                origin_lat=latitude,
                origin_lon=longitude,
                dest_lat=destination_lat,
                dest_lon=destination_lon,
            )

        return {
            "nearest_ports": nearby_ports[:3] if nearby_ports else [],
            "in_restricted_zone": len(containing_restricted) > 0,
            "in_protected_zone": len(containing_protected) > 0,
            "restricted_zones": [z.name for z in containing_restricted],
            "protected_zones": [z.name for z in containing_protected],
            "route_assessment": route_info,
        }

    @staticmethod
    def get_disaster_safety_evidence(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
        current_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Executes deterministic spatial safety assessment via the Disaster & Safety layer.
        """
        return DisasterService.assess_safety(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            now=current_time,
        )

    @staticmethod
    def get_operations_evidence(
        db: Session,
        origin_lat: float,
        origin_lon: float,
        destination_lat: Optional[float] = None,
        destination_lon: Optional[float] = None,
        speed_kmh: Optional[float] = None,
        current_time: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves voyage travel time, distance, and transit assessment if destination provided.
        """
        if destination_lat is None or destination_lon is None:
            return None

        dist_res = MarineOperationsService.calculate_distance(
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=destination_lat,
            dest_lon=destination_lon,
        )
        dist_km = dist_res["distance_km"]
        duration_min = MarineOperationsService.estimate_duration(dist_km, speed_kmh)

        return {
            "distance_km": dist_km,
            "distance_nautical_miles": dist_res["distance_nautical_miles"],
            "speed_kmh": speed_kmh,
            "estimated_duration_minutes": duration_min,
            "estimated_duration_hours": round(duration_min / 60.0, 2) if duration_min else None,
        }
