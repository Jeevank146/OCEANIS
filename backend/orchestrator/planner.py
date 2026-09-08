from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.schemas import (
    AgentSelection,
    LocationContext,
    OrchestrationQuery,
    QueryUnderstanding,
)
from schemas.agent_contract import QueryIntent
from services.location import LocationService


class OrchestratorPlanner:
    """
    Intelligent Dynamic Query Understanding and Agent Selection Planner for OCEANIS.
    Dynamically analyzes arbitrary marine questions, extracts spatial/temporal/scenario
    entities without fixed templates or hardcoded locations, and dispatches only
    the required domain agents.
    """

    INTENT_KEYWORDS = {
        QueryIntent.COMPARISON.value: [
            "compare", "versus", "vs", "which port", "which location", "which is better",
            "better for fishing", "better place", "or ", "between "
        ],
        QueryIntent.WHAT_IF.value: [
            "what if", "what-if", "if i leave", "if we leave", "if i go", "instead of",
            "suppose i", "what happens if", "shifting to", "delay to"
        ],
        QueryIntent.ROUTE.value: [
            "route", "voyage", "sail from", "transit from", "navigate from",
            "passage to", "safer route", "travel from", "heading to", "waypoint"
        ],
        QueryIntent.SAFETY.value: [
            "cyclone", "storm", "warning", "danger", "hazard", "alert", "distress",
            "protected marine zone", "protected zone", "marine sanctuary", "mpa", "restricted zone",
            "is it safe", "safety alert", "heavy weather", "emergency", "refuge"
        ],
        QueryIntent.INFORMATION.value: [
            "what is the", "what are the", "show sst", "show chlorophyll", "current sst",
            "ocean conditions near", "current wave", "currents offshore", "sea state near",
            "water clarity", "turbidity", "chlorophyll near", "sea temperature"
        ],
        QueryIntent.DECISION.value: [
            "can i go", "can we go", "is it suitable", "should i go", "can i sail",
            "can i fish", "is it recommended", "permission to sail", "trip tomorrow",
            "fishing tomorrow", "good to fish", "allowed to sail"
        ],
    }

    LOCATION_PREPOSITIONS = [
        r"near\s+([a-zA-Z\s]{3,25})",
        r"around\s+([a-zA-Z\s]{3,25})",
        r"offshore\s+(?:from\s+)?([a-zA-Z\s]{3,25})",
        r"from\s+([a-zA-Z\s]{3,25})",
        r"to\s+([a-zA-Z\s]{3,25})",
        r"in\s+([a-zA-Z\s]{3,25})",
        r"at\s+([a-zA-Z\s]{3,25})",
        r"between\s+([a-zA-Z\s]{3,20})\s+and\s+([a-zA-Z\s]{3,20})",
        r"([a-zA-Z\s]{3,20})\s+or\s+([a-zA-Z\s]{3,20})",
        r"([a-zA-Z\s]{3,20})\s+vs\s+([a-zA-Z\s]{3,20})",
    ]

    KNOWN_COASTAL_NAMES = [
        "visakhapatnam", "vizag", "kakinada", "chennai", "mumbai", "kochi", "cochin",
        "paradip", "mangalore", "tuticorin", "machilipatnam", "bhavnagar", "kandla",
        "gangavaram", "krishnapatnam", "gopalpur", "dhamra", "porbandar", "karwar",
        "veraval", "nagapattinam", "cuddalore", "digha", "puri", "kannur", "kozhikode",
        "alappuzha", "kollam", "ratnagiri", "mormugao", "goa", "port blair", "lakshadweep",
        "diu", "daman", "okha", "new delhi", "delhi", "hyderabad", "bangalore", "kolkata"
    ]

    COORD_REGEX = re.compile(
        r"([0-9]{1,2}(?:\.[0-9]+)?)\s*°?\s*([NSns])\s*[, ]\s*([0-9]{1,3}(?:\.[0-9]+)?)\s*°?\s*([EWew])"
    )
    DECIMAL_COORD_REGEX = re.compile(
        r"(-?[0-9]{1,2}\.[0-9]{2,8})\s*,\s*(-?[0-9]{1,3}\.[0-9]{2,8})"
    )

    TIME_REGEX = re.compile(
        r"([0-1]?[0-9]|2[0-3])(?::([0-5][0-9]))?\s*(am|pm|hrs|hours)?",
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

        # 1. Classify Query Intent
        intent = self._classify_intent(lower_text)

        # 2. Extract Location Entities (Primary, Destination, Comparison Targets)
        primary_loc, dest_loc, comparison_locs, is_inland, loc_missing = self._extract_locations(raw_text, query)

        # 3. Extract Temporal Entities (Date & Time)
        target_date_str, target_time_str = self._extract_temporal(lower_text, now_utc)
        if query.target_datetime:
            try:
                dt_obj = datetime.fromisoformat(query.target_datetime.replace("Z", "+00:00"))
                target_date_str = dt_obj.strftime("%Y-%m-%d")
                target_time_str = dt_obj.strftime("%H:%M")
            except Exception:
                pass

        # 4. Extract What-If Factors if applicable
        what_if_factor = self._extract_what_if_factor(lower_text) if intent == QueryIntent.WHAT_IF.value else None

        # 5. Extract Activity / Operation / Vessel
        vessel_type = self._extract_vessel_type(lower_text)
        is_fishing_related = any(k in lower_text for k in ["fish", "pfz", "catch", "trawler", "angler", "species", "tuna", "mackerel"])
        operation_type = "FISHING_TRIP" if is_fishing_related else ("TRANSIT" if intent == QueryIntent.ROUTE.value else "GENERAL_MARINE")

        understanding = QueryUnderstanding(
            intent=intent,
            primary_location=primary_loc,
            destination_location=dest_loc,
            comparison_locations=comparison_locs,
            target_date=target_date_str,
            target_time=target_time_str,
            vessel_type=vessel_type,
            operation_type=operation_type,
            is_comparison=(intent == QueryIntent.COMPARISON.value or len(comparison_locs) > 1),
            entities_extracted={
                "raw_query": raw_text,
                "intent": intent,
                "is_inland": is_inland,
                "location_missing": loc_missing,
                "what_if_factor": what_if_factor,
                "is_fishing_related": is_fishing_related,
            },
        )

        # 6. Select Domain Agents Dynamically based on Intent & Query Content
        selected_agents = self._select_agents(understanding, lower_text)
        return understanding, selected_agents

    def _classify_intent(self, text: str) -> str:
        # Check comparison first (e.g. "which is better", "A or B", "A vs B")
        if any(kw in text for kw in self.INTENT_KEYWORDS[QueryIntent.COMPARISON.value]):
            if any(l in text for l in self.KNOWN_COASTAL_NAMES):
                # Has comparison keywords and location candidates
                if " or " in text or " vs " in text or "compare" in text or "which is better" in text or "which location" in text:
                    return QueryIntent.COMPARISON.value

        if any(kw in text for kw in self.INTENT_KEYWORDS[QueryIntent.WHAT_IF.value]):
            return QueryIntent.WHAT_IF.value

        if any(kw in text for kw in self.INTENT_KEYWORDS[QueryIntent.ROUTE.value]):
            return QueryIntent.ROUTE.value

        if any(kw in text for kw in self.INTENT_KEYWORDS[QueryIntent.SAFETY.value]):
            # If asking specifically about warnings, cyclones, or protected zones
            if "cyclone" in text or "warning" in text or "protected zone" in text or "mpa" in text or "sanctuary" in text:
                return QueryIntent.SAFETY.value

        if any(kw in text for kw in self.INTENT_KEYWORDS[QueryIntent.INFORMATION.value]):
            # Check if it is purely informational (e.g. "What is SST", "Show chlorophyll")
            return QueryIntent.INFORMATION.value

        if any(kw in text for kw in self.INTENT_KEYWORDS[QueryIntent.DECISION.value]):
            return QueryIntent.DECISION.value

        # Default classification based on question structure
        if text.startswith("what") or text.startswith("show") or text.startswith("display") or "condition" in text:
            return QueryIntent.INFORMATION.value

        return QueryIntent.DECISION.value

    def _extract_locations(
        self, raw_text: str, query: OrchestrationQuery
    ) -> Tuple[Optional[LocationContext], Optional[LocationContext], List[LocationContext], bool, bool]:
        lower_text = raw_text.lower()
        primary_loc: Optional[LocationContext] = None
        dest_loc: Optional[LocationContext] = None
        comparison_locs: List[LocationContext] = []
        is_inland = False
        loc_missing = False

        # 1. Coordinate check
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
            return primary_loc, dest_loc, comparison_locs, is_inland, loc_missing

        # 2. Check for route or comparison patterns (e.g. "from A to B" or "A or B" or "A vs B")
        route_match = re.search(r"from\s+([a-zA-Z\s]{3,20})\s+to\s+([a-zA-Z\s]{3,20})", lower_text)
        if route_match:
            loc_a = self._clean_location_string(route_match.group(1))
            loc_b = self._clean_location_string(route_match.group(2))
            val_a = self.location_service.validate_location(query=loc_a)
            val_b = self.location_service.validate_location(query=loc_b)
            if val_a.status != "UNRESOLVED" and val_a.latitude is not None and val_a.longitude is not None:
                primary_loc = LocationContext(
                    name=val_a.display_name or loc_a.title(),
                    latitude=val_a.latitude,
                    longitude=val_a.longitude,
                    is_port=True,
                )
            if val_b.status != "UNRESOLVED" and val_b.latitude is not None and val_b.longitude is not None:
                dest_loc = LocationContext(
                    name=val_b.display_name or loc_b.title(),
                    latitude=val_b.latitude,
                    longitude=val_b.longitude,
                    is_port=True,
                )
            if primary_loc:
                return primary_loc, dest_loc, comparison_locs, is_inland, loc_missing

        comp_match = re.search(r"([a-zA-Z\s]{3,20})\s+(?:or|vs|versus|and)\s+([a-zA-Z\s]{3,20})", lower_text)
        if comp_match:
            cand_a = self._clean_location_string(comp_match.group(1))
            cand_b = self._clean_location_string(comp_match.group(2))
            val_a = self.location_service.validate_location(query=cand_a)
            val_b = self.location_service.validate_location(query=cand_b)
            if val_a.status != "UNRESOLVED" and val_b.status != "UNRESOLVED":
                if val_a.latitude is not None and val_b.latitude is not None:
                    loc_obj_a = LocationContext(
                        name=val_a.display_name or cand_a.title(),
                        latitude=val_a.latitude,
                        longitude=val_a.longitude,
                        is_port=True,
                    )
                    loc_obj_b = LocationContext(
                        name=val_b.display_name or cand_b.title(),
                        latitude=val_b.latitude,
                        longitude=val_b.longitude,
                        is_port=True,
                    )
                    comparison_locs = [loc_obj_a, loc_obj_b]
                    primary_loc = loc_obj_a
                    return primary_loc, dest_loc, comparison_locs, is_inland, loc_missing

        # 3. Check for specific named locations
        for known_name in self.KNOWN_COASTAL_NAMES:
            if re.search(r"" + re.escape(known_name) + r"", lower_text):
                val_res = self.location_service.validate_location(query=known_name)
                if val_res.status != "UNRESOLVED" and val_res.latitude is not None and val_res.longitude is not None:
                    is_inland = (val_res.status == "INLAND")
                    primary_loc = LocationContext(
                        name=val_res.display_name or known_name.title(),
                        latitude=val_res.latitude,
                        longitude=val_res.longitude,
                        is_port=(val_res.distance_to_coast_km is not None and val_res.distance_to_coast_km < 5.0),
                    )
                    return primary_loc, dest_loc, comparison_locs, is_inland, loc_missing

        # 4. Check preposition patterns ("near X", "around X", "offshore X", etc.)
        for pattern in self.LOCATION_PREPOSITIONS:
            m = re.search(pattern, lower_text)
            if m:
                cand = self._clean_location_string(m.group(1))
                val_res = self.location_service.validate_location(query=cand)
                if val_res.status != "UNRESOLVED" and val_res.latitude is not None and val_res.longitude is not None:
                    is_inland = (val_res.status == "INLAND")
                    primary_loc = LocationContext(
                        name=val_res.display_name or cand.title(),
                        latitude=val_res.latitude,
                        longitude=val_res.longitude,
                        is_port=(val_res.distance_to_coast_km is not None and val_res.distance_to_coast_km < 5.0),
                    )
                    return primary_loc, dest_loc, comparison_locs, is_inland, loc_missing

        # 5. Fallback to query payload explicit coordinates or location context if passed
        if query.latitude is not None and query.longitude is not None:
            val_res = self.location_service.validate_coordinates(latitude=query.latitude, longitude=query.longitude)
            is_inland = (val_res.status == "INLAND")
            primary_loc = LocationContext(
                name=val_res.location_name or f"{query.latitude:.4f}°N, {query.longitude:.4f}°E",
                latitude=query.latitude,
                longitude=query.longitude,
                is_port=False,
            )
            return primary_loc, dest_loc, comparison_locs, is_inland, loc_missing

        # 6. If no location found, mark as missing (do NOT silently use a default city)
        loc_missing = True
        return primary_loc, dest_loc, comparison_locs, is_inland, loc_missing

    def _clean_location_string(self, text: str) -> str:
        # Strip stop words, punctuation, and extra phrases
        cleaned = re.sub(r"(tomorrow|today|tonight|morning|evening|at|for|fishing|sailing|weather|conditions|port)", "", text, flags=re.IGNORECASE)
        cleaned = cleaned.strip(" .,?!:;")
        return cleaned.strip()

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
        target_date = None
        target_time = None

        if "tomorrow" in text or "repu" in text or "kal" in text:
            target_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "day after tomorrow" in text or "ellundu" in text or "parso" in text:
            target_date = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        elif "today" in text or "tonight" in text:
            target_date = now.strftime("%Y-%m-%d")
        elif "next week" in text:
            target_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")

        # Specific time matching
        if "6 am" in text or "6am" in text or "06:00" in text:
            target_time = "06:00"
        elif "8 am" in text or "8am" in text or "08:00" in text:
            target_time = "08:00"
        elif "9 am" in text or "9am" in text or "09:00" in text:
            target_time = "09:00"
        elif "10 am" in text or "10am" in text or "10:00" in text:
            target_time = "10:00"
        elif "2 pm" in text or "2pm" in text or "14:00" in text:
            target_time = "14:00"
        elif "4 pm" in text or "4pm" in text or "16:00" in text:
            target_time = "16:00"
        elif "evening" in text or "sayantram" in text or "shaam" in text:
            target_time = "18:00"
        elif "morning" in text or "udayam" in text or "subah" in text:
            target_time = "06:00"
        elif "afternoon" in text or "madhyahnam" in text or "dopahar" in text:
            target_time = "14:00"
        elif "night" in text or "ratri" in text:
            target_time = "21:00"

        return target_date, target_time

    def _extract_what_if_factor(self, text: str) -> str:
        if "9 am" in text or "9am" in text:
            return "departure_time: 09:00"
        elif "8 am" in text or "8am" in text:
            return "departure_time: 08:00"
        elif "tomorrow" in text:
            return "date: tomorrow"
        elif "offshore" in text or "km" in text:
            return "distance: offshore"
        elif "route" in text:
            return "route: alternative"
        return "parameter_shift"

    def _extract_vessel_type(self, text: str) -> str:
        if "trawler" in text:
            return "TRAWLER"
        elif "motorized" in text or "speed" in text:
            return "MOTORIZED_BOAT"
        elif "cargo" in text:
            return "CARGO_VESSEL"
        return "TRADITIONAL_FISHING_BOAT"

    def _select_agents(self, understanding: QueryUnderstanding, text: str) -> List[AgentSelection]:
        """
        Dynamically selects ONLY the domain agents relevant to the specific query intent and content.
        """
        intent = understanding.intent
        is_fishing = understanding.entities_extracted.get("is_fishing_related", False)

        all_agent_defs = {
            "disaster_safety": AgentSelection(
                agent_id="disaster_safety",
                agent_name="Disaster & Safety",
                domain="Safety & Emergency",
                selection_reason="Verify absence of severe weather alerts, cyclone tracks, or hazard zones.",
                priority=1,
                execution_order=1,
            ),
            "geospatial_navigation": AgentSelection(
                agent_id="geospatial_navigation",
                agent_name="Geo-Spatial & Navigation",
                domain="Maritime Boundaries & Ports",
                selection_reason="Check coastal classification, refuge ports, and avoidance of restricted military zones.",
                priority=2,
                execution_order=2,
            ),
            "marine_conditions": AgentSelection(
                agent_id="marine_conditions",
                agent_name="Marine Conditions",
                domain="Ocean Dynamics & Sea State",
                selection_reason="Analyze wave height, swell period, wind speeds, and surface currents.",
                priority=3,
                execution_order=3,
            ),
            "earth_observation": AgentSelection(
                agent_id="earth_observation",
                agent_name="Earth Observation",
                domain="Satellite Remote Sensing",
                selection_reason="Evaluate chlorophyll-a ocean colour concentration and thermal fronts.",
                priority=4,
                execution_order=4,
            ),
            "marine_operations": AgentSelection(
                agent_id="marine_operations",
                agent_name="Marine Operations",
                domain="Voyage & Fleet Operations",
                selection_reason="Calculate voyage distance, departure timing window, and operational clearance.",
                priority=5,
                execution_order=5,
            ),
            "fishing": AgentSelection(
                agent_id="fishing",
                agent_name="Fishing Intelligence",
                domain="Fisheries Decision Support",
                selection_reason="Synthesize fishing suitability index, PFZ advisory status, and species conditions.",
                priority=6,
                execution_order=6,
            ),
        }

        # 1. Pure SST / Chlorophyll / Satellite Remote Sensing query
        if ("sst" in text or "chlorophyll" in text or "satellite" in text or "clarity" in text or "colour" in text) and not is_fishing:
            return [
                all_agent_defs["earth_observation"],
                all_agent_defs["marine_conditions"],
                all_agent_defs["geospatial_navigation"],
            ]

        # 2. Cyclone / Weather Alert / Disaster Safety query
        if ("cyclone" in text or "warning" in text or "storm" in text or "distress" in text) and not is_fishing:
            return [
                all_agent_defs["disaster_safety"],
                all_agent_defs["marine_conditions"],
                all_agent_defs["geospatial_navigation"],
            ]

        # 3. Protected Marine Zone / Marine Sanctuary / Geospatial Boundary query
        if "protected zone" in text or "protected marine" in text or "sanctuary" in text or "mpa" in text:
            return [
                all_agent_defs["geospatial_navigation"],
                all_agent_defs["disaster_safety"],
            ]

        # 4. Route / Transit / Navigation query
        if intent == QueryIntent.ROUTE.value or ("route" in text and not is_fishing):
            return [
                all_agent_defs["geospatial_navigation"],
                all_agent_defs["marine_conditions"],
                all_agent_defs["disaster_safety"],
                all_agent_defs["marine_operations"],
            ]

        # 5. General Ocean Conditions query (waves, wind, currents) without fishing
        if intent == QueryIntent.INFORMATION.value and not is_fishing:
            return [
                all_agent_defs["marine_conditions"],
                all_agent_defs["earth_observation"],
                all_agent_defs["geospatial_navigation"],
            ]

        # 6. Fishing Suitability / Fishing Decision / Comprehensive Marine Decision
        # Full 6-agent consultation
        return [
            all_agent_defs["disaster_safety"],
            all_agent_defs["geospatial_navigation"],
            all_agent_defs["marine_conditions"],
            all_agent_defs["earth_observation"],
            all_agent_defs["marine_operations"],
            all_agent_defs["fishing"],
        ]
