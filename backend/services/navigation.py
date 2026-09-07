from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.geospatial import ProtectedZone, RestrictedZone
from services.geospatial import haversine_distance, km_to_nautical_miles


class NavigationService:
    """
    Navigation Assessment Engine for assessing routes, path distance,
    and spatial intersections against maritime restricted and protected zones.
    """

    @staticmethod
    def calculate_distance(
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> Dict[str, Any]:
        """
        Calculates geodesic distance between origin and destination.
        """
        dist_km = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        dist_nm = km_to_nautical_miles(dist_km)

        return {
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "destination": {"latitude": dest_lat, "longitude": dest_lon},
            "distance_km": round(dist_km, 2),
            "distance_nautical_miles": round(dist_nm, 2),
            "calculation_method": "HAVERSINE_GEODESIC",
        }

    @staticmethod
    def assess_route(
        db: Session,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> Dict[str, Any]:
        """
        Performs spatial route assessment for straight-line navigation path
        between origin and destination coordinates.
        """
        dist_km = round(haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon), 2)
        dist_nm = round(km_to_nautical_miles(dist_km), 2)

        # PostGIS Geometry definitions for points and straight-line path
        orig_pt = func.ST_SetSRID(func.ST_MakePoint(origin_lon, origin_lat), 4326)
        dest_pt = func.ST_SetSRID(func.ST_MakePoint(dest_lon, dest_lat), 4326)
        line_geom = func.ST_MakeLine(orig_pt, dest_pt)

        # 1. Point-in-polygon checks for endpoints
        orig_restricted = (
            db.query(RestrictedZone)
            .filter(RestrictedZone.is_active.is_(True))
            .filter(func.ST_Contains(RestrictedZone.geometry, orig_pt))
            .all()
        )
        dest_restricted = (
            db.query(RestrictedZone)
            .filter(RestrictedZone.is_active.is_(True))
            .filter(func.ST_Contains(RestrictedZone.geometry, dest_pt))
            .all()
        )

        orig_protected = (
            db.query(ProtectedZone)
            .filter(ProtectedZone.is_active.is_(True))
            .filter(func.ST_Contains(ProtectedZone.geometry, orig_pt))
            .all()
        )
        dest_protected = (
            db.query(ProtectedZone)
            .filter(ProtectedZone.is_active.is_(True))
            .filter(func.ST_Contains(ProtectedZone.geometry, dest_pt))
            .all()
        )

        # 2. Path trajectory intersection checks
        intersecting_restricted = (
            db.query(RestrictedZone)
            .filter(RestrictedZone.is_active.is_(True))
            .filter(func.ST_Intersects(RestrictedZone.geometry, line_geom))
            .all()
        )

        intersecting_protected = (
            db.query(ProtectedZone)
            .filter(ProtectedZone.is_active.is_(True))
            .filter(func.ST_Intersects(ProtectedZone.geometry, line_geom))
            .all()
        )

        origin_in_res = len(orig_restricted) > 0
        dest_in_res = len(dest_restricted) > 0
        origin_in_prot = len(orig_protected) > 0
        dest_in_prot = len(dest_protected) > 0

        res_intersect = len(intersecting_restricted) > 0
        prot_intersect = len(intersecting_protected) > 0

        res_zone_names = [z.name for z in intersecting_restricted]
        prot_zone_names = [z.name for z in intersecting_protected]

        # 3. Derive status and reasons
        reasons: List[str] = []

        if origin_in_res or dest_in_res or res_intersect:
            nav_status = "RESTRICTED"
            if origin_in_res:
                reasons.append(f"Origin lies within restricted zone: {', '.join(z.name for z in orig_restricted)}")
            if dest_in_res:
                reasons.append(f"Destination lies within restricted zone: {', '.join(z.name for z in dest_restricted)}")
            if res_intersect and not origin_in_res and not dest_in_res:
                reasons.append(f"Direct trajectory intersects active restricted zone(s): {', '.join(res_zone_names)}")
        elif origin_in_prot or dest_in_prot or prot_intersect:
            nav_status = "CAUTION"
            if origin_in_prot:
                reasons.append(f"Origin is located in sensitive marine protected area: {', '.join(z.name for z in orig_protected)}")
            if dest_in_prot:
                reasons.append(f"Destination is located in sensitive marine protected area: {', '.join(z.name for z in dest_protected)}")
            if prot_intersect and not origin_in_prot and not dest_in_prot:
                reasons.append(f"Direct trajectory passes through marine protected area(s): {', '.join(prot_zone_names)}")
        else:
            nav_status = "CLEAR"
            reasons.append("Path is clear of recorded maritime restricted zones and sensitive protected areas.")

        return {
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "destination": {"latitude": dest_lat, "longitude": dest_lon},
            "distance_km": dist_km,
            "distance_nautical_miles": dist_nm,
            "origin_in_restricted_zone": origin_in_res,
            "destination_in_restricted_zone": dest_in_res,
            "origin_in_protected_zone": origin_in_prot,
            "destination_in_protected_zone": dest_in_prot,
            "restricted_zone_intersection": res_intersect,
            "protected_zone_intersection": prot_intersect,
            "intersecting_restricted_zones": res_zone_names,
            "intersecting_protected_zones": prot_zone_names,
            "navigation_status": nav_status,
            "reasons": reasons,
        }
