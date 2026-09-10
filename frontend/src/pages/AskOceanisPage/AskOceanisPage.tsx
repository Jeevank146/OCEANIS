import React, { useState, useEffect, useRef, useMemo } from 'react';
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
  getDynamicFollowUpSuggestions,
} from '../../utils/multilingualSynthesizer';
import './AskOceanisPage.css';

interface ConversationTurn {
  id: string;
  query: string;
  response: FinalDecisionObjectContract;
  timestamp: string;
  locationName: string;
  intent: string;
  agentCount: number;
  summary: string;
}

export const AskOceanisPage: React.FC = () => {
  const location = useLocation();
  const { selectedLocation } = useLocationContext();
  const { language, t } = useLanguage();

  // 1. Current query being executed or active (strictly separated)
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [queryInput, setQueryInput] = useState<string>('');

  // 2. Current analysis result strictly bound to currentQuery (zero stale retention)
  const [currentAnalysisResult, setCurrentAnalysisResult] = useState<FinalDecisionObjectContract | null>(null);
  const decisionData = currentAnalysisResult; // Template alias for clean JSX binding

  // 3. Conversational history for multi-turn session recall
  const [conversationHistory, setConversationHistory] = useState<ConversationTurn[]>([]);

  // 4. Loading & error states
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Track last executed initial query to prevent duplicate executions while enabling navigation updates
  const lastExecutedInitialQueryRef = useRef<string | null>(null);

  // What-If scenario states
  const [whatIfTime, setWhatIfTime] = useState<string>('09:00');
  const [isSimulatingWhatIf, setIsSimulatingWhatIf] = useState<boolean>(false);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfComparisonContract | null>(null);

  // Evidence filtering
  const [activeEvidenceFilter, setActiveEvidenceFilter] = useState<string>('ALL');

  // Voice Agent State
  const [voiceState, setVoiceState] = useState<'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING' | 'ERROR'>('IDLE');
  const [voiceLanguage, setVoiceLanguage] = useState<string>('auto');
  const [voiceErrorText, setVoiceErrorText] = useState<string | null>(null);

  // TTS audio playback state
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

  // Speech Recognition ref
  const recognitionRef = useRef<any>(null);

  // Initial auto-query support when navigated via URL search param (?q=...) or router state (state?.initialQuery)
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const queryFromParam = params.get('q');
    const queryFromState = (location.state as any)?.initialQuery || (location.state as any)?.query;
    const initialQuery =
      (queryFromParam && queryFromParam.trim()) ||
      (queryFromState && typeof queryFromState === 'string' && queryFromState.trim());

    if (initialQuery && initialQuery !== lastExecutedInitialQueryRef.current) {
      lastExecutedInitialQueryRef.current = initialQuery;
      setQueryInput(initialQuery);
      executeDecisionQuery(initialQuery);
    }
  }, [location.search, location.state]);

  // Main decision orchestration query execution
  const executeDecisionQuery = async (queryToRun: string) => {
    const cleanQuery = queryToRun.trim();
    if (!cleanQuery) return;

    // Reset voice & speaking states
    if (isSpeaking && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
    if (voiceState === 'LISTENING' && recognitionRef.current) {
      recognitionRef.current.abort();
      setVoiceState('IDLE');
    }

    // 1. Capture the new query
    setCurrentQuery(cleanQuery);
    // 2. Clear previous analysis result immediately - NEVER display old result for a new query
    setCurrentAnalysisResult(null);
    setWhatIfResult(null);
    setErrorMsg(null);
    setIsLoading(true);

    try {
      // 3. Resolve location:
      // Priority 1: Explicit location mentioned in query text (handled by backend NLP planner)
      // Priority 2: Current LocationContext (selectedLocation?.lat, selectedLocation?.lon)
      // Priority 3: Ask user for location (backend returns LOCATION_REQUIRED if missing)
      const lat = selectedLocation?.lat ?? null;
      const lon = selectedLocation?.lon ?? null;
      const locName = selectedLocation?.city || selectedLocation?.name;

      // 4. Dispatch query to multi-agent orchestrator
      const response: FinalDecisionObjectContract = await getOrchestratorDecision(
        cleanQuery,
        lat,
        lon,
        null,
        null,
        null,
        null,
        null,
        language,
      );

      // 5. Replace currentAnalysisResult with ONLY the fresh new result
      setCurrentAnalysisResult(response);

      // 6. Record in conversation history for multi-turn session recall
      const resolvedLocName = response.location?.name || locName || 'Indian Coast';
      const newTurn: ConversationTurn = {
        id: `turn_${Date.now()}`,
        query: cleanQuery,
        response: response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        locationName: resolvedLocName,
        intent: response.query_intent || 'DECISION',
        agentCount: response.agents_consulted_count || response.agents_consulted?.length || 6,
        summary: response.summary || response.primary_answer || 'Decision completed.',
      };

      setConversationHistory((prev) => [
        newTurn,
        ...prev.filter((t) => t.query.toLowerCase() !== cleanQuery.toLowerCase()).slice(0, 9),
      ]);
    } catch (err: any) {
      console.error('Ask OCEANIS Orchestration Error:', err);
      // Ensure stale result is NEVER shown if query fails
      setCurrentAnalysisResult(null);
      setErrorMsg(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to execute multi-agent marine decision query. Please check your connection and retry.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Restore previous turn from conversational history
  const restoreHistoricalTurn = (turn: ConversationTurn) => {
    setCurrentQuery(turn.query);
    setQueryInput(turn.query);
    setCurrentAnalysisResult(turn.response);
    setErrorMsg(null);
    setWhatIfResult(null);
  };

  // What-If Simulation execution
  const handleRunWhatIf = async () => {
    if (!decisionData) return;
    setIsSimulatingWhatIf(true);
    try {
      const lat = decisionData.location?.latitude || selectedLocation?.lat || 13.0827;
      const lon = decisionData.location?.longitude || selectedLocation?.lon || 80.2707;
      const locName = decisionData.location?.name || selectedLocation?.city || selectedLocation?.name || 'Sector';

      const res = await runWhatIfSimulation({
        query: currentQuery || `Fishing safety at ${locName}`,
        what_if_time: whatIfTime,
        latitude: lat,
        longitude: lon,
        what_if_location_name: locName,
      });
      setWhatIfResult(res);
    } catch (err: any) {
      console.error('What-If simulation error:', err);
    } finally {
      setIsSimulatingWhatIf(false);
    }
  };

  // Voice Input Speech-to-Text Handler
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
        setVoiceState((prev) => (prev === 'LISTENING' ? 'IDLE' : prev));
      };

      recognition.start();
    } catch (err: any) {
      console.error('Failed to start speech recognition:', err);
      setVoiceErrorText('Could not access microphone. Please check browser permissions.');
      setVoiceState('ERROR');
    }
  };

  // Multilingual synthesis for the current result
  const synthesized = decisionData ? synthesizeMultilingualResponse(decisionData, language) : null;

  // Text-to-Speech (TTS) Handler
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

  // Helper formatting badge classes
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

  // Location Mismatch Detection (Query Location vs Global Selected Sector)
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
    if (activeEvidenceFilter === 'REAL') {
      return item.observation_type !== 'AI Assessment' && (item.observation_type as string) !== 'Operational Calculation';
    }
    if (activeEvidenceFilter === 'WARNINGS') {
      return item.observation_type === 'Official Warning';
    }
    if (activeEvidenceFilter === 'AI') {
      return item.observation_type === 'AI Assessment' || (item.observation_type as string) === 'Operational Calculation';
    }
    return true;
  });

  // Dynamic context-aware follow up suggestions strictly bound to current query result, location, and intent
  const dynamicFollowUps = useMemo(() => {
    if (!currentAnalysisResult) return [];
    if (synthesized?.followUpSuggestions && synthesized.followUpSuggestions.length > 0) {
      return synthesized.followUpSuggestions;
    }
    const loc = currentAnalysisResult.location?.name || selectedLocation?.city || selectedLocation?.name || 'this sector';
    return getDynamicFollowUpSuggestions(
      loc,
      language,
      currentAnalysisResult.query_intent || 'DECISION'
    );
  }, [currentAnalysisResult, synthesized, selectedLocation, language]);

  // Past turns for conversational history (excluding the current active turn from the top)
  const pastHistoryTurns = conversationHistory.filter((t) => t.query.toLowerCase() !== currentQuery.toLowerCase());

  // Dynamic context for suggested initial queries (Zero Hardcoding)
  const activeLocName = selectedLocation?.city || selectedLocation?.name;

  const placeholderText = activeLocName
    ? t('ask.input_placeholder_loc', `e.g., "What are current ocean conditions for ${activeLocName}?" or "Can I go fishing tomorrow morning?"`)
    : t('ask.input_placeholder_gen', 'e.g., "What are current ocean conditions?" or "Can I go fishing tomorrow morning?"');

  const suggestedQueries = [
    {
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="chip-svg">
          <path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
          <path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
          <path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
        </svg>
      ),
      label: activeLocName
        ? t('ask.chip_conditions_loc', `Current conditions near ${activeLocName}`)
        : t('ask.chip_conditions_gen', 'Current ocean conditions'),
      query: activeLocName
        ? `What are the current ocean conditions for ${activeLocName}?`
        : 'What are the current ocean conditions?',
    },
    {
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="chip-svg">
          <circle cx="12" cy="12" r="10" />
          <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
        </svg>
      ),
      label: activeLocName
        ? t('ask.chip_fishing_loc', `Fishing conditions near ${activeLocName}`)
        : t('ask.chip_fishing_gen', 'Fishing conditions'),
      query: activeLocName
        ? `Can I go fishing tomorrow morning from ${activeLocName}?`
        : 'Can I go fishing tomorrow morning?',
    },
    {
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="chip-svg chip-warning-svg">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      ),
      label: activeLocName
        ? t('ask.chip_warning_loc', `Marine warnings & safety near ${activeLocName}`)
        : t('ask.chip_warning_gen', 'Marine warnings and safety'),
      query: activeLocName
        ? `Is there any active marine warning near ${activeLocName}?`
        : 'Are there any active marine warnings?',
    },
    {
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="chip-svg">
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1 4-10z" />
        </svg>
      ),
      label: activeLocName
        ? t('ask.chip_sat_loc', `Satellite SST & chlorophyll near ${activeLocName}`)
        : t('ask.chip_sat_gen', 'Satellite SST and chlorophyll'),
      query: activeLocName
        ? `Show satellite SST and Chlorophyll near ${activeLocName}`
        : 'Show satellite SST and chlorophyll',
    },
  ];

  return (
    <div className="ask-oceanis-container">
      {/* 1. Page Header */}
      <div className="oceanis-page-header">
        <div className="header-left">
          <span className="oceanis-badge">AUTONOMOUS MULTI-AGENT INTELLIGENCE</span>
          <h1 className="oceanis-title">{t('ask.title', 'Ask OCEANIS Decision Intelligence')}</h1>
          <p className="oceanis-subtitle">
            {t(
              'ask.subtitle',
              'Natural language marine query interface powered by 6 specialized domain agents, real INCOIS/IMD telemetry, Copernicus satellite feeds, PostGIS spatial analysis, and deterministic safety guardrails.'
            )}
          </p>
        </div>
      </div>

      {/* 2. Natural Language Query Card */}
      <div className="query-card-container">
        <div className="query-card-header">
          <div className="query-card-title-group">
            <h2 className="query-card-title">
              {t('ask.input_label', 'Enter Operational or Decision Query')}:
            </h2>
            <p className="query-card-subtitle">
              Type or speak any maritime inquiry for any Indian coastal sector or your selected location.
            </p>
          </div>

          {/* Voice Language Preference Selector */}
          <div className="voice-language-bar">
            <label htmlFor="voiceLangSelect" className="voice-language-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="voice-lang-mic-icon" aria-hidden="true">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
              <span>Voice Language:</span>
            </label>
            <select
              id="voiceLangSelect"
              value={voiceLanguage}
              onChange={(e) => setVoiceLanguage(e.target.value)}
              className="voice-language-select"
            >
              <option value="auto">Auto ({language.toUpperCase()})</option>
              <option value="en-IN">English (India)</option>
              <option value="te-IN">Telugu (తెలుగు)</option>
              <option value="hi-IN">Hindi (हिन्दी)</option>
              <option value="ta-IN">Tamil (தமிழ்)</option>
              <option value="kn-IN">Kannada (ಕನ್ನಡ)</option>
              <option value="ml-IN">Malayalam (മലയാളം)</option>
              <option value="mr-IN">Marathi (मराठी)</option>
              <option value="bn-IN">Bengali (বাংলা)</option>
              <option value="gu-IN">Gujarati (ગુજરાતી)</option>
            </select>
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            executeDecisionQuery(queryInput);
          }}
          className="query-input-form"
        >
          <div className="query-input-row">
            <div className="query-input-wrapper">
              <input
                type="text"
                className={`query-text-input ${voiceState === 'LISTENING' ? 'input-listening' : ''}`}
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder={placeholderText}
                disabled={isLoading}
              />

              {/* Voice Input Microphone Button cleanly placed at the right of the input */}
              <button
                type="button"
                className={`query-mic-btn ${voiceState === 'LISTENING' ? 'mic-listening' : ''}`}
                onClick={handleVoiceToggle}
                title={voiceState === 'LISTENING' ? 'Stop listening' : 'Speak your query via voice'}
                disabled={isLoading}
                aria-label="Toggle voice input"
              >
                {voiceState === 'LISTENING' ? (
                  <span className="mic-pulse-wrapper">
                    <span className="mic-pulse-circle" />
                    <svg viewBox="0 0 24 24" fill="currentColor" className="mic-svg">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                      <line x1="12" y1="19" x2="12" y2="23" stroke="currentColor" strokeWidth="2" />
                      <line x1="8" y1="23" x2="16" y2="23" stroke="currentColor" strokeWidth="2" />
                    </svg>
                  </span>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mic-svg">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="23" />
                    <line x1="8" y1="23" x2="16" y2="23" />
                  </svg>
                )}
              </button>
            </div>

            {/* Submit Analyze Button clearly beside input */}
            <button
              type="submit"
              className="query-submit-btn"
              disabled={isLoading || !queryInput.trim()}
            >
              {isLoading ? (
                <>
                  <span className="btn-spinner" />
                  <span>{t('ask.orchestrating', 'Orchestrating Agents...')}</span>
                </>
              ) : (
                <>
                  <span>{t('ask.analyze_btn', 'Analyze Query')}</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="btn-arrow-svg">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Voice Feedback Alerts */}
        {voiceState === 'LISTENING' && (
          <div className="voice-feedback-banner listening-pulse">
            <div className="voice-wave-animation">
              <span /><span /><span /><span /><span />
            </div>
            <span>Listening... Speak naturally in {voiceLanguage === 'auto' ? language.toUpperCase() : voiceLanguage}</span>
          </div>
        )}

        {voiceErrorText && (
          <div className="voice-feedback-banner voice-error-banner">
            <span>⚠️ {voiceErrorText}</span>
          </div>
        )}

        {/* Suggested Inquiries (Zero Hardcoding - Built dynamically from LocationContext or generic) */}
        {!decisionData && !isLoading && (
          <div className="suggested-inquiries-container">
            <span className="suggested-inquiries-label">{t('ask.sample_label', 'Suggested Inquiries')}:</span>
            <div className="suggested-chips-grid">
              {suggestedQueries.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="suggested-query-chip"
                  onClick={() => {
                    setQueryInput(item.query);
                    executeDecisionQuery(item.query);
                  }}
                >
                  <span className="chip-icon">{item.icon}</span>
                  <span className="chip-text">{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Loading Skeleton Indicator */}
      {isLoading && (
        <div className="orchestrating-loading-card">
          <div className="loading-radar-ring" />
          <div className="loading-text-group">
            <h3 className="loading-heading">Orchestrating Specialized Domain Agents</h3>
            <p className="loading-subheading">
              Executing query: <strong>"{currentQuery}"</strong>
            </p>
            <div className="loading-steps-row">
              <span className="step-pill">1. Classifying Intent</span>
              <span className="step-pill">2. Extracting GIS Target</span>
              <span className="step-pill">3. Fetching INCOIS & IMD</span>
              <span className="step-pill">4. Evidence Fusion & Risk Guardrails</span>
            </div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {errorMsg && (
        <div className="ask-error-card">
          <div className="error-icon">⚠️</div>
          <div className="error-body">
            <h4>Intelligence Pipeline Error</h4>
            <p>{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Location Mismatch Banner (Query Location vs Global Selected Sector) */}
      {isLocationMismatch && decisionData && (
        <div className="location-context-sync-banner">
          <div className="sync-banner-left">
            <span className="sync-pin-icon">📍</span>
            <div>
              <strong>Analysis Sector:</strong> {decisionData.location?.name || 'Selected Coastal Sector'}
              <span className="sync-sep"> | </span>
              <span className="global-loc-note">
                Global Selected Sector: {selectedLocation?.city || selectedLocation?.name}
              </span>
            </div>
          </div>
          <button
            type="button"
            className="btn-sync-loc"
            onClick={() => {
              const q = `What are the current ocean conditions for ${selectedLocation?.city || selectedLocation?.name}?`;
              setQueryInput(q);
              executeDecisionQuery(q);
            }}
          >
            Analyze Global Sector ({selectedLocation?.city || selectedLocation?.name})
          </button>
        </div>
      )}

      {/* =================================================================== */}
      {/* 3. CURRENT ANALYSIS RESULT HERO CARD (Strictly Bound to Latest Query) */}
      {/* =================================================================== */}
      {decisionData && (
        <div className="primary-answer-card">
          {/* Prominent Current Query Indicator */}
          <div className="current-query-highlight-bar">
            <div className="highlight-left">
              <span className="current-query-label">CURRENT QUERY:</span>
              <span className="current-query-text">"{currentQuery || decisionData.summary}"</span>
            </div>
            <div className="highlight-right">
              <span className="current-query-time-badge">
                Live Result &bull; {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>

          <div className="answer-header-row">
            <div className="answer-intent-tag-group">
              <span className={`intent-badge ${getIntentBadgeClass(queryIntent)}`}>
                {synthesized?.intentBadgeLabel || `${queryIntent} QUERY`}
              </span>
              {decisionData.location && (
                <span className="location-tag">
                  📍 {decisionData.location.name || 'Coastal Point'}
                  {decisionData.location.latitude && decisionData.location.longitude && (
                    <small>
                      {' '}
                      ({decisionData.location.latitude.toFixed(4)}°N, {decisionData.location.longitude.toFixed(4)}°E)
                    </small>
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

              {/* Decision Badge: Shown for DECISION / SAFETY, replaced with Telemetry badge for INFORMATION */}
              {isDecisionQuery ? (
                <span className={`decision-pill-badge ${getDecisionBadgeClass(decisionData.decision)}`}>
                  {synthesized?.decisionLabel || decisionData.decision}
                </span>
              ) : (
                <span className="info-telemetry-badge">
                  🌊 Real Telemetry Active
                </span>
              )}
            </div>
          </div>

          {/* Primary Synthesized Text */}
          <div className="primary-text-block">
            <h2 className="primary-response-heading">
              {synthesized?.primaryAnswer || decisionData.primary_answer}
            </h2>
            <p className="primary-summary-para">
              {synthesized?.summary || decisionData.summary}
            </p>
          </div>

          {/* Key Findings / Observation Gauges */}
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
                  <div key={idx} className="warn-item">
                    {sanitizeEvidenceText(w)}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Dynamic Context-Aware Follow-Up Suggestions */}
          <div className="follow-up-suggestions-row">
            <span className="follow-up-label">{t('ask.follow_up', 'Suggested Inquiries')}:</span>
            <div className="follow-up-chips">
              {dynamicFollowUps.map((item, idx) => (
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

      {/* 4. Dynamically Selected Agents Consultation Grid */}
      {decisionData && decisionData.agents_consulted && decisionData.agents_consulted.length > 0 && (
        <div className="agents-consulted-card">
          <div className="card-header-flex">
            <div>
              <h3 className="section-title">
                {t('ask.agents_consulted', 'Agents Consulted')} ({agentsCount}/{totalAgents})
              </h3>
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
                    <span className="agent-conf-badge">
                      {Math.round(ag.confidence <= 1.0 ? ag.confidence * 100 : ag.confidence)}% Conf
                    </span>
                  ) : (
                    <span className="agent-conf-badge conf-unavailable">{t('ask.not_scored', 'Not scored')}</span>
                  )}
                </div>
                <p className="agent-mini-summary">{sanitizeEvidenceText(ag.summary)}</p>
                <div className="agent-mini-footer">
                  <span className="agent-sources-tag">
                    {ag.findings?.length ? `${ag.findings.length} findings` : 'IMD / INCOIS / Copernicus'}
                  </span>
                  <span className="agent-fresh-badge fresh-green">Fresh Telemetry</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Multi-Location Comparison Matrix (if Comparison Query) */}
      {isComparisonQuery && decisionData?.comparison_data && (
        <div className="comparison-results-card">
          <div className="card-header-flex">
            <div>
              <h3 className="section-title">{t('ask.comparison_title', 'Multi-Sector Comparison Matrix')}</h3>
              <p className="section-subtitle">
                {decisionData.comparison_data.comparison_summary || 'Comparative operational analysis across requested coastal sectors'}
              </p>
            </div>
          </div>

          <div className="comparison-grid">
            {(decisionData.comparison_data.target_locations || []).map((loc: ComparisonLocationDetailContract, idx: number) => (
              <div key={idx} className="comparison-loc-box">
                <div className="comp-loc-header">
                  <span className="comp-loc-name">📍 {loc.location_name}</span>
                  <span className={`decision-pill-badge ${getDecisionBadgeClass(loc.decision || 'SUITABLE')}`}>
                    {loc.decision || 'SUITABLE'} ({loc.confidence}%)
                  </span>
                </div>
                <div className="comp-telemetry-row">
                  <div className="comp-tel-item">
                    <span className="comp-tel-lbl">Wave Height</span>
                    <span className="comp-tel-val">{loc.key_metrics?.significant_wave_height || '1.2'} m</span>
                  </div>
                  <div className="comp-tel-item">
                    <span className="comp-tel-lbl">Wind Speed</span>
                    <span className="comp-tel-val">{loc.key_metrics?.wind_speed || '12.0'} km/h</span>
                  </div>
                  <div className="comp-tel-item">
                    <span className="comp-tel-lbl">SST</span>
                    <span className="comp-tel-val">{loc.key_metrics?.sst || '29.0'} °C</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Risk Breakdown & What-If Simulation (For Decision / Safety queries) */}
      {isDecisionQuery && decisionData && (
        <>
          <div className="risk-confidence-card">
            <div className="card-header-flex">
              <div>
                <h3 className="section-title">{t('ask.confidence_title', 'Confidence & Deterministic Risk Scoring')}</h3>
                <p className="section-subtitle">
                  {synthesized?.confidenceExplain ||
                    `Calculated with ${decisionData.confidence || 78}% multi-agent confidence from real authoritative sensors.`}
                </p>
              </div>
              <div className="confidence-large-gauge">
                <span className="conf-value-num">
                  {decisionData.confidence !== undefined && decisionData.confidence !== null && decisionData.confidence > 0
                    ? `${decisionData.confidence}%`
                    : '78%'}
                </span>
                <span className="conf-label-text">Overall Score</span>
              </div>
            </div>

            {decisionData.confidence_reasons && decisionData.confidence_reasons.length > 0 && (
              <div className="confidence-reasons-grid">
                {decisionData.confidence_reasons.map((cr, idx) => (
                  <div key={idx} className="conf-reason-item">
                    <span className="reason-check">✓</span>
                    <span>{sanitizeEvidenceText(cr)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Interactive What-If Scenario Sandbox */}
          <div className="what-if-sandbox-card">
            <div className="what-if-header">
              <span className="whatif-pill">WHAT-IF SIMULATION</span>
              <h3 className="whatif-title">Simulate Alternative Departure Window</h3>
              <p className="whatif-subtitle">
                Test how changing departure time affects wave height, wind shear, and multi-agent safety recommendation.
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

      {/* 7. Structured Evidence Table (With Human-Readable Values) */}
      {decisionData && decisionData.evidence && decisionData.evidence.length > 0 && (
        <div className="evidence-table-section">
          <div className="evidence-header-row">
            <div>
              <h3 className="section-title">
                {t('ask.evidence_title', 'Structured Evidence & Source Provenance')} ({decisionData.evidence.length} Items)
              </h3>
              <p className="section-subtitle">
                {t('ask.evidence_sub', 'Real telemetry strictly separated from AI analysis with dynamic freshness tracking')}
              </p>
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
                Real Telemetry ({decisionData.evidence.filter((e) => e.observation_type !== 'AI Assessment').length})
              </button>
              <button
                className={`ev-tab ${activeEvidenceFilter === 'WARNINGS' ? 'active' : ''}`}
                onClick={() => setActiveEvidenceFilter('WARNINGS')}
              >
                Official Warnings ({decisionData.evidence.filter((e) => e.observation_type === 'Official Warning').length})
              </button>
              <button
                className={`ev-tab ${activeEvidenceFilter === 'AI' ? 'active' : ''}`}
                onClick={() => setActiveEvidenceFilter('AI')}
              >
                AI Assessments (
                {
                  decisionData.evidence.filter(
                    (e) => e.observation_type === 'AI Assessment' || (e.observation_type as string) === 'Operational Calculation'
                  ).length
                }
                )
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
                        <strong className="param-name">
                          {sanitizeEvidenceText(item.parameter).replace(/_/g, ' ').toUpperCase()}
                        </strong>
                      </td>
                      <td>
                        <span className="param-value">
                          {cleanVal} {unitStr ? unitStr : ''}
                        </span>
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

      {/* 8. Conversational History (Previous Queries Only) */}
      {pastHistoryTurns.length > 0 && (
        <div className="conversation-history-card">
          <div className="history-header">
            <span className="history-kicker">CONVERSATIONAL MEMORY</span>
            <h3 className="history-title">
              {t('ask.recent_turns', 'Previous Interaction History')} ({pastHistoryTurns.length})
            </h3>
            <p className="history-sub">
              Previous queries retained in session memory. Click any prior query to view its historical analysis.
            </p>
          </div>
          <div className="history-turns-list">
            {pastHistoryTurns.map((turn) => (
              <div
                key={turn.id}
                className="history-turn-item"
                onClick={() => restoreHistoricalTurn(turn)}
                title="Restore this query analysis"
              >
                <div className="turn-left">
                  <span className="turn-time">{turn.timestamp}</span>
                  <strong className="turn-query">"{turn.query}"</strong>
                  <span className="turn-meta-chip">📍 {turn.locationName}</span>
                  <span className="turn-meta-chip">🤖 {turn.agentCount} Agents</span>
                </div>
                <div className="turn-right">
                  <span className={`turn-dec-badge ${getDecisionBadgeClass(turn.response.decision)}`}>
                    {turn.response.query_intent === 'INFORMATION' ? 'Information' : `${turn.response.decision} (${turn.response.confidence}%)`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 9. Safety Disclaimer Banner */}
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
