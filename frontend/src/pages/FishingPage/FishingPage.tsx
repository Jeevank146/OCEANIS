import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import './FishingPage.css';

interface SpeciesScore {
  name: string;
  scientificName: string;
  suitabilityScore: number;
  depthRange: string;
  peakSeason: string;
  habitat: string;
  confidence: 'HIGH' | 'MEDIUM' | 'VERY HIGH';
}

export const FishingPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedLocation } = useLocationContext();
  const [selectedZone, setSelectedZone] = useState<string>(
    selectedLocation.city.toLowerCase().includes('kakinada') ? 'kakinada-bank' : 'vizag-outer'
  );
  const [vesselType, setVesselType] = useState<string>('motorized');
  const [targetDistance, setTargetDistance] = useState<number>(14.5);

  const speciesList: SpeciesScore[] = [
    {
      name: 'Indian Mackerel (Kanagurta)',
      scientificName: 'Rastrelliger kanagurta',
      suitabilityScore: 92,
      depthRange: '15 - 45 m',
      peakSeason: 'Sep - Feb',
      habitat: 'Pelagic thermal boundaries & chlorophyll fronts',
      confidence: 'VERY HIGH',
    },
    {
      name: 'Yellowfin Tuna',
      scientificName: 'Thunnus albacares',
      suitabilityScore: 88,
      depthRange: '40 - 120 m',
      peakSeason: 'Oct - Mar',
      habitat: 'Deep thermocline edges (SST 27.5 - 28.8°C)',
      confidence: 'HIGH',
    },
    {
      name: 'Oil Sardine (Kavallu)',
      scientificName: 'Sardinella longiceps',
      suitabilityScore: 84,
      depthRange: '10 - 30 m',
      peakSeason: 'Aug - Jan',
      habitat: 'Coastal upwelling plumes with high phytoplankton',
      confidence: 'HIGH',
    },
    {
      name: 'Ribbonfish (Savam)',
      scientificName: 'Trichiurus lepturus',
      suitabilityScore: 78,
      depthRange: '25 - 75 m',
      peakSeason: 'Sep - Apr',
      habitat: 'Demersal/benthopelagic sandy-mud shelf',
      confidence: 'MEDIUM',
    },
    {
      name: 'Squid / Cuttlefish',
      scientificName: 'Sepioteuthis lessoniana',
      suitabilityScore: 81,
      depthRange: '20 - 60 m',
      peakSeason: 'Oct - Feb',
      habitat: 'Rocky shelf margins & nocturnal light convergence',
      confidence: 'HIGH',
    },
  ];

  const zones = [
    {
      id: 'vizag-outer',
      name: 'Visakhapatnam Outer Shelf (Zone PFZ-82)',
      distance: 14.5,
      bearing: '095° ESE',
      score: 91,
      sst: '28.2°C',
      sstGrad: '0.65°C / 3NM',
      chlorophyll: '0.84 mg/m³',
      depth: '48m',
      fuelEstimate: '38 Litres',
      recommendation: 'Optimal Yield Window (04:00 - 11:30 hrs)',
    },
    {
      id: 'kakinada-bank',
      name: 'Kakinada Spit & Godavari Plume (Zone PFZ-44)',
      distance: 22.0,
      bearing: '175° S',
      score: 86,
      sst: '28.9°C',
      sstGrad: '0.45°C / 3NM',
      chlorophyll: '1.25 mg/m³',
      depth: '32m',
      fuelEstimate: '56 Litres',
      recommendation: 'High Phytoplankton, Moderate Swell',
    },
    {
      id: 'bheemunipatnam',
      name: 'Bheemunipatnam Coastal Upwelling (Zone PFZ-19)',
      distance: 9.8,
      bearing: '040° NE',
      score: 79,
      sst: '27.9°C',
      sstGrad: '0.38°C / 3NM',
      chlorophyll: '0.62 mg/m³',
      depth: '28m',
      fuelEstimate: '26 Litres',
      recommendation: 'Quick Return, Suitable for Small Crafts',
    },
  ];

  const activeZoneData = zones.find(z => z.id === selectedZone) || zones[0];

  const handleLaunchAgentQuery = (zoneName: string) => {
    navigate('/ask-oceanis', {
      state: { initialQuery: `Evaluate fishing suitability, species probability and safe transit for ${zoneName}` },
    });
  };

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Fishing Intelligence</span>
          </div>
          <h1 className="page-title">
            Potential Fishing Zone (PFZ) & Marine Biomass Intelligence
            <span className="page-title-badge badge-agent">Fishing Agent</span>
          </h1>
          <p className="page-subtitle">
            INCOIS satellite bio-optical Chlorophyll-a telemetry paired with Copernicus SLSTR thermal front analysis and species-specific habitat algorithms.
          </p>
        </div>
        <div className="page-header-actions">
          <button
            type="button"
            className="btn-page-action primary"
            onClick={() => handleLaunchAgentQuery(activeZoneData.name)}
          >
            <span>Ask Fishing Agent</span>
          </button>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="fishing-layout-grid">
        {/* Left Column: Zone Selector + Why This Location? Explainability */}
        <div className="fishing-left-col">
          {/* Zone Selector Card */}
          <div className="ocean-card fishing-zones-card">
            <div className="card-top-header">
              <h3>Active PFZ Advisory Zones</h3>
              <span className="badge-source">INCOIS & Sentinel-3</span>
            </div>
            <p className="card-desc">
              Select an oceanographic waypoint to inspect bio-physical parameters and species habitat suitability.
            </p>

            <div className="zone-button-list">
              {zones.map((zone) => (
                <button
                  key={zone.id}
                  type="button"
                  className={`zone-select-btn ${selectedZone === zone.id ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedZone(zone.id);
                    setTargetDistance(zone.distance);
                  }}
                >
                  <div className="zone-btn-left">
                    <span className="zone-badge-score">{zone.score}%</span>
                    <div className="zone-btn-meta">
                      <strong>{zone.name}</strong>
                      <span className="zone-sub">{zone.distance} NM • {zone.bearing} • Depth {zone.depth}</span>
                    </div>
                  </div>
                  <span className="zone-chevron">›</span>
                </button>
              ))}
            </div>
          </div>

          {/* What-If Fishing Scenario Action Card */}
          <div className="ocean-card whatif-fishing-card">
            <div className="whatif-fishing-header">
              <div className="whatif-fishing-title-group">
                <span className="whatif-fishing-icon">⏱️</span>
                <div>
                  <h3 className="whatif-fishing-title">What-If Fishing Scenario</h3>
                  <span className="whatif-badge-sim">SIMULATION</span>
                </div>
              </div>
            </div>
            <p className="whatif-fishing-desc">
              Compare different fishing times or fishing zones and understand how marine conditions, suitability, confidence and risk may change.
            </p>
            <div className="whatif-fishing-action">
              <Link to="/what-if" className="btn-run-whatif-fishing">
                <span>Run What-If Analysis</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Explainability Engine: "Why this location?" */}
          <div className="ocean-card explainability-card">
            <div className="card-top-header">
              <h3>Scientific Explainability Engine</h3>
              <span className="badge-provenance">Audit Layer</span>
            </div>
            <h4 className="explain-target-title">
              Why Zone: {activeZoneData.name}?
            </h4>
            <div className="explain-pillars-list">
              <div className="explain-pillar">
                <div className="pillar-num">01</div>
                <div className="pillar-content">
                  <strong>Thermal Front & Eddy Convergence</strong>
                  <p>
                    SLSTR radiometric sensors detect a thermal gradient of <strong>{activeZoneData.sstGrad}</strong>. Pelagic fish aggregate along these sharp water mass boundaries where micro-eddies concentrate forage organisms.
                  </p>
                </div>
              </div>

              <div className="explain-pillar">
                <div className="pillar-num">02</div>
                <div className="pillar-content">
                  <strong>Phytoplankton Biomass (Chlorophyll-a)</strong>
                  <p>
                    Sentinel-3 OLCI ocean color data indicates <strong>{activeZoneData.chlorophyll}</strong>. This optical density falls inside the optimal primary productivity envelope (0.6 - 1.5 mg/m³).
                  </p>
                </div>
              </div>

              <div className="explain-pillar">
                <div className="pillar-num">03</div>
                <div className="pillar-content">
                  <strong>Bathymetry Upwelling Ridge</strong>
                  <p>
                    GEBCO shelf data shows a depth contour of <strong>{activeZoneData.depth}</strong>, creating localized bottom current deflection and nutrient upwelling.
                  </p>
                </div>
              </div>
            </div>

            <div className="operational-recommendation-box">
              <span className="rec-icon">💡</span>
              <div className="rec-text">
                <strong>Operational Guidance:</strong> {activeZoneData.recommendation}. Estimated fuel requirement for round trip is approximately {activeZoneData.fuelEstimate}.
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Species Probabilities + Fuel/Trip Calculator */}
        <div className="fishing-right-col">
          {/* Target Species Probabilities */}
          <div className="ocean-card species-card">
            <div className="card-top-header">
              <h3>Species Occurrence & Habitat Matching</h3>
              <span className="badge-model">Biomass Model v2.1</span>
            </div>
            <div className="species-list">
              {speciesList.map((sp) => (
                <div key={sp.name} className="species-item">
                  <div className="species-header">
                    <div>
                      <strong className="sp-name">{sp.name}</strong>
                      <span className="sp-sci">{sp.scientificName}</span>
                    </div>
                    <div className="sp-score-box">
                      <span className="sp-score-num">{sp.suitabilityScore}%</span>
                      <span className="sp-score-label">Suitability</span>
                    </div>
                  </div>
                  <div className="sp-progress-track">
                    <div
                      className="sp-progress-bar"
                      style={{
                        width: `${sp.suitabilityScore}%`,
                        background: sp.suitabilityScore > 85 ? '#16a34a' : sp.suitabilityScore > 75 ? '#0284c7' : '#d97706',
                      }}
                    />
                  </div>
                  <div className="sp-meta-row">
                    <span>Depth: <strong>{sp.depthRange}</strong></span>
                    <span>Peak: <strong>{sp.peakSeason}</strong></span>
                    <span>Confidence: <strong className="conf-badge">{sp.confidence}</strong></span>
                  </div>
                  <p className="sp-habitat">{sp.habitat}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Voyage Fuel & Catch Return Calculator */}
          <div className="ocean-card fuel-calc-card">
            <div className="card-top-header">
              <h3>Voyage Fuel & Economic Index Calculator</h3>
              <span className="badge-tool">Planning</span>
            </div>
            <div className="calc-inputs-grid">
              <div className="calc-field">
                <label>Vessel Category</label>
                <select
                  value={vesselType}
                  onChange={(e) => setVesselType(e.target.value)}
                  className="calc-select"
                >
                  <option value="motorized">Motorized Craft (OBM 9.9 HP)</option>
                  <option value="mechanized">Mechanized Trawler (120 HP)</option>
                  <option value="artisanal">Traditional FRP Boat (5 HP)</option>
                </select>
              </div>

              <div className="calc-field">
                <label>Target Distance: {targetDistance} NM</label>
                <input
                  type="range"
                  min="5"
                  max="40"
                  step="0.5"
                  value={targetDistance}
                  onChange={(e) => setTargetDistance(parseFloat(e.target.value))}
                  className="calc-slider"
                />
              </div>
            </div>

            <div className="calc-results-strip">
              <div className="calc-res-item">
                <span className="res-label">Estimated Diesel</span>
                <span className="res-val">
                  {vesselType === 'mechanized' ? (targetDistance * 4.2).toFixed(0) : (targetDistance * 1.8).toFixed(0)} L
                </span>
              </div>
              <div className="calc-res-item">
                <span className="res-label">Estimated Transit</span>
                <span className="res-val">
                  {(targetDistance / 7.5).toFixed(1)} hrs
                </span>
              </div>
              <div className="calc-res-item">
                <span className="res-label">Biomass Index</span>
                <span className="res-val highlight">
                  {(8.5 * (activeZoneData.score / 100)).toFixed(1)} / 10
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FishingPage;
