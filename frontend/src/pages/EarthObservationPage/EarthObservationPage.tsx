import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './EarthObservationPage.css';

// Satellite Imagery Assets
import satCyclone from '../../assets/images/satellite_cyclone_radar.jpg';
import satEarth from '../../assets/images/hero_satellite_earth.jpg';
import satHarbour from '../../assets/images/coastal_harbour_port.jpg';
import satWaves from '../../assets/images/hero_ocean_waves.jpg';
import satGeo from '../../assets/images/geospatial_gis_coastline.jpg';
import satOps from '../../assets/images/marine_operations_vessel.jpg';
import satSafety from '../../assets/images/hero_maritime_safety.jpg';

interface SatelliteProductCard {
  id: string;
  name: string;
  category: string;
  image: string;
  value: string;
  interpretation: string;
  source: string;
  observationTime: string;
  freshness: string;
  location: string;
  description: string;
  qaScore: string;
}

interface SatellitePass {
  id: string;
  mission: string;
  sensor: string;
  agency: string;
  passTime: string;
  resolution: string;
  cloudCover: string;
  quality: 'EXCELLENT' | 'GOOD' | 'PARTIAL CLOUD';
  spectralBands: string;
  primaryParameter: string;
  description: string;
}

export const EarthObservationPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedPass, setSelectedPass] = useState<string>('s3-olci');
  const [selectedProduct, setSelectedProduct] = useState<SatelliteProductCard | null>(null);

  // 7 Core Image-Rich Visual Satellite Products
  const satelliteProducts: SatelliteProductCard[] = [
    {
      id: 'sst',
      name: 'Sea Surface Temperature',
      category: 'Thermal Radiometry',
      image: satCyclone,
      value: '28.4 °C (Stable Front)',
      interpretation: 'Stable thermal boundary layer with active nutrient-rich upwelling front favorable for pelagic fish aggregation.',
      source: 'MODIS-Aqua / Sentinel-3 SLSTR',
      observationTime: 'Today, 09:15 UTC (14:45 IST)',
      freshness: 'FRESH (< 45m)',
      location: 'Bay of Bengal • Vizag Sector (17.68° N, 83.22° E)',
      description: 'High-resolution dual-view thermal infrared radiometry measuring foundation sea surface temperature (SST) and sub-skin thermal fronts with 0.2 K radiometric accuracy.',
      qaScore: '0.98 (Calibrated L2)',
    },
    {
      id: 'chlorophyll',
      name: 'Chlorophyll-a Concentration',
      category: 'Ocean Colour Bio-Optics',
      image: satEarth,
      value: '2.14 mg/m³ (High Density)',
      interpretation: 'High phytoplankton bloom density demarcating potential fishing zone (PFZ) corridor with elevated primary productivity.',
      source: 'Copernicus Sentinel-3 OLCI',
      observationTime: 'Today, 06:40 UTC (12:10 IST)',
      freshness: 'FRESH (10m Res)',
      location: 'Coastal Andhra (16.98° N, 82.26° E)',
      description: 'Multispectral ocean colour reflectance measuring absorption bands at 442.5 nm to compute chlorophyll-a biomass and pelagic habitat suitability.',
      qaScore: '0.96 (Optimal Optics)',
    },
    {
      id: 'ocean-colour',
      name: 'Ocean Colour',
      category: 'Coastal Water Clarity',
      image: satHarbour,
      value: 'Kd(490): 0.082 m⁻¹',
      interpretation: 'Clear pelagic waters with distinct coastal optical gradient distinguishing riverine discharge plume from offshore blue waters.',
      source: 'Sentinel-3 OLCI Radiometer',
      observationTime: 'Today, 06:40 UTC (12:10 IST)',
      freshness: 'VERIFIED (L2 Clean)',
      location: 'Godavari Estuary & Port Approaches',
      description: 'Diffuse attenuation coefficient Kd(490) and spectral reflectance mapping coastal water clarity, euphotic depth, and optical water mass classification.',
      qaScore: '0.97 (Cloud-Free)',
    },
    {
      id: 'cloud-cover',
      name: 'Cloud Cover',
      category: 'Atmospheric Profiling',
      image: satWaves,
      value: '18% Clear Sky Window',
      interpretation: 'Synoptic maritime corridor clear of severe convective clusters; isolated cumulus patches without cyclonic vortex development.',
      source: 'INSAT-3DR / IMD Doppler Radar',
      observationTime: 'Today, 10:00 UTC (15:30 IST)',
      freshness: 'HOURLY SYNC',
      location: 'Central Bay of Bengal Basin',
      description: 'Infrared atmospheric water vapor profiling, brightness temperature thresholds, and convective storm cluster surveillance across maritime transit corridors.',
      qaScore: '0.94 (Synoptic Clean)',
    },
    {
      id: 'thermal-radiometry',
      name: 'Thermal Radiometry',
      category: 'Dual-View Radiometry',
      image: satGeo,
      value: 'ΔT: +1.4°C Upwelling Front',
      interpretation: 'Sharp sea surface thermal gradient along the 50m bathymetry contour indicating active shelf-break upwelling.',
      source: 'Sentinel-3B SLSTR Radiometer',
      observationTime: 'Today, 10:15 UTC (15:45 IST)',
      freshness: 'FRESH (0.2K Precision)',
      location: 'Continental Shelf Break (17.55° N, 83.45° E)',
      description: 'Dual-angle sea and land surface temperature radiometer detecting foundation and sub-skin thermal structure with 0.2 K absolute calibration.',
      qaScore: '0.99 (High Confidence)',
    },
    {
      id: 'optical-radiometry',
      name: 'Optical Radiometry',
      category: 'Multispectral Turbidity',
      image: satOps,
      value: 'TSM: 14.8 g/m³ (Plume Edge)',
      interpretation: 'Total Suspended Matter (TSM) gradient tracing riverine sediment transport and port approach fairway navigable turbidity.',
      source: 'Sentinel-2 MSI / Oceansat-3',
      observationTime: 'Yesterday, 05:18 UTC (10:48 IST)',
      freshness: 'VERIFIED (10m Res)',
      location: 'Harbor Channel Fairway Corridors',
      description: 'Ultra-high-resolution multi-spectral reflectance indexing suspended sediment transport, dredging plume dispersion, and coastal erosion dynamics.',
      qaScore: '0.95 (Processed)',
    },
    {
      id: 'atmospheric-profiling',
      name: 'Atmospheric Profiling',
      category: 'Tropospheric Profiling',
      image: satSafety,
      value: 'RH: 78% (Dry Slot Corridor)',
      interpretation: 'Low-level maritime tropospheric moisture profile within normal seasonal limits; no mid-tropospheric wind shear anomalies.',
      source: 'INSAT-3D Sounder / ECMWF',
      observationTime: 'Today, 11:30 UTC (17:00 IST)',
      freshness: 'CONTINUOUS GEO',
      location: 'South-Central Bay of Bengal',
      description: 'Multi-level vertical atmospheric soundings measuring temperature profiles, geopotential thickness, and tropospheric moisture flux over maritime basins.',
      qaScore: '0.92 (Operational)',
    },
  ];

  // Satellite Pass Missions
  const passes: SatellitePass[] = [
    {
      id: 's3-olci',
      mission: 'Sentinel-3A',
      sensor: 'OLCI (Ocean & Land Colour Instrument)',
      agency: 'ESA / Copernicus',
      passTime: '09:42 UTC (15:12 IST Today)',
      resolution: '300m spatial resolution',
      cloudCover: '14% (Clear coastal window)',
      quality: 'EXCELLENT',
      spectralBands: '21 Optical Bands (400 - 1020 nm)',
      primaryParameter: 'Chlorophyll-a & Total Suspended Matter (TSM)',
      description: 'High-accuracy bio-optical ocean color retrieval over Andhra and Odisha coasts. Clearly demarcates Godavari river discharge plume and offshore chlorophyll gradient.',
    },
    {
      id: 's3-slstr',
      mission: 'Sentinel-3B',
      sensor: 'SLSTR (Sea & Land Surface Temp Radiometer)',
      agency: 'ESA / Copernicus',
      passTime: '10:15 UTC (15:45 IST Today)',
      resolution: '1.0 km thermal IR',
      cloudCover: '18%',
      quality: 'EXCELLENT',
      spectralBands: '9 Bands (Dual View Radiometry)',
      primaryParameter: 'Sub-Skin & Foundation SST (0.2 K precision)',
      description: 'Precision radiometric thermal imaging detecting coastal upwelling temperature drop of 1.4°C along the 50m bathymetry contour off Visakhapatnam.',
    },
    {
      id: 's2-msi',
      mission: 'Sentinel-2B',
      sensor: 'MSI (MultiSpectral Instrument)',
      agency: 'ESA / Copernicus',
      passTime: '05:18 UTC (10:48 IST Yesterday)',
      resolution: '10m - 20m high-res',
      cloudCover: '8%',
      quality: 'EXCELLENT',
      spectralBands: '13 Spectral Bands (VNIR - SWIR)',
      primaryParameter: 'Coastal Turbidity & Port Approach Bathymetry',
      description: 'Ultra-high-resolution imaging for port fairway sediment tracking, breakwater wave diffraction, and coastal shoreline morphology.',
    },
    {
      id: 'insat-3dr',
      mission: 'INSAT-3DR',
      sensor: 'Imager & Sounder',
      agency: 'ISRO (India)',
      passTime: '11:30 UTC (17:00 IST Continuous)',
      resolution: '1.0 km Visible / 4.0 km IR',
      cloudCover: 'Bay of Bengal Synoptic View',
      quality: 'GOOD',
      spectralBands: '6-channel Imager (Vis, SWIR, MIR, TIR)',
      primaryParameter: 'Convective Clouds, Cyclonic Vortex & Sea Surface Winds',
      description: 'Geostationary 30-minute repeat cycle monitoring convective cloud clusters and cyclone eye formation over central and southern Bay of Bengal.',
    },
    {
      id: 'oceansat-3',
      mission: 'EOS-06 (Oceansat-3)',
      sensor: 'OCM-3 (Ocean Colour Monitor)',
      agency: 'ISRO (India)',
      passTime: '06:30 UTC (12:00 IST Today)',
      resolution: '360m / 1km',
      cloudCover: '12%',
      quality: 'EXCELLENT',
      spectralBands: '13 Bands optimized for ocean optics',
      primaryParameter: 'Indian EEZ Chlorophyll & Algal Bloom Index',
      description: 'National Earth observation satellite dedicated to Indian coastal and pelagic resource mapping and fishery zone generation.',
    },
  ];

  const activePassData = passes.find((p) => p.id === selectedPass) || passes[0];

  const handleQueryAgent = (productName?: string) => {
    const query = productName
      ? `Provide detailed remote sensing analysis for ${productName} in the Bay of Bengal sector.`
      : `Analyze recent satellite passes (${activePassData.sensor}) and explain ocean color / thermal patterns in Andhra sector.`;
    navigate('/ask-oceanis', { state: { initialQuery: query } });
  };

  return (
    <div className="ocean-page-container eo-page-root">
      {/* ====================================================================
          PAGE HEADER BANNER
          ==================================================================== */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Earth Observation</span>
          </div>
          <h1 className="page-title">
            Satellite Earth Observation & Remote Sensing Telemetry
            <span className="page-title-badge badge-agent">EO Agent</span>
          </h1>
          <p className="page-subtitle">
            Multi-mission orbital telemetry ingest from Sentinel-3 OLCI/SLSTR, Sentinel-2 MSI, ISRO Oceansat-3 (EOS-06), and INSAT-3DR.
          </p>
        </div>
        <div className="page-header-actions">
          <button
            type="button"
            className="btn-page-action primary"
            onClick={() => handleQueryAgent()}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span>Query EO Agent</span>
          </button>
        </div>
      </header>

      {/* ====================================================================
          SECTION 1: IMAGE-RICH EARTH OBSERVATION VISUAL CARDS (7 PRODUCTS)
          ==================================================================== */}
      <section className="eo-visual-products-section" aria-label="Earth Observation Products">
        <div className="section-header-compact">
          <div>
            <h2 className="section-title-sm">Earth Observation Visual Products</h2>
            <span className="section-meta-tag">7 Calibrated Remote Sensing Channels</span>
          </div>
          <div className="eo-status-pill">
            <span className="live-dot pulse" />
            <span>SENTINEL-3 • MODIS • OCEANSAT-3 • INSAT-3D</span>
          </div>
        </div>

        <div className="eo-product-cards-grid">
          {satelliteProducts.map((card) => (
            <div key={card.id} className="ocean-card eo-visual-card">
              {/* Photographic Imagery Thumbnail Header */}
              <div
                className="eo-card-media"
                style={{ backgroundImage: `url(${card.image})` }}
              >
                <div className="eo-card-media-overlay" />
                <div className="eo-media-top-badges">
                  <span className="eo-badge-category">{card.category}</span>
                  <span className="eo-badge-freshness">{card.freshness}</span>
                </div>
                <div className="eo-media-metric-banner">
                  <span className="eo-metric-lbl">Measured Value</span>
                  <strong className="eo-metric-val">{card.value}</strong>
                </div>
              </div>

              {/* Card Body */}
              <div className="eo-card-body">
                <h3 className="eo-product-name">{card.name}</h3>
                <p className="eo-interpretation-text">{card.interpretation}</p>

                {/* Metadata Details */}
                <div className="eo-card-meta-list">
                  <div className="eo-meta-item">
                    <span className="meta-k">Data Source:</span>
                    <strong className="meta-v">{card.source}</strong>
                  </div>
                  <div className="eo-meta-item">
                    <span className="meta-k">Observation Time:</span>
                    <span className="meta-v">{card.observationTime}</span>
                  </div>
                  <div className="eo-meta-item">
                    <span className="meta-k">Coverage Grid:</span>
                    <span className="meta-v">{card.location}</span>
                  </div>
                </div>

                {/* Action Trigger */}
                <button
                  type="button"
                  className="btn-view-analysis"
                  onClick={() => setSelectedProduct(card)}
                >
                  <span>View Analysis</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ====================================================================
          SECTION 2: DETAILED SATELLITE PASS & RADIOMETRIC INSPECTOR WORKSPACE
          ==================================================================== */}
      <section className="eo-deep-workspace-section" aria-label="Orbital Pass and Radiometric Inspector">
        <div className="section-header-compact">
          <h2 className="section-title-sm">Orbital Geometry & Radiometric Telemetry Workspace</h2>
          <span className="section-meta-tag">Multi-Mission Sensor Ingest</span>
        </div>

        <div className="eo-layout-grid">
          {/* Left Column: Satellite Pass Selector */}
          <div className="eo-left-col">
            <div className="ocean-card pass-list-card">
              <div className="card-top-header">
                <h3>Ingested Satellite Passes</h3>
                <span className="badge-source">5 Missions Live</span>
              </div>
              <p className="card-desc">
                Select a satellite sensor to inspect orbital geometry, spectral resolution, and radiometric calibration flags.
              </p>

              <div className="pass-selector-list">
                {passes.map((pass) => (
                  <button
                    key={pass.id}
                    type="button"
                    className={`pass-item-btn ${selectedPass === pass.id ? 'active' : ''}`}
                    onClick={() => setSelectedPass(pass.id)}
                  >
                    <div className="pass-btn-header">
                      <strong className="pass-mission">{pass.mission}</strong>
                      <span className={`pass-qual-badge qual-${pass.quality.toLowerCase().replace(/\s+/g, '-')}`}>
                        {pass.quality}
                      </span>
                    </div>
                    <span className="pass-sensor-name">{pass.sensor}</span>
                    <div className="pass-meta-row">
                      <span>{pass.agency}</span>
                      <span>{pass.passTime}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Sensor Deep-Dive & Radiometric Inspector */}
          <div className="eo-right-col">
            <div className="ocean-card pass-detail-card">
              <div className="card-top-header">
                <div>
                  <h3>Sensor Profile & Radiometric Telemetry</h3>
                  <span className="pass-sub-title">{activePassData.mission} • {activePassData.sensor}</span>
                </div>
                <span className="badge-provenance">{activePassData.agency}</span>
              </div>

              <div className="pass-specs-grid">
                <div className="spec-box">
                  <span className="spec-label">Spatial Resolution</span>
                  <strong className="spec-value">{activePassData.resolution}</strong>
                </div>
                <div className="spec-box">
                  <span className="spec-label">Cloud Cover</span>
                  <strong className="spec-value">{activePassData.cloudCover}</strong>
                </div>
                <div className="spec-box">
                  <span className="spec-label">Spectral Channels</span>
                  <strong className="spec-value">{activePassData.spectralBands}</strong>
                </div>
                <div className="spec-box">
                  <span className="spec-label">Primary Target</span>
                  <strong className="spec-value">{activePassData.primaryParameter}</strong>
                </div>
              </div>

              <div className="pass-analysis-box">
                <h4>Oceanographic Interpretation:</h4>
                <p>{activePassData.description}</p>
              </div>

              {/* Simulated Spectral Bands Radiance Graph */}
              <div className="spectral-bands-section">
                <h4>Radiometric Channels & Signal-to-Noise Ratio (SNR)</h4>
                <div className="spectral-bar-list">
                  <div className="spectral-bar-item">
                    <div className="spectral-bar-labels">
                      <span>Band 412.5 nm (Yellow Substance / CDOM)</span>
                      <strong>SNR: 1850 (Optimal)</strong>
                    </div>
                    <div className="spectral-track"><div className="spectral-fill" style={{ width: '92%', background: '#3b82f6' }} /></div>
                  </div>
                  <div className="spectral-bar-item">
                    <div className="spectral-bar-labels">
                      <span>Band 442.5 nm (Chlorophyll Absorption Peak)</span>
                      <strong>SNR: 2100 (Optimal)</strong>
                    </div>
                    <div className="spectral-track"><div className="spectral-fill" style={{ width: '96%', background: '#10b981' }} /></div>
                  </div>
                  <div className="spectral-bar-item">
                    <div className="spectral-bar-labels">
                      <span>Band 560.0 nm (Chlorophyll Green Reflectance)</span>
                      <strong>SNR: 1980 (Optimal)</strong>
                    </div>
                    <div className="spectral-track"><div className="spectral-fill" style={{ width: '94%', background: '#16a34a' }} /></div>
                  </div>
                  <div className="spectral-bar-item">
                    <div className="spectral-bar-labels">
                      <span>Band 865.0 nm (Aerosol Atmospheric Correction)</span>
                      <strong>SNR: 1420 (Clean)</strong>
                    </div>
                    <div className="spectral-track"><div className="spectral-fill" style={{ width: '82%', background: '#f59e0b' }} /></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          ANALYSIS INSPECTOR MODAL DIALOG
          ==================================================================== */}
      {selectedProduct && (
        <div className="eo-modal-backdrop" onClick={() => setSelectedProduct(null)}>
          <div className="eo-modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="eo-modal-header">
              <div>
                <span className="eo-modal-cat">{selectedProduct.category}</span>
                <h3 className="eo-modal-title">{selectedProduct.name} Remote Sensing Analysis</h3>
              </div>
              <button
                type="button"
                className="btn-close-modal"
                onClick={() => setSelectedProduct(null)}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <div className="eo-modal-img" style={{ backgroundImage: `url(${selectedProduct.image})` }}>
              <div className="eo-modal-img-overlay" />
              <div className="eo-modal-val-box">
                <span>Measured Level:</span>
                <strong>{selectedProduct.value}</strong>
              </div>
              <div className="eo-modal-freshness-pill">
                <span>{selectedProduct.freshness}</span>
              </div>
            </div>

            <div className="eo-modal-body">
              <div className="eo-modal-interp-block">
                <h4>Short Interpretation</h4>
                <p>{selectedProduct.interpretation}</p>
              </div>

              <div className="eo-modal-desc-block">
                <h4>Scientific Description</h4>
                <p>{selectedProduct.description}</p>
              </div>

              <div className="eo-modal-specs-grid">
                <div className="spec-card">
                  <span className="spec-title">Coverage Grid</span>
                  <span className="spec-detail">{selectedProduct.location}</span>
                </div>
                <div className="spec-card">
                  <span className="spec-title">Observation Time</span>
                  <span className="spec-detail">{selectedProduct.observationTime}</span>
                </div>
                <div className="spec-card">
                  <span className="spec-title">Data Source</span>
                  <span className="spec-detail">{selectedProduct.source}</span>
                </div>
                <div className="spec-card">
                  <span className="spec-title">Radiometric Quality</span>
                  <span className="spec-detail">{selectedProduct.qaScore}</span>
                </div>
              </div>
            </div>

            <div className="eo-modal-footer">
              <button
                type="button"
                className="btn-modal-query"
                onClick={() => {
                  const pName = selectedProduct.name;
                  setSelectedProduct(null);
                  handleQueryAgent(pName);
                }}
              >
                <span>Ask OCEANIS About This Product →</span>
              </button>
              <button
                type="button"
                className="btn-modal-close"
                onClick={() => setSelectedProduct(null)}
              >
                Close Analysis
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EarthObservationPage;
