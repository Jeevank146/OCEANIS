import json
import logging
import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests
from schemas.location import (
    LocationCandidate,
    LocationValidationResult,
)

logger = logging.getLogger("oceanis.services.location")

# Threshold distance to coast for a location to be considered coastal/marine (km)
COASTAL_THRESHOLD_KM = 50.0

# In-memory LRU-style cache for geocoding to avoid rate-limits and optimize responsiveness
_GEOCODE_CACHE: Dict[str, Any] = {}
_REVERSE_GEOCODE_CACHE: Dict[str, Any] = {}

# Comprehensive verified registry of coastal stations, ports, fishing harbours, and reference hubs
KNOWN_LOCATIONS: List[Dict[str, Any]] = [
    # --- ANDHRA PRADESH COAST ---
    {
        "id": "loc-vpt",
        "name": "Visakhapatnam Coast",
        "display_name": "Visakhapatnam, Andhra Pradesh, India",
        "city": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "country": "India",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.5,
        "place_type": "major_port",
        "nearest_port": "Visakhapatnam Port (VPT)",
        "marine_context": "Bay of Bengal • Andhra Pradesh Shelf",
        "keywords": ["visakhapatnam", "vizag", "vpt", "rushikonda", "rk beach", "gangavaram", "yarada", "waltair"],
    },
    {
        "id": "loc-kakinada",
        "name": "Kakinada Coast",
        "display_name": "Kakinada, Andhra Pradesh, India",
        "city": "Kakinada",
        "state": "Andhra Pradesh",
        "country": "India",
        "latitude": 16.9891,
        "longitude": 82.2475,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 1.2,
        "place_type": "deepwater_port",
        "nearest_port": "Kakinada Deepwater Port",
        "marine_context": "Bay of Bengal • Godavari Estuary & Spit",
        "keywords": ["kakinada", "godavari", "coringa", "hope island", "vakalapudi", "kakinada port", "surasaniyanam"],
    },
    {
        "id": "loc-machilipatnam",
        "name": "Machilipatnam Coast",
        "display_name": "Machilipatnam, Andhra Pradesh, India",
        "city": "Machilipatnam",
        "state": "Andhra Pradesh",
        "country": "India",
        "latitude": 16.1875,
        "longitude": 81.1389,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 2.0,
        "place_type": "fishing_harbour",
        "nearest_port": "Machilipatnam Port",
        "marine_context": "Bay of Bengal • Krishna River Delta",
        "keywords": ["machilipatnam", "bandar", "manginapudi", "gilakaladindi", "krishna delta"],
    },
    {
        "id": "loc-krishnapatnam",
        "name": "Krishnapatnam Port",
        "display_name": "Krishnapatnam, Nellore, Andhra Pradesh, India",
        "city": "Nellore",
        "state": "Andhra Pradesh",
        "country": "India",
        "latitude": 14.2500,
        "longitude": 80.1167,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.8,
        "place_type": "major_port",
        "nearest_port": "Krishnapatnam Port",
        "marine_context": "Bay of Bengal • South Andhra Shelf",
        "keywords": ["krishnapatnam", "nellore", "mypadu", "kandaleru", "tupilipalem"],
    },
    {
        "id": "loc-bheemunipatnam",
        "name": "Bheemunipatnam Coast",
        "display_name": "Bheemunipatnam, Visakhapatnam, Andhra Pradesh, India",
        "city": "Bheemunipatnam",
        "state": "Andhra Pradesh",
        "country": "India",
        "latitude": 17.8911,
        "longitude": 83.4542,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.4,
        "place_type": "fishing_harbour",
        "nearest_port": "Bheemili Fish Landing Centre",
        "marine_context": "Bay of Bengal • North Andhra Upwelling Zone",
        "keywords": ["bheemunipatnam", "bheemili", "gosthani", "tagarapuvalasa"],
    },
    {
        "id": "loc-bhavanapadu",
        "name": "Bhavanapadu Fishing Harbour",
        "display_name": "Bhavanapadu, Srikakulam, Andhra Pradesh, India",
        "city": "Srikakulam",
        "state": "Andhra Pradesh",
        "country": "India",
        "latitude": 18.5667,
        "longitude": 84.3500,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.3,
        "place_type": "fishing_harbour",
        "nearest_port": "Bhavanapadu Port",
        "marine_context": "Bay of Bengal • Kalingapatnam Ridge",
        "keywords": ["bhavanapadu", "srikakulam", "kalingapatnam", "baruva"],
    },

    # --- TAMIL NADU & PUDUCHERRY ---
    {
        "id": "loc-chennai",
        "name": "Chennai Coast",
        "display_name": "Chennai, Tamil Nadu, India",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 1.0,
        "place_type": "major_port",
        "nearest_port": "Chennai Port (ChPT)",
        "marine_context": "Bay of Bengal • Coromandel Coast",
        "keywords": ["chennai", "madras", "ennore", "kamarajar", "marina", "royapuram", "kasimedu"],
    },
    {
        "id": "loc-tuticorin",
        "name": "Thoothukudi (Tuticorin) Coast",
        "display_name": "Thoothukudi, Tamil Nadu, India",
        "city": "Thoothukudi",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 8.7642,
        "longitude": 78.1348,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.8,
        "place_type": "major_port",
        "nearest_port": "V.O. Chidambaranar Port (VOCPT)",
        "marine_context": "Gulf of Mannar • Palk Strait",
        "keywords": ["tuticorin", "thoothukudi", "voc", "gulf of mannar", "punnakayal"],
    },
    {
        "id": "loc-cuddalore",
        "name": "Cuddalore Fishing Harbour",
        "display_name": "Cuddalore, Tamil Nadu, India",
        "city": "Cuddalore",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 11.7480,
        "longitude": 79.7714,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 1.5,
        "place_type": "fishing_harbour",
        "nearest_port": "Cuddalore Minor Port",
        "marine_context": "Bay of Bengal • Uppanar Estuary",
        "keywords": ["cuddalore", "silver beach", "parangipettai", "uppanar"],
    },
    {
        "id": "loc-rameswaram",
        "name": "Rameswaram Coast",
        "display_name": "Rameswaram, Tamil Nadu, India",
        "city": "Rameswaram",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 9.2876,
        "longitude": 79.3129,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.2,
        "place_type": "fishing_harbour",
        "nearest_port": "Pamban Harbor",
        "marine_context": "Palk Bay • Gulf of Mannar Biosphere",
        "keywords": ["rameswaram", "pamban", "dhanushkodi", "mandapam"],
    },
    {
        "id": "loc-kanyakumari",
        "name": "Kanyakumari Coast",
        "display_name": "Kanyakumari, Tamil Nadu, India",
        "city": "Kanyakumari",
        "state": "Tamil Nadu",
        "country": "India",
        "latitude": 8.0883,
        "longitude": 77.5385,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.2,
        "place_type": "coastal_station",
        "nearest_port": "Chinnamuttam Fishing Harbour",
        "marine_context": "Indian Ocean • Arabian Sea & Bay of Bengal Tri-Junction",
        "keywords": ["kanyakumari", "chinnamuttam", "muttam", "colachel"],
    },
    {
        "id": "loc-puducherry",
        "name": "Puducherry Coast",
        "display_name": "Puducherry, Union Territory of Puducherry, India",
        "city": "Puducherry",
        "state": "Puducherry",
        "country": "India",
        "latitude": 11.9416,
        "longitude": 79.8083,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.5,
        "place_type": "fishing_harbour",
        "nearest_port": "Puducherry Port",
        "marine_context": "Bay of Bengal • Coromandel Sector",
        "keywords": ["puducherry", "pondicherry", "promenade", "thengaithittu"],
    },

    # --- MAHARASHTRA & GOA ---
    {
        "id": "loc-mumbai",
        "name": "Mumbai Coast",
        "display_name": "Mumbai, Maharashtra, India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 18.9400,
        "longitude": 72.8350,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.5,
        "place_type": "major_port",
        "nearest_port": "Mumbai Port (MbPT) & JNPA",
        "marine_context": "Arabian Sea • Konkan Sector",
        "keywords": ["mumbai", "bombay", "jnpt", "jnpa", "sassoon dock", "versova", "colaba", "bandra"],
    },
    {
        "id": "loc-ratnagiri",
        "name": "Ratnagiri Coast",
        "display_name": "Ratnagiri, Maharashtra, India",
        "city": "Ratnagiri",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 16.9902,
        "longitude": 73.3120,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 1.0,
        "place_type": "fishing_harbour",
        "nearest_port": "Mirkarwada Fishing Harbour",
        "marine_context": "Arabian Sea • South Konkan Shelf",
        "keywords": ["ratnagiri", "mirkarwada", "jaigad", "bhatye", "ganpatipule"],
    },
    {
        "id": "loc-goa",
        "name": "Goa (Mormugao) Coast",
        "display_name": "Mormugao, Goa, India",
        "city": "Mormugao",
        "state": "Goa",
        "country": "India",
        "latitude": 15.4167,
        "longitude": 73.8000,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.4,
        "place_type": "major_port",
        "nearest_port": "Mormugao Port (MPT)",
        "marine_context": "Arabian Sea • Goa Coastal Fairway",
        "keywords": ["goa", "mormugao", "panaji", "vasco", "calangute", "candolim", "betul", "malpe"],
    },

    # --- KERALA & KARNATAKA ---
    {
        "id": "loc-kochi",
        "name": "Kochi (Cochin) Coast",
        "display_name": "Kochi, Kerala, India",
        "city": "Kochi",
        "state": "Kerala",
        "country": "India",
        "latitude": 9.9312,
        "longitude": 76.2673,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.8,
        "place_type": "major_port",
        "nearest_port": "Cochin Port (CoPA) & ICTT Vallarpadam",
        "marine_context": "Arabian Sea • Malabar Coast & Vembanad",
        "keywords": ["kochi", "cochin", "thoppumpady", "munambam", "fort kochi", "vallarpadam", "ernakulam"],
    },
    {
        "id": "loc-kozhikode",
        "name": "Kozhikode (Calicut) Coast",
        "display_name": "Kozhikode, Kerala, India",
        "city": "Kozhikode",
        "state": "Kerala",
        "country": "India",
        "latitude": 11.2588,
        "longitude": 75.7804,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.6,
        "place_type": "fishing_harbour",
        "nearest_port": "Beypore Port & Fishing Harbour",
        "marine_context": "Arabian Sea • North Malabar Shelf",
        "keywords": ["kozhikode", "calicut", "beypore", "puthiyappa", "kappad"],
    },
    {
        "id": "loc-mangaluru",
        "name": "Mangaluru (Mangalore) Coast",
        "display_name": "Mangaluru, Karnataka, India",
        "city": "Mangaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.9141,
        "longitude": 74.8560,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 1.2,
        "place_type": "major_port",
        "nearest_port": "New Mangalore Port (NMPT)",
        "marine_context": "Arabian Sea • Canara Coast",
        "keywords": ["mangaluru", "mangalore", "nmpt", "panambur", "old port", "tannirbhavi", "malpe", "udupi"],
    },
    {
        "id": "loc-karwar",
        "name": "Karwar Coast",
        "display_name": "Karwar, Uttara Kannada, Karnataka, India",
        "city": "Karwar",
        "state": "Karnataka",
        "country": "India",
        "latitude": 14.8054,
        "longitude": 74.1240,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.4,
        "place_type": "major_port",
        "nearest_port": "Karwar Port / INS Kadamba",
        "marine_context": "Arabian Sea • Kali Estuary & Seabird Corridor",
        "keywords": ["karwar", "baithkol", "tadadi", "ankola", "gokarna", "kadamba"],
    },

    # --- ODISHA & WEST BENGAL ---
    {
        "id": "loc-paradip",
        "name": "Paradip Coast",
        "display_name": "Paradip, Jagatsinghpur, Odisha, India",
        "city": "Paradip",
        "state": "Odisha",
        "country": "India",
        "latitude": 20.2644,
        "longitude": 86.6710,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.5,
        "place_type": "major_port",
        "nearest_port": "Paradip Port (PPT)",
        "marine_context": "Bay of Bengal • Mahanadi Delta Shelf",
        "keywords": ["paradip", "paradeep", "mahanadi", "jagatsinghpur", "jatadhari", "nuagarh"],
    },
    {
        "id": "loc-gopalpur",
        "name": "Gopalpur Coast",
        "display_name": "Gopalpur, Ganjam, Odisha, India",
        "city": "Gopalpur",
        "state": "Odisha",
        "country": "India",
        "latitude": 19.2600,
        "longitude": 84.9100,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.4,
        "place_type": "deepwater_port",
        "nearest_port": "Gopalpur Port",
        "marine_context": "Bay of Bengal • Rushikulya Marine Sanctuary",
        "keywords": ["gopalpur", "ganjam", "rushikulya", "berhampur", "chhatrapur"],
    },
    {
        "id": "loc-puri",
        "name": "Puri Coast",
        "display_name": "Puri, Odisha, India",
        "city": "Puri",
        "state": "Odisha",
        "country": "India",
        "latitude": 19.8135,
        "longitude": 85.8312,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.3,
        "place_type": "fishing_harbour",
        "nearest_port": "Puri Fish Landing Centre / Chilika Mouth",
        "marine_context": "Bay of Bengal • Chilika Lagoon Barrier",
        "keywords": ["puri", "chilika", "chandrabhaga", "konark", "satapada", "arukhuda"],
    },
    {
        "id": "loc-digha",
        "name": "Digha Coast",
        "display_name": "Digha, Purba Medinipur, West Bengal, India",
        "city": "Digha",
        "state": "West Bengal",
        "country": "India",
        "latitude": 21.6266,
        "longitude": 87.5074,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.3,
        "place_type": "fishing_harbour",
        "nearest_port": "Shankarpur Fishing Harbour",
        "marine_context": "Bay of Bengal • Bengal Basin Shallow Shelf",
        "keywords": ["digha", "shankarpur", "tajpur", "mandarmani", "haldia", "sagar island", "kakdwip"],
    },

    # --- GUJARAT ---
    {
        "id": "loc-veraval",
        "name": "Veraval Fishing Harbour",
        "display_name": "Veraval, Gir Somnath, Gujarat, India",
        "city": "Veraval",
        "state": "Gujarat",
        "country": "India",
        "latitude": 20.9000,
        "longitude": 70.3667,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.2,
        "place_type": "fishing_harbour",
        "nearest_port": "Veraval Major Fishing Port",
        "marine_context": "Arabian Sea • Saurashtra Pelagic Basin",
        "keywords": ["veraval", "somnath", "porbandar", "okha", "kandla", "mundra", "pipavav"],
    },

    # --- ISLAND TERRITORIES ---
    {
        "id": "loc-portblair",
        "name": "Port Blair Coast",
        "display_name": "Port Blair, Andaman & Nicobar Islands, India",
        "city": "Port Blair",
        "state": "Andaman & Nicobar",
        "country": "India",
        "latitude": 11.6234,
        "longitude": 92.7265,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.2,
        "place_type": "major_port",
        "nearest_port": "Port Blair Harbour (Haddo Wharf)",
        "marine_context": "Andaman Sea • Bay of Bengal Pelagic Corridor",
        "keywords": ["port blair", "andaman", "nicobar", "havelock", "swaraj dweep", "neil island", "haddo"],
    },
    {
        "id": "loc-kavaratti",
        "name": "Kavaratti Island",
        "display_name": "Kavaratti, Union Territory of Lakshadweep, India",
        "city": "Kavaratti",
        "state": "Lakshadweep",
        "country": "India",
        "latitude": 10.5667,
        "longitude": 72.6333,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.1,
        "place_type": "island_port",
        "nearest_port": "Kavaratti Jetty",
        "marine_context": "Arabian Sea • Lakshadweep Coral Atoll Lagoon",
        "keywords": ["kavaratti", "lakshadweep", "agatti", "minicoy", "andrott"],
    },

    # --- INTERNATIONAL COASTAL REFERENCE STATIONS ---
    {
        "id": "loc-miami",
        "name": "Miami Coast",
        "display_name": "Miami, Florida, United States",
        "city": "Miami",
        "state": "Florida",
        "country": "United States",
        "latitude": 25.7617,
        "longitude": -80.1918,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.5,
        "place_type": "major_port",
        "nearest_port": "PortMiami",
        "marine_context": "North Atlantic • Straits of Florida & Gulf Stream",
        "keywords": ["miami", "portmiami", "biscayne", "florida keys", "south beach"],
    },
    {
        "id": "loc-rotterdam",
        "name": "Rotterdam Port",
        "display_name": "Rotterdam, South Holland, Netherlands",
        "city": "Rotterdam",
        "state": "South Holland",
        "country": "Netherlands",
        "latitude": 51.9244,
        "longitude": 4.4777,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 1.5,
        "place_type": "major_port",
        "nearest_port": "Port of Rotterdam (Europoort)",
        "marine_context": "North Sea • Rhine-Meuse-Scheldt Delta",
        "keywords": ["rotterdam", "europoort", "maasvlakte", "hoek van holland", "south holland"],
    },
    {
        "id": "loc-singapore",
        "name": "Singapore Coast & Port",
        "display_name": "Singapore, Republic of Singapore",
        "city": "Singapore",
        "state": "Central Region",
        "country": "Singapore",
        "latitude": 1.3521,
        "longitude": 103.8198,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.8,
        "place_type": "major_port",
        "nearest_port": "Port of Singapore (PSA)",
        "marine_context": "Singapore Strait • Malacca Pelagic Gateway",
        "keywords": ["singapore", "jurong", "tuas", "marina bay", "sentosa", "keppel"],
    },
    {
        "id": "loc-sydney",
        "name": "Sydney Coast & Harbour",
        "display_name": "Sydney, New South Wales, Australia",
        "city": "Sydney",
        "state": "New South Wales",
        "country": "Australia",
        "latitude": -33.8688,
        "longitude": 151.2093,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.4,
        "place_type": "major_port",
        "nearest_port": "Port Jackson / Port Botany",
        "marine_context": "Tasman Sea • South Pacific Coastal Sector",
        "keywords": ["sydney", "port jackson", "botany bay", "manly", "bondi", "darling harbour"],
    },
    {
        "id": "loc-dubai",
        "name": "Dubai Coast & Jebel Ali",
        "display_name": "Dubai, United Arab Emirates",
        "city": "Dubai",
        "state": "Dubai Emirate",
        "country": "United Arab Emirates",
        "latitude": 25.2048,
        "longitude": 55.2708,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 0.6,
        "place_type": "major_port",
        "nearest_port": "Port of Jebel Ali",
        "marine_context": "Persian Gulf • Arabian Sea Gateway",
        "keywords": ["dubai", "jebel ali", "port rashid", "deira", "jumeirah"],
    },
    {
        "id": "loc-tokyo",
        "name": "Tokyo Bay Coast",
        "display_name": "Tokyo, Kantō, Japan",
        "city": "Tokyo",
        "state": "Tokyo Metropolis",
        "country": "Japan",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "is_coastal": True,
        "is_marine": True,
        "distance_to_coast_km": 1.0,
        "place_type": "major_port",
        "nearest_port": "Port of Tokyo / Yokohama",
        "marine_context": "North Pacific • Tokyo Bay Basin",
        "keywords": ["tokyo", "yokohama", "odaiba", "tokyo bay", "chiba"],
    },

    # --- INLAND HUBS (FOR INLAND VALIDATION) ---
    {
        "id": "loc-hyderabad",
        "name": "Hyderabad",
        "display_name": "Hyderabad, Telangana, India",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "is_coastal": False,
        "is_marine": False,
        "distance_to_coast_km": 278.0,
        "place_type": "inland_city",
        "nearest_port": "Machilipatnam Port (285 km)",
        "marine_context": None,
        "keywords": ["hyderabad", "secunderabad", "telangana", "cyberabad", "hitec city"],
    },
    {
        "id": "loc-delhi",
        "name": "New Delhi",
        "display_name": "New Delhi, Delhi, India",
        "city": "New Delhi",
        "state": "Delhi",
        "country": "India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "is_coastal": False,
        "is_marine": False,
        "distance_to_coast_km": 1050.0,
        "place_type": "inland_city",
        "nearest_port": "Kandla Port (1080 km)",
        "marine_context": None,
        "keywords": ["delhi", "new delhi", "ncr", "noida", "gurugram", "gurgaon"],
    },
    {
        "id": "loc-bengaluru",
        "name": "Bengaluru",
        "display_name": "Bengaluru, Karnataka, India",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "is_coastal": False,
        "is_marine": False,
        "distance_to_coast_km": 285.0,
        "place_type": "inland_city",
        "nearest_port": "Chennai Port (290 km) / Mangalore (310 km)",
        "marine_context": None,
        "keywords": ["bengaluru", "bangalore", "whitefield", "electronic city", "mysore"],
    },
    {
        "id": "loc-nagpur",
        "name": "Nagpur",
        "display_name": "Nagpur, Maharashtra, India",
        "city": "Nagpur",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 21.1458,
        "longitude": 79.0882,
        "is_coastal": False,
        "is_marine": False,
        "distance_to_coast_km": 620.0,
        "place_type": "inland_city",
        "nearest_port": "Paradip Port (640 km) / Mumbai Port (710 km)",
        "marine_context": None,
        "keywords": ["nagpur", "vidarbha", "wardha"],
    },
    {
        "id": "loc-pune",
        "name": "Pune",
        "display_name": "Pune, Maharashtra, India",
        "city": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "is_coastal": False,
        "is_marine": False,
        "distance_to_coast_km": 115.0,
        "place_type": "inland_city",
        "nearest_port": "Mumbai Port / JNPT (120 km)",
        "marine_context": None,
        "keywords": ["pune", "pcmc", "haveli"],
    },
    {
        "id": "loc-paris",
        "name": "Paris",
        "display_name": "Paris, Île-de-France, France",
        "city": "Paris",
        "state": "Île-de-France",
        "country": "France",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "is_coastal": False,
        "is_marine": False,
        "distance_to_coast_km": 170.0,
        "place_type": "inland_city",
        "nearest_port": "Le Havre Port (180 km)",
        "marine_context": None,
        "keywords": ["paris", "france", "ile-de-france"],
    },
    {
        "id": "loc-dallas",
        "name": "Dallas",
        "display_name": "Dallas, Texas, United States",
        "city": "Dallas",
        "state": "Texas",
        "country": "United States",
        "latitude": 32.7767,
        "longitude": -96.7970,
        "is_coastal": False,
        "is_marine": False,
        "distance_to_coast_km": 420.0,
        "place_type": "inland_city",
        "nearest_port": "Port of Houston (390 km)",
        "marine_context": None,
        "keywords": ["dallas", "fort worth", "texas", "dfw"],
    },
]

