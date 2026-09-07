from datetime import datetime, timedelta, timezone
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from conversation.context import (
    ConversationContextManager,
    default_context_manager,
)
from conversation.language import LanguageDetector
from conversation.llm_client import BaseLLMClient, LLMClientFactory
from conversation.prompts import QUERY_PARSER_SYSTEM_PROMPT
from conversation.schemas import (
    ExtractedEntity,
    LocationEntity,
    ParsedQuery,
)
from orchestrator.schemas import LocationContext, OrchestrationQuery

logger = logging.getLogger("oceanis.conversation.parser")


class ConversationalQueryParser:
    """
    Multilingual semantic parser converting user messages into structured context
    for the OCEANIS Agent Orchestrator.
    Combines LLM intelligence with deterministic pattern recognition and session context.
    """

    # Verified coastal ports & navigation reference nodes
    KNOWN_PORTS = {
        "kakinada": {"name": "Kakinada Port", "latitude": 16.9890, "longitude": 82.2474, "is_port": True},
        "visakhapatnam": {"name": "Visakhapatnam Port", "latitude": 17.6868, "longitude": 83.2185, "is_port": True},
        "vizag": {"name": "Visakhapatnam Port", "latitude": 17.6868, "longitude": 83.2185, "is_port": True},
        "machilipatnam": {"name": "Machilipatnam Port", "latitude": 16.1875, "longitude": 81.1389, "is_port": True},
        "krishnapatnam": {"name": "Krishnapatnam Port", "latitude": 14.2500, "longitude": 80.1167, "is_port": True},
        "bhavanapadu": {"name": "Bhavanapadu Harbor", "latitude": 18.5667, "longitude": 84.3500, "is_port": True},
        "gangavaram": {"name": "Gangavaram Port", "latitude": 17.6200, "longitude": 83.2300, "is_port": True},
        "chennai": {"name": "Chennai Port", "latitude": 13.0827, "longitude": 80.2707, "is_port": True},
        "paradip": {"name": "Paradip Port", "latitude": 20.3167, "longitude": 86.6167, "is_port": True},
    }

    # Decimal coordinate patterns
    COORD_PATTERNS = [
        re.compile(r"lat\s*[:=]?\s*(-?\d+(\.\d+)?)\s*(?:,|and)?\s*lon\s*[:=]?\s*(-?\d+(\.\d+)?)", re.IGNORECASE),
        re.compile(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)"),
    ]

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        context_manager: Optional[ConversationContextManager] = None,
    ):
        self.llm_client = llm_client or LLMClientFactory.get_client()
        self.context_manager = context_manager or default_context_manager

    def parse(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        explicit_language: Optional[str] = None,
        explicit_mode: Optional[str] = None,
        explicit_location: Optional[Dict[str, Any]] = None,
        context_overrides: Optional[Dict[str, Any]] = None,
        now: Optional[datetime] = None,
    ) -> Tuple[ParsedQuery, OrchestrationQuery]:
        """
        Parses incoming message, resolves context from history, and builds an OrchestratorQuery.
        """
        now_utc = now or datetime.now(timezone.utc)

        # 1. Detect language and script mode
        detected_lang, detected_mode = LanguageDetector.detect_language(message)
        lang = explicit_language or detected_lang
        mode = explicit_mode or detected_mode

        # 2. Get or create conversation session
        session_context = self.context_manager.get_or_create_context(
            conversation_id=conversation_id,
            language=lang,
            input_mode=mode,
        )

        # 3. Fast deterministic extraction
        deterministic_parsed = self._deterministic_parse(
            message=message,
            lang=lang,
            mode=mode,
            explicit_location=explicit_location,
            now_utc=now_utc,
        )

        # 4. If LLM provider is active (non-deterministic fallback), optionally refine parsing
        final_parsed = deterministic_parsed
        if self.llm_client.provider_name != "deterministic_rule_engine":
            try:
                llm_parsed = self._llm_parse(message=message, lang=lang, mode=mode)
                if llm_parsed:
                    final_parsed = llm_parsed
            except Exception as e:
                logger.warning(f"LLM parsing failed, using deterministic parse: {e}")

        # 5. Resolve multi-turn context (inherit missing parameters for follow-ups)
        final_parsed = self.context_manager.resolve_follow_up_context(
            context=session_context,
            parsed_query=final_parsed,
        )

        # 6. Apply any explicit context overrides
        if context_overrides:
            for k, v in context_overrides.items():
                if hasattr(final_parsed, k) and v is not None:
                    setattr(final_parsed, k, v)

        # 7. Construct compatible OrchestrationQuery
        dest_lat = final_parsed.destination_location.latitude if final_parsed.destination_location else None
        dest_lon = final_parsed.destination_location.longitude if final_parsed.destination_location else None
        orig_lat = final_parsed.location.latitude if final_parsed.location else None
        orig_lon = final_parsed.location.longitude if final_parsed.location else None

        orch_query = OrchestrationQuery(
            query=final_parsed.orchestrator_query,
            latitude=orig_lat,
            longitude=orig_lon,
            destination_latitude=dest_lat,
            destination_longitude=dest_lon,
            target_datetime=final_parsed.datetime_context,
            vessel_type=final_parsed.vessel_type,
            operation_type=final_parsed.operation_type,
            target_species=final_parsed.target_species,
            language=final_parsed.language,
            context={"conversation_id": session_context.conversation_id},
        )

        return final_parsed, orch_query

    def _deterministic_parse(
        self,
        message: str,
        lang: str,
        mode: str,
        explicit_location: Optional[Dict[str, Any]],
        now_utc: datetime,
    ) -> ParsedQuery:
        """
        Pure rule-based semantic parser for zero-latency, deterministic execution.
        """
        norm_text = LanguageDetector.normalize_to_english_intent(message, lang, mode)
        lower_norm = norm_text.lower()
        lower_orig = message.lower()
        entities: List[ExtractedEntity] = []

        # Extract locations
        locations = self._extract_locations(message, norm_text)
        primary_loc: Optional[LocationEntity] = None
        dest_loc: Optional[LocationEntity] = None
        comp_locs: List[LocationEntity] = []

        if explicit_location and "latitude" in explicit_location and "longitude" in explicit_location:
            primary_loc = LocationEntity(
                name=explicit_location.get("name", "Current Location"),
                latitude=float(explicit_location["latitude"]),
                longitude=float(explicit_location["longitude"]),
                is_port=explicit_location.get("is_port", False),
            )
        elif locations:
            primary_loc = locations[0]
            if len(locations) > 1:
                dest_loc = locations[1]
                comp_locs = locations

        # Extract temporal parameters
        target_date, target_time, dt_iso = self._extract_time(message, norm_text, now_utc)

        # Classify Intent
        is_comp = False
        is_follow_up = False

        if "what if" in lower_orig or "how about" in lower_orig or "pothe" in lower_orig:
            is_follow_up = True

        if any(w in lower_norm for w in ["which is better", "compare", "versus", " vs ", "or vizag", "better for fishing"]):
            intent = "FISHING_COMPARISON"
            is_comp = True
            if len(locations) >= 2:
                comp_locs = locations
        elif any(w in lower_norm for w in ["travel from", "route", "travel to", "sail to", "reach", "transit"]):
            intent = "ROUTE_OPERATION"
        elif any(w in lower_norm for w in ["cyclone", "warning", "alert", "danger", "hazard", "threat", "storm"]):
            intent = "MARINE_SAFETY"
        elif any(w in lower_norm for w in ["sea state", "wave", "waves", "swell", "wind", "current", "tide"]):
            intent = "MARINE_CONDITIONS"
        elif any(w in lower_norm for w in ["chlorophyll", "satellite", "sst", "ocean color", "productivity"]):
            intent = "EARTH_OBSERVATION"
        elif any(w in lower_norm for w in ["fishing", "catch", "tuna", "mackerel", "chepalu", "machli", "veta"]):
            intent = "FISHING_ASSESSMENT"
        else:
            intent = "FISHING_ASSESSMENT" if "can i go" in lower_norm or "vellacha" in lower_orig else "GENERAL_INQUIRY"

        # Build clean English orchestrator query
        loc_name = primary_loc.name if primary_loc else ""
        time_str = f"at {target_time}" if target_time else ""
        date_str = f"on {target_date}" if target_date else "tomorrow"

        if intent == "FISHING_ASSESSMENT":
            orch_q = f"Can I go fishing {date_str} {time_str} from {loc_name}?".strip() if loc_name else norm_text
        elif intent == "FISHING_COMPARISON" and len(comp_locs) >= 2:
            orch_q = f"Which is better for fishing tomorrow morning, {comp_locs[0].name} or {comp_locs[1].name}?"
        elif intent == "ROUTE_OPERATION" and dest_loc:
            orch_q = f"Is it safe to travel from {primary_loc.name} to {dest_loc.name}?"
        elif intent == "MARINE_SAFETY":
            orch_q = f"Are there active cyclone warnings near {loc_name}?" if loc_name else norm_text
        elif intent == "MARINE_CONDITIONS":
            orch_q = f"What are the current sea state and wave conditions near {loc_name}?" if loc_name else norm_text
        elif intent == "EARTH_OBSERVATION":
            orch_q = f"What is the satellite chlorophyll condition near {loc_name}?" if loc_name else norm_text
        else:
            orch_q = norm_text

        return ParsedQuery(
            original_query=message,
            language=lang,
            input_mode=mode,
            intent=intent,
            location=primary_loc,
            destination_location=dest_loc,
            comparison_locations=comp_locs,
            datetime_context=dt_iso,
            target_date=target_date,
            target_time=target_time,
            target_species=None,
            vessel_type="small_boat" if intent.startswith("FISHING") else "FISHING_VESSEL",
            operation_type="FISHING" if intent.startswith("FISHING") else "TRANSIT",
            is_comparison=is_comp,
            is_follow_up=is_follow_up,
            entities=entities,
            user_context={},
            orchestrator_query=orch_q,
        )

    def _extract_locations(self, orig_text: str, norm_text: str) -> List[LocationEntity]:
        """
        Extracts recognized coastal ports and coordinates from query text.
        """
        locs: List[LocationEntity] = []
        combined_text = f"{orig_text} {norm_text}"

        # 1. Check coordinates
        for pat in self.COORD_PATTERNS:
            m = pat.search(combined_text)
            if m:
                try:
                    if len(m.groups()) >= 4:
                        lat_val = float(m.group(1))
                        lon_val = float(m.group(3))
                    else:
                        lat_val = float(m.group(1))
                        lon_val = float(m.group(2))
                    locs.append(
                        LocationEntity(
                            name=f"Lat {lat_val:.2f}, Lon {lon_val:.2f}",
                            latitude=lat_val,
                            longitude=lon_val,
                            is_port=False,
                        )
                    )
                except (ValueError, IndexError):
                    pass

        # 2. Check known port names
        for key, info in self.KNOWN_PORTS.items():
            if re.search(rf"\b{key}\b", combined_text, re.IGNORECASE):
                # Avoid duplicate ports
                if not any(l.name == info["name"] for l in locs):
                    locs.append(
                        LocationEntity(
                            name=info["name"],
                            latitude=info["latitude"],
                            longitude=info["longitude"],
                            is_port=True,
                            port_name=info["name"],
                        )
                    )

        return locs

    def _extract_time(self, orig_text: str, norm_text: str, now_utc: datetime) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extracts target date and time from temporal references.
        """
        combined = f"{orig_text} {norm_text}".lower()

        target_date: Optional[str] = None
        target_time: Optional[str] = None

        # Check date markers
        if any(w in combined for w in ["tomorrow", "repu", "kal"]):
            target_date = (now_utc + timedelta(days=1)).strftime("%Y-%m-%d")
        elif any(w in combined for w in ["today", "ivvala", "eroju", "aaj"]):
            target_date = now_utc.strftime("%Y-%m-%d")

        # Check time markers (e.g. 6 AM, 6:00, 9 AM, 6 ki)
        m_time = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", combined)
        if m_time:
            hour = int(m_time.group(1))
            minute = int(m_time.group(2)) if m_time.group(2) else 0
            meridiem = m_time.group(3)
            if meridiem and meridiem.lower() == "pm" and hour < 12:
                hour += 12
            elif meridiem and meridiem.lower() == "am" and hour == 12:
                hour = 0
            target_time = f"{hour:02d}:{minute:02d}"

        dt_iso = None
        if target_date or target_time:
            d_str = target_date or now_utc.strftime("%Y-%m-%d")
            t_str = target_time or "06:00"
            dt_iso = f"{d_str}T{t_str}:00Z"

        return target_date, target_time, dt_iso

    def _llm_parse(self, message: str, lang: str, mode: str) -> Optional[ParsedQuery]:
        """
        Optional LLM-based structured parser for complex or ambiguous natural-language utterances.
        """
        prompt = f"Parse the following maritime query (Language: {lang}, Mode: {mode}):\n\n\"{message}\""
        raw_json = self.llm_client.generate_text(
            prompt=prompt,
            system_prompt=QUERY_PARSER_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.0,
        )
        data = json.loads(raw_json)
        if "intent" in data:
            loc_data = data.get("location")
            loc_entity = LocationEntity(**loc_data) if loc_data else None
            return ParsedQuery(
                original_query=message,
                language=data.get("language", lang),
                input_mode=data.get("input_mode", mode),
                intent=data.get("intent", "FISHING_ASSESSMENT"),
                location=loc_entity,
                destination_location=LocationEntity(**data["destination_location"]) if data.get("destination_location") else None,
                comparison_locations=[LocationEntity(**l) for l in data.get("comparison_locations", [])],
                target_date=data.get("target_date"),
                target_time=data.get("target_time"),
                target_species=data.get("target_species"),
                vessel_type=data.get("vessel_type", "small_boat"),
                is_comparison=data.get("is_comparison", False),
                is_follow_up=data.get("is_follow_up", False),
                entities=[],
                user_context={},
                orchestrator_query=data.get("orchestrator_query", message),
            )
        return None
