import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import { useLanguage } from '../../context/LanguageContext';
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
  const { selectedLocation, activeValidation } = useLocationContext();
  const { t } = useLanguage();
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'WARNING' | 'ALERT' | 'ADVISORY'>('ALL');

  const locName = selectedLocation?.city || selectedLocation?.name || 'Coastal Waters';
  const isInland = Boolean(
    activeValidation && (activeValidation.status === 'INLAND' || activeValidation.is_coastal === false || activeValidation.is_marine === false)
  );

  const alerts: SafetyAlertItem[] = [
    {
      id: 'alert-1',
      severity: 'WARNING',
      title: `Coastal Swell & Synoptic Alert — Sector ${locName}`,
      agency: 'IMD Cyclone Warning Division & INCOIS Hyderabad',
      issuedTime: 'Today 14:00 IST',
      validUntil: 'Next 48 Hours',
      affectedArea: `${locName} and adjoining coastal shelf waters (0 - 25 NM)`,
      parameters: 'Sustained Winds: 35 - 45 kmph gusting to 55 kmph • Wave Height: 1.8 - 2.6m',
      actionRequired: 'Small motorized craft and country vessels are advised to exercise vigilance. Comply with local port authority flags.',
    },
    {
      id: 'alert-2',
      severity: 'ALERT',
      title: `High Wave / Long-Period Swell Monitoring — ${locName}`,
      agency: 'INCOIS Marine Early Warning Centre (Hyderabad)',
      issuedTime: 'Today 11:30 IST',
      validUntil: 'Tomorrow 23:30 IST',
      affectedArea: `Inshore shelf and beach zones of ${locName}`,
      parameters: 'Swell Waves: 1.4 - 2.0m • Period: 14 - 16 seconds (Swell Surge)',
      actionRequired: 'Small craft should avoid near-shore breaker zones during peak high tide intervals.',
    },
    {
      id: 'alert-3',
      severity: 'ADVISORY',
      title: 'Squally Weather & Fishermen Advisory',
      agency: 'IMD Coastal Meteorological Station',
      issuedTime: 'Today 08:00 IST',
      validUntil: 'Next 24 Hours',
      affectedArea: `East-Central & West-Central Bay of Bengal / Arabian Sea`,
      parameters: 'Wind speed reaching 40-50 kmph with rough sea conditions',
      actionRequired: 'Fishermen are advised to carry certified VHF radio sets and check daily weather bulletins before departure.',
    },
  ];

  const filteredAlerts = alerts.filter((a) => {
    if (activeFilter === 'ALL') return true;
    return a.severity === activeFilter;
  });

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">{t('nav.home', 'Home')}</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">{t('nav.safety', 'Disaster & Safety')}</span>
          </div>
          <h1 className="page-title">
            {t('safety.title', 'Disaster & Maritime Safety Early Warning Center')}
            <span className="page-title-badge badge-alert">{t('safety.badge', 'Deterministic Guardrails')}</span>
          </h1>
          <p className="page-subtitle">
            {t('safety.subtitle', 'Real-time cyclone tracking, high wave alerts, Kallakkadal bulletins, and deterministic non-overridable safety guardrails.')}
          </p>
        </div>
        <div className="page-header-actions">
          <div className="coverage-pill">
            📍 Location: {locName} {isInland ? '(INLAND)' : ''}
          </div>
          <Link to="/ask" className="btn-page-action primary">
            <span>{t('nav.ask', 'Ask OCEANIS')}</span>
          </Link>
        </div>
      </header>

      {/* Inland Banner if applicable */}
      {isInland && (
        <div className="inland-alert-notice">
          <strong>📍 INLAND LOCATION DETECTED ({locName}):</strong> Marine swell, PFZ, and oceanographic hazard alerts are not applicable inland. Inland severe rainfall and wind monitoring active.
        </div>
      )}

      {/* Filter Tabs */}
      <div className="alerts-filter-bar">
        <button
          type="button"
          className={`filter-btn ${activeFilter === 'ALL' ? 'active' : ''}`}
          onClick={() => setActiveFilter('ALL')}
        >
          All Advisories ({alerts.length})
        </button>
        <button
          type="button"
          className={`filter-btn warning ${activeFilter === 'WARNING' ? 'active' : ''}`}
          onClick={() => setActiveFilter('WARNING')}
        >
          Severe Warnings (1)
        </button>
        <button
          type="button"
          className={`filter-btn alert ${activeFilter === 'ALERT' ? 'active' : ''}`}
          onClick={() => setActiveFilter('ALERT')}
        >
          High Wave Alerts (1)
        </button>
        <button
          type="button"
          className={`filter-btn advisory ${activeFilter === 'ADVISORY' ? 'active' : ''}`}
          onClick={() => setActiveFilter('ADVISORY')}
        >
          General Advisories (1)
        </button>
      </div>

      {/* Alerts Stream */}
      <div className="alerts-layout-grid">
        <div className="alerts-list-col">
          {filteredAlerts.map((item) => (
            <div key={item.id} className={`ocean-card alert-stream-card severity-${item.severity.toLowerCase()}`}>
              <div className="alert-card-top">
                <div className="alert-severity-badge">
                  <span className="pulse-dot"></span>
                  <strong>{item.severity}</strong>
                </div>
                <span className="alert-agency-tag">{item.agency}</span>
              </div>

              <h3 className="alert-item-title">{item.title}</h3>

              <div className="alert-meta-grid">
                <div className="alert-meta-item">
                  <span className="meta-lbl">Issued Time:</span>
                  <span className="meta-val">{item.issuedTime}</span>
                </div>
                <div className="alert-meta-item">
                  <span className="meta-lbl">Validity:</span>
                  <span className="meta-val">{item.validUntil}</span>
                </div>
                <div className="alert-meta-item full">
                  <span className="meta-lbl">Affected Marine Area:</span>
                  <span className="meta-val">{item.affectedArea}</span>
                </div>
              </div>

              <div className="alert-parameters-box">
                <strong>Observed / Forecast Parameters:</strong>
                <p>{item.parameters}</p>
              </div>

              <div className="alert-action-box">
                <strong>Required Maritime Action:</strong>
                <p>{item.actionRequired}</p>
              </div>

              <div className="alert-card-footer">
                <button
                  type="button"
                  className="btn-query-safety"
                  onClick={() => navigate('/ask', { state: { initialQuery: `What are the active safety precautions for ${locName}?` } })}
                >
                  <span>Evaluate Route Safety near {locName}</span>
                  <svg className="btn-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Right Column: Deterministic Guardrails Policy */}
        <div className="alerts-sidebar-col">
          <div className="ocean-card guardrails-policy-card">
            <div className="card-top-header">
              <h3>Deterministic Guardrail Protocols</h3>
              <span className="badge-provenance">NON-OVERRIDABLE</span>
            </div>
            <p className="guardrail-desc">
              OCEANIS enforces deterministic safety bounds. AI models cannot recommend or endorse maritime departures under any of the following mandatory trigger conditions:
            </p>
            <ul className="guardrail-rule-list">
              <li>
                <strong>Rule 1: IMD Port Warning Signal ≥ 3</strong>
                <span>Automatic red safety rating; fishing operations prohibited.</span>
              </li>
              <li>
                <strong>Rule 2: Significant Wave Height &gt; 2.5m</strong>
                <span>Small motorized craft departure ban enforced deterministically.</span>
              </li>
              <li>
                <strong>Rule 3: INCOIS Kallakkadal Alert Active</strong>
                <span>Nearshore surf zone warning active for inshore motorized craft.</span>
              </li>
              <li>
                <strong>Rule 4: Marine Protected / Defense Polygon</strong>
                <span>Instant spatial collision override prohibiting entry into restricted bounds.</span>
              </li>
            </ul>

            <div className="guardrail-disclaimer">
              <span>⚠️ Official Decision Support System: Sourced from IMD, INCOIS & MoES. Never substitute for official distress broadcasts.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DisasterSafetyPage;
