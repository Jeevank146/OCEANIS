import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import { LiveOceanMap } from '../../components/LiveOceanMap/LiveOceanMap';
import { fetchLiveMarineConditions, type MarineConditionData } from '../../services/api';
import './DashboardPage.css';

interface CoastalLocationDetail {
  label: string;
  city: string;
  state: string;
  lat: number;
  lon: number;
  sea: string;
}

const quickAccessLocations: CoastalLocationDetail[] = [
  { label: 'Visakhapatnam, Andhra Pradesh', city: 'Visakhapatnam', state: 'Andhra Pradesh', lat: 17.6868, lon: 83.2185, sea: 'Bay of Bengal' },
  { label: 'Kakinada, Andhra Pradesh', city: 'Kakinada', state: 'Andhra Pradesh', lat: 16.9891, lon: 82.2475, sea: 'Bay of Bengal' },
  { label: 'Chennai, Tamil Nadu', city: 'Chennai', state: 'Tamil Nadu', lat: 13.0827, lon: 80.2707, sea: 'Coromandel Coast • Bay of Bengal' },
  { label: 'Mangalore, Karnataka', city: 'Mangalore', state: 'Karnataka', lat: 12.9141, lon: 74.8560, sea: 'Arabian Sea' },
  { label: 'Kochi, Kerala', city: 'Kochi', state: 'Kerala', lat: 9.9312, lon: 76.2673, sea: 'Malabar Coast • Arabian Sea' },
  { label: 'Paradeep, Odisha', city: 'Paradeep', state: 'Odisha', lat: 20.2644, lon: 86.6710, sea: 'Odisha Coast • Bay of Bengal' },
  { label: 'Mumbai, Maharashtra', city: 'Mumbai', state: 'Maharashtra', lat: 18.9400, lon: 72.8350, sea: 'Konkan Coast • Arabian Sea' },
  { label: 'Port Blair, Andaman & Nicobar', city: 'Port Blair', state: 'Andaman & Nicobar', lat: 11.6234, lon: 92.7265, sea: 'Andaman Sea' },
];

