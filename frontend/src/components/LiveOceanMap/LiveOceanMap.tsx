import React, { useState, useEffect } from 'react';
import { useLocationContext } from '../../context/LocationContext';
import './LiveOceanMap.css';

type MapLayer = 
  | 'satellite'
  | 'sst'
  | 'chlorophyll'
  | 'waves'
  | 'wind'
  | 'currents'
  | 'fishing_zones'
  | 'hazard_zones'
  | 'protected_areas'
  | 'restricted_areas'
  | 'ports';

interface MapLayerConfig {
  id: MapLayer;
  label: string;
  category: 'Raster' | 'Dynamics' | 'Geofence' | 'Infrastructure';
  legendTitle: string;
  legendScale: string[];
  unit: string;
}

const mapLayers: MapLayerConfig[] = [
  { id: 'sst', label: 'SST Radiometry', category: 'Raster', legendTitle: 'Sea Surface Temp (°C)', legendScale: ['26.0°C', '27.5°C', '28.8°C', '30.0°C'], unit: '°C' },
  { id: 'chlorophyll', label: 'Chlorophyll-a', category: 'Raster', legendTitle: 'Chlorophyll-a Bio-Optics', legendScale: ['0.1 mg/m³', '0.5 mg/m³', '1.5 mg/m³', '3.0+ mg/m³'], unit: 'mg/m³' },
  { id: 'waves', label: 'Wave Fields', category: 'Dynamics', legendTitle: 'Significant Wave Height', legendScale: ['0.5 m', '1.2 m', '1.8 m', '2.5+ m'], unit: 'm' },
  { id: 'wind', label: 'Wind Vectors', category: 'Dynamics', legendTitle: 'Surface Wind Velocity', legendScale: ['5 kts', '15 kts', '25 kts', '35+ kts'], unit: 'kts' },
  { id: 'currents', label: 'Ocean Currents', category: 'Dynamics', legendTitle: 'Surface Current Drift', legendScale: ['0.2 kts', '0.6 kts', '1.2 kts', '2.0+ kts'], unit: 'kts' },
  { id: 'fishing_zones', label: 'Fishing Zones (PFZ)', category: 'Geofence', legendTitle: 'PFZ Thermal-Optic Score', legendScale: ['Low', 'Moderate', 'High', 'Prime Front'], unit: 'Score' },
  { id: 'hazard_zones', label: 'Hazard Zones', category: 'Geofence', legendTitle: 'Hazard Severity Polygons', legendScale: ['Normal', 'Advisory', 'Warning', 'Critical'], unit: 'Alert' },
  { id: 'ports', label: 'Ports & Refuges', category: 'Infrastructure', legendTitle: 'Maritime Facilities', legendScale: ['Major Port', 'Fishing Harbor', 'Designated Refuge'], unit: 'Port' },
];

