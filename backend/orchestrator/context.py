from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.models import AgentQueryRequest, ExtractedEntities, LocationEntity


# Standard reference coordinates for prominent Indian coastal ports and marine centers
COASTAL_LOCATIONS: Dict[str, Tuple[float, float, str]] = {
    "kakinada": (16.9890, 82.2474, "Kakinada Port"),
    "visakhapatnam": (17.6868, 83.2185, "Visakhapatnam Port"),
    "vizag": (17.6868, 83.2185, "Visakhapatnam Port"),
    "chennai": (13.0827, 80.2707, "Chennai Port"),
    "madras": (13.0827, 80.2707, "Chennai Port"),
    "paradip": (20.3165, 86.6114, "Paradip Port"),
    "mangalore": (12.9141, 74.8560, "New Mangalore Port"),
    "kochi": (9.9312, 76.2673, "Cochin Port"),
    "cochin": (9.9312, 76.2673, "Cochin Port"),
    "mumbai": (18.9400, 72.8353, "Mumbai Port"),
    "bombay": (18.9400, 72.8353, "Mumbai Port"),
    "goa": (15.4050, 73.8000, "Mormugao Port"),
    "mormugao": (15.4050, 73.8000, "Mormugao Port"),
    "machilipatnam": (16.1800, 81.1300, "Machilipatnam Coastal Sector"),
    "tuticorin": (8.7642, 78.1348, "V.O. Chidambaranar Port"),
    "thoothukudi": (8.7642, 78.1348, "V.O. Chidambaranar Port"),
    "gopalpur": (19.2600, 84.9100, "Gopalpur Port"),
    "port blair": (11.6234, 92.7265, "Port Blair Harbor"),
}

SPECIES_KEYWORDS: List[str] = [
    "mackerel", "tuna", "sardine", "seerfish", "hilsa", "anchovy", "pomfret",
    "shrimp", "prawn", "squid", "cobia", "barracuda", "snapper", "ribbonfish",
]

VESSEL_KEYWORDS: Dict[str, str] = {
    "small boat": "small_boat",
    "small_boat": "small_boat",
    "country craft": "traditional_craft",
    "traditional craft": "traditional_craft",
    "motorized boat": "motorized_boat",
    "motorised boat": "motorized_boat",
    "trawler": "trawler",
    "fishing trawler": "trawler",
    "cargo": "cargo_vessel",
    "container": "container_ship",
    "ferry": "passenger_ferry",
    "yacht": "motorized_boat",
}


