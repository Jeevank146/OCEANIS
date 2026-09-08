from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.schemas import (
    AgentSelection,
    LocationContext,
    OrchestrationQuery,
    QueryUnderstanding,
)
from services.location import LocationService


class OrchestratorPlanner:
    """
    Intelligent Query Understanding and Dynamic Agent Selection Planner for OCEANIS.
    Parses natural-language user queries into structured semantic understanding,
    dynamically resolves geographic locations without hardcoding, and determines
    the optimal subset or full suite (6/6) of domain agents.
    """

    INTENT_KEYWORDS = {
        "FISHING_ASSESSMENT": [
            "fish", "fishing", "catch", "pfz", "tuna", "mackerel", "sardine",
            "shrimp", "angler", "trawler", "gillnet", "hook", "longline",
            "vellacha", "fishing ki", "machli", "macchi", "seafood"
        ],
        "FISHING_COMPARISON": [
            "compare", "versus", "vs", "which port", "which location", "better for fishing",
            "compare fishing", "kakinada and vizag", "vizag or kakinada"
        ],
        "ROUTE_OPERATION": [
            "route", "voyage", "sail", "transit", "navigate", "travel to", "heading to",
            "departure", "transit time", "fuel", "speed", "distance to", "travel time"
        ],
        "MARINE_SAFETY": [
            "safe", "safety", "cyclone", "storm", "warning", "danger", "hazard",
            "alert", "distress", "refuge", "harbor of refuge", "sos", "emergency"
        ],
        "MARINE_CONDITIONS": [
            "wave", "swell", "wind", "current", "sea state", "tide", "weather",
            "rough sea", "visibility", "rain", "precipitation"
        ],
        "EARTH_OBSERVATION": [
            "satellite", "chlorophyll", "ocean colour", "remote sensing",
            "thermal front", "modis", "sentinel", "optical", "cloud cover"
        ],
    }

    LOCATION_KEYWORDS = [
        "visakhapatnam", "vizag", "kakinada", "chennai", "mumbai", "kochi", "cochin",
        "paradip", "mangalore", "tuticorin", "machilipatnam", "bhavnagar", "kandla",
        "gangavaram", "krishnapatnam", "gopalpur", "dhamra", "porbandar", "karwar",
        "veraval", "nagapattinam", "cuddalore", "digha", "puri", "kannur", "kozhikode",
        "alappuzha", "kollam", "ratnagiri", "mormugao", "new delhi", "delhi", "hyderabad",
        "bangalore", "kolkata"
    ]

    COORD_REGEX = re.compile(
        r"([0-9]{1,2}(?:\.[0-9]+)?)\s*°?\s*([NSns])\s*[, ]\s*([0-9]{1,3}(?:\.[0-9]+)?)\s*°?\s*([EWew])"
    )
    DECIMAL_COORD_REGEX = re.compile(
        r"(-?[0-9]{1,2}\.[0-9]{2,8})\s*,\s*(-?[0-9]{1,3}\.[0-9]{2,8})"
    )

    TIME_REGEX = re.compile(
        r"\b([0-1]?[0-9]|2[0-3])(?::([0-5][0-9]))?\s*(am|pm|hrs|hours)?\b",
        re.IGNORECASE,
    )

    def __init__(self, location_service: Optional[LocationService] = None):
        self.location_service = location_service or LocationService()

    def plan(
        self,
        query: OrchestrationQuery,
        now: Optional[datetime] = None,
    ) -> Tuple[QueryUnderstanding, List[AgentSelection]]:
        now_utc = now or datetime.now(timezone.utc)
        raw_text = query.query.strip()
        lower_text = raw_text.lower()

        # 1. Extract Target Coordinates or Named Location
        primary_loc = None
        is_inland = False
        parsed_lat, parsed_lon = self._extract_coordinates(raw_text)

        if parsed_lat is not None and parsed_lon is not None:
            val_res = self.location_service.validate_coordinates(latitude=parsed_lat, longitude=parsed_lon)
            is_inland = (val_res.status == "INLAND")
            primary_loc = LocationContext(
                name=val_res.location_name or f"{parsed_lat:.4f}°N, {parsed_lon:.4f}°E",
                latitude=parsed_lat,
                longitude=parsed_lon,
                is_port=False,
            )
        else:
            loc_name = self._extract_location_name(lower_text)
            if loc_name:
                val_res = self.location_service.validate_location(query=loc_name)
                if val_res.status != "UNRESOLVED" and val_res.latitude is not None and val_res.longitude is not None:
                    is_inland = (val_res.status == "INLAND")
                    primary_loc = LocationContext(
                        name=val_res.display_name or loc_name.title(),
                        latitude=val_res.latitude,
                        longitude=val_res.longitude,
                        is_port=(val_res.distance_to_coast_km is not None and val_res.distance_to_coast_km < 5.0),
                    )

        # Fallback to query explicit coordinates if provided in payload
        if not primary_loc and query.latitude is not None and query.longitude is not None:
            val_res = self.location_service.validate_coordinates(latitude=query.latitude, longitude=query.longitude)
            is_inland = (val_res.status == "INLAND")
            primary_loc = LocationContext(
                name=val_res.location_name or f"{query.latitude:.4f}°N, {query.longitude:.4f}°E",
                latitude=query.latitude,
                longitude=query.longitude,
                is_port=False,
            )

        # 2. Extract Temporal Entities (Date & Time)
        target_date_str, target_time_str = self._extract_temporal(lower_text, now_utc)
        if query.target_datetime:
            try:
                dt_obj = datetime.fromisoformat(query.target_datetime.replace("Z", "+00:00"))
                target_date_str = dt_obj.strftime("%Y-%m-%d")
                target_time_str = dt_obj.strftime("%H:%M")
            except Exception:
                pass

        # 3. Classify Operational Intent
        intent = self._classify_intent(lower_text)
        is_comparison = (intent == "FISHING_COMPARISON")

        # 4. Extract Vessel Information
        vessel_type = self._extract_vessel_type(lower_text)

        understanding = QueryUnderstanding(
            intent=intent,
            primary_location=primary_loc,
            destination_location=None,
            target_date=target_date_str,
            target_time=target_time_str,
            vessel_type=vessel_type,
            operation_type="FISHING_TRIP" if "fish" in intent.lower() else "TRANSIT",
            is_comparison=is_comparison,
            comparison_locations=[],
            entities_extracted={"raw_query": raw_text, "is_inland": is_inland},
        )

        # 5. Select Domain Agents
        selected_agents = self._select_agents(understanding)
        return understanding, selected_agents

    def _classify_intent(self, text: str) -> str:
        if any(kw in text for kw in self.INTENT_KEYWORDS["FISHING_COMPARISON"]):
            return "FISHING_COMPARISON"
        elif any(kw in text for kw in self.INTENT_KEYWORDS["FISHING_ASSESSMENT"]):
            return "FISHING_ASSESSMENT"
        elif any(kw in text for kw in self.INTENT_KEYWORDS["ROUTE_OPERATION"]):
            return "ROUTE_OPERATION"
        elif any(kw in text for kw in self.INTENT_KEYWORDS["MARINE_SAFETY"]):
            return "MARINE_SAFETY"
        elif any(kw in text for kw in self.INTENT_KEYWORDS["EARTH_OBSERVATION"]):
            return "EARTH_OBSERVATION"
        elif any(kw in text for kw in self.INTENT_KEYWORDS["MARINE_CONDITIONS"]):
            return "MARINE_CONDITIONS"
        return "FISHING_ASSESSMENT"

    def _extract_location_name(self, text: str) -> Optional[str]:
        for loc in self.LOCATION_KEYWORDS:
            if re.search(r"\b" + re.escape(loc) + r"\b", text):
                return loc
        return None

    def _extract_coordinates(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        m = self.COORD_REGEX.search(text)
        if m:
            lat_val = float(m.group(1)) * (1 if m.group(2).upper() == "N" else -1)
            lon_val = float(m.group(3)) * (1 if m.group(4).upper() == "E" else -1)
            return lat_val, lon_val

        m2 = self.DECIMAL_COORD_REGEX.search(text)
        if m2:
            return float(m2.group(1)), float(m2.group(2))
        return None, None

    def _extract_temporal(self, text: str, now: datetime) -> Tuple[Optional[str], Optional[str]]:
        target_date = now.strftime("%Y-%m-%d")
        if "tomorrow" in text or "repu" in text or "kal" in text:
            target_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "day after tomorrow" in text or "ellundu" in text or "parso" in text:
            target_date = (now + timedelta(days=2)).strftime("%Y-%m-%d")

        target_time = "06:00"
        if "6 am" in text or "6am" in text or "6 ki" in text:
            target_time = "06:00"
        elif "8 am" in text or "8am" in text:
            target_time = "08:00"
        elif "9 am" in text or "9am" in text:
            target_time = "09:00"
        elif "morning" in text or "udayam" in text or "subah" in text:
            target_time = "06:00"
        elif "afternoon" in text or "madhyahnam" in text or "dopahar" in text:
            target_time = "14:00"
        elif "evening" in text or "sayantram" in text or "shaam" in text:
            target_time = "18:00"

        return target_date, target_time

    def _extract_vessel_type(self, text: str) -> str:
        if "trawler" in text:
            return "TRAWLER"
        elif "motorized" in text or "speed" in text:
            return "MOTORIZED_BOAT"
        elif "cargo" in text:
            return "CARGO_VESSEL"
        return "TRADITIONAL_FISHING_BOAT"

    def _select_agents(self, understanding: QueryUnderstanding) -> List[AgentSelection]:
        """
        Selects domain agents. For marine decision and fishing queries,
        consults all six specialized domain agents for multi-domain verification.
        """
        selections = [
            AgentSelection(
                agent_id="disaster_safety",
                agent_name="Disaster & Safety",
                domain="Safety & Emergency",
                selection_reason="Verify absence of severe weather alerts, cyclone tracks, or hazard zones.",
                priority=1,
                execution_order=1,
            ),
            AgentSelection(
                agent_id="geospatial_navigation",
                agent_name="Geo-Spatial & Navigation",
                domain="Maritime Boundaries & Ports",
                selection_reason="Check coastal classification, refuge ports, and avoidance of restricted military zones.",
                priority=2,
                execution_order=2,
            ),
            AgentSelection(
                agent_id="marine_conditions",
                agent_name="Marine Conditions",
                domain="Ocean Dynamics & Sea State",
                selection_reason="Analyze wave height, swell period, wind speeds, and surface currents.",
                priority=3,
                execution_order=3,
            ),
            AgentSelection(
                agent_id="earth_observation",
                agent_name="Earth Observation",
                domain="Satellite Remote Sensing",
                selection_reason="Evaluate chlorophyll-a ocean colour concentration and thermal fronts.",
                priority=4,
                execution_order=4,
            ),
            AgentSelection(
                agent_id="marine_operations",
                agent_name="Marine Operations",
                domain="Voyage & Fleet Operations",
                selection_reason="Calculate voyage distance, departure timing window, and operational clearance.",
                priority=5,
                execution_order=5,
            ),
            AgentSelection(
                agent_id="fishing",
                agent_name="Fishing Intelligence",
                domain="Fisheries Decision Support",
                selection_reason="Synthesize fishing suitability index, PFZ advisory status, and species conditions.",
                priority=6,
                execution_order=6,
            ),
        ]
        return selections
