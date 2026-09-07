from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from agents.earth_observation.schemas import (
    EarthObservationEvidenceItem,
    EarthObservationIndicators,
    EarthObservationTemporalComparison,
)
from services.freshness import FreshnessCategory


@dataclass(frozen=True)
class EarthObservationThresholds:
    """
    Configurable deterministic oceanographic thresholds for satellite-derived
    thermal, optical, and bio-optical measurements.
    Isolated from API and orchestration layers.
    """
    # Sea Surface Temperature (°C)
    SST_MIN_TROPICAL_C: float = 24.0
    SST_MAX_TROPICAL_C: float = 31.0
    SST_OPTIMAL_MIN_C: float = 26.0
    SST_OPTIMAL_MAX_C: float = 29.5

    # Chlorophyll-a Concentration (mg/m³)
    CHL_OLIGOTROPHIC_MAX_MG_M3: float = 0.20
    CHL_MODERATE_MAX_MG_M3: float = 1.00
    CHL_HIGH_FAVORABLE_MAX_MG_M3: float = 5.00
    CHL_ANOMALOUS_BLOOM_MIN_MG_M3: float = 5.00

    # Cloud Cover Percentage (%)
    CLOUD_CLEAR_MAX_PERCENT: float = 20.0
    CLOUD_MODERATE_MAX_PERCENT: float = 60.0
    CLOUD_OBSCURED_MIN_PERCENT: float = 60.0

    # Solar Irradiance (W/m²)
    SOLAR_IRRADIANCE_HIGH_W_M2: float = 600.0


