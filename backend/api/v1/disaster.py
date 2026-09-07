from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.disaster import (
    CycloneTrackResponse,
    HazardZoneResponse,
    MarineAlertResponse,
    SafetyAssessmentResponse,
)
from services.disaster import DisasterService

router = APIRouter(prefix="/disaster", tags=["Disaster & Safety"])


@router.get(
    "/alerts",
    response_model=List[MarineAlertResponse],
    summary="Get marine warnings and disaster alerts",
    description="Retrieve active or historical marine alerts with optional spatial proximity filtering and severity filters.",
)
def get_marine_alerts(
    latitude: Optional[float] = Query(
        None,
        ge=-90.0,
        le=90.0,
        description="Focal latitude in decimal degrees (-90 to 90)",
    ),
    longitude: Optional[float] = Query(
        None,
        ge=-180.0,
        le=180.0,
        description="Focal longitude in decimal degrees (-180 to 180)",
    ),
    radius_km: float = Query(
        50.0,
        gt=0.0,
        le=1000.0,
        description="Spatial search radius in kilometers (max 1000 km)",
    ),
    severity: Optional[str] = Query(
        None,
        description="Filter by alert severity (INFO, CAUTION, WARNING, CRITICAL)",
    ),
    active_only: bool = Query(
        True,
        description="Filter only active and non-expired alerts",
    ),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    if (latitude is None and longitude is not None) or (latitude is not None and longitude is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both latitude and longitude must be provided together for spatial proximity queries.",
        )

    return DisasterService.get_alerts(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        severity=severity,
        active_only=active_only,
    )


@router.get(
    "/alerts/{alert_id}",
    response_model=MarineAlertResponse,
    summary="Get marine alert details by ID",
    description="Retrieve full metadata, description, and geometry for a specific marine alert bulletin.",
)
def get_marine_alert_by_id(
    alert_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    alert = DisasterService.get_alert_by_id(db=db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Marine alert with ID '{alert_id}' was not found.",
        )
    return alert


@router.get(
    "/cyclones",
    response_model=List[CycloneTrackResponse],
    summary="Get cyclone tracking and forecast points",
    description="Retrieve observed and forecast tropical cyclone track positions, central pressures, wind speeds, and movement vectors.",
)
def get_cyclone_tracks(
    active_only: bool = Query(
        True,
        description="Filter only active cyclonic systems",
    ),
    latitude: Optional[float] = Query(
        None,
        ge=-90.0,
        le=90.0,
        description="Focal latitude in decimal degrees (-90 to 90)",
    ),
    longitude: Optional[float] = Query(
        None,
        ge=-180.0,
        le=180.0,
        description="Focal longitude in decimal degrees (-180 to 180)",
    ),
    radius_km: float = Query(
        500.0,
        gt=0.0,
        le=3000.0,
        description="Spatial search radius in kilometers (max 3000 km)",
    ),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    if (latitude is None and longitude is not None) or (latitude is not None and longitude is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both latitude and longitude must be provided together for spatial proximity queries.",
        )

    return DisasterService.get_cyclone_tracks(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        active_only=active_only,
    )


@router.get(
    "/hazard-zones",
    response_model=List[HazardZoneResponse],
    summary="Get spatial hazard zones",
    description="Retrieve designated hazard polygons (cyclone impact, storm surge inundation, high waves) with containment and distance metrics.",
)
def get_hazard_zones(
    latitude: Optional[float] = Query(
        None,
        ge=-90.0,
        le=90.0,
        description="Focal latitude in decimal degrees (-90 to 90)",
    ),
    longitude: Optional[float] = Query(
        None,
        ge=-180.0,
        le=180.0,
        description="Focal longitude in decimal degrees (-180 to 180)",
    ),
    radius_km: float = Query(
        50.0,
        gt=0.0,
        le=1000.0,
        description="Spatial search radius in kilometers (max 1000 km)",
    ),
    hazard_type: Optional[str] = Query(
        None,
        description="Filter by hazard category (e.g. CYCLONE_IMPACT_ZONE, STORM_SURGE_ZONE, HIGH_WAVE_RISK)",
    ),
    active_only: bool = Query(
        True,
        description="Filter only active hazard zones",
    ),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    if (latitude is None and longitude is not None) or (latitude is not None and longitude is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both latitude and longitude must be provided together for spatial proximity queries.",
        )

    return DisasterService.get_hazard_zones(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        hazard_type=hazard_type,
        active_only=active_only,
    )


@router.get(
    "/safety-assessment",
    response_model=SafetyAssessmentResponse,
    summary="Get deterministic safety assessment for a location",
    description="Evaluates all active marine warnings, cyclonic activity, hazard zones, and nearest port refuges strictly based on stored source data.",
)
def get_safety_assessment(
    latitude: float = Query(
        ...,
        ge=-90.0,
        le=90.0,
        description="Location latitude in decimal degrees (-90 to 90)",
    ),
    longitude: float = Query(
        ...,
        ge=-180.0,
        le=180.0,
        description="Location longitude in decimal degrees (-180 to 180)",
    ),
    radius_km: float = Query(
        50.0,
        gt=0.0,
        le=1000.0,
        description="Assessment radius in kilometers (max 1000 km)",
    ),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return DisasterService.assess_safety(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )
