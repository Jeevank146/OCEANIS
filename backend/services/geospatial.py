import json
import math
from typing import Any, Dict, List, Optional, Tuple

from geoalchemy2 import Geography
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.geospatial import Port, ProtectedZone, RestrictedZone


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two geospatial coordinates
    on Earth (WGS84 ellipsoid approximation) in kilometers.
    """
    r = 6371.0  # Earth mean radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def km_to_nautical_miles(km: float) -> float:
    """
    Converts kilometers to international nautical miles (1 NM = 1.852 km).
    """
    return km / 1.852


class GeoSpatialService:
    """
    Reusable PostGIS spatial query service for ports, restricted zones,
    and protected marine sanctuaries.
    """

    @staticmethod
    def get_nearby_ports(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find ports within radius_km of given coordinates using PostGIS geography ST_DWithin.
        """
        radius_meters = radius_km * 1000.0

        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)
        port_geog = func.cast(Port.location, Geography)

        distance_km_expr = func.ST_Distance(port_geog, point_geog) / 1000.0
        geojson_expr = func.ST_AsGeoJSON(Port.location)

        query = db.query(
            Port,
            distance_km_expr.label("distance_km"),
            geojson_expr.label("geojson"),
        ).filter(
            func.ST_DWithin(port_geog, point_geog, radius_meters)
        )

        if active_only:
            query = query.filter(Port.is_active.is_(True))

        query = query.order_by("distance_km")

        results = []
        for port, dist_km, geojson_str in query.all():
            results.append({
                "id": port.id,
                "name": port.name,
                "port_type": port.port_type,
                "latitude": port.latitude,
                "longitude": port.longitude,
                "country": port.country,
                "state": port.state,
                "district": port.district,
                "description": port.description,
                "is_active": port.is_active,
                "distance_km": round(float(dist_km), 2) if dist_km is not None else None,
                "location_geojson": json.loads(geojson_str) if geojson_str else None,
                "created_at": port.created_at,
                "updated_at": port.updated_at,
            })
        return results

    @staticmethod
    def get_nearby_restricted_zones(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find restricted zones within radius_km of coordinates using PostGIS.
        """
        radius_meters = radius_km * 1000.0
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)
        zone_geog = func.cast(RestrictedZone.geometry, Geography)

        distance_km_expr = func.ST_Distance(zone_geog, point_geog) / 1000.0
        geojson_expr = func.ST_AsGeoJSON(RestrictedZone.geometry)

        query = db.query(
            RestrictedZone,
            distance_km_expr.label("distance_km"),
            geojson_expr.label("geojson"),
        ).filter(
            func.ST_DWithin(zone_geog, point_geog, radius_meters)
        )

        if active_only:
            query = query.filter(RestrictedZone.is_active.is_(True))

        query = query.order_by("distance_km")

        results = []
        for zone, dist_km, geojson_str in query.all():
            results.append({
                "id": zone.id,
                "name": zone.name,
                "zone_type": zone.zone_type,
                "description": zone.description,
                "authority": zone.authority,
                "is_active": zone.is_active,
                "distance_km": round(float(dist_km), 2) if dist_km is not None else 0.0,
                "geometry_geojson": json.loads(geojson_str) if geojson_str else None,
                "created_at": zone.created_at,
                "updated_at": zone.updated_at,
            })
        return results

    @staticmethod
    def get_nearby_protected_zones(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find protected/sensitive marine zones within radius_km using PostGIS.
        """
        radius_meters = radius_km * 1000.0
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)
        zone_geog = func.cast(ProtectedZone.geometry, Geography)

        distance_km_expr = func.ST_Distance(zone_geog, point_geog) / 1000.0
        geojson_expr = func.ST_AsGeoJSON(ProtectedZone.geometry)

        query = db.query(
            ProtectedZone,
            distance_km_expr.label("distance_km"),
            geojson_expr.label("geojson"),
        ).filter(
            func.ST_DWithin(zone_geog, point_geog, radius_meters)
        )

        if active_only:
            query = query.filter(ProtectedZone.is_active.is_(True))

        query = query.order_by("distance_km")

        results = []
        for zone, dist_km, geojson_str in query.all():
            results.append({
                "id": zone.id,
                "name": zone.name,
                "zone_type": zone.zone_type,
                "description": zone.description,
                "authority": zone.authority,
                "is_active": zone.is_active,
                "distance_km": round(float(dist_km), 2) if dist_km is not None else 0.0,
                "geometry_geojson": json.loads(geojson_str) if geojson_str else None,
                "created_at": zone.created_at,
                "updated_at": zone.updated_at,
            })
        return results


    @staticmethod
    def get_containing_restricted_zones(
        db: Session,
        latitude: float,
        longitude: float,
        active_only: bool = True,
    ) -> List[RestrictedZone]:
        """
        Point-in-polygon check: returns all active restricted zones containing the point.
        """
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        query = db.query(RestrictedZone).filter(
            func.ST_Contains(RestrictedZone.geometry, point_geom)
        )
        if active_only:
            query = query.filter(RestrictedZone.is_active.is_(True))
        return query.all()

    @staticmethod
    def get_containing_protected_zones(
        db: Session,
        latitude: float,
        longitude: float,
        active_only: bool = True,
    ) -> List[ProtectedZone]:
        """
        Point-in-polygon check: returns all active protected zones containing the point.
        """
        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        query = db.query(ProtectedZone).filter(
            func.ST_Contains(ProtectedZone.geometry, point_geom)
        )
        if active_only:
            query = query.filter(ProtectedZone.is_active.is_(True))
        return query.all()
