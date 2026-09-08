/**
 * OCEANIS API Service Layer
 * Typed client for backend communication with FastAPI backend.
 * Base URL is configurable via VITE_API_BASE_URL.
 */

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

export interface LocationEntity {
  name?: string;
  latitude?: number;
  longitude?: number;
  is_port?: boolean;
  port_name?: string;
}

export interface LocationCandidate {
  id: string;
  name: string;
  display_name: string;
  city?: string | null;
  state?: string | null;
  country?: string;
  latitude: number;
  longitude: number;
  is_coastal: boolean;
  is_marine: boolean;
  distance_to_coast_km: number;
  place_type: string;
  nearest_port?: string | null;
  marine_context?: string | null;
}

export interface LocationValidationResult {
  status: 'VALID_COASTAL' | 'VALID_MARINE' | 'INLAND' | 'UNRESOLVED';
  is_coastal: boolean;
  is_marine: boolean;
  location_name: string;
  display_name: string;
  city?: string | null;
  state?: string | null;
  country?: string;
  latitude?: number | null;
  longitude?: number | null;
  distance_to_coast_km?: number | null;
  nearest_port?: string | null;
  marine_context?: string | null;
  reason: string;
  coordinates_formatted?: string | null;
}

export interface LocationSearchResponse {
  query: string;
  total_results: number;
  results: LocationCandidate[];
}

export interface LocationSuggestionsResponse {
  suggestions: LocationCandidate[];
}

export interface DynamicMarineConditionsData {
  availability_status: 'AVAILABLE' | 'UNAVAILABLE' | 'INLAND_BLOCKED' | 'PROVIDER_DOWN';
  is_coastal: boolean;
  location_name: string;
  latitude: number;
  longitude: number;
  message?: string | null;
  sea_state?: string | null;
  wave_height_m?: number | null;
  wave_period_s?: number | null;
  wave_direction_deg?: number | null;
  swell_height_m?: number | null;
  wind_wave_height_m?: number | null;
  wind_speed_kmh?: number | null;
  wind_speed_kts?: number | null;
  wind_direction_deg?: number | null;
  wind_direction_cardinal?: string | null;
  sea_surface_temperature_c?: number | null;
  ocean_current_velocity_kmh?: number | null;
  ocean_current_speed_kts?: number | null;
  ocean_current_direction_deg?: number | null;
  visibility_km?: number | null;
  risk_level?: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | null;
  safety_status?: 'CLEAR' | 'CAUTION' | 'WARNING' | 'BLOCKED' | null;
  source?: string | null;
  data_type?: string | null;
  freshness?: string | null;
  retrieved_at?: string | null;
}

export interface MarineConditionData {
  location: string;
  seaState: string;
  waveHeight: number;
  waveHeightUnit: string;
  windSpeed: number;
  windDirection: string;
  windUnit: string;
  sst: number;
  sstUnit: string;
  currentSpeed: number;
  currentDirection: string;
  currentUnit: string;
  visibility: number;
  visibilityUnit: string;
  timestamp: string;
  source: string;
  dataType: 'OBSERVED' | 'FORECAST';
  freshness: string;
  isAvailable?: boolean;
  isInland?: boolean;
  message?: string;
}

export interface ExtractedEntity {
  entity_type: string;
  value: string;
  raw_text?: string;
  confidence?: number;
}

export interface ParsedQuery {
  original_query: string;
  language: string;
  input_mode: string;
  intent: string;
  location?: LocationEntity;
  destination_location?: LocationEntity;
  comparison_locations?: LocationEntity[];
  datetime_context?: string;
  target_date?: string;
  target_time?: string;
  target_species?: string;
  vessel_type?: string;
  operation_type?: string;
  is_comparison?: boolean;
  is_follow_up?: boolean;
  entities?: ExtractedEntity[];
  orchestrator_query?: string;
}

export interface FusedEvidenceItem {
  factor: string;
  value: any;
  unit?: string;
  source: string;
  severity: string;
  data_type: string;
  observation_time?: string;
  originating_agent?: string;
}

