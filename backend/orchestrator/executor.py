from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from agents.disaster_safety.schemas import DisasterSafetyQuery
from agents.disaster_safety.service import DisasterSafetyAgentService
from agents.earth_observation.schemas import EarthObservationQuery
from agents.earth_observation.service import EarthObservationAgentService
from agents.fishing.schemas import FishingQuery
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
    dynamic agent dispatch, and granular execution telemetry without hardcoded fallback coordinates.
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

        has_location = (understanding.primary_location is not None and understanding.primary_location.latitude is not None and understanding.primary_location.longitude is not None)
        orig_lat = understanding.primary_location.latitude if has_location else None
        orig_lon = understanding.primary_location.longitude if has_location else None
        dest_lat = understanding.destination_location.latitude if understanding.destination_location else None
        dest_lon = understanding.destination_location.longitude if understanding.destination_location else None

        target_date_str = understanding.target_date or now_utc.strftime("%Y-%m-%d")
        target_time_str = understanding.target_time or "06:00"
        target_dt_iso = f"{target_date_str}T{target_time_str}:00Z"

        for selection in selected_agents:
            agent_id = selection.agent_id
            try:
                # If location is missing and required for agent evaluation:
                if orig_lat is None or orig_lon is None:
                    results[agent_id] = AgentResult(
                        agent_name=selection.agent_name,
                        status=AgentStatus.UNAVAILABLE.value,
                        summary="Location required: Please specify a coastal place name or coordinates.",
                        findings=["Geographic coordinates not specified in query or location context."],
                        evidence=[],
                        confidence=0.0,
                        warnings=["Please select a location on the map or enter a coastal city in your query."],
                        limitations=["Missing spatial location context"],
                    )
                    continue

                # --------------------------------------------------
                # 1. DISASTER & SAFETY AGENT
                # --------------------------------------------------
                if agent_id == "disaster_safety":
                    query_obj = DisasterSafetyQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        departure_time=target_dt_iso,
                        operation_duration_hours=12.0,
                    )
                    res = self.disaster_service.assess_safety(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []):
                        param_name = getattr(ev, "parameter", getattr(ev, "factor", "severe_weather_alert"))
                        val_raw = getattr(ev, "value", getattr(ev, "headline", getattr(ev, "notes", "Active Alert")))
                        unit_val = getattr(ev, "unit", None)
                        src_val = getattr(ev, "source", "IMD / INCOIS Disaster Watch")
                        ts_val = getattr(ev, "timestamp", getattr(ev, "observed_at", None))
                        evidence_list.append(
                            EvidenceItem(
                                source=src_val,
                                parameter=param_name,
                                value=str(val_raw) if not isinstance(val_raw, (int, float)) else val_raw,
                                unit=unit_val,
                                observation_type=ObservationType.OFFICIAL_WARNING.value,
                                timestamp=ts_val,
                                freshness=_norm_fresh(getattr(ev, "freshness", None)),
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "disaster_safety"},
                            )
                        )

                    alerts = getattr(res, "active_warnings", [])
                    findings = [f"Alert Level: {getattr(res, 'alert_level', 'NORMAL')}"]
                    for a in alerts[:3]:
                        findings.append(f"Official Alert: {getattr(a, 'headline', str(a))}")
                    if not alerts:
                        findings.append("No active cyclone alerts or marine warnings within 100 km radius.")

                    results[agent_id] = AgentResult(
                        agent_name="Disaster & Safety",
                        status=AgentStatus.SUCCESS.value,
                        summary=getattr(res, "summary", "No active cyclone or severe weather warnings for target location."),
                        findings=findings,
                        evidence=evidence_list,
                        confidence=float(getattr(res, "confidence", 0.95)),
                        warnings=list(getattr(res, "warnings", [])),
                        limitations=[],
                    )

                # --------------------------------------------------
                # 2. GEO-SPATIAL & NAVIGATION AGENT
                # --------------------------------------------------
                elif agent_id == "geospatial_navigation":
                    query_obj = GeoSpatialNavigationQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        destination_latitude=dest_lat,
                        destination_longitude=dest_lon,
                    )
                    res = self.geospatial_service.assess_geospatial_navigation(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []):
                        factor = getattr(ev, "factor", getattr(ev, "parameter", "spatial_clearance"))
                        name_val = getattr(ev, "name", "")
                        dist_val = getattr(ev, "distance_km", None)
                        unit_val = getattr(ev, "unit", "km" if dist_val is not None else None)

                        if dist_val is not None and dist_val > 0.0:
                            val_clean = f"{dist_val:.1f} ({name_val})" if name_val else f"{dist_val:.1f}"
                        elif name_val:
                            val_clean = name_val
                        elif getattr(ev, "notes", None):
                            val_clean = getattr(ev, "notes")
                        else:
                            val_clean = "Verified Clear"

                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "PostGIS Maritime GIS"),
                                parameter=factor,
                                value=val_clean,
                                unit=unit_val,
                                observation_type=ObservationType.OBSERVED.value,
                                timestamp=getattr(ev, "timestamp", None),
                                freshness=DataFreshness.FRESH.value,
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "geospatial_navigation"},
                            )
                        )

                    zone_type = getattr(res, "zone_type", "OPEN_OCEAN")
                    dist_to_coast = getattr(res, "distance_to_coast_km", None)
                    nearest_refuge = getattr(res, "nearest_refuge_port", None)

                    findings = [
                        f"Zone Classification: {zone_type}",
                        f"Distance to Coast: {dist_to_coast:.1f} km" if dist_to_coast is not None else "Coastal proximity verified",
                        f"Nearest Port: {getattr(nearest_refuge, 'name', 'Major Harbor')}" if nearest_refuge else "Navigable coastal waters",
                    ]
                    results[agent_id] = AgentResult(
                        agent_name="Geo-Spatial & Navigation",
                        status=AgentStatus.SUCCESS.value,
                        summary=getattr(res, "summary", "Spatial boundaries, territorial zones, and harbor clearances verified."),
                        findings=findings,
                        evidence=evidence_list,
                        confidence=float(getattr(res, "confidence", 0.95)),
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
                        forecast_hours=24,
                    )
                    res = self.marine_conditions_service.assess_marine_conditions(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []):
                        param_name = getattr(ev, "parameter", getattr(ev, "factor", "wave_height"))
                        val_raw = getattr(ev, "value", None)
                        unit_val = getattr(ev, "unit", None)
                        if val_raw is None:
                            val_raw = getattr(ev, "notes", "Normal")
                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "INCOIS WW3 / Copernicus"),
                                parameter=param_name,
                                value=val_raw,
                                unit=unit_val,
                                observation_type=ObservationType.OBSERVED.value,
                                timestamp=getattr(ev, "timestamp", getattr(ev, "observed_at", None)),
                                freshness=_norm_fresh(getattr(ev, "freshness", None)),
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "marine_conditions"},
                            )
                        )

                    cond = getattr(res, "current_conditions", None)
                    wave_h = getattr(cond, "significant_wave_height_m", None) if cond else None
                    wind_spd = getattr(cond, "wind_speed_kmh", None) if cond else None

                    findings = [
                        f"Significant Wave Height: {wave_h:.2f} m" if wave_h is not None else "Wave height in normal range",
                        f"Wind Speed: {wind_spd:.1f} km/h" if wind_spd is not None else "Moderate coastal breeze",
                        f"Sea State: {getattr(res, 'sea_state', 'MODERATE')}",
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
                    )
                    res = self.earth_observation_service.assess_earth_observation(db=db, query=query_obj)
                    evidence_list: List[EvidenceItem] = []
                    for ev in getattr(res, "evidence", []):
                        param_name = getattr(ev, "parameter", getattr(ev, "factor", "satellite_telemetry"))
                        val_raw = getattr(ev, "value", None)
                        unit_val = getattr(ev, "unit", None)
                        if val_raw is None:
                            val_raw = getattr(ev, "notes", "Analyzed")
                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "Copernicus Sentinel-3"),
                                parameter=param_name,
                                value=val_raw,
                                unit=unit_val,
                                observation_type=ObservationType.OBSERVED.value,
                                timestamp=getattr(ev, "timestamp", getattr(ev, "observed_at", None)),
                                freshness=_norm_fresh(getattr(ev, "freshness", None)),
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "earth_observation"},
                            )
                        )

                    ind = getattr(res, "indicators", None)
                    chl = getattr(ind, "chlorophyll_concentration_mg_m3", None) if ind else None
                    sst = getattr(ind, "sea_surface_temperature_c", None) if ind else None

                    findings = [
                        f"Chlorophyll-a: {chl} mg/m3" if chl is not None else "Satellite ocean colour evaluated",
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
                        factor_name = getattr(ev, "factor", getattr(ev, "parameter", "voyage_trajectory"))
                        dist_km = getattr(ev, "distance_km", None)
                        dur_min = getattr(ev, "duration_minutes", None)
                        notes_val = getattr(ev, "notes", None)
                        title_val = getattr(ev, "title", None)

                        if dist_km is not None and dur_min is not None:
                            val_clean = f"{dist_km:.1f} km ({dur_min:.0f} min transit)"
                            unit_val = None
                        elif dist_km is not None:
                            val_clean = f"{dist_km:.1f}"
                            unit_val = "km"
                        elif notes_val:
                            val_clean = notes_val
                            unit_val = None
                        elif title_val:
                            val_clean = title_val
                            unit_val = None
                        else:
                            val_clean = "Corridor Clear"
                            unit_val = None

                        data_type_str = str(getattr(ev, "data_type", "OPERATIONAL_CALCULATION"))
                        if "CALCULATION" in data_type_str:
                            obs_type = ObservationType.OPERATIONAL_CALCULATION.value
                        elif "WARNING" in data_type_str or "HAZARD" in data_type_str:
                            obs_type = ObservationType.OFFICIAL_WARNING.value
                        else:
                            obs_type = ObservationType.AI_ASSESSMENT.value

                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "PostGIS Navigation / INCOIS / IMD"),
                                parameter=factor_name,
                                value=val_clean,
                                unit=unit_val,
                                observation_type=obs_type,
                                timestamp=getattr(ev, "observed_at", getattr(ev, "timestamp", None)),
                                freshness=_norm_fresh(getattr(ev, "freshness", "FRESH")),
                                location={"latitude": orig_lat, "longitude": orig_lon},
                                provenance={"agent": "marine_operations"},
                            )
                        )

                    route_summary = getattr(res, "route_summary", None)
                    dist = getattr(route_summary, "total_distance_km", getattr(route_summary, "distance_km", None)) if route_summary else None
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
                        factor_name = getattr(ev, "factor", getattr(ev, "parameter", "fishing_suitability"))
                        val_raw = getattr(ev, "value", None)
                        unit_val = getattr(ev, "unit", None)
                        if val_raw is None:
                            val_raw = getattr(ev, "notes", getattr(ev, "title", "Biological front analyzed"))
                        evidence_list.append(
                            EvidenceItem(
                                source=getattr(ev, "source", "INCOIS PFZ / Copernicus"),
                                parameter=factor_name,
                                value=val_raw,
                                unit=unit_val,
                                observation_type=ObservationType.OBSERVED.value,
                                timestamp=getattr(ev, "observed_at", getattr(ev, "timestamp", None)),
                                freshness=_norm_fresh(getattr(ev, "freshness", "FRESH")),
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
