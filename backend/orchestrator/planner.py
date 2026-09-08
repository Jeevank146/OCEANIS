from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.registry import AgentRegistry
from orchestrator.schemas import (
    AgentSelection,
    LocationContext,
    OrchestrationQuery,
    QueryUnderstanding,
)

# Known coastal ports and geographic reference coordinates
KNOWN_LOCATIONS: Dict[str, Tuple[float, float, bool, str]] = {
    "kakinada": (16.9890, 82.2474, True, "Kakinada Deep Water Port"),
    "kakinada port": (16.9890, 82.2474, True, "Kakinada Deep Water Port"),
    "visakhapatnam": (17.6868, 83.2185, True, "Visakhapatnam Port"),
    "visakhapatnam port": (17.6868, 83.2185, True, "Visakhapatnam Port"),
    "vizag": (17.6868, 83.2185, True, "Visakhapatnam Port"),
    "vizag port": (17.6868, 83.2185, True, "Visakhapatnam Port"),
    "machilipatnam": (16.1800, 81.1300, True, "Machilipatnam Port"),
    "machilipatnam port": (16.1800, 81.1300, True, "Machilipatnam Port"),
    "chennai": (13.0827, 80.2707, True, "Chennai Port"),
    "chennai port": (13.0827, 80.2707, True, "Chennai Port"),
    "gopalpur": (19.2600, 84.9000, True, "Gopalpur Port"),
    "gopalpur port": (19.2600, 84.9000, True, "Gopalpur Port"),
    "paradip": (20.3160, 86.6100, True, "Paradip Port"),
    "paradip port": (20.3160, 86.6100, True, "Paradip Port"),
    "mumbai": (18.9400, 72.8400, True, "Mumbai Port"),
    "kochi": (9.9600, 76.2600, True, "Cochin Port"),
    "cochin": (9.9600, 76.2600, True, "Cochin Port"),
    "mangaluru": (12.9100, 74.8500, True, "New Mangalore Port"),
    "mangalore": (12.9100, 74.8500, True, "New Mangalore Port"),
    "tuticorin": (8.7600, 78.1300, True, "V.O. Chidambaranar Port"),
    "thoothukudi": (8.7600, 78.1300, True, "V.O. Chidambaranar Port"),
}

# Species keywords
SPECIES_KEYWORDS = [
    "mackerel", "tuna", "sardine", "shrimp", "hilsa", "pomfret",
    "seerfish", "anchovy", "squid", "cuttlefish", "ribbonfish",
]

# Vessel keywords
VESSEL_KEYWORDS = {
    "small boat": "small_boat",
    "traditional boat": "traditional_boat",
    "motorized craft": "motorized_boat",
    "trawler": "trawler",
    "cargo": "cargo",
    "tanker": "tanker",
    "patrol boat": "patrol_boat",
    "container": "container",
}


