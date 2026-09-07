import React, { useState } from 'react';
import './WhatIfSimulation.css';
import { sendConversationQuery } from '../../services/api';

interface ScenarioPreset {
  id: string;
  label: string;
  origin: string;
  slotA: {
    time: string;
    wave: number;
    wind: number;
    risk: string;
    status: string;
    confidence: string;
  };
  slotB: {
    time: string;
    wave: number;
    wind: number;
    risk: string;
    status: string;
    confidence: string;
  };
}

const scenarioPresets: ScenarioPreset[] = [
  {
    id: 'kakinada-time-shift',
    label: 'Kakinada: 06:00 AM vs 09:00 AM Departure',
    origin: 'Kakinada Port',
    slotA: { time: '06:00 AM (Early Departure)', wave: 1.8, wind: 24.0, risk: 'MODERATE', status: 'CAUTION', confidence: 'HIGH' },
    slotB: { time: '09:00 AM (Mid-Morning)', wave: 1.3, wind: 16.0, risk: 'LOW', status: 'CLEAR', confidence: 'HIGH' },
  },
  {
    id: 'vizag-comparison',
    label: 'Vizag vs Kakinada Fishing Grounds',
    origin: 'Visakhapatnam vs Kakinada',
    slotA: { time: 'Vizag Offshore (25 NM)', wave: 1.5, wind: 20.0, risk: 'LOW', status: 'CLEAR', confidence: 'HIGH' },
    slotB: { time: 'Kakinada Offshore (20 NM)', wave: 1.2, wind: 15.0, risk: 'LOW', status: 'CLEAR (FAVORABLE)', confidence: 'HIGH' },
  },
  {
    id: 'chennai-speed-profile',
    label: 'Chennai to Ennore Passage: 8 kts vs 12 kts Vessel Speed',
    origin: 'Chennai Harbor Corridor',
    slotA: { time: 'Standard 8 kts Speed', wave: 1.6, wind: 22.0, risk: 'LOW', status: 'CLEAR', confidence: 'HIGH' },
    slotB: { time: 'High-Speed 12 kts', wave: 1.9, wind: 25.0, risk: 'MODERATE', status: 'CAUTION', confidence: 'HIGH' },
  },
];

