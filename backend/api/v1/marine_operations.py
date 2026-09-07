from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.marine_operations import (
    DepartureAssessmentResponse,
    MarineOperationAssessment,
    MarineOperationCreate,
    MarineOperationResponse,
    MarineOperationUpdate,
    OperationDistanceResponse,
    OperationTimeEstimateResponse,
)
from services.marine_operations import MarineOperationsService

router = APIRouter(prefix="/operations", tags=["Marine Operations"])


@router.post(
    "",
    response_model=MarineOperationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new marine operation",
    description="Registers and persists a new planned or simulated vessel voyage/operation in OCEANIS.",
)
def create_operation(
    payload: MarineOperationCreate,
    db: Session = Depends(get_db),
) -> Any:
    if payload.operation_id:
        existing = MarineOperationsService.get_operation_by_id(db, payload.operation_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Marine operation with ID '{payload.operation_id}' already exists.",
            )
    return MarineOperationsService.create_operation(
        db=db,
        operation_data=payload.model_dump(),
    )


@router.get(
    "",
    response_model=List[MarineOperationResponse],
    summary="List marine operations",
    description="Retrieves a list of registered vessel trips and operations with optional filtering by type and status.",
)
def list_operations(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type (e.g. FISHING_TRIP, TRANSIT)"),
    operational_status: Optional[str] = Query(None, description="Filter by operational status (e.g. PLANNED, ASSESSED)"),
    db: Session = Depends(get_db),
) -> Any:
    return MarineOperationsService.get_operations(
        db=db,
        limit=limit,
        offset=offset,
        operation_type=operation_type,
        operational_status=operational_status,
    )


@router.get(
    "/distance",
    response_model=OperationDistanceResponse,
    summary="Calculate geodesic distance between coordinates",
    description="Computes great-circle distance between origin and destination in kilometers and nautical miles.",
)
def calculate_distance(
    origin_latitude: float = Query(..., ge=-90.0, le=90.0, description="Origin latitude"),
    origin_longitude: float = Query(..., ge=-180.0, le=180.0, description="Origin longitude"),
    destination_latitude: float = Query(..., ge=-90.0, le=90.0, description="Destination latitude"),
    destination_longitude: float = Query(..., ge=-180.0, le=180.0, description="Destination longitude"),
) -> Any:
    return MarineOperationsService.calculate_distance(
        origin_lat=origin_latitude,
        origin_lon=origin_longitude,
        dest_lat=destination_latitude,
        dest_lon=destination_longitude,
    )


@router.get(
    "/estimate-time",
    response_model=OperationTimeEstimateResponse,
    summary="Estimate transit duration",
    description="Calculates transit duration in minutes and hours based on great-circle distance and vessel speed.",
)
def estimate_transit_time(
    origin_latitude: float = Query(..., ge=-90.0, le=90.0, description="Origin latitude"),
    origin_longitude: float = Query(..., ge=-180.0, le=180.0, description="Origin longitude"),
    destination_latitude: float = Query(..., ge=-90.0, le=90.0, description="Destination latitude"),
    destination_longitude: float = Query(..., ge=-180.0, le=180.0, description="Destination longitude"),
    speed_kmh: float = Query(..., gt=0.0, description="Vessel cruising speed in km/h (> 0)"),
) -> Any:
    dist_res = MarineOperationsService.calculate_distance(
        origin_lat=origin_latitude,
        origin_lon=origin_longitude,
        dest_lat=destination_latitude,
        dest_lon=destination_longitude,
    )
    dist_km = dist_res["distance_km"]
    dist_nm = dist_res["distance_nautical_miles"]
    duration_min = MarineOperationsService.estimate_duration(dist_km, speed_kmh)
    duration_hrs = round(duration_min / 60.0, 2) if duration_min is not None else 0.0

    return {
        "origin": {"latitude": origin_latitude, "longitude": origin_longitude},
        "destination": {"latitude": destination_latitude, "longitude": destination_longitude},
        "distance_km": dist_km,
        "distance_nautical_miles": dist_nm,
        "speed_kmh": speed_kmh,
        "estimated_duration_minutes": duration_min,
        "estimated_duration_hours": duration_hrs,
        "calculation_notes": f"Estimated at constant cruising speed of {speed_kmh} km/h.",
    }


