import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  type LocationCandidate,
  type LocationValidationResult,
  validateLocation,
  reverseGeocodeLocation,
  getLocationSuggestions,
} from '../services/api';

export interface LocationInfo {
  name: string;
  city: string;
  state: string;
  coordinates: string;
  lat: number;
  lon: number;
  isPort: boolean;
  portName?: string;
  region: 'East Coast' | 'West Coast' | 'Island Territory' | 'Inland Area' | 'International Waters';
  is_coastal?: boolean;
  is_marine?: boolean;
  distance_to_coast_km?: number | null;
  marine_context?: string | null;
  status?: string;
}

export const POPULAR_LOCATIONS: LocationInfo[] = [
  {
    name: 'Visakhapatnam Coast',
    city: 'Visakhapatnam',
    state: 'Andhra Pradesh',
    coordinates: '17.6868° N, 83.2185° E',
    lat: 17.6868,
    lon: 83.2185,
    isPort: true,
    portName: 'Visakhapatnam Port (VPT)',
    region: 'East Coast',
    is_coastal: true,
    is_marine: true,
    distance_to_coast_km: 0.5,
    marine_context: 'Bay of Bengal • Andhra Coastal Shelf',
    status: 'VALID_COASTAL',
  },
  {
    name: 'Kakinada Coast',
    city: 'Kakinada',
    state: 'Andhra Pradesh',
    coordinates: '16.9891° N, 82.2475° E',
    lat: 16.9891,
    lon: 82.2475,
    isPort: true,
    portName: 'Kakinada Deepwater Port',
    region: 'East Coast',
    is_coastal: true,
    is_marine: true,
    distance_to_coast_km: 0.2,
    marine_context: 'Bay of Bengal • Godavari Delta Fairway',
    status: 'VALID_COASTAL',
  },
  {
    name: 'Chennai Coast',
    city: 'Chennai',
    state: 'Tamil Nadu',
    coordinates: '13.0827° N, 80.2707° E',
    lat: 13.0827,
    lon: 80.2707,
    isPort: true,
    portName: 'Chennai Port',
    region: 'East Coast',
    is_coastal: true,
    is_marine: true,
    distance_to_coast_km: 0.8,
    marine_context: 'Bay of Bengal • Coromandel Shelf',
    status: 'VALID_COASTAL',
  },
  {
    name: 'Mumbai Coast',
    city: 'Mumbai',
    state: 'Maharashtra',
    coordinates: '18.9400° N, 72.8350° E',
    lat: 18.9400,
    lon: 72.8350,
    isPort: true,
    portName: 'Mumbai Port (MbPT)',
    region: 'West Coast',
    is_coastal: true,
    is_marine: true,
    distance_to_coast_km: 0.5,
    marine_context: 'Arabian Sea • Konkan Sector',
    status: 'VALID_COASTAL',
  },
  {
    name: 'Kochi (Cochin) Coast',
    city: 'Kochi',
    state: 'Kerala',
    coordinates: '9.9312° N, 76.2673° E',
    lat: 9.9312,
    lon: 76.2673,
    isPort: true,
    portName: 'Cochin Port',
    region: 'West Coast',
    is_coastal: true,
    is_marine: true,
    distance_to_coast_km: 0.8,
    marine_context: 'Arabian Sea • Malabar Coast & Vembanad',
    status: 'VALID_COASTAL',
  },
  {
    name: 'Paradip Coast',
    city: 'Paradip',
    state: 'Odisha',
    coordinates: '20.2644° N, 86.6710° E',
    lat: 20.2644,
    lon: 86.6710,
    isPort: true,
    portName: 'Paradip Port',
    region: 'East Coast',
    is_coastal: true,
    is_marine: true,
    distance_to_coast_km: 0.5,
    marine_context: 'Bay of Bengal • Mahanadi Delta Shelf',
    status: 'VALID_COASTAL',
  },
];

