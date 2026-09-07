# OCEANIS — Earth Observation & Satellite Chlorophyll-a Integration

## Overview
The OCEANIS Earth Observation (EO) data pipeline integrates official Copernicus Marine multi-mission satellite telemetry to provide high-resolution, near-real-time biological productivity and ocean colour data.

---

## 1. Upstream Provider & Dataset Metadata

| Attribute | Details |
| :--- | :--- |
| **Provider** | Copernicus Marine Service / European Space Agency (ESA) |
| **Product ID** | `OCEANCOLOUR_GLO_BGC_L4_NRT_009_102` |
| **Dataset ID** | `cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D` |
| **Title** | Global Ocean Colour (Copernicus-GlobColour), Bio-Geo-Chemical, L4 from Satellite Observations (Near Real Time) |
| **Satellites / Instruments** | Sentinel-3A/B OLCI, Suomi-NPP VIIRS, Aqua MODIS (Multi-Mission Merged & Interpolated) |
| **Resolution** | 4 km spatial grid |
| **Temporal Frequency** | Daily (P1D) |

---

## 2. Ingested Variables & Parameters

* **`CHL` (`chlorophyll_a_mg_m3`)**: Mass concentration of chlorophyll-a in sea water ($\text{mg/m}^3$).
* **`CHL_uncertainty` (`chl_uncertainty_percent`)**: Satellite retrieval error estimate ($\%$).
* **`flags`**: Land mask and interpolation flags.
* **`ocean_colour`**: Bio-optical classification derived from chlorophyll-a concentration:
  - `< 0.1 mg/m³`: Deep Blue (Oligotrophic / Ultra-Clear)
  - `0.1 – 0.5 mg/m³`: Blue (Low Chlorophyll / High Clarity)
  - `0.5 – 1.5 mg/m³`: Blue-Green (Mesotrophic / Productive Coastal)
  - `1.5 – 4.0 mg/m³`: Greenish (Eutrophic / Active Plankton Growth)
  - `> 4.0 mg/m³`: Dark Green / Turbid (Hyper-Eutrophic / Algal Bloom)
* **Assimilated Metrics**:
  - `sea_surface_temperature_c` ($^\circ\text{C}$)
  - `cloud_cover_percent` ($\%$)
  - `solar_radiation_w_m2` ($\text{W/m}^2$)

---

## 3. Authentication & Configuration

The connector uses the official `copernicusmarine` Python toolbox. Credentials are loaded from `backend/.env`:

```env
COPERNICUS_USERNAME=your_copernicus_username
COPERNICUS_PASSWORD=your_copernicus_password
COPERNICUS_ENABLED=true
```

If credentials are omitted, the connector marks `is_configured = False` and graceful fallback to atmospheric assimilation is maintained.

---

## 4. PostgreSQL / PostGIS Persistence & De-duplication

* Ingested records are stored in the `earth_observations` table.
* **De-duplication**: The ingestion pipeline checks for existing observations matching `(source, product_type, observed_at, latitude, longitude)` within a spatial radius, updating existing rows rather than creating duplicates.

---

## 5. Verification & Tests

Run the automated Earth Observation integration tests:

```bash
# Run Earth Observation test suite
python -m pytest tests/test_earth_observation_persistence.py -v

# Run full multi-provider test suite
python -m pytest tests/test_copernicus_persistence.py tests/test_incois_persistence.py tests/test_earth_observation_persistence.py tests/test_location.py -v
```

---

## 6. Known Limitations

* **Temporal Latency**: Multi-mission Level-4 satellite ocean colour products undergo multi-sensor calibration and cloud gap-filling, resulting in an operational near-real-time (NRT) latency of 1 to 2 days relative to the current wall-clock date.
* **Optical Cloud Penetration**: Ocean colour optical sensors (OLCI, VIIRS, MODIS) observe the surface layer; gap-free L4 employs optimal interpolation to estimate values under persistent cloud cover.
