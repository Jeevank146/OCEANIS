from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from agents.fishing.schemas import (
    ConfidenceAssessment,
    EvidenceItem,
    FishingAssessment,
    FishingQuery,
    FishingSuitability,
    FishingSuitabilityFactor,
    LocationComparisonResponse,
    PFZAssessment,
    WhatIfResponse,
)
from services.freshness import FreshnessCategory


@dataclass(frozen=True)
class FishingThresholds:
    """
    Configurable deterministic oceanographic and meteorological thresholds
    for fishing operations. Kept strictly separated from orchestration code.
    """
    # Wave / Sea State thresholds (meters)
    WAVE_FAVORABLE_MAX_M: float = 1.2
    WAVE_CAUTION_MAX_M: float = 2.2
    WAVE_UNFAVORABLE_MAX_M: float = 3.2

    # Surface Wind thresholds (km/h)
    WIND_FAVORABLE_MAX_KMH: float = 25.0
    WIND_CAUTION_MAX_KMH: float = 40.0
    WIND_UNFAVORABLE_MAX_KMH: float = 55.0

    # Sea Surface Temperature (°C) preferred ranges for tropical pelagic fisheries
    SST_OPTIMAL_MIN_C: float = 26.0
    SST_OPTIMAL_MAX_C: float = 29.5
    SST_ACCEPTABLE_MIN_C: float = 24.0
    SST_ACCEPTABLE_MAX_C: float = 31.0

    # Bio-productivity / Chlorophyll-a (mg/m³)
    CHLOROPHYLL_FAVORABLE_MIN_MG_M3: float = 0.30

    # Ocean current velocity (km/h)
    CURRENT_FAVORABLE_MAX_KMH: float = 3.5

    # Precipitation threshold (mm)
    PRECIPITATION_HEAVY_MM: float = 15.0


