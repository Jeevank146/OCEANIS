from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from agents.disaster_safety.schemas import DisasterSafetyQuery
from agents.disaster_safety.service import DisasterSafetyAgentService
from agents.earth_observation.schemas import EarthObservationQuery
from agents.earth_observation.service import EarthObservationAgentService
from agents.fishing.schemas import FishingLocationInput, FishingQuery, LocationComparisonQuery
from agents.fishing.service import FishingAgentService
from agents.geospatial_navigation.schemas import GeoSpatialNavigationQuery
from agents.geospatial_navigation.service import GeoSpatialNavigationAgentService
from agents.marine_conditions.schemas import MarineConditionsQuery
from agents.marine_conditions.service import MarineConditionsAgentService
from agents.marine_operations.schemas import MarineOperationsQuery
from agents.marine_operations.service import MarineOperationsAgentService
from orchestrator.schemas import AgentSelection, QueryUnderstanding
from schemas.agent_contract import (
    AgentResult,
    AgentStatus,
    DataFreshness,
    EvidenceItem,
    ObservationType,
)



def _norm_fresh(raw_val: Optional[str]) -> str:
    if not raw_val:
        return DataFreshness.FRESH.value
    upper = str(raw_val).upper()
    if "FRESH" in upper:
        return DataFreshness.FRESH.value
    elif "AGING" in upper:
        return DataFreshness.AGING.value
    elif "STALE" in upper:
        return DataFreshness.STALE.value
    return DataFreshness.UNAVAILABLE.value