@router.get(
    "/assess-route",
    response_model=MarineOperationAssessment,
    summary="Assess route constraints, zones, and safety hazards",
    description="Performs deterministic multi-layer operational assessment against restricted areas, protected zones, hazard polygons, and active alerts.",
)
def assess_route_operation(
    origin_latitude: float = Query(..., ge=-90.0, le=90.0, description="Origin latitude"),
    origin_longitude: float = Query(..., ge=-180.0, le=180.0, description="Origin longitude"),
    destination_latitude: float = Query(..., ge=-90.0, le=90.0, description="Destination latitude"),
    destination_longitude: float = Query(..., ge=-180.0, le=180.0, description="Destination longitude"),
    speed_kmh: Optional[float] = Query(None, gt=0.0, description="Optional vessel cruising speed in km/h"),
    db: Session = Depends(get_db),
) -> Any:
    return MarineOperationsService.assess_operation(
        db=db,
        origin_lat=origin_latitude,
        origin_lon=origin_longitude,
        dest_lat=destination_latitude,
        dest_lon=destination_longitude,
        speed_kmh=speed_kmh,
    )


@router.get(
    "/departure-assessment",
    response_model=DepartureAssessmentResponse,
    summary="Evaluate departure timing and forecast window",
    description="Assesses planned departure timestamp against temporal warnings, active advisories, and estimated transit duration.",
)
def assess_departure_timing(
    origin_latitude: float = Query(..., ge=-90.0, le=90.0, description="Origin latitude"),
    origin_longitude: float = Query(..., ge=-180.0, le=180.0, description="Origin longitude"),
    destination_latitude: float = Query(..., ge=-90.0, le=90.0, description="Destination latitude"),
    destination_longitude: float = Query(..., ge=-180.0, le=180.0, description="Destination longitude"),
    departure_at: datetime = Query(..., description="Planned departure timestamp in ISO 8601 format"),
    speed_kmh: Optional[float] = Query(None, gt=0.0, description="Optional vessel cruising speed in km/h"),
    db: Session = Depends(get_db),
) -> Any:
    return MarineOperationsService.assess_departure(
        db=db,
        origin_lat=origin_latitude,
        origin_lon=origin_longitude,
        dest_lat=destination_latitude,
        dest_lon=destination_longitude,
        departure_at=departure_at,
        speed_kmh=speed_kmh,
    )


@router.get(
    "/{operation_id}",
    response_model=MarineOperationResponse,
    summary="Get single marine operation by ID",
    description="Retrieves full metadata and status for a specific operational record.",
)
def get_operation(
    operation_id: str,
    db: Session = Depends(get_db),
) -> Any:
    operation = MarineOperationsService.get_operation_by_id(db=db, operation_id=operation_id)
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Marine operation with ID '{operation_id}' was not found.",
        )
    return operation


@router.patch(
    "/{operation_id}",
    response_model=MarineOperationResponse,
    summary="Update marine operation details",
    description="Updates parameters for an existing operation, updating calculated distance/duration if coordinates or speed changed.",
)
def update_operation(
    operation_id: str,
    payload: MarineOperationUpdate,
    db: Session = Depends(get_db),
) -> Any:
    operation = MarineOperationsService.update_operation(
        db=db,
        operation_id=operation_id,
        update_data=payload.model_dump(exclude_unset=True),
    )
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Marine operation with ID '{operation_id}' was not found.",
        )
    return operation


@router.get(
    "/{operation_id}/assessment",
    response_model=MarineOperationAssessment,
    summary="Run operational assessment for saved operation",
    description="Runs a multi-layer deterministic assessment on a saved marine operation record.",
)
def get_operation_assessment(
    operation_id: str,
    db: Session = Depends(get_db),
) -> Any:
    operation = MarineOperationsService.get_operation_by_id(db=db, operation_id=operation_id)
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Marine operation with ID '{operation_id}' was not found.",
        )

    return MarineOperationsService.assess_operation(
        db=db,
        origin_lat=operation.origin_latitude,
        origin_lon=operation.origin_longitude,
        dest_lat=operation.destination_latitude,
        dest_lon=operation.destination_longitude,
        speed_kmh=operation.estimated_speed_kmh,
        operation_id=operation.operation_id,
    )
