from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.geospatial import Port, ProtectedZone, RestrictedZone
from services.geospatial import GeoSpatialService, km_to_nautical_miles
from services.navigation import NavigationService


class GeoSpatialNavigationDataCollector:
    """
    Retrieves and normalizes spatial and regulatory navigation evidence from the
    existing OCEANIS Geo-Spatial & Navigation data layer (PostGIS).
    Preserves spatial coordinates, geometry intersections, containment, ports,
    restricted zones, protected areas, and geodesic distances.
    """

    @staticmethod
    def get_spatial_evidence(
        db: Session,
        latitude: float,
        longitude: float,
        destination_latitude: Optional[float] = None,
        destination_longitude: Optional[float] = None,
        radius_km: float = 100.0,
    ) -> Dict[str, Any]:
        """
        Gathers comprehensive spatial evidence for an origin coordinate and optional destination.
        """
        # 1. Total counts in database to detect empty database scenario
        total_ports = db.query(Port).count()
        total_restricted = db.query(RestrictedZone).count()
        total_protected = db.query(ProtectedZone).count()
        has_spatial_db_data = (total_ports + total_restricted + total_protected) > 0

        # 2. Origin Proximity & Containment
        nearby_ports = GeoSpatialService.get_nearby_ports(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=max(radius_km, 150.0),
            active_only=True,
        )

        nearby_restricted = GeoSpatialService.get_nearby_restricted_zones(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            active_only=True,
        )

        nearby_protected = GeoSpatialService.get_nearby_protected_zones(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
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

        # 3. Destination Evaluation & Route Assessment (if destination coordinates provided)
        route_info: Optional[Dict[str, Any]] = None
        distance_info: Optional[Dict[str, Any]] = None
        dest_containing_restricted: List[RestrictedZone] = []
        dest_containing_protected: List[ProtectedZone] = []

        if destination_latitude is not None and destination_longitude is not None:
            distance_info = NavigationService.calculate_distance(
                origin_lat=latitude,
                origin_lon=longitude,
                dest_lat=destination_latitude,
                dest_lon=destination_longitude,
            )

            route_info = NavigationService.assess_route(
                db=db,
                origin_lat=latitude,
                origin_lon=longitude,
                dest_lat=destination_latitude,
                dest_lon=destination_longitude,
            )

            dest_containing_restricted = GeoSpatialService.get_containing_restricted_zones(
                db=db,
                latitude=destination_latitude,
                longitude=destination_longitude,
                active_only=True,
            )

            dest_containing_protected = GeoSpatialService.get_containing_protected_zones(
                db=db,
                latitude=destination_latitude,
                longitude=destination_longitude,
                active_only=True,
            )

        return {
            "has_spatial_db_data": has_spatial_db_data,
            "origin": {"latitude": latitude, "longitude": longitude},
            "destination": (
                {"latitude": destination_latitude, "longitude": destination_longitude}
                if destination_latitude is not None and destination_longitude is not None
                else None
            ),
            "nearby_ports": nearby_ports,
            "nearby_restricted_zones": nearby_restricted,
            "nearby_protected_zones": nearby_protected,
            "containing_restricted_zones": containing_restricted,
            "containing_protected_zones": containing_protected,
            "dest_containing_restricted_zones": dest_containing_restricted,
            "dest_containing_protected_zones": dest_containing_protected,
            "route_assessment": route_info,
            "distance_assessment": distance_info,
        }
