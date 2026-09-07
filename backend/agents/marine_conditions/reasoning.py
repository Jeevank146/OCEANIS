from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from agents.marine_conditions.schemas import MarineConditionsEvidenceItem
from services.freshness import FreshnessCategory


@dataclass(frozen=True)
class MarineConditionsThresholds:
    """
    Configurable deterministic oceanographic thresholds for sea state,
    wave dynamics, swell severity, and current velocity.
    Isolated from API and orchestration logic.
    """
    # Significant Wave Height (m) - WMO Sea State Guide
    WAVE_NORMAL_MAX_M: float = 1.25
    WAVE_MODERATE_MAX_M: float = 2.50
    WAVE_ROUGH_MAX_M: float = 4.00

    # Swell Wave Height (m)
    SWELL_NORMAL_MAX_M: float = 1.00
    SWELL_MODERATE_MAX_M: float = 2.00
    SWELL_ROUGH_MAX_M: float = 3.50

    # Wind-Wave Height (m)
    WIND_WAVE_NORMAL_MAX_M: float = 1.00
    WIND_WAVE_MODERATE_MAX_M: float = 2.00

    # Ocean Current Velocity (km/h)
    CURRENT_NORMAL_MAX_KMH: float = 2.50
    CURRENT_MODERATE_MAX_KMH: float = 5.00

    # Wave Period Thresholds (seconds) - Long period swells pose elevated harbor surge & shallow shoaling risks
    SWELL_LONG_PERIOD_THRESHOLD_S: float = 12.0


