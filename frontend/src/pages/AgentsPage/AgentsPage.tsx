import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import { useLanguage } from '../../context/LanguageContext';
import './AgentsPage.css';

// Photographic Image Assets for 6 Domain Agents
import imgFishing from '../../assets/images/hero_coastal_fishing.jpg';
import imgMarine from '../../assets/images/hero_ocean_waves.jpg';
import imgEO from '../../assets/images/hero_satellite_earth.jpg';
import imgGeo from '../../assets/images/geospatial_gis_coastline.jpg';
import imgSafety from '../../assets/images/satellite_cyclone_radar.jpg';
import imgOps from '../../assets/images/marine_operations_vessel.jpg';

interface DomainAgentDetail {
  id: string;
  name: string;
  badge: string;
  domain: string;
  route: string;
  icon: string;
  image: string;
  status: 'ONLINE' | 'ACTIVE';
  latency: string;
  capabilities: string[];
  dataSources: string[];
  responsibilities: string[];
  sampleQuery: string;
  description: string;
}

export const AgentsPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedLocation } = useLocationContext();
  const { t } = useLanguage();

  const locName = selectedLocation?.city || selectedLocation?.name || 'Operational Sector';

  const domainAgents: DomainAgentDetail[] = [
    {
      id: 'fishing',
      name: 'Fishing Intelligence Agent',
      badge: 'BIO-SUITABILITY',
      domain: 'PELAGIC BIOMASS & PFZ',
      route: '/fishing',
      icon: '🐟',
      image: imgFishing,
      status: 'ONLINE',
      latency: '14ms',
      capabilities: ['PFZ Advisories', 'SST Gradients', 'Species Match', 'Catch Optimization'],
      dataSources: ['INCOIS PFZ Bulletins', 'Copernicus Chlorophyll-a', 'Sentinel-3 SLSTR SST'],
      responsibilities: [
        'Identify Potential Fishing Zones (PFZ) and thermal eddy convergence',
        'Species-specific habitat suitability modeling for pelagic shoals',
        'Fuel and catch economic return optimization for artisanal & motorized craft',
      ],
      sampleQuery: `Can I go fishing tomorrow from ${locName} and what are the top PFZ coordinates?`,
      description: 'Specialized in marine bio-optics and fisheries intelligence, matching ocean color and thermal fronts to maximize sustainable catch.',
    },
    {
      id: 'marine-conditions',
      name: 'Marine Conditions Agent',
      badge: 'OCEAN DYNAMICS',
      domain: 'WAVES, WINDS & TIDES',
      route: '/marine-conditions',
      icon: '🌊',
      image: imgMarine,
      status: 'ONLINE',
      latency: '11ms',
      capabilities: ['Significant Wave Height', 'Swell Vectors', 'Tidal Forecasting', 'Current Fields'],
      dataSources: ['INCOIS Wave Watch 3', 'IMD Coastal Stations', 'Copernicus CMEMS Physics'],
      responsibilities: [
        'Calculate significant wave height, peak period, and swell directional energy',
        'Track tidal amplitude and coastal current velocity vectors',
        'Issue sea-state roughness scales (Douglas Sea Scale) for safe navigation',
      ],
      sampleQuery: `What are the wave height and swell conditions near ${locName}?`,
      description: 'Monitors dynamic hydrodynamic parameters, wind-wave coupling, and long-period swell surges along continental shelf waters.',
    },
    {
      id: 'earth-observation',
      name: 'Earth Observation Agent',
      badge: 'REMOTE SENSING',
      domain: 'OPTICAL & RADAR EO',
      route: '/earth-observation',
      icon: '🛰️',
      image: imgEO,
      status: 'ONLINE',
      latency: '18ms',
      capabilities: ['Sentinel-3 Radiometry', 'Chlorophyll-a Maps', 'SST Front Extraction', 'Algal Bloom Alerts'],
      dataSources: ['Copernicus Sentinel-3 OLCI', 'Sentinel-3 SLSTR', 'ISRO Oceansat-3'],
      responsibilities: [
        'Extract high-resolution Sea Surface Temperature (SST) thermal fronts',
        'Measure Chlorophyll-a concentration gradients indicating nutrient upwelling',
        'Detect harmful algal blooms and sediment discharge plumes from estuaries',
      ],
      sampleQuery: `Show recent Sentinel-3 chlorophyll and SST readings for ${locName}`,
      description: 'Integrates spaceborne optical and thermal sensor data to map oceanic fronts, primary productivity, and water clarity.',
    },
    {
      id: 'geospatial',
      name: 'Geo-Spatial & Navigation Agent',
      badge: 'GIS & SPATIAL',
      domain: 'POSTGIS TOPOLOGY',
      route: '/navigation',
      icon: '🗺️',
      image: imgGeo,
      status: 'ONLINE',
      latency: '8ms',
      capabilities: ['Maritime Boundary Buffers', 'PostGIS Geometry Queries', 'Port Distances', 'Bathymetry Profiles'],
      dataSources: ['PostGIS Spatial Engine', 'GEBCO Bathymetry', 'UNCLOS Maritime Limits'],
      responsibilities: [
        'Perform spatial calculations for 12 NM territorial and 200 NM EEZ boundaries',
        'Verify Marine Protected Areas (MPA) and restricted defense exercise corridors',
        'Calculate shortest navigable sea routes avoiding hazards and shallow shoals',
      ],
      sampleQuery: `What are the safe navigation corridors and nearest refuge ports from ${locName}?`,
      description: 'Executes spatial topology algorithms and bathymetric clearance checks across official nautical charts and coastal limits.',
    },
    {
      id: 'disaster-safety',
      name: 'Disaster & Safety Agent',
      badge: 'EARLY WARNING',
      domain: 'CYCLONES & SWELL SURGES',
      route: '/safety',
      icon: '⚠️',
      image: imgSafety,
      status: 'ONLINE',
      latency: '9ms',
      capabilities: ['Cyclone Tracking', 'High Wave Alerts', 'Gale Warnings', 'Distress Broadcasting'],
      dataSources: ['IMD Cyclone Warning Division', 'INCOIS Early Warning Centre', 'RSMC Bulletins'],
      responsibilities: [
        'Track tropical cyclonic storm paths, central pressure, and gale radius buffers',
        'Disseminate Kallakkadal (swell surge) and tsunami early warning bulletins',
        'Deterministic override: enforce strict maritime safety bans during severe weather',
      ],
      sampleQuery: `Are there any active cyclone or high wave alerts active in ${locName}?`,
      description: 'Directly linked to India Meteorological Department and INCOIS early warning streams to safeguard coastal communities.',
    },
    {
      id: 'marine-operations',
      name: 'Marine Operations Agent',
      badge: 'MISSION PLANNING',
      domain: 'VESSEL LOGISTICS',
      route: '/operations',
      icon: '⚓',
      image: imgOps,
      status: 'ONLINE',
      latency: '15ms',
      capabilities: ['Passage Planning', 'Harbor Clearance', 'Fuel Economy Modeling', 'Multi-Criteria Decision'],
      dataSources: ['National AIS Feeds', 'Port Authority Systems', 'Fleet Registry DB'],
      responsibilities: [
        'Multi-factor operational readiness scoring for commercial and fishing vessels',
        'Port fairway clearance, pilotage windows, and anchorage status',
        'Optimize vessel departure timing using What-If temporal simulation',
      ],
      sampleQuery: `What is the operational readiness and passage clearance for departing ${locName}?`,
      description: 'Synthesizes weather, hydrodynamic, and spatial constraints into actionable operational decisions for skippers and port authorities.',
    },
  ];

  const handleLaunchAgent = (query: string) => {
    navigate('/ask', { state: { initialQuery: query } });
  };

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">{t('nav.home', 'Home')}</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">{t('nav.agents', 'Domain Agents')}</span>
          </div>
          <h1 className="page-title">
            {t('agents.title', 'Six Specialized Marine Domain Agents')}
            <span className="page-title-badge badge-agent">{t('sidebar.agents_online', '6/6 Domain Agents Online')}</span>
          </h1>
          <p className="page-subtitle">
            {t('agents.subtitle', 'Dedicated autonomous intelligence nodes engineered with domain-specific telemetry pipelines, deterministic guardrails, and cryptographic provenance.')}
          </p>
        </div>
        <div className="page-header-actions">
          <div className="coverage-pill" style={{ background: 'rgba(8, 42, 67, 0.7)', border: '1px solid rgba(22, 184, 216, 0.3)', padding: '6px 12px', borderRadius: '20px', color: '#16B8D8', fontSize: '0.8125rem', fontWeight: 600 }}>
            📍 {t('agents.operational_coverage', 'Coverage')}: {locName}
          </div>
          <Link to="/ask" className="btn-page-action primary">
            <span>{t('nav.ask', 'Ask OCEANIS')}</span>
          </Link>
        </div>
      </header>

      {/* Agents Grid */}
      <div className="agents-grid">
        {domainAgents.map((agent) => (
          <div key={agent.id} className="ocean-card agent-card">
            <div className="agent-card-header">
              <div className="agent-avatar-box">
                <span className="agent-avatar-icon">{agent.icon}</span>
              </div>
              <div className="agent-header-titles">
                <div className="agent-badge-row">
                  <span className="badge-agent">{agent.badge}</span>
                  <span className="badge-provenance">{agent.domain}</span>
                </div>
                <h3 className="agent-card-title">{agent.name}</h3>
              </div>
              <div className="agent-status-tag">
                <span className="status-dot-green"></span>
                <span>{agent.status}</span>
              </div>
            </div>

            <div className="agent-card-image-box">
              <img src={agent.image} alt={agent.name} className="agent-feature-photo" />
              <div className="agent-image-overlay">
                <span className="agent-latency-tag">⚡ Latency: {agent.latency}</span>
              </div>
            </div>

            <p className="agent-description">{agent.description}</p>

            <div className="agent-details-section">
              <div className="detail-group">
                <span className="detail-label">Core Capabilities:</span>
                <div className="capabilities-tag-cloud">
                  {agent.capabilities.map((cap, idx) => (
                    <span key={idx} className="cap-tag">{cap}</span>
                  ))}
                </div>
              </div>

              <div className="detail-group">
                <span className="detail-label">Verified Data Feeds:</span>
                <ul className="data-sources-list">
                  {agent.dataSources.map((ds, idx) => (
                    <li key={idx}>✓ {ds}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="agent-card-footer">
              <button
                type="button"
                className="btn-agent-query"
                onClick={() => handleLaunchAgent(agent.sampleQuery)}
                title={`Launch query with ${agent.name}`}
              >
                <span>Query Agent: "{agent.sampleQuery.slice(0, 45)}..."</span>
                <svg className="btn-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentsPage;
