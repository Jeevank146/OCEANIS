import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useLocationContext } from '../../context/LocationContext';
import { LiveOceanMap } from '../../components/LiveOceanMap/LiveOceanMap';
import { searchLocations, type LocationCandidate } from '../../services/api';
import './LiveMapPage.css';

interface SafePort {
  id: string;
  name: string;
  lat: number;
  lon: number;
  draftDepth: string;
  berthStatus: 'Protected Harbor' | 'Available' | 'High Occupancy';
  vhfChannel: string;
}

// Reference coastal havens and port facilities along the Indian coastline and maritime bounds
const ALL_SAFE_PORTS: SafePort[] = [
  { id: 'vsk', name: 'Visakhapatnam Port (VPT / Outer Harbor)', lat: 17.6868, lon: 83.2185, draftDepth: '18.5m', berthStatus: 'Protected Harbor', vhfChannel: 'Ch 16 / 12' },
  { id: 'kak', name: 'Kakinada Deepwater Port', lat: 16.9890, lon: 82.2474, draftDepth: '14.5m', berthStatus: 'Available', vhfChannel: 'Ch 16 / 14' },
  { id: 'mac', name: 'Machilipatnam Anchorage Harbor', lat: 16.1950, lon: 81.1620, draftDepth: '9.0m', berthStatus: 'Available', vhfChannel: 'Ch 16 / 08' },
  { id: 'kri', name: 'Krishnapatnam Port (KPCL)', lat: 14.2500, lon: 80.1200, draftDepth: '18.0m', berthStatus: 'Protected Harbor', vhfChannel: 'Ch 16 / 71' },
  { id: 'che', name: 'Chennai Port Trust (CPT / Outer Breakwater)', lat: 13.0827, lon: 80.2707, draftDepth: '17.0m', berthStatus: 'High Occupancy', vhfChannel: 'Ch 16 / 14' },
  { id: 'enn', name: 'Kamarajar Port (Ennore)', lat: 13.2600, lon: 80.3300, draftDepth: '16.0m', berthStatus: 'Available', vhfChannel: 'Ch 16 / 11' },
  { id: 'par', name: 'Paradip Major Port (PPT)', lat: 20.2600, lon: 86.6700, draftDepth: '17.1m', berthStatus: 'Protected Harbor', vhfChannel: 'Ch 16 / 12' },
  { id: 'dha', name: 'Dhamra Deepwater Port', lat: 20.8100, lon: 86.9600, draftDepth: '18.0m', berthStatus: 'Available', vhfChannel: 'Ch 16 / 69' },
  { id: 'gop', name: 'Gopalpur Port (ArcelorMittal)', lat: 19.3000, lon: 84.9700, draftDepth: '13.5m', berthStatus: 'Available', vhfChannel: 'Ch 16 / 09' },
  { id: 'tut', name: 'V.O. Chidambaranar Port (Tuticorin)', lat: 8.7500, lon: 78.1800, draftDepth: '14.2m', berthStatus: 'Available', vhfChannel: 'Ch 16 / 12' },
  { id: 'koc', name: 'Cochin Port (Willingdon Island)', lat: 9.9312, lon: 76.2673, draftDepth: '14.5m', berthStatus: 'Protected Harbor', vhfChannel: 'Ch 16 / 14' },
  { id: 'mum', name: 'Mumbai Port (MbPT / JNPT Nhava Sheva)', lat: 18.9220, lon: 72.8347, draftDepth: '16.5m', berthStatus: 'Protected Harbor', vhfChannel: 'Ch 16 / 12' },
  { id: 'mor', name: 'Mormugao Port (Goa)', lat: 15.4100, lon: 73.8000, draftDepth: '14.0m', berthStatus: 'Available', vhfChannel: 'Ch 16 / 14' },
  { id: 'kan', name: 'Deendayal Port (Kandla / Gulf of Kutch)', lat: 23.0100, lon: 70.2200, draftDepth: '14.5m', berthStatus: 'Protected Harbor', vhfChannel: 'Ch 16 / 10' },
  { id: 'man', name: 'New Mangalore Port (NMPT)', lat: 12.9141, lon: 74.8560, draftDepth: '15.1m', berthStatus: 'Available', vhfChannel: 'Ch 16 / 12' },
];

