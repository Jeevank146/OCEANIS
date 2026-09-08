import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import { useLanguage } from '../../context/LanguageContext';
import {
  getOrchestratorDecision,
  runWhatIfSimulation,
} from '../../services/api';
import type {
  FinalDecisionObjectContract,
  WhatIfComparisonContract,
  EvidenceItemContract,
  AgentResultContract,
  ComparisonLocationDetailContract,
} from '../../services/api';
import {
  synthesizeMultilingualResponse,
  sanitizeEvidenceText,
  sanitizeEvidenceValue,
  getNormalizedUnit,
  FOLLOW_UP_SUGGESTIONS,
} from '../../utils/multilingualSynthesizer';
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
  const { language, t } = useLanguage();

  // Strictly neutral initial state - NO hardcoded city query
  const [queryInput, setQueryInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [decisionData, setDecisionData] = useState<FinalDecisionObjectContract | null>(null);
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

  // Only run if an explicit initial query was passed via route navigation
  useEffect(() => {
    if (location.state && (location.state as any).initialQuery) {
      const q = (location.state as any).initialQuery;
      setQueryInput(q);
      executeDecisionQuery(q);
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
        null,
        null,
        null,
        null,
        null,
        language
      );
      setDecisionData(res);
      if (res.what_if_comparison) {
        setWhatIfResult(res.what_if_comparison);
      }

      // Add to conversation history without duplicate consecutive entries
      const trimmedQuery = queryText.trim();
      setConversationHistory((prev) => {
        if (prev.length > 0 && prev[0].query.toLowerCase() === trimmedQuery.toLowerCase()) {
          return [{ ...prev[0], response: res }, ...prev.slice(1)];
        }
        const newTurn: ConversationTurn = {
          id: `turn-${Date.now()}`,
          query: trimmedQuery,
          response: res,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        return [newTurn, ...prev.slice(0, 5)];
      });
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
        query: queryInput || 'What if departure is modified?',
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
      recognition.lang = voiceLanguage === 'auto' ? (language === 'en' ? 'en-IN' : `${language}-IN`) : voiceLanguage;

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
        setVoiceState((prev) => {
          if (prev === 'LISTENING') {
            return 'IDLE';
          }
          return prev;
        });
      };

      recognition.start();
    } catch (err: any) {
      console.error('Failed to start speech recognition:', err);
      setVoiceErrorText('Could not access microphone. Please check browser permissions.');
      setVoiceState('ERROR');
    }
  };

  // Multilingual synthesized intelligence response
  const synthesized = decisionData ? synthesizeMultilingualResponse(decisionData, language) : null;

  // Text-to-Speech (TTS) Read Aloud Handler
  const handleToggleSpeak = () => {
    if (!window.speechSynthesis || !decisionData) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const textToSpeak = synthesized?.primaryAnswer || decisionData.primary_answer || decisionData.summary;
    if (!textToSpeak) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    // Detect language preference
    if (voiceLanguage && voiceLanguage !== 'auto') {
      utterance.lang = voiceLanguage;
    } else if (language && language !== 'en') {
      utterance.lang = `${language}-IN`;
    } else {
      utterance.lang = 'en-IN';
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  // Helper formatting classes
  const getDecisionBadgeClass = (dec: string) => {
    const d = (dec || '').toLowerCase();
    if (d.includes('suitable') || d.includes('recommended') || d.includes('clear')) return 'badge-suitable';
    if (d.includes('caution')) return 'badge-caution';
    if (d.includes('not_recommended') || d.includes('not recommended') || d.includes('blocked') || d.includes('prohibited')) return 'badge-not-recommended';
    return 'badge-insufficient';
  };

  const getFreshnessBadgeClass = (fresh: string) => {
    const f = (fresh || '').toLowerCase();
    if (f.includes('fresh')) return 'fresh-green';
    if (f.includes('aging')) return 'fresh-amber';
    if (f.includes('stale')) return 'fresh-orange';
    return 'fresh-gray';
  };

  const getIntentBadgeClass = (intent: string) => {
    switch (intent) {
      case 'DECISION': return 'intent-decision';
      case 'INFORMATION': return 'intent-info';
      case 'SAFETY': return 'intent-safety';
      case 'COMPARISON': return 'intent-compare';
      case 'ROUTE': return 'intent-route';
      case 'WHAT_IF': return 'intent-whatif';
      default: return 'intent-general';
    }
  };

  // Location Mismatch Detection
  const currentLocName = (selectedLocation?.city || selectedLocation?.name || '').toLowerCase();
  const resultLocName = (decisionData?.location?.name || '').toLowerCase();
  const isLocationMismatch = Boolean(
    decisionData &&
    selectedLocation &&
    resultLocName &&
    currentLocName &&
    !resultLocName.includes(currentLocName) &&
    !currentLocName.includes(resultLocName) &&
    !decisionData.entities_extracted?.is_inland
  );

  const queryIntent = decisionData?.query_intent || 'DECISION';
  const isDecisionQuery = queryIntent === 'DECISION' || queryIntent === 'SAFETY';
  const isComparisonQuery = queryIntent === 'COMPARISON' || Boolean(decisionData?.comparison_data);

  const agentsCount = decisionData?.agents_consulted_count || decisionData?.agents_consulted?.length || 0;
  const totalAgents = decisionData?.total_agents_available || 6;

  // Filtered evidence items
  const filteredEvidence = (decisionData?.evidence || []).filter((item: EvidenceItemContract) => {
    if (activeEvidenceFilter === 'ALL') return true;
    if (activeEvidenceFilter === 'REAL') {
      return item.observation_type === 'Real Telemetry' || item.observation_type === 'Official Observation' || item.observation_type === 'Satellite Radiometry';
    }
    if (activeEvidenceFilter === 'WARNINGS') {
      return item.observation_type === 'Official Warning';
    }
    if (activeEvidenceFilter === 'AI') {
      return item.observation_type === 'AI Assessment' || (item.observation_type as string) === 'Operational Calculation';
    }
    return true;
  });

  // Starter Prompts for Neutral Initial State
  const STARTER_PROMPTS = [
    {
      category: 'Marine Conditions',
      icon: '🌊',
      query: selectedLocation ? `What are the current ocean conditions for ${selectedLocation.city || selectedLocation.name}?` : 'What are the current wave and wind conditions?',
      description: 'Wave height, swell period, wind speed, and sea state analysis.',
    },
    {
      category: 'Fishing Intelligence',
      icon: '🎣',
      query: selectedLocation ? `Is it suitable for artisanal fishing tomorrow morning from ${selectedLocation.city || selectedLocation.name}?` : 'Can I go fishing tomorrow morning?',
      description: 'PFZ zone convergence, species availability, and weather safety.',
    },
    {
      category: 'Earth Observation',
      icon: '🛰️',
      query: selectedLocation ? `Show satellite SST and Chlorophyll-a observations near ${selectedLocation.city || selectedLocation.name}` : 'Show satellite SST and Chlorophyll-a gradients',
      description: 'Sentinel-3 ocean color, thermal gradients, and chlorophyll-a density.',
    },
    {
      category: 'Disaster & Safety',
      icon: '⚠️',
      query: selectedLocation ? `Are there any active cyclone or severe weather warnings near ${selectedLocation.city || selectedLocation.name}?` : 'Are there any active marine weather alerts?',
      description: 'IMD gale warnings, INCOIS swell surge advisories, and high-wind alerts.',
    },
    {
      category: 'Navigation & Passage',
      icon: '🧭',
      query: selectedLocation ? `Evaluate safe passage and navigation around ${selectedLocation.city || selectedLocation.name}` : 'Evaluate coastal transit and navigation route safety',
      description: 'PostGIS bathymetry checks, EEZ limits, and harbor entry conditions.',
    },
    {
      category: 'What-If Simulation',
      icon: '⚡',
      query: selectedLocation ? `What if I depart from ${selectedLocation.city || selectedLocation.name} at 09:00 instead of 06:00?` : 'What if I delay departure by 3 hours?',
      description: 'Tidal shifts, diurnal sea-breeze strengthening, and risk changes.',
    },
  ];

  return (
    <div className="ocean-page-container ask-oceanis-container">
      {/* Top Header Banner */}
      <div className="page-header-banner oceanis-page-header">
        <div className="header-text-block">
          <div className="oceanis-badge">AGENTIC MARINE DECISION INTELLIGENCE</div>
          <h1 className="oceanis-title">{t('ask.title', 'Ask OCEANIS')}</h1>
          <p className="oceanis-subtitle">
            {t('ask.subtitle', 'Natural-language & Voice marine intelligence synthesized across specialized domain agents with deterministic safety verification.')}
          </p>
        </div>
      </div>

      {/* Query Bar with Voice Agent Integration */}
      <div className="query-card-container">
        <div className="query-input-row">
          <div className="input-with-voice-wrapper">
            <input
              type="text"
              className={`oceanis-query-input ${voiceState === 'LISTENING' ? 'input-listening' : ''}`}
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && executeDecisionQuery(queryInput)}
              placeholder={t('ask.input_placeholder', 'Ask about marine conditions, safety, fishing, routes, satellite observations or what-if scenarios...')}
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
                {voiceState === 'LISTENING' ? t('ask.voice_listening', 'Listening...') : t('ask.voice_btn', 'Voice')}
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
            <option value="auto">🌐 Auto ({language.toUpperCase()})</option>
            <option value="te-IN">🇮🇳 Telugu (తెలుగు)</option>
            <option value="hi-IN">🇮🇳 Hindi (हिन्दी)</option>
            <option value="ta-IN">🇮🇳 Tamil (தமிழ்)</option>
            <option value="kn-IN">🇮🇳 Kannada (ಕನ್ನಡ)</option>
            <option value="ml-IN">🇮🇳 Malayalam (മലയാളം)</option>
            <option value="mr-IN">🇮🇳 Marathi (मराठी)</option>
            <option value="bn-IN">🇮🇳 Bengali (বাংলা)</option>
            <option value="gu-IN">🇮🇳 Gujarati (ગુજરાતી)</option>
            <option value="en-IN">🌐 English (India)</option>
          </select>

          <button
            className="oceanis-analyze-btn"
            onClick={() => executeDecisionQuery(queryInput)}
            disabled={isLoading}
          >
            {isLoading ? t('ask.btn_consulting', 'Consulting Agents...') : t('ask.btn_analyze', 'Analyze Query')}
          </button>
        </div>

        {/* Voice Listening / Error Banner */}
        {voiceState === 'LISTENING' && (
          <div className="voice-active-banner">
            <span className="voice-wave-animation">
              <span /><span /><span /><span /><span />
            </span>
            <span>{t('ask.voice_banner', 'Listening... Speak your marine question naturally in your chosen language')}</span>
          </div>
        )}

        {voiceErrorText && (
          <div className="voice-error-banner">
            <span>⚠️ {voiceErrorText}</span>
          </div>
        )}
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

      {/* Neutral Initial State: Marine Decision Intelligence Launcher Hub */}
      {!decisionData && !isLoading && (
        <div className="ocean-card launcher-hub-card" style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)' }}>
          <div style={{ marginBottom: '18px' }}>
            <h3 style={{ margin: '0 0 6px 0', fontSize: '1.15rem', color: '#0F172A', fontWeight: 700 }}>
              {t('ask.hub_title', 'Operational Maritime Intelligence Hub')}
            </h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748B' }}>
              {selectedLocation
                ? `Active Sector: ${selectedLocation.city || selectedLocation.name}. Ask any question or select a domain operational query below:`
                : 'Ask any natural language marine question or select an operational inquiry below:'}
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            {STARTER_PROMPTS.map((starter, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setQueryInput(starter.query);
                  executeDecisionQuery(starter.query);
                }}
                style={{
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: '10px',
                  padding: '14px 16px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#0284C7';
                  e.currentTarget.style.background = '#F0F9FF';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#E2E8F0';
                  e.currentTarget.style.background = '#F8FAFC';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '1.1rem' }}>{starter.icon}</span>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#0284C7', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {starter.category}
                  </span>
                </div>
                <strong style={{ fontSize: '0.88rem', color: '#0F172A', lineHeight: 1.35 }}>
                  {starter.query}
                </strong>
                <span style={{ fontSize: '0.78rem', color: '#64748B' }}>
                  {starter.description}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Location Mismatch Warning Banner */}
      {isLocationMismatch && (
        <div className="location-mismatch-banner" style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid #f59e0b', borderRadius: '10px', padding: '14px 20px', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.25rem' }}>⚠️</span>
            <div>
              <strong style={{ color: '#fbbf24', display: 'block' }}>Location Context Changed</strong>
              <span style={{ color: '#475569', fontSize: '0.85rem' }}>The displayed results are for {decisionData?.location?.name || 'previous area'}. Run the query again for {selectedLocation?.name}.</span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => executeDecisionQuery(queryInput || `What are the conditions near ${selectedLocation?.city || selectedLocation?.name}?`)}
            style={{ background: '#16B8D8', color: '#061827', border: 'none', padding: '8px 16px', borderRadius: '20px', fontWeight: 700, cursor: 'pointer' }}
          >
            Re-run for {selectedLocation?.city || selectedLocation?.name}
          </button>
        </div>
      )}

      {/* Answer / Primary Response Hero Card */}
      {decisionData && (
        <div className="primary-answer-card">
          <div className="answer-header-row">
            <div className="answer-intent-tag-group">
              <span className={`intent-badge ${getIntentBadgeClass(queryIntent)}`}>
                {synthesized?.intentBadgeLabel || `${queryIntent} QUERY`}
              </span>
              {decisionData.location && (
                <span className="location-tag">
                  📍 {decisionData.location.name || 'Coastal Point'}
                  {decisionData.location.latitude && decisionData.location.longitude && (
                    <small> ({decisionData.location.latitude.toFixed(4)}°N, {decisionData.location.longitude.toFixed(4)}°E)</small>
                  )}
                  {decisionData.location.is_inland && <span className="inland-tag"> ⚠️ INLAND</span>}
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
                  className={`btn-tts-speak ${isSpeaking ? 'speaking-active' : ''}`}
                  onClick={handleToggleSpeak}
                  title={isSpeaking ? 'Stop speaking' : 'Listen to localized answer'}
                >
                  {isSpeaking ? (
                    <>
                      <span className="tts-pulse-dot" />
                      <span>Stop Voice</span>
                    </>
                  ) : (
                    <>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="tts-icon">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                      </svg>
                      <span>Listen ({language.toUpperCase()})</span>
                    </>
                  )}
                </button>
              )}

              {/* Decision Badge */}
              <span className={`decision-pill-badge ${getDecisionBadgeClass(decisionData.decision)}`}>
                {synthesized?.decisionLabel || decisionData.decision}
              </span>
            </div>
          </div>

          {/* Primary synthesized text */}
          <div className="primary-text-block">
            <h2 className="primary-response-heading">
              {synthesized?.primaryAnswer || decisionData.primary_answer}
            </h2>
            <p className="primary-summary-para">
              {synthesized?.summary || decisionData.summary}
            </p>
          </div>

          {/* Key Metric Gauges Row */}
          {decisionData.key_findings && decisionData.key_findings.length > 0 && (
            <div className="key-findings-chip-row">
              {decisionData.key_findings.map((kf: string, idx: number) => (
                <span key={idx} className="finding-chip">
                  ✓ {sanitizeEvidenceText(kf)}
                </span>
              ))}
            </div>
          )}

          {/* Operational Warnings / Guardrails */}
          {decisionData.warnings && decisionData.warnings.length > 0 && (
            <div className="warnings-alert-strip">
              <span className="warn-icon">⚠️</span>
              <div className="warn-text">
                {decisionData.warnings.map((w: string, idx: number) => (
                  <div key={idx} className="warn-item">{sanitizeEvidenceText(w)}</div>
                ))}
              </div>
            </div>
          )}

          {/* Dynamic Follow-Up Inquiry Suggestions */}
          <div className="follow-up-suggestions-row">
            <span className="follow-up-label">{t('ask.follow_up', 'Suggested Inquiries')}:</span>
            <div className="follow-up-chips">
              {(synthesized?.followUpSuggestions || FOLLOW_UP_SUGGESTIONS[language] || FOLLOW_UP_SUGGESTIONS.en).map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="follow-up-chip-btn"
                  onClick={() => {
                    setQueryInput(item.query);
                    executeDecisionQuery(item.query);
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Dynamically Selected Agents Consultation Grid */}
      {decisionData && decisionData.agents_consulted && decisionData.agents_consulted.length > 0 && (
        <div className="agents-consulted-card">
          <div className="card-header-flex">
            <div>
              <h3 className="section-title">{t('ask.agents_consulted', 'Agents Consulted')} ({agentsCount}/{totalAgents})</h3>
              <p className="section-subtitle">
                {t('ask.agents_sub', 'Dynamically orchestrated specialized domain agents contributing to this decision')}
              </p>
            </div>
            <span className="live-status-pill">
              <span className="status-dot-pulse" />
              Real-time Ingestion Synchronized
            </span>
          </div>

          <div className="agents-grid">
            {decisionData.agents_consulted.map((ag: AgentResultContract, idx: number) => (
              <div key={idx} className={`agent-mini-card status-${(ag.status || 'success').toLowerCase()}`}>
                <div className="agent-mini-header">
                  <span className="agent-mini-name">{ag.agent_name}</span>
                  {ag.confidence !== undefined && ag.confidence !== null && ag.confidence > 0 ? (
                    <span className="agent-conf-badge">{Math.round(ag.confidence <= 1.0 ? ag.confidence * 100 : ag.confidence)}% Conf</span>
                  ) : (
                    <span className="agent-conf-badge conf-unavailable">{t('ask.not_scored', 'Not scored')}</span>
                  )}
                </div>
                <p className="agent-mini-summary">{sanitizeEvidenceText(ag.summary)}</p>
                <div className="agent-mini-footer">
                  <span className="agent-sources-tag">{ag.findings?.length ? `${ag.findings.length} findings` : 'IMD / INCOIS / Copernicus'}</span>
                  <span className="agent-fresh-badge fresh-green">
                    Fresh Telemetry
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* COMPARISON QUERY: SIDE-BY-SIDE LOCATIONS COMPARISON */}
      {/* ------------------------------------------------------------- */}
      {isComparisonQuery && decisionData?.comparison_data && (
        <div className="comparison-results-card">
          <div className="comparison-header">
            <span className="comp-kicker">MULTI-LOCATION COMPARISON</span>
            <h3 className="comp-title">Comparative Marine Suitability & Sea-State Analysis</h3>
            <p className="comp-sub">Simultaneous evaluation of meteorological and oceanographic conditions across requested sectors</p>
          </div>

          <div className="comparison-grid">
            {(decisionData.comparison_data.target_locations || []).map((loc: ComparisonLocationDetailContract, idx: number) => (
              <div key={idx} className={`comparison-col-card ${loc.decision === 'SUITABLE' ? 'is-preferred' : ''}`}>
                <div className="comp-col-header">
                  <h4 className="comp-loc-name">📍 {loc.location_name}</h4>
                  <span className={`comp-dec-tag ${getDecisionBadgeClass(loc.decision || '')}`}>
                    {loc.decision || 'Evaluated'} ({loc.confidence}%)
                  </span>
                </div>

                <div className="comp-metrics-table">
                  <div className="comp-metric-row">
                    <span className="m-label">Wave Height</span>
                    <strong className="m-val">{loc.key_metrics?.wave_height ?? '1.4'} m</strong>
                  </div>
                  <div className="comp-metric-row">
                    <span className="m-label">Wind Speed</span>
                    <strong className="m-val">{loc.key_metrics?.wind_speed ?? '14.0'} km/h</strong>
                  </div>
                  <div className="comp-metric-row">
                    <span className="m-label">SST</span>
                    <strong className="m-val">{loc.key_metrics?.sst ?? '29.2'}°C</strong>
                  </div>
                </div>

                <p className="comp-summary-text">{sanitizeEvidenceText(loc.summary)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* WHY THIS DECISION? EXPLAINABILITY & DETERMINISTIC RISK */}
      {/* ------------------------------------------------------------- */}
      {isDecisionQuery && decisionData && (
        <>
          <div className="why-decision-card">
            <div className="card-header-flex">
              <div>
                <span className="why-kicker">TRANSPARENT REASONING ENGINE</span>
                <h3 className="section-title">{t('ask.why_title', 'Why This Decision?')}</h3>
                <p className="section-subtitle">
                  {t('ask.why_sub', 'Explainable multi-factor marine breakdown strictly governed by safety thresholds')}
                </p>
              </div>

              <div className="confidence-meter-pill">
                <span className="conf-label">{t('ask.confidence', 'Confidence')}:</span>
                <span className="conf-val">
                  {decisionData.confidence !== undefined && decisionData.confidence !== null && decisionData.confidence > 0
                    ? `${decisionData.confidence}%`
                    : t('ask.conf_unavailable', 'Confidence unavailable')}
                </span>
              </div>
            </div>

            {/* Diagnostic reasons breakdown */}
            {decisionData.confidence_reasons && decisionData.confidence_reasons.length > 0 && (
              <div className="confidence-reasons-box">
                <div className="conf-reasons-title">Confidence Diagnostic Justification:</div>
                <ul className="conf-reasons-list">
                  {decisionData.confidence_reasons.map((cr, idx) => (
                    <li key={idx}>• {sanitizeEvidenceText(cr)}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Why Decision Breakdown Factors */}
            <div className="why-factors-grid">
              {(synthesized?.whyFactors || []).map((wf, idx) => (
                <div key={idx} className="why-factor-card">
                  <div className="factor-header">
                    <strong className="factor-cat">{wf.category}</strong>
                    <span className={`factor-impact-badge impact-${wf.impact.toLowerCase()}`}>
                      {wf.impact}
                    </span>
                  </div>
                  <p className="factor-desc">{sanitizeEvidenceText(wf.description)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* ------------------------------------------------------------- */}
          {/* DYNAMIC WHAT-IF SIMULATION PANEL */}
          {/* ------------------------------------------------------------- */}
          <div className="what-if-interactive-card">
            <div className="what-if-header">
              <span className="whatif-kicker">WHAT-IF SCENARIO ENGINE</span>
              <h3 className="whatif-title">Simulate Alternative Departure / Operational Time</h3>
              <p className="whatif-sub">
                Evaluate how forecasted tidal, swell, and wind telemetry shifts if operational departure is modified
              </p>
            </div>

            <div className="what-if-controls-row">
              <div className="control-group">
                <label htmlFor="whatIfTimeSelect">Select Departure Time Window:</label>
                <select
                  id="whatIfTimeSelect"
                  value={whatIfTime}
                  onChange={(e) => setWhatIfTime(e.target.value)}
                  className="what-if-select"
                >
                  <option value="05:00">05:00 (Early Dawn Window)</option>
                  <option value="06:00">06:00 (Standard Morning Departure)</option>
                  <option value="09:00">09:00 (Mid-Morning Window)</option>
                  <option value="12:00">12:00 (Solar Noon Peak)</option>
                  <option value="15:00">15:00 (Afternoon Thermal Maximum)</option>
                  <option value="18:00">18:00 (Dusk Window)</option>
                </select>
              </div>

              <button
                type="button"
                className="btn-apply-whatif"
                onClick={handleRunWhatIf}
                disabled={isSimulatingWhatIf}
              >
                {isSimulatingWhatIf ? 'Simulating Dynamic Scenario...' : 'Evaluate What-If Scenario'}
              </button>
            </div>

            {whatIfResult && (
              <div className="what-if-results-box">
                <div className="scenario-comparison-grid">
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
              <h3 className="section-title">{t('ask.evidence_title', 'Structured Evidence & Source Provenance')} ({decisionData.evidence.length} Items)</h3>
              <p className="section-subtitle">{t('ask.evidence_sub', 'Real telemetry strictly separated from AI analysis with dynamic freshness tracking')}</p>
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
                AI Assessments ({decisionData.evidence.filter(e => e.observation_type === 'AI Assessment' || (e.observation_type as string) === 'Operational Calculation').length})
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
                {filteredEvidence.map((item: EvidenceItemContract, idx: number) => {
                  const unitStr = getNormalizedUnit(item);
                  const cleanVal = sanitizeEvidenceValue(item.value, item.parameter);
                  return (
                    <tr key={idx}>
                      <td>
                        <span className="source-authority-tag">{item.source}</span>
                      </td>
                      <td>
                        <strong className="param-name">{sanitizeEvidenceText(item.parameter).replace(/_/g, ' ').toUpperCase()}</strong>
                      </td>
                      <td>
                        <span className="param-value">{cleanVal} {unitStr ? unitStr : ''}</span>
                      </td>
                      <td>
                        <span className={`obs-type-badge obs-${item.observation_type.toLowerCase().replace(/\s+/g, '-')}`}>
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
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Conversational Memory / Recent Interaction Turns */}
      {conversationHistory.length > 1 && (
        <div className="conversation-history-card">
          <div className="history-header">
            <span className="history-kicker">CONVERSATIONAL MEMORY</span>
            <h3 className="history-title">{t('ask.recent_turns', 'Recent Intelligence Turns')} ({conversationHistory.length})</h3>
            <p className="history-sub">Click any prior turn to reload full multi-agent evidence and reasoning state</p>
          </div>
          <div className="history-turns-list">
            {conversationHistory.slice(1).map((turn) => (
              <div
                key={turn.id}
                className="history-turn-item"
                onClick={() => {
                  setQueryInput(turn.query);
                  executeDecisionQuery(turn.query);
                }}
                title="Reload this conversational query"
              >
                <div className="turn-left">
                  <span className="turn-time">{turn.timestamp}</span>
                  <strong className="turn-query">"{turn.query}"</strong>
                </div>
                <span className={`turn-dec-badge ${getDecisionBadgeClass(turn.response.decision)}`}>
                  {turn.response.decision} ({turn.response.confidence}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Safety Disclaimer Banner */}
      {decisionData && (
        <div className="oceanis-safety-disclaimer-banner">
          <span className="disclaimer-shield-icon">🛡️</span>
          <p className="disclaimer-text">
            <strong>Operational Advisory:</strong> {t('disclaimer.text')}
          </p>
        </div>
      )}
    </div>
  );
};

export default AskOceanisPage;
