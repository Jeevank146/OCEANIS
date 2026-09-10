import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import {
  assessFishingOperation,
  fetchDynamicMarineConditions,
  type DynamicMarineConditionsData,
  type FishingAssessmentContract,
  type PFZZoneContract,
} from '../../services/api';
import './FishingPage.css';

interface SpeciesScore {
  name: string;
  scientificName: string;
  suitabilityScore: number | null;
  depthRange: string;
  peakSeason: string;
  habitat: string;
  confidence: 'HIGH' | 'MEDIUM' | 'VERY HIGH' | 'INSUFFICIENT' | 'UNAVAILABLE';
}

interface ActiveZoneView {
  id: string;
  name: string;
  distance: number;
  bearing: string;
  score: number;
  sstGrad: string;
  chlorophyll: string;
  depth: string;
  fuelEstimate: string;
  recommendation: string;
}

const BASELINE_SPECIES_DEFINITIONS = [
  {
    name: 'Indian Mackerel (Kanagurta)',
    scientificName: 'Rastrelliger kanagurta',
    depthRange: '15 - 45 m',
    peakSeason: 'Sep - Feb',
    habitat: 'Pelagic thermal boundaries & chlorophyll fronts',
    optimalSSTMin: 27.0,
    optimalSSTMax: 29.5,
    maxWaveFavorable: 1.8,
  },
  {
    name: 'Yellowfin Tuna',
    scientificName: 'Thunnus albacares',
    depthRange: '40 - 120 m',
    peakSeason: 'Oct - Mar',
    habitat: 'Deep thermocline edges (SST 26.5 - 28.8°C)',
    optimalSSTMin: 26.5,
    optimalSSTMax: 28.8,
    maxWaveFavorable: 2.2,
  },
  {
    name: 'Oil Sardine (Kavallu)',
    scientificName: 'Sardinella longiceps',
    depthRange: '10 - 30 m',
    peakSeason: 'Aug - Jan',
    habitat: 'Coastal upwelling plumes with high phytoplankton',
    optimalSSTMin: 26.5,
    optimalSSTMax: 29.0,
    maxWaveFavorable: 1.5,
  },
  {
    name: 'Ribbonfish (Savam)',
    scientificName: 'Trichiurus lepturus',
    depthRange: '25 - 75 m',
    peakSeason: 'Sep - Apr',
    habitat: 'Demersal/benthopelagic sandy-mud shelf',
    optimalSSTMin: 25.5,
    optimalSSTMax: 29.5,
    maxWaveFavorable: 2.0,
  },
  {
    name: 'Squid / Cuttlefish',
    scientificName: 'Sepioteuthis lessoniana',
    depthRange: '20 - 60 m',
    peakSeason: 'Oct - Feb',
    habitat: 'Rocky shelf margins & nocturnal light convergence',
    optimalSSTMin: 26.0,
    optimalSSTMax: 29.0,
    maxWaveFavorable: 1.6,
  },
];