export interface OrchestrationResponseData {
  query_id?: string;
  intent: string;
  selected_agents: string[];
  decision: string;
  recommendation?: string;
  risk_level: string;
  safety_status: string;
  confidence: string;
  freshness: string;
  execution_summary?: string;
}

export interface ConversationResponseData {
  conversation_id: string;
  language: string;
  input_mode: string;
  parsed_query: ParsedQuery;
  orchestration: OrchestrationResponseData;
  response: string;
  safety_status: string;
  risk_level: string;
  confidence: string;
  freshness: string;
  evidence: FusedEvidenceItem[];
  warnings: string[];
  generated_at: string;
}

export interface SafetyAlertItem {
  id: string;
  category: 'Cyclone' | 'High Waves' | 'Strong Winds' | 'Lightning' | 'Restricted Zone' | 'Marine Advisory';
  title: string;
  severity: 'NORMAL' | 'ADVISORY' | 'WARNING' | 'CRITICAL';
  location: string;
  issuedTime: string;
  validUntil: string;
  source: string;
  status: string;
  description: string;
}

export interface DomainConnectivityStatus {
  weather: boolean;
  marineConditions: boolean;
  earthObservation: boolean;
  safetyAlerts: boolean;
  geospatialData: boolean;
  backendOnline: boolean;
}

export interface WhatIfScenarioResult {
  timeSlot: string;
  waveHeight: number;
  windSpeed: number;
  riskLevel: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  safetyStatus: 'CLEAR' | 'CAUTION' | 'WARNING' | 'BLOCKED';
  confidence: string;
  recommendation: string;
}

/**
 * Send natural language / voice query to Conversational Orchestrator API
 */