# Global coastline anchor mesh covering all major continents and sea lines
GLOBAL_COASTLINE_POINTS: List[Tuple[float, float]] = [
    # 1. INDIAN SUBCONTINENT (Dense mesh)
    # Gujarat & Gulf of Kutch / Khambhat
    (23.2, 68.6), (22.5, 69.1), (21.7, 69.4), (20.9, 70.4), (20.7, 71.0),
    (21.1, 72.0), (21.6, 72.5), (20.8, 72.8), (20.0, 72.7),
    # Maharashtra & Goa
    (19.3, 72.8), (18.9, 72.8), (18.4, 72.9), (17.7, 73.1), (17.0, 73.3),
    (16.2, 73.5), (15.5, 73.7), (15.0, 74.0),
    # Karnataka & Kerala
    (14.5, 74.3), (13.9, 74.5), (13.3, 74.7), (12.8, 74.8), (12.2, 75.0),
    (11.3, 75.7), (10.8, 75.9), (10.0, 76.2), (9.3, 76.4), (8.5, 76.9), (8.1, 77.5),
    # Tamil Nadu & Coromandel
    (8.2, 77.7), (8.7, 78.1), (9.2, 79.1), (9.3, 79.3), (9.8, 79.2),
    (10.3, 79.5), (10.8, 79.8), (11.7, 79.8), (12.2, 80.0), (12.8, 80.2), (13.3, 80.3),
    # Andhra Pradesh
    (13.8, 80.2), (14.3, 80.1), (15.2, 80.1), (15.9, 80.5), (16.2, 81.1),
    (16.5, 81.7), (16.9, 82.2), (17.3, 82.6), (17.7, 83.2), (18.1, 83.7),
    (18.6, 84.3), (19.0, 84.7),
    # Odisha & West Bengal
    (19.3, 84.9), (19.8, 85.8), (20.3, 86.7), (20.8, 86.9), (21.5, 87.4),
    (21.6, 87.7), (21.7, 88.1), (21.6, 88.8),
    # Andaman & Nicobar & Lakshadweep
    (13.2, 92.9), (11.6, 92.7), (9.1, 92.8), (7.0, 93.8),
    (10.6, 72.6), (8.3, 73.0),
    # Sri Lanka & Maldives
    (9.7, 80.0), (8.6, 81.2), (6.9, 81.9), (6.0, 80.2), (4.2, 73.5), (0.7, 73.1),

    # 2. NORTH AMERICA (Atlantic, Pacific, Gulf of Mexico, Caribbean)
    (44.6, -63.6), (42.4, -71.0), (40.7, -74.0), (38.9, -76.4), (36.8, -76.0),
    (32.8, -79.9), (30.3, -81.4), (25.8, -80.2), (24.6, -81.8), (27.8, -82.6),
    (30.2, -88.0), (29.9, -90.1), (29.3, -94.8), (26.0, -97.2), (21.2, -86.8),
    (19.2, -96.1), (15.8, -97.1), (20.6, -105.2), (23.2, -106.4), (32.7, -117.2),
    (33.7, -118.2), (37.8, -122.4), (46.2, -124.0), (47.6, -122.3), (49.3, -123.1),
    (58.3, -134.4), (21.3, -157.8), (18.2, -66.1), (23.1, -82.4), (18.0, -76.8),

    # 3. EUROPE & MEDITERRANEAN (North Sea, Baltic, Atlantic, Med, Black Sea)
    (51.9, 4.5), (52.4, 4.9), (53.5, 9.9), (51.2, 2.9), (51.5, 0.1),
    (50.8, -1.4), (50.4, -4.1), (53.4, -3.0), (55.9, -3.2), (53.3, -6.3),
    (48.4, -4.5), (44.8, -0.6), (43.3, -8.4), (41.2, -8.7), (38.7, -9.1),
    (36.1, -5.3), (36.7, -4.4), (39.5, 2.6), (41.4, 2.2), (43.3, 5.4),
    (43.7, 7.3), (44.4, 8.9), (40.8, 14.3), (38.1, 13.4), (37.5, 15.1),
    (45.4, 12.3), (42.6, 18.1), (37.9, 23.7), (35.3, 25.1), (41.0, 29.0),
    (44.2, 28.7), (46.5, 30.7), (55.7, 12.6), (59.3, 18.1), (60.2, 24.9),
    (59.9, 10.7), (60.4, 5.3), (64.1, -21.9),

    # 4. EAST & SOUTHEAST ASIA
    (35.7, 139.7), (34.7, 135.5), (33.6, 130.4), (43.1, 141.3), (35.1, 129.0),
    (37.5, 126.6), (38.9, 121.6), (39.0, 117.7), (36.1, 120.4), (31.2, 121.5),
    (29.9, 121.5), (24.5, 118.1), (22.3, 114.2), (22.5, 113.9), (25.0, 121.5),
    (22.6, 120.3), (14.6, 121.0), (10.3, 123.9), (10.8, 106.7), (16.1, 108.2),
    (13.7, 100.5), (3.1, 101.7), (5.4, 100.3), (1.4, 103.8), (-6.2, 106.8),
    (-7.2, 112.7), (-8.7, 115.2), (21.9, 91.8), (16.8, 96.2), (24.9, 67.0),

    # 5. MIDDLE EAST & RED SEA
    (25.2, 55.3), (24.5, 54.4), (25.3, 51.5), (26.2, 50.6), (29.4, 48.0),
    (26.4, 50.1), (23.6, 58.6), (17.0, 54.1), (21.5, 39.2), (24.1, 38.1),
    (29.5, 35.0), (32.8, 35.0), (33.9, 35.5), (31.2, 29.9), (31.3, 32.3),

    # 6. OCEANIA (Australia, New Zealand, Pacific)
    (-33.9, 151.2), (-37.8, 144.9), (-27.5, 153.0), (-16.9, 145.8), (-12.5, 130.8),
    (-31.9, 115.8), (-34.9, 138.6), (-42.9, 147.3), (-36.8, 174.8), (-41.3, 174.8),
    (-43.5, 172.6), (-18.1, 178.4), (-17.5, -149.6), (13.4, 144.8),

    # 7. AFRICA (North, South, East, West)
    (-33.9, 18.4), (-29.9, 31.0), (-34.0, 25.6), (-26.0, 32.6), (-6.8, 39.3),
    (-4.0, 39.7), (-20.2, 57.5), (-4.7, 55.5), (6.4, 3.4), (5.6, -0.2),
    (5.3, -4.0), (14.7, -17.4), (-8.8, 13.2), (33.6, -7.6), (35.8, -5.8),
    (36.8, 3.0), (36.8, 10.2),
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points on Earth in km."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def calculate_distance_to_nearest_coast(lat: float, lon: float) -> Tuple[float, Tuple[float, float]]:
    """Calculates distance in km to the closest point along the global coastline."""
    min_dist = float("inf")
    closest_pt = GLOBAL_COASTLINE_POINTS[0]

    for pt in GLOBAL_COASTLINE_POINTS:
        dist = haversine_km(lat, lon, pt[0], pt[1])
        if dist < min_dist:
            min_dist = dist
            closest_pt = pt

    return min_dist, closest_pt


def is_offshore_sea_coordinate(lat: float, lon: float) -> Tuple[bool, Optional[str]]:
    """
    Determines if a coordinate lies within offshore sea/ocean waters worldwide.
    Identifies ocean basins including:
    - Bay of Bengal, Arabian Sea, Indian Ocean, Andaman Sea, Lakshadweep Sea
    - North Atlantic, South Atlantic, Caribbean Sea, Gulf of Mexico
    - North Pacific, South Pacific, Coral Sea, Tasman Sea
    - Mediterranean Sea, North Sea, Baltic Sea
    - South China Sea, East China Sea, Sea of Japan
    - Persian Gulf, Red Sea
    """
    # 1. Bay of Bengal Offshore Sector
    if 4.0 <= lat <= 22.5 and 80.0 <= lon <= 94.0:
        return True, "Bay of Bengal Offshore Sector"

    # 2. Arabian Sea Offshore Sector
    if 4.0 <= lat <= 25.0 and 55.0 <= lon <= 77.0:
        return True, "Arabian Sea Offshore Sector"

    # 3. Andaman & Nicobar Sea
    if 5.0 <= lat <= 15.0 and 91.5 <= lon <= 96.0:
        return True, "Andaman Sea Pelagic Basin"

    # 4. Lakshadweep Sea
    if 7.0 <= lat <= 13.5 and 70.0 <= lon <= 74.5:
        return True, "Lakshadweep Sea Lagoon"

    # 5. Southern / Equatorial Indian Ocean
    if -30.0 <= lat < 5.0 and 40.0 <= lon <= 110.0:
        return True, "Equatorial Indian Ocean Basin"

    # 6. North Atlantic Ocean
    if 0.0 <= lat <= 65.0 and -80.0 <= lon <= -10.0:
        if 10.0 <= lat <= 30.0 and -88.0 <= lon <= -60.0:
            return True, "Caribbean Sea & Straits of Florida"
        if 20.0 <= lat <= 30.0 and -98.0 <= lon <= -82.0:
            return True, "Gulf of Mexico Marine Basin"
        return True, "North Atlantic Pelagic Sector"

    # 7. South Atlantic Ocean
    if -60.0 <= lat < 0.0 and -60.0 <= lon <= 20.0:
        return True, "South Atlantic Pelagic Basin"

    # 8. North Pacific Ocean
    if 0.0 <= lat <= 60.0 and (-180.0 <= lon <= -120.0 or 120.0 <= lon <= 180.0):
        return True, "North Pacific Marine Corridor"

    # 9. South Pacific Ocean & Tasman / Coral Sea
    if -55.0 <= lat < 0.0 and (140.0 <= lon <= 180.0 or -180.0 <= lon <= -70.0):
        if -45.0 <= lat <= -20.0 and 150.0 <= lon <= 175.0:
            return True, "Tasman Sea & Coral Sea Sector"
        return True, "South Pacific Pelagic Basin"

    # 10. North Sea & Baltic Sea
    if 50.0 <= lat <= 65.0 and -4.0 <= lon <= 25.0:
        return True, "North Sea & Baltic Marine Fairway"

    # 11. Mediterranean Sea
    if 30.0 <= lat <= 45.0 and -5.0 <= lon <= 36.0:
        return True, "Mediterranean Sea Basin"

    # 12. South China Sea & East Asia Seas
    if 0.0 <= lat <= 30.0 and 100.0 <= lon <= 130.0:
        return True, "South China Sea Maritime Sector"

    # 13. Persian Gulf & Gulf of Oman
    if 22.0 <= lat <= 30.0 and 48.0 <= lon <= 60.0:
        return True, "Persian Gulf & Gulf of Oman"

    # 14. Red Sea
    if 12.0 <= lat <= 30.0 and 32.0 <= lon <= 44.0:
        return True, "Red Sea Marine Corridor"

    return False, None


def format_coordinates(lat: float, lon: float) -> str:
    """Formats decimal latitude and longitude into user-friendly string."""
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"{abs(lat):.4f}° {lat_dir}, {abs(lon):.4f}° {lon_dir}"


def parse_raw_coordinates(query: str) -> Optional[Tuple[float, float]]:
    """
    Parses coordinate string formats:
    - 17.6868, 83.2185
    - 17.6868 N, 83.2185 E
    - 25.7617 N, 80.1918 W
    - -33.8688, 151.2093
    - lat: 17.68 lon: 83.21
    - 17.6868° N, 83.2185° E
    """
    cleaned = (
        query.strip()
        .replace("°", "")
        .replace("lat:", "")
        .replace("lon:", "")
        .replace("latitude:", "")
        .replace("longitude:", "")
    )

    pattern = re.compile(
        r"^(-?\d+(\.\d+)?)\s*([NSEWnsew])?\s*[,/ ]\s*(-?\d+(\.\d+)?)\s*([NSEWnsew])?$"
    )
    match = pattern.match(cleaned)
    if match:
        lat = float(match.group(1))
        lat_dir = match.group(3)
        lon = float(match.group(4))
        lon_dir = match.group(6)

        if lat_dir and lat_dir.upper() == "S":
            lat = -abs(lat)
        if lon_dir and lon_dir.upper() == "W":
            lon = -abs(lon)

        if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
            return lat, lon

    return None


class LocationService:
    """
    Core dynamic Location Intelligence Service:
    - Truly location-agnostic, supporting any coastal port, harbour, city, village, sea area worldwide
    - Coordinate parsing & dynamic validation against global coastline and ocean models
    - Unrestricted dynamic geocoding & reverse geocoding via OpenStreetMap Nominatim with local fallback
    - Categorization into VALID_COASTAL, VALID_MARINE, INLAND, UNRESOLVED with descriptive reasons
    """

    @classmethod
    def get_curated_suggestions(cls) -> List[LocationCandidate]:
        """Returns top curated coastal stations for quick selection."""
        coastal_only = [loc for loc in KNOWN_LOCATIONS if loc.get("is_coastal", False)]
        candidates = []
        for loc in coastal_only[:9]:
            candidates.append(
                LocationCandidate(
                    id=loc["id"],
                    name=loc["name"],
                    display_name=loc["display_name"],
                    city=loc.get("city"),
                    state=loc.get("state"),
                    country=loc.get("country", "India"),
                    latitude=loc["latitude"],
                    longitude=loc["longitude"],
                    is_coastal=loc["is_coastal"],
                    is_marine=loc["is_marine"],
                    distance_to_coast_km=loc["distance_to_coast_km"],
                    place_type=loc["place_type"],
                    nearest_port=loc.get("nearest_port"),
                    marine_context=loc.get("marine_context"),
                )
            )
        return candidates

    @classmethod
    def search_locations(cls, query: str, limit: int = 10) -> List[LocationCandidate]:
        """
        Dynamically searches coastal places, ports, harbours, cities, and coordinates globally.
        1. Checks coordinates if format matches.
        2. Queries internal high-performance registry.
        3. Queries OpenStreetMap Nominatim globally without country restrictions.
        """
        q = query.strip().lower()
        if not q:
            return cls.get_curated_suggestions()

        # 1. Coordinate query check
        coords = parse_raw_coordinates(query)
        if coords:
            validated = cls.validate_coordinates(coords[0], coords[1])
            return [
                LocationCandidate(
                    id=f"coord-{coords[0]:.4f}-{coords[1]:.4f}",
                    name=validated.location_name,
                    display_name=validated.display_name,
                    city=validated.city,
                    state=validated.state,
                    country=validated.country or "Global Marine",
                    latitude=coords[0],
                    longitude=coords[1],
                    is_coastal=validated.is_coastal,
                    is_marine=validated.is_marine,
                    distance_to_coast_km=validated.distance_to_coast_km or 0.0,
                    place_type="marine_coordinate" if validated.is_marine else "custom_coordinate",
                    nearest_port=validated.nearest_port,
                    marine_context=validated.marine_context,
                )
            ]

        candidates: List[LocationCandidate] = []
        seen_ids = set()

        # 2. Local Registry Match (Fast path)
        matched_results: List[Tuple[int, Dict[str, Any]]] = []
        for loc in KNOWN_LOCATIONS:
            score = 0
            name_lower = loc["name"].lower()
            city_lower = (loc.get("city") or "").lower()
            state_lower = (loc.get("state") or "").lower()
            country_lower = (loc.get("country") or "").lower()
            keywords = [k.lower() for k in loc.get("keywords", [])]

            if q == city_lower or q == name_lower:
                score += 100
            elif q in name_lower or q in city_lower:
                score += 50
            elif any(q in kw for kw in keywords):
                score += 30
            elif any(kw in q for kw in keywords):
                score += 25
            elif q in state_lower or q in country_lower:
                score += 10

            if score > 0:
                if loc.get("is_coastal", False):
                    score += 15
                matched_results.append((score, loc))

        matched_results.sort(key=lambda x: x[0], reverse=True)

        for _, loc in matched_results:
            if loc["id"] in seen_ids:
                continue
            seen_ids.add(loc["id"])
            candidates.append(
                LocationCandidate(
                    id=loc["id"],
                    name=loc["name"],
                    display_name=loc["display_name"],
                    city=loc.get("city"),
                    state=loc.get("state"),
                    country=loc.get("country", "India"),
                    latitude=loc["latitude"],
                    longitude=loc["longitude"],
                    is_coastal=loc["is_coastal"],
                    is_marine=loc["is_marine"],
                    distance_to_coast_km=loc["distance_to_coast_km"],
                    place_type=loc["place_type"],
                    nearest_port=loc.get("nearest_port"),
                    marine_context=loc.get("marine_context"),
                )
            )

        # 3. Dynamic External Geocoding (Global, unrestricted)
        if len(q) >= 2 and len(candidates) < limit:
            external_results = cls._query_external_geocoding(query, limit=limit)
            for ext in external_results:
                if ext.id not in seen_ids and not any(
                    haversine_km(ext.latitude, ext.longitude, c.latitude, c.longitude) < 5.0
                    for c in candidates
                ):
                    seen_ids.add(ext.id)
                    candidates.append(ext)

        return candidates[:limit]

    @classmethod
    def validate_location(
        cls,
        query: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> LocationValidationResult:
        """
        Validates whether a location or coordinate is coastal/marine, inland, or unresolved.
        Provides detailed rationale, coordinates, distance to coast, and marine context.
        """
        if latitude is not None and longitude is not None:
            return cls.validate_coordinates(latitude, longitude, custom_name=query)

        if not query or not query.strip():
            return LocationValidationResult(
                status="UNRESOLVED",
                is_coastal=False,
                is_marine=False,
                location_name="Unspecified Location",
                display_name="No location query provided",
                reason="Please enter a location name, port, or coordinates to validate.",
            )

        # Check if query is coordinate string
        coords = parse_raw_coordinates(query)
        if coords:
            return cls.validate_coordinates(coords[0], coords[1])

        # Search matching location dynamically
        results = cls.search_locations(query, limit=5)
        if results:
            best = results[0]
            dist_km = best.distance_to_coast_km
            coords_fmt = format_coordinates(best.latitude, best.longitude)

            if best.is_coastal or best.is_marine:
                status_code = "VALID_MARINE" if best.place_type == "marine_coordinate" else "VALID_COASTAL"
                return LocationValidationResult(
                    status=status_code,
                    is_coastal=True,
                    is_marine=True,
                    location_name=best.name,
                    display_name=best.display_name,
                    city=best.city,
                    state=best.state,
                    country=best.country or "India",
                    latitude=best.latitude,
                    longitude=best.longitude,
                    distance_to_coast_km=dist_km,
                    nearest_port=best.nearest_port or f"{best.city or best.name} Port / Harbour",
                    marine_context=best.marine_context or f"Coastal Waters • {best.state or best.country or 'Marine'}",
                    reason="Coastal location detected. Marine intelligence available for this area.",
                    coordinates_formatted=coords_fmt,
                )
            else:
                return LocationValidationResult(
                    status="INLAND",
                    is_coastal=False,
                    is_marine=False,
                    location_name=best.name,
                    display_name=best.display_name,
                    city=best.city,
                    state=best.state,
                    country=best.country or "India",
                    latitude=best.latitude,
                    longitude=best.longitude,
                    distance_to_coast_km=dist_km,
                    nearest_port=best.nearest_port,
                    marine_context=None,
                    reason=f"⚠️ No seashore or marine area found at this location ({dist_km:.0f} km from nearest coast).",
                    coordinates_formatted=coords_fmt,
                )

        return LocationValidationResult(
            status="UNRESOLVED",
            is_coastal=False,
            is_marine=False,
            location_name=query.strip(),
            display_name=f"'{query.strip()}' (Unresolved)",
            reason="⚠️ Location could not be resolved. Please verify spelling or provide coordinates (e.g. 17.68, 83.21).",
        )

    @classmethod
    def validate_coordinates(
        cls,
        latitude: float,
        longitude: float,
        custom_name: Optional[str] = None,
    ) -> LocationValidationResult:
        """
        Validates latitude/longitude against the global coastline and ocean basin model.
        """
        dist_to_coast, _ = calculate_distance_to_nearest_coast(latitude, longitude)
        coords_fmt = format_coordinates(latitude, longitude)

        # Check for known nearby port from registry
        nearest_port_name = None
        min_port_dist = float("inf")
        matched_loc_name = None
        matched_marine_context = None
        matched_country = "India" if (6.0 <= latitude <= 37.0 and 68.0 <= longitude <= 98.0) else "International"

        for loc in KNOWN_LOCATIONS:
            p_dist = haversine_km(latitude, longitude, loc["latitude"], loc["longitude"])
            if p_dist < min_port_dist:
                min_port_dist = p_dist
                nearest_port_name = loc.get("nearest_port") or loc["name"]
                if loc.get("is_coastal"):
                    matched_marine_context = loc.get("marine_context")
                if p_dist < 15.0:
                    matched_loc_name = loc["name"]
                    matched_country = loc.get("country", matched_country)

        # Check if coordinate is in offshore ocean/sea waters
        is_offshore, offshore_sector = is_offshore_sea_coordinate(latitude, longitude)

        # Determine Marine Context
        marine_ctx = (
            offshore_sector
            or matched_marine_context
            or ("Bay of Bengal Sector" if (6.0 <= latitude <= 23.0 and 80.0 <= longitude <= 95.0)
                else "Arabian Sea Sector" if (6.0 <= latitude <= 25.0 and 60.0 <= longitude < 80.0)
                else "Open Marine Waters")
        )

        # Coastal / Marine classification (within 50km of coast OR inside offshore ocean basin)
        if dist_to_coast <= COASTAL_THRESHOLD_KM or is_offshore:
            status_code = "VALID_MARINE" if is_offshore and dist_to_coast > 20.0 else "VALID_COASTAL"
            loc_title = custom_name or matched_loc_name or (
                f"Maritime Waypoint ({coords_fmt})" if dist_to_coast < 2.0 or is_offshore else f"Coastal Area ({coords_fmt})"
            )
            return LocationValidationResult(
                status=status_code,
                is_coastal=True,
                is_marine=True,
                location_name=loc_title,
                display_name=f"{loc_title} ({coords_fmt})",
                city=matched_loc_name.split(" ")[0] if matched_loc_name else ("Offshore Basin" if is_offshore else "Coastal Station"),
                state="Coastal Sector",
                country=matched_country,
                latitude=latitude,
                longitude=longitude,
                distance_to_coast_km=round(dist_to_coast, 1),
                nearest_port=nearest_port_name,
                marine_context=marine_ctx,
                reason="Marine location detected. Oceanographic and marine intelligence available for this area.",
                coordinates_formatted=coords_fmt,
            )
        else:
            # Try reverse geocode to get real place name if available
            rev_name = cls._try_reverse_geocode_name(latitude, longitude)
            loc_title = custom_name or rev_name or matched_loc_name or f"Inland Coordinate ({coords_fmt})"
            return LocationValidationResult(
                status="INLAND",
                is_coastal=False,
                is_marine=False,
                location_name=loc_title,
                display_name=f"{loc_title} ({coords_fmt})",
                city=matched_loc_name or (rev_name.split(",")[0] if rev_name else "Inland Area"),
                state="Inland Sector",
                country=matched_country,
                latitude=latitude,
                longitude=longitude,
                distance_to_coast_km=round(dist_to_coast, 1),
                nearest_port=f"{nearest_port_name} (~{min_port_dist:.0f} km)" if nearest_port_name else None,
                marine_context=None,
                reason=f"⚠️ No seashore or marine area found at this location ({dist_to_coast:.0f} km from nearest coast).",
                coordinates_formatted=coords_fmt,
            )

    @classmethod
    def _query_external_geocoding(cls, query: str, limit: int = 5) -> List[LocationCandidate]:
        """
        Queries OpenStreetMap Nominatim for live location resolution with global reach.
        Includes in-memory caching and resilient timeouts.
        """
        cache_key = f"search:{query.lower().strip()}:{limit}"
        if cache_key in _GEOCODE_CACHE:
            return _GEOCODE_CACHE[cache_key]

        candidates: List[LocationCandidate] = []
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": query,
                "format": "json",
                "addressdetails": 1,
                "limit": limit,
            }
            headers = {
                "User-Agent": os.getenv("OCEANIS_GEOCODER_USER_AGENT", "OCEANIS-Marine-Intelligence/2.0")
            }
            resp = requests.get(url, params=params, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    lat = float(item["lat"])
                    lon = float(item["lon"])
                    dist_to_coast, _ = calculate_distance_to_nearest_coast(lat, lon)
                    is_offshore, offshore_sector = is_offshore_sea_coordinate(lat, lon)

                    # Check OSM tags for coastal/marine identifiers
                    osm_type = item.get("type", "")
                    osm_class = item.get("class", "")
                    is_osm_coastal = any(
                        t in (osm_type + " " + osm_class)
                        for t in ["bay", "harbour", "port", "beach", "coastline", "sea", "ocean", "marine", "island", "pier"]
                    )

                    is_coastal = (dist_to_coast <= COASTAL_THRESHOLD_KM) or is_osm_coastal or is_offshore

                    addr = item.get("address", {})
                    city = (
                        addr.get("city")
                        or addr.get("town")
                        or addr.get("village")
                        or addr.get("county")
                        or query.title()
                    )
                    state = addr.get("state") or addr.get("region") or addr.get("province") or ""
                    country = addr.get("country") or "International"

                    clean_name = f"{city} Coast" if (is_coastal and "coast" not in city.lower() and "port" not in city.lower()) else city
                    marine_ctx = offshore_sector or (f"Coastal Waters • {state or country}" if is_coastal else None)

                    candidates.append(
                        LocationCandidate(
                            id=f"osm-{item.get('osm_id', 'custom')}-{lat:.3f}-{lon:.3f}",
                            name=clean_name,
                            display_name=item.get("display_name", f"{city}, {state}, {country}"),
                            city=city,
                            state=state,
                            country=country,
                            latitude=lat,
                            longitude=lon,
                            is_coastal=is_coastal,
                            is_marine=is_coastal,
                            distance_to_coast_km=round(dist_to_coast, 1),
                            place_type="coastal_settlement" if is_coastal else "inland_settlement",
                            nearest_port=f"{city} Harbour" if is_coastal else None,
                            marine_context=marine_ctx,
                        )
                    )

            _GEOCODE_CACHE[cache_key] = candidates
        except Exception as exc:
            logger.debug("External geocoding skipped or timed out: %s", exc)

        return candidates

    @classmethod
    def _try_reverse_geocode_name(cls, latitude: float, longitude: float) -> Optional[str]:
        """
        Reverse geocodes a coordinate to a human readable locality name.
        """
        cache_key = f"rev:{latitude:.4f}:{longitude:.4f}"
        if cache_key in _REVERSE_GEOCODE_CACHE:
            return _REVERSE_GEOCODE_CACHE[cache_key]

        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
            }
            headers = {
                "User-Agent": os.getenv("OCEANIS_GEOCODER_USER_AGENT", "OCEANIS-Marine-Intelligence/2.0")
            }
            resp = requests.get(url, params=params, headers=headers, timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                addr = data.get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county")
                state = addr.get("state") or addr.get("country")
                if city:
                    res_name = f"{city}, {state}" if state else city
                    _REVERSE_GEOCODE_CACHE[cache_key] = res_name
                    return res_name
        except Exception as exc:
            logger.debug("Reverse geocoding timed out: %s", exc)

        return None
