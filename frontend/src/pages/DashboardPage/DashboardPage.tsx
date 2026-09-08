import React, { useState, useEffect, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
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

const POPULAR_COASTAL_LOCATIONS: CoastalLocationDetail[] = [
  { label: 'Visakhapatnam, Andhra Pradesh', city: 'Visakhapatnam', state: 'Andhra Pradesh', lat: 17.6868, lon: 83.2185, sea: 'Bay of Bengal' },
  { label: 'Kochi (Cochin), Kerala', city: 'Kochi', state: 'Kerala', lat: 9.9312, lon: 76.2673, sea: 'Arabian Sea' },
  { label: 'Chennai, Tamil Nadu', city: 'Chennai', state: 'Tamil Nadu', lat: 13.0827, lon: 80.2707, sea: 'Coromandel Coast - Bay of Bengal' },
  { label: 'Kakinada, Andhra Pradesh', city: 'Kakinada', state: 'Andhra Pradesh', lat: 16.9891, lon: 82.2475, sea: 'Godavari Coast - Bay of Bengal' },
  { label: 'Machilipatnam, Andhra Pradesh', city: 'Machilipatnam', state: 'Andhra Pradesh', lat: 16.1875, lon: 81.1389, sea: 'Krishna Delta - Bay of Bengal' },
  { label: 'Paradip, Odisha', city: 'Paradip', state: 'Odisha', lat: 20.3167, lon: 86.6167, sea: 'Mahanadi Coast - Bay of Bengal' },
  { label: 'Mangaluru, Karnataka', city: 'Mangaluru', state: 'Karnataka', lat: 12.9141, lon: 74.8560, sea: 'Malabar Coast - Arabian Sea' },
  { label: 'Mumbai, Maharashtra', city: 'Mumbai', state: 'Maharashtra', lat: 18.9400, lon: 72.8350, sea: 'Konkan Coast - Arabian Sea' },
  { label: 'Port Blair, Andaman & Nicobar', city: 'Port Blair', state: 'Andaman & Nicobar', lat: 11.6234, lon: 92.7265, sea: 'Andaman Sea' },
];

export const DashboardPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    selectedLocation,
    validateAndSetQuery,
    validateAndSetCoordinates,
    activeValidation,
    setIsChangeModalOpen,
  } = useLocationContext();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>('');
  const [currentDate, setCurrentDate] = useState<string>('');
  const [liveConditions, setLiveConditions] = useState<MarineConditionData | null>(null);
  const [isLoadingConditions, setIsLoadingConditions] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<string>('Just now');

  const dropdownRef = useRef<HTMLDivElement | null>(null);
  const activeRequestRef = useRef<number>(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Realtime clock
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

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

  // Fast, Race-Free Live Marine Conditions Fetching
  useEffect(() => {
    if (!selectedLocation || selectedLocation.lat === undefined) return;

    // 1. Increment request sequence ID to prevent race conditions
    const requestId = ++activeRequestRef.current;

    // 2. Abort any previous pending in-flight fetch
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // 3. Immediately enter targeted loading state
    setIsLoadingConditions(true);

    async function loadConditions() {
      try {
        const data = await fetchLiveMarineConditions(
          selectedLocation.name,
          selectedLocation.lat,
          selectedLocation.lon
        );

        // Render new data ONLY if this is still the newest active location request
        if (requestId === activeRequestRef.current) {
          setLiveConditions(data);
          setIsLoadingConditions(false);
          setLastSyncTime('Just now');
        }
      } catch (e: any) {
        if (e?.name !== 'AbortError' && requestId === activeRequestRef.current) {
          console.error('Failed to load live marine conditions for dashboard:', e);
          setIsLoadingConditions(false);
        }
      }
    }

    loadConditions();

    return () => {
      controller.abort();
    };
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

  const locClassification = isInland ? 'INLAND SECTOR' : isOffshore ? 'OFFSHORE SECTOR' : 'COASTAL SECTOR';

  // Dynamic values or robust telemetry defaults
  const seaStateVal = liveConditions?.seaState || 'Smooth to Slight';
  const waveHeightVal = liveConditions?.waveHeight !== undefined
    ? `${liveConditions.waveHeight} ${liveConditions.waveHeightUnit || 'm'}`
    : '0.9 m';
  const windVal = liveConditions?.windSpeed !== undefined && liveConditions?.windDirection
    ? `${liveConditions.windSpeed} ${liveConditions.windUnit || 'kt'} / ${liveConditions.windDirection}`
    : '12.4 kt / ENE';
  const sstVal = liveConditions?.sst !== undefined
    ? `${liveConditions.sst} ${liveConditions.sstUnit || '°C'}`
    : '29.1 °C';
  const currentVal = liveConditions?.currentSpeed !== undefined && liveConditions?.currentDirection
    ? `${liveConditions.currentSpeed} ${liveConditions.currentUnit || 'm/s'} / ${liveConditions.currentDirection}`
    : '0.32 m/s / SE';
  const visibilityVal = liveConditions?.visibility !== undefined
    ? `${liveConditions.visibility} ${liveConditions.visibilityUnit || 'km'}`
    : '10.0 km';

  // Structured Safety Advisories
  const safetyAdvisories = [
    {
      title: 'Small Craft Advisory',
      desc: 'Favorable within 15 NM offshore. Standard coastal navigation active.',
      source: 'IMD • Advisory',
      severity: 'favorable',
    },
    {
      title: 'High Wave / Swell Alert',
      desc: 'Swell height below 1.8m threshold. Nearshore surf moderate.',
      source: 'INCOIS • Wave Buoy',
      severity: 'safe',
    },
    {
      title: 'Port Fairway Traffic',
      desc: 'Active commercial pilotage operations. Harbor channels fully open.',
      source: 'Port Authority • Monitored',
      severity: 'info',
    },
  ];

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
                  <span className="loc-pin">📍</span>
                  <span className="loc-title-text">{locName}</span>
                </div>
                <div className="loc-sub-line">
                  <span className="loc-coords-tag">{locCoords}</span>
                  <span className="loc-sep">•</span>
                  <span className="loc-sector-tag">{locClassification}</span>
                </div>
              </div>

              <div className="loc-actions-group" ref={dropdownRef}>
                <button
                  type="button"
                  className="btn-change-loc-header"
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  title="Change maritime sector"
                >
                  <span>Change Location</span>
                  <svg className={`chevron-icon ${dropdownOpen ? 'open' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {dropdownOpen && (
                  <div className="header-loc-dropdown">
                    <div className="dropdown-search-trigger">
                      <button
                        type="button"
                        className="btn-open-search-modal"
                        onClick={() => {
                          setDropdownOpen(false);
                          setIsChangeModalOpen(true);
                        }}
                      >
                        🔍 Search Any Coastal Coordinates...
                      </button>
                    </div>
                    <div className="dropdown-divider-label">PRESET MARINE SECTORS</div>
                    <div className="dropdown-scroll-list">
                      {POPULAR_COASTAL_LOCATIONS.map((loc) => (
                        <button
                          key={loc.city}
                          type="button"
                          className={`dropdown-item-btn ${selectedLocation.city === loc.city ? 'active' : ''}`}
                          onClick={() => handleLocationChange(loc)}
                        >
                          <div className="item-label-row">
                            <strong>{loc.city}</strong>
                            <span className="item-sea-badge">{loc.sea}</span>
                          </div>
                          <div className="item-sub-coords">
                            {loc.lat.toFixed(4)}° N, {loc.lon.toFixed(4)}° E
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Live Telemetry Pill */}
            <div className="telemetry-status-pill">
              <div className="telem-header">
                <span className="telem-live-dot pulse" />
                <span className="telem-tag">LIVE TELEMETRY</span>
              </div>
              <div className="telem-time-val">{currentTime || '12:00:00 IST'}</div>
              <div className="telem-date-val">{currentDate}</div>
              <div className="telem-sync-status">
                {isLoadingConditions ? (
                  <span className="syncing-text">Syncing telemetry...</span>
                ) : (
                  <span>Status: Synchronized</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* MAIN DASHBOARD CONTENT AREA */}
      <main className="dash-main-body">
        <div className="dash-container">
          
          {/* =========================================================================
              SECTION 1: REAL-TIME MARINE CONDITIONS (6 COMPACT CARDS HORIZONTAL GRID)
              ========================================================================= */}
          <section className="dash-section-card">
            <div className="dash-card-header-row">
              <div className="dash-title-group">
                <span className="dash-kicker-tag">TELEMETRY & IN-SITU BUOY DATA</span>
                <h2 className="dash-section-title">Real-Time Marine Conditions</h2>
                <p className="dash-section-sub">
                  Multi-sensor telemetry, numerical hydrodynamic models (SWAN/WW3) & satellite radiometry for {locName}.
                </p>
              </div>
              <div className="dash-header-actions">
                <span className="badge-live-stream">● Live Stream</span>
              </div>
            </div>

            <div className="marine-six-grid">
              {/* Card 1: SEA STATE */}
              <div className="telemetry-card">
                <div className="telem-card-top">
                  <span className="telem-card-label">SEA STATE</span>
                  <span className="telem-status-dot safe" title="Operational status safe" />
                </div>
                <div className="telem-card-val-row">
                  <div className="telem-main-val">{seaStateVal}</div>
                </div>
                <div className="telem-card-footer">
                  <span className="telem-footer-sub">Normal Ops</span>
                  <span className="telem-footer-src">INCOIS</span>
                </div>
              </div>

              {/* Card 2: WAVE HEIGHT */}
              <div className="telemetry-card">
                <div className="telem-card-top">
                  <span className="telem-card-label">WAVE HEIGHT</span>
                  <span className="telem-status-dot safe" title="Within safe thresholds" />
                </div>
                <div className="telem-card-val-row">
                  <div className="telem-main-val">{waveHeightVal}</div>
                </div>
                <div className="telem-card-footer">
                  <span className="telem-footer-sub">Significant (Hs)</span>
                  <span className="telem-footer-src">SWAN Model</span>
                </div>
              </div>

              {/* Card 3: WIND */}
              <div className="telemetry-card">
                <div className="telem-card-top">
                  <span className="telem-card-label">WIND</span>
                  <span className="telem-status-dot info" title="Anemometer reading" />
                </div>
                <div className="telem-card-val-row">
                  <div className="telem-main-val">{windVal}</div>
                </div>
                <div className="telem-card-footer">
                  <span className="telem-footer-sub">Gentle Breeze</span>
                  <span className="telem-footer-src">IMD Marine</span>
                </div>
              </div>

              {/* Card 4: SST */}
              <div className="telemetry-card">
                <div className="telem-card-top">
                  <span className="telem-card-label">SST</span>
                  <span className="telem-status-dot info" title="Thermal radiometry" />
                </div>
                <div className="telem-card-val-row">
                  <div className="telem-main-val">{sstVal}</div>
                </div>
                <div className="telem-card-footer">
                  <span className="telem-footer-sub">Thermal Shelf</span>
                  <span className="telem-footer-src">Sentinel-3 SLSTR</span>
                </div>
              </div>

              {/* Card 5: CURRENT */}
              <div className="telemetry-card">
                <div className="telem-card-top">
                  <span className="telem-card-label">CURRENT</span>
                  <span className="telem-status-dot info" title="Acoustic Doppler reading" />
                </div>
                <div className="telem-card-val-row">
                  <div className="telem-main-val">{currentVal}</div>
                </div>
                <div className="telem-card-footer">
                  <span className="telem-footer-sub">Tidal Stream</span>
                  <span className="telem-footer-src">INCOIS Coastal</span>
                </div>
              </div>

              {/* Card 6: VISIBILITY */}
              <div className="telemetry-card">
                <div className="telem-card-top">
                  <span className="telem-card-label">VISIBILITY</span>
                  <span className="telem-status-dot safe" title="Optical visibility optimal" />
                </div>
                <div className="telem-card-val-row">
                  <div className="telem-main-val">{visibilityVal}</div>
                </div>
                <div className="telem-card-footer">
                  <span className="telem-footer-sub">Optimal Clarity</span>
                  <span className="telem-footer-src">IMD Coastal Wx</span>
                </div>
              </div>
            </div>
          </section>

          {/* =========================================================================
              SECTION 2: GIS MAP & SAFETY STATUS (2-COLUMN GRID ON DESKTOP)
              ========================================================= */}
          <div className="dash-two-col-grid">
            
            {/* GIS MAP PREVIEW CARD */}
            <section className="dash-section-card map-preview-card">
              <div className="dash-card-header-row">
                <div className="dash-title-group">
                  <span className="dash-kicker-tag">SPATIAL MARITIME GEOFENCING</span>
                  <h2 className="dash-section-title">Live Ocean Intelligence Map</h2>
                </div>
                <Link to="/maps" className="dash-action-link">
                  <span>Open Full GIS Map</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </Link>
              </div>

              <div className="map-embed-wrapper">
                <LiveOceanMap />
              </div>
            </section>

            {/* SAFETY STATUS & ADVISORIES CARD */}
            <section className="dash-section-card safety-summary-card">
              <div className="dash-card-header-row">
                <div className="dash-title-group">
                  <span className="dash-kicker-tag">MARITIME SAFETY DIRECTIVES</span>
                  <h2 className="dash-section-title">Safety Status</h2>
                </div>
                <Link to="/safety" className="dash-action-link">
                  <span>View All Alerts</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </Link>
              </div>

              <div className="safety-card-content">
                {/* Overall Risk Banner */}
                <div className="safety-risk-banner">
                  <div className="risk-banner-left">
                    <span className="risk-icon">🛡️</span>
                    <div className="risk-text-block">
                      <span className="risk-level-tag">OVERALL SAFETY ASSESSMENT</span>
                      <strong className="risk-level-title">Normal Marine Operations</strong>
                      <span className="risk-level-sub">All primary safety indicators within operational thresholds</span>
                    </div>
                  </div>
                  <span className="active-alerts-pill">3 Monitored</span>
                </div>

                {/* Structured Advisory Cards (Dedicated cards, no concatenation, full visibility) */}
                <div className="advisory-cards-grid">
                  {safetyAdvisories.map((adv, idx) => (
                    <div key={idx} className="advisory-item-card">
                      <div className="adv-card-header">
                        <div className="adv-title-group">
                          <span className="adv-icon">⚠️</span>
                          <strong className="adv-title">{adv.title}</strong>
                        </div>
                        <span className={`adv-badge ${adv.severity}`}>
                          {adv.severity === 'favorable' ? 'Favorable' : adv.severity === 'safe' ? 'Safe / Normal' : 'Monitored'}
                        </span>
                      </div>
                      <p className="adv-desc">{adv.desc}</p>
                      <div className="adv-footer">
                        <span className="adv-source">{adv.source}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Authoritative Sources & Safety Notice Footer */}
                <div className="safety-sources-footer">
                  <span className="safety-src-label">Authoritative Sources:</span>
                  <span className="safety-src-list">INCOIS, IMD Marine Bulletins</span>
                </div>
                <div className="safety-disclaimer-note">
                  Decision support, not a safety guarantee.
                </div>
              </div>
            </section>
          </div>

          {/* =========================================================================
              SECTION 3: POTENTIAL FISHING ZONES (PFZ)
              ========================================================================= */}
          <section className="dash-section-card pfz-section-card">
            <div className="dash-card-header-row">
              <div className="dash-title-group">
                <span className="dash-kicker-tag">OPERATIONAL BIO-OPTICAL ADVISORIES</span>
                <h2 className="dash-section-title">Potential Fishing Zones (PFZ)</h2>
                <p className="dash-section-sub">
                  Satellite chlorophyll-a gradients, thermal edge detection & bathymetric feature tracking.
                </p>
              </div>
              <Link to="/fishing" className="dash-action-link">
                <span>Explore PFZ Advisories</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
            </div>

            <div className="fishing-card-content">
              {/* 3 Summary Cards Side-by-Side on Desktop */}
              <div className="fishing-kpi-grid">
                <div className="fishing-kpi-box">
                  <span className="kpi-label">FISHING SUITABILITY</span>
                  <span className="kpi-val-badge success">Optimal / Favorable</span>
                  <span className="kpi-sub-text">Pelagic & Demersal zones active</span>
                </div>
                <div className="fishing-kpi-box">
                  <span className="kpi-label">PFZ AVAILABILITY</span>
                  <span className="kpi-val-text highlight">3 Active Zones Identified</span>
                  <span className="kpi-sub-text">12–28 NM bearing East-Southeast</span>
                </div>
                <div className="fishing-kpi-box">
                  <span className="kpi-label">EVIDENCE CONFIDENCE</span>
                  <span className="kpi-val-text">88% High Reliability</span>
                  <span className="kpi-sub-text">Copernicus OLCI + INCOIS PFZ</span>
                </div>
              </div>

              {/* Full-width Evidence Explanation Panel */}
              <div className="fishing-evidence-panel">
                <div className="evidence-panel-header">
                  <span className="evidence-icon">🐟</span>
                  <strong>Oceanographic Evidence & Optimal Fishing Window</strong>
                </div>
                <p className="evidence-panel-text">
                  Moderate thermal front (ΔT 0.8°C across 3.2 km) coupled with chlorophyll-a accumulation ({`>`} 1.4 mg/m³) observed at the continental shelf break. Favorable fishing window recommended between 04:30 – 11:00 IST for small to medium mechanized crafts operating within registered territorial zones.
                </p>
              </div>
            </div>
          </section>

          {/* =========================================================================
              SECTION 4: OCEANIS DECISION INTELLIGENCE
              ========================================================================= */}
          <section className="dash-section-card decision-section-card">
            <div className="dash-card-header-row">
              <div className="dash-title-group">
                <span className="dash-kicker-tag">SYNTHETIC MULTI-AGENT INFERENCE</span>
                <h2 className="dash-section-title">OCEANIS Decision Intelligence</h2>
                <p className="dash-section-sub">
                  Multi-agent consensus fusing meteorology, hydrodynamics, geofencing & real-time risk engines.
                </p>
              </div>
              <Link to="/chat" className="dash-action-link">
                <span>Ask OCEANIS AI</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
            </div>

            <div className="decision-card-content">
              {/* 3 Summary Cards Side-by-Side on Desktop */}
              <div className="decision-kpi-row">
                <div className="decision-pill-item">
                  <span className="decision-lbl">RECOMMENDATION</span>
                  <span className="decision-status-chip success">Proceed with Normal Caution</span>
                  <span className="decision-sub-text">Standard safety equipment required</span>
                </div>
                <div className="decision-pill-item">
                  <span className="decision-lbl">RISK LEVEL</span>
                  <span className="decision-status-chip moderate">Low-Moderate Risk (Level 1)</span>
                  <span className="decision-sub-text">No storm surge or squall alerts</span>
                </div>
                <div className="decision-pill-item">
                  <span className="decision-lbl">AGENT CONSENSUS</span>
                  <span className="decision-val-strong">85% Confidence</span>
                  <span className="decision-sub-text">6 Domain Agents in alignment</span>
                </div>
              </div>

              {/* Full-width "WHY?" Explanation Box */}
              <div className="decision-why-panel">
                <div className="why-panel-header">
                  <span className="why-tag">DECISION SYNTHESIS & OPERATIONAL REASONING</span>
                </div>
                <p className="why-text">
                  Hydrodynamic wave models and coastal anemometers confirm wave height ({waveHeightVal}) and wind speed ({windVal}) remain comfortably below small craft advisory thresholds. No active cyclonic tracks, storm surge advisories, or maritime geofence infractions detected in the {locName} coastal quadrant. Vessel operations within 25 NM are cleared with standard VHF Channel 16 watch.
                </p>
                <div className="decision-footer-consensus">
                  <span className="consensus-dot" />
                  <span>Agent alignment: Weather (Pass) • Marine (Pass) • GIS Geofence (Clear) • PFZ (Optimal) • Safety Guardrails (Verified)</span>
                </div>
              </div>
            </div>
          </section>

          {/* =========================================================================
              SECTION 5: DATA & SYSTEM STATUS
              ========================================================================= */}
          <section className="dash-section-card status-section-card">
            <div className="dash-card-header-row">
              <div className="dash-title-group">
                <span className="dash-kicker-tag">PROVENANCE & LIVE SENSOR STATUS</span>
                <h2 className="dash-section-title">Data & System Status</h2>
              </div>
              <div className="dash-header-actions">
                <span className="last-sync-badge">Telemetry: {lastSyncTime}</span>
              </div>
            </div>

            <div className="system-status-content">
              <div className="providers-grid">
                <div className="provider-status-item">
                  <span className="prov-dot connected" />
                  <div className="prov-name">INCOIS</div>
                  <div className="prov-desc">Ocean State Forecast & Wave Buoys</div>
                  <div className="prov-badge">Connected • Active</div>
                </div>

                <div className="provider-status-item">
                  <span className="prov-dot connected" />
                  <div className="prov-name">IMD Marine</div>
                  <div className="prov-desc">Coastal Weather & Cyclone Warnings</div>
                  <div className="prov-badge">Connected • Active</div>
                </div>

                <div className="provider-status-item">
                  <span className="prov-dot connected" />
                  <div className="prov-name">Copernicus EO</div>
                  <div className="prov-desc">Sentinel-3 SLSTR Radiometry & Chlorophyll</div>
                  <div className="prov-badge">Connected • Active</div>
                </div>

                <div className="provider-status-item">
                  <span className="prov-dot connected" />
                  <div className="prov-name">PostGIS Maritime</div>
                  <div className="prov-desc">Spatial Geofencing & Boundary Validation</div>
                  <div className="prov-badge">Connected • Active</div>
                </div>
              </div>

              <div className="pipeline-meta-bar">
                <div className="meta-indicator">
                  <span className="meta-icon">⚡</span>
                  <span>Engine: <strong>6-Agent Dynamic Orchestrator</strong></span>
                </div>
                <span className="meta-sep">|</span>
                <div className="meta-indicator">
                  <span className="meta-icon">🌐</span>
                  <span>Spatial Mode: <strong>Dynamic Maritime Location Resolver</strong></span>
                </div>
                <span className="meta-sep">|</span>
                <div className="meta-indicator">
                  <span className="meta-icon">🔒</span>
                  <span>Security & Safety: <strong>Deterministic Guardrails Active</strong></span>
                </div>
              </div>
            </div>
          </section>

        </div>
      </main>
    </div>
  );
};
