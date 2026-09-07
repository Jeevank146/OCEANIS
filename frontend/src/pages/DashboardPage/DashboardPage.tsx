import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useLocationContext, type LocationInfo } from '../../context/LocationContext';
import { LiveOceanMap } from '../../components/LiveOceanMap/LiveOceanMap';
import './DashboardPage.css';

interface CoastalLocationDetail {
  label: string;
  city: string;
  state: string;
  lat: number;
  lon: number;
  sea: string;
}

const coastalLocations: CoastalLocationDetail[] = [
  { label: 'Visakhapatnam, Andhra Pradesh', city: 'Visakhapatnam', state: 'Andhra Pradesh', lat: 17.6868, lon: 83.2185, sea: 'Bay of Bengal' },
  { label: 'Kakinada, Andhra Pradesh', city: 'Kakinada', state: 'Andhra Pradesh', lat: 16.9891, lon: 82.2475, sea: 'Bay of Bengal' },
  { label: 'Chennai, Tamil Nadu', city: 'Chennai', state: 'Tamil Nadu', lat: 13.0827, lon: 80.2707, sea: 'Coromandel Coast • Bay of Bengal' },
  { label: 'Mangalore, Karnataka', city: 'Mangalore', state: 'Karnataka', lat: 12.9141, lon: 74.8560, sea: 'Arabian Sea' },
  { label: 'Kochi, Kerala', city: 'Kochi', state: 'Kerala', lat: 9.9312, lon: 76.2673, sea: 'Malabar Coast • Arabian Sea' },
  { label: 'Paradeep, Odisha', city: 'Paradeep', state: 'Odisha', lat: 20.2644, lon: 86.6710, sea: 'Odisha Coast • Bay of Bengal' },
  { label: 'Mumbai, Maharashtra', city: 'Mumbai', state: 'Maharashtra', lat: 18.9400, lon: 72.8350, sea: 'Konkan Coast • Arabian Sea' },
  { label: 'Port Blair, Andaman & Nicobar', city: 'Port Blair', state: 'Andaman & Nicobar', lat: 11.6234, lon: 92.7265, sea: 'Andaman Sea' },
];

function resolveCanonicalLocation(input: string): CoastalLocationDetail {
  const q = input.trim().toLowerCase();

  const found = coastalLocations.find(l => q.includes(l.city.toLowerCase()) || (l.city.toLowerCase() === 'visakhapatnam' && q.includes('vizag')));
  if (found) return found;

  if (input.includes(',')) {
    const parts = input.split(',');
    return { label: input.trim(), city: parts[0].trim(), state: parts[1]?.trim() || 'India', lat: 17.6868, lon: 83.2185, sea: 'Coastal India' };
  }

  return { label: `${input.trim()}, Coastal India`, city: input.trim(), state: 'Coastal India', lat: 17.6868, lon: 83.2185, sea: 'Indian Ocean' };
}

