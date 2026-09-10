import React, { useEffect, useMemo, useState } from 'react';
import './WhatIfSimulation.css';
import {
  getOrchestratorDecision,
  validateLocation,
  type EvidenceItemContract,
  type FinalDecisionObjectContract,
} from '../../services/api';
import { useLocationContext } from '../../context/LocationContext';

type ScenarioType = 'departure-time' | 'location-comparison' | 'route-speed';
interface ScenarioOption { id: ScenarioType; label: string; prompt: string; }
interface ScenarioCardData { title: string; location: string; wave: string; wind: string; risk: string; status: string; confidence: string; sufficient: boolean; }
const INSUFFICIENT = 'INSUFFICIENT EVIDENCE';

function evidenceValue(evidence: EvidenceItemContract[], matcher: RegExp): string {
  const item = evidence.find((candidate) => matcher.test(candidate.parameter.toLowerCase()) && candidate.freshness !== 'Unavailable');
  return !item || item.value === null || item.value === undefined || item.value === '' ? INSUFFICIENT : `${item.value}${item.unit ? ` ${item.unit}` : ''}`;
}

const confidenceLabel = (score?: number | null) => typeof score === 'number' && score > 0 ? `${score}%` : INSUFFICIENT;

function riskFromDecision(decision?: string | null): string {
  const value = (decision || '').toLowerCase();
  if (value.includes('not recommended') || value.includes('blocked')) return 'HIGH';
  if (value.includes('caution')) return 'MODERATE';
  if (value.includes('suitable') || value.includes('clear')) return 'LOW';
  return INSUFFICIENT;
}

function emptyCard(title: string, location = INSUFFICIENT): ScenarioCardData {
  return { title, location, wave: INSUFFICIENT, wind: INSUFFICIENT, risk: INSUFFICIENT, status: INSUFFICIENT, confidence: INSUFFICIENT, sufficient: false };
}

function cardFromDecision(result: FinalDecisionObjectContract, title: string, forcedLocationName?: string): ScenarioCardData {
  const sufficient = result.decision !== 'Insufficient Evidence' && result.confidence > 0;
  const locName = forcedLocationName || result.location?.name || INSUFFICIENT;
  return {
    title,
    location: locName,
    wave: sufficient ? evidenceValue(result.evidence, /wave|swell/) : INSUFFICIENT,
    wind: sufficient ? evidenceValue(result.evidence, /wind/) : INSUFFICIENT,
    risk: sufficient ? riskFromDecision(result.decision) : INSUFFICIENT,
    status: sufficient ? result.safety_status : INSUFFICIENT,
    confidence: sufficient ? confidenceLabel(result.confidence) : INSUFFICIENT,
    sufficient,
  };
}

