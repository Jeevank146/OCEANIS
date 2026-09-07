import React, { useState } from 'react';
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

interface PortMarker {
  name: string;
  lat: string;
  lon: string;
  status: 'OPEN' | 'ADVISORY' | 'REFUGE';
  depth: string;
}

const coastalPorts: PortMarker[] = [
  { name: 'Visakhapatnam Major Port', lat: '17.6868° N', lon: '83.2185° E', status: 'OPEN', depth: '18.0 m' },
  { name: 'Kakinada Deep Water Port', lat: '16.9890° N', lon: '82.2474° E', status: 'REFUGE', depth: '14.5 m' },
  { name: 'Machilipatnam Port', lat: '16.1875° N', lon: '81.1389° E', status: 'OPEN', depth: '8.5 m' },
  { name: 'Chennai Harbor Facility', lat: '13.0827° N', lon: '80.2707° E', status: 'OPEN', depth: '16.5 m' },
];

export const LiveOceanMap: React.FC = () => {
  const [activeLayer, setActiveLayer] = useState<MapLayer>('sst');
  const [zoomLevel, setZoomLevel] = useState<number>(9.5);
  const [activePort, setActivePort] = useState<PortMarker | null>(coastalPorts[0]);
  const [mouseCoords, setMouseCoords] = useState({ lat: '17.6868° N', lon: '83.2185° E' });
  const [isFullscreen, setIsFullscreen] = useState(false);

  const activeConfig = mapLayers.find((l) => l.id === activeLayer) || mapLayers[0];

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.5, 14.0));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.5, 6.0));
  const handleReset = () => {
    setZoomLevel(9.5);
    setActivePort(coastalPorts[0]);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const xRatio = (e.clientX - rect.left) / rect.width;
    const yRatio = (e.clientY - rect.top) / rect.height;
    const lat = (18.8 - yRatio * 3.2).toFixed(4);
    const lon = (81.2 + xRatio * 3.2).toFixed(4);
    setMouseCoords({ lat: `${lat}° N`, lon: `${lon}° E` });
  };

  return (
    <div id="live-map" className={`live-ocean-map-card ocean-card ${isFullscreen ? 'fullscreen-map' : ''}`}>
      {/* Map Header */}
      <div className="map-card-header">
        <div className="map-header-left">
          <h2 className="map-title-text">Live Ocean Intelligence Map</h2>
          <span className="map-crs-tag">EPSG:3857 • MERCATOR PROJECTION</span>
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
      >
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
              <g className="flow-vector-arrows">
                <line x1="390" y1="150" x2="450" y2="120" stroke="#0284c7" strokeWidth="2" strokeDasharray="5 3" />
                <line x1="490" y1="250" x2="550" y2="220" stroke="#0284c7" strokeWidth="2" strokeDasharray="5 3" />
                <line x1="590" y1="350" x2="650" y2="320" stroke="#0284c7" strokeWidth="2" strokeDasharray="5 3" />
                <line x1="690" y1="450" x2="750" y2="420" stroke="#0284c7" strokeWidth="2" strokeDasharray="5 3" />
              </g>
            )}
          </svg>

          {/* Port Beacons Overlay */}
          <div className="ports-overlay">
            {coastalPorts.map((port, idx) => (
              <button
                key={idx}
                type="button"
                className={`map-port-marker ${activePort?.name === port.name ? 'active' : ''}`}
                style={{
                  left: idx === 0 ? '36%' : idx === 1 ? '29%' : idx === 2 ? '24%' : '19%',
                  top: idx === 0 ? '25%' : idx === 1 ? '46%' : idx === 2 ? '66%' : '86%',
                }}
                onClick={() => setActivePort(port)}
                title={`${port.name} (${port.lat}, ${port.lon})`}
              >
                <span className="port-dot" />
                <span className="port-name-label">{port.name.split(' ')[0]}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Top-Left: Coordinate HUD */}
        <div className="map-hud-coords">
          <span className="hud-coord-item">
            <strong>LAT/LON:</strong> {mouseCoords.lat}, {mouseCoords.lon}
          </span>
          <span className="hud-coord-item">
            <strong>ZOOM:</strong> {zoomLevel.toFixed(1)}x
          </span>
        </div>

        {/* Top-Right: Zoom Controls */}
        <div className="map-hud-zoom-controls">
          <button type="button" className="btn-zoom" onClick={handleZoomIn} title="Zoom in">+</button>
          <button type="button" className="btn-zoom" onClick={handleZoomOut} title="Zoom out">−</button>
          <button type="button" className="btn-zoom btn-reset" onClick={handleReset} title="Reset view">⟲</button>
        </div>

        {/* Bottom-Right: Dynamic Legend */}
        <div className="map-hud-legend-card">
          <div className="legend-title-row">
            <span className="legend-label">{activeConfig.legendTitle}</span>
            <span className="legend-unit">[{activeConfig.unit}]</span>
          </div>
          <div className="legend-color-bar" />
          <div className="legend-scale-steps">
            {activeConfig.legendScale.map((lbl, i) => (
              <span key={i} className="scale-lbl">{lbl}</span>
            ))}
          </div>
        </div>

        {/* Bottom-Left: Selected Port Refuge Card */}
        {activePort && (
          <div className="map-hud-port-refuge-card">
            <div className="port-refuge-lead">
              <span className="port-refuge-icon">⚓</span>
              <div>
                <h4 className="port-refuge-name">{activePort.name}</h4>
                <span className="port-refuge-coords">{activePort.lat}, {activePort.lon}</span>
              </div>
            </div>
            <div className="port-refuge-meta">
              <span>Depth Draft: <strong>{activePort.depth}</strong></span>
              <span className={`refuge-status-tag status-${activePort.status.toLowerCase()}`}>
                {activePort.status}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
