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
  } = useLocationContext();

  const [bgIndex, setBgIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<LocationCandidate[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isGeoLocating, setIsGeoLocating] = useState(false);

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
    }, 240);

    return () => {
      if (searchDebounceRef.current) {
        clearTimeout(searchDebounceRef.current);
      }
    };
  }, [searchQuery]);

  const handleSelectCandidate = async (candidate: LocationCandidate) => {
    setIsDropdownOpen(false);
    setSearchQuery('');
    await validateAndSetCoordinates(candidate.latitude, candidate.longitude, candidate.name);
  };

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsDropdownOpen(false);
    await validateAndSetQuery(searchQuery.trim());
  };

  const handleUseCurrentLocation = async () => {
    setIsGeoLocating(true);
    try {
      await useCurrentLocation();
      setSearchQuery('');
      setIsDropdownOpen(false);
    } catch (e) {
      console.error('Current location error', e);
    } finally {
      setIsGeoLocating(false);
    }
  };

  const handleSelectPopular = (loc: LocationInfo) => {
    setSelectedLocation(loc);
    setSearchQuery('');
    setIsDropdownOpen(false);
  };

  const isLocationValid = Boolean(
    selectedLocation &&
    selectedLocation.name &&
    (selectedLocation.is_coastal !== false && selectedLocation.is_marine !== false) &&
    activeValidation.status !== 'INLAND' &&
    activeValidation.status !== 'UNRESOLVED'
  );

  const handleGetLiveInfo = () => {
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
            {/* Left Column: Mission & Capabilities */}
            <div className="landing-left-content">
              <div className="landing-eyebrow-pill">
                <span className="eyebrow-beacon-dot" />
                <span className="eyebrow-text">INDIAN COASTAL INTELLIGENCE</span>
              </div>

              <h1 className="landing-headline">
                Safer Seas<br />
                <span className="landing-headline-gradient">Brighter Tomorrows</span>
              </h1>

              <p className="landing-supporting-text">
                Real-time ocean conditions, satellite intelligence, safety alerts and decision support for coastal communities, fishermen, and maritime authorities.
              </p>

              {/* Action Buttons */}
              <div className="landing-cta-row">
                <button
                  type="button"
                  className="btn-landing-primary"
                  onClick={() => navigate('/maps')}
                >
                  <span>Explore Live Map</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>

                <button
                  type="button"
                  className="btn-landing-secondary"
                  onClick={() => navigate('/ask')}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                  <span>Ask OCEANIS</span>
                </button>
              </div>

              {/* Bottom Feature Capabilities Row */}
              <div className="landing-features-strip">
                <div className="feature-item">
                  <span className="feature-title">Satellite Data</span>
                  <span className="feature-detail">MODIS • Sentinel-3</span>
                </div>
                <div className="feature-divider" />
                <div className="feature-item">
                  <span className="feature-title">Real-time Conditions</span>
                  <span className="feature-detail">Waves • Currents • Wind</span>
                </div>
                <div className="feature-divider" />
                <div className="feature-item">
                  <span className="feature-title">Safety Alerts</span>
                  <span className="feature-detail">Cyclones • Hazard Zones</span>
                </div>
                <div className="feature-divider" />
                <div className="feature-item">
                  <span className="feature-title">For Coastal Communities</span>
                  <span className="feature-detail">Fishermen • Authorities • Fleet</span>
                </div>
              </div>
            </div>

            {/* Right Column: Location Selection Card */}
            <div className="landing-right-card-wrapper">
              <div className="landing-location-card" ref={searchContainerRef}>
                <div className="loc-card-top">
                  <span className="loc-card-badge">LIVE SECTOR TELEMETRY</span>
                  <h2 className="loc-card-title">Select Your Location</h2>
                  <p className="loc-card-desc">
                    Enter a coastal location to view real-time ocean conditions and safety information.
                  </p>
                </div>

                {/* Location Search Box */}
                <div className="loc-search-box">
                  <form onSubmit={handleSearchSubmit}>
                    <div className="search-input-wrapper">
                      <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8" />
                        <line x1="21" y1="21" x2="16.65" y2="16.65" />
                      </svg>
                      <input
                        type="text"
                        className="loc-search-input"
                        placeholder="Search coastal area, city, port or coordinates..."
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
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </form>

                  {/* Dynamic Dropdown Results */}
                  {isDropdownOpen && (
                    <div className="loc-search-dropdown">
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
                          >
                            <span className="res-icon">⚓</span>
                            <div className="res-meta">
                              <strong>{item.name}</strong>
                              <span>{item.display_name} • {item.is_coastal ? 'Coastal' : 'Inland'}</span>
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

                {/* Quick Action Options */}
                <div className="loc-quick-actions">
                  <button
                    type="button"
                    className="btn-quick-action"
                    onClick={() => {
                      const input = document.querySelector('.loc-search-input') as HTMLInputElement;
                      if (input) input.focus();
                    }}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="3 11 22 2 13 21 11 13 3 11" />
                    </svg>
                    <span>{isGeoLocating ? 'GPS Detecting...' : 'Use My Location'}</span>
                  </button>

                  <button
                    type="button"
                    className="btn-quick-action"
                    onClick={() => navigate('/maps?draw=1')}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
                    </svg>
                    <span>Draw on Map</span>
                  </button>
                </div>

                {/* Popular Locations */}
                <div className="popular-locations-section">
                  <span className="pop-label">Popular Coastal Locations</span>
                  <div className="popular-chips-grid">
                    {popularLocations.map((loc) => {
                      const isSelected = (selectedLocation.name === loc.name || selectedLocation.city === loc.city);
                      return (
                        <button
                          key={loc.name}
                          type="button"
                          className={`pop-chip-btn ${isSelected ? 'active' : ''}`}
                          onClick={() => handleSelectPopular(loc)}
                        >
                          {isSelected && <span className="chip-check">✓</span>}
                          <span>{loc.city || loc.name}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Active Selected Location Display Card */}
                {selectedLocation && selectedLocation.name && (
                  <div className="selected-location-display">
                    <div className="sel-loc-header">
                      <span className="sel-loc-label">Active Coastal Station</span>
                      <span className="sel-loc-status">VALIDATED COASTAL</span>
                    </div>
                    <div className="sel-loc-body">
                      <svg className="sel-loc-pin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                        <circle cx="12" cy="10" r="3" />
                      </svg>
                      <div className="sel-loc-details">
                        <strong className="sel-loc-name">{selectedLocation.name}, {selectedLocation.state}</strong>
                        <span className="sel-loc-coords">{selectedLocation.coordinates} • {selectedLocation.portName || 'Coastal Sector'}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Card Footer & Action Button */}
                <div className="loc-card-footer">
                  <button
                    type="button"
                    className="btn-get-live-info"
                    onClick={handleGetLiveInfo}
                    disabled={!isLocationValid}
                  >
                    <span>Get Live Information</span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                  </button>
                  <span className="telemetry-notice">
                    Direct live feeds from INCOIS, IMD Doppler Radar, ISRO & Copernicus Sentinel-3
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Subtle Scroll / Enter Indicator */}
        <div className="landing-bottom-indicator">
          <button
            type="button"
            className="btn-scroll-indicator"
            onClick={() => navigate('/dashboard')}
          >
            <span className="scroll-text">Scroll to explore</span>
            <svg className="scroll-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