async function resolveLocationPriority(
  query: string,
  ctxName: string,
  ctxLat?: number,
  ctxLon?: number,
  ctxStatus?: string
): Promise<{
  name: string;
  latitude?: number;
  longitude?: number;
  isInland: boolean;
  isResolved: boolean;
}> {
  const trimmed = query.trim();

  // Tier 1a: Explicit coordinates in query (e.g. "12.91, 74.85" or "12.91° N, 74.85° E")
  const coordMatch = trimmed.match(/(?:^|[^\d.-])(-?\d{1,2}(?:\.\d+)?)\s*°?\s*([NSns])?\s*[,/ ]\s*(-?\d{1,3}(?:\.\d+)?)\s*°?\s*([EWew])?/);
  if (coordMatch) {
    let lat = parseFloat(coordMatch[1]);
    let lon = parseFloat(coordMatch[3]);
    if (coordMatch[2] && coordMatch[2].toUpperCase() === 'S') lat = -lat;
    if (coordMatch[4] && coordMatch[4].toUpperCase() === 'W') lon = -lon;
    if (!isNaN(lat) && !isNaN(lon)) {
      try {
        const val = await validateLocation({ latitude: lat, longitude: lon });
        return {
          name: val.location_name || `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? 'N' : 'S'}, ${Math.abs(lon).toFixed(4)}° ${lon >= 0 ? 'E' : 'W'}`,
          latitude: val.latitude ?? lat,
          longitude: val.longitude ?? lon,
          isInland: val.status === 'INLAND' || (!val.is_coastal && !val.is_marine),
          isResolved: true,
        };
      } catch (e) {
        console.warn('Coordinates validation error:', e);
      }
    }
  }

  // Tier 1b: Prepositional location pattern (e.g. "at Mangalore", "from Paradip", "near Goa", "offshore Kochi")
  const prepMatch = trimmed.match(/\b(?:at|from|near|offshore|around|in)\s+([a-zA-Z\s]{3,30})/i);
  if (prepMatch) {
    const candidate = prepMatch[1].trim().replace(/\s+(?:tomorrow|today|tonight|morning|evening|afternoon|at|\d{1,2}(?::\d{2})?|knots?|kts?)\b.*/i, '').trim();
    if (candidate.length >= 3) {
      try {
        const val = await validateLocation({ query: candidate });
        if (val && val.status !== 'UNRESOLVED' && typeof val.latitude === 'number' && typeof val.longitude === 'number') {
          return {
            name: val.display_name || val.location_name || candidate,
            latitude: val.latitude,
            longitude: val.longitude,
            isInland: val.status === 'INLAND' || (!val.is_coastal && !val.is_marine),
            isResolved: true,
          };
        }
      } catch (e) {
        console.warn('Preposition location validation error:', e);
      }
    }
  }

  // Tier 2: Current selected LocationContext
  const hasCtx = Boolean(ctxName) && typeof ctxLat === 'number' && typeof ctxLon === 'number' && ctxStatus !== 'UNRESOLVED';
  if (hasCtx) {
    return {
      name: ctxName,
      latitude: ctxLat,
      longitude: ctxLon,
      isInland: ctxStatus === 'INLAND',
      isResolved: true,
    };
  }

  // Tier 1c: If query is simply a location name
  if (trimmed.length >= 3 && trimmed.length <= 40 && !trimmed.includes('?') && !/\b(?:how|what|why|can|is|are|will|departure|speed|time)\b/i.test(trimmed)) {
    try {
      const val = await validateLocation({ query: trimmed });
      if (val && val.status !== 'UNRESOLVED' && typeof val.latitude === 'number' && typeof val.longitude === 'number') {
        return {
          name: val.display_name || val.location_name || trimmed,
          latitude: val.latitude,
          longitude: val.longitude,
          isInland: val.status === 'INLAND' || (!val.is_coastal && !val.is_marine),
          isResolved: true,
        };
      }
    } catch {
      // Ignored
    }
  }

  // Tier 3: Unresolved
  return {
    name: '',
    isInland: false,
    isResolved: false,
  };
}

async function resolveComparisonTargets(
  query: string,
  primaryName: string,
  primaryLat?: number,
  primaryLon?: number
): Promise<{ locA: { name: string; lat: number; lon: number } | null; locB: { name: string; lat: number; lon: number } | null }> {
  // Check for "A vs B" or "A or B" or "compare A and B"
  const compMatch = query.match(/([a-zA-Z\s]{3,25})\s+(?:vs|versus|or|and)\s+([a-zA-Z\s]{3,25})/i);
  if (compMatch) {
    const nameA = compMatch[1].trim();
    const nameB = compMatch[2].trim();
    try {
      const [valA, valB] = await Promise.all([
        validateLocation({ query: nameA }),
        validateLocation({ query: nameB }),
      ]);
      if (
        valA.status !== 'UNRESOLVED' &&
        valB.status !== 'UNRESOLVED' &&
        typeof valA.latitude === 'number' &&
        typeof valB.latitude === 'number' &&
        typeof valA.longitude === 'number' &&
        typeof valB.longitude === 'number'
      ) {
        return {
          locA: { name: valA.display_name || valA.location_name || nameA, lat: valA.latitude, lon: valA.longitude },
          locB: { name: valB.display_name || valB.location_name || nameB, lat: valB.latitude, lon: valB.longitude },
        };
      }
    } catch (e) {
      console.warn('Comparison locations validation error:', e);
    }
  }

  // Check if single alternative given: e.g. "vs Goa" with LocationContext as primary
  const altMatch = query.match(/(?:vs|versus|compare with|with|to)\s+([a-zA-Z\s]{3,25})/i);
  const altName = altMatch ? altMatch[1].trim() : (query.trim() !== primaryName ? query.trim() : '');
  if (altName && primaryName && typeof primaryLat === 'number' && typeof primaryLon === 'number') {
    try {
      const valB = await validateLocation({ query: altName });
      if (valB.status !== 'UNRESOLVED' && typeof valB.latitude === 'number' && typeof valB.longitude === 'number') {
        return {
          locA: { name: primaryName, lat: primaryLat, lon: primaryLon },
          locB: { name: valB.display_name || valB.location_name || altName, lat: valB.latitude, lon: valB.longitude },
        };
      }
    } catch (e) {
      console.warn('Alternative comparison validation error:', e);
    }
  }

  return { locA: null, locB: null };
}

