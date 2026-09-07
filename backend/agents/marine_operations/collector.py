from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from geoalchemy2 import Geography
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from agents.marine_operations.schemas import (
    OperationalEvidenceItem,
    RouteOperationalSummary,
)
from models.disaster import CycloneTrack, HazardZone, MarineAlert
from models.geospatial import Port, ProtectedZone, RestrictedZone
from models.marine import MarineObservation
from models.weather import WeatherObservation
from services.disaster import DisasterService
from services.freshness import FreshnessCategory, evaluate_freshness
from services.geospatial import GeoSpatialService, haversine_distance, km_to_nautical_miles
from services.navigation import NavigationService


class MarineOperationsDataCollector:
    """
    Data Collector for Marine Operations Intelligence Agent.
    Collects route distances, estimated durations, PostGIS regulatory & hazard zone
    intersections, active disaster alerts, cyclone tracks, safe harbors, and marine/weather telemetry.
    """

    def collect(
        self,
        db: Session,
        origin_latitude: float,
        origin_longitude: float,
        destination_latitude: float,
        destination_longitude: float,
        speed_kmh: Optional[float] = 20.0,
        planned_departure_at: Optional[str] = None,
        operation_type: str = "TRANSIT",
        vessel_type: str = "FISHING_VESSEL",
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Gathers multi-domain operational data for transit between origin and destination coordinates.
        """
        current_time = now or datetime.now(timezone.utc)

        # 1. Geodesic distance calculation
        dist_km = round(haversine_distance(origin_latitude, origin_longitude, destination_latitude, destination_longitude), 2)
        dist_nm = round(km_to_nautical_miles(dist_km), 2)

        # 2. Duration and schedule estimation
        duration_minutes: Optional[float] = None
        duration_hours: Optional[float] = None
        departure_dt: Optional[datetime] = None
        estimated_arrival_dt: Optional[datetime] = None

        if speed_kmh and speed_kmh > 0:
            duration_minutes = round((dist_km / speed_kmh) * 60.0, 2)
            duration_hours = round(dist_km / speed_kmh, 2)

        if planned_departure_at:
            try:
                departure_dt = datetime.fromisoformat(planned_departure_at.replace("Z", "+00:00"))
                if duration_minutes is not None:
                    estimated_arrival_dt = departure_dt + timedelta(minutes=duration_minutes)
            except Exception:
                pass
        else:
            departure_dt = current_time
            if duration_minutes is not None:
                estimated_arrival_dt = departure_dt + timedelta(minutes=duration_minutes)

        # 3. PostGIS Navigation Assessment (Restricted & Protected Zones)
        nav_res = NavigationService.assess_route(
            db=db,
            origin_lat=origin_latitude,
            origin_lon=origin_longitude,
            dest_lat=destination_latitude,
            dest_lon=destination_longitude,
        )

        # 4. PostGIS Line Geometry for Hazard Zone Intersections
        orig_pt = func.ST_SetSRID(func.ST_MakePoint(origin_longitude, origin_latitude), 4326)
        dest_pt = func.ST_SetSRID(func.ST_MakePoint(destination_longitude, destination_latitude), 4326)
        line_geom = func.ST_MakeLine(orig_pt, dest_pt)

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

        # Alternative route logic
        alt_available = False
        alt_suggestion = None
        if nav_res["restricted_zone_intersection"] or nav_res["protected_zone_intersection"] or hazard_intersect:
            alt_available = True
            if nav_res["restricted_zone_intersection"]:
                alt_suggestion = "Establish offshore waypoint clearance skirting designated military/naval exclusion boundaries."
            elif hazard_intersect:
                alt_suggestion = "Establish coastal detour route around designated surge/inundation hazard sectors."
            else:
                alt_suggestion = "Route via verified marine corridor avoiding protected sanctuary core zone."

        route_summary = RouteOperationalSummary(
            distance_km=dist_km,
            distance_nautical_miles=dist_nm,
            speed_kmh=speed_kmh,
            estimated_duration_minutes=duration_minutes,
            estimated_duration_hours=duration_hours,
            planned_departure_at=departure_dt.isoformat() if departure_dt else None,
            estimated_arrival_at=estimated_arrival_dt.isoformat() if estimated_arrival_dt else None,
            restricted_zone_intersection=nav_res["restricted_zone_intersection"],
            protected_zone_intersection=nav_res["protected_zone_intersection"],
            hazard_zone_intersection=hazard_intersect,
            origin_in_restricted_zone=nav_res["origin_in_restricted_zone"],
            destination_in_restricted_zone=nav_res["destination_in_restricted_zone"],
            origin_in_protected_zone=nav_res["origin_in_protected_zone"],
            destination_in_protected_zone=nav_res["destination_in_protected_zone"],
            intersecting_restricted_zones=nav_res["intersecting_restricted_zones"],
            intersecting_protected_zones=nav_res["intersecting_protected_zones"],
            intersecting_hazard_zones=hazard_names,
            alternative_route_available=alt_available,
            alternative_route_suggestion=alt_suggestion,
        )

        # 5. Disaster Alerts & Cyclones along Route Corridor
        mid_lat = (origin_latitude + destination_latitude) / 2.0
        mid_lon = (origin_longitude + destination_longitude) / 2.0
        search_radius = max(dist_km / 2.0, 50.0)

        active_alerts = DisasterService.get_alerts(
            db=db,
            latitude=mid_lat,
            longitude=mid_lon,
            radius_km=min(search_radius, 500.0),
            active_only=True,
            now=current_time,
        )

        cyclones = DisasterService.get_cyclone_tracks(
            db=db,
            latitude=mid_lat,
            longitude=mid_lon,
            radius_km=max(search_radius, 300.0),
            active_only=True,
            now=current_time,
        )

        # 6. Safe Harbors / Refuges
        nearest_ports_orig = GeoSpatialService.get_nearby_ports(db, origin_latitude, origin_longitude, radius_km=300.0, active_only=True)
        nearest_ports_dest = GeoSpatialService.get_nearby_ports(db, destination_latitude, destination_longitude, radius_km=300.0, active_only=True)
        combined_ports = {p["id"]: p for p in (nearest_ports_orig[:2] + nearest_ports_dest[:2])}
        safe_ports_list = list(combined_ports.values())

        # 7. Local Environmental Telemetry (Origin Vicinity)
        orig_geog = func.cast(orig_pt, Geography)
        marine_point = func.ST_SetSRID(func.ST_MakePoint(MarineObservation.longitude, MarineObservation.latitude), 4326)
        latest_marine = (
            db.query(MarineObservation)
            .filter(func.ST_DWithin(func.cast(marine_point, Geography), orig_geog, 100000.0))
            .order_by(MarineObservation.observed_at.desc())
            .first()
        )

        weather_point = func.ST_SetSRID(func.ST_MakePoint(WeatherObservation.longitude, WeatherObservation.latitude), 4326)
        latest_weather = (
            db.query(WeatherObservation)
            .filter(func.ST_DWithin(func.cast(weather_point, Geography), orig_geog, 100000.0))
            .order_by(WeatherObservation.observed_at.desc())
            .first()
        )

        marine_payload: Optional[Dict[str, Any]] = None
        marine_freshness = FreshnessCategory.UNKNOWN
        if latest_marine:
            marine_freshness = evaluate_freshness(latest_marine.observed_at, current_time=current_time)
            marine_payload = {
                "wave_height_m": latest_marine.wave_height_m,
                "wave_period_s": latest_marine.wave_period_s,
                "swell_wave_height_m": latest_marine.swell_wave_height_m,
                "ocean_current_velocity_kmh": latest_marine.ocean_current_velocity_kmh,
                "sea_surface_temperature_c": latest_marine.sea_surface_temperature_c,
                "observed_at": latest_marine.observed_at.isoformat(),
                "source": latest_marine.source,
                "freshness": str(marine_freshness),
            }

        weather_payload: Optional[Dict[str, Any]] = None
        weather_freshness = FreshnessCategory.UNKNOWN
        if latest_weather:
            weather_freshness = evaluate_freshness(latest_weather.observed_at, current_time=current_time)
            weather_payload = {
                "temperature_c": latest_weather.temperature_c,
                "wind_speed_kmh": latest_weather.wind_speed_kmh,
                "wind_direction_deg": latest_weather.wind_direction_deg,
                "precipitation_mm": latest_weather.precipitation_mm,
                "observed_at": latest_weather.observed_at.isoformat(),
                "source": latest_weather.source,
                "freshness": str(weather_freshness),
            }

        # Determine if telemetry coverage exists
        has_local_telemetry = (
            marine_freshness in (FreshnessCategory.FRESH, FreshnessCategory.AGING)
            or weather_freshness in (FreshnessCategory.FRESH, FreshnessCategory.AGING)
        )

        # 8. Build Traceable Evidence
        evidence = self._build_evidence(
            dist_km=dist_km,
            duration_minutes=duration_minutes,
            speed_kmh=speed_kmh,
            nav_res=nav_res,
            intersecting_hazards=intersecting_hazards,
            active_alerts=active_alerts,
            cyclones=cyclones,
            latest_marine=latest_marine,
            latest_weather=latest_weather,
            safe_ports_list=safe_ports_list,
        )

        return {
            "origin": {"latitude": origin_latitude, "longitude": origin_longitude},
            "destination": {"latitude": destination_latitude, "longitude": destination_longitude},
            "route": route_summary,
            "nav_res": nav_res,
            "intersecting_hazards": intersecting_hazards,
            "active_alerts": active_alerts,
            "cyclones": cyclones,
            "safe_ports": safe_ports_list,
            "marine_conditions": marine_payload,
            "weather_conditions": weather_payload,
            "has_local_telemetry": has_local_telemetry,
            "marine_freshness": marine_freshness,
            "weather_freshness": weather_freshness,
            "evidence": evidence,
            "collected_at": current_time,
        }

    def _build_evidence(
        self,
        dist_km: float,
        duration_minutes: Optional[float],
        speed_kmh: Optional[float],
        nav_res: Dict[str, Any],
        intersecting_hazards: List[HazardZone],
        active_alerts: List[Dict[str, Any]],
        cyclones: List[Dict[str, Any]],
        latest_marine: Optional[MarineObservation],
        latest_weather: Optional[WeatherObservation],
        safe_ports_list: List[Dict[str, Any]],
    ) -> List[OperationalEvidenceItem]:
        evidence: List[OperationalEvidenceItem] = []

        # 1. Route distance & duration evidence
        evidence.append(
            OperationalEvidenceItem(
                factor="route_trajectory",
                title="Geodesic Path Calculation",
                entity_type="ROUTE_GEOMETRY",
                severity="NORMAL",
                source="PostGIS Geodesic / Navigation Engine",
                source_category="OFFICIAL",
                data_type="OPERATIONAL_CALCULATION",
                distance_km=dist_km,
                duration_minutes=duration_minutes,
                spatial_relationship="LINE_TRAJECTORY",
                confidence=1.0,
                freshness="FRESH",
                notes=f"Calculated straight-line geodesic distance: {dist_km} km. Estimated travel duration: {duration_minutes or 0.0} min at {speed_kmh or 0.0} km/h.",
            )
        )

        # 2. Restricted zone intersection evidence
        if nav_res["restricted_zone_intersection"] or nav_res["origin_in_restricted_zone"] or nav_res["destination_in_restricted_zone"]:
            evidence.append(
                OperationalEvidenceItem(
                    factor="restricted_zone_intersection",
                    title="Designated Maritime Exclusion Sector",
                    entity_type="REGULATORY_ZONE",
                    severity="CRITICAL",
                    source="PostGIS Maritime Boundaries",
                    source_category="OFFICIAL",
                    data_type="SPATIAL_REGULATORY",
                    spatial_relationship="INTERSECTS",
                    confidence=1.0,
                    freshness="FRESH",
                    notes=f"Route intersects military/restricted zones: {', '.join(nav_res['intersecting_restricted_zones'])}",
                )
            )

        # 3. Protected zone intersection evidence
        if nav_res["protected_zone_intersection"] or nav_res["origin_in_protected_zone"] or nav_res["destination_in_protected_zone"]:
            evidence.append(
                OperationalEvidenceItem(
                    factor="protected_zone_intersection",
                    title="Ecologically Protected Marine Sanctuary",
                    entity_type="REGULATORY_ZONE",
                    severity="CAUTION",
                    source="PostGIS Protected Zones Registry",
                    source_category="OFFICIAL",
                    data_type="SPATIAL_REGULATORY",
                    spatial_relationship="INTERSECTS",
                    confidence=1.0,
                    freshness="FRESH",
                    notes=f"Route traverses marine protected sanctuary: {', '.join(nav_res['intersecting_protected_zones'])}",
                )
            )

        # 4. Hazard zone intersection evidence
        for hz in intersecting_hazards:
            sev = hz.severity.upper()
            evidence.append(
                OperationalEvidenceItem(
                    factor="hazard_zone_intersection",
                    title=hz.name,
                    entity_type="HAZARD_ZONE",
                    severity=sev,
                    source=hz.source,
                    source_category=hz.source_category,
                    data_type="OBSERVED_HAZARD",
                    observed_at=hz.effective_from.isoformat() if hz.effective_from else None,
                    spatial_relationship="INTERSECTS",
                    confidence=1.0,
                    freshness="FRESH",
                    notes=f"Route intersects active {hz.hazard_type} zone '{hz.name}' ({sev})",
                )
            )

        # 5. Alert evidence
        for alert in active_alerts:
            sev = alert.get("severity", "WARNING").upper()
            evidence.append(
                OperationalEvidenceItem(
                    factor="marine_alert",
                    title=alert.get("title"),
                    entity_type="OFFICIAL_ALERT",
                    severity=sev,
                    source=alert.get("source", "INCOIS"),
                    source_category=alert.get("source_category", "OFFICIAL"),
                    data_type="OFFICIAL_WARNING",
                    observed_at=alert.get("issued_at").isoformat() if hasattr(alert.get("issued_at"), "isoformat") else str(alert.get("issued_at")),
                    distance_km=alert.get("distance_km"),
                    spatial_relationship="PROXIMITY",
                    confidence=1.0,
                    freshness=str(alert.get("freshness", "FRESH")),
                    notes=f"Active {alert.get('alert_type')} alert along operational corridor: {alert.get('title')}",
                )
            )

        # 6. Cyclone evidence
        for cyc in cyclones:
            dist = cyc.get("distance_km")
            c_name = cyc.get("name", "Unnamed")
            c_class = cyc.get("classification", "CYCLONIC_STORM")
            wind = cyc.get("wind_speed_kmh")
            wind_str = f" ({wind} km/h)" if wind else ""
            sev = "CRITICAL" if dist is not None and dist <= 150.0 else ("WARNING" if dist is not None and dist <= 300.0 else "CAUTION")
            evidence.append(
                OperationalEvidenceItem(
                    factor="cyclone_proximity",
                    title=f"Tropical Cyclone {c_name}",
                    entity_type="CYCLONE_TRACK",
                    severity=sev,
                    source=cyc.get("source", "IMD"),
                    source_category=cyc.get("source_category", "OFFICIAL"),
                    data_type="OBSERVED_HAZARD" if cyc.get("data_type") == "OBSERVED" else "FORECAST_HAZARD",
                    observed_at=cyc.get("observed_at").isoformat() if hasattr(cyc.get("observed_at"), "isoformat") else str(cyc.get("observed_at")),
                    distance_km=dist,
                    spatial_relationship="PROXIMITY",
                    confidence=1.0,
                    freshness=str(cyc.get("freshness", "FRESH")),
                    notes=f"Active {c_class} '{c_name}'{wind_str} located {dist} km from route corridor",
                )
            )

        # 7. Marine telemetry evidence
        if latest_marine:
            wave_sev = "WARNING" if latest_marine.wave_height_m and latest_marine.wave_height_m >= 3.5 else ("CAUTION" if latest_marine.wave_height_m and latest_marine.wave_height_m >= 2.5 else "NORMAL")
            evidence.append(
                OperationalEvidenceItem(
                    factor="marine_conditions",
                    title="Sea State & Wave Observation",
                    entity_type="MARINE_TELEMETRY",
                    severity=wave_sev,
                    source=latest_marine.source,
                    source_category="OFFICIAL",
                    data_type="OBSERVED_HAZARD",
                    observed_at=latest_marine.observed_at.isoformat(),
                    confidence=0.95,
                    freshness=str(evaluate_freshness(latest_marine.observed_at)),
                    notes=f"Significant wave height: {latest_marine.wave_height_m}m, swell: {latest_marine.swell_wave_height_m}m, current: {latest_marine.ocean_current_velocity_kmh} km/h.",
                )
            )

        # 8. Weather telemetry evidence
        if latest_weather:
            wind_sev = "WARNING" if latest_weather.wind_speed_kmh and latest_weather.wind_speed_kmh >= 55.0 else ("CAUTION" if latest_weather.wind_speed_kmh and latest_weather.wind_speed_kmh >= 40.0 else "NORMAL")
            evidence.append(
                OperationalEvidenceItem(
                    factor="weather_conditions",
                    title="Atmospheric Wind & Surface Observation",
                    entity_type="WEATHER_TELEMETRY",
                    severity=wind_sev,
                    source=latest_weather.source,
                    source_category="OFFICIAL",
                    data_type="OBSERVED_HAZARD",
                    observed_at=latest_weather.observed_at.isoformat(),
                    confidence=0.95,
                    freshness=str(evaluate_freshness(latest_weather.observed_at)),
                    notes=f"Sustained wind: {latest_weather.wind_speed_kmh} km/h, direction: {latest_weather.wind_direction_deg}°, temperature: {latest_weather.temperature_c}°C.",
                )
            )

        # 9. Safe port refuges
        for p in safe_ports_list[:2]:
            evidence.append(
                OperationalEvidenceItem(
                    factor="safe_harbor_refuge",
                    title=p.get("name"),
                    entity_type="SAFE_PORT",
                    severity="NORMAL",
                    source="Port Authority / PostGIS Registry",
                    source_category="OFFICIAL",
                    data_type="SPATIAL_REGULATORY",
                    distance_km=p.get("distance_km"),
                    spatial_relationship="PROXIMITY",
                    confidence=1.0,
                    freshness="FRESH",
                    notes=f"Designated harbor of safe refuge: {p.get('name')} ({p.get('distance_km')} km)",
                )
            )

        return evidence