class FishingReasoningEngine:
    """
    Deterministic reasoning, multi-domain evidence fusion, and safety override engine
    for the OCEANIS Fishing Intelligence domain.
    """

    def __init__(self, thresholds: Optional[FishingThresholds] = None):
        self.thresholds = thresholds or FishingThresholds()

    def fuse_evidence(
        self,
        weather: Optional[Dict[str, Any]],
        marine: Optional[Dict[str, Any]],
        eo: Optional[Dict[str, Any]],
        safety: Dict[str, Any],
        geospatial: Dict[str, Any],
        operations: Optional[Dict[str, Any]],
    ) -> List[EvidenceItem]:
        """
        Synthesizes structured, traceable evidence items from all domain sources.
        """
        evidence: List[EvidenceItem] = []

        # 1. Marine Conditions Telemetry Evidence
        if marine:
            wave_h = marine.get("wave_height_m")
            if wave_h is not None:
                wave_assess = (
                    "FAVORABLE"
                    if wave_h < self.thresholds.WAVE_FAVORABLE_MAX_M
                    else ("NEUTRAL" if wave_h <= self.thresholds.WAVE_CAUTION_MAX_M else "UNFAVORABLE")
                )
                evidence.append(EvidenceItem(
                    factor="significant_wave_height",
                    value=wave_h,
                    unit="m",
                    source=marine.get("source", "Open-Meteo Marine"),
                    data_type=marine.get("data_type", "OBSERVATION"),
                    observed_at=marine.get("observed_at"),
                    freshness=marine.get("freshness", FreshnessCategory.UNKNOWN),
                    assessment=wave_assess,
                    notes=f"Wave height of {wave_h}m is {wave_assess.lower()} for coastal fishing operations.",
                ))

            sst = marine.get("sea_surface_temperature_c")
            if sst is not None:
                sst_assess = (
                    "FAVORABLE"
                    if self.thresholds.SST_OPTIMAL_MIN_C <= sst <= self.thresholds.SST_OPTIMAL_MAX_C
                    else ("NEUTRAL" if self.thresholds.SST_ACCEPTABLE_MIN_C <= sst <= self.thresholds.SST_ACCEPTABLE_MAX_C else "UNFAVORABLE")
                )
                evidence.append(EvidenceItem(
                    factor="sea_surface_temperature",
                    value=sst,
                    unit="°C",
                    source=marine.get("source", "Open-Meteo Marine"),
                    data_type=marine.get("data_type", "OBSERVATION"),
                    observed_at=marine.get("observed_at"),
                    freshness=marine.get("freshness", FreshnessCategory.UNKNOWN),
                    assessment=sst_assess,
                    notes=f"Sea surface temperature at {sst}°C provides typical tropical pelagic habitat conditions.",
                ))

            current_v = marine.get("ocean_current_velocity_kmh")
            if current_v is not None:
                evidence.append(EvidenceItem(
                    factor="ocean_current_velocity",
                    value=current_v,
                    unit="km/h",
                    source=marine.get("source", "Marine Model"),
                    data_type=marine.get("data_type", "OBSERVATION"),
                    observed_at=marine.get("observed_at"),
                    freshness=marine.get("freshness", FreshnessCategory.UNKNOWN),
                    assessment="FAVORABLE" if current_v < self.thresholds.CURRENT_FAVORABLE_MAX_KMH else "NEUTRAL",
                    notes=f"Current velocity {current_v} km/h.",
                ))

        # 2. Weather Telemetry Evidence
        if weather:
            wind_spd = weather.get("wind_speed_kmh")
            if wind_spd is not None:
                wind_assess = (
                    "FAVORABLE"
                    if wind_spd < self.thresholds.WIND_FAVORABLE_MAX_KMH
                    else ("NEUTRAL" if wind_spd <= self.thresholds.WIND_CAUTION_MAX_KMH else "UNFAVORABLE")
                )
                evidence.append(EvidenceItem(
                    factor="wind_speed",
                    value=wind_spd,
                    unit="km/h",
                    source=weather.get("source", "Open-Meteo"),
                    data_type="OBSERVATION",
                    observed_at=weather.get("observed_at"),
                    freshness=weather.get("freshness", FreshnessCategory.UNKNOWN),
                    assessment=wind_assess,
                    notes=f"Surface wind speed of {wind_spd} km/h is {wind_assess.lower()} for vessel handling.",
                ))

            temp = weather.get("temperature_c")
            if temp is not None:
                evidence.append(EvidenceItem(
                    factor="air_temperature",
                    value=temp,
                    unit="°C",
                    source=weather.get("source", "Open-Meteo"),
                    data_type="OBSERVATION",
                    observed_at=weather.get("observed_at"),
                    freshness=weather.get("freshness", FreshnessCategory.UNKNOWN),
                    assessment="FAVORABLE",
                    notes=f"Ambient air temperature {temp}°C.",
                ))

            precip = weather.get("precipitation_mm")
            if precip is not None and precip > 5.0:
                evidence.append(EvidenceItem(
                    factor="precipitation",
                    value=precip,
                    unit="mm",
                    source=weather.get("source", "Open-Meteo"),
                    data_type="OBSERVATION",
                    observed_at=weather.get("observed_at"),
                    freshness=weather.get("freshness", FreshnessCategory.UNKNOWN),
                    assessment="UNFAVORABLE" if precip > self.thresholds.PRECIPITATION_HEAVY_MM else "NEUTRAL",
                    notes=f"Active rainfall of {precip} mm may reduce visibility at sea.",
                ))

        # 3. Earth Observation Satellite Evidence
        if eo:
            chlor = eo.get("chlorophyll_a_mg_m3")
            if chlor is not None:
                chlor_assess = "FAVORABLE" if chlor >= self.thresholds.CHLOROPHYLL_FAVORABLE_MIN_MG_M3 else "NEUTRAL"
                evidence.append(EvidenceItem(
                    factor="chlorophyll_a_concentration",
                    value=chlor,
                    unit="mg/m³",
                    source=eo.get("source", "Copernicus/Sentinel"),
                    data_type="OBSERVATION",
                    observed_at=eo.get("observed_at"),
                    freshness=eo.get("freshness", FreshnessCategory.UNKNOWN),
                    assessment=chlor_assess,
                    notes=f"Chlorophyll-a density of {chlor} mg/m³ indicates biological productivity concentration.",
                ))

            clouds = eo.get("cloud_cover_percent")
            if clouds is not None:
                evidence.append(EvidenceItem(
                    factor="cloud_cover",
                    value=clouds,
                    unit="%",
                    source=eo.get("source", "Copernicus/Sentinel"),
                    data_type="OBSERVATION",
                    observed_at=eo.get("observed_at"),
                    freshness=eo.get("freshness", FreshnessCategory.UNKNOWN),
                    assessment="NEUTRAL",
                    notes=f"Cloud coverage at {clouds}%.",
                ))

        # 4. Disaster & Safety Evidence
        alerts = safety.get("active_alerts", [])
        hazards = safety.get("nearby_hazards", [])
        cyclones = safety.get("nearby_cyclones", [])

        if alerts:
            for a in alerts:
                sev = a.get("severity", "WARNING").upper()
                evidence.append(EvidenceItem(
                    factor="marine_disaster_alert",
                    value=a.get("title"),
                    unit=None,
                    source=a.get("source", "Official Advisory"),
                    data_type=a.get("source_category", "OFFICIAL"),
                    observed_at=str(a.get("issued_at")),
                    freshness=a.get("freshness", FreshnessCategory.FRESH),
                    assessment="CRITICAL_HAZARD" if sev == "CRITICAL" else "UNFAVORABLE",
                    notes=f"Official {sev} alert: {a.get('description', a.get('title'))}",
                ))

        if hazards:
            for h in hazards:
                evidence.append(EvidenceItem(
                    factor="hazard_zone",
                    value=h.get("name"),
                    unit=None,
                    source=h.get("source", "Official Zone"),
                    data_type=h.get("source_category", "OFFICIAL"),
                    observed_at=str(h.get("effective_from")),
                    freshness=h.get("freshness", FreshnessCategory.FRESH),
                    assessment="UNFAVORABLE" if h.get("contains_point") else "NEUTRAL",
                    notes=f"Hazard zone '{h.get('name')}' ({h.get('hazard_type')}) in operational proximity.",
                ))

        if cyclones:
            for c in cyclones:
                evidence.append(EvidenceItem(
                    factor="cyclone_activity",
                    value=f"{c.get('name')} ({c.get('classification')})",
                    unit=None,
                    source=c.get("source", "IMD"),
                    data_type=c.get("source_category", "OFFICIAL"),
                    observed_at=str(c.get("observed_at")),
                    freshness=c.get("freshness", FreshnessCategory.FRESH),
                    assessment="CRITICAL_HAZARD" if c.get("distance_km", 999) < 200 else "UNFAVORABLE",
                    notes=f"Cyclonic system '{c.get('name')}' active at {c.get('distance_km')} km distance.",
                ))

        # 5. Geo-Spatial Regulatory Evidence
        if geospatial.get("in_restricted_zone"):
            evidence.append(EvidenceItem(
                factor="maritime_restricted_zone",
                value=", ".join(geospatial.get("restricted_zones", [])),
                unit=None,
                source="Geo-Spatial Registry",
                data_type="OFFICIAL",
                observed_at=None,
                freshness=FreshnessCategory.FRESH,
                assessment="RESTRICTED",
                notes="Location lies within a restricted military/firing exclusion zone.",
            ))

        if geospatial.get("in_protected_zone"):
            evidence.append(EvidenceItem(
                factor="marine_protected_area",
                value=", ".join(geospatial.get("protected_zones", [])),
                unit=None,
                source="Conservation Registry",
                data_type="OFFICIAL",
                observed_at=None,
                freshness=FreshnessCategory.FRESH,
                assessment="UNFAVORABLE",
                notes="Location is within an ecologically sensitive Marine Protected Area (MPA).",
            ))

        return evidence

    def evaluate_suitability(
        self,
        evidence: List[EvidenceItem],
        safety: Dict[str, Any],
        geospatial: Dict[str, Any],
        target_species: Optional[str] = None,
        vessel_type: Optional[str] = None,
    ) -> Tuple[FishingSuitability, List[str], str, List[str]]:
        """
        Computes deterministic fishing suitability, diagnostic reasons, risk level, and warnings.
        Applies absolute safety overrides: Safety strictly supersedes environmental suitability.
        """
        factors: List[FishingSuitabilityFactor] = []
        reasons: List[str] = []
        warnings_and_overrides: List[str] = []

        # 1. SST Evaluation
        sst_items = [e for e in evidence if e.factor == "sea_surface_temperature"]
        if sst_items:
            sst_val = sst_items[0].value
            if self.thresholds.SST_OPTIMAL_MIN_C <= sst_val <= self.thresholds.SST_OPTIMAL_MAX_C:
                factors.append(FishingSuitabilityFactor(
                    name="Thermal Profile (SST)",
                    status="FAVORABLE",
                    impact="POSITIVE",
                    summary=f"Sea surface temperature of {sst_val}°C is well-aligned with pelagic feeding activity.",
                ))
            elif self.thresholds.SST_ACCEPTABLE_MIN_C <= sst_val <= self.thresholds.SST_ACCEPTABLE_MAX_C:
                factors.append(FishingSuitabilityFactor(
                    name="Thermal Profile (SST)",
                    status="NEUTRAL",
                    impact="NEUTRAL",
                    summary=f"Sea surface temperature of {sst_val}°C is within acceptable range.",
                ))
            else:
                factors.append(FishingSuitabilityFactor(
                    name="Thermal Profile (SST)",
                    status="UNFAVORABLE",
                    impact="NEGATIVE",
                    summary=f"Sea surface temperature of {sst_val}°C is outside preferred thermal range.",
                ))
        else:
            factors.append(FishingSuitabilityFactor(
                name="Thermal Profile (SST)",
                status="UNKNOWN",
                impact="NEUTRAL",
                summary="SST telemetry is unavailable for this coordinate.",
            ))

        # 2. Wave & Sea State Evaluation
        wave_items = [e for e in evidence if e.factor == "significant_wave_height"]
        if wave_items:
            wave_h = wave_items[0].value
            if wave_h < self.thresholds.WAVE_FAVORABLE_MAX_M:
                factors.append(FishingSuitabilityFactor(
                    name="Sea State & Wave Conditions",
                    status="FAVORABLE",
                    impact="POSITIVE",
                    summary=f"Calm to moderate sea state with {wave_h}m wave height facilitates steady gear deployment.",
                ))
            elif wave_h <= self.thresholds.WAVE_CAUTION_MAX_M:
                factors.append(FishingSuitabilityFactor(
                    name="Sea State & Wave Conditions",
                    status="NEUTRAL",
                    impact="NEUTRAL",
                    summary=f"Moderate sea state ({wave_h}m wave height) manageable for motorized craft; exercise standard vigilance.",
                ))
            else:
                factors.append(FishingSuitabilityFactor(
                    name="Sea State & Wave Conditions",
                    status="UNFAVORABLE",
                    impact="NEGATIVE",
                    summary=f"Rough sea state with {wave_h}m wave height hampers small craft safety and net handling.",
                ))
                warnings_and_overrides.append(f"Elevated wave heights ({wave_h}m) exceed optimal operational limits.")
        else:
            factors.append(FishingSuitabilityFactor(
                name="Sea State & Wave Conditions",
                status="UNKNOWN",
                impact="NEUTRAL",
                summary="Wave height telemetry is unavailable.",
            ))

        # 3. Wind & Atmospheric Weather Evaluation
        wind_items = [e for e in evidence if e.factor == "wind_speed"]
        if wind_items:
            wind_spd = wind_items[0].value
            if wind_spd < self.thresholds.WIND_FAVORABLE_MAX_KMH:
                factors.append(FishingSuitabilityFactor(
                    name="Surface Wind Conditions",
                    status="FAVORABLE",
                    impact="POSITIVE",
                    summary=f"Light to gentle breeze ({wind_spd} km/h) favorable for drift stability.",
                ))
            elif wind_spd <= self.thresholds.WIND_CAUTION_MAX_KMH:
                factors.append(FishingSuitabilityFactor(
                    name="Surface Wind Conditions",
                    status="NEUTRAL",
                    impact="NEUTRAL",
                    summary=f"Moderate wind speed ({wind_spd} km/h); anchor holding and drift rate moderately affected.",
                ))
            else:
                factors.append(FishingSuitabilityFactor(
                    name="Surface Wind Conditions",
                    status="UNFAVORABLE",
                    impact="NEGATIVE",
                    summary=f"Strong winds ({wind_spd} km/h) induce surface drift and choppy waters.",
                ))
                warnings_and_overrides.append(f"High surface winds ({wind_spd} km/h) induce hazardous drift.")
        else:
            factors.append(FishingSuitabilityFactor(
                name="Surface Wind Conditions",
                status="UNKNOWN",
                impact="NEUTRAL",
                summary="Surface wind telemetry is unavailable.",
            ))

        # 4. Ocean Colour & Chlorophyll-a (Bio-productivity)
        chlor_items = [e for e in evidence if e.factor == "chlorophyll_a_concentration"]
        if chlor_items:
            chlor_val = chlor_items[0].value
            if chlor_val >= self.thresholds.CHLOROPHYLL_FAVORABLE_MIN_MG_M3:
                factors.append(FishingSuitabilityFactor(
                    name="Marine Productivity (Chlorophyll-a)",
                    status="FAVORABLE",
                    impact="POSITIVE",
                    summary=f"Satellite chlorophyll-a concentration ({chlor_val} mg/m³) indicates elevated planktonic density.",
                ))
            else:
                factors.append(FishingSuitabilityFactor(
                    name="Marine Productivity (Chlorophyll-a)",
                    status="NEUTRAL",
                    impact="NEUTRAL",
                    summary=f"Chlorophyll-a concentration ({chlor_val} mg/m³) is at baseline oligotrophic levels.",
                ))
        else:
            factors.append(FishingSuitabilityFactor(
                name="Marine Productivity (Chlorophyll-a)",
                status="UNKNOWN",
                impact="NEUTRAL",
                summary="Satellite chlorophyll-a optical data is currently unavailable.",
            ))

        # 5. Regulatory / Conservation Sanctuary Check
        if geospatial.get("in_restricted_zone"):
            factors.append(FishingSuitabilityFactor(
                name="Regulatory Zoning",
                status="UNFAVORABLE",
                impact="BLOCKING",
                summary=f"Location inside restricted maritime sector: {', '.join(geospatial.get('restricted_zones', []))}.",
            ))
            reasons.append("Location is inside a legally restricted maritime exclusion zone where fishing is prohibited.")
            warnings_and_overrides.append("Legal restriction override: Coordinates intersect prohibited naval/military zone.")
        elif geospatial.get("in_protected_zone"):
            factors.append(FishingSuitabilityFactor(
                name="Marine Protected Area",
                status="UNFAVORABLE",
                impact="NEGATIVE",
                summary=f"Location inside Marine Protected Area: {', '.join(geospatial.get('protected_zones', []))}.",
            ))
            reasons.append("Location lies inside a designated Marine Protected Area with strict conservation restrictions.")
            warnings_and_overrides.append("Conservation boundary alert: Operations inside Marine Protected Area (MPA).")
        else:
            factors.append(FishingSuitabilityFactor(
                name="Spatial Navigability",
                status="FAVORABLE",
                impact="POSITIVE",
                summary="Location is clear of recorded military exclusions and marine protected sanctuaries.",
            ))

        # -------------------------------------------------------------
        # 6. SAFETY OVERRIDE ENGINE (Safety ALWAYS takes precedence)
        # -------------------------------------------------------------
        safety_status = safety.get("status", "UNKNOWN").upper()
        active_alerts = safety.get("active_alerts", [])
        has_critical = any(a.get("severity", "").upper() == "CRITICAL" for a in active_alerts) or safety_status == "CRITICAL"
        has_warning = any(a.get("severity", "").upper() == "WARNING" for a in active_alerts) or safety_status == "WARNING"
        in_restricted = geospatial.get("in_restricted_zone", False)

        favorable_count = sum(1 for f in factors if f.status == "FAVORABLE")
        unfavorable_count = sum(1 for f in factors if f.status == "UNFAVORABLE")
        unknown_count = sum(1 for f in factors if f.status == "UNKNOWN")

        if in_restricted or has_critical:
            final_status = "BLOCKED"
            risk_level = "CRITICAL"
            reasons.append("CRITICAL safety hazard or restricted exclusion zone active. Operations are BLOCKED.")
            warnings_and_overrides.append("SAFETY OVERRIDE: Severe hazard or legal exclusion blocks departure.")
        elif has_warning:
            final_status = "WARNING"
            risk_level = "HIGH"
            reasons.append("Active official WARNING or severe hazard zone detected. Fishing operations are NOT recommended.")
            warnings_and_overrides.append("SAFETY OVERRIDE: Active official warning alert supersedes suitability.")
        elif safety_status == "CAUTION" or geospatial.get("in_protected_zone"):
            final_status = "CAUTION"
            risk_level = "MODERATE"
            reasons.append("Advisory caution or protected sanctuary constraints active in this operational sector.")
        elif safety_status == "INSUFFICIENT_DATA" or unknown_count >= 3:
            final_status = "INSUFFICIENT_DATA"
            risk_level = "UNKNOWN"
            reasons.append("Sufficient local oceanographic telemetry is unavailable. Cannot adequately evaluate operational safety.")
            warnings_and_overrides.append("DATA OVERRIDE: Telemetry gaps prevent definitive safety clearance.")
        else:
            if unfavorable_count > favorable_count:
                final_status = "UNFAVORABLE"
                risk_level = "MODERATE"
                reasons.append("Environmental factors (sea state, wind, or low productivity) indicate unfavorable fishing conditions.")
            elif favorable_count >= 2:
                final_status = "FAVORABLE"
                risk_level = "LOW"
                reasons.append("Environmental indicators (SST, calm sea state, manageable wind) appear favorable based on available data.")
            else:
                final_status = "NEUTRAL"
                risk_level = "LOW"
                reasons.append("Environmental conditions are at average seasonal baseline levels.")

        # Calculate deterministic score if not blocked
        suitability_score = None
        if final_status not in ("BLOCKED", "INSUFFICIENT_DATA"):
            valid_factors = [f for f in factors if f.status in ("FAVORABLE", "NEUTRAL", "UNFAVORABLE")]
            if valid_factors:
                score_sum = sum(1.0 if f.status == "FAVORABLE" else (0.5 if f.status == "NEUTRAL" else 0.0) for f in valid_factors)
                suitability_score = round(score_sum / len(valid_factors), 2)

        return (
            FishingSuitability(
                status=final_status,
                score=suitability_score,
                factors=factors,
            ),
            reasons,
            risk_level,
            warnings_and_overrides,
        )

    def evaluate_confidence(
        self,
        evidence: List[EvidenceItem],
        safety: Dict[str, Any],
        suitability_status: str,
    ) -> ConfidenceAssessment:
        """
        Determines deterministic confidence level based on data source diversity,
        telemetry freshness, and safety coverage.
        """
        reasons: List[str] = []
        fresh_count = sum(1 for e in evidence if e.freshness == FreshnessCategory.FRESH)
        aging_count = sum(1 for e in evidence if e.freshness == FreshnessCategory.AGING)
        stale_count = sum(1 for e in evidence if e.freshness in (FreshnessCategory.STALE, FreshnessCategory.EXPIRED))

        has_marine = any("wave" in e.factor or "current" in e.factor for e in evidence)
        has_weather = any("wind" in e.factor or "air_temperature" in e.factor for e in evidence)
        has_eo = any("chlorophyll" in e.factor or "cloud" in e.factor for e in evidence)

        if has_marine:
            reasons.append("Marine sea state telemetry verified from active observational records.")
        else:
            reasons.append("Direct marine sea state observations unavailable for immediate coordinates.")

        if has_weather:
            reasons.append("Atmospheric wind and precipitation telemetry verified.")
        else:
            reasons.append("Local atmospheric weather telemetry missing.")

        reasons.append("Official INCOIS Potential Fishing Zone (PFZ) advisory data is currently unavailable.")

        if suitability_status == "INSUFFICIENT_DATA" or stale_count > 0 or (not has_marine and not has_weather):
            level = "LOW"
            reasons.append("Low confidence due to incomplete or stale telemetry coverage.")
        elif fresh_count >= 3 and has_marine and has_weather:
            level = "HIGH"
            reasons.append("High confidence: multiple fresh official observation layers verified.")
        elif fresh_count + aging_count >= 2:
            level = "MEDIUM"
            reasons.append("Medium confidence: partial observation layers available.")
        else:
            level = "LOW"

        return ConfidenceAssessment(level=level, reasons=reasons)

    def build_domain_contributions(
        self,
        weather: Optional[Dict[str, Any]],
        marine: Optional[Dict[str, Any]],
        eo: Optional[Dict[str, Any]],
        safety: Dict[str, Any],
        geospatial: Dict[str, Any],
        operations: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Summarizes domain-specific inputs into structured agent contributions.
        """
        return {
            "weather": {
                "status": "AVAILABLE" if weather else "UNAVAILABLE",
                "source": weather.get("source") if weather else None,
                "freshness": weather.get("freshness", "UNKNOWN") if weather else "UNKNOWN",
                "wind_speed_kmh": weather.get("wind_speed_kmh") if weather else None,
            },
            "marine_conditions": {
                "status": "AVAILABLE" if marine else "UNAVAILABLE",
                "source": marine.get("source") if marine else None,
                "freshness": marine.get("freshness", "UNKNOWN") if marine else "UNKNOWN",
                "wave_height_m": marine.get("wave_height_m") if marine else None,
                "sst_c": marine.get("sea_surface_temperature_c") if marine else None,
            },
            "earth_observation": {
                "status": "AVAILABLE" if eo else "UNAVAILABLE",
                "source": eo.get("source") if eo else None,
                "freshness": eo.get("freshness", "UNKNOWN") if eo else "UNKNOWN",
                "chlorophyll_a_mg_m3": eo.get("chlorophyll_a_mg_m3") if eo else None,
            },
            "geospatial_navigation": {
                "in_restricted_zone": geospatial.get("in_restricted_zone", False),
                "in_protected_zone": geospatial.get("in_protected_zone", False),
                "nearest_port_count": len(geospatial.get("nearest_ports", [])),
            },
            "disaster_safety": {
                "safety_status": safety.get("status", "UNKNOWN"),
                "active_alert_count": len(safety.get("active_alerts", [])),
                "cyclone_threat_count": len(safety.get("nearby_cyclones", [])),
            },
            "marine_operations": {
                "distance_km": operations.get("distance_km") if operations else None,
                "estimated_duration_minutes": operations.get("estimated_duration_minutes") if operations else None,
            },
        }

    def build_key_conditions(
        self,
        weather: Optional[Dict[str, Any]],
        marine: Optional[Dict[str, Any]],
        eo: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Builds a concise summary of primary environmental conditions.
        """
        conditions: Dict[str, Any] = {}
        if marine:
            conditions["wave_height_m"] = marine.get("wave_height_m")
            conditions["sea_surface_temperature_c"] = marine.get("sea_surface_temperature_c")
            conditions["current_velocity_kmh"] = marine.get("ocean_current_velocity_kmh")
        if weather:
            conditions["wind_speed_kmh"] = weather.get("wind_speed_kmh")
            conditions["air_temperature_c"] = weather.get("temperature_c")
            conditions["precipitation_mm"] = weather.get("precipitation_mm")
        if eo:
            conditions["chlorophyll_a_mg_m3"] = eo.get("chlorophyll_a_mg_m3")
            conditions["cloud_cover_percent"] = eo.get("cloud_cover_percent")
        return conditions

    def build_data_quality(
        self,
        evidence: List[EvidenceItem],
    ) -> Tuple[Dict[str, Any], str]:
        """
        Computes overall data freshness and telemetry quality metrics.
        """
        fresh_count = sum(1 for e in evidence if e.freshness == FreshnessCategory.FRESH)
        total_count = len(evidence)
        overall_freshness = "FRESH" if fresh_count >= 2 else ("AGING" if fresh_count == 1 else "STALE")

        quality_summary = {
            "overall_freshness": overall_freshness,
            "total_evidence_factors": total_count,
            "fresh_factor_count": fresh_count,
            "aging_factor_count": sum(1 for e in evidence if e.freshness == FreshnessCategory.AGING),
            "stale_factor_count": sum(1 for e in evidence if e.freshness in (FreshnessCategory.STALE, FreshnessCategory.EXPIRED)),
            "coverage_completeness": "COMPLETE" if total_count >= 5 else ("PARTIAL" if total_count >= 2 else "MINIMAL"),
        }
        return quality_summary, overall_freshness

    def compare_locations(
        self,
        assessment_a: FishingAssessment,
        assessment_b: FishingAssessment,
        name_a: str = "Location A",
        name_b: str = "Location B",
    ) -> LocationComparisonResponse:
        """
        Performs objective comparative evaluation of two candidate fishing grounds.
        """
        status_rank = {
            "FAVORABLE": 4,
            "NEUTRAL": 3,
            "CAUTION": 2,
            "UNFAVORABLE": 1,
            "INSUFFICIENT_DATA": 0,
            "WARNING": -1,
            "BLOCKED": -2,
        }

        status_a = assessment_a.fishing_suitability.status
        status_b = assessment_b.fishing_suitability.status
        rank_a = status_rank.get(status_a, 0)
        rank_b = status_rank.get(status_b, 0)

        score_a = assessment_a.fishing_suitability.score or 0.0
        score_b = assessment_b.fishing_suitability.score or 0.0

        reasons: List[str] = []

        if rank_a > rank_b:
            recommended = "location_a"
            reasons.append(f"{name_a} is recommended ({status_a}) over {name_b} ({status_b}) based on superior safety clearance and marine indicators.")
        elif rank_b > rank_a:
            recommended = "location_b"
            reasons.append(f"{name_b} is recommended ({status_b}) over {name_a} ({status_a}) based on superior safety clearance and marine indicators.")
        elif rank_a >= 3 and rank_b >= 3:
            if score_a > score_b:
                recommended = "location_a"
                reasons.append(f"Both locations are {status_a}; {name_a} shows slightly higher environmental index ({score_a} vs {score_b}).")
            elif score_b > score_a:
                recommended = "location_b"
                reasons.append(f"Both locations are {status_b}; {name_b} shows slightly higher environmental index ({score_b} vs {score_a}).")
            else:
                recommended = "undetermined"
                reasons.append(f"Both {name_a} and {name_b} display comparable {status_a} operational conditions.")
        else:
            recommended = "neither"
            reasons.append(f"Neither location is recommended under current safety and environmental assessments ({name_a}: {status_a}, {name_b}: {status_b}).")

        summary = {
            "location_a": {
                "name": name_a,
                "coordinates": assessment_a.location,
                "status": status_a,
                "risk_level": assessment_a.risk_level,
                "score": score_a,
                "confidence": assessment_a.confidence.level,
            },
            "location_b": {
                "name": name_b,
                "coordinates": assessment_b.location,
                "status": status_b,
                "risk_level": assessment_b.risk_level,
                "score": score_b,
                "confidence": assessment_b.confidence.level,
            },
            "recommended_option": recommended,
        }

        conf = "HIGH" if (assessment_a.confidence.level == "HIGH" and assessment_b.confidence.level == "HIGH") else "MEDIUM"

        return LocationComparisonResponse(
            location_a_assessment=assessment_a,
            location_b_assessment=assessment_b,
            comparison_summary=summary,
            recommended_option=recommended,
            reasons=reasons,
            confidence=conf,
        )

    def evaluate_what_if(
        self,
        baseline: FishingAssessment,
        scenario: FishingAssessment,
        changes: List[str],
        scenario_description: Optional[str] = None,
    ) -> WhatIfResponse:
        """
        Compares baseline operational assessment against what-if scenario assessment.
        """
        status_rank = {
            "FAVORABLE": 5,
            "NEUTRAL": 4,
            "CAUTION": 3,
            "UNFAVORABLE": 2,
            "INSUFFICIENT_DATA": 1,
            "WARNING": 0,
            "BLOCKED": -1,
        }
        base_rank = status_rank.get(baseline.fishing_suitability.status, 0)
        scen_rank = status_rank.get(scenario.fishing_suitability.status, 0)

        if scen_rank > base_rank:
            suitability_change = "IMPROVED"
            safety_change = "IMPROVED" if scenario.safety.get("status") in ("SAFE", "CAUTION") else "UNCHANGED"
            rec = f"Scenario adjustments ({', '.join(changes)}) improve operational feasibility from {baseline.fishing_suitability.status} to {scenario.fishing_suitability.status}."
        elif scen_rank < base_rank:
            suitability_change = "DEGRADED"
            safety_change = "BLOCKED" if scenario.fishing_suitability.status == "BLOCKED" else "DEGRADED"
            rec = f"Scenario modifications result in less favorable or more restricted conditions ({scenario.fishing_suitability.status} vs baseline {baseline.fishing_suitability.status})."
        else:
            suitability_change = "UNCHANGED"
            safety_change = "UNCHANGED"
            rec = f"No significant shift in operational suitability detected ({scenario.fishing_suitability.status})."

        desc = scenario_description or f"Modified parameters: {', '.join(changes)}"
        summary = f"What-If Analysis [{desc}]: Baseline={baseline.fishing_suitability.status} -> Scenario={scenario.fishing_suitability.status}. Change: {suitability_change}."

        return WhatIfResponse(
            baseline=baseline,
            scenario=scenario,
            changes=changes,
            safety_change=safety_change,
            suitability_change=suitability_change,
            confidence=scenario.confidence.level,
            recommendation=rec,
            summary=summary,
        )
