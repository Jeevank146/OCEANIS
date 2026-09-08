import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLocationContext, type LocationInfo } from '../../context/LocationContext';
import { searchLocations, type LocationCandidate } from '../../services/api';
import './HomePage.css';

// 10 High-Quality Project-Relevant Maritime Images
import heroGisImg from '../../assets/images/geospatial_gis_coastline.jpg';
import heroHarbourImg from '../../assets/images/coastal_harbour_port.jpg';
import heroSatelliteImg from '../../assets/images/hero_satellite_earth.jpg';
import heroSstChlorophyllImg from '../../assets/images/ocean_sst_chlorophyll.jpg';
import heroWavesImg from '../../assets/images/hero_ocean_waves.jpg';
import heroFishingImg from '../../assets/images/hero_coastal_fishing.jpg';
import heroVesselImg from '../../assets/images/marine_operations_vessel.jpg';
import heroCycloneImg from '../../assets/images/satellite_cyclone_radar.jpg';
import heroSafetyImg from '../../assets/images/hero_maritime_safety.jpg';
import heroSunsetImg from '../../assets/images/sunset_ocean_cta.jpg';

const backgroundSlides = [
  { img: heroGisImg, label: 'Indian Coastline & Satellite GIS Radar' },
  { img: heroHarbourImg, label: 'Bay of Bengal Deepwater Port Operations' },
  { img: heroSatelliteImg, label: 'Indian Ocean Earth Observation & Remote Sensing' },
  { img: heroSstChlorophyllImg, label: 'Sentinel-3 Ocean Colour, Chlorophyll & SST Gradients' },
  { img: heroWavesImg, label: 'Hydrodynamics, Ocean Currents & Wave Models' },
  { img: heroFishingImg, label: 'Coastal Fishing Fleets & Potential Fishing Zones' },
  { img: heroVesselImg, label: 'Maritime Operations & Oceanographic Research Vessels' },
  { img: heroCycloneImg, label: 'Cyclone Tracking & Severe Maritime Weather Systems' },
  { img: heroSafetyImg, label: 'Navigational Safety & Search and Rescue Boundaries' },
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
  const [customError, setCustomError] = useState<string | null>(null);

  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchContainerRef = useRef<HTMLDivElement | null>(null);
  const carouselTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

    // If input looks like coordinates (e.g. 16.20, 82.50), don't query autocomplete
    const isCoordinateLike = /^[-+]?\d{1,3}(?:\.\d+)?[,\s]+[-+]?\d{1,3}(?:\.\d+)?$/.test(trimmed);
    if (isCoordinateLike) {
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
        const res = await searchLocations(trimmed, 8);
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
    setCustomError(null);
    clearValidationError();
    await validateAndSetCoordinates(candidate.latitude, candidate.longitude, candidate.name);
  };

  const executeLocationSearch = async () => {
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      setCustomError('Please enter a coastal area, port name, or coordinates to search.');
      return;
    }

    setIsDropdownOpen(false);
    setGpsNotice(null);
    setCustomError(null);
    clearValidationError();

    // Check if input is formatted as coordinates (e.g. "16.20, 82.50" or "17.6868 83.2185")
    const coordMatch = trimmed.match(/^([-+]?\d{1,3}(?:\.\d+)?)[,\s]+([-+]?\d{1,3}(?:\.\d+)?)$/);
    if (coordMatch) {
      const lat = parseFloat(coordMatch[1]);
      const lon = parseFloat(coordMatch[2]);
      if (!isNaN(lat) && !isNaN(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        const res = await validateAndSetCoordinates(
          lat,
          lon,
          `Coordinates (${lat.toFixed(4)}, ${lon.toFixed(4)})`
        );
        if (res.status === 'UNRESOLVED') {
          setCustomError('Location could not be resolved. Try another location or select a point on the map.');
        }
        return;
      } else {
        setCustomError('Invalid coordinates. Latitude must be between -90 and 90, Longitude between -180 and 180.');
        return;
      }
    }

    // Name-based resolution
    const res = await validateAndSetQuery(trimmed);
    if (res.status === 'UNRESOLVED') {
      setCustomError('Location could not be resolved. Try another location or select a point on the map.');
    }
  };

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await executeLocationSearch();
  };

  const handleSearchBtnClick = async () => {
    if (!searchQuery.trim()) {
      if (searchInputRef.current) {
        searchInputRef.current.focus();
      }
      setCustomError('Please enter a location name or coordinates in the search box.');
      return;
    }
    await executeLocationSearch();
  };

  const handleUseCurrentLocation = async () => {
    setIsGeoLocating(true);
    setGpsNotice(null);
    setCustomError(null);
    clearValidationError();
    try {
      const res = await useCurrentLocation();
      setSearchQuery('');
      setIsDropdownOpen(false);
      if (res.status === 'UNRESOLVED') {
        setGpsNotice(res.reason || 'Location access was not granted. Search for a location or select one on the map.');
      } else {
        setGpsNotice(null);
      }
    } catch (e: any) {
      console.error('Current location error', e);
      setGpsNotice('Location access was not granted. Search for a location or select one on the map.');
    } finally {
      setIsGeoLocating(false);
    }
  };

  const handleSelectPopular = (loc: LocationInfo) => {
    setGpsNotice(null);
    setCustomError(null);
    clearValidationError();
    setSelectedLocation(loc);
    setSearchQuery('');
    setIsDropdownOpen(false);
  };

  // Location resolution states
  const isResolving = isValidating || isSearching || isGeoLocating;
  const hasSelectedLocation = Boolean(
    selectedLocation &&
    selectedLocation.name &&
    activeValidation &&
    activeValidation.status &&
    activeValidation.status !== 'UNRESOLVED'
  );

  const isInland = hasSelectedLocation && activeValidation.status === 'INLAND';
  const isCoastalReady = hasSelectedLocation && !isInland;
  const isCtaEnabled = isCoastalReady && !isResolving;

  const handleContinueToIntelligence = () => {
    if (!isCtaEnabled) return;
    const locParam = encodeURIComponent(selectedLocation.city || selectedLocation.name);
    navigate(`/dashboard?location=${locParam}`);
  };

  const displayErrorMessage = customError || validationError || gpsNotice;

  return (
    <div className="landing-page-root">
      {/* Full-Screen Institutional Marine Hero Section */}
      <section className="landing-hero-section">
        {/* Dynamic 10-Image Carousel with Optimized Maritime Overlays */}
        <div className="landing-bg-carousel">
          {backgroundSlides.map((slide, idx) => (
            <div
              key={idx}
              className={`landing-bg-slide ${idx === bgIndex ? 'active' : ''}`}
              style={{ backgroundImage: `url(${slide.img})` }}
              role="img"
              aria-label={slide.label}
            />
          ))}
          {/* Institutional Navy & Gradient Overlays */}
          <div className="landing-overlay-base" />
          <div className="landing-overlay-gradient" />
          <div className="landing-overlay-vignette" />
        </div>

        {/* Carousel Manual Navigation Controls */}
        <div className="carousel-controls-bar" aria-label="Background image controls">
          <button
            type="button"
            className="btn-carousel-nav btn-prev"
            onClick={handlePrevSlide}
            title="Previous background image"
            aria-label="Previous background image"
          >
            ←
          </button>

          <div className="carousel-pagination-strip" role="tablist" aria-label="Image slide indicators">
            {backgroundSlides.map((slide, idx) => (
              <button
                key={idx}
                type="button"
                className={`pagination-dot ${idx === bgIndex ? 'active' : ''}`}
                onClick={() => handleJumpSlide(idx)}
                title={`Slide ${idx + 1}: ${slide.label}`}
                aria-label={`Slide ${idx + 1}: ${slide.label}`}
                aria-selected={idx === bgIndex}
                role="tab"
              >
                <span className="dot-fill" />
              </button>
            ))}
          </div>

          <button
            type="button"
            className="btn-carousel-nav btn-next"
            onClick={handleNextSlide}
            title="Next background image"
            aria-label="Next background image"
          >
            →
          </button>
        </div>

        {/* Hero Foreground Content */}
        <div className="landing-hero-container">
          <div className="landing-hero-grid">
            {/* Left Hero Column: Official Marine Intelligence Title & Capabilities */}
            <div className="landing-left-col">
              <div className="landing-platform-badge">
                <span className="badge-beacon-dot" />
                <span className="badge-text">MARINE INTELLIGENCE & DECISION SUPPORT</span>
              </div>

              <h1 className="landing-headline">
                Integrated Marine Intelligence for Safer Decisions
              </h1>

              <p className="landing-supporting-text">
                Integrated marine observations, satellite intelligence, environmental conditions and safety information for informed maritime decisions.
              </p>

              {/* Verified Maritime Capability Cards (Clickable & Accessible) */}
              <div className="landing-capabilities-grid">
                <button
                  type="button"
                  className="capability-card"
                  onClick={() => navigate('/marine-conditions')}
                  title="Explore Real-Time Hydrodynamic Intelligence"
                >
                  <div className="cap-icon-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M2 12h20M2 12a10 10 0 0 1 20 0M2 12a10 10 0 0 0 20 0" />
                      <circle cx="12" cy="12" r="4" />
                    </svg>
                  </div>
                  <div className="cap-text">
                    <strong>Hydrodynamic Intelligence</strong>
                    <span>Wave height, swell, currents & ocean forecasts</span>
                  </div>
                </button>

                <button
                  type="button"
                  className="capability-card"
                  onClick={() => navigate('/agents')}
                  title="Explore 6 Specialized Domain Agents"
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
                    <span>6 specialized AI domain agents synthesizing live intelligence</span>
                  </div>
                </button>

                <button
                  type="button"
                  className="capability-card"
                  onClick={() => navigate('/safety')}
                  title="Explore Cyclone Tracking & Early Hazard Warnings"
                >
                  <div className="cap-icon-box">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                  </div>
                  <div className="cap-text">
                    <strong>Marine Hazard Monitoring</strong>
                    <span>Cyclone tracking, high swell & maritime alerts</span>
                  </div>
                </button>
              </div>
            </div>

            {/* Right Hero Column: Professional Translucent Dark Marine Operating Area Panel */}
            <div className="landing-right-card-wrapper">
              <div className="marine-operating-panel">
                {/* Panel Top Heading & Badge */}
                <div className="panel-header-section">
                  <div className="panel-badge-row">
                    <span className="panel-institutional-badge">MARINE OPERATING AREA</span>
                    {hasSelectedLocation && (
                      <span className={`panel-status-pill ${isInland ? 'status-inland' : 'status-coastal'}`}>
                        {isInland ? 'INLAND DETECTED' : 'COASTAL ACTIVE'}
                      </span>
                    )}
                  </div>
                  <h2 className="panel-title">Select a Location</h2>
                  <p className="panel-subtitle">
                    Choose a coastal, offshore or map-defined area to access marine intelligence.
                  </p>
                </div>

                {/* Location Search Input Form with Enter & Submit */}
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

                  {/* Autocomplete Dropdown */}
                  {isDropdownOpen && (
                    <div className="search-autocomplete-dropdown" role="listbox">
                      {isSearching ? (
                        <div className="search-dropdown-state">
                          <span className="dropdown-spinner" />
                          <span>Searching coastal ports, stations & waters...</span>
                        </div>
                      ) : searchResults.length > 0 ? (
                        searchResults.map((item) => (
                          <button
                            key={item.id}
                            type="button"
                            className="autocomplete-item"
                            onClick={() => handleSelectCandidate(item)}
                            role="option"
                            aria-selected="false"
                          >
                            <span className="item-icon" aria-hidden="true">⚓</span>
                            <div className="item-meta">
                              <strong>{item.name}</strong>
                              <span>{item.display_name} · {item.is_coastal ? 'Coastal Waters' : 'Inland Sector'}</span>
                            </div>
                          </button>
                        ))
                      ) : (
                        <div className="search-dropdown-state">
                          <span>No location found. Press Enter or click Search to resolve.</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Primary Panel Action Buttons */}
                <div className="panel-action-buttons">
                  <button
                    type="button"
                    className="btn-action-marine btn-action-search"
                    onClick={handleSearchBtnClick}
                    aria-label="Search entered location"
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

                {/* Popular Coastal Operating Areas */}
                <div className="coastal-operating-section">
                  <span className="section-label">COASTAL OPERATING AREAS</span>
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
                </div>

                {/* State-Driven Location Summary Box */}
                <div className="location-state-container">
                  {isResolving ? (
                    /* STATE 3: Resolving */
                    <div className="state-resolving-box">
                      <span className="resolving-radar-pulse" />
                      <div className="resolving-text">
                        <strong>Resolving location...</strong>
                        <span>Verifying oceanographic boundaries and coastal proximity</span>
                      </div>
                    </div>
                  ) : isInland ? (
                    /* STATE 5: Inland */
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
                    /* STATE 2: Location Selected */
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
                    /* STATE 1: No Location Selected */
                    <div className="state-empty-box">
                      <span className="empty-marine-icon" aria-hidden="true">⚓</span>
                      <span className="empty-marine-text">
                        Select a location above or search to view marine intelligence.
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
                    Real-time observation & multi-agent synthesis from INCOIS, IMD & Copernicus Marine
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Platform Explore Strip */}
        <div className="landing-bottom-strip">
          <button
            type="button"
            className="btn-bottom-explore"
            onClick={() => navigate('/dashboard')}
            aria-label="Explore Operations Dashboard"
          >
            <span className="explore-text">Explore Marine Platform</span>
            <svg className="explore-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
