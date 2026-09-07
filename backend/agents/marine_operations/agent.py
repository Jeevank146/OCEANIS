from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from agents.marine_operations.collector import MarineOperationsDataCollector
from agents.marine_operations.reasoning import MarineOperationsReasoningEngine
from agents.marine_operations.schemas import (
    MarineOperationsAssessmentResponse,
    MarineOperationsQuery,
)


class MarineOperationsIntelligenceAgent:
    """
    OCEANIS Marine Operations Intelligence Domain Agent.
    Owns the complete marine operations and voyage clearance domain:
    - Route geodesic distance and travel duration estimation
    - Departure scheduling and estimated arrival calculation
    - Deterministic spatial intersection checks (Restricted military zones, Marine protected areas)
    - Active hazard zone and disaster alert corridor intersections
    - Environmental operational thresholds (wave heights, sustained winds)
    - Safe harbor refuges and alternative route guidance
    - Explainable multi-factor operational clearance decisions
    """

    def __init__(
        self,
        collector: Optional[MarineOperationsDataCollector] = None,
        reasoning_engine: Optional[MarineOperationsReasoningEngine] = None,
    ):
        self.collector = collector or MarineOperationsDataCollector()
        self.reasoning = reasoning_engine or MarineOperationsReasoningEngine()

    def assess(
        self,
        db: Session,
        query: MarineOperationsQuery,
        now: Optional[datetime] = None,
    ) -> MarineOperationsAssessmentResponse:
        """
        Executes end-to-end marine operations assessment for planned transit between origin and destination.
        """
        collected_data = self.collector.collect(
            db=db,
            origin_latitude=query.origin_latitude,
            origin_longitude=query.origin_longitude,
            destination_latitude=query.destination_latitude,
            destination_longitude=query.destination_longitude,
            speed_kmh=query.speed_kmh,
            planned_departure_at=query.planned_departure_at,
            operation_type=query.operation_type or "TRANSIT",
            vessel_type=query.vessel_type or "FISHING_VESSEL",
            now=now,
        )

        assessment = self.reasoning.evaluate(collected_data=collected_data)
        return assessment