class EarthObservationReasoningEngine:
    """
    Deterministic reasoning engine for satellite Earth Observation (EO) telemetry,
    bio-optical ocean color indicators, thermal fronts, and temporal comparisons.
    """

    def __init__(self, thresholds: Optional[EarthObservationThresholds] = None):
        self.thresholds = thresholds or EarthObservationThresholds()

    def assess_conditions(
        self,
        current_data: Optional[Dict[str, Any]],
        previous_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[
        Dict[str, Any],
        EarthObservationIndicators,
        Optional[EarthObservationTemporalComparison],
        str,
        str,
        float,
        List[EarthObservationEvidenceItem],
        List[str],
        str,
        str,
    ]:
        """
        Evaluates satellite Earth Observation parameters deterministically.
        Returns:
            (observations_dict, indicators, temporal_comparison, observation_quality, data_freshness, confidence, evidence_list, warnings, recommendation, explanation)
        """
        if not current_data:
            temporal_missing = EarthObservationTemporalComparison(
                has_historical_data=False,
                status="INSUFFICIENT_DATA",
                summary="INSUFFICIENT_DATA: No historical satellite observation available for temporal trend comparison.",
            )
            empty_indicators = EarthObservationIndicators()
            return (
                {},
                empty_indicators,
                temporal_missing,
                "UNKNOWN",
                "UNKNOWN",
                0.0,
                [],
                ["No Earth Observation or satellite telemetry is available for this location."],
                "INSUFFICIENT DATA: Satellite ocean colour, SST, and optical observations are unavailable for this sector. Rely on direct in-situ marine observations.",
                "Earth Observation oceanographic indicators cannot be evaluated due to complete absence of local satellite telemetry.",
            )

        evidence: List[EarthObservationEvidenceItem] = []
        warnings: List[str] = []

        source = current_data.get("source", "Copernicus / Sentinel-3")
        platform = current_data.get("satellite_platform")
        sensor = current_data.get("sensor_instrument")
        product = current_data.get("product_type", "SST_AND_OPTICAL")
        lat = current_data.get("latitude")
        lon = current_data.get("longitude")
        observed_at = current_data.get("observed_at")
        retrieved_at = current_data.get("retrieved_at")
        data_type = current_data.get("data_type", "OBSERVATION")
        quality = current_data.get("quality_flag", "OPERATIONAL_QUALITY")
        freshness = current_data.get("freshness", "FRESH")

        cloud_cover = current_data.get("cloud_cover_percent")
        sst = current_data.get("sea_surface_temperature_c")
        chl = current_data.get("chlorophyll_a_mg_m3")
        ocean_col = current_data.get("ocean_colour")
        solar_rad = current_data.get("solar_radiation_w_m2")

        # Base confidence determination
        base_confidence = 0.95 if freshness == FreshnessCategory.FRESH else (
            0.75 if freshness == FreshnessCategory.AGING else (
                0.35 if freshness in (FreshnessCategory.STALE, FreshnessCategory.EXPIRED) else 0.50
            )
        )
        if quality in ("SUSPECT", "DEGRADED", "POOR", "BAD"):
            base_confidence = round(max(0.1, base_confidence - 0.2), 2)

        # Cloud obscuration impact on optical observations
        optical_quality = quality
        optical_confidence = base_confidence
        optical_observability = "HIGH_QUALITY"

        if cloud_cover is not None:
            if cloud_cover > self.thresholds.CLOUD_OBSCURED_MIN_PERCENT:
                optical_observability = "CLOUD_OBSCURED"
                optical_quality = "LOW_QUALITY"
                optical_confidence = round(max(0.2, base_confidence - 0.3), 2)
                warnings.append(
                    f"Heavy cloud cover ({cloud_cover}%) obscures surface ocean optical reflectance; "
                    "optical/chlorophyll measurements may experience atmospheric attenuation."
                )
            elif cloud_cover > self.thresholds.CLOUD_CLEAR_MAX_PERCENT:
                optical_observability = "MODERATE_HAZE"
                optical_confidence = round(max(0.3, base_confidence - 0.1), 2)

        # 1. Sea Surface Temperature (SST) Assessment
        sst_status = "UNKNOWN"
        thermal_front_detected = False
        if sst is not None:
            if sst < self.thresholds.SST_MIN_TROPICAL_C:
                sst_status = "COOL_UPWELLING"
                thermal_front_detected = True
                sst_note = f"SST of {sst}°C indicates cooler water mass, potential coastal upwelling or thermal divergence."
                sst_sev = "FAVORABLE_INDICATOR"
            elif sst > self.thresholds.SST_MAX_TROPICAL_C:
                sst_status = "ANOMALOUS"
                sst_note = f"SST of {sst}°C indicates elevated warm thermal anomaly."
                sst_sev = "ANOMALOUS"
                warnings.append(f"Elevated Sea Surface Temperature detected ({sst}°C); potential warm water layer.")
            elif self.thresholds.SST_OPTIMAL_MIN_C <= sst <= self.thresholds.SST_OPTIMAL_MAX_C:
                sst_status = "NORMAL"
                sst_note = f"SST of {sst}°C is within optimal range for coastal marine species."
                sst_sev = "FAVORABLE_INDICATOR"
            else:
                sst_status = "NORMAL"
                sst_note = f"SST recorded at {sst}°C."
                sst_sev = "NORMAL"

            evidence.append(EarthObservationEvidenceItem(
                factor="sea_surface_temperature",
                value=sst,
                unit="°C",
                source=source,
                satellite_platform=platform,
                sensor_instrument=sensor,
                product_type=product,
                latitude=lat,
                longitude=lon,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=quality,
                freshness=freshness,
                confidence=base_confidence,
                severity=sst_sev,
                notes=sst_note,
            ))

        # 2. Chlorophyll-a Assessment
        chl_status = "UNKNOWN"
        chl_gradient_detected = False
        if chl is not None:
            if chl < self.thresholds.CHL_OLIGOTROPHIC_MAX_MG_M3:
                chl_status = "OLIGOTROPHIC"
                chl_sev = "NORMAL"
                chl_note = f"Chlorophyll-a concentration of {chl} mg/m³ indicates clear, oligotrophic waters with low primary productivity."
            elif chl <= self.thresholds.CHL_MODERATE_MAX_MG_M3:
                chl_status = "MODERATE_PRODUCTIVITY"
                chl_sev = "NORMAL"
                chl_note = f"Chlorophyll-a concentration of {chl} mg/m³ indicates moderate phytoplankton productivity."
            elif chl <= self.thresholds.CHL_HIGH_FAVORABLE_MAX_MG_M3:
                chl_status = "FAVORABLE_INDICATOR"
                chl_gradient_detected = True
                chl_sev = "FAVORABLE_INDICATOR"
                chl_note = (
                    f"Chlorophyll-a concentration of {chl} mg/m³ indicates elevated phytoplankton biomass and primary biological productivity, "
                    "serving as an EO-derived indicator for marine foraging ecology."
                )
            else:
                chl_status = "ANOMALOUS_BLOOM"
                chl_sev = "ANOMALOUS"
                chl_note = f"Unusually high chlorophyll-a ({chl} mg/m³) indicates dense algal concentration or local bloom conditions."
                warnings.append(f"High chlorophyll concentration ({chl} mg/m³) detected; check local water quality for algal blooms.")

            evidence.append(EarthObservationEvidenceItem(
                factor="chlorophyll_a",
                value=chl,
                unit="mg/m³",
                source=source,
                satellite_platform=platform,
                sensor_instrument=sensor,
                product_type=product,
                latitude=lat,
                longitude=lon,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=optical_quality,
                freshness=freshness,
                confidence=optical_confidence,
                severity=chl_sev,
                notes=chl_note,
            ))

        # 3. Ocean Colour Assessment
        ocean_col_status = "UNKNOWN"
        if ocean_col is not None:
            if "Green" in ocean_col or "green" in ocean_col:
                ocean_col_status = "MESOTROPHIC"
            elif "Deep Blue" in ocean_col or "blue" in ocean_col.lower():
                ocean_col_status = "CLEAR_OCEANIC"
            else:
                ocean_col_status = "MESOTROPHIC"

            evidence.append(EarthObservationEvidenceItem(
                factor="ocean_colour",
                value=ocean_col,
                unit=None,
                source=source,
                satellite_platform=platform,
                sensor_instrument=sensor,
                product_type=product,
                latitude=lat,
                longitude=lon,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=optical_quality,
                freshness=freshness,
                confidence=optical_confidence,
                severity="NORMAL",
                notes=f"Ocean optical reflectance classified as '{ocean_col}' ({ocean_col_status}).",
            ))

        # 4. Cloud Cover Assessment
        if cloud_cover is not None:
            cloud_sev = "LOW_QUALITY" if cloud_cover > self.thresholds.CLOUD_OBSCURED_MIN_PERCENT else "NORMAL"
            evidence.append(EarthObservationEvidenceItem(
                factor="cloud_cover",
                value=cloud_cover,
                unit="%",
                source=source,
                satellite_platform=platform,
                sensor_instrument=sensor,
                product_type=product,
                latitude=lat,
                longitude=lon,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=quality,
                freshness=freshness,
                confidence=base_confidence,
                severity=cloud_sev,
                notes=f"Satellite pixel cloud fraction recorded at {cloud_cover}%.",
            ))

        # 5. Solar Radiation
        if solar_rad is not None:
            evidence.append(EarthObservationEvidenceItem(
                factor="solar_radiation",
                value=solar_rad,
                unit="W/m²",
                source=source,
                satellite_platform=platform,
                sensor_instrument=sensor,
                product_type=product,
                latitude=lat,
                longitude=lon,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                data_type=data_type,
                quality=quality,
                freshness=freshness,
                confidence=base_confidence,
                severity="NORMAL",
                notes=f"Downwelling shortwave solar radiation at surface: {solar_rad} W/m².",
            ))

        # -----------------------------------------------------------------
        # Temporal Comparison
        # -----------------------------------------------------------------
        temporal_comp: Optional[EarthObservationTemporalComparison] = None
        if previous_data:
            prev_sst = previous_data.get("sea_surface_temperature_c")
            prev_chl = previous_data.get("chlorophyll_a_mg_m3")
            prev_cloud = previous_data.get("cloud_cover_percent")
            prev_obs_str = previous_data.get("observed_at")
            prev_obs_dt = previous_data.get("observed_at_dt")
            curr_obs_dt = current_data.get("observed_at_dt")

            time_delta = None
            if curr_obs_dt and prev_obs_dt:
                time_delta = round(abs((curr_obs_dt - prev_obs_dt).total_seconds()) / 3600.0, 1)

            sst_diff = None
            sst_trend = "UNKNOWN"
            if sst is not None and prev_sst is not None:
                sst_diff = round(sst - prev_sst, 2)
                if sst_diff > 0.3:
                    sst_trend = "WARMING"
                elif sst_diff < -0.3:
                    sst_trend = "COOLING"
                else:
                    sst_trend = "STABLE"

            chl_diff = None
            chl_trend = "UNKNOWN"
            if chl is not None and prev_chl is not None:
                chl_diff = round(chl - prev_chl, 3)
                if chl_diff > 0.1:
                    chl_trend = "INCREASING"
                elif chl_diff < -0.1:
                    chl_trend = "DECREASING"
                else:
                    chl_trend = "STABLE"

            cloud_diff = None
            cloud_trend = "UNKNOWN"
            if cloud_cover is not None and prev_cloud is not None:
                cloud_diff = round(cloud_cover - prev_cloud, 1)
                if cloud_diff > 5.0:
                    cloud_trend = "INCREASING"
                elif cloud_diff < -5.0:
                    cloud_trend = "DECREASING"
                else:
                    cloud_trend = "STABLE"

            summary_parts = []
            if sst_diff is not None:
                summary_parts.append(f"SST: {sst_trend} ({'+' if sst_diff > 0 else ''}{sst_diff}°C)")
            if chl_diff is not None:
                summary_parts.append(f"Chlorophyll-a: {chl_trend} ({'+' if chl_diff > 0 else ''}{chl_diff} mg/m³)")
            if cloud_diff is not None:
                summary_parts.append(f"Cloud Cover: {cloud_trend} ({'+' if cloud_diff > 0 else ''}{cloud_diff}%)")

            temporal_summary = (
                f"Temporal comparison across {time_delta}h: " + ", ".join(summary_parts)
                if summary_parts else "Temporal delta calculated across available parameters."
            )

            temporal_comp = EarthObservationTemporalComparison(
                has_historical_data=True,
                status="AVAILABLE",
                previous_observed_at=prev_obs_str,
                current_observed_at=observed_at,
                time_delta_hours=time_delta,
                sst_change_c=sst_diff,
                sst_trend=sst_trend,
                chlorophyll_change_mg_m3=chl_diff,
                chlorophyll_trend=chl_trend,
                cloud_cover_change_percent=cloud_diff,
                cloud_cover_trend=cloud_trend,
                summary=temporal_summary,
            )
        else:
            temporal_comp = EarthObservationTemporalComparison(
                has_historical_data=False,
                status="INSUFFICIENT_DATA",
                summary="INSUFFICIENT_DATA: No historical satellite observation available for temporal trend comparison.",
            )

        # -----------------------------------------------------------------
        # Overall Indicators & Narrative Synthesis
        # -----------------------------------------------------------------
        indicators = EarthObservationIndicators(
            sst_status=sst_status,
            chlorophyll_status=chl_status,
            ocean_colour_status=ocean_col_status,
            optical_observability=optical_observability,
            thermal_front_detected=thermal_front_detected,
            chlorophyll_gradient_detected=chl_gradient_detected,
        )

        overall_quality = optical_quality if optical_observability == "CLOUD_OBSCURED" else quality

        # Generate recommendation and explanation
        if chl_status == "FAVORABLE_INDICATOR":
            recommendation = (
                "FAVORABLE BIO-OPTICAL SIGNATURE: Elevated chlorophyll-a concentrations indicate active phytoplankton productivity "
                "in this sector. This serves as an EO-derived ecological indicator contributing to ocean intelligence."
            )
            explanation = (
                f"Satellite telemetry from {source} ({platform or 'Copernicus'}) confirms chlorophyll concentration of {chl} mg/m³ "
                f"with SST at {sst}°C. Optical observability is {optical_observability}."
            )
        elif sst_status == "COOL_UPWELLING":
            recommendation = (
                "THERMAL DIVERGENCE DETECTED: Cooler sea surface temperature indicates potential upwelling dynamics, which often "
                "enhances nutrient circulation in coastal waters."
            )
            explanation = (
                f"SST drop to {sst}°C observed by {platform or source}. Upwelling front detected."
            )
        elif optical_observability == "CLOUD_OBSCURED":
            recommendation = (
                "DEGRADED OPTICAL VISIBILITY: Substantial cloud cover impedes clear surface optical reflectance. "
                "Rely on microwave SST and direct in-situ marine observations."
            )
            explanation = (
                f"Cloud fraction of {cloud_cover}% attenuates optical sensors. Telemetry confidence is adjusted accordingly."
            )
        else:
            recommendation = (
                "STANDARD OCEANOGRAPHIC BASELINE: Earth Observation metrics indicate standard baseline sea surface temperatures "
                "and typical ambient optical characteristics."
            )
            explanation = (
                f"Baseline observations: SST={sst}°C, Chlorophyll-a={chl} mg/m³, Cloud Cover={cloud_cover}%."
            )

        # Strictly clean any accidental certainty or safety guarantee phrasing
        rec_clean = (
            recommendation
            .replace("fish definitely exist here", "favorable bio-optical indicators are observed")
            .replace("guaranteed fishing zone", "elevated productivity zone")
            .replace("100% safe", "manageable under current observations")
            .replace("guaranteed safe", "favorable based on current telemetry")
            .replace("completely safe", "low observable ocean risk")
            .replace("no risk", "low physical risk")
        )
        exp_clean = (
            explanation
            .replace("fish definitely exist here", "favorable bio-optical indicators are observed")
            .replace("guaranteed fishing zone", "elevated productivity zone")
            .replace("100% safe", "manageable under current observations")
            .replace("guaranteed safe", "favorable based on current telemetry")
            .replace("completely safe", "low observable ocean risk")
            .replace("no risk", "low physical risk")
        )

        observations_dict = {
            "sea_surface_temperature_c": sst,
            "chlorophyll_a_mg_m3": chl,
            "ocean_colour": ocean_col,
            "cloud_cover_percent": cloud_cover,
            "solar_radiation_w_m2": solar_rad,
            "satellite_platform": platform,
            "sensor_instrument": sensor,
            "product_type": product,
            "observed_at": observed_at,
            "retrieved_at": retrieved_at,
            "source": source,
            "data_type": data_type,
            "quality_flag": quality,
        }

        # Overall final confidence is the minimum of base_confidence and optical_confidence
        final_confidence = optical_confidence

        return (
            observations_dict,
            indicators,
            temporal_comp,
            overall_quality,
            freshness,
            final_confidence,
            evidence,
            warnings,
            rec_clean,
            exp_clean,
        )