class OrchestratorPlanner:
    """
    Dynamic planner and natural language query understanding engine.
    Parses user inquiries, extracts entities and spatiotemporal context,
    classifies intent, and dynamically selects relevant domain agents.
    """

    def plan(self, query: OrchestrationQuery, now: Optional[datetime] = None) -> Tuple[QueryUnderstanding, List[AgentSelection]]:
        """
        Processes query payload and returns structured understanding + selected agents.
        """
        current_time = now or datetime.now(timezone.utc)
        understanding = self._understand_query(query=query, now=current_time)
        selected_agents = self._select_agents(understanding=understanding, query=query)
        return understanding, selected_agents

    def _understand_query(self, query: OrchestrationQuery, now: datetime) -> QueryUnderstanding:
        q_text = query.query.strip().lower()

        # 1. Coordinate extraction via Regex
        extracted_locations = self._extract_coordinates(q_text)

        # 2. Named location extraction
        named_locations = self._extract_named_locations(q_text)
        all_locations = extracted_locations + named_locations

        # If explicit coordinates passed in payload
        if query.latitude is not None and query.longitude is not None:
            explicit_orig = LocationContext(
                name="Explicit Origin",
                latitude=query.latitude,
                longitude=query.longitude,
                is_port=False,
            )
            # Prepend explicit origin
            all_locations = [explicit_orig] + [loc for loc in all_locations if loc.latitude != query.latitude or loc.longitude != query.longitude]

        dest_location: Optional[LocationContext] = None
        if query.destination_latitude is not None and query.destination_longitude is not None:
            dest_location = LocationContext(
                name="Explicit Destination",
                latitude=query.destination_latitude,
                longitude=query.destination_longitude,
                is_port=False,
            )

        # 3. Origin-to-Destination vs Multi-location Comparison vs Single Location
        is_comparison = False
        primary_location: Optional[LocationContext] = None
        comparison_locations: List[LocationContext] = []

        # Check for comparison patterns
        is_comp_text = bool(
            re.search(r"\b(which\s+is\s+better|compare|or|vs|versus|better\s+for\s+fishing)\b", q_text)
            and len(all_locations) >= 2
        )

        # Check for route patterns (e.g. from X to Y)
        route_match = re.search(r"\bfrom\s+([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\?|$|\s+at|\s+on|\s+via|\s+with)", q_text)

        if is_comp_text and not route_match:
            is_comparison = True
            comparison_locations = all_locations[:2]
            primary_location = comparison_locations[0]
        elif route_match and len(all_locations) >= 2:
            primary_location = all_locations[0]
            dest_location = all_locations[1]
        elif dest_location is not None and len(all_locations) >= 1:
            primary_location = all_locations[0]
        elif len(all_locations) >= 1:
            primary_location = all_locations[0]
            if len(all_locations) >= 2 and not is_comparison:
                dest_location = all_locations[1]
        elif query.latitude is not None and query.longitude is not None:
            primary_location = LocationContext(
                name=query.location_name or f"Coordinates ({query.latitude:.4f}, {query.longitude:.4f})",
                latitude=query.latitude,
                longitude=query.longitude,
                is_port=False,
            )
        else:
            # When completely unspecified and no coordinates provided, create an explicit location prompt context
            primary_location = None

        # 4. Temporal extraction (date & time)
        target_date, target_time = self._extract_temporal(q_text, query.target_datetime, now)

        # 5. Species extraction
        species = query.target_species
        if not species:
            for s in SPECIES_KEYWORDS:
                if re.search(rf"\b{s}\b", q_text):
                    species = s
                    break

        # 6. Vessel extraction
        vessel = query.vessel_type
        if not vessel:
            for v_name, v_code in VESSEL_KEYWORDS.items():
                if v_name in q_text:
                    vessel = v_code
                    break
        if not vessel:
            vessel = "small_boat" if "small boat" in q_text else "trawler" if "trawler" in q_text else "fishing_vessel"

        # 7. Operation Type extraction
        op_type = query.operation_type
        if not op_type:
            if "fishing" in q_text or "fish" in q_text:
                op_type = "FISHING_TRIP"
            elif "transit" in q_text or "travel" in q_text or "route" in q_text:
                op_type = "TRANSIT"
            elif "rescue" in q_text:
                op_type = "RESCUE_SUPPORT"
            else:
                op_type = "TRANSIT"

        # 8. Intent Classification
        intent = self._classify_intent(q_text=q_text, is_comparison=is_comparison, dest_location=dest_location)

        return QueryUnderstanding(
            intent=intent,
            primary_location=primary_location,
            destination_location=dest_location,
            comparison_locations=comparison_locations,
            target_date=target_date,
            target_time=target_time,
            target_species=species,
            vessel_type=vessel,
            operation_type=op_type,
            is_comparison=is_comparison,
        )

    def _extract_coordinates(self, text: str) -> List[LocationContext]:
        locations = []
        # Pattern: -?16.97, -?82.25 or lat 16.97 lon 82.25
        coord_pattern = r"(?:lat(?:itude)?\s*[:=]?\s*)?(-?\d{1,2}(?:\.\d+)?)\s*(?:,|and|\s+)\s*(?:lon(?:gitude)?\s*[:=]?\s*)?(-?\d{1,3}(?:\.\d+)?)"
        matches = re.findall(coord_pattern, text)
        for lat_s, lon_s in matches:
            try:
                lat = float(lat_s)
                lon = float(lon_s)
                if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                    locations.append(LocationContext(
                        name=f"Point ({lat:.4f}, {lon:.4f})",
                        latitude=lat,
                        longitude=lon,
                        is_port=False,
                    ))
            except Exception:
                pass
        return locations

    def _extract_named_locations(self, text: str) -> List[LocationContext]:
        found: List[LocationContext] = []
        seen_names = set()
        for loc_name, (lat, lon, is_port, port_name) in KNOWN_LOCATIONS.items():
            if re.search(rf"\b{loc_name}\b", text):
                clean_name = port_name.split()[0] if port_name else loc_name.capitalize()
                if clean_name not in seen_names:
                    seen_names.add(clean_name)
                    found.append(LocationContext(
                        name=port_name or loc_name.capitalize(),
                        latitude=lat,
                        longitude=lon,
                        is_port=is_port,
                        port_name=port_name,
                    ))
        return found

    def _extract_temporal(self, text: str, explicit_dt: Optional[str], now: datetime) -> Tuple[Optional[str], Optional[str]]:
        if explicit_dt:
            try:
                parsed = datetime.fromisoformat(explicit_dt.replace("Z", "+00:00"))
                return parsed.strftime("%Y-%m-%d"), parsed.strftime("%H:%M")
            except Exception:
                pass

        target_date: Optional[str] = None
        target_time: Optional[str] = None

        if "tomorrow" in text:
            target_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "today" in text or "now" in text:
            target_date = now.strftime("%Y-%m-%d")

        # Time of day extraction
        time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3).lower()
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            target_time = f"{hour:02d}:{minute:02d}"
        elif "morning" in text:
            target_time = "06:00"
        elif "afternoon" in text:
            target_time = "14:00"
        elif "evening" in text:
            target_time = "18:00"
        elif "night" in text:
            target_time = "21:00"

        return target_date, target_time

    def _classify_intent(self, q_text: str, is_comparison: bool, dest_location: Optional[LocationContext]) -> str:
        # 1. Fishing Comparison
        if is_comparison and any(k in q_text for k in ["fishing", "fish", "catch", "better", "compare"]):
            return "FISHING_COMPARISON"

        # 2. Fishing Assessment
        if any(k in q_text for k in ["fishing", "fish", "catch", "pfz", "angler", "species", "mackerel", "tuna", "sardine"]):
            return "FISHING_ASSESSMENT"

        # 3. Route Operation / Transit
        if (dest_location is not None or any(k in q_text for k in ["travel from", "transit from", "route", "voyage", "navigate from", "travel to", "distance between", "travel time"])):
            return "ROUTE_OPERATION"

        # 4. Earth Observation / Satellite
        if any(k in q_text for k in ["satellite", "chlorophyll", "remote sensing", "ocean colour", "optical", "cloud fraction", "sst front"]):
            return "EARTH_OBSERVATION"

        # 5. Marine Safety / Disaster
        if any(k in q_text for k in ["cyclone", "warning", "warnings", "alerts", "alert", "hazard", "storm", "tsunami", "emergency", "danger", "is it safe"]):
            return "MARINE_SAFETY"

        # 6. Marine Conditions / Sea State
        if any(k in q_text for k in ["wave", "waves", "sea state", "swell", "current", "currents", "tide", "water temperature", "marine condition"]):
            return "MARINE_CONDITIONS"

        # Fallback default
        return "FISHING_ASSESSMENT"

    def _select_agents(self, understanding: QueryUnderstanding, query: OrchestrationQuery) -> List[AgentSelection]:
        """
        Dynamically selects only the relevant domain agents based on classified intent.
        Avoids calling unnecessary agents.
        """
        intent = understanding.intent
        selections: List[AgentSelection] = []

        if intent in ("FISHING_ASSESSMENT", "FISHING_COMPARISON"):
            # Fishing queries require multi-layer evidence:
            # Disaster & Safety (override) -> Geo-Spatial -> Marine Conditions -> Earth Observation -> Fishing Intelligence
            selections = [
                AgentSelection(
                    agent_id="disaster_safety",
                    agent_name="Disaster & Safety Agent",
                    domain="Safety & Emergency",
                    selection_reason="Verify absence of severe weather alerts, cyclone tracks, or hazard zones before fishing clearance.",
                    priority=1,
                    execution_order=1,
                ),
                AgentSelection(
                    agent_id="geospatial_navigation",
                    agent_name="Geo-Spatial & Navigation Agent",
                    domain="Maritime Boundaries & Ports",
                    selection_reason="Check proximity to safe harbors and avoid military exclusion or protected core zones.",
                    priority=2,
                    execution_order=2,
                ),
                AgentSelection(
                    agent_id="marine_conditions",
                    agent_name="Marine Conditions Agent",
                    domain="Ocean Dynamics & Sea State",
                    selection_reason="Analyze wave height, swell period, currents, and SST suitable for fishing craft.",
                    priority=3,
                    execution_order=3,
                ),
                AgentSelection(
                    agent_id="earth_observation",
                    agent_name="Earth Observation Agent",
                    domain="Satellite Remote Sensing",
                    selection_reason="Evaluate chlorophyll-a biological density and optical cloud observability.",
                    priority=4,
                    execution_order=4,
                ),
                AgentSelection(
                    agent_id="fishing",
                    agent_name="Fishing Intelligence Agent",
                    domain="Fisheries Decision Support",
                    selection_reason="Synthesize species suitability, potential fishing zones, and operational clearance.",
                    priority=5,
                    execution_order=5,
                ),
            ]
            # If route or travel mentioned in fishing query, include marine operations
            if understanding.destination_location is not None:
                selections.append(
                    AgentSelection(
                        agent_id="marine_operations",
                        agent_name="Marine Operations Agent",
                        domain="Voyage & Fleet Operations",
                        selection_reason="Compute voyage distance and transit timing for fishing transit.",
                        priority=6,
                        execution_order=6,
                    )
                )

        elif intent == "ROUTE_OPERATION":
            # Route operations require:
            # Disaster & Safety -> Geo-Spatial -> Marine Conditions -> Marine Operations
            selections = [
                AgentSelection(
                    agent_id="disaster_safety",
                    agent_name="Disaster & Safety Agent",
                    domain="Safety & Emergency",
                    selection_reason="Verify active disaster warnings and storm surge hazard zones intersecting route.",
                    priority=1,
                    execution_order=1,
                ),
                AgentSelection(
                    agent_id="geospatial_navigation",
                    agent_name="Geo-Spatial & Navigation Agent",
                    domain="Maritime Boundaries & Ports",
                    selection_reason="Evaluate geodesic straight-line trajectory against military exclusion and protected zones.",
                    priority=2,
                    execution_order=2,
                ),
                AgentSelection(
                    agent_id="marine_conditions",
                    agent_name="Marine Conditions Agent",
                    domain="Ocean Dynamics & Sea State",
                    selection_reason="Check sea state, rough waves, and surface currents along transit corridor.",
                    priority=3,
                    execution_order=3,
                ),
                AgentSelection(
                    agent_id="marine_operations",
                    agent_name="Marine Operations Agent",
                    domain="Voyage & Fleet Operations",
                    selection_reason="Calculate transit duration, departure scheduling, and route clearance.",
                    priority=4,
                    execution_order=4,
                ),
            ]

        elif intent == "MARINE_SAFETY":
            # Safety queries require:
            # Disaster & Safety -> Geo-Spatial -> Marine Conditions
            selections = [
                AgentSelection(
                    agent_id="disaster_safety",
                    agent_name="Disaster & Safety Agent",
                    domain="Safety & Emergency",
                    selection_reason="Primary safety assessment: cyclone tracks, official marine warnings, and hazard polygons.",
                    priority=1,
                    execution_order=1,
                ),
                AgentSelection(
                    agent_id="geospatial_navigation",
                    agent_name="Geo-Spatial & Navigation Agent",
                    domain="Maritime Boundaries & Ports",
                    selection_reason="Identify nearest safe ports of refuge and maritime boundaries.",
                    priority=2,
                    execution_order=2,
                ),
                AgentSelection(
                    agent_id="marine_conditions",
                    agent_name="Marine Conditions Agent",
                    domain="Ocean Dynamics & Sea State",
                    selection_reason="Verify live sea state and swell wave conditions.",
                    priority=3,
                    execution_order=3,
                ),
            ]

        elif intent == "MARINE_CONDITIONS":
            # Marine conditions inquiry:
            # Marine Conditions -> Disaster & Safety
            selections = [
                AgentSelection(
                    agent_id="marine_conditions",
                    agent_name="Marine Conditions Agent",
                    domain="Ocean Dynamics & Sea State",
                    selection_reason="Evaluate significant wave height, swell wave profiles, and surface currents.",
                    priority=1,
                    execution_order=1,
                ),
                AgentSelection(
                    agent_id="disaster_safety",
                    agent_name="Disaster & Safety Agent",
                    domain="Safety & Emergency",
                    selection_reason="Check for high-wave advisories or active rough sea alerts.",
                    priority=2,
                    execution_order=2,
                ),
            ]

        elif intent == "EARTH_OBSERVATION":
            # Earth Observation inquiry:
            # Earth Observation -> Marine Conditions
            selections = [
                AgentSelection(
                    agent_id="earth_observation",
                    agent_name="Earth Observation Agent",
                    domain="Satellite Remote Sensing",
                    selection_reason="Retrieve satellite-derived chlorophyll-a, ocean colour classification, and cloud cover.",
                    priority=1,
                    execution_order=1,
                ),
                AgentSelection(
                    agent_id="marine_conditions",
                    agent_name="Marine Conditions Agent",
                    domain="Ocean Dynamics & Sea State",
                    selection_reason="Contextualize thermal upwelling and sea surface temperature telemetry.",
                    priority=2,
                    execution_order=2,
                ),
            ]

        # Sort selections by priority
        selections.sort(key=lambda s: s.priority)
        for idx, sel in enumerate(selections, start=1):
            sel.execution_order = idx

        return selections
