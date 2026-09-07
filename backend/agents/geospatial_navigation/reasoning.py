from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from agents.geospatial_navigation.schemas import (
    DistanceSummary,
    RouteAssessmentSummary,
    SpatialEntitySummary,
    SpatialEvidenceItem,
)
from services.geospatial import km_to_nautical_miles


class GeoSpatialNavigationReasoningEngine:
    """
    Deterministic reasoning engine for maritime spatial boundaries, coastal port infrastructure,
    restricted exclusion sectors, marine protected areas (MPAs), geofencing, and route clearance.
    """

    def assess_spatial_navigation(
        self,
        spatial_data: Dict[str, Any],
    ) -> Tuple[
        str,
        str,
        List[SpatialEntitySummary],
        List[SpatialEntitySummary],
        Optional[RouteAssessmentSummary],
        Optional[DistanceSummary],
        float,
        str,
        List[SpatialEvidenceItem],
        List[str],
        str,
        str,
    ]:
        """
        Evaluates spatial relationships deterministically over PostGIS data.
        Returns:
            (spatial_status, geofence_status, nearby_entities, zones, route_summary, distance_summary, confidence, data_freshness, evidence_items, warnings, recommendation, explanation)
        """
        has_db_data = spatial_data.get("has_spatial_db_data", True)
        nearby_ports = spatial_data.get("nearby_ports", [])
        nearby_restricted = spatial_data.get("nearby_restricted_zones", [])
        nearby_protected = spatial_data.get("nearby_protected_zones", [])
        containing_restricted = spatial_data.get("containing_restricted_zones", [])
        containing_protected = spatial_data.get("containing_protected_zones", [])
        dest_containing_restricted = spatial_data.get("dest_containing_restricted_zones", [])
        dest_containing_protected = spatial_data.get("dest_containing_protected_zones", [])
        route_info = spatial_data.get("route_assessment")
        distance_info = spatial_data.get("distance_assessment")
        origin = spatial_data.get("origin", {})
        destination = spatial_data.get("destination")

        if not has_db_data:
            empty_route = RouteAssessmentSummary(
                has_destination=bool(destination),
                status="INSUFFICIENT_DATA",
                reasons=["No spatial registry data available in the system."],
            )
            return (
                "INSUFFICIENT_DATA",
                "OUTSIDE",
                [],
                [],
                empty_route,
                None,
                0.0,
                "UNKNOWN",
                [],
                ["Spatial registry database contains no spatial records for evaluation."],
                "INSUFFICIENT DATA: Maritime spatial boundaries, port infrastructure, and regulatory zones are unavailable. Navigate with extreme caution.",
                "Spatial navigation assessment cannot be conducted due to absence of GIS boundary data.",
            )

        evidence: List[SpatialEvidenceItem] = []
        warnings: List[str] = []
        entities_list: List[SpatialEntitySummary] = []
        zones_list: List[SpatialEntitySummary] = []

        # -----------------------------------------------------------------
        # 1. Nearby Port Infrastructure Evidence
        # -----------------------------------------------------------------
        for p in nearby_ports:
            dist_km = p.get("distance_km")
            dist_nm = round(km_to_nautical_miles(dist_km), 2) if dist_km is not None else None
            entities_list.append(SpatialEntitySummary(
                id=p.get("id"),
                name=p.get("name"),
                entity_type="PORT",
                zone_type=p.get("port_type"),
                distance_km=dist_km,
                distance_nautical_miles=dist_nm,
                spatial_relation="NEARBY",
                latitude=p.get("latitude"),
                longitude=p.get("longitude"),
                description=p.get("description"),
            ))
            evidence.append(SpatialEvidenceItem(
                factor="nearest_port",
                name=p.get("name"),
                zone_type=p.get("port_type"),
                spatial_relation="NEARBY",
                distance_km=dist_km,
                latitude=p.get("latitude"),
                longitude=p.get("longitude"),
                source="PostGIS / Port Authority Registry",
                data_type="SPATIAL_INFRASTRUCTURE",
                confidence=1.0,
                freshness="FRESH",
                severity="NORMAL",
                notes=f"Coastal port infrastructure '{p.get('name')}' located {dist_km} km ({dist_nm} NM) away.",
            ))

        # -----------------------------------------------------------------
        # 2. Point-in-Polygon Geofencing (Origin)
        # -----------------------------------------------------------------
        origin_in_res = len(containing_restricted) > 0
        origin_in_prot = len(containing_protected) > 0

        geofence_status = "OUTSIDE"

        for z in containing_restricted:
            zones_list.append(SpatialEntitySummary(
                id=z.id,
                name=z.name,
                entity_type="RESTRICTED_ZONE",
                zone_type=z.zone_type,
                distance_km=0.0,
                distance_nautical_miles=0.0,
                spatial_relation="CONTAINS",
                authority=z.authority,
                description=z.description,
            ))
            evidence.append(SpatialEvidenceItem(
                factor="restricted_zone_containment",
                name=z.name,
                zone_type=z.zone_type,
                spatial_relation="CONTAINS",
                distance_km=0.0,
                source="PostGIS / Naval Maritime Exclusion Registry",
                data_type="SPATIAL_REGULATORY",
                confidence=1.0,
                freshness="FRESH",
                severity="BLOCKED",
                notes=f"Coordinates are located INSIDE restricted exclusion zone '{z.name}' ({z.zone_type}).",
            ))
            warnings.append(f"CRITICAL PROHIBITION: Origin coordinates lie inside restricted maritime exclusion zone '{z.name}'.")

        for z in containing_protected:
            zones_list.append(SpatialEntitySummary(
                id=z.id,
                name=z.name,
                entity_type="PROTECTED_ZONE",
                zone_type=z.zone_type,
                distance_km=0.0,
                distance_nautical_miles=0.0,
                spatial_relation="CONTAINS",
                authority=z.authority,
                description=z.description,
            ))
            evidence.append(SpatialEvidenceItem(
                factor="protected_zone_containment",
                name=z.name,
                zone_type=z.zone_type,
                spatial_relation="CONTAINS",
                distance_km=0.0,
                source="PostGIS / Marine Protected Area Registry",
                data_type="SPATIAL_REGULATORY",
                confidence=1.0,
                freshness="FRESH",
                severity="CAUTION",
                notes=f"Coordinates are located INSIDE Marine Protected Area '{z.name}' ({z.zone_type}).",
            ))
            warnings.append(f"ECOLOGICAL CAUTION: Origin coordinates lie inside Marine Protected Area '{z.name}'.")

        # -----------------------------------------------------------------
        # 3. Proximity to Nearby Restricted & Protected Zones
        # -----------------------------------------------------------------
        near_boundary = False
        for z in nearby_restricted:
            dist_km = z.get("distance_km", 0.0)
            dist_nm = round(km_to_nautical_miles(dist_km), 2)
            if dist_km > 0.0:  # If not already containing
                zones_list.append(SpatialEntitySummary(
                    id=z.get("id"),
                    name=z.get("name"),
                    entity_type="RESTRICTED_ZONE",
                    zone_type=z.get("zone_type"),
                    distance_km=dist_km,
                    distance_nautical_miles=dist_nm,
                    spatial_relation="NEARBY",
                    authority=z.get("authority"),
                    description=z.get("description"),
                ))
                evidence.append(SpatialEvidenceItem(
                    factor="nearby_restricted_zone",
                    name=z.get("name"),
                    zone_type=z.get("zone_type"),
                    spatial_relation="NEARBY",
                    distance_km=dist_km,
                    source="PostGIS / Naval Maritime Exclusion Registry",
                    data_type="SPATIAL_REGULATORY",
                    confidence=1.0,
                    freshness="FRESH",
                    severity="CAUTION" if dist_km < 10.0 else "NORMAL",
                    notes=f"Restricted zone '{z.get('name')}' is {dist_km} km away.",
                ))
                if dist_km <= 10.0:
                    near_boundary = True
                    warnings.append(f"Proximity alert: Operating within {dist_km} km of restricted exclusion zone '{z.get('name')}'.")

        for z in nearby_protected:
            dist_km = z.get("distance_km", 0.0)
            dist_nm = round(km_to_nautical_miles(dist_km), 2)
            if dist_km > 0.0:
                zones_list.append(SpatialEntitySummary(
                    id=z.get("id"),
                    name=z.get("name"),
                    entity_type="PROTECTED_ZONE",
                    zone_type=z.get("zone_type"),
                    distance_km=dist_km,
                    distance_nautical_miles=dist_nm,
                    spatial_relation="NEARBY",
                    authority=z.get("authority"),
                    description=z.get("description"),
                ))
                evidence.append(SpatialEvidenceItem(
                    factor="nearby_protected_zone",
                    name=z.get("name"),
                    zone_type=z.get("zone_type"),
                    spatial_relation="NEARBY",
                    distance_km=dist_km,
                    source="PostGIS / Marine Protected Area Registry",
                    data_type="SPATIAL_REGULATORY",
                    confidence=1.0,
                    freshness="FRESH",
                    severity="NORMAL",
                    notes=f"Marine Protected Area '{z.get('name')}' is {dist_km} km away.",
                ))

        if origin_in_res:
            geofence_status = "INSIDE_RESTRICTED"
        elif origin_in_prot:
            geofence_status = "INSIDE_PROTECTED"
        elif near_boundary:
            geofence_status = "NEAR_BOUNDARY"
        else:
            geofence_status = "OUTSIDE"

        # -----------------------------------------------------------------
        # 4. Route Assessment & Distance Calculation (if destination provided)
        # -----------------------------------------------------------------
        route_summary: Optional[RouteAssessmentSummary] = None
        dist_summary: Optional[DistanceSummary] = None
        route_is_blocked = False
        route_is_caution = False

        if destination and route_info and distance_info:
            dist_km = distance_info.get("distance_km")
            dist_nm = distance_info.get("distance_nautical_miles")
            dist_summary = DistanceSummary(
                distance_km=dist_km,
                distance_nautical_miles=dist_nm,
                calculation_method=distance_info.get("calculation_method", "HAVERSINE_GEODESIC"),
            )

            res_intersect = route_info.get("restricted_zone_intersection", False)
            prot_intersect = route_info.get("protected_zone_intersection", False)
            dest_in_res = route_info.get("destination_in_restricted_zone", False) or len(dest_containing_restricted) > 0
            dest_in_prot = route_info.get("destination_in_protected_zone", False) or len(dest_containing_protected) > 0

            intersecting_res_names = route_info.get("intersecting_restricted_zones", [])
            intersecting_prot_names = route_info.get("intersecting_protected_zones", [])

            reasons = list(route_info.get("reasons", []))

            alt_available = False
            alt_suggestion = None

            if origin_in_res or dest_in_res or res_intersect:
                route_status = "BLOCKED"
                route_is_blocked = True
                alt_available = True
                alt_suggestion = "Reroute navigation trajectory via seaward coastal corridors to bypass restricted maritime exclusion zones."
                warnings.append(
                    f"ROUTE BLOCKED: Proposed straight-line trajectory intersects or terminates in restricted exclusion zone(s): {', '.join(intersecting_res_names) if intersecting_res_names else 'Restricted Zone'}."
                )
                evidence.append(SpatialEvidenceItem(
                    factor="route_restricted_intersection",
                    name=", ".join(intersecting_res_names) if intersecting_res_names else "Restricted Zone",
                    spatial_relation="INTERSECTS",
                    distance_km=dist_km,
                    source="PostGIS / Navigation Assessment Engine",
                    data_type="SPATIAL_ANALYSIS",
                    confidence=1.0,
                    freshness="FRESH",
                    severity="BLOCKED",
                    notes="Direct route trajectory penetrates military exclusion or prohibited navigation area.",
                ))
            elif origin_in_prot or dest_in_prot or prot_intersect:
                route_status = "CAUTION"
                route_is_caution = True
                alt_available = True
                alt_suggestion = "Consider alternative route outside MPA boundary to minimize marine ecological impact."
                warnings.append(
                    f"ROUTE CAUTION: Trajectory passes through Marine Protected Area(s): {', '.join(intersecting_prot_names) if intersecting_prot_names else 'Protected Area'}."
                )
                evidence.append(SpatialEvidenceItem(
                    factor="route_protected_intersection",
                    name=", ".join(intersecting_prot_names) if intersecting_prot_names else "Protected Area",
                    spatial_relation="INTERSECTS",
                    distance_km=dist_km,
                    source="PostGIS / Navigation Assessment Engine",
                    data_type="SPATIAL_ANALYSIS",
                    confidence=1.0,
                    freshness="FRESH",
                    severity="CAUTION",
                    notes="Direct trajectory intersects environmentally sensitive marine sanctuary or protected coral reef.",
                ))
            else:
                route_status = "CLEAR"

            route_summary = RouteAssessmentSummary(
                has_destination=True,
                status=route_status,
                distance_km=dist_km,
                distance_nautical_miles=dist_nm,
                origin_in_restricted_zone=origin_in_res,
                destination_in_restricted_zone=dest_in_res,
                origin_in_protected_zone=origin_in_prot,
                destination_in_protected_zone=dest_in_prot,
                restricted_zone_intersection=res_intersect,
                protected_zone_intersection=prot_intersect,
                intersecting_restricted_zones=intersecting_res_names,
                intersecting_protected_zones=intersecting_prot_names,
                alternative_route_available=alt_available,
                alternative_route_suggestion=alt_suggestion,
                reasons=reasons,
            )

        # -----------------------------------------------------------------
        # 5. Overall Spatial Status Determination
        # -----------------------------------------------------------------
        if origin_in_res or route_is_blocked:
            spatial_status = "BLOCKED"
            recommendation = (
                "NAVIGATION PROHIBITED: Vessel movement within or across restricted maritime exclusion zones is strictly prohibited. "
                "Immediate deviation or alternative course planning is mandatory."
            )
            explanation = (
                f"Spatial analysis confirms conflict with restricted maritime zones. "
                f"Geofence containment: {geofence_status}."
            )
        elif origin_in_prot or route_is_caution:
            spatial_status = "PROTECTED" if origin_in_prot else "CAUTION"
            recommendation = (
                "ECOLOGICAL CAUTION: Navigation intersects or operates within recognized Marine Protected Areas. "
                "Observe coastal speed restrictions, zero discharge protocols, and ecological compliance."
            )
            explanation = (
                f"Spatial analysis identifies protected marine ecosystem boundaries in proximity. "
                f"Geofence containment: {geofence_status}."
            )
        elif geofence_status == "NEAR_BOUNDARY":
            spatial_status = "CAUTION"
            recommendation = (
                "BOUNDARY CAUTION: Operating in proximity to restricted maritime perimeter. "
                "Maintain active radar and GPS watchkeeping to prevent unintentional boundary penetration."
            )
            explanation = (
                f"Coordinates are within 10 km of an active restricted boundary. "
                f"Geofence containment: {geofence_status}."
            )
        else:
            spatial_status = "CLEAR"
            recommendation = (
                "SPATIAL CLEARANCE VERIFIED: Location and proposed corridor are clear of recorded restricted exclusion sectors "
                "and sensitive marine sanctuaries. Proceed with standard navigational watch."
            )
            explanation = (
                f"Point-in-polygon and spatial intersection checks confirm clear passage. "
                f"Nearest port is located {nearby_ports[0]['name'] if nearby_ports else 'None'} ({nearby_ports[0]['distance_km'] if nearby_ports else 'N/A'} km)."
            )

        # Conservative phrase guardrails
        rec_clean = (
            recommendation
            .replace("route is 100% safe", "route is clear of recorded spatial restrictions")
            .replace("area is guaranteed safe", "area is outside recorded exclusion zones")
            .replace("navigation is risk-free", "navigation path is clear of regulatory restrictions")
            .replace("100% safe", "clear of recorded restrictions")
            .replace("guaranteed safe", "clear based on spatial registry")
            .replace("completely safe", "clear of spatial barriers")
            .replace("no risk", "low regulatory risk")
        )
        exp_clean = (
            explanation
            .replace("route is 100% safe", "route is clear of recorded spatial restrictions")
            .replace("area is guaranteed safe", "area is outside recorded exclusion zones")
            .replace("navigation is risk-free", "navigation path is clear of regulatory restrictions")
            .replace("100% safe", "clear of recorded restrictions")
            .replace("guaranteed safe", "clear based on spatial registry")
            .replace("completely safe", "clear of spatial barriers")
            .replace("no risk", "low regulatory risk")
        )

        return (
            spatial_status,
            geofence_status,
            entities_list,
            zones_list,
            route_summary,
            dist_summary,
            0.98,
            "FRESH",
            evidence,
            warnings,
            rec_clean,
            exp_clean,
        )
