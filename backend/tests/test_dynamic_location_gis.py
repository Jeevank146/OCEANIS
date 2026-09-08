import pytest
from datetime import datetime, timezone
from database import SessionLocal
from schemas.location import ResolvedLocation, LocationValidationResult
from services.location import LocationService
from services.marine_data import MarineDataService
from services.geospatial import GeoSpatialService
from services.navigation import NavigationService
from orchestrator.orchestrator import AgentOrchestrator
from orchestrator.schemas import OrchestrationQuery


def test_resolved_location_schema_and_factory():
    # 1. Test direct schema initialization
    res = ResolvedLocation(
        name="Kakinada Offshore",
        display_name="Kakinada Offshore Sector, Andhra Pradesh, India",
        latitude=16.9890,
        longitude=82.2474,
        is_coastal=True,
        coastal_status="COASTAL",
        resolution_source="COORDINATE_INPUT",
        requested_latitude=16.9890,
        requested_longitude=82.2474,
        source_grid_latitude=16.9890,
        source_grid_longitude=82.2474,
    )
    assert res.latitude == 16.9890
    assert res.longitude == 82.2474
    assert res.coastal_status == "COASTAL"
    assert res.is_coastal is True
    assert res.source_grid_latitude == 16.9890

    # 2. Test LocationService.resolve_location with coordinates
    res_loc = LocationService.resolve_location(
        latitude=17.6868,
        longitude=83.2185,
        display_name="Visakhapatnam Harbor",
    )
    assert isinstance(res_loc, ResolvedLocation)
    assert res_loc.latitude == 17.6868
    assert res_loc.longitude == 83.2185
    assert res_loc.is_coastal is True
    assert res_loc.coastal_status in ["COASTAL", "OFFSHORE"]
    assert res_loc.requested_latitude == 17.6868
    assert res_loc.requested_longitude == 83.2185

    # 3. Test LocationService coordinate geocode resolution
    res_search = LocationService.resolve_location(latitude=12.9141, longitude=74.8560, display_name="Mangalore Port")
    assert isinstance(res_search, ResolvedLocation)
    assert res_search.is_coastal is True
    assert res_search.latitude > 12.0
    assert res_search.longitude > 74.0


def test_multi_location_spatial_independence():
    # Verify that different coordinates yield completely independent resolved locations
    loc_chennai = LocationService.resolve_location(latitude=13.0827, longitude=80.2707, display_name="Chennai Coast")
    loc_mumbai = LocationService.resolve_location(latitude=18.9220, longitude=72.8347, display_name="Mumbai Port")
    loc_paradip = LocationService.resolve_location(latitude=20.2600, longitude=86.6700, display_name="Paradip Port")

    # Verify coordinate isolation
    assert abs(loc_chennai.latitude - 13.0827) < 1e-4
    assert abs(loc_chennai.longitude - 80.2707) < 1e-4

    assert abs(loc_mumbai.latitude - 18.9220) < 1e-4
    assert abs(loc_mumbai.longitude - 72.8347) < 1e-4

    assert abs(loc_paradip.latitude - 20.2600) < 1e-4
    assert abs(loc_paradip.longitude - 86.6700) < 1e-4

    # Marine contexts should match regional maritime sectors
    assert "Bay of Bengal" in loc_chennai.marine_context or "Coromandel" in loc_chennai.marine_context or "Chennai" in loc_chennai.name
    assert "Arabian Sea" in loc_mumbai.marine_context or "Konkan" in loc_mumbai.marine_context or "Mumbai" in loc_mumbai.name
    assert "Bay of Bengal" in loc_paradip.marine_context or "Odisha" in loc_paradip.marine_context or "Paradip" in loc_paradip.name


def test_inland_location_classification_and_blocking():
    # Test an inland location far from coast (e.g. Hyderabad / New Delhi)
    hyderabad_lat = 17.3850
    hyderabad_lon = 78.4867

    # 1. Location validation must mark it as inland
    val = LocationService.validate_coordinates(hyderabad_lat, hyderabad_lon, custom_name="Hyderabad City")
    assert val.is_coastal is False
    assert val.coastal_status == "INLAND"
    assert val.distance_to_coast_km > 50.0

    # 2. Location resolution must reflect INLAND status
    resolved = LocationService.resolve_location(latitude=hyderabad_lat, longitude=hyderabad_lon)
    assert resolved.is_coastal is False
    assert resolved.coastal_status == "INLAND"

    # 3. Marine data service must block ocean/wave data for inland coordinates
    db = SessionLocal()
    try:
        service = MarineDataService()
        result = service.fetch_marine_intelligence(
            db=db,
            latitude=hyderabad_lat,
            longitude=hyderabad_lon,
            location_name="Hyderabad City",
        )
        assert result.is_coastal is False
        assert len(result.records) == 0
        assert any("inland" in w.lower() or "50km" in w.lower() for w in result.warnings)
    finally:
        db.close()


