import { API_BASE_URL } from '../../services/api';
import React from 'react';
import './Footer.css';

export const Footer: React.FC = () => {
  return (
    <footer className="ocean-footer">
      <div className="container">
        {/* Top Status Banner */}
        <div className="footer-top glass-panel">
          <div className="footer-status-pill">
            <span className="live-dot pulse"></span>
            <span className="footer-status-text">SYSTEM STATUS: ALL 6 DOMAIN AGENTS OPERATIONAL (28/28 APIS ONLINE)</span>
          </div>
          <div className="footer-quick-actions">
            <span className="footer-coverage">COASTAL COVERAGE: BAY OF BENGAL • ARABIAN SEA • INDIAN OCEAN EEZ</span>
          </div>
        </div>

        {/* Main Footer Grid */}
        <div className="footer-grid">
          {/* Brand Col */}
          <div className="footer-brand-col">
            <a href="#" className="footer-logo">
              <span className="footer-logo-icon">🌊</span>
              <span className="footer-logo-text">OCEANIS</span>
            </a>
            <span className="footer-motto">Ocean Intelligence for a Safer Tomorrow</span>
            <p className="footer-mission">
              Next-generation marine intelligence and decision support system. Grounded in orbital remote sensing, in-situ ocean buoys, PostGIS spatial computing, and deterministic safety guardrails.
            </p>
            <div className="footer-tags">
              <span className="footer-chip">INCOIS Grounded</span>
              <span className="footer-chip">IMD Doppler Radars</span>
              <span className="footer-chip">Sentinel-3 Satellites</span>
            </div>
          </div>

          {/* Col 1: Platform & Agents */}
          <div className="footer-col">
            <h4 className="footer-col-title">Intelligence Agents</h4>
            <ul className="footer-links">
              <li><a href="#agents">🐟 Fishing Intelligence Agent</a></li>
              <li><a href="#agents">🌊 Marine Conditions Agent</a></li>
              <li><a href="#agents">🛰️ Earth Observation Agent</a></li>
              <li><a href="#agents">🧭 Geo-Spatial & Navigation Agent</a></li>
              <li><a href="#agents">🚨 Disaster & Safety Agent</a></li>
              <li><a href="#agents">⚓ Marine Operations Agent</a></li>
            </ul>
          </div>

          {/* Col 2: Live Data & Maps */}
          <div className="footer-col">
            <h4 className="footer-col-title">Live Data & GIS Maps</h4>
            <ul className="footer-links">
              <li><a href="#live-overview">Live Marine Overview</a></li>
              <li><a href="#live-map">Operational Ocean GIS Map</a></li>
              <li><a href="#safety-alerts">Cyclone & Marine Alerts</a></li>
              <li><a href="#satellite-eo">Sentinel-3 Chlorophyll Bio-Optics</a></li>
              <li><a href="#satellite-eo">MODIS Sea Surface Temperatures</a></li>
              <li><a href="#what-if-scenarios">What-If Simulation Engine</a></li>
            </ul>
          </div>

          {/* Col 3: Resources & Documentation */}
          <div className="footer-col">
            <h4 className="footer-col-title">Resources & Standards</h4>
            <ul className="footer-links">
              <li><a href="#query">Ask OCEANIS Natural Query</a></li>
              <li><a href="#decision-intelligence">Decision Provenance Architecture</a></li>
              <li><a href="#trusted-sources">Institutional Telemetry Ingestion</a></li>
              <li><a href={`${API_BASE_URL}/docs`} target="_blank" rel="noreferrer">FastAPI Swagger Documentation</a></li>
              <li><a href={`${API_BASE_URL}/redoc`} target="_blank" rel="noreferrer">ReDoc API Specifications</a></li>
              <li><a href="#trust">Maritime Safety Guardrails</a></li>
            </ul>
          </div>
        </div>

        {/* Institutional Disclaimers */}
        <div className="footer-disclaimers">
          <p className="disclaimer-text">
            <strong>Data Source Disclaimer:</strong> Environmental telemetry and oceanographic parameters are ingested from official public observing agencies including INCOIS, IMD, and Copernicus Sentinel missions. Data is intended for operational decision support and situational awareness.
          </p>
          <p className="disclaimer-text">
            <strong>Safety Notice:</strong> Deterministic safety rules strictly enforce non-overridable navigation barriers for designated naval exclusion zones and active tropical cyclone paths. Maritime vessel masters retain ultimate navigational responsibility under international maritime law (SOLAS).
          </p>
        </div>

        {/* Footer Bottom */}
        <div className="footer-bottom">
          <p className="footer-copy">
            &copy; {new Date().getFullYear()} OCEANIS — Ocean Intelligence for a Safer Tomorrow. Developed for maritime safety, sustainable fishing, and coastal resilience.
          </p>
          <div className="footer-legal">
            <a href="#">Privacy Policy</a>
            <span className="dot-sep">•</span>
            <a href="#">Terms of Service</a>
            <span className="dot-sep">•</span>
            <a href="#">Security Standards</a>
            <span className="dot-sep">•</span>
            <a href="#">Contact & Support</a>
          </div>
        </div>
      </div>
    </footer>
  );
};