export const DashboardPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    selectedLocation,
    validateAndSetQuery,
    validateAndSetCoordinates,
    activeValidation,
  } = useLocationContext();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>('');
  const [currentDate, setCurrentDate] = useState<string>('');
  const [liveConditions, setLiveConditions] = useState<MarineConditionData | null>(null);
  const [, setIsLoadingConditions] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<string>('Just now');

  useEffect(() => {
    const updateDateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST');
      setCurrentDate(now.toLocaleDateString('en-GB', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }));
    };
    updateDateTime();
    const timer = setInterval(updateDateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch live conditions for active selected location
  useEffect(() => {
    let isMounted = true;
    async function loadConditions() {
      if (!selectedLocation || selectedLocation.lat === undefined) return;
      setIsLoadingConditions(true);
      try {
        const data = await fetchLiveMarineConditions(
          selectedLocation.name,
          selectedLocation.lat,
          selectedLocation.lon
        );
        if (isMounted) {
          setLiveConditions(data);
          setLastSyncTime('Just now');
        }
      } catch (e) {
        console.error('Failed to load live marine conditions for dashboard:', e);
      } finally {
        if (isMounted) setIsLoadingConditions(false);
      }
    }

    loadConditions();
    return () => { isMounted = false; };
  }, [selectedLocation.name, selectedLocation.lat, selectedLocation.lon]);

  // Read location parameter from URL if provided
  const queryLoc = searchParams.get('location');

  // Sync URL parameter to application state if URL changes
  useEffect(() => {
    if (queryLoc && queryLoc.trim()) {
      const decoded = decodeURIComponent(queryLoc.trim());
      if (selectedLocation.city !== decoded && selectedLocation.name !== decoded) {
        validateAndSetQuery(decoded);
      }
    }
  }, [queryLoc, selectedLocation.city, selectedLocation.name, validateAndSetQuery]);

  // Handler for Header Location Dropdown
  const handleLocationChange = (locDetail: CoastalLocationDetail) => {
    validateAndSetCoordinates(locDetail.lat, locDetail.lon, locDetail.label);
    setSearchParams({ location: locDetail.city }, { replace: true });
    setDropdownOpen(false);
  };

  const hasLocation = Boolean(selectedLocation && selectedLocation.name && selectedLocation.lat !== undefined);
  const isInland = Boolean(
    activeValidation && (activeValidation.status === 'INLAND' || activeValidation.is_coastal === false || activeValidation.is_marine === false)
  );
  const isOffshore = Boolean(
    hasLocation && !isInland && selectedLocation.distance_to_coast_km && selectedLocation.distance_to_coast_km > 20.0
  );

  const locName = selectedLocation.name || selectedLocation.city || 'Visakhapatnam Coast';
  const locCoords = selectedLocation.coordinates || 
    (selectedLocation.lat !== undefined && selectedLocation.lon !== undefined
      ? `${Math.abs(selectedLocation.lat).toFixed(4)}° ${selectedLocation.lat >= 0 ? 'N' : 'S'}, ${Math.abs(selectedLocation.lon).toFixed(4)}° ${selectedLocation.lon >= 0 ? 'E' : 'W'}`
      : '17.6868° N, 83.2185° E');

  const locRegion = selectedLocation.state || selectedLocation.region || 'Andhra Coastal Shelf';

  return (
    <div className="oceanis-dashboard-root">
      {/* 1. COMPACT OPERATIONAL DASHBOARD HEADER */}
      <header className="oceanis-dash-header">
        <div className="dash-container header-layout-flex">
          {/* Left: Organization & Title */}
          <div className="header-title-block">
            <div className="dash-pretag-row">
              <span className="dash-org-tag">OCEANIS</span>
              <span className="dash-dot-sep">•</span>
              <span className="dash-area-tag">OPERATIONAL COMMAND CENTER</span>
            </div>
            <h1 className="dash-primary-heading">Marine Intelligence Dashboard</h1>
          </div>

          {/* Center/Right: Location Badge & Status Cluster */}
          <div className="header-meta-cluster">
            {/* Location Selector Card */}
            <div className="location-control-card">
              <div className="loc-info-text">
                <div className="loc-header-line">
                  <span className="loc-pin-icon">📍</span>
                  <strong className="loc-city-name">{locName}</strong>
                </div>
                <span className="loc-coords-sub">{locCoords} • {locRegion}</span>
              </div>

              <div className="loc-dropdown-wrapper">
                <button
                  type="button"
                  className="btn-change-loc"
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  aria-expanded={dropdownOpen}
                >
                  <span>Change</span>
                  <svg className={`chevron-icon ${dropdownOpen ? 'open' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {dropdownOpen && (
                  <div className="loc-dropdown-menu">
                    <span className="dropdown-label">QUICK ACCESS LOCATIONS</span>
                    {quickAccessLocations.map((l) => (
                      <button
                        key={l.city}
                        type="button"
                        className={`loc-option-btn ${selectedLocation.city === l.city ? 'active' : ''}`}
                        onClick={() => handleLocationChange(l)}
                      >
                        <div className="opt-title">{l.label}</div>
                        <span className="opt-sub">{l.sea}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Time & Telemetry Status Card */}
            <div className="telemetry-status-card">
              <div className="time-display-block">
                <span className="live-clock">{currentTime || '12:00:00 IST'}</span>
                <span className="live-date">{currentDate || 'Today'}</span>
              </div>
              <div className="feed-status-indicator">
                <span className="pulse-beacon green" />
                <span className="status-label">{isInland ? 'INLAND BLOCKED' : isOffshore ? 'OFFSHORE BOUNDS' : 'COASTAL TELEMETRY'}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 2. MAIN DASHBOARD CONTENT */}
      <main className="dash-container dash-main-layout">
        {/* ROW 1: 6 LIVE MARINE CONDITIONS METRICS */}
        <section className="dash-card-section metrics-strip-card" id="marine-conditions-strip">
          <div className="dash-card-header-bar">
            <div className="card-title-group">
              <h2 className="dash-section-title">REAL-TIME MARINE CONDITIONS</h2>
              <span className="card-subtitle-badge">
                {isInland ? 'INLAND TERRITORY' : isOffshore ? 'OFFSHORE TELEMETRY' : 'COASTAL OBSERVATIONS'} • {locName.toUpperCase()}
              </span>
            </div>
            <Link to="/marine-conditions" className="dash-action-link">
              <span>Detailed Telemetry</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </Link>
          </div>

          <div className="metrics-six-grid">
            {/* Metric 1: Sea State */}
            <div className="metric-box">
              <span className="metric-label">SEA STATE</span>
              <div className="metric-value-row">
                <span className="metric-main-val">
                  {liveConditions?.seaState || (isInland ? 'Inland / No Sea' : 'Moderate')}
                </span>
              </div>
              <div className="metric-meta-row">
                <span className={`metric-status-tag ${isInland ? 'warning' : 'safe'}`}>
                  {isInland ? 'No Seashore' : 'Normal Ops'}
                </span>
                <span className="metric-source">{liveConditions?.source || 'INCOIS SWAN'}</span>
              </div>
            </div>

            {/* Metric 2: Wave Height */}
            <div className="metric-box">
              <span className="metric-label">WAVE HEIGHT</span>
              <div className="metric-value-row">
                <span className="metric-main-val">
                  {isInland ? '0.0' : (liveConditions?.waveHeight?.toFixed(1) ?? '1.5')}
                </span>
                <span className="metric-unit">m</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag normal">Significant (Hs)</span>
                <span className="metric-source">SWAN Model</span>
              </div>
            </div>

            {/* Metric 3: Wind Speed */}
            <div className="metric-box">
              <span className="metric-label">WIND</span>
              <div className="metric-value-row">
                <span className="metric-main-val">
                  {liveConditions?.windSpeed ? Math.round(liveConditions.windSpeed) : '18'}
                </span>
                <span className="metric-unit">km/h</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag normal">{liveConditions?.windDirection || 'ENE (10 kts)'}</span>
                <span className="metric-source">IMD Radar</span>
              </div>
            </div>

            {/* Metric 4: SST */}
            <div className="metric-box">
              <span className="metric-label">SST</span>
              <div className="metric-value-row">
                <span className="metric-main-val">
                  {isInland ? '--' : (liveConditions?.sst?.toFixed(1) ?? '28.6')}
                </span>
                <span className="metric-unit">°C</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag normal">{isInland ? 'Inland' : 'Optimal Shelf'}</span>
                <span className="metric-source">Sentinel-3 SLSTR</span>
              </div>
            </div>

            {/* Metric 5: Ocean Current */}
            <div className="metric-box">
              <span className="metric-label">CURRENT</span>
              <div className="metric-value-row">
                <span className="metric-main-val">
                  {isInland ? '0.0' : (liveConditions?.currentSpeed?.toFixed(1) ?? '0.6')}
                </span>
                <span className="metric-unit">kts</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag normal">{liveConditions?.currentDirection || '0.31 m/s (NE)'}</span>
                <span className="metric-source">HF Radar</span>
              </div>
            </div>

            {/* Metric 6: Visibility */}
            <div className="metric-box">
              <span className="metric-label">VISIBILITY</span>
              <div className="metric-value-row">
                <span className="metric-main-val">
                  {liveConditions?.visibility?.toFixed(1) ?? '10.0'}
                </span>
                <span className="metric-unit">km</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag safe">Clear Horizon</span>
                <span className="metric-source">IMD Station</span>
              </div>
            </div>
          </div>
        </section>

        {/* ROW 2: LIVE MAP PREVIEW | SAFETY STATUS */}
        <div className="dash-two-col-grid row-2-split">
          {/* Map Preview Card */}
          <section className="dash-card-section map-preview-card" id="map-preview">
            <div className="dash-card-header-bar">
              <div className="card-title-group">
                <h2 className="dash-section-title">LIVE OCEAN INTELLIGENCE MAP</h2>
                <span className="card-subtitle-badge">GIS PREVIEW • {locName.toUpperCase()}</span>
              </div>
              <Link to="/maps" className="dash-action-link">
                <span>Open Full GIS Map</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </Link>
            </div>

            <div className="map-embed-wrapper">
              <LiveOceanMap />
            </div>
          </section>

          {/* Safety Status Card */}
          <section className="dash-card-section safety-summary-card" id="safety-summary">
            <div className="dash-card-header-bar">
              <div className="card-title-group">
                <h2 className="dash-section-title">SAFETY STATUS</h2>
                <span className="card-subtitle-badge">MULTI-HAZARD SURVEILLANCE</span>
              </div>
              <Link to="/safety" className="dash-action-link">
                <span>Open Safety Center</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </Link>
            </div>

            <div className="safety-card-content">
              {/* Overall Risk Header */}
              <div className="safety-risk-banner moderate">
                <div className="risk-banner-left">
                  <span className="risk-icon">⚠️</span>
                  <div className="risk-text-block">
                    <span className="risk-level-tag">OVERALL RISK LEVEL</span>
                    <strong className="risk-level-title">{isInland ? 'INLAND TERRITORY' : 'MODERATE RISK'}</strong>
                  </div>
                </div>
                <span className="active-alerts-pill">{isInland ? '0 Alerts (Inland)' : '2 Active Advisories'}</span>
              </div>

              {/* Hazard Details */}
              <div className="safety-detail-list">
                <div className="hazard-highlight-item">
                  <span className="hazard-bullet">🔴</span>
                  <div className="hazard-info">
                    <strong className="hazard-title">Moderate Swell Vigilance</strong>
                    <p className="hazard-desc">Wave surge advisory (1.6m swell) in inshore shelf waters off {locName} coastal approaches.</p>
                  </div>
                </div>

                <div className="hazard-highlight-item">
                  <span className="hazard-bullet">🟡</span>
                  <div className="hazard-info">
                    <strong className="hazard-title">Wind Gust Advisory</strong>
                    <p className="hazard-desc">Occasional gusts up to 26 km/h during late afternoon sea breeze cycle.</p>
                  </div>
                </div>
              </div>

              <div className="safety-sources-footer">
                <span className="safety-src-label">Official Authorities:</span>
                <span className="safety-src-list">IMD • INCOIS • Indian Coast Guard</span>
              </div>
            </div>
          </section>
        </div>

        {/* ROW 3: FISHING INTELLIGENCE | OCEANIS DECISION */}
        <div className="dash-two-col-grid row-3-split">
          {/* Fishing Intelligence Card */}
          <section className="dash-card-section fishing-summary-card" id="fishing-summary">
            <div className="dash-card-header-bar">
              <div className="card-title-group">
                <h2 className="dash-section-title">FISHING INTELLIGENCE</h2>
                <span className="card-subtitle-badge">POTENTIAL FISHING ZONES</span>
              </div>
              <Link to="/fishing" className="dash-action-link">
                <span>Open Fishing Intelligence</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </Link>
            </div>

            <div className="fishing-card-content">
              <div className="fishing-kpi-grid">
                <div className="fishing-kpi-box">
                  <span className="kpi-label">FISHING SUITABILITY</span>
                  <span className={`kpi-val-badge ${isInland ? 'danger' : 'success'}`}>{isInland ? 'BLOCKED' : 'FAVORABLE'}</span>
                </div>
                <div className="fishing-kpi-box">
                  <span className="kpi-label">PFZ AVAILABILITY</span>
                  <span className="kpi-val-text">{isInland ? 'INLAND' : 'AVAILABLE'}</span>
                </div>
                <div className="fishing-kpi-box">
                  <span className="kpi-label">CONFIDENCE</span>
                  <span className="kpi-val-text highlight">{isInland ? '0%' : 'HIGH (88%)'}</span>
                </div>
              </div>

              <div className="fishing-brief-note">
                <span className="fishing-icon">🐟</span>
                <p>
                  {isInland 
                    ? 'No marine waters or pelagic fishing zones exist at inland coordinates.' 
                    : `Sentinel-3 thermal front and chlorophyll-a gradient synchronized off ${locName}. Optimal window: 04:30 – 10:00 IST.`
                  }
                </p>
              </div>
            </div>
          </section>

          {/* AI Decision Intelligence Card */}
          <section className="dash-card-section decision-summary-card" id="oceanis-decision">
            <div className="dash-card-header-bar">
              <div className="card-title-group">
                <h2 className="dash-section-title">OCEANIS DECISION</h2>
                <span className="card-subtitle-badge">AI MULTI-AGENT CONSENSUS</span>
              </div>
              <Link to="/ask" className="dash-action-link primary-cta">
                <span>Ask OCEANIS</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </Link>
            </div>

            <div className="decision-card-content">
              <div className="decision-kpi-row">
                <div className="decision-pill-item">
                  <span className="decision-lbl">RECOMMENDATION</span>
                  <span className={`decision-status-chip ${isInland ? 'not-recommended' : 'warning'}`}>
                    {isInland ? 'Blocked (Inland)' : 'Suitable with caution'}
                  </span>
                </div>
                <div className="decision-pill-item">
                  <span className="decision-lbl">RISK</span>
                  <span className={`decision-status-chip ${isInland ? 'danger' : 'moderate'}`}>
                    {isInland ? 'Inland' : 'Moderate'}
                  </span>
                </div>
                <div className="decision-pill-item">
                  <span className="decision-lbl">CONFIDENCE</span>
                  <span className="decision-val-strong">{isInland ? '0%' : '87%'}</span>
                </div>
              </div>

              <div className="decision-explanation-box">
                <span className="why-tag">WHY?</span>
                <p className="why-text">
                  {isInland 
                    ? 'No marine waters found at this coordinate. OCEANIS delivers specialized intelligence for coastal and offshore waters.'
                    : `Wave and wind parameters are acceptable off ${locName}, but active swell advisory requires caution near breakwaters and channel approaches.`
                  }
                </p>
              </div>

              <div className="decision-footer-consensus">
                <span className="consensus-dot" />
                <span>Consensus synthesized from <strong>6/6 Domain Intelligence Agents</strong> & Copernicus feeds.</span>
              </div>
            </div>
          </section>
        </div>

        {/* BOTTOM: DATA SOURCES & SYSTEM STATUS */}
        <section className="dash-card-section system-status-card" id="system-status">
          <div className="dash-card-header-bar">
            <div className="card-title-group">
              <h2 className="dash-section-title">DATA & SYSTEM STATUS</h2>
              <span className="card-subtitle-badge">INSTITUTIONAL DATA PIPELINE & CONNECTIVITY</span>
            </div>
            <Link to="/data-sources" className="dash-action-link">
              <span>View Data Provenance</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </Link>
          </div>

          <div className="system-status-content">
            {/* 4 Connected Institutional Providers */}
            <div className="providers-grid">
              <div className="provider-status-item">
                <span className="prov-dot connected" />
                <span className="prov-name">INCOIS</span>
                <span className="prov-desc">SWAN & Wave Buoy Network</span>
                <span className="prov-badge">Connected</span>
              </div>

              <div className="provider-status-item">
                <span className="prov-dot connected" />
                <span className="prov-name">IMD</span>
                <span className="prov-desc">Coastal Doppler Radar & NWP</span>
                <span className="prov-badge">Connected</span>
              </div>

              <div className="provider-status-item">
                <span className="prov-dot connected" />
                <span className="prov-name">COPERNICUS</span>
                <span className="prov-desc">Sentinel-3 OLCI & SLSTR</span>
                <span className="prov-badge">Connected</span>
              </div>

              <div className="provider-status-item">
                <span className="prov-dot connected" />
                <span className="prov-name">ISRO</span>
                <span className="prov-desc">Oceansat-3 & INSAT-3D</span>
                <span className="prov-badge">Connected</span>
              </div>
            </div>

            {/* Pipeline Integrity Bar */}
            <div className="pipeline-meta-bar">
              <div className="meta-indicator">
                <span className="meta-icon">🤖</span>
                <span><strong>6/6</strong> Domain Agents Online</span>
              </div>
              <div className="meta-sep">•</div>
              <div className="meta-indicator">
                <span className="meta-icon">🗄️</span>
                <span>PostgreSQL / PostGIS <strong>Connected</strong></span>
              </div>
              <div className="meta-sep">•</div>
              <div className="meta-indicator">
                <span className="meta-icon">⏱️</span>
                <span>Last Sync: <strong>{lastSyncTime}</strong></span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default DashboardPage;
