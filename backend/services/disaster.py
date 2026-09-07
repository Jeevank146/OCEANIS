from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Tuple

from geoalchemy2 import Geography
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from models.disaster import CycloneTrack, HazardZone, MarineAlert
from models.geospatial import Port
from models.marine import MarineObservation
from models.weather import WeatherObservation
from services.freshness import FreshnessCategory, evaluate_freshness, is_record_expired
from services.geospatial import GeoSpatialService


class DisasterService:
    """
    Service layer providing PostGIS spatial queries, hazard assessments,
    and deterministic safety evaluations for the Disaster & Safety Data Layer.
    """

    @staticmethod
    def get_alerts(
        db: Session,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: float = 50.0,
        severity: Optional[str] = None,
        active_only: bool = True,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Queries marine alerts with optional spatial proximity filtering and severity filter.
        """
        current_time = now or datetime.now(timezone.utc)
        query = db.query(MarineAlert)

        if active_only:
            query = query.filter(
                MarineAlert.is_active.is_(True),
                MarineAlert.status == "ACTIVE",
                MarineAlert.effective_from <= current_time,
                or_(
                    MarineAlert.effective_until.is_(None),
                    MarineAlert.effective_until >= current_time,
                ),
            )

        if severity:
            query = query.filter(MarineAlert.severity == severity.upper())

        # If spatial coordinates are provided, perform spatial filter
        if latitude is not None and longitude is not None:
            radius_meters = radius_km * 1000.0
            point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
            point_geog = func.cast(point_geom, Geography)

            # Use MarineAlert.geometry if present, else synthesize point from lat/lon
            geom_expr = func.coalesce(
                MarineAlert.geometry,
                func.ST_SetSRID(func.ST_MakePoint(MarineAlert.longitude, MarineAlert.latitude), 4326),
            )
            geom_geog = func.cast(geom_expr, Geography)

            distance_km_expr = func.ST_Distance(geom_geog, point_geog) / 1000.0
            geojson_expr = func.ST_AsGeoJSON(geom_expr)

            query = db.query(
                MarineAlert,
                distance_km_expr.label("distance_km"),
                geojson_expr.label("geojson"),
            ).filter(
                or_(
                    func.ST_DWithin(geom_geog, point_geog, radius_meters),
                    func.ST_Contains(MarineAlert.geometry, point_geom),
                )
            )

            if active_only:
                query = query.filter(
                    MarineAlert.is_active.is_(True),
                    MarineAlert.status == "ACTIVE",
                    MarineAlert.effective_from <= current_time,
                    or_(
                        MarineAlert.effective_until.is_(None),
                        MarineAlert.effective_until >= current_time,
                    ),
                )

            if severity:
                query = query.filter(MarineAlert.severity == severity.upper())

            query = query.order_by("distance_km")

            results = []
            for alert, dist_km, geojson_str in query.all():
                freshness = evaluate_freshness(
                    timestamp=alert.issued_at,
                    effective_until=alert.effective_until,
                    current_time=current_time,
                )
                results.append({
                    "id": alert.id,
                    "alert_id": alert.alert_id,
                    "title": alert.title,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "status": alert.status,
                    "description": alert.description,
                    "source": alert.source,
                    "source_category": alert.source_category,
                    "issued_at": alert.issued_at,
                    "effective_from": alert.effective_from,
                    "effective_until": alert.effective_until,
                    "latitude": alert.latitude,
                    "longitude": alert.longitude,
                    "source_url": alert.source_url,
                    "is_active": alert.is_active,
                    "distance_km": round(float(dist_km), 2) if dist_km is not None else None,
                    "geometry_geojson": json.loads(geojson_str) if geojson_str else None,
                    "freshness": freshness,
                    "created_at": alert.created_at,
                    "updated_at": alert.updated_at,
                })
            return results

        # Non-spatial query
        query = query.order_by(MarineAlert.issued_at.desc())
        alerts = query.all()
        results = []
        for alert in alerts:
            freshness = evaluate_freshness(
                timestamp=alert.issued_at,
                effective_until=alert.effective_until,
                current_time=current_time,
            )
            geojson_dict = None
            if alert.geometry is not None:
                geojson_res = db.scalar(func.ST_AsGeoJSON(alert.geometry))
                if geojson_res:
                    geojson_dict = json.loads(geojson_res)

            results.append({
                "id": alert.id,
                "alert_id": alert.alert_id,
                "title": alert.title,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "status": alert.status,
                "description": alert.description,
                "source": alert.source,
                "source_category": alert.source_category,
                "issued_at": alert.issued_at,
                "effective_from": alert.effective_from,
                "effective_until": alert.effective_until,
                "latitude": alert.latitude,
                "longitude": alert.longitude,
                "source_url": alert.source_url,
                "is_active": alert.is_active,
                "distance_km": None,
                "geometry_geojson": geojson_dict,
                "freshness": freshness,
                "created_at": alert.created_at,
                "updated_at": alert.updated_at,
            })
        return results

    @staticmethod
    def get_alert_by_id(db: Session, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a specific marine alert by its alert_id string.
        """
        alert = db.query(MarineAlert).filter(MarineAlert.alert_id == alert_id).first()
        if not alert:
            return None

        freshness = evaluate_freshness(
            timestamp=alert.issued_at,
            effective_until=alert.effective_until,
        )
        geojson_dict = None
        if alert.geometry is not None:
            geojson_res = db.scalar(func.ST_AsGeoJSON(alert.geometry))
            if geojson_res:
                geojson_dict = json.loads(geojson_res)

        return {
            "id": alert.id,
            "alert_id": alert.alert_id,
            "title": alert.title,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "status": alert.status,
            "description": alert.description,
            "source": alert.source,
            "source_category": alert.source_category,
            "issued_at": alert.issued_at,
            "effective_from": alert.effective_from,
            "effective_until": alert.effective_until,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "source_url": alert.source_url,
            "is_active": alert.is_active,
            "distance_km": None,
            "geometry_geojson": geojson_dict,
            "freshness": freshness,
            "created_at": alert.created_at,
            "updated_at": alert.updated_at,
        }

    @staticmethod
    def get_cyclone_tracks(
        db: Session,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: float = 500.0,
        active_only: bool = True,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves cyclone track points with optional spatial proximity filtering.
        """
        current_time = now or datetime.now(timezone.utc)
        query = db.query(CycloneTrack)

        if active_only:
            query = query.filter(CycloneTrack.is_active.is_(True))

        if latitude is not None and longitude is not None:
            radius_meters = radius_km * 1000.0
            point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
            point_geog = func.cast(point_geom, Geography)
            track_geog = func.cast(CycloneTrack.geometry, Geography)

            distance_km_expr = func.ST_Distance(track_geog, point_geog) / 1000.0
            geojson_expr = func.ST_AsGeoJSON(CycloneTrack.geometry)

            query = db.query(
                CycloneTrack,
                distance_km_expr.label("distance_km"),
                geojson_expr.label("geojson"),
            ).filter(
                func.ST_DWithin(track_geog, point_geog, radius_meters)
            )

            if active_only:
                query = query.filter(CycloneTrack.is_active.is_(True))

            query = query.order_by("distance_km")

            results = []
            for track, dist_km, geojson_str in query.all():
                freshness = evaluate_freshness(
                    timestamp=track.observed_at,
                    current_time=current_time,
                )
                results.append({
                    "id": track.id,
                    "cyclone_id": track.cyclone_id,
                    "name": track.name,
                    "basin": track.basin,
                    "classification": track.classification,
                    "latitude": track.latitude,
                    "longitude": track.longitude,
                    "wind_speed_kmh": track.wind_speed_kmh,
                    "pressure_hpa": track.pressure_hpa,
                    "movement_direction_deg": track.movement_direction_deg,
                    "movement_speed_kmh": track.movement_speed_kmh,
                    "observed_at": track.observed_at,
                    "forecast_time": track.forecast_time,
                    "source": track.source,
                    "source_category": track.source_category,
                    "data_type": track.data_type,
                    "is_active": track.is_active,
                    "distance_km": round(float(dist_km), 2) if dist_km is not None else None,
                    "geometry_geojson": json.loads(geojson_str) if geojson_str else None,
                    "freshness": freshness,
                    "created_at": track.created_at,
                    "updated_at": track.updated_at,
                })
            return results

        # Non-spatial query
        query = query.order_by(CycloneTrack.observed_at.desc())
        tracks = query.all()
        results = []
        for track in tracks:
            freshness = evaluate_freshness(
                timestamp=track.observed_at,
                current_time=current_time,
            )
            geojson_res = db.scalar(func.ST_AsGeoJSON(track.geometry))
            results.append({
                "id": track.id,
                "cyclone_id": track.cyclone_id,
                "name": track.name,
                "basin": track.basin,
                "classification": track.classification,
                "latitude": track.latitude,
                "longitude": track.longitude,
                "wind_speed_kmh": track.wind_speed_kmh,
                "pressure_hpa": track.pressure_hpa,
                "movement_direction_deg": track.movement_direction_deg,
                "movement_speed_kmh": track.movement_speed_kmh,
                "observed_at": track.observed_at,
                "forecast_time": track.forecast_time,
                "source": track.source,
                "source_category": track.source_category,
                "data_type": track.data_type,
                "is_active": track.is_active,
                "distance_km": None,
                "geometry_geojson": json.loads(geojson_res) if geojson_res else None,
                "freshness": freshness,
                "created_at": track.created_at,
                "updated_at": track.updated_at,
            })
        return results

    @staticmethod
    def get_hazard_zones(
        db: Session,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: float = 50.0,
        hazard_type: Optional[str] = None,
        active_only: bool = True,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves hazard zones with optional spatial proximity filtering and containment checks.
        """
        current_time = now or datetime.now(timezone.utc)
        query = db.query(HazardZone)

        if active_only:
            query = query.filter(
                HazardZone.is_active.is_(True),
                or_(
                    HazardZone.effective_until.is_(None),
                    HazardZone.effective_until >= current_time,
                ),
            )

        if hazard_type:
            query = query.filter(HazardZone.hazard_type == hazard_type)

        if latitude is not None and longitude is not None:
            radius_meters = radius_km * 1000.0
            point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
            point_geog = func.cast(point_geom, Geography)
            zone_geog = func.cast(HazardZone.geometry, Geography)

            distance_km_expr = func.ST_Distance(zone_geog, point_geog) / 1000.0
            geojson_expr = func.ST_AsGeoJSON(HazardZone.geometry)
            contains_expr = func.ST_Contains(HazardZone.geometry, point_geom)

            query = db.query(
                HazardZone,
                distance_km_expr.label("distance_km"),
                geojson_expr.label("geojson"),
                contains_expr.label("contains_point"),
            ).filter(
                or_(
                    func.ST_DWithin(zone_geog, point_geog, radius_meters),
                    func.ST_Contains(HazardZone.geometry, point_geom),
                )
            )

            if active_only:
                query = query.filter(
                    HazardZone.is_active.is_(True),
                    or_(
                        HazardZone.effective_until.is_(None),
                        HazardZone.effective_until >= current_time,
                    ),
                )

            if hazard_type:
                query = query.filter(HazardZone.hazard_type == hazard_type)

            query = query.order_by("distance_km")

            results = []
            for zone, dist_km, geojson_str, contains_pt in query.all():
                freshness = evaluate_freshness(
                    timestamp=zone.effective_from or zone.created_at,
                    effective_until=zone.effective_until,
                    current_time=current_time,
                )
                results.append({
                    "id": zone.id,
                    "name": zone.name,
                    "hazard_type": zone.hazard_type,
                    "severity": zone.severity,
                    "description": zone.description,
                    "source": zone.source,
                    "source_category": zone.source_category,
                    "source_url": zone.source_url,
                    "effective_from": zone.effective_from,
                    "effective_until": zone.effective_until,
                    "is_active": zone.is_active,
                    "distance_km": round(float(dist_km), 2) if dist_km is not None else 0.0,
                    "contains_point": bool(contains_pt),
                    "geometry_geojson": json.loads(geojson_str) if geojson_str else None,
                    "freshness": freshness,
                    "created_at": zone.created_at,
                    "updated_at": zone.updated_at,
                })
            return results

        # Non-spatial query
        zones = query.all()
        results = []
        for zone in zones:
            freshness = evaluate_freshness(
                timestamp=zone.effective_from or zone.created_at,
                effective_until=zone.effective_until,
                current_time=current_time,
            )
            geojson_res = db.scalar(func.ST_AsGeoJSON(zone.geometry))
            results.append({
                "id": zone.id,
                "name": zone.name,
                "hazard_type": zone.hazard_type,
                "severity": zone.severity,
                "description": zone.description,
                "source": zone.source,
                "source_category": zone.source_category,
                "source_url": zone.source_url,
                "effective_from": zone.effective_from,
                "effective_until": zone.effective_until,
                "is_active": zone.is_active,
                "distance_km": None,
                "contains_point": None,
                "geometry_geojson": json.loads(geojson_res) if geojson_res else None,
                "freshness": freshness,
                "created_at": zone.created_at,
                "updated_at": zone.updated_at,
            })
        return results

    @staticmethod
    def assess_safety(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic safety assessment engine based ONLY on stored source telemetry and spatial datasets.
        
        Safety Rules:
        1. Never invent safety when coverage is absent -> INSUFFICIENT_DATA.
        2. Expired warnings are excluded from active threat assessment.
        3. Active CRITICAL official alerts or Super/Extremely Severe Cyclone within 200km -> CRITICAL.
        4. Active WARNING alerts or containment in WARNING hazard zone or Cyclonic Storm within 150km -> WARNING.
        5. Containment in CAUTION zone or Depression / high swell alert in vicinity -> CAUTION.
        6. Confirmed fresh observation coverage without active hazards -> SAFE.
        """
        current_time = now or datetime.now(timezone.utc)
        reasons: List[str] = []

        # 1. Fetch active alerts in radius
        alerts = DisasterService.get_alerts(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            active_only=True,
            now=current_time,
        )

        # 2. Fetch active hazard zones in radius
        hazards = DisasterService.get_hazard_zones(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            active_only=True,
            now=current_time,
        )

        # 3. Fetch active cyclone tracks within 300km
        cyclones = DisasterService.get_cyclone_tracks(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=max(radius_km, 300.0),
            active_only=True,
            now=current_time,
        )

        # 4. Find nearest safe port/refuge using GeoSpatial service
        nearest_ports = GeoSpatialService.get_nearby_ports(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=500.0,
            active_only=True,
        )
        nearest_port = nearest_ports[0] if nearest_ports else None

        # 5. Check local marine & weather telemetry presence to assess data coverage
        # Search for telemetry within 100km of requested coordinates
        has_local_telemetry = False
        telemetry_freshness = FreshnessCategory.UNKNOWN

        point_geom = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geog = func.cast(point_geom, Geography)

        weather_point = func.ST_SetSRID(func.ST_MakePoint(WeatherObservation.longitude, WeatherObservation.latitude), 4326)
        latest_weather = (
            db.query(WeatherObservation)
            .filter(func.ST_DWithin(func.cast(weather_point, Geography), point_geog, 100000.0))
            .order_by(WeatherObservation.observed_at.desc())
            .first()
        )

        marine_point = func.ST_SetSRID(func.ST_MakePoint(MarineObservation.longitude, MarineObservation.latitude), 4326)
        latest_marine = (
            db.query(MarineObservation)
            .filter(func.ST_DWithin(func.cast(marine_point, Geography), point_geog, 100000.0))
            .order_by(MarineObservation.observed_at.desc())
            .first()
        )

        if latest_marine or latest_weather:
            latest_ts = None
            if latest_marine and latest_weather:
                latest_ts = max(latest_marine.observed_at, latest_weather.observed_at)
            elif latest_marine:
                latest_ts = latest_marine.observed_at
            else:
                latest_ts = latest_weather.observed_at

            telemetry_freshness = evaluate_freshness(latest_ts, current_time=current_time)
            if telemetry_freshness in (FreshnessCategory.FRESH, FreshnessCategory.AGING):
                has_local_telemetry = True

        # Threat analysis variables
        has_critical = False
        has_warning = False
        has_caution = False

        # Evaluate alerts
        for alert in alerts:
            sev = alert.get("severity", "").upper()
            title = alert.get("title", "")
            dist = alert.get("distance_km")
            dist_str = f" ({dist} km away)" if dist is not None else ""

            if sev == "CRITICAL":
                has_critical = True
                reasons.append(f"CRITICAL official alert active: {title}{dist_str} issued by {alert.get('source')}.")
            elif sev == "WARNING":
                has_warning = True
                reasons.append(f"WARNING official alert active: {title}{dist_str} issued by {alert.get('source')}.")
            elif sev in ("CAUTION", "INFO"):
                has_caution = True
                reasons.append(f"CAUTION advisory active: {title}{dist_str} issued by {alert.get('source')}.")

        # Evaluate hazard zones
        for hz in hazards:
            sev = hz.get("severity", "").upper()
            name = hz.get("name", "")
            contains = hz.get("contains_point", False)
            dist = hz.get("distance_km", 0.0)

            if contains:
                if sev == "CRITICAL":
                    has_critical = True
                    reasons.append(f"Location is DIRECTLY INSIDE critical hazard zone: '{name}' ({hz.get('hazard_type')}).")
                elif sev == "WARNING":
                    has_warning = True
                    reasons.append(f"Location is DIRECTLY INSIDE hazard zone: '{name}' ({hz.get('hazard_type')}).")
                else:
                    has_caution = True
                    reasons.append(f"Location is inside caution zone: '{name}' ({hz.get('hazard_type')}).")
            else:
                if sev in ("CRITICAL", "WARNING") and dist <= 25.0:
                    has_caution = True
                    reasons.append(f"Proximity to high-hazard boundary '{name}' ({dist} km away).")

        # Evaluate cyclones
        for cyc in cyclones:
            dist = cyc.get("distance_km")
            c_name = cyc.get("name", "Unnamed")
            c_class = cyc.get("classification", "CYCLONIC_STORM")
            wind = cyc.get("wind_speed_kmh")
            wind_str = f" with {wind} km/h sustained winds" if wind else ""

            if dist is not None and dist <= 150.0:
                has_critical = True
                reasons.append(f"Extreme danger: Active tropical system '{c_name}' ({c_class}{wind_str}) is within {dist} km.")
            elif dist is not None and dist <= 300.0:
                has_warning = True
                reasons.append(f"Severe warning: Cyclone track point '{c_name}' ({c_class}{wind_str}) is within {dist} km.")
            else:
                has_caution = True
                reasons.append(f"Monitoring advisory: Cyclonic activity '{c_name}' located {dist} km from position.")

        # Determine final status, data freshness, and confidence
        if has_critical:
            status = "CRITICAL"
            confidence = "HIGH"
            overall_freshness = FreshnessCategory.FRESH
        elif has_warning:
            status = "WARNING"
            confidence = "HIGH"
            overall_freshness = FreshnessCategory.FRESH
        elif has_caution:
            status = "CAUTION"
            confidence = "HIGH" if has_local_telemetry else "MEDIUM"
            overall_freshness = telemetry_freshness if has_local_telemetry else FreshnessCategory.AGING
        else:
            # Zero active hazards/alerts/cyclones found
            if not has_local_telemetry:
                status = "INSUFFICIENT_DATA"
                confidence = "LOW"
                overall_freshness = telemetry_freshness
                reasons.append(
                    "No active emergency alerts recorded, but local oceanic telemetry coverage is missing or stale. "
                    "Cannot guarantee safe navigation conditions."
                )
            else:
                status = "SAFE"
                confidence = "HIGH"
                overall_freshness = telemetry_freshness
                reasons.append(
                    f"No active marine alerts, hazard zones, or cyclonic systems within {radius_km} km radius. "
                    "Verified telemetry indicates normal operational maritime conditions."
                )

        if nearest_port:
            port_name = nearest_port.get("name")
            port_dist = nearest_port.get("distance_km")
            reasons.append(f"Nearest safe port/coastal harbor is {port_name} ({port_dist} km).")

        return {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "status": status,
            "active_alerts": alerts,
            "nearby_hazards": hazards,
            "nearby_cyclones": cyclones,
            "nearest_safe_port": nearest_port,
            "data_freshness": overall_freshness,
            "confidence": confidence,
            "reasons": reasons,
            "assessment_timestamp": current_time,
        }