export interface LocationContextType {
  // Primary Validated Location Result
  activeValidation: LocationValidationResult;
  // Legacy / Direct Access Location Info (Guarantees backward compatibility)
  selectedLocation: LocationInfo;
  popularLocations: LocationInfo[];
  recentLocations: LocationInfo[];
  suggestions: LocationCandidate[];
  // State indicators
  isValidating: boolean;
  validationError: string | null;
  isChangeModalOpen: boolean;
  setIsChangeModalOpen: (open: boolean) => void;
  // Action Handlers
  validateAndSetQuery: (query: string) => Promise<LocationValidationResult>;
  validateAndSetCoordinates: (lat: number, lon: number, label?: string) => Promise<LocationValidationResult>;
  useCurrentLocation: () => Promise<LocationValidationResult>;
  setActiveLocation: (loc: LocationInfo | LocationValidationResult | LocationCandidate | string) => void;
  setSelectedLocation: (loc: LocationInfo | string) => void;
  clearValidationError: () => void;
}

const DEFAULT_VALIDATION: LocationValidationResult = {
  status: 'VALID_COASTAL',
  is_coastal: true,
  is_marine: true,
  location_name: 'Visakhapatnam Coast',
  display_name: 'Visakhapatnam, Andhra Pradesh, India',
  city: 'Visakhapatnam',
  state: 'Andhra Pradesh',
  country: 'India',
  latitude: 17.6868,
  longitude: 83.2185,
  distance_to_coast_km: 0.5,
  nearest_port: 'Visakhapatnam Port (VPT)',
  marine_context: 'Bay of Bengal • Andhra Coastal Shelf',
  reason: 'Coastal location detected. Marine intelligence available for this area.',
  coordinates_formatted: '17.6868° N, 83.2185° E',
};

function candidateToValidation(candidate: LocationCandidate): LocationValidationResult {
  const isCoast = candidate.is_coastal || candidate.is_marine;
  const latFmt = `${Math.abs(candidate.latitude).toFixed(4)}° ${candidate.latitude >= 0 ? 'N' : 'S'}`;
  const lonFmt = `${Math.abs(candidate.longitude).toFixed(4)}° ${candidate.longitude >= 0 ? 'E' : 'W'}`;

  return {
    status: isCoast ? 'VALID_COASTAL' : 'INLAND',
    is_coastal: candidate.is_coastal,
    is_marine: candidate.is_marine,
    location_name: candidate.name,
    display_name: candidate.display_name,
    city: candidate.city,
    state: candidate.state,
    country: candidate.country || 'India',
    latitude: candidate.latitude,
    longitude: candidate.longitude,
    distance_to_coast_km: candidate.distance_to_coast_km,
    nearest_port: candidate.nearest_port,
    marine_context: candidate.marine_context,
    reason: isCoast
      ? 'Coastal location detected. Marine intelligence available for this area.'
      : `⚠️ No seashore or marine area found at this location (${candidate.distance_to_coast_km.toFixed(0)} km from nearest coast).`,
    coordinates_formatted: `${latFmt}, ${lonFmt}`,
  };
}

function validationToLocationInfo(v: LocationValidationResult): LocationInfo {
  let region: 'East Coast' | 'West Coast' | 'Island Territory' | 'Inland Area' | 'International Waters' = 'East Coast';
  if (v.country && v.country !== 'India' && v.country !== 'Global Marine') {
    region = 'International Waters';
  } else if (v.longitude && v.longitude < 77.5) {
    region = 'West Coast';
  } else if (v.longitude && v.longitude > 91.0) {
    region = 'Island Territory';
  }
  if (!v.is_coastal && !v.is_marine) {
    region = 'Inland Area';
  }

  const latFmt = v.latitude !== undefined && v.latitude !== null
    ? `${Math.abs(v.latitude).toFixed(4)}° ${v.latitude >= 0 ? 'N' : 'S'}`
    : '0.0000° N';
  const lonFmt = v.longitude !== undefined && v.longitude !== null
    ? `${Math.abs(v.longitude).toFixed(4)}° ${v.longitude >= 0 ? 'E' : 'W'}`
    : '0.0000° E';

  return {
    name: v.location_name,
    city: v.city || v.location_name.split(' ')[0],
    state: v.state || (v.country && v.country !== 'India' ? v.country : 'Coastal Sector'),
    coordinates: v.coordinates_formatted || `${latFmt}, ${lonFmt}`,
    lat: v.latitude ?? 0.0,
    lon: v.longitude ?? 0.0,
    isPort: Boolean(v.nearest_port),
    portName: v.nearest_port || undefined,
    region,
    is_coastal: v.is_coastal,
    is_marine: v.is_marine,
    distance_to_coast_km: v.distance_to_coast_km,
    marine_context: v.marine_context,
    status: v.status,
  };
}

