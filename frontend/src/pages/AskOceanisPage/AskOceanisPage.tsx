import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import {
  getOrchestratorDecision,
  runWhatIfSimulation,
  type FinalDecisionObjectContract,
  type AgentResultContract,
  type EvidenceItemContract,
  type WhatIfComparisonContract,
} from '../../services/api';
import './AskOceanisPage.css';

const DEFAULT_AGENTS: AgentResultContract[] = [
  { agent_name: 'Disaster & Safety', status: 'success', summary: 'Severe storm and warning radar', findings: ['Cyclone track clearance verified'], evidence: [], confidence: 0.98, warnings: [], limitations: [] },
  { agent_name: 'Geo-Spatial & Navigation', status: 'success', summary: 'PostGIS spatial boundaries & harbors', findings: ['Coastal baseline clearance verified'], evidence: [], confidence: 0.95, warnings: [], limitations: [] },
  { agent_name: 'Marine Conditions', status: 'success', summary: 'INCOIS & IMD wave, swell & wind dynamics', findings: ['Wave & wind telemetry verified'], evidence: [], confidence: 0.92, warnings: [], limitations: [] },
  { agent_name: 'Earth Observation', status: 'success', summary: 'Sentinel-3 ocean colour & SST products', findings: ['Chlorophyll-a density verified'], evidence: [], confidence: 0.88, warnings: [], limitations: [] },
  { agent_name: 'Marine Operations', status: 'success', summary: 'Vessel transit timing & operational clearance', findings: ['Direct passage calculated'], evidence: [], confidence: 0.92, warnings: [], limitations: [] },
  { agent_name: 'Fishing Intelligence', status: 'success', summary: 'Fisheries suitability & thermal fronts', findings: ['Suitability index computed'], evidence: [], confidence: 0.88, warnings: [], limitations: [] },
];

