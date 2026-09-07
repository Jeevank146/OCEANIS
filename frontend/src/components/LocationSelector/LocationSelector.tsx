import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import {
  type LocationCandidate,
  type LocationValidationResult,
  searchLocations,
} from '../../services/api';
import './LocationSelector.css';

interface LocationSelectorProps {
  mode?: 'hero' | 'modal' | 'inline';
  onProceed?: () => void;
  onCancel?: () => void;
  showMapAction?: boolean;
}

export const LocationSelector: React.FC<LocationSelectorProps> = ({
  mode = 'hero',
  onProceed,
  showMapAction = true,
}) => {
  const navigate = useNavigate();
  const {
    activeValidation,
    isValidating,
    validateAndSetQuery,
    validateAndSetCoordinates,
    useCurrentLocation,
  } = useLocationContext();

  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<LocationCandidate[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [currentValResult, setCurrentValResult] = useState<LocationValidationResult | null>(null);
  const [isGeoLocating, setIsGeoLocating] = useState(false);

  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (evt: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(evt.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Dynamic debounced search based on user typing (no hardcoded fixed list)
  useEffect(() => {
    if (!query.trim() || query.trim().length < 2) {
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
        const res = await searchLocations(query.trim(), 8);
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
  }, [query]);

  // Handle selecting a candidate from dropdown
  const handleSelectCandidate = async (candidate: LocationCandidate) => {
    setIsDropdownOpen(false);
    setQuery('');
    const res = await validateAndSetCoordinates(candidate.latitude, candidate.longitude, candidate.name);
    setCurrentValResult(res);
  };

  // Handle manual search submit (e.g. user hits Enter)
  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsDropdownOpen(false);
    const res = await validateAndSetQuery(query.trim());
    setCurrentValResult(res);
  };

  // Handle "Use My Current Location"
  const handleUseCurrentLocation = async () => {
    setIsGeoLocating(true);
    try {
      const res = await useCurrentLocation();
      setCurrentValResult(res);
      setQuery('');
      setIsDropdownOpen(false);
    } catch (e) {
      console.error('Current location error', e);
    } finally {
      setIsGeoLocating(false);
    }
  };

  // Handle "Continue to OCEANIS"
  const handleContinue = () => {
    if (onProceed) {
      onProceed();
    } else {
      navigate('/dashboard');
    }
  };

  // Handle "Change Location" (Reset validation feedback to search again)
  const handleChangeLocationReset = () => {
    setCurrentValResult(null);
    setQuery('');
    setIsDropdownOpen(false);
  };

  // Active validation state to display (either newly validated in this component or active from context)
  const valToDisplay = currentValResult || activeValidation;
  const isCoastalOrMarine = valToDisplay.is_coastal || valToDisplay.is_marine;
  const isInland = valToDisplay.status === 'INLAND';
  const isUnresolved = valToDisplay.status === 'UNRESOLVED';

  return (
    <div className={`location-selector-root mode-${mode}`} ref={dropdownRef}>
      {/* Header */}
      <div className="loc-sel-header">
        <div className="loc-sel-eyebrow">
          <span className="pulse-dot" />
          <span>Location Intelligence</span>
        </div>
        <h2 className="loc-sel-title">Where are you operating from?</h2>
        <p className="loc-sel-subtitle">
          Enter any coastal port, fishing harbour, sea area, offshore coordinates or use current GPS location.
        </p>
      </div>

      {/* Location Search Bar with Dynamic Autocomplete Dropdown */}
      <div className="loc-search-container">
        <form onSubmit={handleSearchSubmit}>
          <div className="loc-search-input-wrap">
            <svg className="loc-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              className="loc-search-input"
              placeholder="Search coastal location, port, sea area or coordinates (e.g. Miami, Rotterdam, 17.68, 83.21)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => {
                if (searchResults.length > 0) setIsDropdownOpen(true);
              }}
              autoComplete="off"
            />
            {query && (
              <button
                type="button"
                className="loc-btn-clear"
                onClick={() => {
                  setQuery('');
                  setSearchResults([]);
                  setIsDropdownOpen(false);
                }}
                aria-label="Clear location search"
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
              <div className="loc-dropdown-loading">
                <span className="loc-dropdown-spinner" />
                <span>Searching coastal ports, waters & global locations...</span>
              </div>
            ) : searchResults.length > 0 ? (
              searchResults.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`loc-dropdown-item ${item.is_coastal ? 'is-coastal' : 'is-inland'}`}
                  onClick={() => handleSelectCandidate(item)}
                >
                  <span className="loc-dropdown-icon">
                    {item.is_coastal ? '⚓' : '📍'}
                  </span>
                  <div className="loc-dropdown-meta">
                    <div className="loc-dropdown-line1">
                      <span className="loc-dropdown-title">{item.name}</span>
                      <span className={`loc-type-tag ${item.is_coastal ? 'tag-coastal' : 'tag-inland'}`}>
                        {item.is_coastal ? 'Coastal' : 'Inland'}
                      </span>
                    </div>
                    <span className="loc-dropdown-sub">
                      {item.display_name} • {item.is_coastal ? `${item.distance_to_coast_km} km to sea` : `${item.distance_to_coast_km} km to coast`}
                    </span>
                  </div>
                </button>
              ))
            ) : (
              <div className="loc-dropdown-empty">
                <span>No matching location found. Press enter to search or enter coordinates (lat, lon).</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action Buttons: Geolocation & Map Option */}
      <div className="loc-action-row">
        <button
          type="button"
          className="loc-action-btn"
          onClick={handleUseCurrentLocation}
          disabled={isGeoLocating || isValidating}
        >
          {isGeoLocating ? (
            <svg className="loc-spinner-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" strokeDasharray="30" strokeLinecap="round" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="3 11 22 2 13 21 11 13 3 11" />
            </svg>
          )}
          <span>{isGeoLocating ? 'Detecting GPS...' : 'Use My Current Location'}</span>
        </button>

        {showMapAction && (
          <button
            type="button"
            className="loc-action-btn"
            onClick={() => {
              if (onProceed) onProceed();
              navigate('/live-map');
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
            </svg>
            <span>Select on Map</span>
          </button>
        )}
      </div>

      {/* ====================================================================
          VALIDATION FEEDBACK PANELS
          ==================================================================== */}

      {/* 1. VALID COASTAL / MARINE LOCATION */}
      {isCoastalOrMarine && !isInland && !isUnresolved && (
        <div className="loc-validation-panel valid-coastal">
          <div className="loc-val-header">
            <span className="loc-val-icon">📍</span>
            <div className="loc-val-title-box">
              <span className="loc-val-name">{valToDisplay.location_name}</span>
              <div className="loc-val-status-row">
                <span>Coastal location detected ✓</span>
              </div>
              <p className="loc-val-desc">
                Marine intelligence available for this area.
              </p>
            </div>
          </div>

          <div className="loc-val-meta-pills">
            {valToDisplay.marine_context && (
              <span className="loc-val-pill">🌊 {valToDisplay.marine_context}</span>
            )}
            {valToDisplay.coordinates_formatted && (
              <span className="loc-val-pill">📐 {valToDisplay.coordinates_formatted}</span>
            )}
            {valToDisplay.nearest_port && (
              <span className="loc-val-pill">⚓ {valToDisplay.nearest_port}</span>
            )}
          </div>

          <button
            type="button"
            className="loc-btn-continue"
            onClick={handleContinue}
          >
            <span>Continue to OCEANIS</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </div>
      )}

      {/* 2. INLAND LOCATION (STRICT BLOCK WITH GUIDANCE) */}
      {isInland && (
        <div className="loc-validation-panel inland-block">
          <div className="loc-val-header">
            <span className="loc-val-icon">📍</span>
            <div className="loc-val-title-box">
              <span className="loc-val-name">{valToDisplay.location_name}</span>
              <div className="loc-val-status-row">
                <span>⚠️ No seashore or marine area found at this location.</span>
              </div>
            </div>
          </div>

          <div className="loc-inland-guide">
            Please select a coastal location, port, fishing harbour, or sea area to use OCEANIS marine intelligence.
          </div>

          <button
            type="button"
            className="loc-btn-change-location"
            onClick={handleChangeLocationReset}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
            <span>Change Location</span>
          </button>
        </div>
      )}

      {/* 3. UNRESOLVED / ERROR LOCATION */}
      {isUnresolved && (
        <div className="loc-validation-panel unresolved-block">
          <div className="loc-val-header">
            <span className="loc-val-icon">⚠️</span>
            <div className="loc-val-title-box">
              <span className="loc-val-name">{valToDisplay.location_name || 'Location Not Found'}</span>
              <p className="loc-val-desc">
                {valToDisplay.reason || '⚠️ Location could not be resolved. Please verify spelling or provide coordinates (e.g. 17.68, 83.21).'}
              </p>
            </div>
          </div>

          <button
            type="button"
            className="loc-btn-retry"
            onClick={handleChangeLocationReset}
          >
            <span>Try Another Location</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default LocationSelector;
