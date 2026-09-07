from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional

from agents.marine_operations.schemas import (
    MarineOperationsAssessmentResponse,
    OperationalEvidenceItem,
    RouteOperationalSummary,
)


class MarineOperationsReasoningEngine:
    """
    Deterministic reasoning engine for Marine Operations Intelligence Agent.
    Evaluates travel distance, transit durations, regulatory boundaries, hazard intersections,
    disaster alerts, cyclone proximity, and environmental constraints.
    """

    PROHIBITED_CLAIMS_PATTERN = re.compile(
        r"(100%\s*safe|guaranteed\s*safe|completely\s*safe|risk[-\s]*free|zero\s*risk|absolute\s*safety)",
        re.IGNORECASE,
    )

    def evaluate(
        self,
        collected_data: Dict[str, Any],
    ) -> MarineOperationsAssessmentResponse:
        """
        Synthesizes multi-factor operational evidence and returns structured assessment.
        """
        origin = collected_data["origin"]
        destination = collected_data["destination"]
        route: RouteOperationalSummary = collected_data["route"]
        nav_res: Dict[str, Any] = collected_data["nav_res"]
        intersecting_hazards: List[Any] = collected_data["intersecting_hazards"]
        active_alerts: List[Dict[str, Any]] = collected_data["active_alerts"]
        cyclones: List[Dict[str, Any]] = collected_data["cyclones"]
        safe_ports: List[Dict[str, Any]] = collected_data["safe_ports"]
        marine_cond = collected_data.get("marine_conditions")
        weather_cond = collected_data.get("weather_conditions")
        has_local_telemetry: bool = collected_data.get("has_local_telemetry", False)
        marine_freshness = str(collected_data.get("marine_freshness", "UNKNOWN"))
        weather_freshness = str(collected_data.get("weather_freshness", "UNKNOWN"))
        evidence: List[OperationalEvidenceItem] = collected_data.get("evidence", [])
        collected_at: datetime = collected_data.get("collected_at", datetime.now(timezone.utc))

        warnings: List[str] = []
        constraints: List[str] = []

        is_blocked = False
        is_warning = False
        is_caution = False

        # 1. Evaluate Restricted Zone Intersections (Deterministic BLOCKED)
        if nav_res["restricted_zone_intersection"] or nav_res["origin_in_restricted_zone"] or nav_res["destination_in_restricted_zone"]:
            is_blocked = True
            for r in nav_res["reasons"]:
                warnings.append(r)
                constraints.append(f"Regulatory Barrier: {r}")

        # 2. Evaluate Critical Official Alerts
        for alert in active_alerts:
            sev = alert.get("severity", "").upper()
            title = alert.get("title", "")
            source = alert.get("source", "INCOIS")
            if sev == "CRITICAL":
                is_blocked = True
                warnings.append(f"Operation blocked by active CRITICAL alert: {title} ({source}).")
                constraints.append(f"Severe Weather Alert: {title}")
            elif sev == "WARNING":
                is_warning = True
                warnings.append(f"Active WARNING along operational corridor: {title} ({source}).")
                constraints.append(f"Marine Alert: {title}")
            elif sev in ("CAUTION", "INFO"):
                is_caution = True
                warnings.append(f"Active CAUTION advisory in operational sector: {title} ({source}).")

        # 3. Evaluate Intersecting Hazard Zones
        for hz in intersecting_hazards:
            sev = hz.severity.upper() if hasattr(hz, "severity") else "WARNING"
            name = hz.name if hasattr(hz, "name") else "Hazard Zone"
            htype = hz.hazard_type if hasattr(hz, "hazard_type") else "HAZARD"
            if sev == "CRITICAL":
                is_blocked = True
                warnings.append(f"Route intersects CRITICAL hazard zone: '{name}' ({htype}).")
                constraints.append(f"Critical Inundation Hazard: {name}")
            elif sev == "WARNING":
                is_warning = True
                warnings.append(f"Route intersects WARNING hazard zone: '{name}' ({htype}).")
                constraints.append(f"Active Hazard Zone: {name}")
            else:
                is_caution = True
                warnings.append(f"Route traverses CAUTION hazard zone: '{name}' ({htype}).")

        # 4. Evaluate Protected Marine Sanctuaries
        if nav_res["protected_zone_intersection"] or nav_res["origin_in_protected_zone"] or nav_res["destination_in_protected_zone"]:
            if not is_blocked:
                is_caution = True
            for r in nav_res["reasons"]:
                if "protected" in r.lower() or "sanctuary" in r.lower():
                    warnings.append(r)
                    constraints.append(f"Protected Ecological Area: {r}")

        # 5. Evaluate Tropical Cyclones
        for cyc in cyclones:
            dist = cyc.get("distance_km", 999.0)
            c_name = cyc.get("name", "Unnamed")
            c_class = cyc.get("classification", "CYCLONIC_STORM")
            if dist is not None and dist <= 150.0:
                is_blocked = True
                warnings.append(f"Severe cyclone hazard: '{c_name}' ({c_class}) positioned {dist:.1f} km from route corridor.")
                constraints.append(f"Severe Cyclonic Storm: {c_name}")
            elif dist is not None and dist <= 300.0:
                is_warning = True
                warnings.append(f"Cyclone warning: '{c_name}' ({c_class}) within {dist:.1f} km of operational sector.")
                constraints.append(f"Tropical Cyclone: {c_name}")
            elif dist is not None and dist <= 500.0:
                is_caution = True
                warnings.append(f"Cyclone advisory: '{c_name}' positioned {dist:.1f} km from operational sector.")

        # 6. Evaluate Marine & Weather Thresholds
        if marine_cond:
            wave_h = marine_cond.get("wave_height_m")
            if wave_h is not None and wave_h >= 3.5:
                is_warning = True
                warnings.append(f"Adverse sea state: observed wave height of {wave_h}m exceeds safe cruising limits.")
                constraints.append(f"Rough Sea Limit: {wave_h}m waves")
            elif wave_h is not None and wave_h >= 2.5:
                is_caution = True
                warnings.append(f"Moderate sea state: observed wave height of {wave_h}m warrants caution.")

        if weather_cond:
            wind_spd = weather_cond.get("wind_speed_kmh")
            if wind_spd is not None and wind_spd >= 55.0:
                is_warning = True
                warnings.append(f"Adverse weather: sustained winds of {wind_spd} km/h exceed standard navigation limits.")
                constraints.append(f"High Wind Limit: {wind_spd} km/h")
            elif wind_spd is not None and wind_spd >= 40.0:
                is_caution = True
                warnings.append(f"Elevated wind conditions: sustained winds of {wind_spd} km/h detected.")

        # 7. Operational Status & Confidence Determination
        nearest_refuge = safe_ports[0].get("name") if safe_ports else None
        refuge_dist = safe_ports[0].get("distance_km") if safe_ports else None
        refuge_text = f" Harbor of safe refuge: {nearest_refuge} ({refuge_dist:.1f} km)." if nearest_refuge and refuge_dist else ""

        if is_blocked:
            operational_status = "BLOCKED"
            operational_risk = "CRITICAL"
            confidence = 0.98
            data_freshness = "FRESH"
            alt_text = f" Alternative route guidance: {route.alternative_route_suggestion}" if route.alternative_route_available else ""
            recommendation = (
                f"VOYAGE BLOCKED: Critical navigation or environmental barrier detected along proposed transit corridor.{refuge_text}{alt_text} "
                f"Immediate suspension of vessel movement advised."
            )
            explanation = (
                f"Planned transit between ({origin['latitude']:.4f}, {origin['longitude']:.4f}) and "
                f"({destination['latitude']:.4f}, {destination['longitude']:.4f}) is barred by critical spatial restrictions, "
                f"active severe alerts, or life-threatening storm hazards."
            )
        elif is_warning:
            operational_status = "WARNING"
            operational_risk = "HIGH"
            confidence = 0.95
            data_freshness = "FRESH"
            recommendation = (
                f"OPERATIONAL WARNING: High-severity marine advisory, elevated sea state, or nearby cyclonic activity detected along corridor.{refuge_text} "
                f"Vessels should delay departure until conditions moderate."
            )
            explanation = (
                f"Operation traverses sectors with active warnings or adverse weather thresholds (winds/waves/alerts). "
                f"Deterministic rule mandates a high risk classification."
            )
        elif is_caution:
            operational_status = "CAUTION"
            operational_risk = "MODERATE"
            confidence = 0.90
            data_freshness = marine_freshness if marine_cond else "AGING"
            alt_text = f" Suggested detour: {route.alternative_route_suggestion}" if route.alternative_route_available else ""
            recommendation = (
                f"OPERATIONAL CAUTION: Voyage intersects ecologically protected sectors or advisory conditions.{refuge_text}{alt_text} "
                f"Proceed with heightened vigilance and observe environmental speed restrictions."
            )
            explanation = (
                f"Operation is permissible under heightened caution. Route interacts with marine protected sanctuaries "
                f"or advisory conditions requiring continuous monitoring."
            )
        else:
            # Zero hazards found
            if not has_local_telemetry:
                operational_status = "INSUFFICIENT_DATA"
                operational_risk = "UNKNOWN"
                confidence = 0.0
                data_freshness = "UNAVAILABLE"
                warnings.append("Local marine and meteorological telemetry is absent or stale along this route.")
                recommendation = (
                    "INSUFFICIENT_DATA: Environmental telemetry coverage is missing or stale along this operational corridor. "
                    "Cannot verify safe navigational clearance. Exercise caution."
                )
                explanation = (
                    f"Route geometry ({route.distance_km:.1f} km) is clear of recorded regulatory zones, but live environmental telemetry "
                    f"is unavailable. In accordance with OCEANIS safety rules, operational status is set to INSUFFICIENT_DATA."
                )
            else:
                operational_status = "CLEAR"
                operational_risk = "LOW"
                confidence = 0.95
                data_freshness = marine_freshness if marine_cond else "FRESH"
                timing_str = f" Estimated transit: {route.estimated_duration_minutes:.0f} min ({route.estimated_duration_hours:.1f} hrs) at {route.speed_kmh:.0f} km/h." if route.estimated_duration_minutes else ""
                recommendation = (
                    f"CLEAR FOR TRANSIT: Route corridor ({route.distance_km:.1f} km) is clear of active hazards, exclusion zones, and severe weather.{timing_str}{refuge_text} "
                    f"Conditions currently indicate normal maritime operational parameters."
                )
                explanation = (
                    f"Planned transit between ({origin['latitude']:.4f}, {origin['longitude']:.4f}) and "
                    f"({destination['latitude']:.4f}, {destination['longitude']:.4f}) has confirmed fresh environmental telemetry "
                    f"with 0 restricted barriers, 0 active hazard zones, and 0 warnings along corridor."
                )

        # 8. Sanitize Recommendations to Prevent Misleading 100% Safe Guarantees
        recommendation = self._sanitize_safety_text(recommendation)
        explanation = self._sanitize_safety_text(explanation)

        # Ensure confidence strictly between 0.0 and 1.0
        confidence = max(0.0, min(1.0, float(confidence)))

        return MarineOperationsAssessmentResponse(
            agent="marine_operations",
            origin=origin,
            destination=destination,
            operational_status=operational_status,
            operational_risk=operational_risk,
            route=route,
            marine_conditions=marine_cond,
            weather_conditions=weather_cond,
            safe_ports=safe_ports,
            constraints=constraints,
            confidence=confidence,
            data_freshness=data_freshness,
            evidence=evidence,
            warnings=warnings,
            recommendation=recommendation,
            explanation=explanation,
            generated_at=collected_at,
        )

    def _sanitize_safety_text(self, text: str) -> str:
        """
        Guarantees that no prohibited absolute safety claims appear in generated narratives.
        """
        if not text:
            return text
        sanitized = self.PROHIBITED_CLAIMS_PATTERN.sub("normal operational parameters", text)
        return sanitized
