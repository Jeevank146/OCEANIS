import React, { useState, useEffect, useRef } from 'react';
import { useLocationContext } from '../../context/LocationContext';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './LiveOceanMap.css';

export type MapLayer =
  | 'sst'
  | 'chlorophyll'
  | 'waves'
  | 'wind'
  | 'currents'
  | 'fishing_zones'
  | 'hazard_zones'
  | 'territorial_eez'
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
  { id: 'sst', label: 'SST Radiometry', category: 'Raster', legendTitle: 'Sea Surface Temp (°C)', legendScale: ['26.0°C', '27.5°C', '28.8°C', '30.2°C'], unit: '°C' },
  { id: 'chlorophyll', label: 'Chlorophyll-a', category: 'Raster', legendTitle: 'Chlorophyll-a Bio-Optics', legendScale: ['0.1 mg/m³', '0.5 mg/m³', '1.5 mg/m³', '3.0+ mg/m³'], unit: 'mg/m³' },
  { id: 'waves', label: 'Wave Fields', category: 'Dynamics', legendTitle: 'Significant Wave Height', legendScale: ['0.5 m', '1.0 m', '1.6 m', '2.4+ m'], unit: 'm' },
  { id: 'wind', label: 'Wind Vectors', category: 'Dynamics', legendTitle: 'Surface Wind Velocity', legendScale: ['5 kts', '12 kts', '20 kts', '30+ kts'], unit: 'kts' },
  { id: 'currents', label: 'Ocean Currents', category: 'Dynamics', legendTitle: 'Surface Current Drift', legendScale: ['0.2 kts', '0.5 kts', '1.0 kts', '1.8+ kts'], unit: 'kts' },
  { id: 'fishing_zones', label: 'Fishing Zones (PFZ)', category: 'Geofence', legendTitle: 'PFZ Thermal-Optic Score', legendScale: ['Low', 'Moderate', 'High', 'Prime Front'], unit: 'Score' },
  { id: 'hazard_zones', label: 'Hazard Zones', category: 'Geofence', legendTitle: 'Hazard Severity Polygons', legendScale: ['Normal', 'Advisory', 'Warning', 'Critical'], unit: 'Alert' },
  { id: 'territorial_eez', label: '12 NM & EEZ Limits', category: 'Geofence', legendTitle: 'UNCLOS Maritime Boundaries', legendScale: ['Baseline', '12 NM Terr', '24 NM Contig', '200 NM EEZ'], unit: 'Limit' },
  { id: 'ports', label: 'Ports & Refuges', category: 'Infrastructure', legendTitle: 'Maritime Facilities', legendScale: ['Major Port', 'Fishing Harbor', 'Sheltered Haven'], unit: 'Facility' },
];

const MAJOR_INDIAN_PORTS = [
  { name: 'Visakhapatnam Port (VPT)', lat: 17.6868, lon: 83.2185, type: 'Major Port', vhf: 'Ch 16 / 12' },
  { name: 'Kakinada Deepwater Port', lat: 16.9891, lon: 82.2475, type: 'Commercial Port', vhf: 'Ch 16 / 14' },
  { name: 'Chennai Port Trust', lat: 13.0827, lon: 80.2707, type: 'Major Port', vhf: 'Ch 16 / 09' },
  { name: 'Kochi (Cochin) Port', lat: 9.9312, lon: 76.2673, type: 'Major Port', vhf: 'Ch 16 / 11' },
  { name: 'Paradip Port', lat: 20.3167, lon: 86.6167, type: 'Major Port', vhf: 'Ch 16 / 08' },
  { name: 'Mumbai Port (MBPT)', lat: 18.9400, lon: 72.8350, type: 'Major Port', vhf: 'Ch 16 / 12' },
  { name: 'New Mangalore Port', lat: 12.9141, lon: 74.8560, type: 'Major Port', vhf: 'Ch 16 / 10' },
  { name: 'Mormugao Port (Goa)', lat: 15.4167, lon: 73.8000, type: 'Major Port', vhf: 'Ch 16 / 14' },
  { name: 'Port Blair Harbor', lat: 11.6234, lon: 92.7265, type: 'Island Haven', vhf: 'Ch 16 / 06' },
];

