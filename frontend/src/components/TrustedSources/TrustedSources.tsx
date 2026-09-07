import React from 'react';
import './TrustedSources.css';

interface TrustedSource {
  id: string;
  name: string;
  agency: string;
  dataType: string;
  status: 'OPERATIONAL' | 'SYNCHRONIZED' | 'ACTIVE_INGESTION';
  lastUpdate: string;
  freshness: string;
  parameters: string[];
  icon: React.ReactNode;
}

const trustedSources: TrustedSource[] = [
  {
    id: 'incois',
    name: 'INCOIS Ocean Buoy Network',
    agency: 'Indian National Centre for Ocean Information Services',
    dataType: 'In-Situ Oceanographic Buoys & Hydrodynamic Models',
    status: 'OPERATIONAL',
    lastUpdate: '8 min ago',
    freshness: 'REAL-TIME TELEMETRY',
    parameters: ['Significant Wave Height', 'Peak Swell Period', 'Surface Current Drift', 'Sea State Index'],
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    id: 'imd',
    name: 'IMD Coastal Doppler Radar',
    agency: 'India Meteorological Department (Cyclone Warning Division)',
    dataType: 'Coastal Radars, Atmospheric Soundings & Cyclone Tracks',
    status: 'SYNCHRONIZED',
    lastUpdate: '15 min ago',
    freshness: 'HOURLY SYNC',
    parameters: ['Sustained Wind Velocity', 'Doppler Precipitation', 'Cyclone Vector Coordinates', 'Storm Surge Alerts'],
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
      </svg>
    ),
  },
  {
    id: 'isro',
    name: 'ISRO OceanSat & SCATSAT',
    agency: 'Indian Space Research Organisation (Earth Observation)',
    dataType: 'Orbital Ocean Colour Monitor & Scatterometer Wind Vectors',
    status: 'ACTIVE_INGESTION',
    lastUpdate: 'Today, 08:30 UTC Pass',
    freshness: 'ORBITAL PASS (360m Res)',
    parameters: ['Ocean Surface Vector Winds', 'Chlorophyll Bio-Optics', 'Total Suspended Matter', 'Aerosol Optical Depth'],
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 3v18M3 12h18" />
      </svg>
    ),
  },
  {
    id: 'copernicus',
    name: 'Copernicus Sentinel Missions',
    agency: 'European Space Agency & EUMETSAT Radiometry',
    dataType: 'Sentinel-3 OLCI & SLSTR Multi-Spectral Remote Sensing',
    status: 'ACTIVE_INGESTION',
    lastUpdate: 'Today, 06:40 UTC Pass',
    freshness: 'HIGH RESOLUTION (10m - 300m)',
    parameters: ['Chlorophyll-a Bio-Optics', 'Sea Surface Temperature', 'Thermal Front Detection', 'Water Attenuation Kd(490)'],
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
        <path d="M3 3v5h5" />
        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
        <path d="M16 21h5v-5" />
      </svg>
    ),
  },
  {
    id: 'gebco',
    name: 'GEBCO & Survey of India Bathymetry',
    agency: 'General Bathymetric Chart of the Oceans & Survey of India',
    dataType: 'High-Resolution Gridded Global & Regional Ocean Depth Contours',
    status: 'SYNCHRONIZED',
    lastUpdate: 'Terrain Model 2026',
    freshness: '15 ARC-SECOND GRID',
    parameters: ['12 NM Territorial Limit', '200 NM Indian EEZ Boundary', 'Bathymetric Contours', 'Subsea Ridges'],
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
      </svg>
    ),
  },
  {
    id: 'icg',
    name: 'Indian Coast Guard SAR Operations',
    agency: 'Indian Coast Guard & Directorate General of Shipping',
    dataType: 'Search and Rescue Zones, Navigational Warnings & Port Clearances',
    status: 'OPERATIONAL',
    lastUpdate: 'Live AIS & NAVAREA-VIII',
    freshness: 'CONTINUOUS BROADCAST',
    parameters: ['Naval Exclusion Polygons', 'Safe Harbor Refuges', 'Maritime Safety Broadcasts', 'SAR Sectors'],
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <path d="M9 12l2 2 4-4" />
      </svg>
    ),
  },
];

export const TrustedSources: React.FC = () => {
  return (
    <section id="trusted-sources" className="trusted-sources-section">
      <div className="container">
        {/* Section Header */}
        <div className="trusted-header">
          <div className="trusted-title-block">
            <span className="section-tag">DATA INTEGRITY & TELEMETRY PROVENANCE</span>
            <h2 className="trusted-main-title">Trusted Marine Intelligence Data Sources</h2>
            <p className="trusted-subtitle">
              OCEANIS ingests authoritative observation telemetry directly from verified institutional providers, physical buoy networks, and orbital satellites.
            </p>
          </div>

          <div className="trusted-badge">
            <span className="live-dot pulse" />
            <span className="trusted-badge-text">6 INSTITUTIONAL FEEDS SYNCHRONIZED</span>
          </div>
        </div>

        {/* 6 Source Cards Grid */}
        <div className="trusted-grid">
          {trustedSources.map((src) => (
            <div key={src.id} className="trusted-source-card">
              <div className="src-card-top">
                <div className="src-icon-box">{src.icon}</div>
                <span className="src-status-badge">
                  <span className="src-status-dot pulse" />
                  {src.status}
                </span>
              </div>

              <div className="src-card-body">
                <h3 className="src-name">{src.name}</h3>
                <span className="src-agency">{src.agency}</span>
                <p className="src-datatype">{src.dataType}</p>

                <div className="src-parameters-list">
                  {src.parameters.map((param, i) => (
                    <span key={i} className="src-param-pill">{param}</span>
                  ))}
                </div>
              </div>

              <div className="src-card-footer">
                <div className="src-meta-col">
                  <span className="src-meta-lbl">Last Synchronized:</span>
                  <span className="src-meta-val">{src.lastUpdate}</span>
                </div>
                <div className="src-meta-col text-right">
                  <span className="src-meta-lbl">Freshness Standard:</span>
                  <span className="src-meta-val highlight">{src.freshness}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