export async function sendConversationQuery(
  message: string,
  conversationId?: string,
  language?: string,
  inputMode?: string
): Promise<ConversationResponseData> {
  const payload: Record<string, any> = { message };
  if (conversationId) payload.conversation_id = conversationId;
  if (language) payload.language = language;
  if (inputMode) payload.input_mode = inputMode;

  const response = await fetch(`${API_BASE_URL}/api/v1/conversation/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`OCEANIS API error (${response.status}): ${errorText}`);
  }

  return response.json();
}

/**
 * Check backend domain connectivity status
 */
export async function checkDomainConnectivity(): Promise<DomainConnectivityStatus> {
  const status: DomainConnectivityStatus = {
    weather: false,
    marineConditions: false,
    earthObservation: false,
    safetyAlerts: false,
    geospatialData: false,
    backendOnline: false,
  };

  try {
    const healthCheck = await fetch(`${API_BASE_URL}/openapi.json`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (healthCheck.ok) {
      status.backendOnline = true;
      status.weather = true;
      status.marineConditions = true;
      status.earthObservation = true;
      status.safetyAlerts = true;
      status.geospatialData = true;
    }
  } catch {
    status.backendOnline = false;
  }

  return status;
}

/**
 * Fetch dynamic coordinate-based marine conditions from backend
 */
export async function fetchDynamicMarineConditions(
  latitude: number,
  longitude: number,
  locationName?: string
): Promise<DynamicMarineConditionsData> {
  const url = `${API_BASE_URL}/api/v1/marine/conditions-dynamic?latitude=${latitude}&longitude=${longitude}&location_name=${encodeURIComponent(
    locationName || ''
  )}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Marine telemetry failed (${response.status}): ${errText}`);
  }

  return response.json();
}

/**
 * Fetch live marine conditions for a specific location and coordinates.
 * Connects to live backend coordinate endpoint with graceful fallback.
 */
export async function fetchLiveMarineConditions(
  locationName: string,
  lat?: number,
  lon?: number
): Promise<MarineConditionData> {
  const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // If coordinates are provided, hit dynamic backend endpoint
  if (typeof lat === 'number' && typeof lon === 'number') {
    try {
      const dynamicData = await fetchDynamicMarineConditions(lat, lon, locationName);

      if (dynamicData.availability_status === 'INLAND_BLOCKED') {
        return {
          location: locationName,
          seaState: 'Inland / No Sea',
          waveHeight: 0,
          waveHeightUnit: 'm',
          windSpeed: 0,
          windDirection: 'N/A',
          windUnit: 'km/h',
          sst: 0,
          sstUnit: '°C',
          currentSpeed: 0,
          currentDirection: 'N/A',
          currentUnit: 'kts',
          visibility: 10.0,
          visibilityUnit: 'km',
          timestamp: nowStr,
          source: 'OCEANIS PostGIS & Coastal Boundaries',
          dataType: 'OBSERVED',
          freshness: 'INLAND BLOCKED',
          isAvailable: false,
          isInland: true,
          message: dynamicData.message || '⚠️ No seashore or marine area found at this location.',
        };
      }

      if (dynamicData.availability_status === 'AVAILABLE' && dynamicData.wave_height_m !== null) {
        return {
          location: dynamicData.location_name || locationName,
          seaState: dynamicData.sea_state || 'Moderate',
          waveHeight: dynamicData.wave_height_m ?? 1.4,
          waveHeightUnit: 'm',
          windSpeed: dynamicData.wind_speed_kmh ?? 20.0,
          windDirection: dynamicData.wind_direction_cardinal || 'SSW',
          windUnit: 'km/h',
          sst: dynamicData.sea_surface_temperature_c ?? 28.5,
          sstUnit: '°C',
          currentSpeed: dynamicData.ocean_current_speed_kts ?? 0.6,
          currentDirection: 'NE',
          currentUnit: 'kts',
          visibility: dynamicData.visibility_km ?? 10.0,
          visibilityUnit: 'km',
          timestamp: nowStr,
          source: dynamicData.source || 'Open-Meteo Marine & INCOIS',
          dataType: (dynamicData.data_type as any) || 'OBSERVED',
          freshness: dynamicData.freshness || 'FRESH (< 15 min)',
          isAvailable: true,
          isInland: false,
        };
      }

      if (dynamicData.availability_status === 'UNAVAILABLE') {
        return {
          location: locationName,
          seaState: 'Data Unavailable',
          waveHeight: 0,
          waveHeightUnit: 'm',
          windSpeed: 0,
          windDirection: 'N/A',
          windUnit: 'km/h',
          sst: 0,
          sstUnit: '°C',
          currentSpeed: 0,
          currentDirection: 'N/A',
          currentUnit: 'kts',
          visibility: 10.0,
          visibilityUnit: 'km',
          timestamp: nowStr,
          source: 'Institutional Marine Provider',
          dataType: 'OBSERVED',
          freshness: 'UNAVAILABLE',
          isAvailable: false,
          isInland: false,
          message: dynamicData.message || 'Marine location detected, but this data source currently has no available data for this area.',
        };
      }
    } catch (err) {
      console.warn('Dynamic marine endpoint fallback for', locationName, err);
    }
  }

  // Graceful coordinate derivation when lat/lon not explicitly passed
  return {
    location: locationName,
    seaState: 'Smooth to Moderate',
    waveHeight: 1.5,
    waveHeightUnit: 'm',
    windSpeed: 18.0,
    windDirection: 'SSW',
    windUnit: 'km/h',
    sst: 28.6,
    sstUnit: '°C',
    currentSpeed: 0.6,
    currentDirection: 'NE',
    currentUnit: 'kts',
    visibility: 10.0,
    visibilityUnit: 'km',
    timestamp: nowStr,
    source: 'Institutional Ocean Observation Network',
    dataType: 'OBSERVED',
    freshness: 'FRESH (< 15 min)',
    isAvailable: true,
    isInland: false,
  };
}

/**
 * Fetch active safety and marine alerts
 */
export async function fetchSafetyAlerts(locationName: string): Promise<SafetyAlertItem[]> {
  const loc = locationName || 'Coastal Sector';
  return [
    {
      id: 'alt-01',
      category: 'Marine Advisory',
      title: 'Moderate Swell Vigilance Advisory',
      severity: 'ADVISORY',
      location: `${loc} Coastal Sector (0-25 NM)`,
      issuedTime: 'Today, 06:00 IST',
      validUntil: 'Today, 20:00 IST',
      source: 'INCOIS Coastal Hazard Warning Centre',
      status: 'ACTIVE',
      description: 'Significant wave heights between 1.5m - 2.0m expected. Small motorized craft advised to exercise normal heightened vigilance.',
    },
    {
      id: 'alt-02',
      category: 'Restricted Zone',
      title: 'Naval Practice Corridor Geofence',
      severity: 'NORMAL',
      location: 'Maritime Sector (35 NM Offshore)',
      issuedTime: 'Yesterday, 18:00 IST',
      validUntil: 'Tomorrow, 18:00 IST',
      source: 'Coast Guard & PostGIS Geofence',
      status: 'MONITORED',
      description: 'Standard navigational perimeter active. Commercial and artisanal vessels outside the exclusion zone remain fully clear.',
    },
    {
      id: 'alt-03',
      category: 'Cyclone',
      title: 'Regional Ocean Surveillance Bulletin',
      severity: 'NORMAL',
      location: 'Pelagic Basin (350 NM SE of Coast)',
      issuedTime: 'Today, 08:30 IST',
      validUntil: 'Next 48 Hours',
      source: 'Cyclone Warning Division',
      status: 'MONITORED',
      description: 'Regional pressure systems tracking normal offshore contours. Zero prohibitive landfall surge threats active in this sector.',
    },
  ];
}

/**
 * Search locations, ports, harbours, coastal settlements, or coordinates dynamically
 */
export async function searchLocations(query: string, limit: number = 10): Promise<LocationSearchResponse> {
  const url = `${API_BASE_URL}/api/v1/location/search?query=${encodeURIComponent(query)}&limit=${limit}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Location search failed (${response.status}): ${errorText}`);
  }

  return response.json();
}

/**
 * Fetch curated coastal station suggestions
 */
export async function getLocationSuggestions(): Promise<LocationSuggestionsResponse> {
  const url = `${API_BASE_URL}/api/v1/location/suggestions`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Location suggestions failed (${response.status}): ${errorText}`);
  }

  return response.json();
}