export const LiveOceanMap: React.FC = () => {
  const { selectedLocation, validateAndSetCoordinates, isValidating, activeValidation } = useLocationContext();
  const [activeLayer, setActiveLayer] = useState<MapLayer>('fishing_zones');
  const [isFullscreen, setIsFullscreen] = useState(false);

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const overlayLayerGroupRef = useRef<L.LayerGroup | null>(null);

  const isInland = Boolean(
    activeValidation && (activeValidation.status === 'INLAND' || activeValidation.is_coastal === false || activeValidation.is_marine === false)
  );

  const isOffshoreDomain = Boolean(
    (!selectedLocation?.is_coastal && selectedLocation?.distance_to_coast_km && selectedLocation.distance_to_coast_km > 20.0) ||
    (selectedLocation?.status === 'VALID_MARINE' && !selectedLocation?.is_coastal) ||
    (selectedLocation?.name && selectedLocation.name.toLowerCase().includes('offshore')) ||
    (selectedLocation?.name && selectedLocation.name.toLowerCase().includes('waypoint'))
  );

  const cleanMapLocName = selectedLocation?.name
    ? (selectedLocation.name.replace(/\s*\([^)]*\)/g, '').trim() || selectedLocation.name)
    : 'Selected Operating Area';

  const centerCoordsFormatted = selectedLocation?.lat !== undefined && selectedLocation?.lon !== undefined
    ? `${Math.abs(selectedLocation.lat).toFixed(4)}° ${selectedLocation.lat >= 0 ? 'N' : 'S'}, ${Math.abs(selectedLocation.lon).toFixed(4)}° ${selectedLocation.lon >= 0 ? 'E' : 'W'}`
    : '17.6868° N, 83.2185° E';

  const domainClassificationTag = selectedLocation?.is_coastal
    ? 'COASTAL SECTOR'
    : isOffshoreDomain
    ? 'OFFSHORE SECTOR'
    : 'INLAND SECTOR';

  const activeConfig = mapLayers.find((l) => l.id === activeLayer) || mapLayers[0];

  // 1. Initialize Leaflet Map on Mount
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const initialLat = selectedLocation?.lat || 17.6868;
    const initialLon = selectedLocation?.lon || 83.2185;
    const initialZoom = selectedLocation?.is_coastal ? 10 : 8;

    const map = L.map(mapContainerRef.current, {
      center: [initialLat, initialLon],
      zoom: initialZoom,
      zoomControl: false,
      attributionControl: false,
    });

    // Real Geographic Basemap: CartoDB Voyager / OpenStreetMap tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    }).addTo(map);

    // Overlay Layer Group for OCEANIS intelligence layers
    const overlayGroup = L.layerGroup().addTo(map);
    overlayLayerGroupRef.current = overlayGroup;

    // Custom Maritime Beacon Marker
    const beaconIcon = L.divIcon({
      className: 'oceanis-custom-marker-wrapper',
      html: '<div class="oceanis-marker-beacon"><div class="beacon-pulse"></div><div class="beacon-dot"></div></div>',
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });

    const marker = L.marker([initialLat, initialLon], { icon: beaconIcon }).addTo(map);
    marker.bindPopup(
      `<div class="oceanis-map-popup">
        <strong class="popup-title">${cleanMapLocName}</strong>
        <span class="popup-coords">${centerCoordsFormatted}</span>
        <span class="popup-tag ${selectedLocation?.is_coastal ? 'tag-marine' : 'tag-inland'}">${domainClassificationTag}</span>
      </div>`,
      { closeButton: false, offset: [0, -10] }
    );
    markerRef.current = marker;

    // Map Click to select coordinates
    map.on('click', (e: L.LeafletMouseEvent) => {
      const lat = Number(e.latlng.lat.toFixed(4));
      const lon = Number(e.latlng.lng.toFixed(4));
      validateAndSetCoordinates(lat, lon, `Waypoint (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. React to LocationContext changes: Smooth Auto-Centering and Marker Position
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || selectedLocation?.lat === undefined || selectedLocation?.lon === undefined) return;

    const targetLat = selectedLocation.lat;
    const targetLon = selectedLocation.lon;
    const targetZoom = isInland ? 10 : selectedLocation.is_coastal ? 10 : 8;

    // Smoothly fly to the exact selected coordinates
    map.flyTo([targetLat, targetLon], targetZoom, {
      duration: 0.8,
      easeLinearity: 0.25,
    });

    // Update marker position & popup
    if (markerRef.current) {
      markerRef.current.setLatLng([targetLat, targetLon]);
      markerRef.current.setPopupContent(
        `<div class="oceanis-map-popup">
          <strong class="popup-title">${cleanMapLocName}</strong>
          <span class="popup-coords">${centerCoordsFormatted}</span>
          <span class="popup-tag ${selectedLocation.is_coastal ? 'tag-marine' : 'tag-inland'}">${domainClassificationTag}</span>
        </div>`
      );
    }
  }, [selectedLocation?.lat, selectedLocation?.lon, selectedLocation?.name, isInland, domainClassificationTag, centerCoordsFormatted, cleanMapLocName]);

  // 3. Render Dynamic OCEANIS Marine Intelligence Overlays based on activeLayer
  useEffect(() => {
    const overlayGroup = overlayLayerGroupRef.current;
    if (!overlayGroup) return;

    overlayGroup.clearLayers();

    // If location is inland, suppress marine-specific layers
    if (isInland) {
      return;
    }

    const lat = selectedLocation?.lat || 17.6868;
    const lon = selectedLocation?.lon || 83.2185;

    // Layer: Potential Fishing Zones (PFZ)
    if (activeLayer === 'fishing_zones') {
      const pfzPolygon = L.polygon(
        [
          [lat + 0.12, lon + 0.18],
          [lat + 0.28, lon + 0.35],
          [lat + 0.22, lon + 0.45],
          [lat + 0.05, lon + 0.25],
        ],
        {
          color: '#16a34a',
          fillColor: '#22c55e',
          fillOpacity: 0.35,
          weight: 2,
          dashArray: '4, 4',
        }
      ).bindTooltip('INCOIS PFZ Prime Fishing Front (Thermal ΔT 0.8°C)', { permanent: false, direction: 'top' });

      const secondaryPfz = L.circle([lat - 0.15, lon + 0.3], {
        radius: 8500,
        color: '#059669',
        fillColor: '#10b981',
        fillOpacity: 0.28,
        weight: 1.5,
      }).bindTooltip('Favorable Chlorophyll-a Biomass Convergence', { permanent: false });

      overlayGroup.addLayer(pfzPolygon);
      overlayGroup.addLayer(secondaryPfz);
    }

    // Layer: SST Radiometry
    if (activeLayer === 'sst') {
      const sstThermalBand = L.polygon(
        [
          [lat - 0.4, lon + 0.1],
          [lat + 0.4, lon + 0.3],
          [lat + 0.3, lon + 0.6],
          [lat - 0.5, lon + 0.4],
        ],
        {
          color: '#0284c7',
          fillColor: '#38bdf8',
          fillOpacity: 0.32,
          weight: 1.5,
        }
      ).bindTooltip('Sentinel-3 SLSTR Radiometry: 29.1°C Continental Shelf Break', { permanent: false });
      overlayGroup.addLayer(sstThermalBand);
    }

    // Layer: Chlorophyll-a
    if (activeLayer === 'chlorophyll') {
      const chloroPlume = L.circle([lat + 0.08, lon + 0.22], {
        radius: 12000,
        color: '#0d9488',
        fillColor: '#14b8a6',
        fillOpacity: 0.3,
        weight: 2,
      }).bindTooltip('Copernicus OLCI: 1.62 mg/m³ High Bio-Productivity Plume', { permanent: false });
      overlayGroup.addLayer(chloroPlume);
    }

    // Layer: Waves
    if (activeLayer === 'waves') {
      const waveFront = L.polyline(
        [
          [lat - 0.3, lon + 0.15],
          [lat, lon + 0.25],
          [lat + 0.3, lon + 0.35],
        ],
        {
          color: '#0284c7',
          weight: 4,
          opacity: 0.8,
          dashArray: '8, 6',
        }
      ).bindTooltip('Significant Wave Height (Hs): 0.9m SWAN Model', { permanent: false });
      overlayGroup.addLayer(waveFront);
    }

    // Layer: Wind Vectors & Currents
    if (activeLayer === 'wind' || activeLayer === 'currents') {
      const vectorLine = L.polyline(
        [
          [lat, lon],
          [lat + 0.18, lon + 0.18],
        ],
        {
          color: activeLayer === 'wind' ? '#0ea5e9' : '#06b6d4',
          weight: 3,
        }
      ).bindTooltip(
        activeLayer === 'wind'
          ? 'IMD Anemometer: 12.4 kt / ENE Flow'
          : 'INCOIS Current Drift: 0.32 m/s / SE',
        { permanent: false }
      );
      overlayGroup.addLayer(vectorLine);
    }

    // Layer: Hazard Zones
    if (activeLayer === 'hazard_zones') {
      const hazardPolygon = L.polygon(
        [
          [lat + 0.2, lon + 0.5],
          [lat + 0.45, lon + 0.75],
          [lat + 0.3, lon + 0.9],
          [lat + 0.1, lon + 0.65],
        ],
        {
          color: '#e11d48',
          fillColor: '#f43f5e',
          fillOpacity: 0.3,
          weight: 2,
        }
      ).bindTooltip('IMD Squall Warning Buffer (Squall Wind > 25 kts)', { permanent: false });
      overlayGroup.addLayer(hazardPolygon);
    }

    // Layer: 12 NM Territorial Sea & 200 NM EEZ Boundaries
    if (activeLayer === 'territorial_eez') {
      const terr12nm = L.polyline(
        [
          [lat - 0.6, lon + 0.2],
          [lat, lon + 0.22],
          [lat + 0.6, lon + 0.24],
        ],
        {
          color: '#2563eb',
          weight: 2.5,
          dashArray: '6, 6',
        }
      ).bindTooltip('UNCLOS 12 NM Territorial Water Boundary', { permanent: false });

      const eez200nm = L.polyline(
        [
          [lat - 0.8, lon + 0.8],
          [lat, lon + 0.85],
          [lat + 0.8, lon + 0.9],
        ],
        {
          color: '#9333ea',
          weight: 2,
          dashArray: '10, 8',
        }
      ).bindTooltip('200 NM Exclusive Economic Zone (EEZ) Outer Limit', { permanent: false });

      overlayGroup.addLayer(terr12nm);
      overlayGroup.addLayer(eez200nm);
    }

    // Layer: Ports & Refuges
    if (activeLayer === 'ports') {
      MAJOR_INDIAN_PORTS.forEach((port) => {
        const portMarker = L.circleMarker([port.lat, port.lon], {
          radius: 6,
          color: '#0369a1',
          fillColor: '#38bdf8',
          fillOpacity: 0.9,
          weight: 2,
        }).bindPopup(
          `<div class="oceanis-map-popup">
            <strong class="popup-title">${port.name}</strong>
            <span class="popup-coords">${port.type}</span>
            <span class="popup-tag tag-marine">VHF: ${port.vhf}</span>
          </div>`,
          { closeButton: false, offset: [0, -6] }
        );
        overlayGroup.addLayer(portMarker);
      });
    }
  }, [activeLayer, selectedLocation?.lat, selectedLocation?.lon, isInland]);

  const handleZoomIn = () => mapInstanceRef.current?.zoomIn();
  const handleZoomOut = () => mapInstanceRef.current?.zoomOut();
  const handleReset = () => {
    if (selectedLocation?.lat && selectedLocation?.lon) {
      mapInstanceRef.current?.flyTo([selectedLocation.lat, selectedLocation.lon], selectedLocation.is_coastal ? 10 : 8);
    }
  };

  return (
    <div id="live-map" className={`live-ocean-map-card ocean-card ${isFullscreen ? 'fullscreen-map' : ''}`}>
      {/* 1. CLEAN MAP HEADER (No duplicate coordinates) */}
      <div className="map-card-header">
        <div className="map-header-left">
          <h2 className="map-title-text">Live Ocean Intelligence Map</h2>
          <div className="map-meta-info-row">
            <span className="map-meta-item"><strong className="meta-lbl">{cleanMapLocName}</strong></span>
            <span className="map-meta-sep">•</span>
            <span className="map-meta-item">{centerCoordsFormatted}</span>
            <span className="map-meta-sep">•</span>
            <span className={`domain-badge ${isInland ? 'inland' : ''}`}>{domainClassificationTag}</span>
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

      {/* 2. LAYER PILLS BAR */}
      <div className="map-layer-pills-bar">
        <span className="layer-pills-label">OVERLAYS:</span>
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

      {/* 3. REAL GEOGRAPHIC MAP CONTAINER */}
      <div className="map-viewport-container" title="Click anywhere on the map to set waypoint coordinates">
        {/* Real Leaflet Map Container */}
        <div ref={mapContainerRef} className="leaflet-map-root" />

        {/* Loading Spinner during coordinate resolution */}
        {isValidating && (
          <div className="map-loading-overlay">
            <span className="map-loading-spinner" />
            <span>Resolving spatial coordinates...</span>
          </div>
        )}

        {/* Inland Location Protection Overlay */}
        {isInland && (
          <div className="inland-map-overlay-banner">
            <div className="inland-overlay-icon">🏞️</div>
            <div className="inland-overlay-body">
              <strong>INLAND LOCATION</strong>
              <span>Marine intelligence is unavailable for this location. Oceanographic and coastal models are inactive.</span>
            </div>
          </div>
        )}

        {/* Layer Legend Overlay */}
        {!isInland && (
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
        )}

        {/* Map GIS Controls */}
        <div className="map-gis-controls">
          <button type="button" className="gis-ctrl-btn" onClick={handleZoomIn} title="Zoom In">+</button>
          <button type="button" className="gis-ctrl-btn" onClick={handleZoomOut} title="Zoom Out">−</button>
          <button type="button" className="gis-ctrl-btn" onClick={handleReset} title="Reset View">⊙</button>
        </div>
      </div>
    </div>
  );
};

export default LiveOceanMap;
