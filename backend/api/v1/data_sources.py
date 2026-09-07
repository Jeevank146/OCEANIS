from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import DataSource, DataRefreshLog
from schemas import (
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceResponse,
    DataRefreshLogResponse,
    ProviderHealthResponse,
)
from services.marine_data import MarineDataService

router = APIRouter(
    prefix="/data-sources",
    tags=["Data Sources"],
)


@router.get("/providers/health", response_model=List[ProviderHealthResponse])
def get_all_provider_health():
    """
    Retrieve live health status and credential configuration readiness
    for all primary and fallback ocean data providers (INCOIS, IMD, Copernicus, Fallback).
    """
    service = MarineDataService()
    return service.get_provider_health()



@router.get("", response_model=List[DataSourceResponse])
def list_data_sources(
    active_only: bool = Query(True, description="Filter for only active data sources"),
    db: Session = Depends(get_db),
):
    """
    Retrieve data sources registered in OCEANIS.
    Defaults to returning active data sources.
    """
    query = db.query(DataSource)
    if active_only:
        query = query.filter(DataSource.is_active.is_(True))
    return query.order_by(DataSource.id.asc()).all()


@router.get("/{source_id}", response_model=DataSourceResponse)
def get_data_source(
    source_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a single data source by its ID.
    """
    data_source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {source_id} not found",
        )
    return data_source


@router.post("", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
def create_data_source(
    payload: DataSourceCreate,
    db: Session = Depends(get_db),
):
    """
    Create and register a new ocean data source in OCEANIS.
    """
    existing = db.query(DataSource).filter(DataSource.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Data source with name '{payload.name}' already exists",
        )

    data_source = DataSource(
        name=payload.name,
        provider=payload.provider,
        source_type=payload.source_type,
        base_url=payload.base_url,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


@router.patch("/{source_id}", response_model=DataSourceResponse)
def update_data_source(
    source_id: int,
    payload: DataSourceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update attributes of an existing data source (e.g. name, description, base_url, is_active).
    """
    data_source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {source_id} not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return data_source

    if "name" in update_data and update_data["name"] != data_source.name:
        existing = (
            db.query(DataSource)
            .filter(DataSource.name == update_data["name"], DataSource.id != source_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Data source with name '{update_data['name']}' already exists",
            )

    for field, value in update_data.items():
        setattr(data_source, field, value)

    db.commit()
    db.refresh(data_source)
    return data_source


@router.get("/{source_id}/refresh-logs", response_model=List[DataRefreshLogResponse])
def get_data_source_refresh_logs(
    source_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve ingestion / synchronization refresh logs for a specific data source.
    """
    data_source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {source_id} not found",
        )

    logs = (
        db.query(DataRefreshLog)
        .filter(DataRefreshLog.data_source_id == source_id)
        .order_by(DataRefreshLog.started_at.desc())
        .all()
    )
    return logs
