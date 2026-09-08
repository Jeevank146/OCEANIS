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
    { label: '🎣 Kakinada Fishing (Decision)', text: 'Can I go fishing tomorrow at 6 AM from Kakinada?' },
    { label: '🌊 Chennai Conditions (Info)', text: 'What are the ocean conditions near Chennai tomorrow?' },
    { label: '⚠️ Visakhapatnam Cyclone (Safety)', text: 'Is there any cyclone warning near Visakhapatnam?' },
    { label: '🛰️ Paradip SST & Chl (Remote Sensing)', text: 'Show SST and chlorophyll near Paradip' },
    { label: '⚖️ Port Comparison (Compare)', text: 'Which is better for fishing, Kakinada or Visakhapatnam?' },
    { label: '⏰ 9 AM Shift (What-If)', text: 'What if I leave at 9 AM instead?' },
    { label: '🛡️ Marine Protected Zone (Spatial)', text: 'Is this location inside a protected marine zone?' },
    { label: '🧭 Paradip Route (Transit)', text: 'Find a safer route from Kakinada to Visakhapatnam' },
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

  const getIntentBadgeClass = (intent?: string) => {
    switch (intent) {
      case 'DECISION': return 'intent-decision';
      case 'INFORMATION': return 'intent-info';
      case 'SAFETY': return 'intent-safety';
      case 'COMPARISON': return 'intent-compare';
      case 'WHAT_IF': return 'intent-whatif';
      case 'ROUTE': return 'intent-route';
      default: return 'intent-general';
    }
  };

  const getDecisionBadgeClass = (dec: string) => {
    const lower = (dec || '').toLowerCase();
    if (lower.includes('suitable') || lower.includes('clear') || lower.includes('favorable')) return 'dec-badge-suitable';
    if (lower.includes('caution')) return 'dec-badge-caution';
    if (lower.includes('not recommended') || lower.includes('blocked') || lower.includes('warning')) return 'dec-badge-not-recommended';
    if (lower.includes('information')) return 'dec-badge-info';
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

  const queryIntent = decisionData?.query_intent || 'DECISION';
  const isDecisionQuery = queryIntent === 'DECISION';
  const isComparisonQuery = queryIntent === 'COMPARISON' && decisionData?.comparison_data;

  const agentsCount = decisionData?.agents_consulted?.length || 0;
  const totalAgents = decisionData?.total_agents_available || 6;

  return (
    <div className="ask-oceanis-container">
      {/* Top Banner Header */}
      <div className="oceanis-page-header">
        <div className="oceanis-header-content">
          <div className="oceanis-badge">AGENTIC MARINE DECISION INTELLIGENCE</div>
          <h1 className="oceanis-title">Ask OCEANIS</h1>
          <p className="oceanis-subtitle">
            Natural-language marine intelligence synthesized across specialized domain agents with deterministic safety verification.
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
            placeholder="Ask any natural language marine question: e.g. What are the ocean conditions near Chennai tomorrow?"
          />
          <button
            className="oceanis-analyze-btn"
            onClick={() => executeDecisionQuery(queryInput)}
            disabled={isLoading}
          >
            {isLoading ? 'Consulting Agents...' : 'Analyze Query'}
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

      {/* Answer / Primary Response Hero Card */}
      {decisionData && (
        <div className="primary-answer-card">
          <div className="answer-header-row">
            <div className="answer-intent-tag-group">
              <span className={`intent-badge ${getIntentBadgeClass(queryIntent)}`}>
                {queryIntent} QUERY
              </span>
              {decisionData.location && (
                <span className="location-tag">
                  📍 {decisionData.location.name || 'Coastal Point'}
                  {decisionData.location.latitude && decisionData.location.longitude && (
                    <small> ({decisionData.location.latitude.toFixed(4)}°N, {decisionData.location.longitude.toFixed(4)}°E)</small>
                  )}
                </span>
              )}
              {decisionData.requested_time && (
                <span className="time-tag">
                  🕒 {decisionData.requested_time}
                </span>
              )}
            </div>

            <div className="answer-freshness-pill">
              <span className={`fresh-badge ${getFreshnessBadgeClass(decisionData.freshness_summary)}`}>
                {decisionData.freshness_summary} Telemetry
              </span>
            </div>
          </div>

          <div className="answer-body-content">
            <h2 className="primary-answer-text">
              {decisionData.primary_answer || decisionData.summary}
            </h2>
          </div>
        </div>
      )}

      {/* Dynamically Selected Agents Consultation Grid */}
      {decisionData && decisionData.agents_consulted && decisionData.agents_consulted.length > 0 && (
        <div className="agents-consulted-card">
          <div className="card-header-flex">
            <div>
              <h3 className="section-title">Agents Consulted ({agentsCount}/{totalAgents})</h3>
              <p className="section-subtitle">
                Dynamically selected domain agents based on query intent and required marine telemetry
              </p>
            </div>
            <span className="agent-count-badge">
              {agentsCount} of {totalAgents} Active
            </span>
          </div>

          <div className="agents-grid">
            {decisionData.agents_consulted.map((agent: AgentResultContract, idx: number) => (
              <div key={idx} className={`agent-mini-card ${agent.status === 'success' ? 'agent-success' : 'agent-warn'}`}>
                <div className="agent-card-top">
                  <span className="agent-status-icon">{agent.status === 'success' ? '✓' : '⚠️'}</span>
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
      )}

      {/* ------------------------------------------------------------- */}
      {/* COMPARISON QUERY VIEW (Side-by-Side Target Locations) */}
      {/* ------------------------------------------------------------- */}
      {isComparisonQuery && decisionData?.comparison_data && (
        <div className="comparison-section-card">
          <div className="comparison-header">
            <span className="comparison-kicker">MULTI-LOCATION COMPARATIVE EVALUATION</span>
            <h3 className="comparison-title">
              Recommended: {decisionData.comparison_data.recommended_location}
            </h3>
            <p className="comparison-summary-text">{decisionData.comparison_data.comparison_summary}</p>
          </div>

          <div className="comparison-cards-grid">
            {decisionData.comparison_data.target_locations.map((loc, idx) => (
              <div
                key={idx}
                className={`comparison-loc-card ${loc.location_name === decisionData.comparison_data?.recommended_location ? 'loc-recommended' : ''}`}
              >
                <div className="loc-card-header">
                  <h4>{loc.location_name}</h4>
                  <span className={`dec-pill ${getDecisionBadgeClass(loc.decision || '')}`}>
                    {loc.decision} ({loc.confidence}%)
                  </span>
                </div>

                <div className="loc-metrics-grid">
                  {Object.entries(loc.key_metrics || {}).map(([k, v], i) => (
                    <div key={i} className="loc-metric-item">
                      <span className="metric-k">{k.replace('_', ' ').toUpperCase()}:</span>
                      <span className="metric-v">{String(v)}</span>
                    </div>
                  ))}
                </div>

                {loc.pros && loc.pros.length > 0 && (
                  <div className="loc-pros-box">
                    <strong>Favorable Factors:</strong>
                    <ul>
                      {loc.pros.map((p, i) => <li key={i}>{p}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* DECISION QUERY VIEW (Suitability Banner & Why Breakdown) */}
      {/* ------------------------------------------------------------- */}
      {isDecisionQuery && decisionData && (
        <>
          <div className={`decision-banner-card ${getDecisionBadgeClass(decisionData.decision)}`}>
            <div className="decision-banner-header">
              <div className="decision-title-group">
                <span className="decision-kicker">OPERATIONAL DECISION RECOMMENDATION</span>
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
                <span className="meta-v">{decisionData.location?.name || 'Coastal Point'}</span>
              </div>
              <div className="meta-pill">
                <span className="meta-k">Requested Time:</span>
                <span className="meta-v">{decisionData.requested_time}</span>
              </div>
              <div className="meta-pill">
                <span className="meta-k">Safety Status:</span>
                <span className="safety-status-text">{decisionData.safety_status}</span>
              </div>
            </div>

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

          {/* Why This Decision? (Categorized Grounded Breakdown) */}
          {decisionData.why_decision && (
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
                    <span className="why-icon">🌐</span>
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

          {/* What-If Scenario Simulation Panel */}
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
                {isSimulatingWhatIf ? 'Simulating Scenario...' : 'Run Simulation'}
              </button>
            </div>

            {whatIfResult && (
              <div className="what-if-comparison-results">
                <div className="what-if-result-pill">
                  <strong>Simulated Shift:</strong> {whatIfResult.changed_factors.join(', ') || 'Departure time modified'}
                </div>

                <div className="scenarios-comparison-grid">
                  <div className="scenario-card base-scenario">
                    <div className="scenario-label">Base Scenario</div>
                    <div className="scenario-time">Time: {whatIfResult.base_scenario?.departure_time || '06:00'}</div>
                    <div className="scenario-dec">
                      Decision: <strong>{whatIfResult.base_scenario?.decision}</strong> ({whatIfResult.base_scenario?.confidence_score}%)
                    </div>
                  </div>

                  <div className="scenario-card simulated-scenario">
                    <div className="scenario-label">What-If Simulated</div>
                    <div className="scenario-time">Time: {whatIfResult.what_if_scenario?.departure_time || whatIfTime}</div>
                    <div className="scenario-dec">
                      Decision: <strong>{whatIfResult.what_if_scenario?.decision}</strong> ({whatIfResult.what_if_scenario?.confidence_score}%)
                    </div>
                  </div>
                </div>

                {whatIfResult.decision_difference && (
                  <div className="what-if-delta-box">
                    <strong>Operational Delta:</strong> {whatIfResult.decision_difference}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}

      {/* ------------------------------------------------------------- */}
      {/* STRUCTURED EVIDENCE TABLE (All Queries with Data) */}
      {/* ------------------------------------------------------------- */}
      {decisionData && decisionData.evidence && decisionData.evidence.length > 0 && (
        <div className="evidence-table-section">
          <div className="evidence-header-row">
            <div>
              <h3 className="section-title">Structured Evidence & Source Provenance ({decisionData.evidence.length} Items)</h3>
              <p className="section-subtitle">Real telemetry strictly separated from AI analysis with dynamic freshness tracking</p>
            </div>

            <div className="evidence-filter-tabs">
              <button
                className={`ev-tab ${activeEvidenceFilter === 'ALL' ? 'active' : ''}`}
                onClick={() => setActiveEvidenceFilter('ALL')}
              >
                All ({decisionData.evidence.length})
              </button>
              <button
                className={`ev-tab ${activeEvidenceFilter === 'REAL' ? 'active' : ''}`}
                onClick={() => setActiveEvidenceFilter('REAL')}
              >
                Real Telemetry ({decisionData.evidence.filter(e => e.observation_type !== 'AI Assessment').length})
              </button>
              <button
                className={`ev-tab ${activeEvidenceFilter === 'WARNINGS' ? 'active' : ''}`}
                onClick={() => setActiveEvidenceFilter('WARNINGS')}
              >
                Official Warnings ({decisionData.evidence.filter(e => e.observation_type === 'Official Warning').length})
              </button>
              <button
                className={`ev-tab ${activeEvidenceFilter === 'AI' ? 'active' : ''}`}
                onClick={() => setActiveEvidenceFilter('AI')}
              >
                AI Assessments ({decisionData.evidence.filter(e => e.observation_type === 'AI Assessment').length})
              </button>
            </div>
          </div>

          <div className="evidence-table-wrapper">
            <table className="oceanis-evidence-table">
              <thead>
                <tr>
                  <th>Source Authority</th>
                  <th>Observed Parameter</th>
                  <th>Value</th>
                  <th>Type</th>
                  <th>Freshness</th>
                  <th>Observed Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvidence.map((item: EvidenceItemContract, idx: number) => (
                  <tr key={idx}>
                    <td>
                      <span className="source-authority-tag">{item.source}</span>
                    </td>
                    <td>
                      <strong className="param-name">{item.parameter.replace('_', ' ').toUpperCase()}</strong>
                    </td>
                    <td>
                      <span className="param-value">{String(item.value)} {item.unit || ''}</span>
                    </td>
                    <td>
                      <span className={`obs-type-badge obs-${item.observation_type.toLowerCase().replace(' ', '-')}`}>
                        {item.observation_type}
                      </span>
                    </td>
                    <td>
                      <span className={`fresh-badge ${getFreshnessBadgeClass(item.freshness)}`}>
                        {item.freshness}
                      </span>
                    </td>
                    <td className="timestamp-cell">
                      {item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Live Synced'}
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

export default AskOceanisPage;
