import os
import sys
import unittest

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from services.location import LocationService


class TestLocationIntelligence(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_indian_coastal_cities(self):
        """1. Valid Indian coastal cities: Visakhapatnam, Kakinada, Kochi, Mumbai, Chennai, Veraval"""
        cities = ["Visakhapatnam", "Kakinada", "Kochi", "Mumbai", "Chennai", "Veraval"]
        for city in cities:
            res = LocationService.validate_location(query=city)
            self.assertEqual(res.status, "VALID_COASTAL", f"Failed for {city}")
            self.assertTrue(res.is_coastal, f"{city} should be coastal")
            self.assertTrue(res.is_marine, f"{city} should have marine context")
            self.assertIsNotNone(res.distance_to_coast_km)
            self.assertLess(res.distance_to_coast_km, 10.0)
            self.assertIsNotNone(res.marine_context)

    def test_international_coastal_cities(self):
        """2. Valid International coastal cities: Miami, Rotterdam, Sydney, Singapore"""
        cities = ["Miami", "Rotterdam", "Sydney", "Singapore"]
        for city in cities:
            res = LocationService.validate_location(query=city)
            self.assertIn(res.status, ["VALID_COASTAL", "VALID_MARINE"], f"Failed for international city {city}")
            self.assertTrue(res.is_coastal, f"{city} should be coastal")
            self.assertTrue(res.is_marine, f"{city} should have marine context")
            self.assertLess(res.distance_to_coast_km, 50.0)
            self.assertIsNotNone(res.marine_context)

    def test_offshore_marine_coordinates(self):
        """3. Valid offshore ocean coordinates (Bay of Bengal, Atlantic)"""
        # Bay of Bengal: 16.5, 83.0
        res_bob = LocationService.validate_coordinates(latitude=16.5, longitude=83.0)
        self.assertIn(res_bob.status, ["VALID_COASTAL", "VALID_MARINE"])
        self.assertTrue(res_bob.is_marine)
        self.assertIn("Bay of Bengal", res_bob.marine_context)

        # Atlantic: 25.0, -75.0
        res_atl = LocationService.validate_coordinates(latitude=25.0, longitude=-75.0)
        self.assertIn(res_atl.status, ["VALID_COASTAL", "VALID_MARINE"])
        self.assertTrue(res_atl.is_marine)
        self.assertTrue(any(w in res_atl.marine_context for w in ["Atlantic", "Caribbean", "Marine"]))

    def test_inland_cities_validation(self):
        """4. Inland cities: Hyderabad, New Delhi, Bengaluru, Paris, Dallas"""
        inland = ["Hyderabad", "New Delhi", "Bengaluru", "Paris", "Dallas"]
        for city in inland:
            res = LocationService.validate_location(query=city)
            self.assertEqual(res.status, "INLAND", f"Expected INLAND for {city}, got {res.status}")
            self.assertFalse(res.is_coastal, f"{city} must not be coastal")
            self.assertFalse(res.is_marine, f"{city} must not be marine")
            self.assertGreater(res.distance_to_coast_km, 50.0)
            self.assertIn("No seashore or marine area found", res.reason)

    def test_coordinate_input_parsing(self):
        """5. Coordinate inputs in different formats"""
        # Decimal format
        res1 = LocationService.validate_location(query="17.6868, 83.2185")
        self.assertIn(res1.status, ["VALID_COASTAL", "VALID_MARINE"])

        # Cardinal format (Miami)
        res2 = LocationService.validate_location(query="25.7617 N, 80.1918 W")
        self.assertIn(res2.status, ["VALID_COASTAL", "VALID_MARINE"])

        # Southern Hemisphere (Sydney)
        res3 = LocationService.validate_location(query="-33.8688, 151.2093")
        self.assertIn(res3.status, ["VALID_COASTAL", "VALID_MARINE"])

    def test_invalid_unresolved_location(self):
        """6. Invalid/unresolved nonsense location"""
        res = LocationService.validate_location(query="xyz999nonexistentlocation123")
        self.assertEqual(res.status, "UNRESOLVED")
        self.assertFalse(res.is_coastal)
        self.assertFalse(res.is_marine)
        self.assertIn("could not be resolved", res.reason)

    def test_api_search_endpoint_dynamic(self):
        """7. Test GET /api/v1/location/search with various queries"""
        # Test Indian query
        resp_in = self.client.get("/api/v1/location/search?query=Kochi")
        self.assertEqual(resp_in.status_code, 200)
        data_in = resp_in.json()
        self.assertGreater(data_in["total_results"], 0)
        self.assertTrue(data_in["results"][0]["is_coastal"])

        # Test International query
        resp_intl = self.client.get("/api/v1/location/search?query=Miami")
        self.assertEqual(resp_intl.status_code, 200)
        data_intl = resp_intl.json()
        self.assertGreater(data_intl["total_results"], 0)
        self.assertTrue(data_intl["results"][0]["is_coastal"])

    def test_api_reverse_geocode_endpoint(self):
        """8. Test POST /api/v1/location/reverse-geocode"""
        resp = self.client.post(
            "/api/v1/location/reverse-geocode",
            json={"latitude": 17.6868, "longitude": 83.2185},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "VALID_COASTAL")
        self.assertTrue(data["is_coastal"])
        self.assertLess(data["distance_to_coast_km"], 5.0)

    def test_api_dynamic_marine_conditions_coastal(self):
        """9. Test GET /api/v1/marine/conditions-dynamic for coastal location (Visakhapatnam)"""
        resp = self.client.get(
            "/api/v1/marine/conditions-dynamic?latitude=17.6868&longitude=83.2185&location_name=Visakhapatnam"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_coastal"])
        self.assertIn(data["availability_status"], ["AVAILABLE", "UNAVAILABLE", "PROVIDER_DOWN"])
        if data["availability_status"] == "AVAILABLE":
            self.assertIsNotNone(data["wave_height_m"])
            self.assertIsNotNone(data["sea_state"])
            self.assertIsNotNone(data["risk_level"])

    def test_api_dynamic_marine_conditions_inland(self):
        """10. Test GET /api/v1/marine/conditions-dynamic for inland location (Hyderabad)"""
        resp = self.client.get(
            "/api/v1/marine/conditions-dynamic?latitude=17.3850&longitude=78.4867&location_name=Hyderabad"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["is_coastal"])
        self.assertEqual(data["availability_status"], "INLAND_BLOCKED")
        self.assertEqual(data["safety_status"], "BLOCKED")
        self.assertIn("No seashore or marine area found", data["message"])
        # Must not fabricate wave height on inland land
        self.assertIsNone(data["wave_height_m"])


if __name__ == "__main__":
    unittest.main()
