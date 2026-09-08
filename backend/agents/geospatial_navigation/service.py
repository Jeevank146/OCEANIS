from typing import Optional
from sqlalchemy.orm import Session

from agents.geospatial_navigation.agent import GeoSpatialNavigationIntelligenceAgent
from agents.geospatial_navigation.schemas import (
    GeoSpatialNavigationAssessmentResponse,
    GeoSpatialNavigationQuery,
)


class GeoSpatialNavigationAgentService:
    """
    Service gateway for the Geo-Spatial & Navigation Intelligence Agent.
    Coordinates PostGIS spatial data collection, boundary intersection analysis,
    geofencing, and structured navigation response generation.
    Independently callable by API routes and the Agent Orchestrator.
    """

    def __init__(self, agent: Optional[GeoSpatialNavigationIntelligenceAgent] = None):
        self.agent = agent or GeoSpatialNavigationIntelligenceAgent()

    def assess_geospatial_navigation(
        self,
        db: Session,
        query: GeoSpatialNavigationQuery,
    ) -> GeoSpatialNavigationAssessmentResponse:
        """
        Assesses spatial boundaries, ports, restricted zones, and route clearance for given coordinates.
        """
        return self.agent.assess(db=db, query=query)

    def assess(
        self,
        db: Session,
        query: GeoSpatialNavigationQuery,
    ) -> GeoSpatialNavigationAssessmentResponse:
        """
        Alias for assess_geospatial_navigation.
        """
        return self.assess_geospatial_navigation(db=db, query=query)

    def assess_spatial(
        self,
        db: Session,
        query: GeoSpatialNavigationQuery,
    ) -> GeoSpatialNavigationAssessmentResponse:
        return self.assess_geospatial_navigation(db=db, query=query)