function calcDistanceNm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distKm = R * c;
  return Number((distKm * 0.539957).toFixed(1)); // convert km to Nautical Miles
}

function calcBearing(lat1: number, lon1: number, lat2: number, lon2: number): string {
  const y = Math.sin(((lon2 - lon1) * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180);
  const x =
    Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
    Math.sin((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.cos(((lon2 - lon1) * Math.PI) / 180);
  let brng = (Math.atan2(y, x) * 180) / Math.PI;
  brng = (brng + 360) % 360;

  const cardinalDirections = [
    'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
    'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW',
  ];
  const index = Math.round(brng / 22.5) % 16;
  return `${Math.round(brng)}° ${cardinalDirections[index]}`;
}

export const LiveMapPage: React.FC = () => {
  const {
    selectedLocation,
    validateAndSetQuery,
    validateAndSetCoordinates,
    useCurrentLocation: requestCurrentLocation,
    isValidating,
    setIsChangeModalOpen,
  } = useLocationContext();

  const [selectedPort, setSelectedPort] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'layers' | 'ports' | 'vessels'>('layers');
  
  // Search state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [suggestions, setSuggestions] = useState<LocationCandidate[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch location suggestions with debounce
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await searchLocations(searchQuery.trim(), 8);
        setSuggestions(res.results || []);
        setIsDropdownOpen(true);
      } catch (err) {
        console.error('Error fetching location suggestions:', err);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSelectCandidate = async (candidate: LocationCandidate) => {
    setIsDropdownOpen(false);
    setSearchQuery(candidate.name);
    await validateAndSetCoordinates(candidate.latitude, candidate.longitude, candidate.name);
  };

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsDropdownOpen(false);
    
    // Check if input is "latitude, longitude"
    const coordMatch = searchQuery.match(/^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$/);
    if (coordMatch) {
      const lat = parseFloat(coordMatch[1]);
      const lon = parseFloat(coordMatch[2]);
      if (!isNaN(lat) && !isNaN(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        await validateAndSetCoordinates(lat, lon, `Waypoint (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
        return;
      }
    }

    await validateAndSetQuery(searchQuery.trim());
  };

  const safePorts = useMemo(() => {
    const userLat = selectedLocation.lat;
    const userLon = selectedLocation.lon;
    const ranked = ALL_SAFE_PORTS.map((p) => {
      const dist = calcDistanceNm(userLat, userLon, p.lat, p.lon);
      const bearing = calcBearing(userLat, userLon, p.lat, p.lon);
      return {
        ...p,
        distanceNm: dist,
        bearing,
        coordinates: `${p.lat.toFixed(4)}° N, ${p.lon.toFixed(4)}° E`,
      };
    }).sort((a, b) => a.distanceNm - b.distanceNm);

    if (ranked.length > 0 && (!selectedPort || !ranked.some(r => r.id === selectedPort))) {
      setSelectedPort(ranked[0].id);
    }
    return ranked;
  }, [selectedLocation.lat, selectedLocation.lon]);

  const nearestRefuge = safePorts[0];

  // Derive coastal status tag
  const isOffshore = selectedLocation.is_coastal && (selectedLocation.distance_to_coast_km ?? 0) > 20.0;
  const isInland = selectedLocation.is_coastal === false || selectedLocation.status === 'INLAND';
  const coastalStatusTag = isInland ? 'INLAND' : isOffshore ? 'OFFSHORE' : 'COASTAL';

  return (
    <div className="live-map-page-container">
      {/* Top Banner with Active Dynamic Location Context & Search */}
      <div className="gis-top-banner">
        <div className="gis-banner-header-row">
          <div className="gis-banner-left">
            <div className="gis-pulse-indicator">
              <span className="pulse-dot" />
              <span className="pulse-label">LIVE GIS SPATIAL ENGINE</span>
            </div>
            <h1 className="gis-main-heading">Geospatial Intelligence & Navigation Map</h1>
            <p className="gis-subheading">
              Active Spatial Context: <strong>{selectedLocation.name}</strong> ({selectedLocation.coordinates}) • {selectedLocation.state || selectedLocation.region}
            </p>
          </div>

          {/* Integrated Location Search Toolbar */}
          <div className="gis-search-toolbar" ref={searchContainerRef}>
            <form onSubmit={handleSearchSubmit} className="gis-search-form">
              <div className="gis-search-input-wrapper">
                <svg className="gis-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <input
                  type="text"
                  className="gis-search-input"
                  placeholder="Search port, waypoint or coordinates (e.g. Paradip, 15.2, 80.5)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => {
                    if (suggestions.length > 0) setIsDropdownOpen(true);
                  }}
                  autoComplete="off"
                />
                {searchQuery && (
                  <button
                    type="button"
                    className="gis-search-clear-btn"
                    onClick={() => {
                      setSearchQuery('');
                      setSuggestions([]);
                      setIsDropdownOpen(false);
                    }}
                    aria-label="Clear search input"
                  >
                    ✕
                  </button>
                )}
                <button type="submit" className="gis-search-submit-btn" disabled={isValidating}>
                  {isValidating ? 'Resolving...' : 'Locate'}
                </button>
              </div>
            </form>

            <button
              type="button"
              className="gis-gps-btn"
              onClick={() => requestCurrentLocation()}
              disabled={isValidating}
              title="Detect GPS / Current Location"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="3 11 22 2 13 21 11 13 3 11" />
              </svg>
              <span>GPS</span>
            </button>

            <button
              type="button"
              className="gis-modal-btn"
              onClick={() => setIsChangeModalOpen(true)}
              title="Open Location Directory Modal"
            >
              <span>Change</span>
            </button>

            {/* Suggestions Dropdown */}
            {isDropdownOpen && (
              <div className="gis-search-dropdown">
                {isSearching ? (
                  <div className="gis-dropdown-msg">Searching coastal ports & maritime waypoints...</div>
                ) : suggestions.length > 0 ? (
                  suggestions.map((s) => (
                    <button
                      key={s.id || `${s.latitude}-${s.longitude}`}
                      type="button"
                      className={`gis-dropdown-item ${s.is_coastal ? 'is-coastal' : 'is-inland'}`}
                      onClick={() => handleSelectCandidate(s)}
                    >
                      <span className="gis-dropdown-icon">{s.is_coastal ? '⚓' : '📍'}</span>
                      <div className="gis-dropdown-info">
                        <div className="gis-dropdown-line1">
                          <strong>{s.name}</strong>
                          <span className={`gis-status-badge ${s.is_coastal ? 'badge-coastal' : 'badge-inland'}`}>
                            {s.is_coastal ? 'Coastal' : 'Inland'}
                          </span>
                        </div>
                        <span className="gis-dropdown-sub">{s.display_name} • {s.distance_to_coast_km} km to coast</span>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="gis-dropdown-msg">No matching locations found. Press enter to search or input coordinates (lat, lon).</div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Clean Metadata Cards Grid (Requirement E) */}
        <div className="gis-meta-cards-grid">
          {/* 1. Active Spatial Context */}
          <div className="gis-meta-card primary">
            <span className="gis-meta-label">ACTIVE SPATIAL CONTEXT</span>
            <span className="gis-meta-value main-title">{selectedLocation.name}</span>
            <span className="gis-meta-sub">{selectedLocation.coordinates}</span>
          </div>

          {/* 2. Coastal Status */}
          <div className="gis-meta-card">
            <span className="gis-meta-label">COASTAL STATUS</span>
            <div className="gis-meta-badge-row">
              <span className={`gis-coastal-tag tag-${coastalStatusTag.toLowerCase()}`}>
                {coastalStatusTag}
              </span>
            </div>
            <span className="gis-meta-sub">{selectedLocation.marine_context || 'Maritime Sector'}</span>
          </div>

          {/* 3. Bounds */}
          <div className="gis-meta-card">
            <span className="gis-meta-label">BOUNDS</span>
            <span className="gis-meta-value">PostGIS EPSG:4326</span>
            <span className="gis-meta-sub">WGS 84 Dynamic Grid</span>
          </div>

          {/* 4. Nearest Refuge */}
          <div className="gis-meta-card">
            <span className="gis-meta-label">NEAREST REFUGE</span>
            <span className="gis-meta-value port-title">
              {nearestRefuge ? nearestRefuge.name.split(' ')[0] : 'Scanning...'}
            </span>
            <span className="gis-meta-sub">
              {nearestRefuge ? `${nearestRefuge.distanceNm} NM • Bearing ${nearestRefuge.bearing}` : 'N/A'}
            </span>
          </div>

          {/* 5. Status */}
          <div className="gis-meta-card">
            <span className="gis-meta-label">STATUS</span>
            <div className="gis-status-live-pill">
              <span className="status-live-dot" />
              <span className="gis-meta-value status-active">REAL-TIME SYNC</span>
            </div>
            <span className="gis-meta-sub">PostGIS Spatial Engine</span>
          </div>
        </div>

        {/* Inland Protection Banner (if coordinates are inland) */}
        {isInland && (
          <div className="gis-inland-alert-banner">
            <span className="inland-alert-icon">⚠️</span>
            <div className="inland-alert-body">
              <strong>Inland Coordinates Detected ({selectedLocation.name} — {selectedLocation.coordinates})</strong>
              <p>
                Distance to coast is {selectedLocation.distance_to_coast_km ?? '50+'} km. Oceanographic wave fields, SST radiometry, and marine operational models are protected and blocked for inland coordinates. Please search for a coastal port or click an offshore point on the map.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Main Interactive Map Layout */}
      <div className="gis-workspace-grid">
        {/* Left / Center: Primary Interactive Map Viewport */}
        <div className="gis-map-viewport-wrapper">
          <LiveOceanMap />
        </div>

        {/* Right Sidebar: Safe Port Refuge Directory & Hydrographic Details */}
        <div className="gis-sidebar-panel">
          {/* Tab Switcher */}
          <div className="gis-panel-tabs">
            <button
              type="button"
              className={`gis-tab-btn ${activeTab === 'layers' ? 'active' : ''}`}
              onClick={() => setActiveTab('layers')}
            >
              Active Feeds
            </button>
            <button
              type="button"
              className={`gis-tab-btn ${activeTab === 'ports' ? 'active' : ''}`}
              onClick={() => setActiveTab('ports')}
            >
              Refuge Ports
            </button>
            <button
              type="button"
              className={`gis-tab-btn ${activeTab === 'vessels' ? 'active' : ''}`}
              onClick={() => setActiveTab('vessels')}
            >
              Vessel Traffic
            </button>
          </div>

          <div className="gis-tab-content">
            {activeTab === 'layers' && (
              <div className="gis-layers-info">
                <div className="gis-card-header">
                  <h3>Active Spatial Overlays</h3>
                  <span className="badge-count">8 Active</span>
                </div>
                <div className="layer-item-list">
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#16a34a' }} />
                    <div className="layer-info">
                      <strong>Potential Fishing Zones (PFZ)</strong>
                      <p>High chlorophyll-a bio-convergence & thermal boundaries</p>
                    </div>
                    <span className="layer-source">INCOIS</span>
                  </div>
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#0284c7' }} />
                    <div className="layer-info">
                      <strong>Sea Surface Temperature (SST)</strong>
                      <p>Sentinel-3 SLSTR calibrated thermal raster</p>
                    </div>
                    <span className="layer-source">Copernicus</span>
                  </div>
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#e11d48' }} />
                    <div className="layer-info">
                      <strong>Cyclone Storm Surge & Gale Buffer</strong>
                      <p>IMD Doppler Radar & Bay of Bengal track model</p>
                    </div>
                    <span className="layer-source">IMD</span>
                  </div>
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#9333ea' }} />
                    <div className="layer-info">
                      <strong>12 NM Territorial & 200 NM EEZ</strong>
                      <p>UNCLOS maritime limits and naval exclusion corridors</p>
                    </div>
                    <span className="layer-source">PostGIS</span>
                  </div>
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#d97706' }} />
                    <div className="layer-info">
                      <strong>GEBCO Bathymetry & Shoal Contours</strong>
                      <p>High-resolution depth isobaths with shallow warnings</p>
                    </div>
                    <span className="layer-source">GEBCO</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'ports' && (
              <div className="gis-ports-directory">
                <div className="gis-card-header">
                  <h3>Designated Safe Port Havens</h3>
                  <span className="badge-count">{safePorts.length} Ports</span>
                </div>
                <p className="gis-ports-subtitle">
                  Emergency shelter and harbor berths ranked by nautical distance from current position ({selectedLocation.name}).
                </p>
                <div className="safe-ports-list">
                  {safePorts.map((port) => (
                    <div
                      key={port.id}
                      className={`port-item-card ${selectedPort === port.id ? 'selected' : ''}`}
                      onClick={() => {
                        setSelectedPort(port.id);
                        validateAndSetCoordinates(port.lat, port.lon, port.name);
                      }}
                      title="Click to set active map location to this port"
                    >
                      <div className="port-header">
                        <strong className="port-name">{port.name}</strong>
                        <span className={`port-status-badge status-${port.berthStatus.toLowerCase().replace(/\s+/g, '-')}`}>
                          {port.berthStatus}
                        </span>
                      </div>
                      <div className="port-meta-grid">
                        <div className="port-metric">
                          <span className="metric-label">Distance:</span>
                          <span className="metric-val">{port.distanceNm} NM</span>
                        </div>
                        <div className="port-metric">
                          <span className="metric-label">Bearing:</span>
                          <span className="metric-val">{port.bearing}</span>
                        </div>
                        <div className="port-metric">
                          <span className="metric-label">Max Draft:</span>
                          <span className="metric-val">{port.draftDepth}</span>
                        </div>
                        <div className="port-metric">
                          <span className="metric-label">VHF Comms:</span>
                          <span className="metric-val">{port.vhfChannel}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'vessels' && (
              <div className="gis-vessel-traffic">
                <div className="gis-card-header">
                  <h3>AIS Vessel Traffic Density</h3>
                  <span className="badge-count">14 In-Range</span>
                </div>
                <div className="vessel-summary-grid">
                  <div className="vessel-stat-box">
                    <span className="stat-num">8</span>
                    <span className="stat-label">Fishing Trawlers</span>
                  </div>
                  <div className="vessel-stat-box">
                    <span className="stat-num">4</span>
                    <span className="stat-label">Cargo / Bulk</span>
                  </div>
                  <div className="vessel-stat-box">
                    <span className="stat-num">2</span>
                    <span className="stat-label">Coast Guard Patrol</span>
                  </div>
                </div>
                <div className="vessel-notices">
                  <div className="vessel-notice-card">
                    <span className="notice-icon">⚓</span>
                    <div className="notice-body">
                      <strong>ICG Patrol Vessel Active</strong>
                      <p>Monitoring maritime safety and fishing compliance on VHF Ch 16.</p>
                    </div>
                  </div>
                  <div className="vessel-notice-card warning">
                    <span className="notice-icon">⚠️</span>
                    <div className="notice-body">
                      <strong>Local Craft Advisory</strong>
                      <p>Active traffic operating in proximity to nearest operational fairway.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMapPage;
