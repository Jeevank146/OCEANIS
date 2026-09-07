import React from 'react';
import './DecisionIntelligence.css';

interface DecisionStep {
  stepNum: string;
  title: string;
  subtitle: string;
  desc: string;
  badge: string;
}

const decisionSteps: DecisionStep[] = [
  { stepNum: '01', title: 'User Question', subtitle: 'Multilingual Ingestion', desc: 'Accepts natural coastal language in English, Telugu, Hindi, or Romanized transliterations with intent extraction.', badge: 'VOICE / TEXT' },
  { stepNum: '02', title: 'Domain Agents', subtitle: 'Dynamic Dispatch', desc: 'Central orchestrator routes operational parameters to relevant specialized domain agents.', badge: '6 DOMAINS' },
  { stepNum: '03', title: 'Marine Telemetry', subtitle: 'Physical Observations', desc: 'Collectors fetch live wave buoy metrics, IMD Doppler radars, and Sentinel-3 bio-optics.', badge: 'GROUND TRUTH' },
  { stepNum: '04', title: 'Evidence Fusion', subtitle: 'Provenance Synthesis', desc: 'Normalizes observation timestamps, spatial proximity vectors, and cross-agent telemetry correlation.', badge: 'DATA FUSION' },
  { stepNum: '05', title: 'Safety Analysis', subtitle: 'Deterministic Guardrails', desc: 'PostGIS spatial geofencing applies non-overridable safety rules for naval zones and cyclone buffers.', badge: 'SAFETY FIRST' },
  { stepNum: '06', title: 'Decision & Refuge', subtitle: 'Explainable Outcome', desc: 'Assigns CLEAR, CAUTION, WARNING, or BLOCKED status with designated nearest safe harbor refuge.', badge: 'DECISION' },
];

interface SampleEvidence {
  factor: string;
  value: string;
  source: string;
  timestamp: string;
  dataType: string;
  freshness: string;
  confidence: string;
  agent: string;
}

const sampleEvidenceItems: SampleEvidence[] = [
  {
    factor: 'Significant Wave Height',
    value: '1.8 m',
    source: 'INCOIS Coastal Buoy Network (Buoy-AP04)',
    timestamp: 'Today, 09:30 IST',
    dataType: 'OBSERVED',
    freshness: 'FRESH (12m ago)',
    confidence: 'HIGH (99.2%)',
    agent: 'Marine Conditions Agent',
  },
  {
    factor: 'Thermal SST Gradient',
    value: '28.4 °C (Front Stability: 0.88)',
    source: 'Copernicus Sentinel-3 SLSTR Radiometer',
    timestamp: 'Today, 06:40 UTC',
    dataType: 'SATELLITE_PASS',
    freshness: 'FRESH',
    confidence: 'HIGH (L2 Validated)',
    agent: 'Earth Observation Agent',
  },
  {
    factor: 'Naval Restriction Geofence',
    value: '0 Intersecting Polygons (Clear)',
    source: 'PostGIS 3.5 Maritime Boundary Engine',
    timestamp: 'Today, 10:00 IST',
    dataType: 'GEOFENCE_SPATIAL',
    freshness: 'REAL-TIME',
    confidence: 'DETERMINISTIC',
    agent: 'Geo-Spatial & Navigation Agent',
  },
  {
    factor: 'Tropical Cyclone Track',
    value: '0 Threat Vectors within 150 NM',
    source: 'IMD Cyclone Warning Division Advisory',
    timestamp: 'Today, 08:30 IST',
    dataType: 'OFFICIAL_ADVISORY',
    freshness: 'HOURLY SYNC',
    confidence: 'AUTHORITATIVE',
    agent: 'Disaster & Safety Agent',
  },
];

export const DecisionIntelligence: React.FC = () => {
  return (
    <section id="decision-intelligence" className="decision-intelligence-section">
      <div className="container">
        {/* Section Header */}
        <div className="decision-header">
          <div className="decision-title-block">
            <span className="section-tag">MULTI-AGENT EVIDENCE REASONING</span>
            <h2 className="decision-main-title">Decision Intelligence</h2>
            <p className="decision-subtitle">
              OCEANIS is not a generic chatbot. Every operational recommendation is produced through an audit-traceable pipeline grounded in ocean physics, remote sensing, and deterministic safety rules.
            </p>
          </div>

          <div className="decision-badge">
            <span className="live-dot pulse"></span>
            <span className="badge-text">EVIDENCE PROVENANCE ENGINE ACTIVE</span>
          </div>
        </div>

        {/* Pipeline Communication Flow Ribbon */}
        <div className="pipeline-flow-banner">
          <span className="flow-step-tag">QUESTION</span>
          <span className="flow-arrow">→</span>
          <span className="flow-step-tag">AGENTS</span>
          <span className="flow-arrow">→</span>
          <span className="flow-step-tag">DATA</span>
          <span className="flow-arrow">→</span>
          <span className="flow-step-tag">FUSION</span>
          <span className="flow-arrow">→</span>
          <span className="flow-step-tag">SAFETY</span>
          <span className="flow-arrow">→</span>
          <span className="flow-step-tag highlight">DECISION</span>
        </div>

        {/* 6-Stage Visual Flow */}
        <div className="decision-flow-grid">
          {decisionSteps.map((step, idx) => (
            <div key={step.stepNum} className="decision-step-card">
              <div className="step-card-top">
                <span className="step-badge">{step.badge}</span>
                <span className="step-num">{step.stepNum}</span>
              </div>
              <h3 className="step-title">{step.title}</h3>
              <h4 className="step-subtitle">{step.subtitle}</h4>
              <p className="step-desc">{step.desc}</p>
              {idx < decisionSteps.length - 1 && (
                <div className="step-connector">→</div>
              )}
            </div>
          ))}
        </div>

        {/* Traceable Evidence Cards Showcase */}
        <div className="evidence-showcase-container">
          <div className="evidence-showcase-header">
            <h3 className="showcase-title">Sample Evidence Provenance Cards</h3>
            <span className="showcase-tag">Direct Audit Trail from Selected Domain Agents</span>
          </div>

          <div className="evidence-cards-grid">
            {sampleEvidenceItems.map((ev, i) => (
              <div key={i} className="evidence-provenance-card">
                <div className="ev-top">
                  <span className="ev-factor">{ev.factor}</span>
                  <span className="ev-agent-pill">{ev.agent}</span>
                </div>

                <div className="ev-val-row">
                  <span className="ev-val">{ev.value}</span>
                </div>

                <div className="ev-specs-grid">
                  <div className="ev-spec">
                    <span className="ev-spec-lbl">Source Authority:</span>
                    <span className="ev-spec-val highlight">{ev.source}</span>
                  </div>
                  <div className="ev-spec">
                    <span className="ev-spec-lbl">Observation Time:</span>
                    <span className="ev-spec-val">{ev.timestamp}</span>
                  </div>
                  <div className="ev-spec">
                    <span className="ev-spec-lbl">Telemetry Quality:</span>
                    <span className="ev-spec-val">{ev.freshness} • {ev.confidence}</span>
                  </div>
                  <div className="ev-spec">
                    <span className="ev-spec-lbl">Data Classification:</span>
                    <span className="ev-spec-val">{ev.dataType}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
