from datetime import datetime, timedelta, timezone
import json
import math
import uuid
from typing import Any, Dict, List, Optional, Tuple

from geoalchemy2 import Geography
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models.disaster import CycloneTrack, HazardZone, MarineAlert
from models.geospatial import Port, ProtectedZone, RestrictedZone
from models.marine import MarineObservation
from models.marine_operations import MarineOperation
from models.weather import WeatherObservation
from services.disaster import DisasterService
from services.freshness import FreshnessCategory, ensure_utc, evaluate_freshness
from services.geospatial import GeoSpatialService, haversine_distance, km_to_nautical_miles
from services.navigation import NavigationService


class MarineOperationsService:
    """
    Core service layer for Marine Operations:
    Trip planning, distance/duration estimation, route constraint analysis,
    and deterministic operational safety assessments combining Geo-Spatial,
    Disaster & Safety, Weather, and Marine Conditions data.
    """

    @staticmethod
    def calculate_distance(
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> Dict[str, Any]:
        """
        Calculates geodesic distance between origin and destination.
        """
        dist_km = round(haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon), 2)
        dist_nm = round(km_to_nautical_miles(dist_km), 2)
        return {
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "destination": {"latitude": dest_lat, "longitude": dest_lon},
            "distance_km": dist_km,
            "distance_nautical_miles": dist_nm,
            "calculation_method": "HAVERSINE_GEODESIC",
        }

    @staticmethod
    def estimate_duration(
        distance_km: float,
        speed_kmh: Optional[float],
    ) -> Optional[float]:
        """
        Estimates transit duration in minutes given distance (km) and speed (km/h).
        Returns None if speed is missing or invalid.
        """
        if speed_kmh is None or speed_kmh <= 0:
            return None
        return round((distance_km / speed_kmh) * 60.0, 2)

    @staticmethod
    def generate_operation_id() -> str:
        """
        Generates a unique human-readable operational tracking identifier.
        """
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:6].upper()
        return f"OP_{date_str}_{unique_suffix}"

    @staticmethod
    def create_operation(
        db: Session,
        operation_data: Dict[str, Any],
    ) -> MarineOperation:
        """
        Creates and persists a new marine operation.
        """
        orig_lat = operation_data["origin_latitude"]
        orig_lon = operation_data["origin_longitude"]
        dest_lat = operation_data["destination_latitude"]
        dest_lon = operation_data["destination_longitude"]
        speed = operation_data.get("estimated_speed_kmh")

        dist_km = round(haversine_distance(orig_lat, orig_lon, dest_lat, dest_lon), 2)
        duration_min = MarineOperationsService.estimate_duration(dist_km, speed)

        op_id = operation_data.get("operation_id") or MarineOperationsService.generate_operation_id()

        operation = MarineOperation(
            operation_id=op_id,
            operation_type=operation_data.get("operation_type", "TRANSIT"),
            vessel_type=operation_data.get("vessel_type", "FISHING_VESSEL"),
            vessel_name=operation_data.get("vessel_name"),
            origin_latitude=orig_lat,
            origin_longitude=orig_lon,
            destination_latitude=dest_lat,
            destination_longitude=dest_lon,
            planned_departure_at=operation_data.get("planned_departure_at"),
            estimated_speed_kmh=speed,
            estimated_distance_km=dist_km,
            estimated_duration_minutes=duration_min,
            operational_status=operation_data.get("operational_status", "PLANNED"),
            notes=operation_data.get("notes"),
            source=operation_data.get("source", "MANUAL_INPUT"),
            data_type=operation_data.get("data_type", "PLANNED"),
        )
        db.add(operation)
        db.commit()
        db.refresh(operation)
        return operation

    @staticmethod
    def get_operations(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        operation_type: Optional[str] = None,
        operational_status: Optional[str] = None,
    ) -> List[MarineOperation]:
        """
        Retrieves paginated marine operations with optional filters.
        """
        query = db.query(MarineOperation)
        if operation_type:
            query = query.filter(MarineOperation.operation_type == operation_type)
        if operational_status:
            query = query.filter(MarineOperation.operational_status == operational_status)
        return query.order_by(MarineOperation.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_operation_by_id(
        db: Session,
        operation_id: str,
    ) -> Optional[MarineOperation]:
        """
        Retrieves a single operation by its operation_id string.
        """
        return db.query(MarineOperation).filter(MarineOperation.operation_id == operation_id).first()

    @staticmethod
    def update_operation(
        db: Session,
        operation_id: str,
        update_data: Dict[str, Any],
    ) -> Optional[MarineOperation]:
        """
        Updates an existing operation and recalculates distance/duration if coordinates or speed changed.
        """
        operation = db.query(MarineOperation).filter(MarineOperation.operation_id == operation_id).first()
        if not operation:
            return None

        # Apply updates
        coords_changed = False
        for field, value in update_data.items():
            if value is not None and hasattr(operation, field):
                setattr(operation, field, value)
                if field in ("origin_latitude", "origin_longitude", "destination_latitude", "destination_longitude", "estimated_speed_kmh"):
                    coords_changed = True

        if coords_changed:
            dist_km = round(haversine_distance(
                operation.origin_latitude,
                operation.origin_longitude,
                operation.destination_latitude,
                operation.destination_longitude,
            ), 2)
            operation.estimated_distance_km = dist_km
            operation.estimated_duration_minutes = MarineOperationsService.estimate_duration(
                dist_km,
                operation.estimated_speed_kmh,
            )

        db.commit()
        db.refresh(operation)
        return operation

    @staticmethod
    def assess_operation(
        db: Session,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        speed_kmh: Optional[float] = None,
        operation_id: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic operational assessment combining Geo-Spatial, Disaster & Safety,
        Weather, and Marine Conditions layers.
        """
        current_time = now or datetime.now(timezone.utc)
        reasons: List[str] = []
        evidence: List[Dict[str, Any]] = []

        # 1. Distance and Duration
        dist_res = MarineOperationsService.calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        dist_km = dist_res["distance_km"]
        dist_nm = dist_res["distance_nautical_miles"]
        duration_min = MarineOperationsService.estimate_duration(dist_km, speed_kmh)

        # 2. Geo-Spatial Navigation Assessment (Restricted & Protected Zones)
        nav_res = NavigationService.assess_route(db, origin_lat, origin_lon, dest_lat, dest_lon)

        # 3. PostGIS Route Line Geometry for Hazard Zone Intersections
        orig_pt = func.ST_SetSRID(func.ST_MakePoint(origin_lon, origin_lat), 4326)
        dest_pt = func.ST_SetSRID(func.ST_MakePoint(dest_lon, dest_lat), 4326)
        line_geom = func.ST_MakeLine(orig_pt, dest_pt)

        # Query active Hazard Zones intersecting the navigation line
        intersecting_hazards = (
            db.query(HazardZone)
            .filter(HazardZone.is_active.is_(True))
            .filter(
                or_(
                    HazardZone.effective_until.is_(None),
                    HazardZone.effective_until >= current_time,
                )
            )
            .filter(
                or_(
                    func.ST_Intersects(HazardZone.geometry, line_geom),
                    func.ST_Contains(HazardZone.geometry, orig_pt),
                    func.ST_Contains(HazardZone.geometry, dest_pt),
                )
            )
            .all()
        )

        hazard_intersect = len(intersecting_hazards) > 0
        hazard_names = [f"{h.name} ({h.hazard_type}, {h.severity})" for h in intersecting_hazards]

        route_assessment_payload = {
            "navigation_status": nav_res["navigation_status"],
            "restricted_zone_intersection": nav_res["restricted_zone_intersection"],
            "protected_zone_intersection": nav_res["protected_zone_intersection"],
            "hazard_intersection": hazard_intersect,
            "origin_in_restricted_zone": nav_res["origin_in_restricted_zone"],
            "destination_in_restricted_zone": nav_res["destination_in_restricted_zone"],
            "origin_in_protected_zone": nav_res["origin_in_protected_zone"],
            "destination_in_protected_zone": nav_res["destination_in_protected_zone"],
            "intersecting_restricted_zones": nav_res["intersecting_restricted_zones"],
            "intersecting_protected_zones": nav_res["intersecting_protected_zones"],
            "intersecting_hazard_zones": hazard_names,
        }

        # 4. Disaster & Safety Alerts in Proximity (origin, destination, midpoint)
        mid_lat = (origin_lat + dest_lat) / 2.0
        mid_lon = (origin_lon + dest_lon) / 2.0
        search_radius = max(dist_km / 2.0, 50.0)

        active_alerts = DisasterService.get_alerts(
            db=db,
            latitude=mid_lat,
            longitude=mid_lon,
            radius_km=min(search_radius, 500.0),
            active_only=True,
            now=current_time,
        )

        # 5. Nearby Cyclone Activity
        cyclones = DisasterService.get_cyclone_tracks(
            db=db,
            latitude=mid_lat,
            longitude=mid_lon,
            radius_km=max(search_radius, 300.0),
            active_only=True,
            now=current_time,
        )

        # 6. Safe Port Refuges
        nearest_ports_orig = GeoSpatialService.get_nearby_ports(db, origin_lat, origin_lon, radius_km=300.0, active_only=True)
        nearest_ports_dest = GeoSpatialService.get_nearby_ports(db, dest_lat, dest_lon, radius_km=300.0, active_only=True)
        combined_ports = {p["id"]: p for p in (nearest_ports_orig[:2] + nearest_ports_dest[:2])}
        safe_ports_list = list(combined_ports.values())

        # 7. Marine Conditions & Weather Telemetry (Near Origin and Destination)
        marine_payload = None
        weather_payload = None
        freshness_audit: Dict[str, Any] = {}

        # Marine check
        orig_geog = func.cast(orig_pt, Geography)
        marine_geom = func.ST_SetSRID(func.ST_MakePoint(MarineObservation.longitude, MarineObservation.latitude), 4326)
        latest_marine = (
            db.query(MarineObservation)
            .filter(func.ST_DWithin(func.cast(marine_geom, Geography), orig_geog, 100000.0))
            .order_by(MarineObservation.observed_at.desc())
            .first()
        )
        if latest_marine:
            marine_freshness = evaluate_freshness(latest_marine.observed_at, current_time=current_time)
            freshness_audit["marine_conditions"] = marine_freshness
            marine_payload = {
                "wave_height_m": latest_marine.wave_height_m,
                "wave_period_s": latest_marine.wave_period_s,
                "swell_wave_height_m": latest_marine.swell_wave_height_m,
                "ocean_current_velocity_kmh": latest_marine.ocean_current_velocity_kmh,
                "sea_surface_temperature_c": latest_marine.sea_surface_temperature_c,
                "observed_at": latest_marine.observed_at.isoformat(),
                "source": latest_marine.source,
                "freshness": marine_freshness,
            }
            evidence.append({
                "source": latest_marine.source,
                "source_type": "OBSERVATION",
                "timestamp": latest_marine.observed_at.isoformat(),
                "metric": f"Wave Height: {latest_marine.wave_height_m}m, Swell: {latest_marine.swell_wave_height_m}m",
            })
        else:
            freshness_audit["marine_conditions"] = FreshnessCategory.UNKNOWN

        # Weather check
        weather_geom = func.ST_SetSRID(func.ST_MakePoint(WeatherObservation.longitude, WeatherObservation.latitude), 4326)
        latest_weather = (
            db.query(WeatherObservation)
            .filter(func.ST_DWithin(func.cast(weather_geom, Geography), orig_geog, 100000.0))
            .order_by(WeatherObservation.observed_at.desc())
            .first()
        )
        if latest_weather:
            weather_freshness = evaluate_freshness(latest_weather.observed_at, current_time=current_time)
            freshness_audit["weather_conditions"] = weather_freshness
            weather_payload = {
                "temperature_c": latest_weather.temperature_c,
                "wind_speed_kmh": latest_weather.wind_speed_kmh,
                "wind_direction_deg": latest_weather.wind_direction_deg,
                "precipitation_mm": latest_weather.precipitation_mm,
                "observed_at": latest_weather.observed_at.isoformat(),
                "source": latest_weather.source,
                "freshness": weather_freshness,
            }
            evidence.append({
                "source": latest_weather.source,
                "source_type": "OBSERVATION",
                "timestamp": latest_weather.observed_at.isoformat(),
                "metric": f"Wind Speed: {latest_weather.wind_speed_kmh} km/h, Temp: {latest_weather.temperature_c}°C",
            })
        else:
            freshness_audit["weather_conditions"] = FreshnessCategory.UNKNOWN

        # 8. Deterministic Operational Decision Rules
        # Severity hierarchy: BLOCKED > WARNING > CAUTION > INSUFFICIENT_DATA > ASSESSED
        is_blocked = False
        is_warning = False
        is_caution = False

        # Rule 1: Restricted Zone Intersection -> BLOCKED
        if nav_res["restricted_zone_intersection"] or nav_res["origin_in_restricted_zone"] or nav_res["destination_in_restricted_zone"]:
            is_blocked = True
            reasons.extend(nav_res["reasons"])

        # Rule 2: Critical alerts affecting route -> BLOCKED
        for alert in active_alerts:
            sev = alert.get("severity", "").upper()
            title = alert.get("title", "")
            source = alert.get("source", "Official")
            evidence.append({
                "source": source,
                "source_type": alert.get("source_category", "OFFICIAL"),
                "timestamp": alert.get("issued_at").isoformat() if hasattr(alert.get("issued_at"), "isoformat") else str(alert.get("issued_at")),
                "metric": f"Alert {alert.get('alert_type')} ({sev})",
            })
            if sev == "CRITICAL":
                is_blocked = True
                reasons.append(f"Operation blocked by active CRITICAL safety advisory: {title} ({source}).")
            elif sev == "WARNING":
                is_warning = True
                reasons.append(f"Active WARNING along operational corridor: {title} ({source}).")
            elif sev in ("CAUTION", "INFO"):
                is_caution = True
                reasons.append(f"Active CAUTION advisory in operational sector: {title} ({source}).")

        # Rule 3: Hazard Zone Intersections
        for hz in intersecting_hazards:
            sev = hz.severity.upper()
            evidence.append({
                "source": hz.source,
                "source_type": hz.source_category,
                "timestamp": hz.created_at.isoformat(),
                "metric": f"Hazard {hz.hazard_type} ({sev})",
            })
            if sev == "CRITICAL":
                is_blocked = True
                reasons.append(f"Route path intersects critical hazard zone: '{hz.name}' ({hz.hazard_type}).")
            elif sev == "WARNING":
                is_warning = True
                reasons.append(f"Route path intersects active warning hazard zone: '{hz.name}' ({hz.hazard_type}).")
            else:
                is_caution = True
                reasons.append(f"Route path traverses caution hazard zone: '{hz.name}' ({hz.hazard_type}).")

        # Rule 4: Protected Zone Intersections -> CAUTION
        if nav_res["protected_zone_intersection"] or nav_res["origin_in_protected_zone"] or nav_res["destination_in_protected_zone"]:
            if not is_blocked:
                is_caution = True
                reasons.extend([r for r in nav_res["reasons"] if "marine protected" in r.lower()])

        # Rule 5: Cyclone proximity
        for cyc in cyclones:
            dist = cyc.get("distance_km", 999.0)
            c_name = cyc.get("name", "Unnamed")
            c_class = cyc.get("classification", "CYCLONIC_STORM")
            evidence.append({
                "source": cyc.get("source", "IMD"),
                "source_type": cyc.get("source_category", "OFFICIAL"),
                "timestamp": cyc.get("observed_at").isoformat() if hasattr(cyc.get("observed_at"), "isoformat") else str(cyc.get("observed_at")),
                "metric": f"Cyclone {c_name} ({c_class}) at {dist}km",
            })
            if dist <= 150.0:
                is_blocked = True
                reasons.append(f"Severe cyclone danger: '{c_name}' ({c_class}) positioned {dist} km from route corridor.")
            elif dist <= 300.0:
                is_warning = True
                reasons.append(f"Cyclone warning: '{c_name}' ({c_class}) located within {dist} km of operational sector.")

        # Rule 6: Weather & Marine threshold checks
        if latest_marine and latest_marine.wave_height_m and latest_marine.wave_height_m >= 3.5:
            is_warning = True
            reasons.append(f"Adverse sea state: observed wave height of {latest_marine.wave_height_m}m exceeds safe operational limits.")

        if latest_weather and latest_weather.wind_speed_kmh and latest_weather.wind_speed_kmh >= 55.0:
            is_warning = True
            reasons.append(f"High wind warning: sustained wind speed of {latest_weather.wind_speed_kmh} km/h detected.")

        # Evaluate Final Operational Status & Confidence
        has_fresh_telemetry = (
            freshness_audit.get("marine_conditions") in (FreshnessCategory.FRESH, FreshnessCategory.AGING)
            or freshness_audit.get("weather_conditions") in (FreshnessCategory.FRESH, FreshnessCategory.AGING)
        )

        if is_blocked:
            operational_status = "BLOCKED"
            confidence = "HIGH"
        elif is_warning:
            operational_status = "WARNING"
            confidence = "HIGH"
        elif is_caution:
            operational_status = "CAUTION"
            confidence = "HIGH" if has_fresh_telemetry else "MEDIUM"
        else:
            # Zero hazards found
            if not has_fresh_telemetry:
                operational_status = "INSUFFICIENT_DATA"
                confidence = "LOW"
                reasons.append(
                    "No active regulatory restrictions or emergency alerts recorded, but verified ocean telemetry "
                    "coverage is missing or unverified for this corridor. Cannot confirm operational readiness."
                )
            else:
                operational_status = "ASSESSED"
                confidence = "HIGH"
                reasons.append(
                    f"Direct navigation corridor ({dist_km} km) assessed against active spatial zones and telemetry. "
                    "Conditions meet standard operational thresholds. Vessel master retains ultimate navigational command."
                )

        if duration_min is None:
            reasons.append("Transit duration estimation unavailable because vessel cruising speed was not specified.")

        return {
            "operation_id": operation_id,
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "destination": {"latitude": dest_lat, "longitude": dest_lon},
            "distance_km": dist_km,
            "distance_nautical_miles": dist_nm,
            "estimated_speed_kmh": speed_kmh,
            "estimated_duration_minutes": duration_min,
            "route_assessment": route_assessment_payload,
            "marine_conditions": marine_payload,
            "weather_conditions": weather_payload,
            "active_alerts": active_alerts,
            "cyclone_activity": cyclones,
            "nearest_safe_ports": safe_ports_list,
            "operational_status": operational_status,
            "data_freshness": freshness_audit,
            "confidence": confidence,
            "reasons": reasons,
            "evidence": evidence,
            "assessment_timestamp": current_time,
        }

    @staticmethod
    def assess_departure(
        db: Session,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_at: datetime,
        speed_kmh: Optional[float] = None,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates planned departure timing against temporal warnings, forecast validity windows,
        and operational route constraints.
        """
        current_time = now or datetime.now(timezone.utc)
        dist_res = MarineOperationsService.calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        dist_km = dist_res["distance_km"]
        dist_nm = dist_res["distance_nautical_miles"]
        duration_min = MarineOperationsService.estimate_duration(dist_km, speed_kmh)

        arrival_at = None
        if duration_min is not None:
            arrival_at = departure_at + timedelta(minutes=duration_min)

        # Base operational assessment
        base_assessment = MarineOperationsService.assess_operation(
            db=db,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
            speed_kmh=speed_kmh,
            now=current_time,
        )

        warnings: List[str] = []
        dep_reasons: List[str] = list(base_assessment["reasons"])

        # Check if departure time is in the past
        dep_utc = ensure_utc(departure_at)
        now_utc = ensure_utc(current_time)

        if dep_utc and now_utc and dep_utc < now_utc - timedelta(minutes=10):
            warnings.append(f"Departure time '{departure_at.isoformat()}' is in the past.")

        # Temporal check against active alerts effective windows
        for alert in base_assessment["active_alerts"]:
            eff_until_utc = ensure_utc(alert.get("effective_until"))
            if eff_until_utc and dep_utc and dep_utc <= eff_until_utc:
                warnings.append(
                    f"Planned departure overlaps with active alert: '{alert.get('title')}' (effective until {eff_until_utc})."
                )

        status = base_assessment["operational_status"]
        if warnings and status == "ASSESSED":
            status = "CAUTION"

        overall_freshness = "FRESH" if base_assessment["confidence"] == "HIGH" else "INSUFFICIENT_DATA"

        return {
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "destination": {"latitude": dest_lat, "longitude": dest_lon},
            "departure_at": departure_at,
            "estimated_arrival_at": arrival_at,
            "distance_km": dist_km,
            "distance_nautical_miles": dist_nm,
            "estimated_speed_kmh": speed_kmh,
            "estimated_duration_minutes": duration_min,
            "operational_status": status,
            "route_assessment": base_assessment["route_assessment"],
            "marine_conditions": base_assessment["marine_conditions"],
            "weather_conditions": base_assessment["weather_conditions"],
            "active_alerts": base_assessment["active_alerts"],
            "warnings": warnings,
            "reasons": dep_reasons,
            "confidence": base_assessment["confidence"],
            "data_freshness": overall_freshness,
            "assessment_timestamp": current_time,
        }