export const WhatIfSimulation: React.FC = () => {
  const { selectedLocation, activeValidation } = useLocationContext();
  const [scenarioType, setScenarioType] = useState<ScenarioType>('departure-time');
  const [scenarioQuery, setScenarioQuery] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [cards, setCards] = useState<[ScenarioCardData, ScenarioCardData]>([emptyCard('Current Evidence'), emptyCard('Simulated Alternative')]);
  const [simulationResult, setSimulationResult] = useState<string | null>(null);

  const locationName = selectedLocation.name || activeValidation.location_name || '';
  const latitude = activeValidation.latitude ?? (selectedLocation.name ? selectedLocation.lat : undefined);
  const longitude = activeValidation.longitude ?? (selectedLocation.name ? selectedLocation.lon : undefined);

  const scenarioOptions = useMemo<ScenarioOption[]>(() => [
    { id: 'departure-time', label: `Departure-time comparison${locationName ? ` — ${locationName}` : ''}`, prompt: 'Optional: specify departure time or explicitly name an operating location.' },
    { id: 'location-comparison', label: `Fishing-ground comparison${locationName ? ` — ${locationName}` : ''}`, prompt: 'Name the two locations or fishing grounds to compare (e.g. "Mangalore or Goa").' },
    { id: 'route-speed', label: `Vessel-speed / route comparison${locationName ? ` — ${locationName}` : ''}`, prompt: 'Describe destination and two vessel speeds to compare (e.g. "12 knots vs 18 knots").' },
  ], [locationName]);

  useEffect(() => {
    setCards([emptyCard('Current Evidence', locationName || INSUFFICIENT), emptyCard('Simulated Alternative')]);
    setSimulationResult(null);
  }, [locationName, latitude, longitude]);

  const handleRunScenario = async () => {
    setIsRunning(true);
    setSimulationResult(null);

    try {
      // 1. Resolve target location using strict priority:
      // explicit location in query -> selected LocationContext -> ask user
      const resolved = await resolveLocationPriority(
        scenarioQuery,
        locationName,
        latitude,
        longitude,
        activeValidation.status
      );

      // Inland Protection: Strictly block fabricated marine data
      if (resolved.isInland) {
        setCards([
          emptyCard('Current Evidence', resolved.name || INSUFFICIENT),
          emptyCard('Simulated Alternative', resolved.name || INSUFFICIENT),
        ]);
        setSimulationResult('INSUFFICIENT EVIDENCE — selected location is inland. Marine and hydrodynamic operations require coastal or marine coordinates.');
        return;
      }

      // No location resolved: Prompt user truthfully
      if (!resolved.isResolved) {
        setCards([emptyCard('Current Evidence'), emptyCard('Simulated Alternative')]);
        setSimulationResult('INSUFFICIENT EVIDENCE — select an operating location or explicitly name a location in the scenario.');
        return;
      }

      const now = new Date();
      const alternative = new Date(now.getTime() + 3 * 60 * 60 * 1000);
      const query = scenarioQuery.trim();

      // SCENARIO 1: Departure-Time Comparison
      if (scenarioType === 'departure-time') {
        const scenario = query || `Assess departure conditions at ${resolved.name}.`;
        const [base, changed] = await Promise.all([
          getOrchestratorDecision(`${scenario} Base departure.`, resolved.latitude, resolved.longitude, now.toISOString()),
          getOrchestratorDecision(`${scenario} Alternative departure three hours later.`, resolved.latitude, resolved.longitude, alternative.toISOString()),
        ]);

        const cardA = cardFromDecision(base, `Departure ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`, resolved.name);
        const cardB = cardFromDecision(changed, `Departure ${alternative.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`, resolved.name);
        setCards([cardA, cardB]);

        if (base.confidence > 0 && changed.confidence > 0) {
          setSimulationResult(`${base.summary} Alternative: ${changed.summary}`);
        } else {
          setSimulationResult(`INSUFFICIENT EVIDENCE — operational departure windows require current marine evidence at ${resolved.name}.`);
        }
        return;
      }

      // SCENARIO 2: Fishing-Ground / Location Comparison
      if (scenarioType === 'location-comparison') {
        const targets = await resolveComparisonTargets(query, resolved.name, resolved.latitude, resolved.longitude);

        if (targets.locA && targets.locB) {
          const [evalA, evalB] = await Promise.all([
            getOrchestratorDecision(`Assess marine safety and fishing conditions at ${targets.locA.name}.`, targets.locA.lat, targets.locA.lon),
            getOrchestratorDecision(`Assess marine safety and fishing conditions at ${targets.locB.name}.`, targets.locB.lat, targets.locB.lon),
          ]);

          const cardA = cardFromDecision(evalA, targets.locA.name, targets.locA.name);
          const cardB = cardFromDecision(evalB, targets.locB.name, targets.locB.name);
          setCards([cardA, cardB]);

          const bothSufficient = evalA.confidence > 0 && evalB.confidence > 0;
          setSimulationResult(
            bothSufficient
              ? `Comparative analysis completed: ${targets.locA.name} evaluated at ${evalA.safety_status} (${evalA.decision}) vs ${targets.locB.name} evaluated at ${evalB.safety_status} (${evalB.decision}).`
              : 'INSUFFICIENT EVIDENCE — both locations require current marine evidence for comparative evaluation.'
          );
          return;
        }

        // Fallback to query comparison parser
        const comparison = await getOrchestratorDecision(query || resolved.name, resolved.latitude, resolved.longitude);
        const candidates = comparison.comparison_data?.target_locations || [];

        if (candidates.length >= 2) {
          const evaluated = await Promise.all(
            candidates.slice(0, 2).map((target) =>
              getOrchestratorDecision(`Assess current marine safety and fishing evidence at ${target.location_name}.`, target.latitude, target.longitude)
            )
          );
          setCards([
            cardFromDecision(evaluated[0], candidates[0].location_name, candidates[0].location_name),
            cardFromDecision(evaluated[1], candidates[1].location_name, candidates[1].location_name),
          ]);
          setSimulationResult(
            evaluated.every((item) => item.confidence > 0)
              ? comparison.summary
              : 'INSUFFICIENT EVIDENCE — both locations require current marine evidence.'
          );
          return;
        }

        setCards([cardFromDecision(comparison, 'Current Evidence', resolved.name), emptyCard('Alternative Location')]);
        setSimulationResult(`INSUFFICIENT EVIDENCE — explicitly name two resolvable locations or an alternative ground to compare with ${resolved.name} (e.g. "${resolved.name} vs Goa").`);
        return;
      }

      // SCENARIO 3: Vessel-Speed / Route Comparison
      const speeds = [...query.matchAll(/(\d+(?:\.\d+)?)\s*(?:kt|kts|knots?)\b/gi)].map((match) => match[1]);
      const speedA = speeds[0] || '10';
      const speedB = speeds[1] || '16';

      const corridorQuery = query || `Transit passage from ${resolved.name}`;
      const [evalSpeedA, evalSpeedB] = await Promise.all([
        getOrchestratorDecision(`${corridorQuery} at ${speedA} knots vessel speed.`, resolved.latitude, resolved.longitude),
        getOrchestratorDecision(`${corridorQuery} at ${speedB} knots vessel speed.`, resolved.latitude, resolved.longitude),
      ]);

      setCards([
        cardFromDecision(evalSpeedA, `${speedA} knot option`, resolved.name),
        cardFromDecision(evalSpeedB, `${speedB} knot option`, resolved.name),
      ]);

      if (evalSpeedA.confidence > 0 && evalSpeedB.confidence > 0) {
        setSimulationResult(`${evalSpeedA.summary} Alternative: ${evalSpeedB.summary}`);
      } else {
        setSimulationResult(`INSUFFICIENT EVIDENCE — both route-speed options require current operational evidence at ${resolved.name}.`);
      }
    } catch (error) {
      setCards([emptyCard('Current Evidence', locationName || INSUFFICIENT), emptyCard('Simulated Alternative')]);
      setSimulationResult(`INSUFFICIENT EVIDENCE — ${error instanceof Error ? error.message : 'analysis pipeline unavailable'}`);
    } finally {
      setIsRunning(false);
    }
  };

  const selectedOption = scenarioOptions.find((option) => option.id === scenarioType)!;
  const renderCard = (card: ScenarioCardData, alternative: boolean) => (
    <div className={`scenario-card ${alternative ? 'card-option-b' : 'card-option-a'}`}>
      <div className="scenario-card-header">
        <span className={`scenario-tag ${alternative ? 'highlight-teal' : ''}`}>
          {alternative ? 'OPTION B (SIMULATED ALTERNATIVE)' : 'OPTION A'}
        </span>
        <h3 className="scenario-slot-name">{card.title}</h3>
        <span className="scenario-location-name">{card.location}</span>
      </div>
      <div className="scenario-metrics-list">
        {[
          ['Wave Height:', card.wave],
          ['Wind Speed:', card.wind],
          ['Risk Level:', card.risk],
          ['Safety Status:', card.status],
          ['Confidence:', card.confidence],
        ].map(([label, value]) => (
          <div className="s-metric-row" key={label}>
            <span className="s-lbl">{label}</span>
            <span className={`s-val ${!card.sufficient ? 'insufficient' : ''}`}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <section id="what-if-scenarios" className="whatif-section">
      <div className="container">
        <div className="whatif-header">
          <div className="whatif-title-block">
            <span className="section-tag">PREDICTIVE MARITIME SIMULATION</span>
            <h2 className="whatif-main-title">What-If Scenarios</h2>
            <p className="whatif-subtitle">
              Simulate operational decisions using the selected operating location and currently available OCEANIS evidence.
            </p>
          </div>
          <div className="whatif-badge">
            <span className="live-dot pulse"></span>
            <span className="badge-text">WHAT-IF SIMULATION ENGINE ACTIVE</span>
          </div>
        </div>

        <div className="scenario-preset-selector">
          <span className="selector-title">SELECT SIMULATION SCENARIO:</span>
          <div className="preset-buttons-row">
            {scenarioOptions.map((option) => (
              <button
                key={option.id}
                type="button"
                className={`preset-btn ${scenarioType === option.id ? 'active' : ''}`}
                onClick={() => {
                  setScenarioType(option.id);
                  setSimulationResult(null);
                }}
              >
                {option.label}
              </button>
            ))}
          </div>
          <label className="scenario-query-label" htmlFor="whatif-query">
            SCENARIO DETAILS
          </label>
          <textarea
            id="whatif-query"
            className="scenario-query-input"
            value={scenarioQuery}
            onChange={(event) => setScenarioQuery(event.target.value)}
            placeholder={selectedOption.prompt}
            rows={2}
          />
        </div>

        <div className="whatif-comparison-grid">
          {renderCard(cards[0], false)}
          <div className="versus-badge-container">
            <span className="versus-pill">VS</span>
          </div>
          {renderCard(cards[1], true)}
        </div>

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

export default WhatIfSimulation;

