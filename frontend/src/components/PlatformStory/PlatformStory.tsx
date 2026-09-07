import React from 'react';
import './PlatformStory.css';

interface FlowStep {
  step: string;
  title: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const flowSteps: FlowStep[] = [
  {
    step: '01',
    title: 'User Question',
    label: 'Natural Language / Voice',
    description: 'Fishermen and coastal operators ask questions in English, Telugu, Hindi, or Romanized transliteration.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    step: '02',
    title: 'Agent Planning',
    label: 'Query Understanding',
    description: 'The Central Orchestrator parses operational intent, target harbor locations, coordinates, and departure timeframes.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
      </svg>
    ),
  },
  {
    step: '03',
    title: 'Domain Agents',
    label: 'Specialized Expertise',
    description: 'Dynamic dispatch to dedicated agents (Fishing, Marine Conditions, Earth Observation, Geospatial, Safety, Operations).',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    ),
  },
  {
    step: '04',
    title: 'Real Marine Data',
    label: 'Grounded Telemetry',
    description: 'Direct ingestion from INCOIS wave buoys, IMD coastal radars, Sentinel-3 satellite bio-optics, and PostGIS geofences.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 3v18M3 12h18" />
      </svg>
    ),
  },
  {
    step: '05',
    title: 'Evidence Fusion',
    label: 'Multi-Source Synthesis',
    description: 'Normalizes observation timestamps, unit scales, spatial proximity, and cross-agent telemetry correlation.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    ),
  },
  {
    step: '06',
    title: 'Safety Guardrails',
    label: 'Non-Overridable Rules',
    description: 'Deterministic rules check for naval exclusions, gale advisories, or cyclone paths. The LLM cannot soften safety rules.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
  {
    step: '07',
    title: 'Decision',
    label: 'Deterministic Status',
    description: 'Computes objective safety classification (CLEAR, CAUTION, WARNING, BLOCKED) and operational risk rankings.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    ),
  },
  {
    step: '08',
    title: 'Explainable Response',
    label: 'Clear Provenance',
    description: 'Delivers a transparent natural-language explanation citing exact observation sources, timestamps, and safe harbor refuges.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
];

export const PlatformStory: React.FC = () => {
  return (
    <section id="platform-story" className="platform-story-section">
      <div className="container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-tag">DECISION PIPELINE ARCHITECTURE</span>
          <h2 className="section-title">How OCEANIS Works</h2>
          <p className="section-subtitle">
            A transparent 8-stage decision pipeline that bridges coastal natural language with orbital Earth observation and deterministic maritime safety.
          </p>
        </div>

        {/* Visual Pipeline Pathway */}
        <div className="pipeline-grid">
          {flowSteps.map((step, idx) => (
            <div key={step.step} className="pipeline-card-wrapper">
              <div className="pipeline-card glass-panel">
                <div className="pipeline-card-top">
                  <div className="pipeline-icon-box">{step.icon}</div>
                  <span className="pipeline-step-number">{step.step}</span>
                </div>

                <div className="pipeline-card-body">
                  <h3 className="pipeline-step-title">{step.title}</h3>
                  <span className="pipeline-step-label">{step.label}</span>
                  <p className="pipeline-step-desc">{step.description}</p>
                </div>
              </div>

              {idx < flowSteps.length - 1 && (
                <div className="pipeline-connector-arrow">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