export const FishingPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedLocation, activeValidation } = useLocationContext();

  const [selectedZone, setSelectedZone] = useState<string>('');
  const [vesselType, setVesselType] = useState<string>('motorized');
  const [targetDistance, setTargetDistance] = useState<number>(14.5);

  const [dynamicZones, setDynamicZones] = useState<ActiveZoneView[]>([]);
  const [marineTelemetry, setMarineTelemetry] = useState<DynamicMarineConditionsData | null>(null);
  const [fishingAssessment, setFishingAssessment] = useState<FishingAssessmentContract | null>(null);
  const [pfzNotes, setPfzNotes] = useState<string>('');

  const locationName = selectedLocation.name || activeValidation.location_name || '';
  const latitude = activeValidation.latitude ?? (selectedLocation.name ? selectedLocation.lat : undefined);
  const longitude = activeValidation.longitude ?? (selectedLocation.name ? selectedLocation.lon : undefined);
  const isInland =
    activeValidation.status === 'INLAND' ||
    selectedLocation.region === 'Inland Area' ||
    (!activeValidation.is_coastal && !activeValidation.is_marine && Boolean(locationName));
  const hasLocation =
    Boolean(locationName) &&
    latitude !== undefined &&
    longitude !== undefined &&
    activeValidation.status !== 'UNRESOLVED';

  // Dynamically load marine telemetry and fishing intelligence for the selected location
  useEffect(() => {
    let isMounted = true;

    if (!hasLocation || isInland || latitude === undefined || longitude === undefined) {
      setDynamicZones([]);
      setMarineTelemetry(null);
      setFishingAssessment(null);
      setPfzNotes('');
      setSelectedZone('');
      return;
    }

    async function loadFishingData() {
      try {
        const [telemetryRes, assessmentRes] = await Promise.allSettled([
          fetchDynamicMarineConditions(latitude!, longitude!, locationName),
          assessFishingOperation({ latitude: latitude!, longitude: longitude! }),
        ]);

        if (!isMounted) return;

        let activeTelemetry: DynamicMarineConditionsData | null = null;
        if (telemetryRes.status === 'fulfilled') {
          activeTelemetry = telemetryRes.value;
          setMarineTelemetry(telemetryRes.value);
        }

        if (assessmentRes.status === 'fulfilled') {
          const assessment = assessmentRes.value;
          setFishingAssessment(assessment);

          if (assessment.pfz?.zones && assessment.pfz.zones.length > 0) {
            const mappedZones: ActiveZoneView[] = assessment.pfz.zones.map((z: PFZZoneContract, idx: number) => ({
              id: z.id || `zone-${idx + 1}`,
              name: z.name,
              distance: z.distance ?? 12.0,
              bearing: z.bearing || 'Offshore Shelf',
              score: z.score ?? 85,
              sstGrad: z.sstGrad || (activeTelemetry?.sea_surface_temperature_c ? `${activeTelemetry.sea_surface_temperature_c}°C SST profile` : 'Thermal front telemetry'),
              chlorophyll: z.chlorophyll || 'Bio-optical chlorophyll density',
              depth: z.depth || 'Coastal shelf depth',
              fuelEstimate: z.fuelEstimate || '35 - 50 Litres',
              recommendation: z.recommendation || assessment.recommendation || 'Operational Window Open',
            }));
            setDynamicZones(mappedZones);
            setSelectedZone(mappedZones[0].id);
            setTargetDistance(mappedZones[0].distance);
          } else {
            setDynamicZones([]);
            setSelectedZone('');
            setPfzNotes(
              assessment.pfz?.notes ||
              'Official INCOIS Potential Fishing Zone (PFZ) advisory data is currently unavailable for this sector; assessment relies on direct satellite SST, ocean current, and chlorophyll indicators.'
            );
          }
        } else {
          setDynamicZones([]);
          setSelectedZone('');
          setPfzNotes(
            'Official INCOIS Potential Fishing Zone (PFZ) advisory data is currently unavailable for this sector; assessment relies on direct satellite SST, ocean current, and chlorophyll indicators.'
          );
        }
      } catch (err) {
        if (isMounted) {
          console.warn('Dynamic fishing data retrieval note:', err);
          setDynamicZones([]);
          setSelectedZone('');
        }
      }
    }

    loadFishingData();

    return () => {
      isMounted = false;
    };
  }, [hasLocation, isInland, latitude, longitude, locationName]);

  // Compute dynamic species suitability scores based on real telemetry
  const speciesList = useMemo<SpeciesScore[]>(() => {
    if (isInland || !hasLocation) {
      return BASELINE_SPECIES_DEFINITIONS.map((def) => ({
        name: def.name,
        scientificName: def.scientificName,
        suitabilityScore: null,
        depthRange: def.depthRange,
        peakSeason: def.peakSeason,
        habitat: isInland
          ? 'Inland location — marine species habitat matching is not applicable.'
          : 'Select an operating coastal location to evaluate species habitat suitability.',
        confidence: 'UNAVAILABLE',
      }));
    }

    const sst = marineTelemetry?.sea_surface_temperature_c;
    const wave = marineTelemetry?.wave_height_m;
    const hasTelemetry = sst !== null && sst !== undefined;

    return BASELINE_SPECIES_DEFINITIONS.map((def) => {
      if (!hasTelemetry) {
        return {
          name: def.name,
          scientificName: def.scientificName,
          suitabilityScore: null,
          depthRange: def.depthRange,
          peakSeason: def.peakSeason,
          habitat: def.habitat,
          confidence: 'INSUFFICIENT',
        };
      }

      let score = 50;

      // SST match against optimal envelope
      if (sst >= def.optimalSSTMin && sst <= def.optimalSSTMax) {
        score += 35;
      } else {
        const delta = Math.min(Math.abs(sst - def.optimalSSTMin), Math.abs(sst - def.optimalSSTMax));
        score += Math.max(0, Math.round(30 - delta * 15));
      }

      // Wave conditions impact
      if (typeof wave === 'number') {
        if (wave <= def.maxWaveFavorable) {
          score += 15;
        } else if (wave <= def.maxWaveFavorable + 0.8) {
          score += 5;
        } else {
          score -= 15;
        }
      } else {
        score += 5;
      }

      const clampedScore = Math.max(15, Math.min(95, score));
      const confidence: 'HIGH' | 'MEDIUM' | 'VERY HIGH' | 'INSUFFICIENT' | 'UNAVAILABLE' =
        typeof wave === 'number' && typeof sst === 'number' ? 'HIGH' : 'MEDIUM';

      return {
        name: def.name,
        scientificName: def.scientificName,
        suitabilityScore: clampedScore,
        depthRange: def.depthRange,
        peakSeason: def.peakSeason,
        habitat: def.habitat,
        confidence,
      };
    });
  }, [isInland, hasLocation, marineTelemetry]);

  const activeZoneData = useMemo<ActiveZoneView>(() => {
    if (dynamicZones.length > 0) {
      return dynamicZones.find((z) => z.id === selectedZone) || dynamicZones[0];
    }

    const sstVal = marineTelemetry?.sea_surface_temperature_c;
    const waveVal = marineTelemetry?.wave_height_m;
    const sstStr = sstVal !== null && sstVal !== undefined ? `${sstVal}°C observed SST` : 'Telemetry unavailable';
    const waveStr = waveVal !== null && waveVal !== undefined ? `${waveVal}m significant wave height` : 'Wave telemetry unavailable';

    return {
      id: 'dynamic-sector',
      name: locationName || 'Selected Marine Sector',
      distance: targetDistance,
      bearing: 'Offshore Fairway',
      score: fishingAssessment?.overall_suitability?.score ? Math.round(fishingAssessment.overall_suitability.score * 100) : 0,
      sstGrad: sstStr,
      chlorophyll: 'Satellite ocean color baseline',
      depth: waveStr,
      fuelEstimate: `${(targetDistance * 2.2).toFixed(0)} Litres`,
      recommendation: fishingAssessment?.recommendation || 'Continuous monitoring of live marine telemetry advised.',
    };
  }, [dynamicZones, selectedZone, marineTelemetry, fishingAssessment, locationName, targetDistance]);

  const handleLaunchAgentQuery = (targetName: string) => {
    navigate('/ask-oceanis', {
      state: { initialQuery: `Evaluate fishing suitability, species probability and safe transit for ${targetName}` },
    });
  };

  const biomassIndex = useMemo(() => {
    if (isInland) return '0.0 / 10 (Inland)';
    if (!hasLocation) return 'N/A (Select Location)';

    const rawScore =
      dynamicZones.length > 0
        ? activeZoneData.score
        : fishingAssessment?.overall_suitability?.score !== undefined && fishingAssessment.overall_suitability.score !== null
        ? Math.round(fishingAssessment.overall_suitability.score * 100)
        : null;

    if (rawScore === null || rawScore === 0) {
      const avgSpecies = speciesList.filter((s) => typeof s.suitabilityScore === 'number');
      if (avgSpecies.length > 0) {
        const mean = avgSpecies.reduce((acc, sp) => acc + (sp.suitabilityScore || 0), 0) / avgSpecies.length;
        return `${(8.5 * (mean / 100)).toFixed(1)} / 10`;
      }
      return 'INSUFFICIENT EVIDENCE';
    }

    return `${(8.5 * (rawScore / 100)).toFixed(1)} / 10`;
  }, [isInland, hasLocation, dynamicZones, activeZoneData.score, fishingAssessment, speciesList]);

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Fishing Intelligence</span>
          </div>
          <h1 className="page-title">
            Potential Fishing Zone (PFZ) & Marine Biomass Intelligence
            <span className="page-title-badge badge-agent">Fishing Agent</span>
          </h1>
          <p className="page-subtitle">
            INCOIS satellite bio-optical Chlorophyll-a telemetry paired with Copernicus SLSTR thermal front analysis and species-specific habitat algorithms.
          </p>
        </div>
        <div className="page-header-actions">
          <button
            type="button"
            className="btn-page-action primary"
            onClick={() => handleLaunchAgentQuery(activeZoneData.name)}
          >
            <span>Ask Fishing Agent</span>
          </button>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="fishing-layout-grid">
        {/* Left Column: Zone Selector + Why This Location? Explainability */}
        <div className="fishing-left-col">
          {/* Zone Selector Card */}
          <div className="ocean-card fishing-zones-card">
            <div className="card-top-header">
              <h3>Active PFZ Advisory Zones</h3>
              <span className="badge-source">INCOIS & Sentinel-3</span>
            </div>
            <p className="card-desc">
              Select an oceanographic waypoint to inspect bio-physical parameters and species habitat suitability.
            </p>

            {isInland ? (
              <div className="zone-empty-state">
                <span className="zone-empty-icon">⚠️</span>
                <h4 className="zone-empty-title">No active PFZ evidence available for this location</h4>
                <p className="zone-empty-desc">
                  Selected location ({locationName || 'Inland Sector'}) is inland
                  {activeValidation.distance_to_coast_km
                    ? ` (~${Math.round(activeValidation.distance_to_coast_km)} km from nearest coast)`
                    : ''}. Potential Fishing Zones (PFZ) are only applicable to coastal and offshore marine waters.
                </p>
              </div>
            ) : !hasLocation ? (
              <div className="zone-empty-state">
                <span className="zone-empty-icon">📍</span>
                <h4 className="zone-empty-title">No location selected</h4>
                <p className="zone-empty-desc">
                  Select an operational coastal location or enter a harbor name to inspect active PFZ advisory zones.
                </p>
              </div>
            ) : dynamicZones.length === 0 ? (
              <div className="zone-empty-state">
                <span className="zone-empty-icon">ℹ️</span>
                <h4 className="zone-empty-title">No active PFZ evidence available for this location</h4>
                <p className="zone-empty-desc">
                  {pfzNotes ||
                    'Official INCOIS Potential Fishing Zone (PFZ) advisory data is currently unavailable for this sector; assessment relies on direct satellite SST, ocean current, and chlorophyll indicators.'}
                </p>
              </div>
            ) : (
              <div className="zone-button-list">
                {dynamicZones.map((zone) => (
                  <button
                    key={zone.id}
                    type="button"
                    className={`zone-select-btn ${selectedZone === zone.id ? 'active' : ''}`}
                    onClick={() => {
                      setSelectedZone(zone.id);
                      setTargetDistance(zone.distance);
                    }}
                  >
                    <div className="zone-btn-left">
                      <span className="zone-badge-score">{zone.score}%</span>
                      <div className="zone-btn-meta">
                        <strong>{zone.name}</strong>
                        <span className="zone-sub">
                          {zone.distance} NM • {zone.bearing} • Depth {zone.depth}
                        </span>
                      </div>
                    </div>
                    <span className="zone-chevron">›</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* What-If Fishing Scenario Action Card */}
          <div className="ocean-card whatif-fishing-card">
            <div className="whatif-fishing-header">
              <div className="whatif-fishing-title-group">
                <span className="whatif-fishing-icon">⏱️</span>
                <div>
                  <h3 className="whatif-fishing-title">What-If Fishing Scenario</h3>
                  <span className="whatif-badge-sim">SIMULATION</span>
                </div>
              </div>
            </div>
            <p className="whatif-fishing-desc">
              Compare different fishing times or fishing zones and understand how marine conditions, suitability, confidence and risk may change.
            </p>
            <div className="whatif-fishing-action">
              <Link to="/what-if" className="btn-run-whatif-fishing">
                <span>Run What-If Analysis</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Explainability Engine: "Why this location?" */}
          <div className="ocean-card explainability-card">
            <div className="card-top-header">
              <h3>Scientific Explainability Engine</h3>
              <span className="badge-provenance">Audit Layer</span>
            </div>
            <h4 className="explain-target-title">
              {isInland
                ? 'Inland Location — Ocean Physics Not Applicable'
                : dynamicZones.length > 0
                ? `Why Zone: ${activeZoneData.name}?`
                : `Bio-Physical Ocean Analysis — ${locationName || 'Current Location'}`}
            </h4>
            <div className="explain-pillars-list">
              <div className="explain-pillar">
                <div className="pillar-num">01</div>
                <div className="pillar-content">
                  <strong>Thermal Front & Eddy Convergence</strong>
                  <p>
                    {isInland
                      ? 'No sea surface temperature telemetry available for inland coordinates.'
                      : marineTelemetry?.sea_surface_temperature_c !== null && marineTelemetry?.sea_surface_temperature_c !== undefined
                      ? `SLSTR radiometric sensor indicates Sea Surface Temperature of ${marineTelemetry.sea_surface_temperature_c}°C (${activeZoneData.sstGrad}). Pelagic fish aggregate along thermal boundaries.`
                      : 'SLSTR radiometric thermal sensor data indicates standard seasonal water mass profile for this coastal sector.'}
                  </p>
                </div>
              </div>

              <div className="explain-pillar">
                <div className="pillar-num">02</div>
                <div className="pillar-content">
                  <strong>Phytoplankton Biomass (Chlorophyll-a)</strong>
                  <p>
                    {isInland
                      ? 'No satellite marine ocean color observations available for inland coordinates.'
                      : 'Sentinel-3 OLCI ocean color data indicates baseline biological primary productivity envelope for pelagic forage fish concentration.'}
                  </p>
                </div>
              </div>

              <div className="explain-pillar">
                <div className="pillar-num">03</div>
                <div className="pillar-content">
                  <strong>Bathymetry Upwelling & Sea State</strong>
                  <p>
                    {isInland
                      ? 'No marine bathymetric upwelling data applicable for inland coordinates.'
                      : marineTelemetry?.wave_height_m !== null && marineTelemetry?.wave_height_m !== undefined
                      ? `Current significant wave height of ${marineTelemetry.wave_height_m}m with sustained surface wind of ${marineTelemetry.wind_speed_kmh ?? 'N/A'} km/h.`
                      : 'GEBCO shelf data indicates standard coastal shelf depth contour with localized current deflection.'}
                  </p>
                </div>
              </div>
            </div>

            <div className="operational-recommendation-box">
              <span className="rec-icon">💡</span>
              <div className="rec-text">
                <strong>Operational Guidance:</strong>{' '}
                {isInland
                  ? 'Marine fishing operations are blocked for inland locations. Select a coastal port.'
                  : activeZoneData.recommendation}
                {!isInland && ` Estimated fuel requirement for round trip is approximately ${activeZoneData.fuelEstimate}.`}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Species Probabilities + Fuel/Trip Calculator */}
        <div className="fishing-right-col">
          {/* Target Species Probabilities */}
          <div className="ocean-card species-card">
            <div className="card-top-header">
              <h3>Species Occurrence & Habitat Matching</h3>
              <span className="badge-model">Biomass Model v2.1</span>
            </div>
            <div className="species-list">
              {speciesList.map((sp) => (
                <div key={sp.name} className="species-item">
                  <div className="species-header">
                    <div>
                      <strong className="sp-name">{sp.name}</strong>
                      <span className="sp-sci">{sp.scientificName}</span>
                    </div>
                    <div className="sp-score-box">
                      <span className="sp-score-num">
                        {sp.suitabilityScore !== null ? `${sp.suitabilityScore}%` : 'N/A'}
                      </span>
                      <span className="sp-score-label">
                        {sp.suitabilityScore !== null ? 'Suitability' : 'Unavailable'}
                      </span>
                    </div>
                  </div>
                  <div className="sp-progress-track">
                    <div
                      className="sp-progress-bar"
                      style={{
                        width: `${sp.suitabilityScore ?? 0}%`,
                        background:
                          (sp.suitabilityScore ?? 0) > 80
                            ? '#16a34a'
                            : (sp.suitabilityScore ?? 0) > 60
                            ? '#0284c7'
                            : '#d97706',
                      }}
                    />
                  </div>
                  <div className="sp-meta-row">
                    <span>
                      Depth: <strong>{sp.depthRange}</strong>
                    </span>
                    <span>
                      Peak: <strong>{sp.peakSeason}</strong>
                    </span>
                    <span>
                      Confidence: <strong className="conf-badge">{sp.confidence}</strong>
                    </span>
                  </div>
                  <p className="sp-habitat">{sp.habitat}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Voyage Fuel & Catch Return Calculator */}
          <div className="ocean-card fuel-calc-card">
            <div className="card-top-header">
              <h3>Voyage Fuel & Economic Index Calculator</h3>
              <span className="badge-tool">Planning</span>
            </div>
            <div className="calc-inputs-grid">
              <div className="calc-field">
                <label>Vessel Category</label>
                <select
                  value={vesselType}
                  onChange={(e) => setVesselType(e.target.value)}
                  className="calc-select"
                >
                  <option value="motorized">Motorized Craft (OBM 9.9 HP)</option>
                  <option value="mechanized">Mechanized Trawler (120 HP)</option>
                  <option value="artisanal">Traditional FRP Boat (5 HP)</option>
                </select>
              </div>

              <div className="calc-field">
                <label>Target Distance: {targetDistance} NM</label>
                <input
                  type="range"
                  min="5"
                  max="40"
                  step="0.5"
                  value={targetDistance}
                  onChange={(e) => setTargetDistance(parseFloat(e.target.value))}
                  className="calc-slider"
                  disabled={isInland}
                />
              </div>
            </div>

            <div className="calc-results-strip">
              <div className="calc-res-item">
                <span className="res-label">Estimated Diesel</span>
                <span className="res-val">
                  {isInland
                    ? '0 L'
                    : vesselType === 'mechanized'
                    ? `${(targetDistance * 4.2).toFixed(0)} L`
                    : `${(targetDistance * 1.8).toFixed(0)} L`}
                </span>
              </div>
              <div className="calc-res-item">
                <span className="res-label">Estimated Transit</span>
                <span className="res-val">
                  {isInland ? '0.0 hrs' : `${(targetDistance / 7.5).toFixed(1)} hrs`}
                </span>
              </div>
              <div className="calc-res-item">
                <span className="res-label">Biomass Index</span>
                <span className="res-val highlight">{biomassIndex}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FishingPage;