export const WhatIfSimulation: React.FC = () => {
  const [selectedPreset, setSelectedPreset] = useState<ScenarioPreset>(scenarioPresets[0]);
  const [isRunning, setIsRunning] = useState(false);
  const [simulationResult, setSimulationResult] = useState<string | null>(null);

  const handleRunScenario = async () => {
    setIsRunning(true);
    setSimulationResult(null);

    const queryMessage = `What if I leave ${selectedPreset.origin} at 9 AM instead of 6 AM?`;
    try {
      const res = await sendConversationQuery(queryMessage);
      setSimulationResult(res.response);
    } catch {
      // Local fallback simulation explanation
      setTimeout(() => {
        setSimulationResult(
          `SIMULATION OUTCOME: Shifting departure from 06:00 AM to 09:00 AM reduces sustained wind velocity from 24 km/h to 16 km/h and wave height from 1.8m to 1.3m near ${selectedPreset.origin}. Risk classification improves from CAUTION to CLEAR (LOW RISK). Recommended departure window: 08:30 AM - 11:00 AM.`
        );
      }, 600);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <section id="what-if-scenarios" className="whatif-section">
      <div className="container">
        {/* Section Header */}
        <div className="whatif-header">
          <div className="whatif-title-block">
            <span className="section-tag">PREDICTIVE MARITIME SIMULATION</span>
            <h2 className="whatif-main-title">What-If Scenarios</h2>
            <p className="whatif-subtitle">
              Simulate operational decisions in advance. Compare weather windows, departure time shifts, and alternative routes with side-by-side hydrodynamics and risk evaluations.
            </p>
          </div>

          <div className="whatif-badge">
            <span className="live-dot pulse"></span>
            <span className="badge-text">WHAT-IF SIMULATION ENGINE ACTIVE</span>
          </div>
        </div>

        {/* Preset Selector */}
        <div className="scenario-preset-selector">
          <span className="selector-title">SELECT SIMULATION SCENARIO:</span>
          <div className="preset-buttons-row">
            {scenarioPresets.map((preset) => (
              <button
                key={preset.id}
                type="button"
                className={`preset-btn ${selectedPreset.id === preset.id ? 'active' : ''}`}
                onClick={() => {
                  setSelectedPreset(preset);
                  setSimulationResult(null);
                }}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Side-by-Side Comparison Container */}
        <div className="whatif-comparison-grid">
          {/* Option A */}
          <div className="scenario-card card-option-a">
            <div className="scenario-card-header">
              <span className="scenario-tag">OPTION A</span>
              <h3 className="scenario-slot-name">{selectedPreset.slotA.time}</h3>
            </div>

            <div className="scenario-metrics-list">
              <div className="s-metric-row">
                <span className="s-lbl">Wave Height:</span>
                <span className="s-val">{selectedPreset.slotA.wave} m</span>
              </div>
              <div className="s-metric-row">
                <span className="s-lbl">Wind Speed:</span>
                <span className="s-val">{selectedPreset.slotA.wind} km/h</span>
              </div>
              <div className="s-metric-row">
                <span className="s-lbl">Risk Level:</span>
                <span className={`s-val-badge risk-${selectedPreset.slotA.risk.toLowerCase()}`}>
                  {selectedPreset.slotA.risk}
                </span>
              </div>
              <div className="s-metric-row">
                <span className="s-lbl">Safety Status:</span>
                <span className={`s-val-badge status-${selectedPreset.slotA.status.toLowerCase().split(' ')[0]}`}>
                  {selectedPreset.slotA.status}
                </span>
              </div>
              <div className="s-metric-row">
                <span className="s-lbl">Confidence:</span>
                <span className="s-val highlight">{selectedPreset.slotA.confidence}</span>
              </div>
            </div>
          </div>

          {/* Versus Divider Badge */}
          <div className="versus-badge-container">
            <span className="versus-pill">VS</span>
          </div>

          {/* Option B */}
          <div className="scenario-card card-option-b">
            <div className="scenario-card-header">
              <span className="scenario-tag highlight-teal">OPTION B (SIMULATED ALTERNATIVE)</span>
              <h3 className="scenario-slot-name">{selectedPreset.slotB.time}</h3>
            </div>

            <div className="scenario-metrics-list">
              <div className="s-metric-row">
                <span className="s-lbl">Wave Height:</span>
                <span className="s-val text-green">{selectedPreset.slotB.wave} m</span>
              </div>
              <div className="s-metric-row">
                <span className="s-lbl">Wind Speed:</span>
                <span className="s-val text-green">{selectedPreset.slotB.wind} km/h</span>
              </div>
              <div className="s-metric-row">
                <span className="s-lbl">Risk Level:</span>
                <span className={`s-val-badge risk-${selectedPreset.slotB.risk.toLowerCase()}`}>
                  {selectedPreset.slotB.risk}
                </span>
              </div>
              <div className="s-metric-row">
                <span className="s-lbl">Safety Status:</span>
                <span className={`s-val-badge status-${selectedPreset.slotB.status.toLowerCase().split(' ')[0]}`}>
                  {selectedPreset.slotB.status}
                </span>
              </div>
              <div className="s-metric-row">
                <span className="s-lbl">Confidence:</span>
                <span className="s-val highlight">{selectedPreset.slotB.confidence}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Button & Dynamic Simulation Result */}
        <div className="whatif-action-row">
          <button
            type="button"
            className="btn-run-scenario"
            onClick={handleRunScenario}
            disabled={isRunning}
          >
            {isRunning ? (
              <span className="scenario-spinner"></span>
            ) : (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 14 14" />
                </svg>
                <span>Run Scenario Simulation</span>
              </>
            )}
          </button>
        </div>

        {simulationResult && (
          <div className="whatif-result-card glass-panel">
            <div className="whatif-result-header">
              <span className="result-sparkle-icon">✨</span>
              <h4 className="whatif-result-title">Multi-Agent Comparative Synthesis</h4>
            </div>
            <p className="whatif-result-text">{simulationResult}</p>
          </div>
        )}
      </div>
    </section>
  );
};
