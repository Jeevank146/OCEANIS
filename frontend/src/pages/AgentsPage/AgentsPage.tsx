import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
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

  const domainAgents: DomainAgentDetail[] = [
    {
      id: 'fishing',
      name: 'Fishing Intelligence Agent',
      badge: 'BIO-SUITABILITY',
      domain: 'PELAGIC BIOMASS & PFZ',
      route: '/fishing-intelligence',
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
      sampleQuery: 'Can I go fishing tomorrow from Kakinada and what are the top PFZ coordinates?',
      description: 'Specialized in marine bio-optics and fisheries intelligence, matching ocean color and thermal fronts to maximize sustainable catch while conserving fuel.',
    },
    {
      id: 'marine-conditions',
      name: 'Marine Conditions Agent',
      badge: 'PHYSICS DYNAMICS',
      domain: 'OCEAN & WEATHER PHYSICS',
      route: '/marine-conditions',
      icon: '🌊',
      image: imgMarine,
      status: 'ONLINE',
      latency: '11ms',
      capabilities: ['Significant Wave Height', 'Swell Period', 'Sea State 3-5', 'Capsizing Risk'],
      dataSources: ['INCOIS Moored Buoy Network', 'IMD Coastal Doppler Radar', 'ECMWF Wave Models'],
      responsibilities: [
        'Real-time tracking of wave height, swell period, currents, and salinity',
        '24-hour hydrodynamic progression modeling and capsizing risk assessment',
        'High tide, flood stage, and coastal current drift calculations',
      ],
      sampleQuery: 'What are the current sea state and wave conditions near Kakinada and Vizag?',
      description: 'Monitors 12+ real-time physical and oceanographic parameters, alerting operators to sea state transitions, breaking waves, and strong longshore currents.',
    },
    {
      id: 'earth-observation',
      name: 'Earth Observation Agent',
      badge: 'REMOTE SENSING',
      domain: 'ORBITAL BIO-OPTICS',
      route: '/earth-observation',
      icon: '🛰️',
      image: imgEO,
      status: 'ONLINE',
      latency: '18ms',
      capabilities: ['Sentinel-3 OLCI/SLSTR', 'Chlorophyll-a 10m', 'Thermal Fronts', 'Turbidity Plumes'],
      dataSources: ['Sentinel-3 OLCI/SLSTR', 'Sentinel-2 MSI', 'ISRO Oceansat-3 (EOS-06)', 'INSAT-3DR'],
      responsibilities: [
        'Radiometric ingestion of optical ocean color and multi-channel infrared passes',
        'Sediment plume tracking, riverine discharge turbidity, and coastal erosion monitoring',
        'Atmospheric cloud screening and radiometric quality validation',
      ],
      sampleQuery: 'Analyze Sentinel-3 pass quality and coastal turbidity plume off Godavari mouth.',
      description: 'Ingests multi-mission optical and thermal satellite telemetry, extracting ocean color bio-optics, sediment dynamics, and synoptic convective patterns.',
    },
    {
      id: 'geospatial',
      name: 'Geo-Spatial & Navigation Agent',
      badge: 'POSTGIS GIS',
      domain: 'MARITIME BOUNDARIES & CLEARANCE',
      route: '/geo-spatial',
      icon: '🧭',
      image: imgGeo,
      status: 'ONLINE',
      latency: '8ms',
      capabilities: ['12 NM Territorial Limit', '200 NM EEZ Border', 'Naval Exercise Zones', 'Harbor Approaches'],
      dataSources: ['PostGIS EPSG:4326', 'UNCLOS Maritime Boundary Database', 'Naval Hydrographic Office Charts'],
      responsibilities: [
        'Point-in-polygon verification for 12 NM Territorial Sea and 200 NM EEZ boundaries',
        'Active naval firing corridor and marine protected area clearance validation',
        'Geodesic distance calculation to baselines, shoals, and navigational hazards',
      ],
      sampleQuery: 'Verify boundary compliance and distance to 12 NM baseline for waypoint 17.68°N, 83.21°E.',
      description: 'Maintains high-performance spatial indexing over maritime jurisdictions, preventing unlawful boundary incursions and navigation into hazardous exclusion zones.',
    },
    {
      id: 'disaster-safety',
      name: 'Disaster & Safety Agent',
      badge: 'EARLY WARNING',
      domain: 'HAZARD MITIGATION & VETO',
      route: '/disaster-safety',
      icon: '🛡️',
      image: imgSafety,
      status: 'ONLINE',
      latency: '9ms',
      capabilities: ['Cyclone Surveillance', 'Storm Surge Buffers', 'Safe Port Refuge', 'Safety Veto Shield'],
      dataSources: ['IMD Cyclone Warning Division', 'INCOIS Marine Early Warning Centre', 'Indian Coast Guard MRCC'],
      responsibilities: [
        'Continuous synoptic surveillance for tropical cyclones and depression tracks',
        'Kallakkadal / high wave alert synthesis and storm surge inundation buffers',
        'Fishermen return-to-shore protocols and closest safe port refuge recommendations',
      ],
      sampleQuery: 'Are there active storm warnings, cyclone alerts or high swell advisories within 100 NM of Vizag?',
      description: 'Authoritative safety sentinel that issues life-saving marine warnings and enforces strict veto guardrails over all operational decisions.',
    },
    {
      id: 'marine-operations',
      name: 'Marine Operations Agent',
      badge: 'VOYAGE OPS',
      domain: 'PASSAGE PLANNING & LOGISTICS',
      route: '/marine-operations',
      icon: '⚓',
      image: imgOps,
      status: 'ONLINE',
      latency: '12ms',
      capabilities: ['Nautical Mileage & ETA', 'Speed Profiling 8-16 kts', 'Weather Windows', 'Fairway Depth'],
      dataSources: ['Port VTS AIS Feeds', 'Survey of India Tide Tables', 'Nautical Passage Optimization Engine'],
      responsibilities: [
        'Port-to-port passage planning, waypoint sequencing, and speed profiling',
        'Fuel consumption and optimal departure window calculation with tidal assistance',
        'Port fairway depth, pilotage status, and berth congestion evaluation',
      ],
      sampleQuery: 'Calculate passage plan, speed profile, and optimal departure window from Vizag to Kakinada.',
      description: 'Optimizes commercial and artisanal maritime voyages, computing shortest safe tracks, fuel burn rates, and fairway clearances for safe transit.',
    },
  ];

  const handleAskAgent = (agent: DomainAgentDetail) => {
    navigate('/ask-oceanis', { state: { initialQuery: agent.sampleQuery } });
  };

  return (
    <div className="ocean-page-container agents-page-root">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Agents</span>
          </div>
          <h1 className="page-title">
            Six Domain Intelligence Agents
            <span className="page-title-badge badge-agent">6/6 Online</span>
          </h1>
          <p className="page-subtitle">
            OCEANIS coordinates six specialized domain agents orchestrated under a deterministic consensus layer with zero hallucination.
          </p>
        </div>
        <div className="page-header-actions">
          <Link to="/decision-intelligence" className="btn-page-action secondary">
            <span>Pipeline Provenance</span>
          </Link>
          <Link to="/ask-oceanis" className="btn-page-action primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span>Launch Multi-Agent Chat</span>
          </Link>
        </div>
      </header>

      {/* Agents 6 Cards Grid */}
      <div className="agents-directory-grid">
        {domainAgents.map((agent) => (
          <div key={agent.id} className="ocean-card domain-agent-card">
            {/* Photographic Image Thumbnail Header */}
            <div
              className="agent-card-banner"
              style={{ backgroundImage: `url(${agent.image})` }}
            >
              <div className="agent-banner-overlay" />
              <div className="agent-banner-content">
                <span className="agent-domain-badge">{agent.badge}</span>
                <div className="agent-status-capsule">
                  <span className="live-dot pulse" />
                  <span className="agent-latency">{agent.latency}</span>
                </div>
              </div>
            </div>

            {/* Content Body */}
            <div className="agent-card-body">
              <div className="agent-card-header-row">
                <div className="agent-name-group">
                  <span className="agent-icon-emoji">{agent.icon}</span>
                  <h3 className="agent-title-name">{agent.name}</h3>
                </div>
                <span className="agent-tagline-text">{agent.domain}</span>
              </div>

              <p className="agent-desc-text">{agent.description}</p>

              {/* Capability Chips */}
              <div className="agent-capabilities-section">
                <span className="specs-subheading">Specialized Capabilities:</span>
                <div className="agent-cap-chips-row">
                  {agent.capabilities.map((cap, i) => (
                    <span key={i} className="agent-cap-chip">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>

              {/* Responsibilities */}
              <div className="agent-specs-section">
                <span className="specs-subheading">Core Operational Functions:</span>
                <ul className="agent-resp-list">
                  {agent.responsibilities.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>

              {/* Data Sources */}
              <div className="agent-sources-strip">
                <span className="specs-subheading">Institutional Data Feeds:</span>
                <div className="agent-source-tags">
                  {agent.dataSources.map((s, i) => (
                    <span key={i} className="source-tag-item">{s}</span>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="agent-card-actions">
                <Link to={agent.route} className="btn-agent-nav">
                  <span>Open Dedicated Workspace</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </Link>
                <button
                  type="button"
                  className="btn-agent-ask"
                  onClick={() => handleAskAgent(agent)}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                  <span>Query Agent</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentsPage;