class MarineConditionsReasoningEngine:
    """
    Deterministic reasoning engine for marine conditions, wave dynamics,
    swell analysis, current velocity, and physical ocean risk evaluation.
    """

    def __init__(self, thresholds: Optional[MarineConditionsThresholds] = None):
        self.thresholds = thresholds or MarineConditionsThresholds()

    def assess_conditions(
        self,
        marine_data: Optional[Dict[str, Any]],
    ) -> Tuple[str, str, float, str, List[MarineConditionsEvidenceItem], List[str], str, str]:
        """
        Evaluates physical marine parameters deterministically.
        Returns:
            (sea_state, risk_level, confidence, data_freshness, evidence_list, warnings, recommendation, explanation)
        """
        if not marine_data:
            return (
                "INSUFFICIENT_DATA",
                "UNKNOWN",
                0.0,
                "UNKNOWN",
                [],
                ["No observational or model marine data is available for this location."],
                "INSUFFICIENT DATA: Real-time marine conditions and wave metrics are not available. Exercise extreme caution and consult official coastal bulletins.",
                "Marine sea state cannot be determined due to complete absence of local oceanographic telemetry.",
            )

        evidence: List[MarineConditionsEvidenceItem] = []
        warnings: List[str] = []
        severities: List[str] = []

        source = marine_data.get("source", "Marine Data Layer")
        data_type = marine_data.get("data_type", "OBSERVATION")
        quality = marine_data.get("quality_flag", "GOOD")
        freshness = marine_data.get("freshness", "FRESH")
        observed_at = marine_data.get("observed_at")
        retrieved_at = marine_data.get("retrieved_at")

        # Base confidence calculation based on data freshness and quality
        base_confidence = 0.95 if freshness == FreshnessCategory.FRESH else (
            0.75 if freshness == FreshnessCategory.AGING else (
                0.35 if freshness in (FreshnessCategory.STALE, FreshnessCategory.EXPIRED) else 0.50
            )
        )
        if quality in ("SUSPECT", "DEGRADED", "POOR", "BAD", "CORRUPT"):
            base_confidence = round(max(0.1, base_confidence - 0.2), 2)

        # 1. Significant Wave Height Assessment
        wave_h = marine_data.get("wave_height_m")
        if wave_h is not None:
            if wave_h < self.thresholds.WAVE_NORMAL_MAX_M:
                wave_sev = "NORMAL"
                wave_note = f"Wave height of {wave_h}m indicates calm to slight sea conditions."
            elif wave_h <= self.thresholds.WAVE_MODERATE_MAX_M:
                wave_sev = "MODERATE"
                wave_note = f"Wave height of {wave_h}m indicates moderate sea state; manageable for motorized craft."
            elif wave_h <= self.thresholds.WAVE_ROUGH_MAX_M:
                wave_sev = "ROUGH"
                wave_note = f"Wave height of {wave_h}m represents rough sea state with pronounced chop."
                warnings.append(f"Rough sea state: Significant wave height reached {wave_h}m.")
            else:
                wave_sev = "SEVERE"
                wave_note = f"Wave height of {wave_h}m represents high/severe sea state; hazardous for marine navigation."
                warnings.append(f"HAZARDOUS SEA STATE: Wave height is {wave_h}m.")

            severities.append(wave_sev)
            evidence.append(MarineConditionsEvidenceItem(
                factor="significant_wave_height",
                value=wave_h,
                unit="m",
                source=source,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=quality,
                freshness=freshness,
                confidence=base_confidence,
                severity=wave_sev,
                notes=wave_note,
            ))

        # 2. Swell Wave Height & Period Assessment
        swell_h = marine_data.get("swell_wave_height_m")
        swell_p = marine_data.get("swell_wave_period_s")
        if swell_h is not None:
            if swell_h < self.thresholds.SWELL_NORMAL_MAX_M:
                swell_sev = "NORMAL"
                swell_note = f"Swell height of {swell_h}m is at low baseline levels."
            elif swell_h <= self.thresholds.SWELL_MODERATE_MAX_M:
                swell_sev = "MODERATE"
                swell_note = f"Moderate swell of {swell_h}m detected."
            elif swell_h <= self.thresholds.SWELL_ROUGH_MAX_M:
                swell_sev = "ROUGH"
                swell_note = f"Heavy swell of {swell_h}m induces strong rhythmic boat rolling."
                warnings.append(f"Heavy swell: Swell wave height reached {swell_h}m.")
            else:
                swell_sev = "SEVERE"
                swell_note = f"Severe swell surge of {swell_h}m creates critical shoaling and breaker danger."
                warnings.append(f"CRITICAL SWELL SURGE: Swell height is {swell_h}m.")

            if swell_p is not None and swell_p >= self.thresholds.SWELL_LONG_PERIOD_THRESHOLD_S:
                warnings.append(f"Long-period swell ({swell_p}s) carries high energy; exercise vigilance near shallow shoals and harbor entrances.")

            severities.append(swell_sev)
            evidence.append(MarineConditionsEvidenceItem(
                factor="swell_wave_height",
                value=swell_h,
                unit="m",
                source=source,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=quality,
                freshness=freshness,
                confidence=base_confidence,
                severity=swell_sev,
                notes=swell_note,
            ))

        # 3. Wind-Wave Height Assessment
        wind_wave_h = marine_data.get("wind_wave_height_m")
        if wind_wave_h is not None:
            if wind_wave_h < self.thresholds.WIND_WAVE_NORMAL_MAX_M:
                wind_wave_sev = "NORMAL"
            elif wind_wave_h <= self.thresholds.WIND_WAVE_MODERATE_MAX_M:
                wind_wave_sev = "MODERATE"
            else:
                wind_wave_sev = "ROUGH"
                warnings.append(f"Elevated wind waves ({wind_wave_h}m) causing local surface chop.")

            severities.append(wind_wave_sev)
            evidence.append(MarineConditionsEvidenceItem(
                factor="wind_wave_height",
                value=wind_wave_h,
                unit="m",
                source=source,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=quality,
                freshness=freshness,
                confidence=base_confidence,
                severity=wind_wave_sev,
                notes=f"Wind-wave height of {wind_wave_h}m.",
            ))

        # 4. Ocean Current Velocity Assessment
        current_v = marine_data.get("ocean_current_velocity_kmh")
        if current_v is not None:
            if current_v < self.thresholds.CURRENT_NORMAL_MAX_KMH:
                curr_sev = "NORMAL"
                curr_note = f"Current velocity of {current_v} km/h is gentle."
            elif current_v <= self.thresholds.CURRENT_MODERATE_MAX_KMH:
                curr_sev = "MODERATE"
                curr_note = f"Moderate current velocity of {current_v} km/h."
            else:
                curr_sev = "ROUGH"
                curr_note = f"Strong ocean current velocity of {current_v} km/h induces significant vessel drift."
                warnings.append(f"Strong current: Ocean current velocity is {current_v} km/h.")

            severities.append(curr_sev)
            evidence.append(MarineConditionsEvidenceItem(
                factor="ocean_current_velocity",
                value=current_v,
                unit="km/h",
                source=source,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=quality,
                freshness=freshness,
                confidence=base_confidence,
                severity=curr_sev,
                notes=curr_note,
            ))

        # 5. Sea Surface Temperature (SST) Context
        sst = marine_data.get("sea_surface_temperature_c")
        if sst is not None:
            evidence.append(MarineConditionsEvidenceItem(
                factor="sea_surface_temperature",
                value=sst,
                unit="°C",
                source=source,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=quality,
                freshness=freshness,
                confidence=base_confidence,
                severity="NORMAL",
                notes=f"Sea surface temperature recorded at {sst}°C.",
            ))

        # -----------------------------------------------------------------
        # Overall Sea State & Risk Level Synthesis
        # -----------------------------------------------------------------
        if "SEVERE" in severities:
            sea_state = "SEVERE"
            risk_level = "CRITICAL"
            recommendation = (
                "SEVERE SEA CONDITIONS DETECTED: Hazardous wave and swell heights present substantial physical risks to maritime craft. "
                "Non-essential coastal navigation and small-craft departures are strongly advised against."
            )
            explanation = (
                f"Severe sea state is driven by elevated physical telemetry: significant wave height ({wave_h}m) or swell ({swell_h}m) "
                "exceeding standard seaworthiness limits."
            )
        elif "ROUGH" in severities:
            sea_state = "ROUGH"
            risk_level = "HIGH"
            recommendation = (
                "ROUGH SEA CONDITIONS: Rough waves and pronounced swell detected in the target sector. "
                "Small vessel operations are not recommended without advanced sea-keeping capability and crew safety protocols."
            )
            explanation = (
                f"Rough sea state identified based on wave heights ({wave_h}m) or heavy swell ({swell_h}m). "
                "Vessel masters should monitor VHF marine broadcasts and avoid shallow bar crossings."
            )
        elif "MODERATE" in severities:
            sea_state = "MODERATE"
            risk_level = "MODERATE"
            recommendation = (
                "MODERATE SEA CONDITIONS: Manageable sea state with moderate wave chop. "
                "Standard coastal operations may proceed with routine navigational vigilance and active life-jacket protocols."
            )
            explanation = (
                f"Moderate sea conditions confirmed with wave height of {wave_h}m and swell of {swell_h}m within standard operational thresholds."
            )
        else:
            sea_state = "NORMAL"
            risk_level = "LOW"
            recommendation = (
                "NORMAL SEA CONDITIONS: Available observational data indicates calm to slight sea state and gentle currents. "
                "Proceed with standard operational procedures and watchkeeping."
            )
            explanation = (
                f"Calm to slight sea state verified across wave ({wave_h}m), swell ({swell_h}m), and current ({current_v} km/h) measurements."
            )

        # Strictly clean any accidental safety guarantee wording
        rec_clean = (
            recommendation
            .replace("100% safe", "manageable under current observations")
            .replace("guaranteed safe", "favorable based on current telemetry")
            .replace("no risk", "low physical risk")
        )

        return (
            sea_state,
            risk_level,
            base_confidence,
            freshness,
            evidence,
            warnings,
            rec_clean,
            explanation,
        )
