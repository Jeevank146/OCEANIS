import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLocationContext, type LocationInfo } from '../../context/LocationContext';
import { searchLocations, type LocationCandidate } from '../../services/api';
import './HomePage.css';

// 10 High-Quality Maritime Background Images (Flagship Indian Coastline is Slide 0)
import heroFlagshipImg from '../../assets/images/oceanis_flagship_coastline.jpg';
import heroGisImg from '../../assets/images/geospatial_gis_coastline.jpg';
import heroHarbourImg from '../../assets/images/coastal_harbour_port.jpg';
import heroSatelliteImg from '../../assets/images/hero_satellite_earth.jpg';
import heroSstChlorophyllImg from '../../assets/images/ocean_sst_chlorophyll.jpg';
import heroWavesImg from '../../assets/images/hero_ocean_waves.jpg';
import heroFishingImg from '../../assets/images/hero_coastal_fishing.jpg';
import heroVesselImg from '../../assets/images/marine_operations_vessel.jpg';
import heroCycloneImg from '../../assets/images/satellite_cyclone_radar.jpg';
import heroSunsetImg from '../../assets/images/sunset_ocean_cta.jpg';

const backgroundSlides = [
  { img: heroFlagshipImg, label: 'Indian Coastline & Marine Operations Corridor' },
  { img: heroGisImg, label: 'Indian Coastline & Satellite GIS Radar' },
  { img: heroHarbourImg, label: 'Bay of Bengal Deepwater Port Operations' },
  { img: heroSatelliteImg, label: 'Indian Ocean Earth Observation & Remote Sensing' },
  { img: heroSstChlorophyllImg, label: 'Sentinel-3 Ocean Colour, Chlorophyll & SST Gradients' },
  { img: heroWavesImg, label: 'Hydrodynamics, Ocean Currents & Wave Models' },
  { img: heroFishingImg, label: 'Coastal Fishing Fleets & Potential Fishing Zones' },
  { img: heroVesselImg, label: 'Maritime Operations & Research Vessels' },
  { img: heroCycloneImg, label: 'Cyclone Tracking & Severe Maritime Weather Systems' },
  { img: heroSunsetImg, label: 'Open Ocean Navigation & Maritime Operations' },
];

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const {
    activeValidation,
    selectedLocation,
    popularLocations,
    isValidating,
    validateAndSetQuery,
    validateAndSetCoordinates,
    useCurrentLocation,
    validationError,
    clearValidationError,
  } = useLocationContext();

  const [bgIndex, setBgIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<LocationCandidate[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isGeoLocating, setIsGeoLocating] = useState(false);
  const [gpsNotice, setGpsNotice] = useState<string | null>(null);
  const [customError, setCustomError] = useState<string | null>(null);

  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchContainerRef = useRef<HTMLDivElement | null>(null);
  const carouselTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Preload next image
  useEffect(() => {
    const nextIdx = (bgIndex + 1) % backgroundSlides.length;
    const img = new Image();
    img.src = backgroundSlides[nextIdx].img;
  }, [bgIndex]);

  // Background carousel auto-rotation (every 3.5 seconds)
  const resetCarouselTimer = useCallback(() => {
    if (carouselTimerRef.current) {
      clearInterval(carouselTimerRef.current);
    }
    carouselTimerRef.current = setInterval(() => {
      setBgIndex((prev) => (prev + 1) % backgroundSlides.length);
    }, 3500);
  }, []);

  useEffect(() => {
    resetCarouselTimer();
    return () => {
      if (carouselTimerRef.current) {
        clearInterval(carouselTimerRef.current);
      }
    };
  }, [resetCarouselTimer]);

  const handlePrevSlide = () => {
    setBgIndex((prev) => (prev - 1 + backgroundSlides.length) % backgroundSlides.length);
    resetCarouselTimer();
  };

  const handleNextSlide = () => {
    setBgIndex((prev) => (prev + 1) % backgroundSlides.length);
    resetCarouselTimer();
  };

  const handleJumpSlide = (idx: number) => {
    setBgIndex(idx);
    resetCarouselTimer();
  };

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
    const trimmed = searchQuery.trim();
    if (!trimmed || trimmed.length < 2) {
      setSearchResults([]);
      setIsDropdownOpen(false);
      return;
    }

    const isCoordinateLike = /^[-+]?\d{1,3}(?:\.\d+)?[,\s]+[-+]?\d{1,3}(?:\.\d+)?$/.test(trimmed);
    if (isCoordinateLike) {
      setSearchResults([]);
      setIsDropdownOpen(false);
      return;
    }

    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }

    searchDebounceRef.current = setTimeout(async () => {
      try {
        const res = await searchLocations(trimmed, 8);
        setSearchResults(res.results || []);
        setIsDropdownOpen(true);
      } catch (e) {
        console.error('Search query error', e);
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
    setCustomError(null);
    clearValidationError();

    await validateAndSetQuery(candidate.name);
  };

  const executeSearch = async (rawQuery: string) => {
    const q = rawQuery.trim();
    if (!q) {
      setCustomError('Please enter a location name, port, or coordinates (e.g. 17.68, 83.21).');
      return;
    }

    setGpsNotice(null);
    setCustomError(null);
    clearValidationError();
    setIsDropdownOpen(false);

    const coordMatch = q.match(/^([-+]?\d{1,3}(?:\.\d+)?)[,\s]+([-+]?\d{1,3}(?:\.\d+)?)$/);
    if (coordMatch) {
      const lat = parseFloat(coordMatch[1]);
      const lon = parseFloat(coordMatch[2]);
      if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        await validateAndSetCoordinates(lat, lon, `Custom Coordinates (${lat.toFixed(2)}, ${lon.toFixed(2)})`);
        setSearchQuery('');
        return;
      }
    }

    await validateAndSetQuery(q);
    setSearchQuery('');
  };

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (searchResults.length > 0 && isDropdownOpen) {
      handleSelectCandidate(searchResults[0]);
    } else {
      executeSearch(searchQuery);
    }
  };

  const handleSelectPopular = async (loc: LocationInfo) => {
    setGpsNotice(null);
    setCustomError(null);
    clearValidationError();
    setIsDropdownOpen(false);
    setSearchQuery('');

    if (loc.lat && loc.lon) {
      await validateAndSetCoordinates(loc.lat, loc.lon, loc.name);
    } else {
      await validateAndSetQuery(loc.name);
    }
  };

  const handleUseCurrentLocation = async () => {
    setCustomError(null);
    setGpsNotice(null);
    clearValidationError();
    setIsGeoLocating(true);
    try {
      await useCurrentLocation();
    } catch (err: any) {
      setGpsNotice(err.message || 'GPS location denied or unavailable.');
    } finally {
      setIsGeoLocating(false);
    }
  };

  const handleContinueToIntelligence = () => {
    if (isCoastalReady) {
      navigate('/dashboard');
    }
  };

  // State calculations
  const hasSelectedLocation = Boolean(
    selectedLocation &&
    selectedLocation.name &&
    selectedLocation.lat !== undefined &&
    selectedLocation.lon !== undefined
  );

  const isInland = Boolean(
    activeValidation &&
    (activeValidation.status === 'INLAND' || activeValidation.is_coastal === false || activeValidation.is_marine === false)
  );

  const isCoastalReady = hasSelectedLocation && !isInland;
  const isResolving = isValidating;
  const isCtaEnabled = isCoastalReady && !isResolving;
  const displayErrorMessage = customError || validationError || gpsNotice;

  return (
    <div className="landing-page-root">
      {/* Full-Screen Hero Viewport */}
      <section className="landing-hero-section" aria-label="OCEANIS Marine Intelligence Portal">
        {/* Full-Screen Background Carousel */}
        <div className="landing-bg-carousel" aria-hidden="true">
          {backgroundSlides.map((slide, idx) => (
            <div
              key={idx}
              className={`landing-bg-slide ${idx === bgIndex ? 'active' : ''}`}
              style={{ backgroundImage: `url(${slide.img})` }}
            />
          ))}
        </div>

        {/* Realistic Marine Atmospheric Overlays (High visual fidelity to Reference 1) */}
        <div className="landing-overlay-base" aria-hidden="true" />
        <div className="landing-overlay-gradient" aria-hidden="true" />
        <div className="landing-overlay-vignette" aria-hidden="true" />

        {/* Carousel Slide Indicators & Manual Arrows */}
        <div className="carousel-controls-bar" role="toolbar" aria-label="Background image selector">
          <button
            type="button"
            className="btn-carousel-nav btn-carousel-prev"
            onClick={handlePrevSlide}
            aria-label="Previous background satellite view"
          >
            ←
          </button>
          <div className="carousel-pagination-strip">
            {backgroundSlides.map((_, idx) => (
              <button
                key={idx}
                type="button"
                className={`pagination-dot ${idx === bgIndex ? 'active' : ''}`}
                onClick={() => handleJumpSlide(idx)}
                aria-label={`Switch to background slide ${idx + 1}`}
              >
                <span className="dot-fill" />
              </button>
            ))}
          </div>
          <button
            type="button"
            className="btn-carousel-nav btn-carousel-next"
            onClick={handleNextSlide}
            aria-label="Next background satellite view"
          >
            →
          </button>
        </div>

        {/* Main Hero Container */}
        <div className="landing-hero-container">
          <div className="landing-hero-grid">
            {/* Left Hero Column: Marine Intelligence Badge, 3-Line Headline, Subtitle, 3 Capabilities */}
            <div className="landing-left-col">
              {/* Pill Badge matching Reference 1 */}
              <div className="landing-platform-badge">
                <span className="badge-beacon-dot" />
                <span className="badge-text">MARINE INTELLIGENCE &amp; DECISION SUPPORT</span>
              </div>

              {/* Exact 3-Line Hero Headline matching Reference 1 */}
              <h1 className="landing-headline">
                Integrated Marine<br />
                <span className="accent-cyan">Intelligence</span><br />
                for Safer Decisions
              </h1>

              {/* Exact Subtitle matching Reference 1 */}
              <p className="landing-supporting-text">
                Integrated marine observations, satellite intelligence, environmental conditions and safety information for informed maritime decisions.
              </p>

              {/* 3 Horizontal Compact Capability Cards matching Reference 1 */}
              <div className="landing-capabilities-grid">
                <button
                  type="button"
                  className="capability-card"
                  onClick={() => navigate('/marine-conditions')}
                  title="Explore Wave, Swell and Current Intelligence"
                >
                  <div className="cap-icon-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M2 12c3-4 6-4 9 0s6 4 9 0" />
                      <path d="M2 17c3-4 6-4 9 0s6 4 9 0" />
                    </svg>
                  </div>
                  <div className="cap-text">
                    <strong>Hydrodynamic Intelligence</strong>
                    <span>Wave, swell and current intelligence</span>
                  </div>
                </button>

                <button
                  type="button"
                  className="capability-card"
                  onClick={() => navigate('/agents')}
                  title="Explore Specialized Domain Intelligence Agents"
                >
                  <div className="cap-icon-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="12 2 2 7 12 12 22 7 12 2" />
                      <polyline points="2 17 12 22 22 17" />
                      <polyline points="2 12 12 17 22 12" />
                    </svg>
                  </div>
                  <div className="cap-text">
                    <strong>Multi-Agent Marine Analysis</strong>
                    <span>Six specialized domain agents for marine reasoning</span>
                  </div>
                </button>

                <button
                  type="button"
                  className="capability-card"
                  onClick={() => navigate('/safety')}
                  title="Explore Marine Warnings, Hazard Zones and Operational Risk Indicators"
                >
                  <div className="cap-icon-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                  </div>
                  <div className="cap-text">
                    <strong>Marine Hazard Monitoring</strong>
                    <span>Marine warnings, hazard zones and operational risk indicators</span>
                  </div>
                </button>
              </div>
            </div>

            {/* Right Hero Column: Professional Dark Translucent Marine Operating Area Panel */}
            <div className="landing-right-card-wrapper">
              <div className="marine-operating-panel">
                {/* Panel Top Heading & Badge */}
                <div className="panel-header-section">
                  <div className="panel-badge-row">
                    <span className="panel-institutional-badge">
                      <svg className="panel-crosshair-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="22" y1="12" x2="18" y2="12" />
                        <line x1="6" y1="12" x2="2" y2="12" />
                        <line x1="12" y1="6" x2="12" y2="2" />
                        <line x1="12" y1="22" x2="12" y2="18" />
                      </svg>
                      MARINE OPERATING AREA
                    </span>
                    {hasSelectedLocation && (
                      <span className={`panel-status-pill ${isInland ? 'status-inland' : 'status-coastal'}`}>
                        {isInland ? 'INLAND' : 'COASTAL'}
                      </span>
                    )}
                  </div>
                  <h2 className="panel-title">Select a Location</h2>
                  <p className="panel-subtitle">
                    Choose a coastal, offshore, or map-defined area to access marine intelligence.
                  </p>
                </div>

                {/* Location Search Input Form */}
                <div className="panel-search-container" ref={searchContainerRef}>
                  <form onSubmit={handleSearchSubmit} role="search" className="search-form">
                    <div className="search-input-box">
                      <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                        <circle cx="11" cy="11" r="8" />
                        <line x1="21" y1="21" x2="16.65" y2="16.65" />
                      </svg>
                      <input
                        ref={searchInputRef}
                        type="text"
                        className="marine-search-input"
                        placeholder="Search port, coastal area or coordinates..."
                        aria-label="Search port, coastal area or coordinates"
                        value={searchQuery}
                        onChange={(e) => {
                          setSearchQuery(e.target.value);
                          if (customError) setCustomError(null);
                        }}
                        onFocus={() => {
                          if (searchResults.length > 0) setIsDropdownOpen(true);
                        }}
                        autoComplete="off"
                      />
                      {searchQuery && (
                        <button
                          type="button"
                          className="btn-clear-input"
                          onClick={() => {
                            setSearchQuery('');
                            setSearchResults([]);
                            setIsDropdownOpen(false);
                            setCustomError(null);
                          }}
                          aria-label="Clear search field"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </form>

                  {/* Search Autocomplete Results Dropdown */}
                  {isDropdownOpen && searchResults.length > 0 && (
                    <div className="search-results-dropdown" role="listbox">
                      {searchResults.map((cand) => (
                        <button
                          key={`${cand.name}-${cand.latitude}-${cand.longitude}`}
                          type="button"
                          className="search-result-item"
                          onClick={() => handleSelectCandidate(cand)}
                        >
                          <div className="result-item-main">
                            <span className="result-loc-pin">📍</span>
                            <div className="result-loc-info">
                              <strong className="result-loc-name">{cand.name}</strong>
                              <span className="result-loc-meta">
                                {[cand.city, cand.state, cand.country].filter(Boolean).join(', ')} ·{' '}
                                {cand.latitude.toFixed(2)}°N, {cand.longitude.toFixed(2)}°E
                              </span>
                            </div>
                          </div>
                          <span className={`result-tag ${cand.is_coastal ? 'tag-coastal' : 'tag-inland'}`}>
                            {cand.is_coastal ? 'COASTAL' : 'INLAND'}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* 3 Action Buttons (Search, Use Current Position, Select on Map) */}
                <div className="panel-action-buttons">
                  <button
                    type="button"
                    className="btn-action-marine btn-action-search"
                    onClick={() => executeSearch(searchQuery)}
                    aria-label="Execute search"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    <span>Search</span>
                  </button>

                  <button
                    type="button"
                    className="btn-action-marine btn-action-gps"
                    onClick={handleUseCurrentLocation}
                    disabled={isGeoLocating}
                    aria-label="Use Current Position via GPS"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <polygon points="3 11 22 2 13 21 11 13 3 11" />
                    </svg>
                    <span>{isGeoLocating ? 'Detecting GPS...' : 'Use Current Position'}</span>
                  </button>

                  <button
                    type="button"
                    className="btn-action-marine btn-action-map"
                    onClick={() => navigate('/maps?draw=1')}
                    aria-label="Select on interactive GIS map"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
                    </svg>
                    <span>Select on Map</span>
                  </button>
                </div>

                {/* Error Notice / GPS Warning */}
                {displayErrorMessage && (
                  <div className="panel-alert-banner" role="alert">
                    <span className="alert-icon">⚠️</span>
                    <span className="alert-text">{displayErrorMessage}</span>
                  </div>
                )}

                {/* Quick Access Locations (3x2 Grid Shortcuts) */}
                <div className="coastal-operating-section">
                  <span className="section-label">
                    <span className="section-label-icon">⚓</span> QUICK ACCESS LOCATIONS
                  </span>
                  <div className="coastal-buttons-grid">
                    {popularLocations.slice(0, 6).map((loc) => {
                      const isSelected = Boolean(
                        hasSelectedLocation &&
                        (selectedLocation.name === loc.name || selectedLocation.city === loc.city)
                      );
                      return (
                        <button
                          key={loc.name}
                          type="button"
                          className={`coastal-loc-btn ${isSelected ? 'active' : ''}`}
                          onClick={() => handleSelectPopular(loc)}
                          aria-pressed={isSelected}
                        >
                          {isSelected && <span className="btn-check-icon" aria-hidden="true">✓</span>}
                          <span>{loc.city || loc.name}</span>
                        </button>
                      );
                    })}
                  </div>
                  <div className="quick-access-helper-text">
                    Search any location or select a point on the map.
                  </div>
                </div>

                {/* State-Driven Location Summary Box */}
                <div className="location-state-container">
                  {isResolving ? (
                    <div className="state-resolving-box">
                      <span className="resolving-radar-pulse" />
                      <div className="resolving-text">
                        <strong>Resolving location...</strong>
                        <span>Verifying oceanographic boundaries and coastal proximity</span>
                      </div>
                    </div>
                  ) : isInland ? (
                    <div className="state-inland-box">
                      <div className="inland-header">
                        <span className="inland-badge">INLAND TERRITORY</span>
                        <span className="inland-distance">
                          {activeValidation.distance_to_coast_km
                            ? `${activeValidation.distance_to_coast_km.toFixed(0)} km to ocean`
                            : 'No marine waters'}
                        </span>
                      </div>
                      <strong className="inland-name">{activeValidation.location_name || selectedLocation.name}</strong>
                      <p className="inland-reason">
                        {activeValidation.reason ||
                          'No seashore or marine area found at this location. OCEANIS delivers specialized maritime intelligence for coastal and offshore waters.'}
                      </p>
                    </div>
                  ) : isCoastalReady ? (
                    <div className="state-selected-box">
                      <div className="selected-box-header">
                        <span className="sel-operating-title">SELECTED OPERATING AREA</span>
                        <span className="sel-port-badge">
                          {selectedLocation.isPort ? 'PORT & HARBOUR' : 'COASTAL ZONE'}
                        </span>
                      </div>
                      <div className="selected-box-body">
                        <svg className="sel-marine-pin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                          <circle cx="12" cy="10" r="3" />
                        </svg>
                        <div className="sel-marine-details">
                          <strong className="sel-marine-name">
                            {selectedLocation.name}
                            {selectedLocation.state ? `, ${selectedLocation.state}` : ''}
                          </strong>
                          <span className="sel-marine-coords">
                            {selectedLocation.coordinates} · {selectedLocation.portName || selectedLocation.marine_context || 'Bay of Bengal / Coastal Shelf'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="state-empty-box">
                      <div className="empty-box-header">
                        <span className="empty-marine-badge">LOCATION REQUIRED</span>
                      </div>
                      <span className="empty-marine-text">
                        Select a location to view marine spatial intelligence.
                      </span>
                    </div>
                  )}
                </div>

                {/* Panel Footer & Primary CTA Button */}
                <div className="panel-footer-section">
                  <button
                    type="button"
                    className={`btn-continue-marine ${isCtaEnabled ? 'enabled' : 'disabled'}`}
                    onClick={handleContinueToIntelligence}
                    disabled={!isCtaEnabled}
                    aria-disabled={!isCtaEnabled}
                  >
                    <span>Continue to Marine Intelligence →</span>
                  </button>
                  <span className="panel-telemetry-note">
                    Authoritative marine observations and forecasts from INCOIS, IMD and Copernicus Marine.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Institutional Data Source Strip matching Reference 1 */}
        <div className="landing-bottom-data-strip">
          <div className="bottom-strip-container">
            {/* Left side: INDIAN OCEAN & Institutional Data Sources */}
            <div className="bottom-left-sources">
              <span className="ocean-region-label">I N D I A N &nbsp; O C E A N</span>
              
              <div className="institutional-source-item" onClick={() => navigate('/data-sources')}>
                <div className="source-icon-wrap">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M2 12c3-3 6-3 9 0s6 3 9 0" />
                    <path d="M2 17c3-3 6-3 9 0s6 3 9 0" />
                    <path d="M2 7c3-3 6-3 9 0s6 3 9 0" />
                  </svg>
                </div>
                <div className="source-text-block">
                  <strong className="source-org">INCOIS</strong>
                  <span className="source-desc">Ocean Observations</span>
                </div>
              </div>

              <div className="institutional-source-item" onClick={() => navigate('/safety')}>
                <div className="source-icon-wrap">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                  </svg>
                </div>
                <div className="source-text-block">
                  <strong className="source-org">IMD</strong>
                  <span className="source-desc">Weather &amp; Warnings</span>
                </div>
              </div>

              <div className="institutional-source-item" onClick={() => navigate('/earth-observation')}>
                <div className="source-icon-wrap">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="8" />
                    <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
                    <path d="M2 12h20" />
                  </svg>
                </div>
                <div className="source-text-block">
                  <strong className="source-org">Copernicus Marine</strong>
                  <span className="source-desc">Satellite Data</span>
                </div>
              </div>
            </div>

            {/* Right side: PEOPLE | OCEAN | SAFETY | SUSTAINABLE TOMORROW */}
            <div className="bottom-right-motto">
              <span>PEOPLE &nbsp;|&nbsp; OCEAN &nbsp;|&nbsp; SAFETY &nbsp;|&nbsp; SUSTAINABLE TOMORROW</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
