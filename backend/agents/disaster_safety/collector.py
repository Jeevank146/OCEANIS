from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from geoalchemy2 import Geography
from sqlalchemy import func
from sqlalchemy.orm import Session

from agents.disaster_safety.schemas import (
    AlertSummary,
    CycloneSummary,
    HazardSummary,
    SafePortSummary,
    SafetyEvidenceItem,
)
from models.marine import MarineObservation
from models.weather import WeatherObservation
from services.disaster import DisasterService
from services.freshness import FreshnessCategory, evaluate_freshness
from services.geospatial import GeoSpatialService


class DisasterSafetyDataCollector:
    """
    Data Collector for Disaster & Safety Intelligence Agent.
    Interacts with PostgreSQL/PostGIS services to collect active alerts,
    hazard zones, cyclone tracking observations, and nearest safe ports.
    """

    def collect(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
        target_datetime: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Collects all relevant disaster, alert, hazard, cyclone, and port data for the given location.
        """
        now = datetime.now(timezone.utc)
        if target_datetime:
            try:
                now = datetime.fromisoformat(target_datetime.replace("Z", "+00:00"))
            except Exception:
                pass

        # 1. Collect active marine alerts
        raw_alerts = DisasterService.get_alerts(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            active_only=True,
            now=now,
        )

        # 2. Collect active hazard zones
        raw_hazards = DisasterService.get_hazard_zones(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            active_only=True,
            now=now,
        )

        # 3. Collect active cyclone tracks
        raw_cyclones = DisasterService.get_cyclone_tracks(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=max(radius_km, 500.0),
            active_only=True,
            now=now,
        )

        # 4. Nearest safe port
        nearby_ports = GeoSpatialService.get_nearby_ports(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=500.0,
            active_only=True,
        )
        nearest_port_dict = nearby_ports[0] if nearby_ports else None

        # 5. Check local marine and weather telemetry presence within 100km
        has_local_telemetry, telemetry_freshness, latest_telemetry_ts = self._check_telemetry_coverage(
            db=db, latitude=latitude, longitude=longitude, now=now
        )

        # 6. Format summaries
        alerts_summary: List[AlertSummary] = []
        for a in raw_alerts:
            alerts_summary.append(
                AlertSummary(
                    id=a.get("id"),
                    alert_id=a.get("alert_id", "UNKNOWN"),
                    title=a.get("title", "Untitled Alert"),
                    alert_type=a.get("alert_type", "GENERAL"),
                    severity=a.get("severity", "UNKNOWN"),
                    status=a.get("status", "ACTIVE"),
                    description=a.get("description"),
                    source=a.get("source", "INCOIS"),
                    source_category=a.get("source_category", "OFFICIAL"),
                    issued_at=a.get("issued_at").isoformat() if a.get("issued_at") else None,
                    effective_from=a.get("effective_from").isoformat() if a.get("effective_from") else None,
                    effective_until=a.get("effective_until").isoformat() if a.get("effective_until") else None,
                    distance_km=a.get("distance_km"),
                    freshness=str(a.get("freshness", "FRESH")),
                )
            )

        hazards_summary: List[HazardSummary] = []
        for h in raw_hazards:
            hazards_summary.append(
                HazardSummary(
                    id=h.get("id"),
                    name=h.get("name", "Unnamed Hazard"),
                    hazard_type=h.get("hazard_type", "GENERAL_HAZARD"),
                    severity=h.get("severity", "WARNING"),
                    description=h.get("description"),
                    source=h.get("source", "INCOIS"),
                    source_category=h.get("source_category", "OFFICIAL"),
                    distance_km=h.get("distance_km"),
                    contains_point=bool(h.get("contains_point", False)),
                    freshness=str(h.get("freshness", "FRESH")),
                )
            )

        cyclones_summary: List[CycloneSummary] = []
        for c in raw_cyclones:
            cyclones_summary.append(
                CycloneSummary(
                    id=c.get("id"),
                    cyclone_id=c.get("cyclone_id", "UNKNOWN"),
                    name=c.get("name", "Unnamed System"),
                    basin=c.get("basin", "NORTH_INDIAN_OCEAN"),
                    classification=c.get("classification", "CYCLONIC_STORM"),
                    latitude=c.get("latitude", 0.0),
                    longitude=c.get("longitude", 0.0),
                    wind_speed_kmh=c.get("wind_speed_kmh"),
                    pressure_hpa=c.get("pressure_hpa"),
                    movement_direction_deg=c.get("movement_direction_deg"),
                    movement_speed_kmh=c.get("movement_speed_kmh"),
                    observed_at=c.get("observed_at").isoformat() if c.get("observed_at") else None,
                    forecast_time=c.get("forecast_time").isoformat() if c.get("forecast_time") else None,
                    distance_km=c.get("distance_km"),
                    data_type=c.get("data_type", "OBSERVED"),
                    freshness=str(c.get("freshness", "FRESH")),
                )
            )

        safe_port_summary: Optional[SafePortSummary] = None
        if nearest_port_dict:
            safe_port_summary = SafePortSummary(
                id=nearest_port_dict.get("id"),
                name=nearest_port_dict.get("name", "Nearest Port"),
                port_type=nearest_port_dict.get("port_type"),
                distance_km=nearest_port_dict.get("distance_km"),
                latitude=nearest_port_dict.get("latitude"),
                longitude=nearest_port_dict.get("longitude"),
                country=nearest_port_dict.get("country"),
                state=nearest_port_dict.get("state"),
            )

        # Build traceable evidence list
        evidence_items = self._build_evidence(
            raw_alerts=raw_alerts,
            raw_hazards=raw_hazards,
            raw_cyclones=raw_cyclones,
            nearest_port_dict=nearest_port_dict,
            has_local_telemetry=has_local_telemetry,
            telemetry_freshness=telemetry_freshness,
            latest_telemetry_ts=latest_telemetry_ts,
        )

        return {
            "origin": {"latitude": latitude, "longitude": longitude},
            "radius_km": radius_km,
            "alerts": alerts_summary,
            "hazards": hazards_summary,
            "cyclones": cyclones_summary,
            "nearest_safe_port": safe_port_summary,
            "has_local_telemetry": has_local_telemetry,
            "telemetry_freshness": telemetry_freshness,
            "evidence": evidence_items,
            "collected_at": now,
        }

    def _check_telemetry_coverage(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        now: datetime,
    ) -> Tuple[bool, FreshnessCategory, Optional[datetime]]:
        """
        Checks whether fresh/aging weather and marine observations exist within 100km.
        """
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

        if not latest_weather and not latest_marine:
            return False, FreshnessCategory.UNKNOWN, None

        latest_ts = None
        if latest_weather and latest_marine:
            latest_ts = max(latest_weather.observed_at, latest_marine.observed_at)
        elif latest_weather:
            latest_ts = latest_weather.observed_at
        else:
            latest_ts = latest_marine.observed_at

        freshness = evaluate_freshness(latest_ts, current_time=now)
        has_coverage = freshness in (FreshnessCategory.FRESH, FreshnessCategory.AGING)
        return has_coverage, freshness, latest_ts

    def _build_evidence(
        self,
        raw_alerts: List[Dict[str, Any]],
        raw_hazards: List[Dict[str, Any]],
        raw_cyclones: List[Dict[str, Any]],
        nearest_port_dict: Optional[Dict[str, Any]],
        has_local_telemetry: bool,
        telemetry_freshness: FreshnessCategory,
        latest_telemetry_ts: Optional[datetime],
    ) -> List[SafetyEvidenceItem]:
        """
        Builds traceable safety evidence items with provenance and spatial relationships.
        """
        evidence: List[SafetyEvidenceItem] = []

        # 1. Alert evidence
        for alert in raw_alerts:
            sev = alert.get("severity", "WARNING").upper()
            dist = alert.get("distance_km")
            spatial_rel = "PROXIMITY" if dist is not None and dist > 0 else "CONTAINS"
            evidence.append(
                SafetyEvidenceItem(
                    factor="active_alert",
                    title=alert.get("title"),
                    entity_type="OFFICIAL_ALERT",
                    severity=sev,
                    source=alert.get("source", "INCOIS"),
                    source_category=alert.get("source_category", "OFFICIAL"),
                    data_type="OFFICIAL_WARNING",
                    observed_at=alert.get("issued_at").isoformat() if alert.get("issued_at") else None,
                    effective_from=alert.get("effective_from").isoformat() if alert.get("effective_from") else None,
                    effective_until=alert.get("effective_until").isoformat() if alert.get("effective_until") else None,
                    distance_km=dist,
                    spatial_relationship=spatial_rel,
                    confidence=1.0,
                    freshness=str(alert.get("freshness", "FRESH")),
                    notes=f"Official {alert.get('alert_type')} alert from {alert.get('source')}: {alert.get('title')}",
                )
            )

        # 2. Hazard zone evidence
        for hz in raw_hazards:
            sev = hz.get("severity", "WARNING").upper()
            contains = hz.get("contains_point", False)
            dist = hz.get("distance_km", 0.0)
            spatial_rel = "INSIDE" if contains else ("NEAR_BOUNDARY" if dist <= 25.0 else "PROXIMITY")
            evidence.append(
                SafetyEvidenceItem(
                    factor="hazard_containment" if contains else "hazard_proximity",
                    title=hz.get("name"),
                    entity_type="HAZARD_ZONE",
                    severity=sev,
                    source=hz.get("source", "INCOIS"),
                    source_category=hz.get("source_category", "OFFICIAL"),
                    data_type="OBSERVED_HAZARD",
                    observed_at=hz.get("effective_from").isoformat() if hz.get("effective_from") else None,
                    effective_from=hz.get("effective_from").isoformat() if hz.get("effective_from") else None,
                    effective_until=hz.get("effective_until").isoformat() if hz.get("effective_until") else None,
                    distance_km=0.0 if contains else dist,
                    spatial_relationship=spatial_rel,
                    confidence=1.0,
                    freshness=str(hz.get("freshness", "FRESH")),
                    notes=f"{'Direct containment inside' if contains else 'Proximity to'} {hz.get('hazard_type')} zone '{hz.get('name')}'",
                )
            )

        # 3. Cyclone evidence
        for cyc in raw_cyclones:
            dist = cyc.get("distance_km")
            c_name = cyc.get("name", "Unnamed")
            c_class = cyc.get("classification", "CYCLONIC_STORM")
            wind = cyc.get("wind_speed_kmh")
            wind_str = f" ({wind} km/h)" if wind else ""
            sev = "CRITICAL" if dist is not None and dist <= 150.0 else ("WARNING" if dist is not None and dist <= 300.0 else "CAUTION")
            evidence.append(
                SafetyEvidenceItem(
                    factor="cyclone_proximity",
                    title=f"Tropical Cyclone {c_name}",
                    entity_type="CYCLONE_TRACK",
                    severity=sev,
                    source=cyc.get("source", "IMD"),
                    source_category=cyc.get("source_category", "OFFICIAL"),
                    data_type="OBSERVED_HAZARD" if cyc.get("data_type") == "OBSERVED" else "FORECAST_HAZARD",
                    observed_at=cyc.get("observed_at").isoformat() if cyc.get("observed_at") else None,
                    distance_km=dist,
                    spatial_relationship="PROXIMITY",
                    confidence=1.0,
                    freshness=str(cyc.get("freshness", "FRESH")),
                    notes=f"Active {c_class} '{c_name}'{wind_str} located {dist} km away",
                )
            )

        # 4. Nearest port infrastructure
        if nearest_port_dict:
            evidence.append(
                SafetyEvidenceItem(
                    factor="nearest_safe_refuge",
                    title=nearest_port_dict.get("name"),
                    entity_type="SAFE_PORT",
                    severity="NORMAL",
                    source="Port Authority / PostGIS Registry",
                    source_category="OFFICIAL",
                    data_type="SPATIAL_INFRASTRUCTURE",
                    distance_km=nearest_port_dict.get("distance_km"),
                    spatial_relationship="PROXIMITY",
                    confidence=1.0,
                    freshness="FRESH",
                    notes=f"Nearest harbor of safe refuge: {nearest_port_dict.get('name')} ({nearest_port_dict.get('distance_km')} km)",
                )
            )

        # 5. Local telemetry coverage evidence
        if has_local_telemetry:
            evidence.append(
                SafetyEvidenceItem(
                    factor="telemetry_coverage",
                    title="Coastal Marine & Weather Telemetry",
                    entity_type="TELEMETRY_COVERAGE",
                    severity="NORMAL",
                    source="INCOIS / Open-Meteo",
                    source_category="OFFICIAL",
                    data_type="OBSERVED_HAZARD",
                    observed_at=latest_telemetry_ts.isoformat() if latest_telemetry_ts else None,
                    distance_km=0.0,
                    spatial_relationship="CONTAINS",
                    confidence=0.95,
                    freshness=str(telemetry_freshness),
                    notes="Local environmental monitoring coverage verified within 100 km radius",
                )
            )

        return evidence
