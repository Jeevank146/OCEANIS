import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './MarineOperationsPage.css';

export const MarineOperationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [originPort, setOriginPort] = useState<string>('Visakhapatnam');
  const [destPort, setDestPort] = useState<string>('Kakinada');
  const [cruisingSpeedKnots, setCruisingSpeedKnots] = useState<number>(10.5);

  const routes: Record<string, number> = {
    'Visakhapatnam-Kakinada': 68.5,
    'Visakhapatnam-Gopalpur': 112.0,
    'Visakhapatnam-Paradip': 198.4,
    'Visakhapatnam-Chennai': 310.0,
    'Kakinada-Chennai': 245.0,
    'Gopalpur-Paradip': 88.0,
  };

  const routeKey = `${originPort}-${destPort}`;
  const reverseKey = `${destPort}-${originPort}`;
  const routeDistance = routes[routeKey] || routes[reverseKey] || 75.0;

  const transitTimeHours = routeDistance / cruisingSpeedKnots;
  const estimatedFuelLitres = routeDistance * 3.4;

  const handleQueryOperationsAgent = () => {
    navigate('/ask-oceanis', {
      state: { initialQuery: `Calculate voyage plan, weather window, fuel consumption, and fairway clearance from ${originPort} to ${destPort} at ${cruisingSpeedKnots} knots.` },
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
            <span className="page-breadcrumb-current">Marine Operations</span>
          </div>
          <h1 className="page-title">
            Marine Operations & Voyage Route Planning
            <span className="page-title-badge badge-agent">Operations Agent</span>
          </h1>
          <p className="page-subtitle">
            Nautical passage planning, fuel profiling, fairway clearance, and weather-routed voyage optimization for coastal and commercial vessels.
          </p>
        </div>
        <div className="page-header-actions">
          <button
            type="button"
            className="btn-page-action primary"
            onClick={handleQueryOperationsAgent}
          >
            <span>Ask Operations Agent</span>
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <div className="ops-layout-grid">
        {/* Left Column: Voyage Planning Calculator */}
        <div className="ops-left-col">
          <div className="ocean-card voyage-calc-card">
            <div className="card-top-header">
              <h3>Passage Planning & Fuel Calculator</h3>
              <span className="badge-tool">Route Optimizer</span>
            </div>

            <div className="route-select-row">
              <div className="route-field">
                <label>Departure Port (Origin)</label>
                <select
                  value={originPort}
                  onChange={(e) => setOriginPort(e.target.value)}
                  className="ops-select"
                >
                  <option value="Visakhapatnam">Visakhapatnam (VPT)</option>
                  <option value="Kakinada">Kakinada Deepwater</option>
                  <option value="Gopalpur">Gopalpur Port</option>
                  <option value="Paradip">Paradip Roadstead</option>
                  <option value="Chennai">Chennai Harbour</option>
                </select>
              </div>

              <div className="route-field">
                <label>Arrival Port (Destination)</label>
                <select
                  value={destPort}
                  onChange={(e) => setDestPort(e.target.value)}
                  className="ops-select"
                >
                  <option value="Kakinada">Kakinada Deepwater</option>
                  <option value="Visakhapatnam">Visakhapatnam (VPT)</option>
                  <option value="Gopalpur">Gopalpur Port</option>
                  <option value="Paradip">Paradip Roadstead</option>
                  <option value="Chennai">Chennai Harbour</option>
                </select>
              </div>
            </div>

            <div className="speed-slider-field">
              <div className="speed-labels">
                <label>Target Cruising Speed</label>
                <strong>{cruisingSpeedKnots} Knots</strong>
              </div>
              <input
                type="range"
                min="6"
                max="24"
                step="0.5"
                value={cruisingSpeedKnots}
                onChange={(e) => setCruisingSpeedKnots(parseFloat(e.target.value))}
                className="ops-slider"
              />
            </div>

            {/* Calculated Passage Summary */}
            <div className="passage-summary-box">
              <div className="summary-stat">
                <span className="stat-name">Total Distance</span>
                <strong className="stat-val">{routeDistance.toFixed(1)} NM</strong>
              </div>
              <div className="summary-stat">
                <span className="stat-name">Estimated Transit</span>
                <strong className="stat-val">{transitTimeHours.toFixed(1)} Hours</strong>
              </div>
              <div className="summary-stat">
                <span className="stat-name">Fuel Consumption</span>
                <strong className="stat-val">{estimatedFuelLitres.toFixed(0)} Litres</strong>
              </div>
              <div className="summary-stat">
                <span className="stat-name">Optimal Departure</span>
                <strong className="stat-val text-success">04:30 IST (Tide Assist)</strong>
              </div>
            </div>
          </div>

          {/* Scenario Planning Action Card */}
          <div className="ocean-card scenario-planning-card">
            <div className="scenario-planning-header">
              <div className="scenario-planning-title-group">
                <span className="scenario-planning-icon">⏱️</span>
                <div>
                  <h3 className="scenario-planning-title">Scenario Planning</h3>
                  <span className="scenario-badge-sim">WHAT-IF SIMULATION</span>
                </div>
              </div>
            </div>
            <p className="scenario-planning-desc">
              Simulate operational decisions in advance. Compare weather windows, departure time shifts, and alternate routes with side-by-side hydrodynamics.
            </p>
            <div className="scenario-planning-action">
              <Link to="/what-if" className="btn-ops-whatif">
                <span>Run What-If</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
            </div>
          </div>
        </div>

        {/* Right Column: Coastal Port Readiness & Fairway Status */}
        <div className="ops-right-col">
          <div className="ocean-card port-readiness-card">
            <div className="card-top-header">
              <h3>Port Fairway & Pilotage Readiness</h3>
              <span className="badge-source">Port VTS Live</span>
            </div>

            <div className="port-status-list">
              <div className="port-status-row">
                <div className="port-info-main">
                  <strong>Visakhapatnam Outer Harbor</strong>
                  <span>Channel Depth: 16.5m • Fairway: Clear</span>
                </div>
                <span className="badge-port-open">OPEN</span>
              </div>

              <div className="port-status-row">
                <div className="port-info-main">
                  <strong>Kakinada Anchorage</strong>
                  <span>Channel Depth: 14.0m • Light Swell</span>
                </div>
                <span className="badge-port-open">OPEN</span>
              </div>

              <div className="port-status-row">
                <div className="port-info-main">
                  <strong>Paradip Fairway Corridor</strong>
                  <span>Channel Depth: 17.1m • Tug Pilotage Active</span>
                </div>
                <span className="badge-port-caution">PILOTAGE ONLY</span>
              </div>

              <div className="port-status-row">
                <div className="port-info-main">
                  <strong>Gopalpur Port Haven</strong>
                  <span>Channel Depth: 12.5m • Berthing Normal</span>
                </div>
                <span className="badge-port-open">OPEN</span>
              </div>
            </div>

            <div className="berthing-guidance-box">
              <strong>Maritime Operations Protocol:</strong>
              <p>
                All vessels planning coastal transit must file passage plans with local VTS at least 2 hours prior to unmooring. Confirm VHF Channel 12 for port control.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarineOperationsPage;