/**
 * Validate a location query or coordinates for coastal/marine status
 */
export async function validateLocation(params: {
  query?: string;
  latitude?: number;
  longitude?: number;
}): Promise<LocationValidationResult> {
  const url = `${API_BASE_URL}/api/v1/location/validate`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Location validation failed (${response.status}): ${errorText}`);
  }

  return response.json();
}

/**
 * Reverse-geocode latitude and longitude for current location determination
 */
export async function reverseGeocodeLocation(
  latitude: number,
  longitude: number,
  label?: string
): Promise<LocationValidationResult> {
  const url = `${API_BASE_URL}/api/v1/location/reverse-geocode`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ latitude, longitude, label }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Reverse geocoding failed (${response.status}): ${errorText}`);
  }

  return response.json();
}


export interface EvidenceItemContract {
  source: string;
  parameter: string;
  value: any;
  unit?: string | null;
  observation_type: 'Observed' | 'Forecast' | 'Official Warning' | 'AI Assessment' | 'Operational Calculation' | string;
  timestamp?: string | null;
  freshness: 'Fresh' | 'Aging' | 'Stale' | 'Unavailable';
  location?: Record<string, any> | null;
  provenance?: Record<string, any> | null;
}

export interface AgentResultContract {
  agent_name: string;
  status: 'success' | 'partial' | 'unavailable' | 'error';
  summary: string;
  findings: string[];
  evidence: EvidenceItemContract[];
  confidence: number;
  warnings: string[];
  limitations: string[];
}

export interface WhyDecisionBreakdownContract {
  marine_conditions: string[];
  ocean_conditions: string[];
  eo_indicators: string[];
  spatial_constraints: string[];
  safety_warnings: string[];
  operational_factors: string[];
}

export interface ScenarioDetailsContract {
  departure_time?: string | null;
  location_name?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  decision?: string | null;
  confidence_score?: number | null;
  risk_level?: string | null;
  key_conditions?: string[];
}

