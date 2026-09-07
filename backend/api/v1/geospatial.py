import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.geospatial import Port, ProtectedZone, RestrictedZone
from schemas.geospatial import (
    DistanceCalculationResponse,
    NearbyZonesResponse,
    PortResponse,
    ProtectedZoneResponse,
    RestrictedZoneResponse,
    RouteAssessmentResponse,
)
from services.geospatial import GeoSpatialService
from services.navigation import NavigationService

router = APIRouter(
    prefix="/geospatial",
    tags=["Geo-Spatial"],
)


@router.get(
    "/ports",
    response_model=List[PortResponse],
    summary="List or query nearby maritime ports",
    description=(
        "Retrieves ports registered in OCEANIS. If latitude and longitude are supplied, "
        "filters for ports within the specified radius (in km) and orders them by proximity."
    ),
)
def get_ports(
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Latitude of query origin"),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Longitude of query origin"),
    radius_km: float = Query(50.0, ge=0.1, le=5000.0, description="Search radius in kilometers"),
    active_only: bool = Query(True, description="Filter for operational ports only"),
    db: Session = Depends(get_db),
):
    if latitude is not None and longitude is not None:
        return GeoSpatialService.get_nearby_ports(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            active_only=active_only,
        )

    query = db.query(Port, func.ST_AsGeoJSON(Port.location).label("geojson"))
    if active_only:
        query = query.filter(Port.is_active.is_(True))

    results = []
    for port, geojson_str in query.order_by(Port.name.asc()).all():
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
            "distance_km": None,
            "location_geojson": json.loads(geojson_str) if geojson_str else None,
            "created_at": port.created_at,
            "updated_at": port.updated_at,
        })
    return results


@router.get(
    "/ports/{port_id}",
    response_model=PortResponse,
    summary="Get single port by ID",
)
def get_port_by_id(
    port_id: int,
    db: Session = Depends(get_db),
):
    row = (
        db.query(Port, func.ST_AsGeoJSON(Port.location).label("geojson"))
        .filter(Port.id == port_id)
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Port with ID {port_id} not found",
        )
    port, geojson_str = row
    return {
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
        "distance_km": None,
        "location_geojson": json.loads(geojson_str) if geojson_str else None,
        "created_at": port.created_at,
        "updated_at": port.updated_at,
    }


@router.get(
    "/restricted-zones",
    response_model=List[RestrictedZoneResponse],
    summary="List maritime restricted zones",
)
def list_restricted_zones(
    active_only: bool = Query(True, description="Filter active restrictions only"),
    db: Session = Depends(get_db),
):
    query = db.query(RestrictedZone, func.ST_AsGeoJSON(RestrictedZone.geometry).label("geojson"))
    if active_only:
        query = query.filter(RestrictedZone.is_active.is_(True))

    results = []
    for zone, geojson_str in query.order_by(RestrictedZone.name.asc()).all():
        results.append({
            "id": zone.id,
            "name": zone.name,
            "zone_type": zone.zone_type,
            "description": zone.description,
            "authority": zone.authority,
            "is_active": zone.is_active,
            "geometry_geojson": json.loads(geojson_str) if geojson_str else None,
            "distance_km": None,
            "created_at": zone.created_at,
            "updated_at": zone.updated_at,
        })
    return results


@router.get(
    "/protected-zones",
    response_model=List[ProtectedZoneResponse],
    summary="List marine protected areas and sanctuaries",
)
def list_protected_zones(
    active_only: bool = Query(True, description="Filter active protected areas only"),
    db: Session = Depends(get_db),
):
    query = db.query(ProtectedZone, func.ST_AsGeoJSON(ProtectedZone.geometry).label("geojson"))
    if active_only:
        query = query.filter(ProtectedZone.is_active.is_(True))

    results = []
    for zone, geojson_str in query.order_by(ProtectedZone.name.asc()).all():
        results.append({
            "id": zone.id,
            "name": zone.name,
            "zone_type": zone.zone_type,
            "description": zone.description,
            "authority": zone.authority,
            "is_active": zone.is_active,
            "geometry_geojson": json.loads(geojson_str) if geojson_str else None,
            "distance_km": None,
            "created_at": zone.created_at,
            "updated_at": zone.updated_at,
        })
    return results


@router.get(
    "/nearby-zones",
    response_model=NearbyZonesResponse,
    summary="Find restricted and protected zones near coordinates",
)
def get_nearby_zones(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Center latitude"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Center longitude"),
    radius_km: float = Query(50.0, ge=0.1, le=2000.0, description="Proximity search radius in km"),
    db: Session = Depends(get_db),
):
    restricted = GeoSpatialService.get_nearby_restricted_zones(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        active_only=True,
    )
    protected = GeoSpatialService.get_nearby_protected_zones(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        active_only=True,
    )
    return {
        "center_latitude": latitude,
        "center_longitude": longitude,
        "radius_km": radius_km,
        "restricted_zones": restricted,
        "protected_zones": protected,
    }


@router.get(
    "/distance",
    response_model=DistanceCalculationResponse,
    summary="Calculate great-circle distance between two coordinates",
)
def calculate_distance(
    origin_latitude: float = Query(..., ge=-90.0, le=90.0, description="Origin latitude"),
    origin_longitude: float = Query(..., ge=-180.0, le=180.0, description="Origin longitude"),
    destination_latitude: float = Query(..., ge=-90.0, le=90.0, description="Destination latitude"),
    destination_longitude: float = Query(..., ge=-180.0, le=180.0, description="Destination longitude"),
):
    return NavigationService.calculate_distance(
        origin_lat=origin_latitude,
        origin_lon=origin_longitude,
        dest_lat=destination_latitude,
        dest_lon=destination_longitude,
    )


@router.get(
    "/assess-route",
    response_model=RouteAssessmentResponse,
    summary="Assess maritime path safety against spatial zones",
    description=(
        "Performs spatial analysis along the direct navigation path between origin "
        "and destination. Evaluates intersection against active restricted areas and "
        "marine protected sanctuaries, providing a structured navigation assessment."
    ),
)
def assess_route(
    origin_latitude: float = Query(..., ge=-90.0, le=90.0, description="Origin latitude"),
    origin_longitude: float = Query(..., ge=-180.0, le=180.0, description="Origin longitude"),
    destination_latitude: float = Query(..., ge=-90.0, le=90.0, description="Destination latitude"),
    destination_longitude: float = Query(..., ge=-180.0, le=180.0, description="Destination longitude"),
    db: Session = Depends(get_db),
):
    try:
        return NavigationService.assess_route(
            db=db,
            origin_lat=origin_latitude,
            origin_lon=origin_longitude,
            dest_lat=destination_latitude,
            dest_lon=destination_longitude,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spatial route assessment failure: {str(exc)}",
        )
