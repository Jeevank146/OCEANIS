from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from agents.disaster_safety.schemas import DisasterSafetyQuery
from agents.disaster_safety.service import DisasterSafetyAgentService
from agents.earth_observation.schemas import EarthObservationQuery
from agents.earth_observation.service import EarthObservationAgentService
from agents.fishing.schemas import (
    FishingLocationInput,
    FishingQuery,
    LocationComparisonQuery,
)
from agents.fishing.service import FishingAgentService
from agents.geospatial_navigation.schemas import GeoSpatialNavigationQuery
from agents.geospatial_navigation.service import GeoSpatialNavigationAgentService
from agents.marine_conditions.schemas import MarineConditionsQuery
from agents.marine_conditions.service import MarineConditionsAgentService
from agents.marine_operations.schemas import MarineOperationsQuery
from agents.marine_operations.service import MarineOperationsAgentService
from orchestrator.schemas import (
    AgentExecutionResult,
    AgentSelection,
    QueryUnderstanding,
)


class AgentExecutor:
    """
    Structured execution coordinator for OCEANIS domain agents.
    Executes selected domain agents with error handling, latency monitoring,
    and standardized result normalization.
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
    ) -> Dict[str, AgentExecutionResult]:
        """
        Executes each selected domain agent in priority order and captures structured outputs.
        """
        results: Dict[str, AgentExecutionResult] = {}
        now_utc = now or datetime.now(timezone.utc)

        # Primary location coordinates
        orig_lat = understanding.primary_location.latitude if understanding.primary_location else 16.9890
        orig_lon = understanding.primary_location.longitude if understanding.primary_location else 82.2474

        # Destination coordinates if present
        dest_lat = understanding.destination_location.latitude if understanding.destination_location else None
        dest_lon = understanding.destination_location.longitude if understanding.destination_location else None

        target_date_str = understanding.target_date or now_utc.strftime("%Y-%m-%d")
        target_time_str = understanding.target_time or "06:00"
        target_dt_iso = f"{target_date_str}T{target_time_str}:00Z"

        for selection in selected_agents:
            agent_id = selection.agent_id
            start_t = time.perf_counter()
            try:
                if agent_id == "disaster_safety":
                    query_obj = DisasterSafetyQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        radius_km=50.0,
                        target_datetime=target_dt_iso,
                    )
                    res = self.disaster_service.assess_safety(db=db, query=query_obj)
                    res_dict = res.model_dump(mode="json")
                    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                    results[agent_id] = AgentExecutionResult(
                        agent_id=agent_id,
                        agent_name=selection.agent_name,
                        status="SUCCESS",
                        result=res_dict,
                        confidence=res.confidence,
                        freshness=res.data_freshness,
                        warnings=res.warnings,
                        execution_time_ms=round(elapsed_ms, 2),
                    )

                elif agent_id == "geospatial_navigation":
                    query_obj = GeoSpatialNavigationQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        destination_latitude=dest_lat,
                        destination_longitude=dest_lon,
                    )
                    res = self.geospatial_service.assess_geospatial_navigation(db=db, query=query_obj)
                    res_dict = res.model_dump(mode="json")
                    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                    results[agent_id] = AgentExecutionResult(
                        agent_id=agent_id,
                        agent_name=selection.agent_name,
                        status="SUCCESS",
                        result=res_dict,
                        confidence=res.confidence,
                        freshness=res.data_freshness,
                        warnings=res.warnings,
                        execution_time_ms=round(elapsed_ms, 2),
                    )

                elif agent_id == "marine_conditions":
                    query_obj = MarineConditionsQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        target_datetime=target_dt_iso,
                    )
                    res = self.marine_conditions_service.assess_marine_conditions(db=db, query=query_obj)
                    res_dict = res.model_dump(mode="json")
                    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                    results[agent_id] = AgentExecutionResult(
                        agent_id=agent_id,
                        agent_name=selection.agent_name,
                        status="SUCCESS",
                        result=res_dict,
                        confidence=res.confidence,
                        freshness=res.data_freshness,
                        warnings=res.warnings,
                        execution_time_ms=round(elapsed_ms, 2),
                    )

                elif agent_id == "earth_observation":
                    query_obj = EarthObservationQuery(
                        latitude=orig_lat,
                        longitude=orig_lon,
                        target_datetime=target_dt_iso,
                    )
                    res = self.earth_observation_service.assess_earth_observation(db=db, query=query_obj)
                    res_dict = res.model_dump(mode="json")
                    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                    results[agent_id] = AgentExecutionResult(
                        agent_id=agent_id,
                        agent_name=selection.agent_name,
                        status="SUCCESS",
                        result=res_dict,
                        confidence=res.confidence,
                        freshness=res.data_freshness,
                        warnings=res.warnings,
                        execution_time_ms=round(elapsed_ms, 2),
                    )

                elif agent_id == "marine_operations":
                    # Fallback destination if none specified for operations
                    ops_dest_lat = dest_lat if dest_lat is not None else (orig_lat + 0.5)
                    ops_dest_lon = dest_lon if dest_lon is not None else (orig_lon + 0.5)
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
                    res_dict = res.model_dump(mode="json")
                    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                    results[agent_id] = AgentExecutionResult(
                        agent_id=agent_id,
                        agent_name=selection.agent_name,
                        status="SUCCESS",
                        result=res_dict,
                        confidence=res.confidence,
                        freshness=res.data_freshness,
                        warnings=res.warnings,
                        execution_time_ms=round(elapsed_ms, 2),
                    )

                elif agent_id == "fishing":
                    if understanding.is_comparison and len(understanding.comparison_locations) >= 2:
                        comp_query = LocationComparisonQuery(
                            location_a=FishingLocationInput(
                                name=understanding.comparison_locations[0].name or "Location A",
                                latitude=understanding.comparison_locations[0].latitude,
                                longitude=understanding.comparison_locations[0].longitude,
                            ),
                            location_b=FishingLocationInput(
                                name=understanding.comparison_locations[1].name or "Location B",
                                latitude=understanding.comparison_locations[1].latitude,
                                longitude=understanding.comparison_locations[1].longitude,
                            ),
                            date=target_date_str,
                            departure_time=target_time_str,
                            vessel_type=understanding.vessel_type or "small_boat",
                            target_species=understanding.target_species,
                        )
                        res = self.fishing_service.compare_locations(db=db, query=comp_query)
                        res_dict = res.model_dump(mode="json")
                        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                        results[agent_id] = AgentExecutionResult(
                            agent_id=agent_id,
                            agent_name=selection.agent_name,
                            status="SUCCESS",
                            result=res_dict,
                            confidence=0.95,
                            freshness="FRESH",
                            warnings=[],
                            execution_time_ms=round(elapsed_ms, 2),
                        )
                    else:
                        query_obj = FishingQuery(
                            latitude=orig_lat,
                            longitude=orig_lon,
                            date=target_date_str,
                            departure_time=target_time_str,
                            vessel_type=understanding.vessel_type or "small_boat",
                            target_species=understanding.target_species,
                        )
                        res = self.fishing_service.assess_fishing_query(db=db, query=query_obj)
                        res_dict = res.model_dump(mode="json")
                        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                        conf_map = {"HIGH": 0.95, "MEDIUM": 0.75, "LOW": 0.5, "UNKNOWN": 0.3}
                        if hasattr(res.confidence, "level"):
                            conf_val = conf_map.get(str(res.confidence.level).upper(), 0.85)
                        elif isinstance(res.confidence, (int, float)):
                            conf_val = float(res.confidence)
                        else:
                            conf_val = 0.85

                        freshness_val = getattr(res, "freshness", None) or getattr(res, "data_freshness", "FRESH")
                        results[agent_id] = AgentExecutionResult(
                            agent_id=agent_id,
                            agent_name=selection.agent_name,
                            status="SUCCESS",
                            result=res_dict,
                            confidence=conf_val,
                            freshness=freshness_val,
                            warnings=res.warnings,
                            execution_time_ms=round(elapsed_ms, 2),
                        )

            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                results[agent_id] = AgentExecutionResult(
                    agent_id=agent_id,
                    agent_name=selection.agent_name,
                    status="FAILED",
                    result=None,
                    confidence=0.0,
                    freshness="UNAVAILABLE",
                    warnings=[f"Agent {selection.agent_name} failed: {str(e)}"],
                    execution_time_ms=round(elapsed_ms, 2),
                    error=str(e),
                )

        return results
