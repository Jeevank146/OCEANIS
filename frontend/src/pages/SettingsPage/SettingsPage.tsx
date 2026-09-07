import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './SettingsPage.css';

export const SettingsPage: React.FC = () => {
  const [operatorName, setOperatorName] = useState<string>('Cmdr. R. Verma');
  const [callSign, setCallSign] = useState<string>('VPT-OPS-04');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en');
  const [unitSystem, setUnitSystem] = useState<'nautical' | 'metric'>('nautical');
  const [smsAlerts, setSmsAlerts] = useState<boolean>(true);
  const [vhfRelay, setVhfRelay] = useState<boolean>(true);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Settings</span>
          </div>
          <h1 className="page-title">
            Platform Settings & Maritime Operator Profile
            <span className="page-title-badge badge-agent">Operator Config</span>
          </h1>
          <p className="page-subtitle">
            Configure authenticated maritime operator details, default linguistic preferences, nautical measurement units, and emergency distress broadcast relays.
          </p>
        </div>
      </header>

      {/* Main Form */}
      <div className="settings-layout-grid">
        <div className="ocean-card settings-card">
          <div className="card-top-header">
            <h3>Operator & Platform Configuration</h3>
            <span className="badge-source">Authenticated Profile</span>
          </div>

          <form onSubmit={handleSaveSettings} className="settings-form">
            {/* Operator Profile Section */}
            <div className="settings-section">
              <span className="settings-section-title">1. Maritime Operator Profile</span>
              <div className="settings-fields-grid">
                <div className="form-field">
                  <label>Operator Name & Rank</label>
                  <input
                    type="text"
                    value={operatorName}
                    onChange={(e) => setOperatorName(e.target.value)}
                    className="settings-input"
                  />
                </div>
                <div className="form-field">
                  <label>Radio Call Sign / Unit Identifier</label>
                  <input
                    type="text"
                    value={callSign}
                    onChange={(e) => setCallSign(e.target.value)}
                    className="settings-input"
                  />
                </div>
              </div>
            </div>

            {/* Units & Language Section */}
            <div className="settings-section">
              <span className="settings-section-title">2. Language & Unit System</span>
              <div className="settings-fields-grid">
                <div className="form-field">
                  <label>Default Interface Language</label>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="settings-select"
                  >
                    <option value="en">English (Official)</option>
                    <option value="te">Telugu (తెలుగు)</option>
                    <option value="hi">Hindi (हिन्दी)</option>
                    <option value="ta">Tamil (தமிழ்)</option>
                  </select>
                </div>

                <div className="form-field">
                  <label>Navigation & Measurement System</label>
                  <select
                    value={unitSystem}
                    onChange={(e) => setUnitSystem(e.target.value as any)}
                    className="settings-select"
                  >
                    <option value="nautical">Nautical Units (Knots, Nautical Miles, Meters depth)</option>
                    <option value="metric">Standard Metric (km/h, Kilometers, Meters)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Emergency Broadcast Channels */}
            <div className="settings-section">
              <span className="settings-section-title">3. Safety & Warning Dispatch Channels</span>
              <div className="settings-checkboxes-list">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={smsAlerts}
                    onChange={(e) => setSmsAlerts(e.target.checked)}
                  />
                  <span>Direct SMS Distress Broadcast to Coastal Fishermen (NAVTEX & Cell-Broadcast)</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={vhfRelay}
                    onChange={(e) => setVhfRelay(e.target.checked)}
                  />
                  <span>Automated VHF Channel 16 synthesized voice relay on severe weather triggers</span>
                </label>
              </div>
            </div>

            {/* Save Button */}
            <div className="settings-actions-row">
              <button type="submit" className="btn-save-settings">
                Save Platform Preferences
              </button>
              {saveSuccess && (
                <span className="save-success-tag">✓ Preferences updated successfully.</span>
              )}
            </div>
          </form>
        </div>

        {/* Backend & Connectivity Status Card */}
        <div className="ocean-card system-diag-card">
          <div className="card-top-header">
            <h3>System Diagnostics & Service Endpoints</h3>
            <span className="badge-provenance">Active Cluster</span>
          </div>

          <div className="diag-item-list">
            <div className="diag-item">
              <div className="diag-main">
                <strong>FastAPI Core Orchestrator</strong>
                <span>http://127.0.0.1:8000 (28 Active Endpoints)</span>
              </div>
              <span className="badge-diag-green">HEALTHY</span>
            </div>

            <div className="diag-item">
              <div className="diag-main">
                <strong>PostGIS Vector Engine</strong>
                <span>EPSG:4326 Maritime Limits & Polygons</span>
              </div>
              <span className="badge-diag-green">ONLINE</span>
            </div>

            <div className="diag-item">
              <div className="diag-main">
                <strong>Copernicus CMEMS Telemetry Ingest</strong>
                <span>Sentinel-3 OLCI/SLSTR Radiometric Pipeline</span>
              </div>
              <span className="badge-diag-green">SYNCED</span>
            </div>

            <div className="diag-item">
              <div className="diag-main">
                <strong>INCOIS & IMD Early Warning Sync</strong>
                <span>High Wave & Cyclone Doppler Stream</span>
              </div>
              <span className="badge-diag-green">LIVE</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