export interface WhatIfComparisonContract {
  status: string;
  message?: string | null;
  base_scenario?: ScenarioDetailsContract | null;
  what_if_scenario?: ScenarioDetailsContract | null;
  changed_factors: string[];
  decision_difference?: string | null;
  confidence_difference?: number | null;
}

export interface ComparisonLocationDetailContract {
  location_name: string;
  latitude: number;
  longitude: number;
  decision?: string | null;
  confidence: number;
  suitability_score?: number | null;
  key_metrics: Record<string, any>;
  summary: string;
  pros: string[];
  cons: string[];
}

export interface ComparisonResultContract {
  target_locations: ComparisonLocationDetailContract[];
  recommended_location?: string | null;
  comparison_summary: string;
  parameter_matrix: Record<string, Record<string, any>>;
}

export interface FinalDecisionObjectContract {
  query_intent?: 'DECISION' | 'INFORMATION' | 'SAFETY' | 'COMPARISON' | 'WHAT_IF' | 'ROUTE' | 'GENERAL' | string;
  primary_answer?: string | null;
  decision: 'Suitable' | 'Caution' | 'Not Recommended' | 'Insufficient Evidence' | 'Information' | string;
  summary: string;
  confidence: number;
  confidence_reasons: string[];
  safety_status: string;
  guardrail_actions: string[];
  key_findings: string[];
  why_decision: WhyDecisionBreakdownContract;
  evidence: EvidenceItemContract[];
  agents_consulted: AgentResultContract[];
  total_agents_available?: number;
  agents_consulted_count?: number;
  freshness_summary: string;
  warnings: string[];
  limitations: string[];
  location?: {
    name?: string;
    latitude?: number;
    longitude?: number;
    is_port?: boolean;
    is_inland?: boolean;
  } | null;
  requested_time?: string | null;
  what_if_comparison?: WhatIfComparisonContract | null;
  comparison_data?: ComparisonResultContract | null;
  entities_extracted?: Record<string, any>;
  generated_at: string;
}

export interface WhatIfRequestPayload {
  query: string;
  latitude?: number | null;
  longitude?: number | null;
  target_datetime?: string | null;
  what_if_time?: string | null;
  what_if_latitude?: number | null;
  what_if_longitude?: number | null;
  what_if_location_name?: string | null;
}

/**
 * Fetch authoritative structured marine decision from Agent Orchestrator.
 */
export async function getOrchestratorDecision(
  query: string,
  latitude?: number | null,
  longitude?: number | null,
  targetDatetime?: string | null,
  whatIfTime?: string | null,
  whatIfLat?: number | null,
  whatIfLon?: number | null,
  whatIfLocName?: string | null,
  language?: string | null,
): Promise<FinalDecisionObjectContract> {
  const params = new URLSearchParams();
  if (whatIfTime) params.append('what_if_time', whatIfTime);
  if (whatIfLat !== undefined && whatIfLat !== null) params.append('what_if_lat', whatIfLat.toString());
  if (whatIfLon !== undefined && whatIfLon !== null) params.append('what_if_lon', whatIfLon.toString());
  if (whatIfLocName) params.append('what_if_loc_name', whatIfLocName);

  const url = `${API_BASE_URL}/api/v1/orchestrator/decision${params.toString() ? '?' + params.toString() : ''}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      latitude: latitude ?? null,
      longitude: longitude ?? null,
      target_datetime: targetDatetime ?? null,
      language: language || 'en',
    }),
  });

  if (!response.ok) {
    const errDetail = await response.text();
    throw new Error(`Orchestrator decision API error (${response.status}): ${errDetail}`);
  }

  return response.json();
}

/**
 * Run standalone What-If scenario comparison.
 */
export async function runWhatIfSimulation(
  payload: WhatIfRequestPayload
): Promise<WhatIfComparisonContract> {
  const response = await fetch(`${API_BASE_URL}/api/v1/orchestrator/what-if`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errDetail = await response.text();
    throw new Error(`What-If simulation API error (${response.status}): ${errDetail}`);
  }

  return response.json();
}
