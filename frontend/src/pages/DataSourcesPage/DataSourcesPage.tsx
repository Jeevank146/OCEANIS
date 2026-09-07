import React from 'react';
import { Link } from 'react-router-dom';
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
        'Coastal Doppler Weather Radar (Machilipatnam, Vizag, Paradip)',
        'Synoptic Surface Pressure & Coastal Wind Vectors',
        'Squally Weather & Port Warning Signals (1 to 11)',
      ],
      attributionStatement: 'Meteorological bulletins sourced from IMD Cyclone Warning Division, New Delhi.',
    },
    {
      name: 'Indian Space Research Organisation',
      acronym: 'ISRO / NRSC',
      agencyType: 'Department of Space, Govt. of India',
      ingestProtocol: 'HDF5 / NetCDF4 Satellite Orbital Ingest',
      syncFrequency: 'Pass-by-Pass (6-12 hrs)',
      status: 'SYNCHRONIZED',
      uptime: '99.90%',
      parametersProvided: [
        'Oceansat-3 (EOS-06) Ocean Colour Monitor (OCM-3)',
        'INSAT-3DR Geostationary Multi-Spectral Imager',
        'Scatterometer Ocean Surface Wind Vectors',
        'Coastal Zone Boundary & Mangrove Mapping',
      ],
      attributionStatement: 'Satellite data processed via ISRO National Remote Sensing Centre (NRSC) Bhuvan API.',
    },
    {
      name: 'Copernicus Earth Observation Programme',
      acronym: 'ESA Copernicus',
      agencyType: 'European Space Agency & EUMETSAT',
      ingestProtocol: 'Copernicus Marine Data Store (CMEMS) OPeNDAP',
      syncFrequency: 'Every 3 Hours',
      status: 'SYNCHRONIZED',
      uptime: '99.99%',
      parametersProvided: [
        'Sentinel-3 OLCI Level-2 Chlorophyll-a & Phytoplankton Biomass',
        'Sentinel-3 SLSTR Radiometric Sea Surface Temperature (SST)',
        'Sentinel-2 MSI 10m Coastal High-Resolution Orthoimages',
        'Global Sea Surface Height & Altimetric Geostrophic Currents',
      ],
      attributionStatement: 'Copernicus Marine Service information is used under EU Copernicus Open Access Policy.',
    },
    {
      name: 'General Bathymetric Chart of the Oceans',
      acronym: 'GEBCO / IHO',
      agencyType: 'International Hydrographic Organization & IOC-UNESCO',
      ingestProtocol: 'GeoTIFF 15-arcsecond Bathymetric Grid',
      syncFrequency: 'Static Grid (Monthly Sync)',
      status: 'SYNCHRONIZED',
      uptime: '100%',
      parametersProvided: [
        'Global High-Resolution Seafloor Depth Contours',
        'Continental Shelf Margin & Trench Demarcation',
        'Coastal Shoal & Shallow Reef Warning Hazards',
      ],
      attributionStatement: 'Bathymetric grid generated from GEBCO_2023 Grid release.',
    },
    {
      name: 'Indian Coast Guard & Naval Hydrographic Office',
      acronym: 'ICG / NHO',
      agencyType: 'Ministry of Defence, Govt. of India',
      ingestProtocol: 'PostGIS Vector Geodatabase & Notices to Mariners',
      syncFrequency: 'Daily / On-Notice',
      status: 'SYNCHRONIZED',
      uptime: '99.99%',
      parametersProvided: [
        '12 NM Territorial Waters & 200 NM EEZ Maritime Limits',
        'Electronic Navigational Charts (ENC) Fairway Channels',
        'Naval Firing Corridor NOTAMs & Restricted Marine Sanctuaries',
        'Maritime Rescue Coordination Centre (MRCC) SAR Sectors',
      ],
      attributionStatement: 'Maritime coordinates referenced from official Gazette and UNCLOS Treaty baselines.',
    },
  ];

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Data Sources</span>
          </div>
          <h1 className="page-title">
            Trusted Institutional Data Sources & Ingestion Streams
            <span className="page-title-badge badge-official">6 Verified Feeds</span>
          </h1>
          <p className="page-subtitle">
            OCEANIS is grounded exclusively in verified institutional data feeds from national and international oceanographic agencies with full cryptographic provenance.
          </p>
        </div>
        <div className="page-header-actions">
          <Link to="/decision-intelligence" className="btn-page-action primary">
            <span>Inspect Provenance Audit</span>
          </Link>
        </div>
      </header>

      {/* Embedded Component */}
      <div className="trusted-sources-component-wrapper">
        <TrustedSources />
      </div>

      {/* Deep-Dive Technical Feed Directory */}
      <div className="ocean-card sources-tech-card">
        <div className="card-top-header">
          <h3>Ingestion Protocols & Operational Governance</h3>
          <span className="badge-source">Data Architecture</span>
        </div>

        <div className="sources-detailed-list">
          {sourcesDetail.map((src) => (
            <div key={src.acronym} className="source-detailed-box">
              <div className="src-header-row">
                <div>
                  <div className="src-title-group">
                    <strong className="src-acronym">{src.acronym}</strong>
                    <span className="src-full-name">{src.name}</span>
                  </div>
                  <span className="src-agency-type">{src.agencyType}</span>
                </div>
                <div className="src-status-box">
                  <span className="src-sync-badge">{src.status}</span>
                  <span className="src-uptime">Uptime: {src.uptime}</span>
                </div>
              </div>

              <div className="src-tech-meta-grid">
                <div className="src-meta-col">
                  <span className="meta-lbl">Protocol:</span>
                  <strong>{src.ingestProtocol}</strong>
                </div>
                <div className="src-meta-col">
                  <span className="meta-lbl">Sync Frequency:</span>
                  <strong>{src.syncFrequency}</strong>
                </div>
              </div>

              <div className="src-params-list">
                <span className="meta-lbl">Ingested Data Parameters:</span>
                <ul>
                  {src.parametersProvided.map((p, idx) => (
                    <li key={idx}>{p}</li>
                  ))}
                </ul>
              </div>

              <div className="src-attribution">
                <span>⚖️ {src.attributionStatement}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DataSourcesPage;
