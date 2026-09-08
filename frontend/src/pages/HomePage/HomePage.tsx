import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLocationContext, type LocationInfo } from '../../context/LocationContext';
import { searchLocations, type LocationCandidate } from '../../services/api';
import './HomePage.css';

import heroFishingImg from '../../assets/images/hero_coastal_fishing.jpg';
import heroWavesImg from '../../assets/images/hero_ocean_waves.jpg';
import heroSatelliteImg from '../../assets/images/hero_satellite_earth.jpg';
import heroHarbourImg from '../../assets/images/coastal_harbour_port.jpg';
import heroVesselImg from '../../assets/images/marine_operations_vessel.jpg';

const backgroundImages = [
  heroHarbourImg,
  heroFishingImg,
  heroWavesImg,
  heroVesselImg,
  heroSatelliteImg,
];

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const {
    activeValidation,
    selectedLocation,
    popularLocations,
    validateAndSetQuery,
    validateAndSetCoordinates,
    useCurrentLocation,
    setSelectedLocation,
    validationError,
    clearValidationError,
  } = useLocationContext();

  const [bgIndex, setBgIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<LocationCandidate[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isGeoLocating, setIsGeoLocating] = useState(false);
  const [gpsNotice, setGpsNotice] = useState<string | null>(null);

  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchContainerRef = useRef<HTMLDivElement | null>(null);

  // Background carousel rotation
  useEffect(() => {
    const timer = setInterval(() => {
      setBgIndex((prev) => (prev + 1) % backgroundImages.length);
    }, 8000);
    return () => clearInterval(timer);
  }, []);

  // Close search dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (evt: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(evt.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Dynamic debounced search
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      setSearchResults([]);
      setIsDropdownOpen(false);
      return;
    }

    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }

    setIsSearching(true);
    searchDebounceRef.current = setTimeout(async () => {
      try {
        const res = await searchLocations(searchQuery.trim(), 8);
        setSearchResults(res.results || []);
        setIsDropdownOpen(true);
      } catch (e) {
        console.error('Search query error', e);
      } finally {
        setIsSearching(false);
      }
    }, 220);

    return () => {
      if (searchDebounceRef.current) {
        clearTimeout(searchDebounceRef.current);
      }
    };
  }, [searchQuery]);

  const handleSelectCandidate = async (candidate: LocationCandidate) => {
    setIsDropdownOpen(false);
    setSearchQuery('');
    setGpsNotice(null);
    clearValidationError();
    await validateAndSetCoordinates(candidate.latitude, candidate.longitude, candidate.name);
  };

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsDropdownOpen(false);
    setGpsNotice(null);
    clearValidationError();
    await validateAndSetQuery(searchQuery.trim());
  };

  const handleFocusSearch = () => {
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  };

  const handleUseCurrentLocation = async () => {
    setIsGeoLocating(true);
    setGpsNotice(null);
    clearValidationError();
    try {
      const res = await useCurrentLocation();
      setSearchQuery('');
      setIsDropdownOpen(false);
      if (res.status === 'UNRESOLVED') {
        setGpsNotice(res.reason || 'Geolocation access was denied or unavailable.');
      } else {
        setGpsNotice(null);
      }
    } catch (e: any) {
      console.error('Current location error', e);
      setGpsNotice('Unable to acquire GPS position. Please select a coastal location manually.');
    } finally {
      setIsGeoLocating(false);
    }
  };

  const handleSelectPopular = (loc: LocationInfo) => {
    setGpsNotice(null);
    clearValidationError();
    setSelectedLocation(loc);
    setSearchQuery('');
    setIsDropdownOpen(false);
  };

  // Location validity: must have a resolved name and not be UNRESOLVED
  const hasSelectedLocation = Boolean(
    selectedLocation &&
    selectedLocation.name &&
    activeValidation &&
    activeValidation.status !== 'UNRESOLVED'
  );

  const isLocationValid = hasSelectedLocation;

  const handleViewMarineIntelligence = () => {
    if (!isLocationValid) return;
    const locParam = encodeURIComponent(selectedLocation.city || selectedLocation.name);
    navigate(`/dashboard?location=${locParam}`);
  };

  return (
    <div className="landing-page-root">
      {/* Full-Screen Hero Container */}
      <section className="landing-hero-section">
        {/* Cinematic Ocean Background Carousel */}
        <div className="landing-bg-carousel">
          {backgroundImages.map((img, idx) => (
            <div
              key={idx}
              className={`landing-bg-slide ${idx === bgIndex ? 'active' : ''}`}
              style={{ backgroundImage: `url(${img})` }}
            />
          ))}
          {/* Deep Navy/Blue Atmospheric Overlays */}
          <div className="landing-overlay-base" />
          <div className="landing-overlay-gradient" />
          <div className="landing-overlay-vignette" />
        </div>

        {/* Hero Foreground Content */}
        <div className="landing-hero-container">
          <div className="landing-hero-grid">
            {/* Left Hero Column: Official Maritime Title */}
            <div className="landing-left-col">
              <div className="landing-platform-tag">
                <span className="platform-tag-pulse" />
                <span className="platform-tag-text">OFFICIAL MARINE DECISION PLATFORM</span>
              </div>

              <h1 className="landing-headline">
                Turning Ocean Data into Intelligent Decisions.
              </h1>

              <p className="landing-supporting-text">
                Multi-agent ocean intelligence synthesizing satellite remote sensing, Doppler radar forecasts, hydrodynamic currents, and navigational safety boundaries.
              </p>

              {/* Verified Maritime Capabilities */}
              <div className="landing-capabilities-grid">
                <div className="capability-item">
                  <div className="cap-icon-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M2 12h20M2 12a10 10 0 0 1 20 0M2 12a10 10 0 0 0 20 0" />
                      <circle cx="12" cy="12" r="4" />
                    </svg>
                  </div>
                  <div className="cap-text">
                    <strong>Hydrodynamic Forecasts</strong>
                    <span>Real-time wave height, swell & currents</span>
                  </div>
                </div>

                <div className="capability-item">
                  <div className="cap-icon-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="12 2 2 7 12 12 22 7 12 2" />
                      <polyline points="2 17 12 22 22 17" />
                      <polyline points="2 12 12 17 22 12" />
                    </svg>
                  </div>
                  <div className="cap-text">
                    <strong>Multi-Agent Fusion</strong>
                    <span>6 specialized marine AI domain agents</span>
                  </div>
                </div>

                <div className="capability-item">
                  <div className="cap-icon-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                  </div>
                  <div className="cap-text">
                    <strong>Early Hazard Warning</strong>
                    <span>Cyclone tracking & severe weather watches</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Hero Column: Official Maritime Location Gateway Card */}
            <div className="landing-right-card-wrapper">
              <div className="landing-location-card">
                {/* Gateway Card Header */}
                <div className="loc-card-top">
                  <div className="loc-card-header-row">
                    <span className="loc-card-badge">MARINE INTELLIGENCE</span>
                    {hasSelectedLocation && (
                      <span className={`loc-status-pill ${activeValidation.status === 'INLAND' ? 'status-inland' : 'status-coastal'}`}>
                        {activeValidation.status === 'INLAND' ? 'INLAND' : 'COASTAL READY'}
                      </span>
                    )}
                  </div>
                  <h2 className="loc-card-title">Select Your Location</h2>
                  <p className="loc-card-desc">
                    Choose a coastal, offshore, or map location to continue.
                  </p>
                </div>

                {/* Location Search Input Form */}
                <div className="loc-search-box" ref={searchContainerRef}>
                  <form onSubmit={handleSearchSubmit} role="search">
                    <div className="search-input-wrapper">
                      <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                        <circle cx="11" cy="11" r="8" />
                        <line x1="21" y1="21" x2="16.65" y2="16.65" />
                      </svg>
                      <input
                        ref={searchInputRef}
                        type="text"
                        className="loc-search-input"
                        placeholder="Search coastal area, port or coordinates..."
                        aria-label="Search coastal area, port or coordinates"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onFocus={() => {
                          if (searchResults.length > 0) setIsDropdownOpen(true);
                        }}
                        autoComplete="off"
                      />
                      {searchQuery && (
                        <button
                          type="button"
                          className="btn-clear-search"
                          onClick={() => {
                            setSearchQuery('');
                            setSearchResults([]);
                            setIsDropdownOpen(false);
                          }}
                          aria-label="Clear search query"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </form>

                  {/* Dynamic Dropdown Search Results */}
                  {isDropdownOpen && (
                    <div className="loc-search-dropdown" role="listbox">
                      {isSearching ? (
                        <div className="no-search-results">
                          <span>Searching coastal ports, waters & stations...</span>
                        </div>
                      ) : searchResults.length > 0 ? (
                        searchResults.map((item) => (
                          <button
                            key={item.id}
                            type="button"
                            className="search-result-item"
                            onClick={() => handleSelectCandidate(item)}
                            role="option"
                            aria-selected="false"
                          >
                            <span className="res-icon" aria-hidden="true">⚓</span>
                            <div className="res-meta">
                              <strong>{item.name}</strong>
                              <span>{item.display_name} · {item.is_coastal ? 'Coastal' : 'Inland'}</span>
                            </div>
                          </button>
                        ))
                      ) : (
                        <div className="no-search-results">
                          <span>No coastal location found. Press Enter to validate or provide coordinates.</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Quick Action Buttons */}
                <div className="loc-quick-actions">
                  <button
                    type="button"
                    className="btn-quick-action"
                    onClick={handleFocusSearch}
                    aria-label="Search location by text"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    <span>Search Location</span>
                  </button>

                  <button
                    type="button"
                    className="btn-quick-action"
                    onClick={handleUseCurrentLocation}
                    disabled={isGeoLocating}
                    aria-label="Use my GPS location"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <polygon points="3 11 22 2 13 21 11 13 3 11" />
                    </svg>
                    <span>{isGeoLocating ? 'GPS Detecting...' : 'Use My Location'}</span>
                  </button>

                  <button
                    type="button"
                    className="btn-quick-action"
                    onClick={() => navigate('/maps?draw=1')}
                    aria-label="Draw on interactive map"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
                    </svg>
                    <span>Draw on Map</span>
                  </button>
                </div>

                {/* GPS Notice or Validation Error */}
                {(gpsNotice || validationError) && (
                  <div className="loc-error-notice" role="alert">
                    <span className="notice-icon">⚠️</span>
                    <span className="notice-text">{gpsNotice || validationError}</span>
                  </div>
                )}

                {/* Popular Coastal Locations Grid */}
                <div className="popular-locations-section">
                  <span className="pop-label">Popular Coastal Locations</span>
                  <div className="popular-chips-grid">
                    {popularLocations.slice(0, 6).map((loc) => {
                      const isSelected = Boolean(
                        hasSelectedLocation &&
                        (selectedLocation.name === loc.name || selectedLocation.city === loc.city)
                      );
                      return (
                        <button
                          key={loc.name}
                          type="button"
                          className={`pop-chip-btn ${isSelected ? 'active' : ''}`}
                          onClick={() => handleSelectPopular(loc)}
                          aria-pressed={isSelected}
                        >
                          {isSelected && <span className="chip-check" aria-hidden="true">✓</span>}
                          <span>{loc.city || loc.name}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Selected Location Summary or Initial Empty Prompt */}
                {hasSelectedLocation ? (
                  <div className="selected-location-display">
                    <div className="sel-loc-header">
                      <span className="sel-loc-label">SELECTED LOCATION</span>
                      <span className={`sel-loc-status ${activeValidation.status === 'INLAND' ? 'status-inland' : 'status-coastal'}`}>
                        {activeValidation.status === 'INLAND' ? 'INLAND TERRITORY' : (selectedLocation.isPort ? 'PORT & HARBOUR' : 'COASTAL WATERS')}
                      </span>
                    </div>
                    <div className="sel-loc-body">
                      <svg className="sel-loc-pin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                        <circle cx="12" cy="10" r="3" />
                      </svg>
                      <div className="sel-loc-details">
                        <strong className="sel-loc-name">{selectedLocation.name}{selectedLocation.state ? `, ${selectedLocation.state}` : ''}</strong>
                        <span className="sel-loc-coords">
                          {selectedLocation.coordinates} · {selectedLocation.portName || selectedLocation.marine_context || (selectedLocation.is_coastal ? 'Coastal Marine Zone' : 'Inland Sector')}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="no-location-prompt">
                    <span className="no-loc-icon" aria-hidden="true">⚓</span>
                    <span className="no-loc-text">
                      Select a location above or search to view marine intelligence.
                    </span>
                  </div>
                )}

                {/* Card Footer & Primary Action Button */}
                <div className="loc-card-footer">
                  <button
                    type="button"
                    className="btn-get-live-info"
                    onClick={handleViewMarineIntelligence}
                    disabled={!isLocationValid}
                    aria-disabled={!isLocationValid}
                  >
                    <span>View Marine Intelligence →</span>
                  </button>
                  <span className="telemetry-notice">
                    Authoritative observational & forecast data from INCOIS, IMD, and Copernicus Marine
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Subtle Bottom Scroll / Explore Indicator */}
        <div className="landing-bottom-indicator">
          <button
            type="button"
            className="btn-scroll-indicator"
            onClick={() => navigate('/dashboard')}
            aria-label="Explore dashboard"
          >
            <span className="scroll-text">Explore Marine Platform</span>
            <svg className="scroll-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