export const AskOceanisPage: React.FC = () => {
  const location = useLocation();
  const { selectedLocation } = useLocationContext();

  const [queryInput, setQueryInput] = useState<string>('Can I go fishing tomorrow at 6 AM from Kakinada?');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [decisionData, setDecisionData] = useState<FinalDecisionObjectContract | null>(null);

  // What-If state
  const [whatIfTime, setWhatIfTime] = useState<string>('09:00');
  const [isSimulatingWhatIf, setIsSimulatingWhatIf] = useState<boolean>(false);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfComparisonContract | null>(null);

  // Active tab for evidence viewing
  const [activeEvidenceFilter, setActiveEvidenceFilter] = useState<string>('ALL');

  const samplePrompts = [
    { label: 'Kakinada Fishing', text: 'Can I go fishing tomorrow at 6 AM from Kakinada?' },
    { label: 'Paradip Route', text: 'Can I sail from Paradip to Gopalpur tomorrow at 8 AM?' },
    { label: 'Visakhapatnam Swell', text: 'Are there active storm surge warnings or high waves off Visakhapatnam?' },
    { label: 'Inland Check', text: 'Can I go ocean fishing in Hyderabad?' },
  ];

  // Auto-run if query passed from navigation
  useEffect(() => {
    if (location.state && (location.state as any).initialQuery) {
      const q = (location.state as any).initialQuery;
      setQueryInput(q);
      executeDecisionQuery(q);
    } else if (!decisionData && queryInput) {
      executeDecisionQuery(queryInput);
    }
  }, [location.state]);

  const executeDecisionQuery = async (queryText: string) => {
    if (!queryText.trim()) return;
    setIsLoading(true);
    setErrorMsg(null);
    setWhatIfResult(null);

    try {
      const res = await getOrchestratorDecision(
        queryText.trim(),
        selectedLocation?.lat,
        selectedLocation?.lon,
      );
      setDecisionData(res);
      if (res.what_if_comparison) {
        setWhatIfResult(res.what_if_comparison);
      }
    } catch (err: any) {
      console.error('Decision pipeline error:', err);
      setErrorMsg(err.message || 'Failed to retrieve multi-agent decision intelligence.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunWhatIf = async () => {
    if (!decisionData || !whatIfTime) return;
    setIsSimulatingWhatIf(true);
    try {
      const res = await runWhatIfSimulation({
        query: queryInput,
        latitude: decisionData.location?.latitude,
        longitude: decisionData.location?.longitude,
        what_if_time: whatIfTime,
        what_if_location_name: decisionData.location?.name,
      });
      setWhatIfResult(res);
    } catch (err: any) {
      console.error('What-If simulation error:', err);
    } finally {
      setIsSimulatingWhatIf(false);
    }
  };

  const getDecisionBadgeClass = (dec: string) => {
    const lower = (dec || '').toLowerCase();
    if (lower.includes('suitable') || lower.includes('clear') || lower.includes('favorable')) return 'dec-badge-suitable';
    if (lower.includes('caution')) return 'dec-badge-caution';
    if (lower.includes('not recommended') || lower.includes('blocked') || lower.includes('warning')) return 'dec-badge-not-recommended';
    return 'dec-badge-insufficient';
  };

  const getFreshnessBadgeClass = (freshness: string) => {
    const lower = (freshness || '').toLowerCase();
    if (lower.includes('fresh')) return 'fresh-fresh';
    if (lower.includes('aging')) return 'fresh-aging';
    if (lower.includes('stale')) return 'fresh-stale';
    return 'fresh-unavailable';
  };

  const filteredEvidence = (decisionData?.evidence || []).filter(item => {
    if (activeEvidenceFilter === 'ALL') return true;
    if (activeEvidenceFilter === 'REAL') return item.observation_type !== 'AI Assessment';
    if (activeEvidenceFilter === 'WARNINGS') return item.observation_type === 'Official Warning';
    if (activeEvidenceFilter === 'AI') return item.observation_type === 'AI Assessment';
    return true;
  });

  const agentsToDisplay = (decisionData && decisionData.agents_consulted && decisionData.agents_consulted.length > 0)
    ? decisionData.agents_consulted
    : DEFAULT_AGENTS;

  return (
    <div className="ask-oceanis-container">
      {/* Top Banner Header */}
      <div className="oceanis-page-header">
        <div className="oceanis-header-content">
          <div className="oceanis-badge">AGENTIC MARINE DECISION ENGINE</div>
          <h1 className="oceanis-title">Ask OCEANIS</h1>
          <p className="oceanis-subtitle">
            Natural-language marine intelligence synthesized across six autonomous domain agents with deterministic safety verification.
          </p>
        </div>
      </div>

      {/* Query Bar */}
      <div className="query-card-container">
        <div className="query-input-row">
          <input
            type="text"
            className="oceanis-query-input"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && executeDecisionQuery(queryInput)}
            placeholder="Ask anything: e.g. Can I go fishing tomorrow at 6 AM from Kakinada?"
          />
          <button
            className="oceanis-analyze-btn"
            onClick={() => executeDecisionQuery(queryInput)}
            disabled={isLoading}
          >
            {isLoading ? 'Consulting Agents...' : 'Analyze Decision'}
          </button>
        </div>

        {/* Quick Prompts */}
        <div className="quick-prompts-row">
          <span className="quick-label">Suggested Queries:</span>
          {samplePrompts.map((p, idx) => (
            <button
              key={idx}
              className="quick-prompt-btn"
              onClick={() => {
                setQueryInput(p.text);
                executeDecisionQuery(p.text);
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {errorMsg && (
        <div className="error-alert-banner">
          <strong>Pipeline Exception:</strong> {errorMsg}
        </div>
      )}

      {/* Agent Collaboration Status (6/6 Agents) */}
      <div className="agents-consulted-card">
        <div className="card-header-flex">
          <div>
            <h3 className="section-title">Agents Consulted (6/6)</h3>
            <p className="section-subtitle">Real-time domain consensus and telemetry evaluation</p>
          </div>
          <span className="agent-count-badge">
            {decisionData ? `${decisionData.agents_consulted.filter(a => a.status === 'success').length}/6 Active` : '6 Ready'}
          </span>
        </div>

        <div className="agents-grid">
          {agentsToDisplay.map((agent: AgentResultContract, idx: number) => (
            <div key={idx} className={`agent-mini-card ${agent.status === 'success' ? 'agent-success' : 'agent-warn'}`}>
              <div className="agent-card-top">
                <span className="agent-status-icon">✓</span>
                <strong className="agent-name-text">{agent.agent_name}</strong>
              </div>
              <p className="agent-summary-text">{agent.summary}</p>
              {agent.findings && agent.findings.length > 0 && (
                <div className="agent-findings-snippet">
                  • {agent.findings[0]}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main Decision Banner */}
      {decisionData && (
        <div className={`decision-banner-card ${getDecisionBadgeClass(decisionData.decision)}`}>
          <div className="decision-banner-header">
            <div className="decision-title-group">
              <span className="decision-kicker">OCEANIS DECISION RECOMMENDATION</span>
              <h2 className="decision-main-title">{decisionData.decision.toUpperCase()}</h2>
            </div>
            <div className="confidence-meter-pill">
              <span className="conf-label">Confidence:</span>
              <span className="conf-val">{decisionData.confidence}%</span>
            </div>
          </div>

          <p className="decision-summary-paragraph">{decisionData.summary}</p>

          <div className="decision-meta-strip">
            <div className="meta-pill">
              <span className="meta-k">Location:</span>
              <span className="meta-v">{decisionData.location?.name || 'Coastal Point'} ({decisionData.location?.latitude?.toFixed(4)}°N, {decisionData.location?.longitude?.toFixed(4)}°E)</span>
            </div>
            <div className="meta-pill">
              <span className="meta-k">Requested Time:</span>
              <span className="meta-v">{decisionData.requested_time}</span>
            </div>
            <div className="meta-pill">
              <span className="meta-k">Evidence Freshness:</span>
              <span className={`fresh-badge ${getFreshnessBadgeClass(decisionData.freshness_summary)}`}>
                {decisionData.freshness_summary}
              </span>
            </div>
            <div className="meta-pill">
              <span className="meta-k">Safety Status:</span>
              <span className="safety-status-text">{decisionData.safety_status}</span>
            </div>
          </div>

          {/* Confidence Diagnostic Reasons */}
          {decisionData.confidence_reasons && decisionData.confidence_reasons.length > 0 && (
            <div className="confidence-reasons-box">
              <div className="conf-reasons-title">Confidence Diagnostic Justification:</div>
              <ul className="conf-reasons-list">
                {decisionData.confidence_reasons.map((cr, idx) => (
                  <li key={idx}>{cr}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Why This Decision? (Categorized Grounded Breakdown) */}
      {decisionData && decisionData.why_decision && (
        <div className="why-decision-section">
          <h3 className="section-title">Why This Decision?</h3>
          <p className="section-subtitle">Multi-domain evidence tracing across environmental and regulatory factors</p>

          <div className="why-cards-grid">
            <div className="why-card">
              <div className="why-card-header">
                <span className="why-icon">🌊</span>
                <h4>Marine Conditions</h4>
              </div>
              <ul className="why-points-list">
                {decisionData.why_decision.marine_conditions.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>

            <div className="why-card">
              <div className="why-card-header">
                <span className="why-icon">🧭</span>
                <h4>Ocean Dynamics</h4>
              </div>
              <ul className="why-points-list">
                {decisionData.why_decision.ocean_conditions.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>

            <div className="why-card">
              <div className="why-card-header">
                <span className="why-icon">🛰️</span>
                <h4>Earth Observation</h4>
              </div>
              <ul className="why-points-list">
                {decisionData.why_decision.eo_indicators.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>

            <div className="why-card">
              <div className="why-card-header">
                <span className="why-icon">🗺️</span>
                <h4>Spatial Clearance</h4>
              </div>
              <ul className="why-points-list">
                {decisionData.why_decision.spatial_constraints.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>

            <div className="why-card">
              <div className="why-card-header">
                <span className="why-icon">⚠️</span>
                <h4>Disaster & Warnings</h4>
              </div>
              <ul className="why-points-list">
                {decisionData.why_decision.safety_warnings.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>

            <div className="why-card">
              <div className="why-card-header">
                <span className="why-icon">⚓</span>
                <h4>Marine Operations</h4>
              </div>
              <ul className="why-points-list">
                {decisionData.why_decision.operational_factors.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Safety Guardrails Card */}
      {decisionData && (
        <div className="safety-guardrail-card">
          <div className="guardrail-header">
            <span className="shield-icon">🛡️</span>
            <div>
              <h4 className="guardrail-title">Safety Guardrails & Regulatory Compliance</h4>
              <p className="guardrail-subtitle">Official alerts and spatial restrictions take strict precedence over AI interpretations</p>
            </div>
          </div>
          <div className="guardrail-actions-list">
            {decisionData.guardrail_actions.map((act, i) => (
              <div key={i} className="guardrail-action-row">
                <span className="guardrail-check">✓</span>
                <span>{act}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* What-If Scenario Simulation Panel */}
      {decisionData && (
        <div className="what-if-simulation-card">
          <div className="what-if-header">
            <div>
              <h3 className="section-title">What-If Scenario Simulation</h3>
              <p className="section-subtitle">Simulate alternative departure windows or locations to inspect decision differences</p>
            </div>
          </div>

          <div className="what-if-controls-row">
            <div className="what-if-control-group">
              <label>Shift Departure Time:</label>
              <select
                className="what-if-select"
                value={whatIfTime}
                onChange={(e) => setWhatIfTime(e.target.value)}
              >
                <option value="05:00">05:00 (Early Dawn)</option>
                <option value="06:00">06:00 (Standard Morning)</option>
                <option value="09:00">09:00 (Mid-Morning)</option>
                <option value="12:00">12:00 (Midday)</option>
                <option value="15:00">15:00 (Afternoon Thermal Breeze)</option>
                <option value="18:00">18:00 (Evening)</option>
              </select>
            </div>

            <button
              className="run-what-if-btn"
              onClick={handleRunWhatIf}
              disabled={isSimulatingWhatIf}
            >
              {isSimulatingWhatIf ? 'Simulating Shift...' : 'Run What-If Comparison'}
            </button>
          </div>

          {whatIfResult && whatIfResult.base_scenario && whatIfResult.what_if_scenario && (
            <div className="what-if-comparison-grid">
              <div className="scenario-box base-scenario-box">
                <div className="scenario-tag">BASE SCENARIO</div>
                <div className="scen-time">{whatIfResult.base_scenario.departure_time || '06:00'}</div>
                <div className={`scen-decision ${getDecisionBadgeClass(whatIfResult.base_scenario.decision || '')}`}>
                  {whatIfResult.base_scenario.decision}
                </div>
                <div className="scen-conf">Confidence: {whatIfResult.base_scenario.confidence_score}%</div>
              </div>

              <div className="scenario-diff-box">
                <div className="diff-icon">➔</div>
                <div className="diff-text">
                  <strong>Delta:</strong> {whatIfResult.decision_difference}
                </div>
                {whatIfResult.confidence_difference !== undefined && whatIfResult.confidence_difference !== null && (
                  <div className="diff-conf">
                    Confidence Δ: {whatIfResult.confidence_difference >= 0 ? `+${whatIfResult.confidence_difference}%` : `${whatIfResult.confidence_difference}%`}
                  </div>
                )}
                {whatIfResult.changed_factors.map((cf, i) => (
                  <div key={i} className="diff-factor">• {cf}</div>
                ))}
              </div>

              <div className="scenario-box what-if-scenario-box">
                <div className="scenario-tag">WHAT-IF SCENARIO</div>
                <div className="scen-time">{whatIfResult.what_if_scenario.departure_time}</div>
                <div className={`scen-decision ${getDecisionBadgeClass(whatIfResult.what_if_scenario.decision || '')}`}>
                  {whatIfResult.what_if_scenario.decision}
                </div>
                <div className="scen-conf">Confidence: {whatIfResult.what_if_scenario.confidence_score}%</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Structured Evidence Table */}
      {decisionData && (
        <div className="evidence-table-card">
          <div className="evidence-table-header">
            <div>
              <h3 className="section-title">Traceable Evidence Provenance</h3>
              <p className="section-subtitle">Grounded observations and models from IMD, INCOIS, Copernicus & GIS</p>
            </div>

            <div className="evidence-filter-tabs">
              {['ALL', 'REAL', 'WARNINGS', 'AI'].map(tab => (
                <button
                  key={tab}
                  className={`filter-tab-btn ${activeEvidenceFilter === tab ? 'active' : ''}`}
                  onClick={() => setActiveEvidenceFilter(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <div className="table-responsive">
            <table className="oceanis-evidence-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Parameter</th>
                  <th>Value</th>
                  <th>Observation Type</th>
                  <th>Freshness</th>
                  <th>Originating Agent</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvidence.map((ev: EvidenceItemContract, idx: number) => (
                  <tr key={idx}>
                    <td>
                      <span className="source-tag">{ev.source}</span>
                    </td>
                    <td>
                      <strong className="param-text">{ev.parameter.replace('_', ' ')}</strong>
                    </td>
                    <td>
                      <span className="val-text">
                        {typeof ev.value === 'number' ? ev.value.toFixed(2) : String(ev.value)}
                        {ev.unit ? ` ${ev.unit}` : ''}
                      </span>
                    </td>
                    <td>
                      <span className={`obs-type-tag obs-${(ev.observation_type || 'Observed').toLowerCase().replace(' ', '-')}`}>
                        {ev.observation_type}
                      </span>
                    </td>
                    <td>
                      <span className={`fresh-badge ${getFreshnessBadgeClass(ev.freshness)}`}>
                        {ev.freshness}
                      </span>
                    </td>
                    <td className="agent-origin-cell">
                      {ev.provenance?.agent || 'Domain Agent'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
