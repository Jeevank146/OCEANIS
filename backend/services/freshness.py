from datetime import datetime, timezone
from typing import Dict, NamedTuple, Optional

from schemas.marine_provider import DataFreshnessStatus


class FreshnessCategory:
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ThresholdRule(NamedTuple):
    fresh_hours: float
    aging_hours: float
    stale_hours: float


# Parameter- and Provider-specific Freshness Thresholds
PARAMETER_THRESHOLDS: Dict[str, ThresholdRule] = {
    # High frequency in-situ observations (Wave Buoys, Radars)
    "wave_height": ThresholdRule(fresh_hours=1.0, aging_hours=3.0, stale_hours=12.0),
    "wave_period": ThresholdRule(fresh_hours=1.0, aging_hours=3.0, stale_hours=12.0),
    "wave_direction": ThresholdRule(fresh_hours=1.0, aging_hours=3.0, stale_hours=12.0),
    "swell_wave_height": ThresholdRule(fresh_hours=1.0, aging_hours=3.0, stale_hours=12.0),
    "ocean_current_velocity": ThresholdRule(fresh_hours=1.5, aging_hours=4.0, stale_hours=12.0),
    "wind_speed": ThresholdRule(fresh_hours=1.0, aging_hours=3.0, stale_hours=12.0),
    "wind_direction": ThresholdRule(fresh_hours=1.0, aging_hours=3.0, stale_hours=12.0),
    "pressure": ThresholdRule(fresh_hours=1.0, aging_hours=3.0, stale_hours=12.0),
    
    # Official Warnings & Advisories
    "marine_alert": ThresholdRule(fresh_hours=6.0, aging_hours=12.0, stale_hours=24.0),
    "cyclone_track": ThresholdRule(fresh_hours=3.0, aging_hours=6.0, stale_hours=12.0),
    "hazard_zone": ThresholdRule(fresh_hours=12.0, aging_hours=24.0, stale_hours=48.0),

    # Earth Observation / Satellite Passes
    "sea_surface_temperature": ThresholdRule(fresh_hours=12.0, aging_hours=24.0, stale_hours=48.0),
    "chlorophyll_a": ThresholdRule(fresh_hours=24.0, aging_hours=48.0, stale_hours=96.0),
    "ocean_colour": ThresholdRule(fresh_hours=24.0, aging_hours=48.0, stale_hours=96.0),
    "salinity": ThresholdRule(fresh_hours=24.0, aging_hours=48.0, stale_hours=96.0),
    "sea_level_anomaly": ThresholdRule(fresh_hours=24.0, aging_hours=48.0, stale_hours=96.0),
}

DEFAULT_MODEL_THRESHOLD = ThresholdRule(fresh_hours=3.0, aging_hours=6.0, stale_hours=24.0)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensures datetime is timezone-aware in UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def evaluate_freshness(
    timestamp: Optional[datetime],
    effective_until: Optional[datetime] = None,
    current_time: Optional[datetime] = None,
    fresh_hours_threshold: float = 6.0,
    aging_hours_threshold: float = 24.0,
    stale_hours_threshold: float = 72.0,
) -> str:
    """
    Evaluates data freshness deterministically without inventing timestamps.
    Backward-compatible implementation.
    """
    now = ensure_utc(current_time or datetime.now(timezone.utc))

    effective_until_utc = ensure_utc(effective_until)
    if effective_until_utc is not None and effective_until_utc < now:
        return FreshnessCategory.EXPIRED

    ts_utc = ensure_utc(timestamp)
    if ts_utc is None:
        return FreshnessCategory.UNKNOWN

    age_seconds = (now - ts_utc).total_seconds()
    if age_seconds < 0:
        # Timestamp is in the future (forecast data)
        return FreshnessCategory.FRESH

    age_hours = age_seconds / 3600.0

    if age_hours <= fresh_hours_threshold:
        return FreshnessCategory.FRESH
    elif age_hours <= aging_hours_threshold:
        return FreshnessCategory.AGING
    elif age_hours <= stale_hours_threshold:
        return FreshnessCategory.STALE
    else:
        return FreshnessCategory.EXPIRED


def evaluate_parameter_freshness(
    timestamp: Optional[datetime],
    parameter: Optional[str] = None,
    provider: Optional[str] = None,
    effective_until: Optional[datetime] = None,
    current_time: Optional[datetime] = None,
) -> DataFreshnessStatus:
    """
    Evaluates parameter-specific data freshness according to parameter rules.
    """
    if timestamp is None:
        return DataFreshnessStatus.UNAVAILABLE

    rule = PARAMETER_THRESHOLDS.get(parameter, DEFAULT_MODEL_THRESHOLD) if parameter else DEFAULT_MODEL_THRESHOLD
    
    # Provider-specific override: In-situ buoy data ages faster
    if provider and "INCOIS" in provider.upper() and parameter in ("wave_height", "wave_period"):
        rule = ThresholdRule(fresh_hours=1.0, aging_hours=2.0, stale_hours=6.0)

    category = evaluate_freshness(
        timestamp=timestamp,
        effective_until=effective_until,
        current_time=current_time,
        fresh_hours_threshold=rule.fresh_hours,
        aging_hours_threshold=rule.aging_hours,
        stale_hours_threshold=rule.stale_hours,
    )

    if category == FreshnessCategory.FRESH:
        return DataFreshnessStatus.FRESH
    elif category == FreshnessCategory.AGING:
        return DataFreshnessStatus.AGING
    elif category == FreshnessCategory.STALE:
        return DataFreshnessStatus.STALE
    elif category == FreshnessCategory.EXPIRED:
        return DataFreshnessStatus.EXPIRED
    else:
        return DataFreshnessStatus.UNAVAILABLE


def is_record_expired(
    effective_until: Optional[datetime],
    current_time: Optional[datetime] = None,
) -> bool:
    """
    Returns True if an effective_until timestamp exists and is prior to current_time.
    """
    if effective_until is None:
        return False
    now = ensure_utc(current_time or datetime.now(timezone.utc))
    effective_until_utc = ensure_utc(effective_until)
    return effective_until_utc < now