export const LiveOceanMap: React.FC = () => {
  const { selectedLocation, validateAndSetCoordinates, isValidating } = useLocationContext();
  const [activeLayer, setActiveLayer] = useState<MapLayer>('sst');
  const [zoomLevel, setZoomLevel] = useState<number>(9.5);
  const [mouseCoords, setMouseCoords] = useState({
    lat: `${Math.abs(selectedLocation.lat).toFixed(4)}° ${selectedLocation.lat >= 0 ? 'N' : 'S'}`,
    lon: `${Math.abs(selectedLocation.lon).toFixed(4)}° ${selectedLocation.lon >= 0 ? 'E' : 'W'}`,
  });
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    setMouseCoords({
      lat: `${Math.abs(selectedLocation.lat).toFixed(4)}° ${selectedLocation.lat >= 0 ? 'N' : 'S'}`,
      lon: `${Math.abs(selectedLocation.lon).toFixed(4)}° ${selectedLocation.lon >= 0 ? 'E' : 'W'}`,
    });
  }, [selectedLocation.lat, selectedLocation.lon]);

  const activeConfig = mapLayers.find((l) => l.id === activeLayer) || mapLayers[0];

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.5, 14.0));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.5, 6.0));
  const handleReset = () => setZoomLevel(9.5);

  const getCoordinatesFromEvent = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const xRatio = (e.clientX - rect.left) / rect.width;
    const yRatio = (e.clientY - rect.top) / rect.height;
    const span = 3.2 / (zoomLevel / 9.5);
    const lat = Number((selectedLocation.lat + span / 2 - yRatio * span).toFixed(4));
    const lon = Number((selectedLocation.lon - span / 2 + xRatio * span).toFixed(4));
    return { lat, lon };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const { lat, lon } = getCoordinatesFromEvent(e);
    setMouseCoords({
      lat: `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? 'N' : 'S'}`,
      lon: `${Math.abs(lon).toFixed(4)}° ${lon >= 0 ? 'E' : 'W'}`,
    });
  };

  const handleMapClick = async (e: React.MouseEvent<HTMLDivElement>) => {
    const { lat, lon } = getCoordinatesFromEvent(e);
    await validateAndSetCoordinates(lat, lon, `Waypoint (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
  };

  // Clean location & coordinate values without duplication
  const cleanMapLocName = selectedLocation?.name
    ? (selectedLocation.name.replace(/\s*\([^)]*\)/g, '').trim() || selectedLocation.name)
    : 'Selected Operating Area';

  const centerCoordsFormatted = selectedLocation?.lat !== undefined && selectedLocation?.lon !== undefined
    ? `${Math.abs(selectedLocation.lat).toFixed(4)}° ${selectedLocation.lat >= 0 ? 'N' : 'S'}, ${Math.abs(selectedLocation.lon).toFixed(4)}° ${selectedLocation.lon >= 0 ? 'E' : 'W'}`
    : '17.6868° N, 83.2185° E';

  const isOffshoreDomain = Boolean(
    (!selectedLocation?.is_coastal && selectedLocation?.distance_to_coast_km && selectedLocation.distance_to_coast_km > 20.0) ||
    (selectedLocation?.status === 'VALID_MARINE' && !selectedLocation?.is_coastal) ||
    cleanMapLocName.toLowerCase().includes('offshore') ||
    cleanMapLocName.toLowerCase().includes('waypoint')
  );

  const domainClassificationTag = selectedLocation?.is_coastal
    ? 'COASTAL'
    : isOffshoreDomain
    ? 'OFFSHORE'
    : 'INLAND';

  return (
    <div id="live-map" className={`live-ocean-map-card ocean-card ${isFullscreen ? 'fullscreen-map' : ''}`}>
      {/* Map Header */}
      <div className="map-card-header">
        <div className="map-header-left">
          <h2 className="map-title-text">LIVE OCEAN INTELLIGENCE MAP</h2>
          <div className="map-meta-info-row">
            <span className="map-meta-item"><strong className="meta-lbl">LOCATION:</strong> {cleanMapLocName}</span>
            <span className="map-meta-sep">•</span>
            <span className="map-meta-item"><strong className="meta-lbl">CENTER:</strong> {centerCoordsFormatted}</span>
            <span className="map-meta-sep">•</span>
            <span className="map-meta-item"><strong className="meta-lbl">DOMAIN:</strong> <span className="domain-badge">{domainClassificationTag}</span></span>
            <span className="map-meta-sep">•</span>
            <span className="map-analytical-note">Marine analytical layer</span>
          </div>
        </div>

        <div className="map-header-actions">
          <button
            type="button"
            className="btn-map-fullscreen"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit Full Screen' : 'Open in Full Screen'}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {isFullscreen ? (
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
              ) : (
                <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
              )}
            </svg>
            <span>{isFullscreen ? 'Exit' : 'Full Screen'}</span>
          </button>
        </div>
      </div>

      {/* Layer Pills Bar */}
      <div className="map-layer-pills-bar">
        <span className="layer-pills-label">LAYERS:</span>
        <div className="layer-pills-scroll">
          {mapLayers.map((layer) => (
            <button
              key={layer.id}
              type="button"
              className={`layer-pill ${activeLayer === layer.id ? 'active' : ''}`}
              onClick={() => setActiveLayer(layer.id)}
            >
              <span className="layer-dot" />
              <span>{layer.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* GIS Viewport Canvas */}
      <div 
        className="map-viewport-container"
        onMouseMove={handleMouseMove}
        onClick={handleMapClick}
        style={{ cursor: 'crosshair' }}
        title="Click anywhere on the map to set waypoint coordinates"
      >
        {isValidating && (
          <div className="map-loading-overlay">
            <span className="map-loading-spinner" />
            <span>Resolving spatial coordinates...</span>
          </div>
        )}

        <div className={`map-gis-canvas layer-mode-${activeLayer}`}>
          {/* Cartographic Vector Lines & Contours */}
          <svg className="map-gis-svg" viewBox="0 0 1000 560" preserveAspectRatio="none">
            {/* Bathymetric Depth Contours */}
            <path d="M 0 40 Q 220 110 420 190 T 820 420 L 1000 560 L 0 560 Z" className="bathymetry-line shallow" />
            <path d="M 160 0 Q 360 90 560 210 T 960 480 L 1000 560 L 160 560 Z" className="bathymetry-line mid" />
            <path d="M 320 0 Q 520 110 720 250 T 1000 530 L 1000 560 L 320 560 Z" className="bathymetry-line deep" />

            {/* Indian Coastline Outline */}
            <path d="M 200 0 Q 250 170 280 310 T 230 560" className="coastline-vector" />
            <path d="M 0 0 L 200 0 Q 250 170 280 310 T 230 560 L 0 560 Z" className="landmass-polygon" />

            {/* 12 NM Territorial Water Boundary */}
            <path d="M 300 0 Q 350 170 380 310 T 330 560" className="boundary-12nm" />

            {/* 200 NM EEZ Outer Boundary */}
            <path d="M 700 0 Q 750 170 780 310 T 730 560" className="boundary-eez" />

            {/* PFZ Potential Fishing Zone (if active) */}
            {(activeLayer === 'fishing_zones' || activeLayer === 'sst' || activeLayer === 'chlorophyll') && (
              <>
                <ellipse cx="460" cy="220" rx="80" ry="40" className="pfz-ellipse prime" transform="rotate(-15 460 220)" />
                <ellipse cx="640" cy="360" rx="100" ry="50" className="pfz-ellipse favorable" transform="rotate(20 640 360)" />
              </>
            )}

            {/* Hazard / Restriction Polygons */}
            {(activeLayer === 'hazard_zones' || activeLayer === 'restricted_areas') && (
              <polygon points="530,110 670,140 630,260 490,220" className="hazard-zone-polygon" />
            )}

            {/* Wave / Wind / Current Flow Vectors */}
            {(activeLayer === 'waves' || activeLayer === 'wind' || activeLayer === 'currents') && (
              <g className="flow-vectors">
                <line x1="380" y1="120" x2="430" y2="150" className="vector-arrow" />
                <line x1="520" y1="180" x2="570" y2="210" className="vector-arrow" />
                <line x1="680" y1="280" x2="730" y2="310" className="vector-arrow" />
                <line x1="440" y1="320" x2="490" y2="350" className="vector-arrow" />
                <line x1="600" y1="400" x2="650" y2="430" className="vector-arrow" />
              </g>
            )}

            {/* Dynamic Active Position Beacon centered on active location */}
            <g className="user-position-beacon" transform="translate(500, 260)">
              <circle r="18" className="beacon-pulse-ring" />
              <circle r="6" className="beacon-core-dot" />
              <text x="14" y="4" className="beacon-label">{selectedLocation.name}</text>
            </g>
          </svg>
        </div>

        {/* Map Legend Overlay */}
        <div className="map-legend-overlay">
          <div className="legend-header">
            <span className="legend-title">{activeConfig.legendTitle}</span>
            <span className="legend-unit">[{activeConfig.unit}]</span>
          </div>
          <div className="legend-gradient-bar">
            <div className={`gradient-fill gradient-${activeLayer}`} />
          </div>
          <div className="legend-scale-labels">
            {activeConfig.legendScale.map((label, idx) => (
              <span key={idx}>{label}</span>
            ))}
          </div>
        </div>

        {/* Map Controls */}
        <div className="map-gis-controls">
          <button type="button" className="gis-ctrl-btn" onClick={handleZoomIn} title="Zoom In">+</button>
          <button type="button" className="gis-ctrl-btn" onClick={handleZoomOut} title="Zoom Out">−</button>
          <button type="button" className="gis-ctrl-btn" onClick={handleReset} title="Reset View">⊙</button>
        </div>

        {/* Coordinates Status Bar */}
        <div className="map-coords-statusbar">
          <div className="coords-readout">
            <span className="coord-tag">CURSOR:</span>
            <span className="coord-value">{mouseCoords.lat}, {mouseCoords.lon}</span>
          </div>
          <div className="coords-readout">
            <span className="coord-tag">LOCATION:</span>
            <span className="coord-value">{selectedLocation.name}</span>
          </div>
          <div className="coords-readout">
            <span className="coord-tag">STATUS:</span>
            <span className={`coord-badge ${selectedLocation.is_coastal ? 'badge-marine' : 'badge-inland'}`}>
              {selectedLocation.is_coastal ? 'MARINE ACTIVE' : 'INLAND'}
            </span>
          </div>
          <div className="coords-readout">
            <span className="coord-tag">ZOOM:</span>
            <span className="coord-value">{zoomLevel.toFixed(1)}x</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveOceanMap;