def test_offshore_coordinate_validation():
    # Deep Bay of Bengal offshore coordinate (200km offshore)
    offshore_lat = 15.0000
    offshore_lon = 87.0000

    val = LocationService.validate_coordinates(offshore_lat, offshore_lon)
    assert val.is_coastal is True
    assert val.coastal_status in ["OFFSHORE", "COASTAL"]
    assert "Bay of Bengal" in val.marine_context or "Marine" in val.marine_context

    resolved = LocationService.resolve_location(latitude=offshore_lat, longitude=offshore_lon)
    assert resolved.is_coastal is True
    assert resolved.coastal_status in ["OFFSHORE", "COASTAL"]


def test_spatial_cache_isolation():
    # Verify that cache lookup for Location A (e.g. Visakhapatnam) does not collide with Location B (e.g. Kakinada ~150km away)
    db = SessionLocal()
    try:
        service = MarineDataService()
        
        # Vizag coordinates
        vizag_lat, vizag_lon = 17.6868, 83.2185
        # Kakinada coordinates
        kak_lat, kak_lon = 16.9890, 82.2474

        now = datetime.now(timezone.utc)
        cached_vizag = service._check_database_cache(db, vizag_lat, vizag_lon, current_time=now)
        cached_kak = service._check_database_cache(db, kak_lat, kak_lon, current_time=now)

        # For any records found, check that coordinate bounding box was respected
        for r in (cached_vizag or []):
            assert abs(r.latitude - vizag_lat) <= 0.08
            assert abs(r.longitude - vizag_lon) <= 0.08

        for r in (cached_kak or []):
            assert abs(r.latitude - kak_lat) <= 0.08
            assert abs(r.longitude - kak_lon) <= 0.08
    finally:
        db.close()


def test_dynamic_navigation_route_assessment():
    db = SessionLocal()
    try:
        nav_service = NavigationService()
        
        # Dynamic passage from Visakhapatnam to Paradip Port
        origin_lat, origin_lon = 17.6868, 83.2185
        dest_lat, dest_lon = 20.2600, 86.6700

        assessment = nav_service.assess_route(
            db=db,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
        )

        assert assessment is not None
        assert assessment["distance_km"] > 0
        assert assessment["origin"]["latitude"] == origin_lat
        assert assessment["destination"]["latitude"] == dest_lat
        assert "navigation_status" in assessment
        assert "reasons" in assessment
    finally:
        db.close()


def test_dynamic_orchestrator_location_context():
    db = SessionLocal()
    try:
        orchestrator = AgentOrchestrator()

        # 1. User passes explicit coordinates for Chennai
        query_chennai = OrchestrationQuery(
            query="Can I go fishing tomorrow morning?",
            latitude=13.0827,
            longitude=80.2707,
            location_name="Chennai Coast",
        )

        response_chennai = orchestrator.orchestrate(db=db, query=query_chennai)
        assert response_chennai.location is not None
        assert abs(response_chennai.location["latitude"] - 13.0827) < 1e-4
        assert abs(response_chennai.location["longitude"] - 80.2707) < 1e-4

        # 2. User passes explicit coordinates for Mumbai
        query_mumbai = OrchestrationQuery(
            query="Is it safe for a trawler operation today?",
            latitude=18.9220,
            longitude=72.8347,
            location_name="Mumbai Harbor",
        )

        response_mumbai = orchestrator.orchestrate(db=db, query=query_mumbai)
        assert response_mumbai.location is not None
        assert abs(response_mumbai.location["latitude"] - 18.9220) < 1e-4
        assert abs(response_mumbai.location["longitude"] - 72.8347) < 1e-4

        # Verify that agents received and executed against the specific user coordinates
        assert len(response_chennai.agent_contributions) > 0
        assert len(response_mumbai.agent_contributions) > 0
    finally:
        db.close()


def test_geospatial_nearby_ports_and_hazard_queries():
    db = SessionLocal()
    try:
        geo = GeoSpatialService()
        
        # Query nearby ports around Cochin (Kochi)
        kochi_lat, kochi_lon = 9.9312, 76.2673
        ports = geo.get_nearby_ports(db, kochi_lat, kochi_lon, radius_km=150.0)
        
        assert isinstance(ports, list)
        if len(ports) > 0:
            for p in ports:
                assert "name" in p
                assert "distance_km" in p
                assert p["distance_km"] <= 150.0
    finally:
        db.close()
