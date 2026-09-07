import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import './DisasterSafetyPage.css';

interface SafetyAlertItem {
  id: string;
  severity: 'WARNING' | 'ALERT' | 'ADVISORY';
  title: string;
  agency: string;
  issuedTime: string;
  validUntil: string;
  affectedArea: string;
  parameters: string;
  actionRequired: string;
}

export const DisasterSafetyPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedLocation } = useLocationContext();
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'WARNING' | 'ALERT' | 'ADVISORY'>('ALL');

  const alerts: SafetyAlertItem[] = [
    {
      id: 'alert-1',
      severity: 'WARNING',
      title: 'Deep Depression / Cyclonic Vortex Warning (Track BD-04)',
      agency: 'IMD Cyclone Warning Division (New Delhi)',
      issuedTime: 'Today 14:00 IST',
      validUntil: 'Next 48 Hours',
      affectedArea: 'West-Central Bay of Bengal off Andhra Pradesh & South Odisha coasts',
      parameters: 'Sustained Winds: 45 - 55 kmph gusting to 65 kmph • Wave Height: 2.8 - 3.8m',
      actionRequired: 'Fishermen are strongly advised NOT to venture into deep sea. Vessels in deep waters advised to return to coast immediately.',
    },
    {
      id: 'alert-2',
      severity: 'ALERT',
      title: 'High Wave / Swell Surge Alert (Kallakkadal Warning)',
      agency: 'INCOIS Marine Early Warning Centre (Hyderabad)',
      issuedTime: 'Today 11:30 IST',
      validUntil: 'Tomorrow 23:30 IST',
      affectedArea: 'Low-lying coastal stretches of Visakhapatnam, Bheemunipatnam, and Kakinada',
      parameters: 'Swell Waves: 1.8 - 2.4m • Period: 14 - 17 seconds (Long Period Swell)',
      actionRequired: 'Small motorized craft and country boats must remain moored. Coastal operations to maintain vigilance during high tide periods.',
    },
    {
      id: 'alert-3',
      severity: 'ADVISORY',
      title: 'Squally Wind & Reduced Fairway Visibility Advisory',
      agency: 'Visakhapatnam Port Authority & IMD Port Meteorological Office',
      issuedTime: 'Today 08:00 IST',
      validUntil: 'Tonight 20:00 IST',
      affectedArea: 'Port approach channel and inner anchorage basin (0 - 5 NM)',
      parameters: 'Wind: ESE 18-22 knots • Visibility: 4-6 km in intermittent rain squalls',
      actionRequired: 'Pilots and tug operations exercise radar caution. Navigational lights mandatory.',
    },
  ];

  const filteredAlerts = activeFilter === 'ALL'
    ? alerts
    : alerts.filter(a => a.severity === activeFilter);

  const handleQuerySafetyAgent = () => {
    navigate('/ask-oceanis', {
      state: { initialQuery: `Provide emergency safety assessment, cyclone track proximity, and closest safe refuge port for ${selectedLocation.name} sector.` },
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
            <span className="page-breadcrumb-current">Disaster & Safety</span>
          </div>
          <h1 className="page-title">
            Disaster & Marine Safety Intelligence Command Center
            <span className="page-title-badge badge-official">Official Warnings</span>
          </h1>
          <p className="page-subtitle">
            Synchronized emergency marine warnings from IMD Cyclone Division, INCOIS Early Warning Centre, and Indian Coast Guard Maritime Rescue Coordination Centre (MRCC).
          </p>
        </div>
        <div className="page-header-actions">
          <button
            type="button"
            className="btn-page-action primary"
            onClick={handleQuerySafetyAgent}
          >
            <span>Ask Safety Agent</span>
          </button>
        </div>
      </header>

      {/* Emergency Distress & Helpline Bar */}
      <div className="emergency-hotline-bar">
        <div className="hotline-item">
          <span className="hotline-icon">🚨</span>
          <div className="hotline-info">
            <span className="hotline-label">Indian Coast Guard SAR Helpline</span>
            <strong className="hotline-num">Toll-Free 1554 / VHF Ch 16</strong>
          </div>
        </div>
        <div className="hotline-item">
          <span className="hotline-icon">📡</span>
          <div className="hotline-info">
            <span className="hotline-label">MRCC Chennai Distress Relay</span>
            <strong className="hotline-num">+91-44-2346-0405</strong>
          </div>
        </div>
        <div className="hotline-item">
          <span className="hotline-icon">⚓</span>
          <div className="hotline-info">
            <span className="hotline-label">VPT Port Emergency Control</span>
            <strong className="hotline-num">+91-891-287-3100</strong>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="safety-layout-grid">
        {/* Left Column: Official Warnings List with Filter */}
        <div className="safety-left-col">
          <div className="ocean-card alerts-feed-card">
            <div className="alerts-card-top">
              <h3>Active Marine Bulletins & Warnings</h3>
              <div className="severity-filters">
                <button
                  type="button"
                  className={`sev-filter-btn ${activeFilter === 'ALL' ? 'active' : ''}`}
                  onClick={() => setActiveFilter('ALL')}
                >
                  All ({alerts.length})
                </button>
                <button
                  type="button"
                  className={`sev-filter-btn btn-sev-warning ${activeFilter === 'WARNING' ? 'active' : ''}`}
                  onClick={() => setActiveFilter('WARNING')}
                >
                  Warning (1)
                </button>
                <button
                  type="button"
                  className={`sev-filter-btn btn-sev-alert ${activeFilter === 'ALERT' ? 'active' : ''}`}
                  onClick={() => setActiveFilter('ALERT')}
                >
                  Alert (1)
                </button>
                <button
                  type="button"
                  className={`sev-filter-btn btn-sev-advisory ${activeFilter === 'ADVISORY' ? 'active' : ''}`}
                  onClick={() => setActiveFilter('ADVISORY')}
                >
                  Advisory (1)
                </button>
              </div>
            </div>

            <div className="alerts-bulletin-list">
              {filteredAlerts.map((alert) => (
                <div key={alert.id} className={`safety-bulletin-card sev-${alert.severity.toLowerCase()}`}>
                  <div className="bulletin-header">
                    <span className={`bulletin-badge badge-${alert.severity.toLowerCase()}`}>
                      {alert.severity}
                    </span>
                    <span className="bulletin-agency">{alert.agency}</span>
                  </div>
                  <h4 className="bulletin-title">{alert.title}</h4>
                  <div className="bulletin-meta-row">
                    <span>Issued: <strong>{alert.issuedTime}</strong></span>
                    <span>Valid: <strong>{alert.validUntil}</strong></span>
                  </div>
                  <div className="bulletin-affected">
                    <span>Target Zone:</span> <strong>{alert.affectedArea}</strong>
                  </div>
                  <div className="bulletin-params">
                    <span>Hydrodynamics:</span> <strong>{alert.parameters}</strong>
                  </div>
                  <div className="bulletin-action-box">
                    <strong>Mandatory Operator Action:</strong>
                    <p>{alert.actionRequired}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Coastal Safety Protocol & Cyclone Track Overview */}
        <div className="safety-right-col">
          {/* Cyclone Track Status */}
          <div className="ocean-card cyclone-track-card">
            <div className="card-top-header">
              <h3>Vortex Track & Storm Surge Buffer</h3>
              <span className="badge-provenance">IMD Radar Model</span>
            </div>
            <div className="cyclone-telemetry-box">
              <div className="cyc-stat-row">
                <span>Current Vortex Center:</span>
                <strong>15.2° N, 84.8° E (180 NM SE of Vizag)</strong>
              </div>
              <div className="cyc-stat-row">
                <span>Estimated Central Pressure:</span>
                <strong>998 hPa (Depression)</strong>
              </div>
              <div className="cyc-stat-row">
                <span>Track Direction & Speed:</span>
                <strong>NNW at 14 km/h</strong>
              </div>
              <div className="cyc-stat-row">
                <span>Peak Storm Surge Forecast:</span>
                <strong>+0.6m above astronomical tide</strong>
              </div>
            </div>
            <div className="cyclone-guidance">
              <span className="guidance-icon">🛡️</span>
              <p>
                The predicted track maintains a safe distance of &gt;110 NM from the coast for the next 24 hours. Coastal ports remain on Port Warning Signal 3 (Local Cautionary).
              </p>
            </div>
          </div>

          {/* Fishermen Return-to-Shore Checklist */}
          <div className="ocean-card safety-checklist-card">
            <div className="card-top-header">
              <h3>Emergency Evacuation & Vessel Protocol</h3>
              <span className="badge-source">SOP Guidelines</span>
            </div>
            <div className="sop-checklist">
              <div className="sop-item checked">
                <span className="sop-check">✓</span>
                <div className="sop-text">
                  <strong>VHF Channel 16 Dual Watch</strong>
                  <p>Maintain continuous radio listen-in on marine distress frequency.</p>
                </div>
              </div>
              <div className="sop-item checked">
                <span className="sop-check">✓</span>
                <div className="sop-text">
                  <strong>Safe Port Distance Verification</strong>
                  <p>Confirm closest port haven distance is within 2 hours cruising time.</p>
                </div>
              </div>
              <div className="sop-item">
                <span className="sop-check">○</span>
                <div className="sop-text">
                  <strong>Secure Gear & Deck Cargo</strong>
                  <p>Lash trawl nets, outriggers, and anchor gear prior to rough sea entry.</p>
                </div>
              </div>
              <div className="sop-item">
                <span className="sop-check">○</span>
                <div className="sop-text">
                  <strong>AIS / DAT Emergency Beacon Readiness</strong>
                  <p>Ensure Distress Alert Transmitter (DAT) battery indicator is green.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DisasterSafetyPage;
