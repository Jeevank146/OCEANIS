from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from agents.geospatial_navigation.collector import GeoSpatialNavigationDataCollector
from agents.geospatial_navigation.reasoning import GeoSpatialNavigationReasoningEngine
from agents.geospatial_navigation.schemas import (
    GeoSpatialNavigationAssessmentResponse,
    GeoSpatialNavigationQuery,
)


class GeoSpatialNavigationIntelligenceAgent:
    """
    OCEANIS Geo-Spatial & Navigation Intelligence Domain Agent.
    Owns the complete spatial and navigation domain:
    - Geographic coordinate validation and spatial queries
    - Coastal ports and maritime infrastructure
    - Maritime boundaries, restricted zones, and protected marine sanctuaries
    - Geofence containment (INSIDE_RESTRICTED, INSIDE_PROTECTED, NEAR_BOUNDARY, OUTSIDE)
    - Geodesic distance calculation and straight-line trajectory geometry
    - Spatial route clearance, barrier intersections, and alternative route guidance
    - Strict deterministic BLOCKED enforcement when intersecting exclusion zones
    """

    def __init__(
        self,
        data_collector: Optional[GeoSpatialNavigationDataCollector] = None,
        reasoning_engine: Optional[GeoSpatialNavigationReasoningEngine] = None,
    ):
        self.collector = data_collector or GeoSpatialNavigationDataCollector()
        self.reasoning = reasoning_engine or GeoSpatialNavigationReasoningEngine()

    def assess(
        self,
        db: Session,
        query: GeoSpatialNavigationQuery,
        now: Optional[datetime] = None,
    ) -> GeoSpatialNavigationAssessmentResponse:
        """
        Executes PostGIS spatial analysis, geofencing, route intersection checks,
        and deterministic regulatory reasoning for the given query.
        """
        current_time = now or datetime.now(timezone.utc)
        lat = query.latitude
        lon = query.longitude
        dest_lat = query.destination_latitude
        dest_lon = query.destination_longitude

        # 1. Collect spatial evidence via PostGIS layer
        spatial_data = self.collector.get_spatial_evidence(
            db=db,
            latitude=lat,
            longitude=lon,
            destination_latitude=dest_lat,
            destination_longitude=dest_lon,
        )

        # 2. Perform deterministic spatial navigation reasoning
        (
            spatial_status,
            geofence_status,
            nearby_entities,
            zones,
            route_summary,
            dist_summary,
            confidence,
            data_freshness,
            evidence_items,
            warnings,
            recommendation,
            explanation,
        ) = self.reasoning.assess_spatial_navigation(spatial_data=spatial_data)

        origin_dict = {"latitude": lat, "longitude": lon}
        dest_dict = (
            {"latitude": dest_lat, "longitude": dest_lon}
            if dest_lat is not None and dest_lon is not None
            else None
        )

        return GeoSpatialNavigationAssessmentResponse(
            agent="geospatial_navigation",
            origin=origin_dict,
            destination=dest_dict,
            spatial_status=spatial_status,
            geofence_status=geofence_status,
            nearby_entities=nearby_entities,
            zones=zones,
            route=route_summary,
            distance=dist_summary,
            confidence=confidence,
            data_freshness=data_freshness,
            evidence=evidence_items,
            warnings=warnings,
            recommendation=recommendation,
            explanation=explanation,
            generated_at=current_time,
        )
