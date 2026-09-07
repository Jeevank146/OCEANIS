import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { DecisionIntelligence } from '../../components/DecisionIntelligence/DecisionIntelligence';
import './DecisionIntelligencePage.css';

export const DecisionIntelligencePage: React.FC = () => {
  const [selectedAuditRule, setSelectedAuditRule] = useState<string>('rule-1');

  const auditRules = [
    {
      id: 'rule-1',
      title: 'Safety-First Conflict Resolution Override',
      scenario: 'Fishing Agent suggests HIGH (Score: 92%) while Disaster Agent reports SWELL SURGE (Wave > 2.0m)',
      resolution: 'CRITICAL OVERRIDE ACTIVATED',
      decision: 'PROHIBITED / CAUTION',
      rationale: 'Safety guardrails take strict precedence over economic biomass yield. Under rule SAF-01, wave heights exceeding 1.8m mandate immediate advisory downgrade regardless of chlorophyll density.',
    },
    {
      id: 'rule-2',
      title: 'Sensor Data Freshness Degradation Penalty',
      scenario: 'Satellite pass is >24 hours old with 45% cloud occlusion',
      resolution: 'CONFIDENCE DOWNGRADED',
      decision: 'CONFIDENCE: MEDIUM (0.68)',
      rationale: 'Telemetry aging past 18 hours triggers automatic confidence dampening. Physical buoy observations are assigned higher weighting than stale optical rasters.',
    },
    {
      id: 'rule-3',
      title: 'Naval Restriction Corridors & Boundary Encroachment',
      scenario: 'High PFZ waypoint falls inside Active Naval Exercise Corridor (ENC-NAV-04)',
      resolution: 'WAYPOINT DISQUALIFICATION',
      decision: 'RESTRICTED SECTOR',
      rationale: 'PostGIS spatial boundary engine automatically flags illegal/hazardous entry. Spatial polygon intersection rejects the waypoint and reroutes to the nearest lawful alternative.',
    },
  ];

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Decision Intelligence</span>
          </div>
          <h1 className="page-title">
            6-Stage Decision Intelligence Pipeline & Provenance Audit
            <span className="page-title-badge badge-official">Deterministic Engine</span>
          </h1>
          <p className="page-subtitle">
            Formal multi-agent consensus architecture ensuring deterministic safety guardrails, verifiable source citations, and zero black-box hallucination.
          </p>
        </div>
        <div className="page-header-actions">
          <Link to="/what-if" className="btn-page-action secondary">
            <span>Simulate What-If</span>
          </Link>
          <Link to="/ask-oceanis" className="btn-page-action primary">
            <span>Query Orchestrator</span>
          </Link>
        </div>
      </header>

      {/* Embedded 6-Stage Visual Architecture Component */}
      <div className="decision-pipeline-wrapper">
        <DecisionIntelligence />
      </div>

      {/* Conflict Resolution & Deterministic Guardrail Matrix */}
      <div className="ocean-card audit-matrix-card">
        <div className="card-top-header">
          <h3>Deterministic Conflict Resolution & Safety Rules</h3>
          <span className="badge-provenance">Formal Governance</span>
        </div>
        <p className="card-desc">
          Inspect how contradictory agent telemetry (e.g., high economic catch potential vs hostile wave state) is deterministically resolved.
        </p>

        <div className="audit-rules-grid">
          {auditRules.map((rule) => (
            <div
              key={rule.id}
              className={`audit-rule-box ${selectedAuditRule === rule.id ? 'active' : ''}`}
              onClick={() => setSelectedAuditRule(rule.id)}
            >
              <div className="rule-header">
                <strong>{rule.title}</strong>
                <span className="rule-badge">{rule.resolution}</span>
              </div>
              <p className="rule-scenario"><strong>Scenario:</strong> {rule.scenario}</p>
              <div className="rule-outcome">
                <span className="outcome-label">Enforced Decision:</span>
                <span className="outcome-val">{rule.decision}</span>
              </div>
              <p className="rule-rationale">{rule.rationale}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DecisionIntelligencePage;
