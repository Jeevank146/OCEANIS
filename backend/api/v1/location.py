from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from schemas.location import (
    LocationCandidate,
    LocationReverseGeocodeRequest,
    LocationSearchResponse,
    LocationSuggestionsResponse,
    LocationValidateRequest,
    LocationValidationResult,
)
from services.location import LocationService

router = APIRouter(
    prefix="/location",
    tags=["Location Intelligence"],
)


@router.get(
    "/search",
    response_model=LocationSearchResponse,
    summary="Search coastal locations, ports, harbours and places",
    description=(
        "Searches for coastal cities, fishing harbours, major/minor ports, coastal villages, "
        "and coordinates. Returns normalized candidates with preliminary coastal classification."
    ),
)
def search_locations(
    query: str = Query(..., min_length=1, max_length=200, description="Location search term or coordinates"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
):
    try:
        results = LocationService.search_locations(query=query, limit=limit)
        return {
            "query": query,
            "total_results": len(results),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Location search failure: {str(exc)}",
        )


@router.get(
    "/suggestions",
    response_model=LocationSuggestionsResponse,
    summary="Get curated coastal station suggestions",
    description="Returns top operational coastal ports and fishing stations across East & West Coasts.",
)
def get_suggestions():
    try:
        suggestions = LocationService.get_curated_suggestions()
        return {"suggestions": suggestions}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve location suggestions: {str(exc)}",
        )


@router.post(
    "/validate",
    response_model=LocationValidationResult,
    summary="Validate location or coordinates for coastal/marine intelligence",
    description=(
        "Validates whether the requested place or coordinate is coastal/marine, inland, or unresolved. "
        "Returns distance to coast, marine context, nearest port, and operational readiness."
    ),
)
def validate_location(
    request: LocationValidateRequest,
):
    try:
        result = LocationService.validate_location(
            query=request.query,
            latitude=request.latitude,
            longitude=request.longitude,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Location validation failure: {str(exc)}",
        )


@router.post(
    "/reverse-geocode",
    response_model=LocationValidationResult,
    summary="Reverse-geocode coordinates (e.g. from browser geolocation or map click)",
    description=(
        "Determines whether the provided coordinates represent a coastal/marine location, "
        "calculates distance to nearest coast, identifies nearest port, and enriches with marine context."
    ),
)
def reverse_geocode(
    request: LocationReverseGeocodeRequest,
):
    try:
        result = LocationService.validate_coordinates(
            latitude=request.latitude,
            longitude=request.longitude,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reverse geocode failure: {str(exc)}",
        )