export const DashboardPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    selectedLocation,
    setSelectedLocation,
    validateAndSetQuery,
  } = useLocationContext();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>('');
  const [currentDate, setCurrentDate] = useState<string>('');

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

  // Read location parameter from URL if provided (e.g. /dashboard?location=Visakhapatnam)
  const queryLoc = searchParams.get('location');

  const resolved = useMemo(() => {
    if (queryLoc && queryLoc.trim()) {
      return resolveCanonicalLocation(decodeURIComponent(queryLoc.trim()));
    }
    const currentName = selectedLocation.name || selectedLocation.city || 'Visakhapatnam';
    return resolveCanonicalLocation(currentName);
  }, [queryLoc, selectedLocation.name, selectedLocation.city]);

  // Sync URL parameter to application state
  useEffect(() => {
    if (queryLoc && queryLoc.trim()) {
      const canonical = resolveCanonicalLocation(decodeURIComponent(queryLoc.trim()));
      if (selectedLocation.city !== canonical.city) {
        validateAndSetQuery(canonical.city);
      }
    }
  }, [queryLoc, selectedLocation.city, validateAndSetQuery]);

  // Handler for Header Location Dropdown
  const handleLocationChange = (locDetail: CoastalLocationDetail) => {
    const updatedLocationInfo: LocationInfo = {
      ...selectedLocation,
      name: locDetail.label,
      city: locDetail.city,
      state: locDetail.state,
      lat: locDetail.lat,
      lon: locDetail.lon,
    };
    setSelectedLocation(updatedLocationInfo);
    setSearchParams({ location: locDetail.city }, { replace: true });
    setDropdownOpen(false);
  };

  return (
    <div className="oceanis-dashboard-root">
      {/* ===================================================================
          1. COMPACT OPERATIONAL DASHBOARD HEADER
          =================================================================== */}
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
                  <span className="loc-marker-icon">📍</span>
                  <strong className="loc-name-display">{resolved.label.toUpperCase()}</strong>
                </div>
                <div className="loc-coords-line">
                  {resolved.lat.toFixed(4)}° N, {resolved.lon.toFixed(4)}° E • <span className="loc-sea-tag">{resolved.sea}</span>
                </div>
              </div>

              <div className="loc-dropdown-anchor">
                <button
                  type="button"
                  className="btn-change-loc"
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  aria-label="Change coastal sector location"
                >
                  <span>Change Location</span>
                  <svg className={`chevron-icon ${dropdownOpen ? 'open' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {dropdownOpen && (
                  <div className="loc-picker-menu">
                    <div className="loc-menu-title">SELECT COASTAL SECTOR</div>
                    {coastalLocations.map((item) => (
                      <button
                        key={item.city}
                        type="button"
                        className={`loc-menu-btn ${resolved.city === item.city ? 'active' : ''}`}
                        onClick={() => handleLocationChange(item)}
                      >
                        <span className="loc-pin-glyph">⚓</span>
                        <div className="loc-btn-text">
                          <span className="loc-btn-label">{item.label}</span>
                          <span className="loc-btn-sea">{item.sea}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Telemetry Status & Freshness Strip */}
            <div className="telemetry-status-pill">
              <div className="telemetry-live-row">
                <span className="live-indicator-dot pulse" />
                <span className="live-text-tag">LIVE TELEMETRY</span>
              </div>
              <div className="telemetry-time-text">{currentDate ? `${currentDate} • ` : ''}{currentTime || '01:45 PM IST'}</div>
              <div className="telemetry-sources-text">INCOIS • IMD • Sentinel-3 • MODIS • Copernicus</div>
            </div>
          </div>
        </div>
      </header>

      {/* ===================================================================
          OPERATIONAL DASHBOARD BODY
          =================================================================== */}
      <main className="dash-container dash-main-grid-body">
        {/* ===================================================================
            ROW 1: LIVE MARINE CONDITIONS (SUMMARY ONLY)
            =================================================================== */}
        <section className="dash-card-section" id="marine-conditions-summary">
          <div className="dash-card-header-bar">
            <div className="card-title-group">
              <h2 className="dash-section-title">LIVE MARINE CONDITIONS</h2>
              <span className="card-subtitle-badge">IN-SITU BUOY & SATELLITE TELEMETRY</span>
            </div>
            <Link to="/marine-conditions" className="dash-action-link">
              <span>View Full Marine Conditions</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </Link>
          </div>

          <div className="marine-metrics-grid">
            {/* Metric 1: Sea State */}
            <div className="metric-box">
              <span className="metric-label">SEA STATE</span>
              <div className="metric-value-row">
                <span className="metric-main-val">Smooth–Moderate</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag safe">Normal Ops</span>
                <span className="metric-source">INCOIS</span>
              </div>
            </div>

            {/* Metric 2: Wave Height */}
            <div className="metric-box">
              <span className="metric-label">WAVE HEIGHT</span>
              <div className="metric-value-row">
                <span className="metric-main-val">1.5</span>
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
                <span className="metric-main-val">18</span>
                <span className="metric-unit">km/h</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag normal">ENE (10 kts)</span>
                <span className="metric-source">IMD Radar</span>
              </div>
            </div>

            {/* Metric 4: SST */}
            <div className="metric-box">
              <span className="metric-label">SST</span>
              <div className="metric-value-row">
                <span className="metric-main-val">28.6</span>
                <span className="metric-unit">°C</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag normal">Optimal Shelf</span>
                <span className="metric-source">Sentinel-3</span>
              </div>
            </div>

            {/* Metric 5: Ocean Current */}
            <div className="metric-box">
              <span className="metric-label">CURRENT</span>
              <div className="metric-value-row">
                <span className="metric-main-val">0.6</span>
                <span className="metric-unit">kts</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag normal">0.31 m/s (NE)</span>
                <span className="metric-source">HF Radar</span>
              </div>
            </div>

            {/* Metric 6: Visibility */}
            <div className="metric-box">
              <span className="metric-label">VISIBILITY</span>
              <div className="metric-value-row">
                <span className="metric-main-val">10.0</span>
                <span className="metric-unit">km</span>
              </div>
              <div className="metric-meta-row">
                <span className="metric-status-tag safe">Clear Horizon</span>
                <span className="metric-source">IMD Station</span>
              </div>
            </div>
          </div>
        </section>

        {/* ===================================================================
            ROW 2: LIVE MAP PREVIEW (LEFT) | SAFETY STATUS (RIGHT)
            =================================================================== */}
        <div className="dash-two-col-grid row-2-split">
          {/* Map Preview Card */}
          <section className="dash-card-section map-preview-card" id="map-preview">
            <div className="dash-card-header-bar">
              <div className="card-title-group">
                <h2 className="dash-section-title">LIVE OCEAN INTELLIGENCE MAP</h2>
                <span className="card-subtitle-badge">GIS PREVIEW • {resolved.city.toUpperCase()} SECTOR</span>
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
                    <strong className="risk-level-title">MODERATE RISK</strong>
                  </div>
                </div>
                <span className="active-alerts-pill">3 Active Alerts</span>
              </div>

              {/* Hazard Details */}
              <div className="safety-detail-list">
                <div className="hazard-highlight-item">
                  <span className="hazard-bullet">🔴</span>
                  <div className="hazard-info">
                    <strong className="hazard-title">Moderate Swell Vigilance</strong>
                    <p className="hazard-desc">Wave surge alert (1.8m swell) in inshore shelf waters off {resolved.city} coastal approaches.</p>
                  </div>
                </div>

                <div className="hazard-highlight-item">
                  <span className="hazard-bullet">🟡</span>
                  <div className="hazard-info">
                    <strong className="hazard-title">Wind Gust Advisory</strong>
                    <p className="hazard-desc">Occasional gusts up to 28 km/h during late afternoon sea breeze cycle.</p>
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

        {/* ===================================================================
            ROW 3: FISHING INTELLIGENCE (LEFT) | OCEANIS DECISION (RIGHT)
            =================================================================== */}
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
                  <span className="kpi-val-badge success">GOOD</span>
                </div>
                <div className="fishing-kpi-box">
                  <span className="kpi-label">PFZ AVAILABILITY</span>
                  <span className="kpi-val-text">AVAILABLE</span>
                </div>
                <div className="fishing-kpi-box">
                  <span className="kpi-label">CONFIDENCE</span>
                  <span className="kpi-val-text highlight">HIGH (88%)</span>
                </div>
              </div>

              <div className="fishing-brief-note">
                <span className="fishing-icon">🐟</span>
                <p>
                  Sentinel-3 SLSTR thermal front and chlorophyll-a gradient detected <strong>12–18 nm offshore</strong>. Optimal window: <strong>04:30 – 10:00 IST</strong> for pelagic shoals.
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
                  <span className="decision-status-chip warning">Suitable with caution</span>
                </div>
                <div className="decision-pill-item">
                  <span className="decision-lbl">RISK</span>
                  <span className="decision-status-chip moderate">Moderate</span>
                </div>
                <div className="decision-pill-item">
                  <span className="decision-lbl">CONFIDENCE</span>
                  <span className="decision-val-strong">87%</span>
                </div>
              </div>

              <div className="decision-explanation-box">
                <span className="why-tag">WHY?</span>
                <p className="why-text">
                  Wave and wind parameters are acceptable for coastal crafts, but active swell advisory requires caution near breakwaters and harbour entry channels.
                </p>
              </div>

              <div className="decision-footer-consensus">
                <span className="consensus-dot" />
                <span>Consensus synthesized from <strong>6/6 Domain Intelligence Agents</strong> & Copernicus feeds.</span>
              </div>
            </div>
          </section>
        </div>

        {/* ===================================================================
            BOTTOM: DATA SOURCES & SYSTEM STATUS
            =================================================================== */}
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
                <span>Last Sync: <strong>2 minutes ago</strong></span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default DashboardPage;
