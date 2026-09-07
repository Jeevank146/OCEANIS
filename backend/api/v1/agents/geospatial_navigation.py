from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from agents.geospatial_navigation.schemas import (
    GeoSpatialNavigationAssessmentResponse,
    GeoSpatialNavigationQuery,
)
from agents.geospatial_navigation.service import GeoSpatialNavigationAgentService
from database import get_db

router = APIRouter(prefix="/agents/geospatial-navigation", tags=["Geo-Spatial Navigation"])
geospatial_nav_service = GeoSpatialNavigationAgentService()


@router.post(
    "/assess",
    response_model=GeoSpatialNavigationAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess spatial navigation, ports, geofencing, and route clearance",
    description=(
        "Executes PostGIS-powered spatial intelligence to evaluate proximity to coastal ports, "
        "geofence containment across military restricted zones and marine protected areas, "
        "geodesic distances, route trajectory intersections, and deterministic navigation clearance."
    ),
)
def assess_geospatial_navigation(
    payload: GeoSpatialNavigationQuery,
    db: Session = Depends(get_db),
) -> Any:
    """
    Assesses maritime spatial boundaries, restricted zones, and route clearances.
    """
    return geospatial_nav_service.assess_geospatial_navigation(db=db, query=payload)
