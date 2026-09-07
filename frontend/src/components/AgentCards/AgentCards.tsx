import React from 'react';
import './AgentCards.css';

import imgFishing from '../../assets/images/hero_coastal_fishing.jpg';
import imgMarine from '../../assets/images/hero_ocean_waves.jpg';
import imgEO from '../../assets/images/hero_satellite_earth.jpg';
import imgGeo from '../../assets/images/geospatial_gis_coastline.jpg';
import imgSafety from '../../assets/images/satellite_cyclone_radar.jpg';
import imgOps from '../../assets/images/marine_operations_vessel.jpg';

interface DomainAgent {
  id: string;
  name: string;
  domain: string;
  tagline: string;
  description: string;
  image: string;
  capabilities: string[];
  themeColor: string;
  sampleQuery: string;
  apiEndpoint: string;
}

const domainAgents: DomainAgent[] = [
  {
    id: 'fishing',
    name: 'Fishing Intelligence Agent',
    domain: 'BIO-SUITABILITY',
    tagline: 'Precision fishing intelligence',
    description: 'PFZ thermal-optic suitability scoring, satellite SST gradients, and target species matching.',
    image: imgFishing,
    capabilities: ['PFZ Advisories', 'SST Gradients', 'Species Match'],
    themeColor: '#00a896',
    sampleQuery: 'Can I go fishing tomorrow from Kakinada?',
    apiEndpoint: 'POST /api/v1/agents/fishing/analyze',
  },
  {
    id: 'marine_conditions',
    name: 'Marine Conditions Agent',
    domain: 'PHYSICAL DYNAMICS',
    tagline: 'Wave heights & swell dynamics',
    description: 'Physics-informed ocean state analysis evaluating wave heights, swell periods, and sea-keeping limits.',
    image: imgMarine,
    capabilities: ['Significant Wave Height', 'Swell Period', 'Sea State'],
    themeColor: '#0284c7',
    sampleQuery: 'What are the current sea state and wave conditions near Kakinada?',
    apiEndpoint: 'POST /api/v1/agents/marine-conditions/analyze',
  },
  {
    id: 'earth_observation',
    name: 'Earth Observation Agent',
    domain: 'REMOTE SENSING',
    tagline: 'Orbital bio-optics & SST radiometry',
    description: 'Direct ingestion of Sentinel-3 OLCI and MODIS-Aqua feeds tracking chlorophyll-a and thermal fronts.',
    image: imgEO,
    capabilities: ['Sentinel-3 OLCI', 'Chlorophyll-a', 'Thermal Fronts'],
    themeColor: '#06b6d4',
    sampleQuery: 'What is the satellite chlorophyll condition near 16.97, 82.25?',
    apiEndpoint: 'POST /api/v1/agents/earth-observation/analyze',
  },
  {
    id: 'geospatial_navigation',
    name: 'Geo-Spatial & Navigation Agent',
    domain: 'GEOFENCING',
    tagline: 'PostGIS maritime boundary clearance',
    description: 'Spatial intelligence mapping coastal ports, EEZ boundaries, naval exclusions, and marine sanctuaries.',
    image: imgGeo,
    capabilities: ['Naval Restricted Zones', 'MPA Sanctuaries', 'Harbor Clearance'],
    themeColor: '#6366f1',
    sampleQuery: 'Are there restricted naval zones between Kakinada and Vizag?',
    apiEndpoint: 'POST /api/v1/agents/geospatial/analyze',
  },
  {
    id: 'disaster_safety',
    name: 'Disaster & Safety Agent',
    domain: 'HAZARD MITIGATION',
    tagline: 'Cyclone shields & refuge havens',
    description: 'Hazard evaluation tracking cyclone paths, storm surge polygons, and automated safe harbor routing.',
    image: imgSafety,
    capabilities: ['Cyclone Tracking', 'Storm Surge Polygons', 'Port Refuge'],
    themeColor: '#dc2626',
    sampleQuery: 'Are there active cyclone warnings near Vizag?',
    apiEndpoint: 'POST /api/v1/agents/disaster-safety/analyze',
  },
  {
    id: 'marine_operations',
    name: 'Marine Operations Agent',
    domain: 'VOYAGE PLANNING',
    tagline: 'Route operations & travel ETA',
    description: 'Voyage routing calculating nautical distance, vessel speed profiling, and departure weather windows.',
    image: imgOps,
    capabilities: ['Nautical Miles', 'Speed Profiling', 'Weather Windows'],
    themeColor: '#d97706',
    sampleQuery: 'Is it safe to travel from Kakinada Port to Visakhapatnam Port?',
    apiEndpoint: 'POST /api/v1/agents/marine-operations/analyze',
  },
];

interface AgentCardsProps {
  onSelectAgentQuery?: (query: string) => void;
}

export const AgentCards: React.FC<AgentCardsProps> = ({ onSelectAgentQuery }) => {
  const handleCardClick = (sampleQuery: string) => {
    if (onSelectAgentQuery) {
      onSelectAgentQuery(sampleQuery);
    } else {
      const queryInput = document.getElementById('oceanis-query-input') as HTMLInputElement;
      if (queryInput) {
        queryInput.value = sampleQuery;
        queryInput.focus();
        document.getElementById('query')?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <div id="agents" className="agents-panel ocean-card">
      {/* Header */}
      <div className="agents-card-header">
        <div className="agents-header-left">
          <h2 className="agents-main-title">Six Domain Intelligence Agents</h2>
          <p className="agents-subtitle">Autonomous multi-agent intelligence reasoning under deterministic safety guardrails</p>
        </div>
        <div className="agents-status-pill">
          <span className="live-dot pulse" />
          <span>6/6 AGENTS ACTIVE</span>
        </div>
      </div>

      {/* 6 Grid Cards */}
      <div className="agents-grid-layout">
        {domainAgents.map((agent) => (
          <div key={agent.id} className="agent-compact-card">
            {/* Photographic Image Thumbnail Header */}
            <div 
              className="agent-card-banner"
              style={{ backgroundImage: `url(${agent.image})` }}
            >
              <div className="agent-banner-overlay" />
              <div className="agent-banner-content">
                <span className="agent-category-tag">{agent.domain}</span>
                <span className="agent-live-status">
                  <span className="agent-live-dot" />
                  Active
                </span>
              </div>
            </div>

            {/* Card Content Body */}
            <div className="agent-card-content">
              <h3 className="agent-card-title">{agent.name}</h3>
              <p className="agent-card-tagline">{agent.tagline}</p>
              <p className="agent-card-desc">{agent.description}</p>

              {/* Capability Chips */}
              <div className="agent-capabilities-row">
                {agent.capabilities.map((cap, i) => (
                  <span key={i} className="agent-cap-chip">
                    {cap}
                  </span>
                ))}
              </div>

              {/* Footer Trigger */}
              <div className="agent-card-action-row">
                <button
                  type="button"
                  className="btn-agent-trigger"
                  onClick={() => handleCardClick(agent.sampleQuery)}
                  title={`Run sample query for ${agent.name}`}
                >
                  <span>Query Agent</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
