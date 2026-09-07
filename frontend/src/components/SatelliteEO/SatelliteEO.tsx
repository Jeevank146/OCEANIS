import React, { useState } from 'react';
import './SatelliteEO.css';

import satCyclone from '../../assets/images/satellite_cyclone_radar.jpg';
import satEarth from '../../assets/images/hero_satellite_earth.jpg';
import satWaves from '../../assets/images/hero_ocean_waves.jpg';
import satHarbour from '../../assets/images/coastal_harbour_port.jpg';

interface SatelliteCard {
  id: string;
  title: string;
  category: string;
  image: string;
  value: string;
  location: string;
  observationTime: string;
  source: string;
  freshness: string;
  description: string;
}

const satelliteCards: SatelliteCard[] = [
  {
    id: 'sst',
    title: 'Sea Surface Temperature',
    category: 'Thermal Radiometry',
    image: satCyclone,
    value: '28.4 °C (Stable Front)',
    location: 'Bay of Bengal • Vizag Sector',
    observationTime: 'Today, 09:15 UTC',
    source: 'MODIS-Aqua / Sentinel-3 SLSTR',
    freshness: 'FRESH (Orbital Pass)',
    description: 'High-resolution thermal radiometry mapping thermal fronts, upwelling boundaries, and pelagic habitat zones.',
  },
  {
    id: 'chlorophyll',
    title: 'Chlorophyll-a Concentration',
    category: 'Ocean Colour Bio-Optics',
    image: satEarth,
    value: '2.14 mg/m³ (High Density)',
    location: 'Coastal Andhra (17.68° N, 83.22° E)',
    observationTime: 'Today, 06:40 UTC',
    source: 'Copernicus Sentinel-3 OLCI',
    freshness: 'FRESH (10m Res)',
    description: 'Multispectral ocean colour measurements identifying phytoplankton bloom density and prime potential fishing zones.',
  },
  {
    id: 'ocean_colour',
    title: 'Water Turbidity & Colour',
    category: 'Optical Radiometry',
    image: satHarbour,
    value: 'Kd(490): 0.082 m⁻¹',
    location: 'Godavari Estuary Plume',
    observationTime: 'Today, 06:40 UTC',
    source: 'Sentinel-3 OLCI Radiometer',
    freshness: 'VERIFIED',
    description: 'Diffuse attenuation coefficient and suspended sediment plume tracking along coastal harbor breakwaters.',
  },
  {
    id: 'cloud_cover',
    title: 'Cloud Cover & Radar',
    category: 'Atmospheric Profiling',
    image: satWaves,
    value: '18% Clear Sky Window',
    location: 'Central Bay of Bengal Basin',
    observationTime: 'Today, 10:00 UTC',
    source: 'INSAT-3D / IMD Radar',
    freshness: 'HOURLY SYNC',
    description: 'Infrared atmospheric water vapor profiling and convective cloud cluster monitoring across maritime transit corridors.',
  },
];

export const SatelliteEO: React.FC = () => {
  const [selectedCard, setSelectedCard] = useState<SatelliteCard | null>(null);

  return (
    <div id="satellite-eo" className="satellite-eo-panel ocean-card">
      {/* Header */}
      <div className="eo-card-header">
        <div className="eo-header-left">
          <h2 className="eo-main-title">Earth Observation Intelligence</h2>
          <p className="eo-subtitle">Latest satellite products and multispectral ocean analysis</p>
        </div>
        <div className="eo-badge-pill">
          <span className="live-dot pulse" />
          <span>SENTINEL-3 • MODIS</span>
        </div>
      </div>

      {/* Grid of Compact Satellite Thumbnail Cards */}
      <div className="eo-cards-grid">
        {satelliteCards.map((card) => (
          <div key={card.id} className="eo-thumb-card">
            <div 
              className="eo-thumb-image"
              style={{ backgroundImage: `url(${card.image})` }}
            >
              <div className="eo-thumb-overlay" />
              <span className="eo-thumb-category">{card.category}</span>
              <span className="eo-thumb-metric">{card.value}</span>
            </div>

            <div className="eo-thumb-body">
              <h4 className="eo-thumb-title">{card.title}</h4>
              <p className="eo-thumb-desc">{card.description}</p>
              
              <div className="eo-thumb-meta">
                <span className="eo-meta-source">{card.source}</span>
                <span className="eo-meta-time">{card.observationTime}</span>
              </div>

              <button
                type="button"
                className="btn-view-analysis"
                onClick={() => setSelectedCard(card)}
              >
                <span>View Analysis</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Analysis Inspector Modal Dialog */}
      {selectedCard && (
        <div className="eo-modal-backdrop" onClick={() => setSelectedCard(null)}>
          <div className="eo-modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="eo-modal-header">
              <div>
                <span className="eo-modal-cat">{selectedCard.category}</span>
                <h3 className="eo-modal-title">{selectedCard.title} Remote Sensing Report</h3>
              </div>
              <button
                type="button"
                className="btn-close-modal"
                onClick={() => setSelectedCard(null)}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <div className="eo-modal-img" style={{ backgroundImage: `url(${selectedCard.image})` }}>
              <div className="eo-modal-img-overlay" />
              <div className="eo-modal-val-box">
                <span>Measured Metric:</span>
                <strong>{selectedCard.value}</strong>
              </div>
            </div>

            <div className="eo-modal-body">
              <p className="eo-modal-desc">{selectedCard.description}</p>
              <div className="eo-modal-specs-grid">
                <div className="spec-card">
                  <span className="spec-title">Coverage Grid</span>
                  <span className="spec-detail">{selectedCard.location}</span>
                </div>
                <div className="spec-card">
                  <span className="spec-title">Pass Timestamp</span>
                  <span className="spec-detail">{selectedCard.observationTime}</span>
                </div>
                <div className="spec-card">
                  <span className="spec-title">Orbital Platform</span>
                  <span className="spec-detail">{selectedCard.source}</span>
                </div>
                <div className="spec-card">
                  <span className="spec-title">Radiometric Quality</span>
                  <span className="spec-detail">Calibrated L2 Ocean Product (QA: 0.98)</span>
                </div>
              </div>
            </div>

            <div className="eo-modal-footer">
              <button
                type="button"
                className="btn-modal-close"
                onClick={() => setSelectedCard(null)}
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
