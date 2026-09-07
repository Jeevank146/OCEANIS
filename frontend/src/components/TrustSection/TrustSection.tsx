import React from 'react';
import './TrustSection.css';

interface Pillar {
  number: string;
  title: string;
  subtitle: string;
  description: string;
  badge: string;
  icon: React.ReactNode;
}

const trustPillars: Pillar[] = [
  {
    number: '01',
    title: 'Real Marine Data',
    subtitle: 'Observation Over Speculation',
    description: 'Direct ingestion from INCOIS wave buoys, IMD coastal radars, and Copernicus Sentinel-3 Earth observation satellites. Zero fabricated metrics or synthetic hallucinations.',
    badge: 'INCOIS / IMD / COPERNICUS',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    ),
  },
  {
    number: '02',
    title: 'Evidence Provenance',
    subtitle: 'Traceable Auditability',
    description: 'Every recommendation cites observation timestamps, official data sources, validity windows, and originating domain agents. Complete transparency with zero black-box obscurity.',
    badge: 'SOURCE CITATION',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
  {
    number: '03',
    title: 'Confidence & Uncertainty',
    subtitle: 'Explicit Data Quality Metrics',
    description: 'Explicitly models telemetry freshness, sensor coverage gaps, and prediction uncertainty. If environmental data is stale or missing, the system outputs INSUFFICIENT_DATA rather than guessing.',
    badge: 'UNCERTAINTY AWARE',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    ),
  },
  {
    number: '04',
    title: 'Safety Guardrails',
    subtitle: 'Deterministic Life Safety First',
    description: 'If a naval exclusion zone is intersected or a severe cyclone surge is active, the system deterministically outputs BLOCKED. The conversational LLM cannot soften or override safety rules.',
    badge: 'NON-OVERRIDABLE RULES',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <polyline points="9 12 11 14 15 10" />
      </svg>
    ),
  },
  {
    number: '05',
    title: 'What-If Scenarios',
    subtitle: 'Operational Simulations',
    description: 'Evaluate scenario changes in departure time (e.g. "What if I leave at 9 AM?") or compare alternative fishing grounds side-by-side with multi-factor risk and suitability rankings.',
    badge: 'DYNAMIC SIMULATION',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 14 14" />
      </svg>
    ),
  },
  {
    number: '06',
    title: 'Multi-Agent Collaboration',
    subtitle: '6 Specialized Domain Experts',
    description: 'Each domain is governed by an independent agent with dedicated data collectors and reasoning engines. Evidence is dynamically fused by the Central Orchestrator into one clear decision.',
    badge: 'MODULAR AGENTS',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="18" cy="5" r="3" />
        <circle cx="6" cy="12" r="3" />
        <circle cx="18" cy="19" r="3" />
        <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
        <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
      </svg>
    ),
  },
];

export const TrustSection: React.FC = () => {
  return (
    <section id="trust" className="trust-section">
      <div className="container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-tag">ENGINEERED FOR MARITIME RELIABILITY</span>
          <h2 className="section-title">Built on Evidence. Governed by Safety.</h2>
          <p className="section-subtitle">
            OCEANIS combines orbital remote sensing, physical oceanography, PostGIS spatial computation, and deterministic safety rules to deliver explainable decisions for coastal communities.
          </p>
        </div>

        {/* 6 Trust Pillars Grid */}
        <div className="trust-grid">
          {trustPillars.map((pillar) => (
            <div key={pillar.number} className="trust-card glass-panel">
              <div className="trust-card-top">
                <div className="trust-icon-box">{pillar.icon}</div>
                <span className="trust-badge">{pillar.badge}</span>
              </div>
              <div className="trust-card-body">
                <span className="trust-number">{pillar.number}</span>
                <h3 className="trust-title">{pillar.title}</h3>
                <h4 className="trust-subtitle">{pillar.subtitle}</h4>
                <p className="trust-desc">{pillar.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
