from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional

from agents.disaster_safety.schemas import (
    AlertSummary,
    CycloneSummary,
    DisasterSafetyAssessmentResponse,
    HazardSummary,
    SafePortSummary,
    SafetyEvidenceItem,
)


class DisasterSafetyReasoningEngine:
    """
    Deterministic safety reasoning engine for Disaster & Safety Intelligence Agent.
    Strictly prioritizes safety-critical overrides and prevents optimistic override
    of hazards, active alerts, and cyclones.
    """

    PROHIBITED_CLAIMS_PATTERN = re.compile(
        r"(100%\s*safe|guaranteed\s*safe|completely\s*safe|risk[-\s]*free|zero\s*risk|absolute\s*safety)",
        re.IGNORECASE,
    )

    def evaluate(
        self,
        collected_data: Dict[str, Any],
    ) -> DisasterSafetyAssessmentResponse:
        """
        Executes deterministic multi-factor disaster and safety assessment.
        """
        origin = collected_data["origin"]
        latitude = origin["latitude"]
        longitude = origin["longitude"]
        radius_km = collected_data.get("radius_km", 50.0)
        alerts: List[AlertSummary] = collected_data.get("alerts", [])
        hazards: List[HazardSummary] = collected_data.get("hazards", [])
        cyclones: List[CycloneSummary] = collected_data.get("cyclones", [])
        nearest_port: Optional[SafePortSummary] = collected_data.get("nearest_safe_port")
        has_local_telemetry: bool = collected_data.get("has_local_telemetry", False)
        telemetry_freshness = str(collected_data.get("telemetry_freshness", "UNKNOWN"))
        evidence: List[SafetyEvidenceItem] = collected_data.get("evidence", [])
        collected_at: datetime = collected_data.get("collected_at", datetime.now(timezone.utc))

        warnings: List[str] = []
        distance_to_hazards: List[Dict[str, Any]] = []

        # Flags for deterministic tiering
        has_critical = False
        has_warning = False
        has_caution = False

        # 1. Evaluate Active Official Alerts
        for alert in alerts:
            sev = alert.severity.upper()
            title = alert.title
            dist = alert.distance_km
            dist_str = f" ({dist:.1f} km away)" if dist is not None else ""

            if sev == "CRITICAL":
                has_critical = True
                warnings.append(f"CRITICAL official alert active: {title}{dist_str} issued by {alert.source}.")
            elif sev == "WARNING":
                has_warning = True
                warnings.append(f"WARNING official alert active: {title}{dist_str} issued by {alert.source}.")
            elif sev in ("CAUTION", "INFO"):
                has_caution = True
                warnings.append(f"CAUTION advisory active: {title}{dist_str} issued by {alert.source}.")

            if dist is not None:
                distance_to_hazards.append({
                    "entity_type": "ALERT",
                    "name": alert.title,
                    "distance_km": dist,
                    "severity": sev,
                })

        # 2. Evaluate Spatial Hazard Zones
        for hz in hazards:
            sev = hz.severity.upper()
            name = hz.name
            contains = hz.contains_point
            dist = hz.distance_km if hz.distance_km is not None else 0.0

            if contains:
                if sev == "CRITICAL":
                    has_critical = True
                    warnings.append(f"Location is DIRECTLY INSIDE critical hazard zone: '{name}' ({hz.hazard_type}).")
                elif sev == "WARNING":
                    has_warning = True
                    warnings.append(f"Location is DIRECTLY INSIDE hazard zone: '{name}' ({hz.hazard_type}).")
                else:
                    has_caution = True
                    warnings.append(f"Location is inside caution zone: '{name}' ({hz.hazard_type}).")
            else:
                if (sev in ("CRITICAL", "WARNING")) and dist <= 25.0:
                    has_caution = True
                    warnings.append(f"Proximity to high-hazard boundary '{name}' ({dist:.1f} km away).")

            distance_to_hazards.append({
                "entity_type": "HAZARD_ZONE",
                "name": hz.name,
                "distance_km": 0.0 if contains else dist,
                "contains_point": contains,
                "severity": sev,
            })

        # 3. Evaluate Cyclones
        for cyc in cyclones:
            dist = cyc.distance_km
            c_name = cyc.name
            c_class = cyc.classification
            wind = cyc.wind_speed_kmh
            wind_str = f" with {wind:.0f} km/h sustained winds" if wind else ""

            if dist is not None and dist <= 150.0:
                has_critical = True
                warnings.append(f"Extreme danger: Active tropical system '{c_name}' ({c_class}{wind_str}) is within {dist:.1f} km.")
            elif dist is not None and dist <= 300.0:
                has_warning = True
                warnings.append(f"Severe warning: Cyclone track point '{c_name}' ({c_class}{wind_str}) is within {dist:.1f} km.")
            elif dist is not None and dist <= 500.0:
                has_caution = True
                warnings.append(f"Monitoring advisory: Cyclonic activity '{c_name}' located {dist:.1f} km from position.")

            if dist is not None:
                distance_to_hazards.append({
                    "entity_type": "CYCLONE",
                    "name": cyc.name,
                    "distance_km": dist,
                    "severity": "CRITICAL" if dist <= 150.0 else ("WARNING" if dist <= 300.0 else "CAUTION"),
                })

        # Sort distance to hazards by distance
        distance_to_hazards.sort(key=lambda x: x.get("distance_km", 99999.0))

        # 4. Deterministic State Resolution & Safety Overrides
        if has_critical:
            safety_status = "BLOCKED"
            risk_level = "EXTREME"
            confidence = 0.98
            data_freshness = "FRESH"
            port_info = f" Seek emergency harbor at {nearest_port.name} ({nearest_port.distance_km:.1f} km away)." if nearest_port and nearest_port.distance_km else ""
            recommendation = (
                f"NAVIGATION BLOCKED: Critical marine hazard or severe storm system detected within active operational sector.{port_info} "
                f"All maritime voyages should be suspended immediately."
            )
            explanation = (
                f"Location ({latitude:.4f}, {longitude:.4f}) is subject to critical emergency conditions. "
                f"Severe hazard alerts or cyclone proximity mandate a deterministic BLOCKED state."
            )
        elif has_warning:
            safety_status = "WARNING"
            risk_level = "HIGH"
            confidence = 0.95
            data_freshness = "FRESH"
            port_info = f" Nearest safe refuge is {nearest_port.name} ({nearest_port.distance_km:.1f} km)." if nearest_port and nearest_port.distance_km else ""
            recommendation = (
                f"WARNING: High-severity marine advisory or nearby cyclonic activity in effect.{port_info} "
                f"Vessels should delay departure and monitor official safety bulletins."
            )
            explanation = (
                f"Location ({latitude:.4f}, {longitude:.4f}) is affected by active warnings or hazard zones. "
                f"Deterministic rule assigns high risk level."
            )
        elif has_caution:
            safety_status = "CAUTION"
            risk_level = "MODERATE"
            confidence = 0.90
            data_freshness = telemetry_freshness if has_local_telemetry else "AGING"
            port_info = f" Nearest harbor is {nearest_port.name} ({nearest_port.distance_km:.1f} km)." if nearest_port and nearest_port.distance_km else ""
            recommendation = (
                f"CAUTION: Proximity to hazard zones or advisory conditions detected.{port_info} "
                f"Exercise heightened vigilance and verify on-board safety gear."
            )
            explanation = (
                f"Location ({latitude:.4f}, {longitude:.4f}) exhibits moderate hazard proximity or caution-level advisories. "
                f"Deterministic rule assigns caution state."
            )
        else:
            # Zero active hazards/alerts/cyclones found
            if not has_local_telemetry:
                safety_status = "INSUFFICIENT_DATA"
                risk_level = "UNKNOWN"
                confidence = 0.0
                data_freshness = "UNAVAILABLE"
                warnings.append("No active emergency alerts recorded, but local oceanic telemetry coverage is missing or stale.")
                recommendation = (
                    "INSUFFICIENT_DATA: Environmental telemetry coverage is absent or stale in this oceanic sector. "
                    "Cannot verify safe navigation conditions. Exercise extreme caution."
                )
                explanation = (
                    f"Location ({latitude:.4f}, {longitude:.4f}) has no active official warnings, but telemetry is unavailable. "
                    f"In accordance with OCEANIS safety rules, status is set to INSUFFICIENT_DATA."
                )
            else:
                safety_status = "CLEAR"
                risk_level = "LOW"
                confidence = 0.95
                data_freshness = telemetry_freshness
                port_info = f" Nearest port of refuge is {nearest_port.name} ({nearest_port.distance_km:.1f} km)." if nearest_port and nearest_port.distance_km else ""
                recommendation = (
                    f"CLEAR: No active marine warnings, hazard zones, or cyclonic systems within {radius_km:.0f} km.{port_info} "
                    f"Conditions currently indicate normal maritime operational parameters within monitored areas."
                )
                explanation = (
                    f"Location ({latitude:.4f}, {longitude:.4f}) has confirmed fresh telemetry coverage with 0 active alerts, "
                    f"0 hazard zones, and 0 cyclones within search radius."
                )

        # 5. Sanitize Recommendations to Strictly Prevent Misleading 100% Safe Guarantees
        recommendation = self._sanitize_safety_text(recommendation)
        explanation = self._sanitize_safety_text(explanation)

        # Ensure confidence is strictly between 0.0 and 1.0
        confidence = max(0.0, min(1.0, float(confidence)))

        return DisasterSafetyAssessmentResponse(
            agent="disaster_safety",
            location={"latitude": latitude, "longitude": longitude},
            safety_status=safety_status,
            risk_level=risk_level,
            hazards=hazards,
            alerts=alerts,
            cyclones=cyclones,
            nearest_safe_port=nearest_port,
            distance_to_hazards=distance_to_hazards,
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
