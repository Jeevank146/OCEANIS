import React, { useState, useEffect, useRef } from 'react';
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

interface ConversationTurn {
  id: string;
  query: string;
  response: FinalDecisionObjectContract;
  timestamp: string;
}

export const AskOceanisPage: React.FC = () => {
  const location = useLocation();
  const { selectedLocation } = useLocationContext();

  const [queryInput, setQueryInput] = useState<string>('Can I go fishing tomorrow morning from Kakinada?');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [decisionData, setDecisionData] = useState<FinalDecisionObjectContract | null>(null);

  // Conversational History State
  const [conversationHistory, setConversationHistory] = useState<ConversationTurn[]>([]);

  // What-If state
  const [whatIfTime, setWhatIfTime] = useState<string>('09:00');
  const [isSimulatingWhatIf, setIsSimulatingWhatIf] = useState<boolean>(false);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfComparisonContract | null>(null);

  // Active tab for evidence viewing
  const [activeEvidenceFilter, setActiveEvidenceFilter] = useState<string>('ALL');

  // Voice Agent State
  const [voiceState, setVoiceState] = useState<'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING' | 'ERROR'>('IDLE');
  const [voiceLanguage, setVoiceLanguage] = useState<string>('auto');
  const [voiceErrorText, setVoiceErrorText] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const recognitionRef = useRef<any>(null);

  // Categorized Demo Query Matrix
  const samplePrompts = [
    { cat: 'DECISION', label: '🎣 Kakinada Fishing (Decision)', text: 'Can I go fishing tomorrow morning from Kakinada?' },
    { cat: 'INFO', label: '🌊 Kakinada Conditions (Info)', text: 'What are the current ocean conditions near Kakinada?' },
    { cat: 'SAFETY', label: '⚠️ Visakhapatnam Cyclone (Safety)', text: 'Is there any marine warning near Visakhapatnam?' },
    { cat: 'EARTH OBS', label: '🛰️ Paradip SST & Chl (Remote Sensing)', text: 'What is the SST and chlorophyll near Paradip?' },
    { cat: 'COMPARE', label: '⚖️ Port Comparison (Compare)', text: 'Which is better for fishing, Kakinada or Visakhapatnam?' },
    { cat: 'ROUTE', label: '🧭 Safest Route (Navigation)', text: 'What is the safest route from Kakinada to Visakhapatnam?' },
    { cat: 'WHAT-IF', label: '⏰ 9 AM Shift (What-If)', text: 'What if I leave at 9 AM instead?' },
    { cat: 'SPATIAL', label: '🛡️ Marine Protected Zone (Spatial)', text: 'Is this location inside a protected marine zone?' },
    { cat: 'INLAND', label: '🏞️ Hyderabad Inland Protection', text: 'Can I go ocean fishing from Hyderabad?' },
    { cat: 'TELUGU', label: '🇮🇳 Telugu: Kakinada lo fishing', text: 'Kakinada lo tomorrow fishing conditions ela untayi?' },
    { cat: 'HINDI', label: '🇮🇳 Hindi: Samundar conditions', text: 'Yahan samundar ki conditions kaisi hain?' },
  ];

  // Follow-up context suggestions
  const followUpSuggestions = [
    { label: '🕒 What about tomorrow morning?', query: 'What about tomorrow morning?' },
    { label: '❓ Why this decision?', query: 'Why this decision?' },
    { label: '⏰ What if I leave at 9 AM instead?', query: 'What if I leave at 9 AM instead?' },
    { label: '📍 What about Visakhapatnam?', query: 'What about Visakhapatnam?' },
    { label: '🌊 Show wave and wind telemetry', query: 'Show wave and wind telemetry' },
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

  // Clean up speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  const executeDecisionQuery = async (queryText: string) => {
    if (!queryText.trim()) return;
    setIsLoading(true);
    setErrorMsg(null);
    setWhatIfResult(null);

    // Cancel any ongoing TTS
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }

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

      // Add to conversation history
      const newTurn: ConversationTurn = {
        id: `turn-${Date.now()}`,
        query: queryText.trim(),
        response: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setConversationHistory((prev) => [newTurn, ...prev.slice(0, 5)]);
    } catch (err: any) {
      console.error('Decision pipeline error:', err);
      setErrorMsg(err.message || 'Failed to retrieve multi-agent decision intelligence.');
    } finally {
      setIsLoading(false);
      setVoiceState('IDLE');
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

  // Voice Agent Speech-to-Text Handler
  const handleVoiceToggle = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceErrorText('Voice recognition is not supported in this browser. You can continue typing naturally.');
      setVoiceState('ERROR');
      return;
    }

    if (voiceState === 'LISTENING') {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      setVoiceState('IDLE');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = voiceLanguage === 'auto' ? 'en-IN' : voiceLanguage;

      setVoiceState('LISTENING');
      setVoiceErrorText(null);

      recognition.onresult = (event: any) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        if (transcript.trim()) {
          setQueryInput(transcript);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
          setVoiceErrorText('Microphone permission denied. Please allow microphone access to speak.');
        } else if (event.error !== 'no-speech') {
          setVoiceErrorText(`Voice input error (${event.error}). You can type your question.`);
        }
        setVoiceState('ERROR');
      };

      recognition.onend = () => {
        if (voiceState === 'LISTENING' && queryInput.trim()) {
          setVoiceState('PROCESSING');
          executeDecisionQuery(queryInput);
        } else {
          setVoiceState('IDLE');
        }
      };

      recognition.start();
    } catch (err: any) {
      console.error('Failed to start speech recognition:', err);
      setVoiceErrorText('Failed to start voice listener. Please type your query.');
      setVoiceState('ERROR');
    }
  };

  // Text-to-Speech (TTS) Read Aloud Handler
  const handleToggleSpeak = () => {
    if (!window.speechSynthesis || !decisionData) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const textToSpeak = decisionData.primary_answer || decisionData.summary;
    if (!textToSpeak) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    // Detect language preference
    if (voiceLanguage && voiceLanguage !== 'auto') {
      utterance.lang = voiceLanguage;
    } else {
      utterance.lang = 'en-IN';
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
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
  const isComparisonQuery = queryIntent === 'COMPARISON' && Boolean(decisionData?.comparison_data);

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
            Natural-language & Voice marine intelligence synthesized across specialized domain agents with deterministic safety verification.
          </p>
        </div>
      </div>

      {/* Query Bar with Real Voice Agent Integration */}
      <div className="query-card-container">
        <div className="query-input-row">
          <div className="input-with-voice-wrapper">
            <input
              type="text"
              className={`oceanis-query-input ${voiceState === 'LISTENING' ? 'input-listening' : ''}`}
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && executeDecisionQuery(queryInput)}
              placeholder="Ask any natural language or voice marine question (English, Telugu, Hindi, Tamil...)"
            />

            {/* Voice Microphone Control */}
            <button
              type="button"
              className={`oceanis-voice-btn state-${voiceState.toLowerCase()}`}
              onClick={handleVoiceToggle}
              title={
                voiceState === 'LISTENING'
                  ? 'Listening... Click to stop'
                  : 'Speak with OCEANIS Voice Agent'
              }
            >
              {voiceState === 'LISTENING' ? (
                <div className="listening-pulse-ring">
                  <span className="mic-pulse-dot" />
                </div>
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mic-icon">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              )}
              <span className="voice-btn-label">
                {voiceState === 'LISTENING' ? 'Listening...' : 'Voice'}
              </span>
            </button>
          </div>

          {/* Voice Language Selector */}
          <select
            className="voice-lang-select"
            value={voiceLanguage}
            onChange={(e) => setVoiceLanguage(e.target.value)}
            title="Select voice input language"
          >
            <option value="auto">🌐 Auto / English (India)</option>
            <option value="hi-IN">🇮🇳 Hindi (हिन्दी)</option>
            <option value="te-IN">🇮🇳 Telugu (తెలుగు)</option>
            <option value="ta-IN">🇮🇳 Tamil (தமிழ்)</option>
            <option value="kn-IN">🇮🇳 Kannada (ಕನ್ನಡ)</option>
            <option value="ml-IN">🇮🇳 Malayalam (മലയാളം)</option>
            <option value="mr-IN">🇮🇳 Marathi (मराठी)</option>
            <option value="bn-IN">🇮🇳 Bengali (বাংলা)</option>
            <option value="gu-IN">🇮🇳 Gujarati (ગુજરાતી)</option>
          </select>

          <button
            className="oceanis-analyze-btn"
            onClick={() => executeDecisionQuery(queryInput)}
            disabled={isLoading}
          >
            {isLoading ? 'Consulting Agents...' : 'Analyze Query'}
          </button>
        </div>

        {/* Voice Listening / Error Banner */}
        {voiceState === 'LISTENING' && (
          <div className="voice-active-banner">
            <span className="voice-wave-animation">
              <span /><span /><span /><span /><span />
            </span>
            <span>Listening... Speak your marine question naturally in your chosen language</span>
          </div>
        )}

        {voiceErrorText && (
          <div className="voice-error-banner">
            <span>ℹ️ {voiceErrorText}</span>
          </div>
        )}

        {/* Quick Categorized Prompts Matrix */}
        <div className="quick-prompts-section">
          <div className="quick-label-row">
            <span className="quick-label">Categorized Verification Prompts:</span>
          </div>
          <div className="quick-prompts-matrix">
            {samplePrompts.map((p, idx) => (
              <button
                key={idx}
                className={`quick-prompt-btn cat-${p.cat.toLowerCase().replace(' ', '-')}`}
                onClick={() => {
                  setQueryInput(p.text);
                  executeDecisionQuery(p.text);
                }}
              >
                <span className="cat-tag">{p.cat}</span>
                <span className="cat-text">{p.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="error-alert-banner">
          <span className="error-alert-icon">⚠️</span>
          <div className="error-alert-text">
            <strong>Unable to Complete Marine Analysis:</strong> {errorMsg}
          </div>
          <button 
            type="button" 
            className="btn-retry-query"
            onClick={() => executeDecisionQuery(queryInput)}
          >
            Retry Query
          </button>
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
                  {decisionData.location.is_inland && <span className="inland-tag"> • INLAND</span>}
                </span>
              )}
              {decisionData.requested_time && (
                <span className="time-tag">
                  🕒 {decisionData.requested_time}
                </span>
              )}
            </div>

            <div className="answer-actions-group">
              {/* Text-to-Speech Playback Button */}
              {window.speechSynthesis && (
                <button
                  type="button"
                  className={`btn-tts-speak ${isSpeaking ? 'speaking' : ''}`}
                  onClick={handleToggleSpeak}
                  title={isSpeaking ? 'Stop Voice Playback' : 'Read Answer Aloud'}
                >
                  <span className="tts-icon">{isSpeaking ? '⏹' : '🔊'}</span>
                  <span>{isSpeaking ? 'Stop Voice' : 'Read Aloud'}</span>
                </button>
              )}

              <div className="answer-freshness-pill">
                <span className={`fresh-badge ${getFreshnessBadgeClass(decisionData.freshness_summary)}`}>
                  {decisionData.freshness_summary} Telemetry
                </span>
              </div>
            </div>
          </div>

          <div className="answer-body-content">
            <h2 className="primary-answer-text">
              {decisionData.primary_answer || decisionData.summary}
            </h2>
          </div>

          {/* Follow-up Quick Suggestions */}
          <div className="follow-up-suggestions-row">
            <span className="follow-up-label">Follow-up Context:</span>
            {followUpSuggestions.map((f, i) => (
              <button
                key={i}
                type="button"
                className="btn-follow-up-chip"
                onClick={() => {
                  setQueryInput(f.query);
                  executeDecisionQuery(f.query);
                }}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Dynamically Selected Agents Consultation Grid */}
      {decisionData && decisionData.agents_consulted && decisionData.agents_consulted.length > 0 && (
        <div className="agents-consulted-card">
          <div className="card-header-flex">
            <div>
              <h3 className="section-title">Agents Consulted ({agentsCount}/{totalAgents})</h3>
              <p className="section-subtitle">Dynamic multi-agent coordination with specialized evidence contributions</p>
            </div>
            <div className="orchestrator-status-pill">
              <span className="orch-pulse-dot" />
              <span>DYNAMIC ORCHESTRATION</span>
            </div>
          </div>

          <div className="agents-grid">
            {decisionData.agents_consulted.map((ag: AgentResultContract, idx: number) => (
              <div key={idx} className={`agent-status-box status-${ag.status}`}>
                <div className="agent-box-header">
                  <span className="agent-domain-icon">
                    {ag.agent_name.includes('Fishing') && '🎣'}
                    {ag.agent_name.includes('Conditions') && '🌊'}
                    {ag.agent_name.includes('Earth') && '🛰️'}
                    {ag.agent_name.includes('Spatial') && '🗺️'}
                    {ag.agent_name.includes('Disaster') && '🛡️'}
                    {ag.agent_name.includes('Operations') && '⚓'}
                  </span>
                  <div className="agent-title-block">
                    <strong className="agent-name">{ag.agent_name}</strong>
                    <span className="agent-conf-badge">{ag.confidence}% Conf</span>
                  </div>
                  <span className={`agent-state-pill state-${ag.status}`}>
                    {ag.status === 'success' ? '✓ SUCCESS' : ag.status.toUpperCase()}
                  </span>
                </div>

                <p className="agent-summary-text">{ag.summary}</p>

                {ag.findings && ag.findings.length > 0 && (
                  <ul className="agent-findings-list">
                    {ag.findings.map((f: string, i: number) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* COMPARISON QUERY VIEW (Side-by-Side Location Contrast) */}
      {/* ------------------------------------------------------------- */}
      {isComparisonQuery && decisionData && decisionData.comparison_data && (
        <div className="comparison-results-section">
          <div className="comparison-header">
            <span className="comparison-kicker">PORT / LOCATION COMPARISON</span>
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
                <span className="meta-v">{decisionData.requested_time || 'Immediate / Tomorrow 06:00'}</span>
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

          {/* What-If Simulation Interactive Panel */}
          <div className="what-if-interactive-card">
            <div className="what-if-header">
              <span className="what-if-kicker">WHAT-IF SCENARIO ANALYSIS</span>
              <h3 className="what-if-title">Operational Departure Shift Simulation</h3>
              <p className="what-if-sub">Evaluate how adjusting departure timing impacts safety margins, wind gusts, and wave steepness</p>
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

      {/* Safety Disclaimer Banner */}
      {decisionData && (
        <div className="oceanis-safety-disclaimer-banner">
          <span className="disclaimer-shield-icon">🛡️</span>
          <p className="disclaimer-text">
            <strong>Operational Advisory:</strong> Decision support, not a safety guarantee. Always cross-reference with official local port authorities, Coast Guard, and IMD/INCOIS meteorological bulletins before initiating offshore voyages.
          </p>
        </div>
      )}
    </div>
  );
};

export default AskOceanisPage;