const LocationContext = createContext<LocationContextType | undefined>(undefined);

export const LocationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeValidation, setActiveValidation] = useState<LocationValidationResult>(() => {
    const saved = localStorage.getItem('oceanis_active_validation_v2');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.warn('Failed to parse saved active location validation', e);
      }
    }
    return DEFAULT_VALIDATION;
  });

  const [suggestions, setSuggestions] = useState<LocationCandidate[]>([]);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isChangeModalOpen, setIsChangeModalOpen] = useState<boolean>(false);

  const [recentLocations, setRecentLocations] = useState<LocationInfo[]>([
    POPULAR_LOCATIONS[0],
    POPULAR_LOCATIONS[1],
    POPULAR_LOCATIONS[2],
  ]);

  // Fetch initial suggestions from backend on mount
  useEffect(() => {
    let isMounted = true;
    getLocationSuggestions()
      .then((res) => {
        if (isMounted && res.suggestions && res.suggestions.length > 0) {
          setSuggestions(res.suggestions);
        }
      })
      .catch((err) => {
        console.warn('Could not load suggestions from backend:', err);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Save active validation to local storage
  useEffect(() => {
    localStorage.setItem('oceanis_active_validation_v2', JSON.stringify(activeValidation));
    localStorage.setItem(
      'oceanis_active_location',
      JSON.stringify(validationToLocationInfo(activeValidation))
    );
  }, [activeValidation]);

  const clearValidationError = () => setValidationError(null);

  // 1. Validate and Set by text / candidate search query
  const validateAndSetQuery = useCallback(async (query: string): Promise<LocationValidationResult> => {
    setIsValidating(true);
    setValidationError(null);
    try {
      const res = await validateLocation({ query });
      if (res.is_coastal || res.is_marine) {
        setActiveValidation(res);
        const locInfo = validationToLocationInfo(res);
        setRecentLocations((prev) => [locInfo, ...prev.filter((p) => p.name !== locInfo.name)].slice(0, 5));
      }
      return res;
    } catch (err: any) {
      const fallbackMsg = err?.message || 'Location validation request failed';
      setValidationError(fallbackMsg);
      const errRes: LocationValidationResult = {
        status: 'UNRESOLVED',
        is_coastal: false,
        is_marine: false,
        location_name: query,
        display_name: `${query} (Unresolved)`,
        reason: fallbackMsg,
      };
      return errRes;
    } finally {
      setIsValidating(false);
    }
  }, []);

  // 2. Validate and Set by exact Latitude / Longitude
  const validateAndSetCoordinates = useCallback(
    async (lat: number, lon: number, label?: string): Promise<LocationValidationResult> => {
      setIsValidating(true);
      setValidationError(null);
      try {
        const res = await reverseGeocodeLocation(lat, lon, label);
        if (res.is_coastal || res.is_marine) {
          setActiveValidation(res);
          const locInfo = validationToLocationInfo(res);
          setRecentLocations((prev) => [locInfo, ...prev.filter((p) => p.name !== locInfo.name)].slice(0, 5));
        }
        return res;
      } catch (err: any) {
        const fallbackMsg = err?.message || 'Coordinate validation request failed';
        setValidationError(fallbackMsg);
        const errRes: LocationValidationResult = {
          status: 'UNRESOLVED',
          is_coastal: false,
          is_marine: false,
          location_name: `${lat.toFixed(4)}, ${lon.toFixed(4)}`,
          display_name: `Coordinates (${lat.toFixed(4)}, ${lon.toFixed(4)})`,
          latitude: lat,
          longitude: lon,
          reason: fallbackMsg,
        };
        return errRes;
      } finally {
        setIsValidating(false);
      }
    },
    []
  );

  // 3. Browser Geolocation Flow
  const useCurrentLocation = useCallback(async (): Promise<LocationValidationResult> => {
    setIsValidating(true);
    setValidationError(null);

    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        const errRes: LocationValidationResult = {
          status: 'UNRESOLVED',
          is_coastal: false,
          is_marine: false,
          location_name: 'Geolocation Unavailable',
          display_name: 'Geolocation is not supported by your browser',
          reason: 'Your browser does not support GPS / Geolocation services.',
        };
        setValidationError(errRes.reason);
        setIsValidating(false);
        resolve(errRes);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          try {
            const res = await reverseGeocodeLocation(latitude, longitude, 'Detected GPS Location');
            if (res.is_coastal || res.is_marine) {
              setActiveValidation(res);
              const locInfo = validationToLocationInfo(res);
              setRecentLocations((prev) => [locInfo, ...prev.filter((p) => p.name !== locInfo.name)].slice(0, 5));
            }
            resolve(res);
          } catch (err: any) {
            const fallbackMsg = err?.message || 'Failed to determine coastal status for your GPS position';
            setValidationError(fallbackMsg);
            resolve({
              status: 'UNRESOLVED',
              is_coastal: false,
              is_marine: false,
              location_name: `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`,
              display_name: 'Current Coordinates',
              latitude,
              longitude,
              reason: fallbackMsg,
            });
          } finally {
            setIsValidating(false);
          }
        },
        (error) => {
          let reasonMsg = 'Geolocation permission was denied.';
          if (error.code === error.POSITION_UNAVAILABLE) {
            reasonMsg = 'Location information is currently unavailable.';
          } else if (error.code === error.TIMEOUT) {
            reasonMsg = 'Location acquisition timed out.';
          }
          setValidationError(reasonMsg);
          setIsValidating(false);
          resolve({
            status: 'UNRESOLVED',
            is_coastal: false,
            is_marine: false,
            location_name: 'Current Location',
            display_name: 'Location access error',
            reason: reasonMsg,
          });
        },
        { timeout: 10000, enableHighAccuracy: true }
      );
    });
  }, []);

  // 4. Direct Set (Supports multiple types)
  const setActiveLocation = (
    loc: LocationInfo | LocationValidationResult | LocationCandidate | string
  ) => {
    if (typeof loc === 'string') {
      validateAndSetQuery(loc);
      return;
    }

    if ('is_coastal' in loc && 'status' in loc && typeof loc.status === 'string') {
      const v = loc as LocationValidationResult;
      setActiveValidation(v);
      const info = validationToLocationInfo(v);
      setRecentLocations((prev) => [info, ...prev.filter((p) => p.name !== info.name)].slice(0, 5));
      return;
    }

    if ('place_type' in loc) {
      const v = candidateToValidation(loc as LocationCandidate);
      setActiveValidation(v);
      const info = validationToLocationInfo(v);
      setRecentLocations((prev) => [info, ...prev.filter((p) => p.name !== info.name)].slice(0, 5));
      return;
    }

    const info = loc as LocationInfo;
    const v: LocationValidationResult = {
      status: info.is_coastal !== false ? 'VALID_COASTAL' : 'INLAND',
      is_coastal: info.is_coastal !== false,
      is_marine: info.is_marine !== false,
      location_name: info.name,
      display_name: `${info.name}, ${info.state}`,
      city: info.city,
      state: info.state,
      latitude: info.lat,
      longitude: info.lon,
      distance_to_coast_km: info.distance_to_coast_km ?? 0.5,
      nearest_port: info.portName,
      marine_context: info.marine_context ?? 'Coastal Waters',
      reason: 'Coastal location active',
      coordinates_formatted: info.coordinates,
    };
    setActiveValidation(v);
    setRecentLocations((prev) => [info, ...prev.filter((p) => p.name !== info.name)].slice(0, 5));
  };

  const setSelectedLocation = (loc: LocationInfo | string) => {
    setActiveLocation(loc);
  };

  const selectedLocation = validationToLocationInfo(activeValidation);

  return (
    <LocationContext.Provider
      value={{
        activeValidation,
        selectedLocation,
        popularLocations: POPULAR_LOCATIONS,
        recentLocations,
        suggestions,
        isValidating,
        validationError,
        isChangeModalOpen,
        setIsChangeModalOpen,
        validateAndSetQuery,
        validateAndSetCoordinates,
        useCurrentLocation,
        setActiveLocation,
        setSelectedLocation,
        clearValidationError,
      }}
    >
      {children}
    </LocationContext.Provider>
  );
};

export const useLocationContext = () => {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error('useLocationContext must be used within a LocationProvider');
  }
  return context;
};
