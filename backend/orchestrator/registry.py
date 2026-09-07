from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AgentDefinition:
    """
    Static registration metadata for an OCEANIS domain agent.
    """
    agent_id: str
    name: str
    domain: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    required_evidence_types: List[str] = field(default_factory=list)
    default_priority: int = 5


class AgentRegistry:
    """
    Central registry of the six OCEANIS domain agents.
    """
    _agents: Dict[str, AgentDefinition] = {
        "fishing": AgentDefinition(
            agent_id="fishing",
            name="Fishing Intelligence Agent",
            domain="Fisheries Decision Support",
            description="Executes deterministic evidence fusion across environmental layers for fishing suitability, species conditions, and multi-location comparisons.",
            capabilities=["fishing_suitability", "species_habitat_assessment", "location_comparison", "what_if_analysis", "pfz_evaluation"],
            required_evidence_types=["MARINE_CONDITIONS", "EARTH_OBSERVATION", "GEO_SPATIAL", "DISASTER_SAFETY"],
            default_priority=6,
        ),
        "marine_conditions": AgentDefinition(
            agent_id="marine_conditions",
            name="Marine Conditions Agent",
            domain="Ocean Dynamics & Sea State",
            description="Evaluates significant wave height, swell profiles, wave periods, surface currents, and sea surface temperature.",
            capabilities=["wave_analysis", "swell_tracking", "current_velocity", "sst_profiling"],
            required_evidence_types=["MARINE_TELEMETRY", "OCEAN_BUOY"],
            default_priority=3,
        ),
        "earth_observation": AgentDefinition(
            agent_id="earth_observation",
            name="Earth Observation Agent",
            domain="Satellite Remote Sensing",
            description="Delivers satellite-derived chlorophyll-a bio-productivity indicators, cloud cover fractions, thermal fronts, and ocean optical quality.",
            capabilities=["chlorophyll_mapping", "cloud_cover_analysis", "thermal_front_detection", "optical_observability"],
            required_evidence_types=["SATELLITE_REMOTE_SENSING"],
            default_priority=4,
        ),
        "geospatial_navigation": AgentDefinition(
            agent_id="geospatial_navigation",
            name="Geo-Spatial & Navigation Agent",
            domain="Maritime Boundaries & Ports",
            description="Assesses port proximities, military restricted exclusion sectors, Marine Protected Areas (MPAs), and route clearance.",
            capabilities=["port_lookup", "restricted_zone_check", "protected_zone_check", "geofencing", "route_clearance"],
            required_evidence_types=["POSTGIS_REGULATORY", "PORT_INFRASTRUCTURE"],
            default_priority=2,
        ),
        "disaster_safety": AgentDefinition(
            agent_id="disaster_safety",
            name="Disaster & Safety Agent",
            domain="Disaster Hazards & Marine Safety",
            description="Evaluates official marine alerts, tropical cyclone tracks, and spatial hazard zones with deterministic safety overrides.",
            capabilities=["cyclone_tracking", "marine_alerts", "hazard_polygons", "emergency_safety_override"],
            required_evidence_types=["OFFICIAL_ALERT", "CYCLONE_TRACK", "HAZARD_ZONE"],
            default_priority=1,
        ),
        "marine_operations": AgentDefinition(
            agent_id="marine_operations",
            name="Marine Operations Agent",
            domain="Voyage & Fleet Operations",
            description="Calculates geodesic route distance, estimated transit durations, departure scheduling, and multi-layer route constraints.",
            capabilities=["distance_calculation", "transit_time_estimation", "route_assessment", "departure_planning"],
            required_evidence_types=["ROUTE_GEOMETRY", "OPERATIONAL_CONSTRAINTS", "SAFE_PORT_REFUGE"],
            default_priority=5,
        ),
    }

    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[AgentDefinition]:
        """
        Retrieves agent definition by agent_id.
        """
        return cls._agents.get(agent_id)

    @classmethod
    def list_agents(cls) -> List[AgentDefinition]:
        """
        Lists all 6 registered domain agents.
        """
        return list(cls._agents.values())

    @classmethod
    def get_all_agent_ids(cls) -> List[str]:
        """
        Returns list of all 6 agent IDs.
        """
        return list(cls._agents.keys())
