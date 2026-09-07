import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from schemas.marine_provider import (
    DataQualityStatus,
    NormalizedMarineRecord,
)

logger = logging.getLogger(__name__)


class PhysicalRange:
    def __init__(self, min_val: float, max_val: float, standard_unit: str, description: str):
        self.min_val = min_val
        self.max_val = max_val
        self.standard_unit = standard_unit
        self.description = description

    def is_valid(self, value: float) -> bool:
        return self.min_val <= value <= self.max_val


# Comprehensive Physical Validation Boundaries
PHYSICAL_BOUNDS: Dict[str, PhysicalRange] = {
    # Ocean Physics
    "wave_height": PhysicalRange(0.0, 30.0, "m", "Significant wave height"),
    "wave_direction": PhysicalRange(0.0, 360.0, "deg", "Mean wave direction"),
    "wave_period": PhysicalRange(0.0, 35.0, "s", "Peak wave period"),
    "swell_wave_height": PhysicalRange(0.0, 30.0, "m", "Swell wave height"),
    "swell_wave_direction": PhysicalRange(0.0, 360.0, "deg", "Swell wave direction"),
    "swell_wave_period": PhysicalRange(0.0, 35.0, "s", "Swell wave period"),
    "wind_wave_height": PhysicalRange(0.0, 25.0, "m", "Wind wave height"),
    "wind_wave_direction": PhysicalRange(0.0, 360.0, "deg", "Wind wave direction"),
    "wind_wave_period": PhysicalRange(0.0, 30.0, "s", "Wind wave period"),
    "ocean_current_velocity": PhysicalRange(0.0, 25.0, "km/h", "Ocean current speed"),
    "ocean_current_direction": PhysicalRange(0.0, 360.0, "deg", "Ocean current direction"),
    "sea_surface_temperature": PhysicalRange(-2.0, 45.0, "C", "Sea surface temperature"),
    "salinity": PhysicalRange(0.0, 50.0, "PSU", "Practical salinity unit"),
    "sea_level_anomaly": PhysicalRange(-5.0, 5.0, "m", "Sea level anomaly"),

    # Atmosphere / Weather
    "wind_speed": PhysicalRange(0.0, 350.0, "km/h", "Sustained wind speed"),
    "wind_gust": PhysicalRange(0.0, 400.0, "km/h", "Peak wind gust"),
    "wind_direction": PhysicalRange(0.0, 360.0, "deg", "Wind azimuth"),
    "temperature": PhysicalRange(-50.0, 60.0, "C", "Ambient air temperature"),
    "relative_humidity": PhysicalRange(0.0, 100.0, "%", "Relative atmospheric humidity"),
    "precipitation": PhysicalRange(0.0, 500.0, "mm", "Precipitation rate"),
    "pressure": PhysicalRange(850.0, 1085.0, "hPa", "Barometric pressure"),
    "visibility": PhysicalRange(0.0, 100.0, "km", "Atmospheric visibility"),

    # Earth Observation / Bio-optics
    "chlorophyll_a": PhysicalRange(0.0, 100.0, "mg/m3", "Chlorophyll-a concentration"),
    "cloud_cover_percent": PhysicalRange(0.0, 100.0, "%", "Cloud cover fraction"),
    "solar_radiation_w_m2": PhysicalRange(0.0, 1500.0, "W/m2", "Downwelling solar irradiance"),
}