class ContextParser:
    """
    Deterministic Natural Language Understanding (NLU) & Entity Extractor for OCEANIS.
    Extracts geographic locations, routes, temporal parameters, activities, and species.
    """

    @classmethod
    def parse_query(
        cls,
        request: AgentQueryRequest,
        now: Optional[datetime] = None,
    ) -> ExtractedEntities:
        current_time = now or datetime.now(timezone.utc)
        query_text = request.query.lower()

        # 1. Location Recognition
        locations: List[LocationEntity] = []

        # Check explicit payload coordinates first
        if request.latitude is not None and request.longitude is not None:
            locations.append(LocationEntity(
                name="Provided Coordinates",
                latitude=request.latitude,
                longitude=request.longitude,
                is_port=False,
            ))

        if request.destination_latitude is not None and request.destination_longitude is not None:
            locations.append(LocationEntity(
                name="Provided Destination",
                latitude=request.destination_latitude,
                longitude=request.destination_longitude,
                is_port=False,
            ))

        # Check coordinate regex in query string: e.g. "16.97, 82.25" or "16.97 82.25"
        coord_matches = re.findall(r"(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,3}\.\d+)", query_text)
        for lat_str, lon_str in coord_matches:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                    if not any(abs(l.latitude - lat) < 0.001 and abs(l.longitude - lon) < 0.001 for l in locations):
                        locations.append(LocationEntity(
                            name=f"Point ({lat}, {lon})",
                            latitude=lat,
                            longitude=lon,
                            is_port=False,
                        ))
            except ValueError:
                pass

        # Check named coastal locations & ports
        for loc_key, (lat, lon, port_name) in COASTAL_LOCATIONS.items():
            if re.search(rf"\b{re.escape(loc_key)}\b", query_text):
                if not any(l.port_name == port_name for l in locations):
                    locations.append(LocationEntity(
                        name=port_name,
                        latitude=lat,
                        longitude=lon,
                        is_port=True,
                        port_name=port_name,
                    ))

        # Assign origin and destination if route or comparison
        origin_loc: Optional[LocationEntity] = None
        dest_loc: Optional[LocationEntity] = None

        # Check "from <loc1> to <loc2>" pattern
        route_match = re.search(r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:$|[,\.\?!]|\bat\b|\bon\b)", query_text)
        if route_match:
            from_text = route_match.group(1).strip()
            to_text = route_match.group(2).strip()

            for k, (lat, lon, p_name) in COASTAL_LOCATIONS.items():
                if k in from_text:
                    origin_loc = LocationEntity(name=p_name, latitude=lat, longitude=lon, is_port=True, port_name=p_name)
                if k in to_text:
                    dest_loc = LocationEntity(name=p_name, latitude=lat, longitude=lon, is_port=True, port_name=p_name)

        # Check "between <loc1> and <loc2>" pattern
        between_match = re.search(r"between\s+([a-zA-Z\s]+?)\s+and\s+([a-zA-Z\s]+?)(?:$|[,\.\?!]|\bat\b|\bon\b)", query_text)
        if between_match:
            loc1_text = between_match.group(1).strip()
            loc2_text = between_match.group(2).strip()

            for k, (lat, lon, p_name) in COASTAL_LOCATIONS.items():
                if k in loc1_text and not origin_loc:
                    origin_loc = LocationEntity(name=p_name, latitude=lat, longitude=lon, is_port=True, port_name=p_name)
                if k in loc2_text and not dest_loc:
                    dest_loc = LocationEntity(name=p_name, latitude=lat, longitude=lon, is_port=True, port_name=p_name)

        if not origin_loc and len(locations) >= 1:
            origin_loc = locations[0]
        if not dest_loc and len(locations) >= 2:
            dest_loc = locations[1]

        # 2. Temporal Understanding
        target_date: Optional[str] = None
        target_time: Optional[str] = None
        duration_hours: Optional[float] = None

        if "tomorrow" in query_text:
            tomorrow = current_time + timedelta(days=1)
            target_date = tomorrow.strftime("%Y-%m-%d")
        elif "today" in query_text:
            target_date = current_time.strftime("%Y-%m-%d")
        else:
            date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", query_text)
            if date_match:
                target_date = date_match.group(1)

        # Check explicit target_datetime payload
        if request.target_datetime:
            try:
                dt = datetime.fromisoformat(request.target_datetime.replace("Z", "+00:00"))
                target_date = dt.strftime("%Y-%m-%d")
                target_time = dt.strftime("%H:%M")
            except ValueError:
                target_date = target_date or request.target_datetime

        # Time of day extraction: e.g. "at 6 AM", "6:00", "06:00", "morning"
        time_match = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", query_text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3)
            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            target_time = f"{hour:02d}:{minute:02d}"
        elif "morning" in query_text and not target_time:
            target_time = "06:00"
        elif "afternoon" in query_text and not target_time:
            target_time = "14:00"
        elif "evening" in query_text and not target_time:
            target_time = "18:00"

        # Duration extraction: e.g. "for 6 hours", "4 hours trip"
        dur_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs)", query_text)
        if dur_match:
            try:
                duration_hours = float(dur_match.group(1))
            except ValueError:
                pass

        # 3. Activity and Target Species
        activity_type = "GENERAL_INQUIRY"
        if any(w in query_text for w in ["fishing", "fish", "catch", "angler", "trawler", "pfz"]):
            activity_type = "FISHING"
        elif any(w in query_text for w in ["travel", "voyage", "navigate", "route", "distance", "transit", "reach"]):
            activity_type = "NAVIGATION_OPERATION"
        elif any(w in query_text for w in ["cyclone", "storm", "warning", "tsunami", "safe to", "safety", "hazard", "alert"]):
            activity_type = "SAFETY_ASSESSMENT"
        elif any(w in query_text for w in ["wave", "swell", "sea state", "current", "sst", "temperature"]):
            activity_type = "ENVIRONMENTAL_MONITORING"
        elif any(w in query_text for w in ["satellite", "chlorophyll", "cloud cover", "remote sensing"]):
            activity_type = "EARTH_OBSERVATION"

        # Species extraction
        target_species = request.target_species
        if not target_species:
            for sp in SPECIES_KEYWORDS:
                if re.search(rf"\b{sp}\b", query_text):
                    target_species = sp
                    break

        # Vessel type extraction
        vessel_type = request.vessel_type
        if not vessel_type:
            for v_key, v_code in VESSEL_KEYWORDS.items():
                if v_key in query_text:
                    vessel_type = v_code
                    break
            if not vessel_type and activity_type == "FISHING":
                vessel_type = "small_boat"

        # Comparison mode detection
        comparison_mode = bool(
            re.search(r"\b(which|better|compare|comparison|versus|vs)\b", query_text)
            and len(locations) >= 2
        )

        return ExtractedEntities(
            locations=locations,
            origin_location=origin_loc,
            destination_location=dest_loc,
            target_date=target_date,
            target_time=target_time,
            duration_hours=duration_hours,
            activity_type=activity_type,
            target_species=target_species,
            vessel_type=vessel_type,
            comparison_mode=comparison_mode,
        )