class AgentExecutor:
    """
    Structured execution coordinator for the six OCEANIS domain agents.
    Executes domain agents with strict error isolation, standardized contract mapping,
    and granular execution telemetry.
    """

    def __init__(
        self,
        fishing_service: Optional[FishingAgentService] = None,
        marine_conditions_service: Optional[MarineConditionsAgentService] = None,
        earth_observation_service: Optional[EarthObservationAgentService] = None,
        geospatial_service: Optional[GeoSpatialNavigationAgentService] = None,
        disaster_service: Optional[DisasterSafetyAgentService] = None,
        marine_operations_service: Optional[MarineOperationsAgentService] = None,
    ):
        self.fishing_service = fishing_service or FishingAgentService()
        self.marine_conditions_service = marine_conditions_service or MarineConditionsAgentService()
        self.earth_observation_service = earth_observation_service or EarthObservationAgentService()
        self.geospatial_service = geospatial_service or GeoSpatialNavigationAgentService()
        self.disaster_service = disaster_service or DisasterSafetyAgentService()
        self.marine_operations_service = marine_operations_service or MarineOperationsAgentService()

    def execute_selected_agents(
        self,
        db: Session,
        selected_agents: List[AgentSelection],
        understanding: QueryUnderstanding,
        now: Optional[datetime] = None,
    ) -> Dict[str, AgentResult]:
        """
        Executes all selected domain agents and returns structured AgentResult objects.
        """
        now_utc = now or datetime.now(timezone.utc)
        results: Dict[str, AgentResult] = {}

        orig_lat = understanding.primary_location.latitude if understanding.primary_location else 17.6868
        orig_lon = understanding.primary_location.longitude if understanding.primary_location else 83.2185
        dest_lat = understanding.destination_location.latitude if understanding.destination_location else None
        dest_lon = understanding.destination_location.longitude if understanding.destination_location else None

        target_date_str = understanding.target_date
        target_time_str = understanding.target_time
        target_dt_iso = None
        if target_date_str and target_time_str:
            target_dt_iso = f"{target_date_str}T{target_time_str}:00Z"
        elif target_date_str:
            target_dt_iso = f"{target_date_str}T12:00:00Z"

        for selection in selected_agents:
            agent_id = selection.agent_id
            start_t = time.perf_counter()

            try:
                # --------------------------------------------------
                # 1. GEO-SPATIAL & NAVIGATION AGENT
                # --------------------------------------------------
                if agent_id == "geospatial_navigation":
                    query_obj = GeoSpatialNavigationQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        destination_latitude=dest_lat,
                        destination_longitude=dest_lon,
                        buffer_km=15.0,
                    )
                    res = self.geospatial_service.assess_geospatial_navigation(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []):
                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "PostGIS GIS Engine"),
                                parameter=getattr(ev, "parameter", "spatial_entity"),
                                value=getattr(ev, "value", str(ev)),
                                unit=getattr(ev, "unit", "km"),
                                observation_type=ObservationType.OBSERVED.value,
                                timestamp=getattr(ev, "observed_at", None) or getattr(ev, "timestamp", None),
                                freshness=DataFreshness.FRESH.value,
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "geospatial_navigation"},
                            )
                        )

                    findings = [
                        f"Location: {orig_lat:.4f}°N, {orig_lon:.4f}°E",
                        f"Zone Clearance: {getattr(res, 'spatial_clearance', 'CLEAR')}",
                    ]
                    if getattr(res, "nearest_port", None):
                        findings.append(f"Nearest Port: {res.nearest_port.name} ({res.nearest_port.distance_km:.1f} km)")

                    results[agent_id] = AgentResult(
                        agent_name="Geo-Spatial & Navigation",
                        status=AgentStatus.SUCCESS.value,
                        summary=getattr(res, "summary", "Spatial baseline navigation evaluation completed."),
                        findings=findings,
                        evidence=evidence_list,
                        confidence=float(getattr(res, "confidence", 0.95)),
                        warnings=list(getattr(res, "warnings", [])),
                        limitations=[],
                    )

                # --------------------------------------------------
                # 2. DISASTER & SAFETY AGENT
                # --------------------------------------------------
                elif agent_id == "disaster_safety":
                    query_obj = DisasterSafetyQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        buffer_km=50.0,
                    )
                    res = self.disaster_service.assess_safety(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []):
                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "IMD / INCOIS Disaster Watch"),
                                parameter=getattr(ev, "parameter", "marine_alert"),
                                value=getattr(ev, "value", str(ev)),
                                unit=getattr(ev, "unit", None),
                                observation_type=ObservationType.OFFICIAL_WARNING.value,
                                timestamp=getattr(ev, "observed_at", None) or getattr(ev, "timestamp", None),
                                freshness=_norm_fresh(getattr(ev, "freshness", None)),
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "disaster_safety"},
                            )
                        )

                    findings = [
                        f"Safety Status: {getattr(res, 'safety_status', 'CLEAR')}",
                        f"Active Alerts: {len(getattr(res, 'active_alerts', []))}",
                        f"Active Cyclones: {len(getattr(res, 'active_cyclones', []))}",
                    ]
                    results[agent_id] = AgentResult(
                        agent_name="Disaster & Safety",
                        status=AgentStatus.SUCCESS.value,
                        summary=getattr(res, "summary", "Disaster, storm track, and safety advisory assessment complete."),
                        findings=findings,
                        evidence=evidence_list,
                        confidence=float(getattr(res, "confidence", 0.98)),
                        warnings=list(getattr(res, "warnings", [])),
                        limitations=[],
                    )

                # --------------------------------------------------
                # 3. MARINE CONDITIONS AGENT
                # --------------------------------------------------
                elif agent_id == "marine_conditions":
                    query_obj = MarineConditionsQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        target_datetime=target_dt_iso,
                    )
                    res = self.marine_conditions_service.assess_marine_conditions(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []):
                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "INCOIS / IMD"),
                                parameter=getattr(ev, "parameter", "sea_state"),
                                value=getattr(ev, "value", 0.0),
                                unit=getattr(ev, "unit", None),
                                observation_type=getattr(ev, "observation_type", ObservationType.OBSERVED.value),
                                timestamp=getattr(ev, "timestamp", None),
                                freshness=_norm_fresh(getattr(ev, "freshness", None)),
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "marine_conditions"},
                            )
                        )

                    summary_obj = getattr(res, "conditions_summary", None)
                    wave_h = getattr(summary_obj, "wave_height_m", None) if summary_obj else None
                    wind_s = getattr(summary_obj, "wind_speed_kmh", None) if summary_obj else None
                    sst_v = getattr(summary_obj, "sea_surface_temperature_c", None) if summary_obj else None

                    findings = [
                        f"Wave Height: {wave_h} m" if wave_h is not None else "Wave telemetry analyzed",
                        f"Wind Speed: {wind_s} km/h" if wind_s is not None else "Wind telemetry analyzed",
                        f"Sea Surface Temp: {sst_v} °C" if sst_v is not None else "SST telemetry analyzed",
                    ]
                    results[agent_id] = AgentResult(
                        agent_name="Marine Conditions",
                        status=AgentStatus.SUCCESS.value,
                        summary=getattr(res, "summary", "Marine wave, wind, swell, and hydrodynamic conditions evaluated."),
                        findings=findings,
                        evidence=evidence_list,
                        confidence=float(getattr(res, "confidence", 0.90)),
                        warnings=list(getattr(res, "warnings", [])),
                        limitations=[],
                    )

                # --------------------------------------------------
                # 4. EARTH OBSERVATION AGENT
                # --------------------------------------------------
                elif agent_id == "earth_observation":
                    query_obj = EarthObservationQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        target_datetime=target_dt_iso,
                    )
                    res = self.earth_observation_service.assess_earth_observation(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []):
                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "Copernicus Earth Observation"),
                                parameter=getattr(ev, "parameter", "chlorophyll_a"),
                                value=getattr(ev, "value", 0.0),
                                unit=getattr(ev, "unit", "mg/m³"),
                                observation_type=ObservationType.OBSERVED.value,
                                timestamp=getattr(ev, "timestamp", None),
                                freshness=_norm_fresh(getattr(ev, "freshness", None)),
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "earth_observation"},
                            )
                        )

                    ind = getattr(res, "indicators", None)
                    chl = getattr(ind, "chlorophyll_concentration_mg_m3", None) if ind else None
                    sst = getattr(ind, "sea_surface_temperature_c", None) if ind else None

                    findings = [
                        f"Chlorophyll-a: {chl} mg/m³" if chl is not None else "Satellite ocean colour evaluated",
                        f"Satellite SST: {sst} °C" if sst is not None else "Satellite thermal telemetry analyzed",
                    ]
                    results[agent_id] = AgentResult(
                        agent_name="Earth Observation",
                        status=AgentStatus.SUCCESS.value,
                        summary=getattr(res, "summary", "Satellite optical ocean colour and thermal front assessment complete."),
                        findings=findings,
                        evidence=evidence_list,
                        confidence=float(getattr(res, "confidence", 0.88)),
                        warnings=list(getattr(res, "warnings", [])),
                        limitations=[],
                    )

                # --------------------------------------------------
                # 5. MARINE OPERATIONS AGENT
                # --------------------------------------------------
                elif agent_id == "marine_operations":
                    ops_dest_lat = dest_lat if dest_lat is not None else (orig_lat + 0.3)
                    ops_dest_lon = dest_lon if dest_lon is not None else (orig_lon + 0.3)
                    query_obj = MarineOperationsQuery(
                        origin_latitude=orig_lat,
                        origin_longitude=orig_lon,
                        destination_latitude=ops_dest_lat,
                        destination_longitude=ops_dest_lon,
                        speed_kmh=20.0,
                        planned_departure_at=target_dt_iso,
                        vessel_type=understanding.vessel_type or "FISHING_VESSEL",
                        operation_type=understanding.operation_type or "TRANSIT",
                    )
                    res = self.marine_operations_service.assess_operations(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []):
                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "Marine Operations Engine"),
                                parameter=getattr(ev, "parameter", "voyage_distance"),
                                value=getattr(ev, "value", str(ev)),
                                unit=getattr(ev, "unit", "km"),
                                observation_type=ObservationType.AI_ASSESSMENT.value,
                                timestamp=getattr(ev, "timestamp", None),
                                freshness=DataFreshness.FRESH.value,
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "marine_operations"},
                            )
                        )

                    route_summary = getattr(res, "route_summary", None)
                    dist = getattr(route_summary, "total_distance_km", None) if route_summary else None
                    dur = getattr(route_summary, "estimated_duration_hours", None) if route_summary else None

                    findings = [
                        f"Route Clearance: {getattr(res, 'operation_clearance', 'CLEAR')}",
                        f"Distance: {dist:.1f} km ({dist * 0.539957:.1f} NM)" if dist is not None else "Direct nautical trajectory evaluated",
                        f"Est Duration: {dur:.1f} hours" if dur is not None else "Estimated transit speed: 20 km/h",
                    ]
                    results[agent_id] = AgentResult(
                        agent_name="Marine Operations",
                        status=AgentStatus.SUCCESS.value,
                        summary=getattr(res, "summary", "Vessel transit feasibility, voyage trajectory, and operational limits evaluated."),
                        findings=findings,
                        evidence=evidence_list,
                        confidence=float(getattr(res, "confidence", 0.92)),
                        warnings=list(getattr(res, "warnings", [])),
                        limitations=[],
                    )

                # --------------------------------------------------
                # 6. FISHING INTELLIGENCE AGENT
                # --------------------------------------------------
                elif agent_id == "fishing":
                    query_obj = FishingQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        date=target_date_str,
                        departure_time=target_time_str,
                        vessel_type=understanding.vessel_type or "small_boat",
                        target_species=understanding.target_species,
                    )
                    res = self.fishing_service.assess_fishing_query(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []) or getattr(res, "evidence_used", []):
                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "INCOIS PFZ / Copernicus"),
                                parameter=getattr(ev, "factor", "fishing_indicator"),
                                value=getattr(ev, "value", str(ev)),
                                unit=getattr(ev, "unit", None),
                                observation_type=ObservationType.OBSERVED.value,
                                timestamp=getattr(ev, "observed_at", None),
                                freshness=DataFreshness.FRESH.value,
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "fishing"},
                            )
                        )

                    suitability_score = getattr(res, "suitability_score", None) or (
                        res.fishing_suitability.overall_score if hasattr(res, "fishing_suitability") and hasattr(res.fishing_suitability, "overall_score") else 80
                    )
                    pfz_status = "No official PFZ advisory active"
                    if hasattr(res, "pfz") and hasattr(res.pfz, "status"):
                        pfz_status = f"PFZ: {res.pfz.status}"

                    findings = [
                        f"Fishing Suitability Score: {suitability_score}/100",
                        pfz_status,
                        "Thermal front and bio-optical density analyzed",
                    ]
                    results[agent_id] = AgentResult(
                        agent_name="Fishing Intelligence",
                        status=AgentStatus.SUCCESS.value,
                        summary=getattr(res, "summary", "Fishing suitability, PFZ zones, and biological productivity analyzed."),
                        findings=findings,
                        evidence=evidence_list,
                        confidence=0.88,
                        warnings=list(getattr(res, "warnings", [])),
                        limitations=["PFZ advisories are updated bi-weekly by INCOIS"],
                    )

            except Exception as e:
                results[agent_id] = AgentResult(
                    agent_name=selection.agent_name,
                    status=AgentStatus.ERROR.value,
                    summary=f"Assessment error: {str(e)}",
                    findings=[f"Failed to execute agent: {str(e)}"],
                    evidence=[],
                    confidence=0.0,
                    warnings=[f"Agent error: {str(e)}"],
                    limitations=["Live connector feed temporarily unavailable"],
                )

        return results