class DataValidator:
    """
    Strict validation gate for all incoming oceanographic, meteorological,
    and satellite observations before normalization, DB storage, or agent consumption.
    """

    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> Tuple[bool, Optional[str]]:
        """
        Validates that coordinates are within valid geographic bounds.
        """
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return False, f"Coordinates must be numeric. Received lat={type(latitude)}, lon={type(longitude)}."

        if not (-90.0 <= latitude <= 90.0):
            return False, f"Latitude {latitude} out of valid bounds [-90.0, 90.0]."

        if not (-180.0 <= longitude <= 180.0):
            return False, f"Longitude {longitude} out of valid bounds [-180.0, 180.0]."

        return True, None

    @staticmethod
    def validate_numerical_range(
        parameter: str,
        value: Optional[float],
        unit: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates numerical value against known physical limits.
        """
        if value is None:
            return True, None  # Null values handled separately

        if not isinstance(value, (int, float)):
            return False, f"Parameter '{parameter}' value must be numeric. Got {type(value)}: {value}"

        num_val = float(value)

        # Check NaN or Inf
        if num_val != num_val or num_val == float("inf") or num_val == float("-inf"):
            return False, f"Parameter '{parameter}' contains invalid numerical value: {value}"

        bounds = PHYSICAL_BOUNDS.get(parameter)
        if bounds:
            if not bounds.is_valid(num_val):
                return False, (
                    f"Physical range violation for '{parameter}': {num_val} {unit or bounds.standard_unit} "
                    f"is outside valid physical limits [{bounds.min_val}, {bounds.max_val} {bounds.standard_unit}]."
                )

        return True, None

    @staticmethod
    def validate_timestamp(
        timestamp_str: str,
        max_age_days: float = 30.0,
        max_future_days: float = 16.0,
    ) -> Tuple[bool, Optional[datetime], Optional[str]]:
        """
        Validates ISO 8601 timestamp string and ensures it's within plausible time window.
        """
        if not timestamp_str or not isinstance(timestamp_str, str):
            return False, None, f"Timestamp must be a non-empty string. Got: {timestamp_str}"

        try:
            cleaned_str = timestamp_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)

            now = datetime.now(timezone.utc)
            oldest_allowed = now - timedelta(days=max_age_days)
            furthest_allowed = now + timedelta(days=max_future_days)

            if dt < oldest_allowed:
                return False, dt, f"Timestamp {timestamp_str} is older than {max_age_days} days."
            if dt > furthest_allowed:
                return False, dt, f"Timestamp {timestamp_str} is further than {max_future_days} days into future."

            return True, dt, None

        except Exception as exc:
            return False, None, f"Invalid ISO 8601 timestamp format '{timestamp_str}': {str(exc)}"

    @classmethod
    def validate_record(cls, record: NormalizedMarineRecord) -> Tuple[bool, Optional[str]]:
        """
        Full record validation check.
        """
        # 1. Validate coordinates
        coord_valid, coord_err = cls.validate_coordinates(record.latitude, record.longitude)
        if not coord_valid:
            logger.warning(f"Record validation failed on coordinates: {coord_err}")
            return False, coord_err

        # 2. Validate value & physical bounds
        if record.value is not None:
            range_valid, range_err = cls.validate_numerical_range(
                record.parameter, record.value, record.unit
            )
            if not range_valid:
                logger.warning(f"Record validation failed on physical bounds: {range_err}")
                return False, range_err

        # 3. Validate timestamps
        valid_time_ok, _, valid_time_err = cls.validate_timestamp(record.valid_time)
        if not valid_time_ok:
            logger.warning(f"Record validation failed on valid_time: {valid_time_err}")
            return False, valid_time_err

        retrieved_time_ok, _, retrieved_time_err = cls.validate_timestamp(record.retrieved_at)
        if not retrieved_time_ok:
            logger.warning(f"Record validation failed on retrieved_at: {retrieved_time_err}")
            return False, retrieved_time_err

        # 4. Validate source
        if not record.source or not record.source.strip():
            return False, "Record must have a non-empty source attribution."

        return True, None

    @classmethod
    def filter_and_validate_records(
        cls,
        records: List[NormalizedMarineRecord],
    ) -> Tuple[List[NormalizedMarineRecord], List[Tuple[NormalizedMarineRecord, str]]]:
        """
        Filters a list of records into valid records and rejected records with error reasons.
        """
        valid: List[NormalizedMarineRecord] = []
        rejected: List[Tuple[NormalizedMarineRecord, str]] = []

        for rec in records:
            is_valid, err_msg = cls.validate_record(rec)
            if is_valid:
                rec.quality_status = DataQualityStatus.VALIDATED
                valid.append(rec)
            else:
                rec.quality_status = DataQualityStatus.REJECTED
                rejected.append((rec, err_msg or "Validation failed"))

        return valid, rejected
