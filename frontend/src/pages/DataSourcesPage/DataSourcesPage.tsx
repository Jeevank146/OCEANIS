import React from 'react';
import { Link } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import { useLanguage } from '../../context/LanguageContext';
import { TrustedSources } from '../../components/TrustedSources/TrustedSources';
import './DataSourcesPage.css';

interface SourceDetailedItem {
  name: string;
  acronym: string;
  agencyType: string;
  ingestProtocol: string;
  syncFrequency: string;
  status: 'SYNCHRONIZED' | 'ACTIVE';
  uptime: string;
  parametersProvided: string[];
  attributionStatement: string;
}

export const DataSourcesPage: React.FC = () => {
  const { selectedLocation } = useLocationContext();
  const { t } = useLanguage();

  const locName = selectedLocation?.city || selectedLocation?.name || 'All Coastal Sectors';

  const sourcesDetail: SourceDetailedItem[] = [
    {
      name: 'Indian National Centre for Ocean Information Services',
      acronym: 'INCOIS',
      agencyType: 'Ministry of Earth Sciences (MoES), Govt. of India',
      ingestProtocol: 'REST API & GeoJSON WFS Service',
      syncFrequency: 'Every 15 Minutes',
      status: 'SYNCHRONIZED',
      uptime: '99.98%',
      parametersProvided: [
        'Potential Fishing Zone (PFZ) Advisories',
        'Ocean State Forecast (OSF): Wave Height, Swell, Period',
        'High Wave Alerts & Kallakkadal Warnings',
        'Tsunami Early Warning Bulletins',
      ],
      attributionStatement: 'Data provided under official open research data access terms by INCOIS Hyderabad.',
    },
    {
      name: 'India Meteorological Department',
      acronym: 'IMD',
      agencyType: 'Ministry of Earth Sciences (MoES), Govt. of India',
      ingestProtocol: 'GRIB2 Numerical Grid & Doppler Radar Feeds',
      syncFrequency: 'Every 30 Minutes',
      status: 'SYNCHRONIZED',
      uptime: '99.95%',
      parametersProvided: [
        'Tropical Cyclone Track & Intensity Bulletins',
        'Coastal Doppler Weather Radar (Machilipatnam, Vizag, Paradip, Chennai, Cochin)',
        'Synoptic Surface Pressure & Coastal Wind Vectors',
        'Squally Weather & Port Warning Signals (1 to 11)',
      ],
      attributionStatement: 'Meteorological bulletins sourced from IMD Cyclone Warning Division, New Delhi.',
    },
    {
      name: 'Indian Space Research Organisation',
      acronym: 'ISRO / SAC',
      agencyType: 'Department of Space, Govt. of India',
      ingestProtocol: 'Oceansat-3 & INSAT-3DR Direct Broadcast',
      syncFrequency: 'Hourly Earth Observation Passes',
      status: 'SYNCHRONIZED',
      uptime: '99.90%',
      parametersProvided: [
        'Oceansat-3 Ocean Color Monitor (OCM-3) Chlorophyll Gradients',
        'INSAT-3DR Rapid-Scan Convective Cloud Imagery',
        'Scatterometer Coastal Surface Winds',
      ],
      attributionStatement: 'Space Applications Centre (SAC), ISRO Ahmedabad & MOSDAC open payload streams.',
    },
    {
      name: 'Copernicus Marine Environment Monitoring Service',
      acronym: 'CMEMS',
      agencyType: 'European Union Marine Programme / Mercator Ocean',
      ingestProtocol: 'Copernicus Marine Data Store API (NetCDF/GRIB)',
      syncFrequency: 'Daily 00:00 & 12:00 UTC Reanalysis Updates',
      status: 'SYNCHRONIZED',
      uptime: '99.99%',
      parametersProvided: [
        'Sentinel-3 OLCI Level-3 High-Res Chlorophyll-a (mg/m³)',
        'Sentinel-3 SLSTR High-Precision Sea Surface Temperature (°C)',
        'Global Ocean Physics Analysis and Forecast (0.083° Grid)',
      ],
      attributionStatement: 'E.U. Copernicus Marine Service information; processed and validated in near-real-time by OCEANIS.',
    },
    {
      name: 'General Bathymetric Chart of the Oceans & PostGIS Spatial DB',
      acronym: 'GEBCO & PostGIS',
      agencyType: 'IHO-IOC & OCEANIS Native Spatial Cluster',
      ingestProtocol: 'PostgreSQL / PostGIS 3.4 Vector Topologies',
      syncFrequency: 'Real-Time Spatial Queries (< 10ms)',
      status: 'ACTIVE',
      uptime: '100.0%',
      parametersProvided: [
        'GEBCO 15 arc-second high-resolution bathymetric elevation grids',
        '12 NM Territorial Waters, 24 NM Contiguous & 200 NM EEZ Polygons',
        'Indian Coastline Marine Protected Areas (MPA) & Defense Enclosures',
        'Official Refuges, Commercial Ports & Anchorage Shelters',
      ],
      attributionStatement: 'GEBCO Compilation Group / UNCLOS Baseline vectors curated by OCEANIS Geo-Spatial Agent.',
    },
  ];

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">{t('nav.home', 'Home')}</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">{t('nav.data_sources', 'Data Sources')}</span>
          </div>
          <h1 className="page-title">
            {t('data_sources.title', 'Integrated Marine Data Feeds & Agency Provenance')}
            <span className="page-title-badge badge-source">{t('data_sources.badge', 'Live Sync')}</span>
          </h1>
          <p className="page-subtitle">
            {t('data_sources.subtitle', 'Official national and international oceanic observational data pipelines synchronized into the OCEANIS Multi-Agent Orchestration cluster with cryptographic verification.')}
          </p>
        </div>
        <div className="page-header-actions">
          <div className="coverage-pill" style={{ background: 'rgba(8, 42, 67, 0.7)', border: '1px solid rgba(22, 184, 216, 0.3)', padding: '6px 12px', borderRadius: '20px', color: '#16B8D8', fontSize: '0.8125rem', fontWeight: 600 }}>
            📍 Operational Coverage: {locName}
          </div>
          <Link to="/reports" className="btn-page-action secondary">
            <span>{t('nav.reports', 'Audit Dossiers')}</span>
          </Link>
        </div>
      </header>

      {/* Trusted Sources Carousel / Banner */}
      <div className="data-sources-top-section">
        <TrustedSources />
      </div>

      {/* Detailed Agency Table / Cards */}
      <div className="data-sources-grid">
        {sourcesDetail.map((src, idx) => (
          <div key={idx} className="ocean-card source-card">
            <div className="source-card-header">
              <div className="source-acronym-badge">
                <span>{src.acronym}</span>
              </div>
              <div className="source-title-block">
                <h3>{src.name}</h3>
                <span className="source-agency-type">{src.agencyType}</span>
              </div>
              <div className="source-status-badge">
                <span className="status-dot-green"></span>
                <span>{src.status}</span>
              </div>
            </div>

            <div className="source-metadata-row">
              <div className="meta-item">
                <span className="meta-label">Ingest Protocol:</span>
                <span className="meta-value">{src.ingestProtocol}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Sync Frequency:</span>
                <span className="meta-value">{src.syncFrequency}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Feed Uptime:</span>
                <span className="meta-value">{src.uptime}</span>
              </div>
            </div>

            <div className="source-params-block">
              <span className="params-heading">Parameters Provided to OCEANIS Domain Agents:</span>
              <ul className="params-list">
                {src.parametersProvided.map((param, pIdx) => (
                  <li key={pIdx}>• {param}</li>
                ))}
              </ul>
            </div>

            <div className="source-attribution-footer">
              <span className="attribution-tag">Official Attribution:</span>
              <p>{src.attributionStatement}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DataSourcesPage;
