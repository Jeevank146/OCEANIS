import React from 'react';
import { Link } from 'react-router-dom';
import { WhatIfSimulation } from '../../components/WhatIfSimulation/WhatIfSimulation';
import './WhatIfPage.css';

export const WhatIfPage: React.FC = () => {

  return (
    <div className="ocean-page-container whatif-page-root">
      {/* Page Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">What-If Scenarios</span>
          </div>
          <h1 className="page-title">
            Predictive What-If Marine Simulation Lab
            <span className="page-title-badge badge-agent">Simulation Engine</span>
          </h1>
          <p className="page-subtitle">
            Simulate operational decisions in advance. Compare weather windows, departure time shifts, and alternative routes with side-by-side hydrodynamics and risk evaluations.
          </p>
        </div>
        <div className="page-header-actions">
          <Link to="/marine-operations" className="btn-page-action secondary">
            <span>Passage Operations</span>
          </Link>
          <Link to="/ask-oceanis" className="btn-page-action primary">
            <span>Query Simulation Agent</span>
          </Link>
        </div>
      </header>

      {/* Main What-If Interactive Engine Component */}
      <div className="whatif-main-component-wrapper">
        <WhatIfSimulation />
      </div>

      {/* Additional Scenario Simulation Guidance Section */}
      <section className="whatif-guidance-section" aria-label="Simulation Guidance">
        <div className="section-header-compact">
          <h2 className="section-title-sm">Operational Simulation Principles</h2>
          <span className="section-meta-tag">Multi-Agent Hydrodynamic Physics</span>
        </div>

        <div className="guidance-cards-grid">
          <div className="ocean-card guidance-card">
            <div className="guidance-card-header">
              <span className="guidance-icon">⏱️</span>
              <strong className="guidance-title">Departure Time Window Shifts</strong>
            </div>
            <p className="guidance-desc">
              Coastal wind patterns and wave steepness often peak during early morning thermal transitions. Shifting departure by 2 to 3 hours can reduce vessel slamming and fuel burn by up to 22%.
            </p>
          </div>

          <div className="ocean-card guidance-card">
            <div className="guidance-card-header">
              <span className="guidance-icon">📍</span>
              <strong className="guidance-title">Zone-to-Zone Ground Comparison</strong>
            </div>
            <p className="guidance-desc">
              Compare pelagic biomass density against transit sea state severity across adjacent fishing grounds to balance catch yields against rough sea exposure.
            </p>
          </div>

          <div className="ocean-card guidance-card">
            <div className="guidance-card-header">
              <span className="guidance-icon">🚢</span>
              <strong className="guidance-title">Vessel Speed & Squall Resistance</strong>
            </div>
            <p className="guidance-desc">
              Speed profiling allows operators to calculate whether higher transit speeds cause excessive encounter frequencies with oncoming swell trains in coastal shipping lanes.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default WhatIfPage;
