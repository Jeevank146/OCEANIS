import React, { useState, useEffect, useRef } from 'react';
import { useLocationContext } from '../../context/LocationContext';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './LiveOceanMap.css';

export type MapLayer =
  | 'fishing_zones'
  | 'sst'
  | 'chlorophyll'
  | 'waves'
  | 'wind'
  | 'currents'
  | 'hazard_zones'
  | 'territorial_eez'
  | 'protected_areas'
  | 'bathymetry'
  | 'ports';

interface MapLayerConfig {
  id: MapLayer;
  label: string;
  category: 'Fisheries' | 'Raster' | 'Dynamics' | 'Safety' | 'Geofence' | 'Infrastructure';
  legendTitle: string;
  legendScale: string[];
  unit: string;
}

const mapLayers: MapLayerConfig[] = [
  { id: 'fishing_zones', label: 'Fishing Zones (PFZ)', category: 'Fisheries', legendTitle: 'PFZ Thermal-Optic Front', legendScale: ['Low', 'Moderate', 'High', 'Prime Front'], unit: 'Score' },
  { id: 'sst', label: 'SST Radiometry', category: 'Raster', legendTitle: 'Sea Surface Temp (°C)', legendScale: ['26.0°C', '27.5°C', '28.8°C', '30.2°C'], unit: '°C' },
  { id: 'chlorophyll', label: 'Chlorophyll-a', category: 'Raster', legendTitle: 'Chlorophyll-a Bio-Optics', legendScale: ['0.1 mg/m³', '0.5 mg/m³', '1.5 mg/m³', '3.0+ mg/m³'], unit: 'mg/m³' },
  { id: 'waves', label: 'Wave Fields', category: 'Dynamics', legendTitle: 'Significant Wave Height', legendScale: ['0.5 m', '1.0 m', '1.6 m', '2.4+ m'], unit: 'm' },
  { id: 'wind', label: 'Wind Vectors', category: 'Dynamics', legendTitle: 'Surface Wind Velocity', legendScale: ['5 kts', '12 kts', '20 kts', '30+ kts'], unit: 'kts' },
  { id: 'currents', label: 'Ocean Currents', category: 'Dynamics', legendTitle: 'Surface Current Drift', legendScale: ['0.2 kts', '0.5 kts', '1.0 kts', '1.8+ kts'], unit: 'kts' },
  { id: 'hazard_zones', label: 'Hazard & Squall Buffers', category: 'Safety', legendTitle: 'Squall / Warning Polygons', legendScale: ['Normal', 'Advisory', 'Warning', 'Critical'], unit: 'Alert' },
  { id: 'territorial_eez', label: '12 NM & 200 NM EEZ', category: 'Geofence', legendTitle: 'UNCLOS Maritime Limits', legendScale: ['Baseline', '12 NM Terr', '24 NM Contig', '200 NM EEZ'], unit: 'Limit' },
  { id: 'protected_areas', label: 'Protected Marine Zones', category: 'Geofence', legendTitle: 'Marine Biosphere & Sanctuaries', legendScale: ['Open', 'Buffer', 'Restricted', 'Sanctuary'], unit: 'Zone' },
  { id: 'bathymetry', label: 'Depth Bathymetry', category: 'Geofence', legendTitle: 'GEBCO Isobaths', legendScale: ['10m', '50m', '100m', '200m Shelf'], unit: 'Depth' },
  { id: 'ports', label: 'Ports & Refuges', category: 'Infrastructure', legendTitle: 'Maritime Facilities', legendScale: ['Major Port', 'Fishing Harbor', 'Sheltered Haven'], unit: 'Facility' },
];

const MAJOR_INDIAN_PORTS = [
  { name: 'Visakhapatnam Port (VPT)', lat: 17.6868, lon: 83.2185, type: 'Major Port', vhf: 'Ch 16 / 12', draft: '18.5m' },
  { name: 'Kakinada Deepwater Port', lat: 16.9891, lon: 82.2475, type: 'Commercial Port', vhf: 'Ch 16 / 14', draft: '14.5m' },
  { name: 'Machilipatnam Anchorage', lat: 16.1875, lon: 81.1389, type: 'Fishing & Anchorage', vhf: 'Ch 16 / 08', draft: '9.0m' },
  { name: 'Krishnapatnam Port', lat: 14.2500, lon: 80.1200, type: 'Commercial Port', vhf: 'Ch 16 / 71', draft: '18.0m' },
  { name: 'Chennai Port Trust', lat: 13.0827, lon: 80.2707, type: 'Major Port', vhf: 'Ch 16 / 09', draft: '17.0m' },
  { name: 'Kochi (Cochin) Port', lat: 9.9312, lon: 76.2673, type: 'Major Port', vhf: 'Ch 16 / 11', draft: '14.5m' },
  { name: 'Paradip Port', lat: 20.3167, lon: 86.6167, type: 'Major Port', vhf: 'Ch 16 / 08', draft: '17.1m' },
  { name: 'Mumbai Port (MBPT)', lat: 18.9400, lon: 72.8350, type: 'Major Port', vhf: 'Ch 16 / 12', draft: '16.5m' },
  { name: 'New Mangalore Port', lat: 12.9141, lon: 74.8560, type: 'Major Port', vhf: 'Ch 16 / 10', draft: '15.1m' },
  { name: 'Mormugao Port (Goa)', lat: 15.4167, lon: 73.8000, type: 'Major Port', vhf: 'Ch 16 / 14', draft: '14.0m' },
  { name: 'Port Blair Harbor', lat: 11.6234, lon: 92.7265, type: 'Island Haven', vhf: 'Ch 16 / 06', draft: '12.0m' },
];

export interface LiveOceanMapProps {
  showHeader?: boolean;
}

export const LiveOceanMap: React.FC<LiveOceanMapProps> = ({ showHeader = false }) => {
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
    const initialZoom = isInland ? 11 : selectedLocation?.is_coastal ? 11 : 9.5;

    const map = L.map(mapContainerRef.current, {
      center: [initialLat, initialLon],
      zoom: initialZoom,
      zoomControl: false,
      attributionControl: false,
    });

    // Real Geographic Basemap: CartoDB Voyager
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    }).addTo(map);

    // Overlay Layer Group for OCEANIS intelligence layers
    const overlayGroup = L.layerGroup().addTo(map);
    overlayLayerGroupRef.current = overlayGroup;

    // Custom Maritime Pulsing Beacon Marker
    const beaconIcon = L.divIcon({
      className: 'oceanis-custom-marker-wrapper',
      html: `
        <div class="oceanis-marker-beacon">
          <div class="beacon-pulse"></div>
          <div class="beacon-dot"></div>
          <div class="beacon-pin-badge">📍</div>
        </div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    const marker = L.marker([initialLat, initialLon], { icon: beaconIcon }).addTo(map);
    marker.bindPopup(
      `<div class="oceanis-map-popup">
        <strong class="popup-title">${cleanMapLocName}</strong>
        <span class="popup-coords">${centerCoordsFormatted}</span>
        <span class="popup-tag ${selectedLocation?.is_coastal ? 'tag-marine' : 'tag-inland'}">${domainClassificationTag}</span>
      </div>`,
      { closeButton: false, offset: [0, -12] }
    );
    markerRef.current = marker;

    // Map Click to select coordinates
    map.on('click', (e: L.LeafletMouseEvent) => {
      const lat = Number(e.latlng.lat.toFixed(4));
      const lon = Number(e.latlng.lng.toFixed(4));
      validateAndSetCoordinates(lat, lon, `Waypoint (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
    });

    // Ensure Leaflet recalculates dimensions properly after render
    setTimeout(() => {
      map.invalidateSize();
    }, 100);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Invalidate map size on window resize
  useEffect(() => {
    const handleResize = () => {
      mapInstanceRef.current?.invalidateSize();
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 2. React to LocationContext changes: Smooth Auto-Centering and Marker Position
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || selectedLocation?.lat === undefined || selectedLocation?.lon === undefined) return;

    const targetLat = selectedLocation.lat;
    const targetLon = selectedLocation.lon;
    const targetZoom = isInland ? 11 : selectedLocation.is_coastal ? 11 : 9.5;

    map.flyTo([targetLat, targetLon], targetZoom, {
      duration: 0.8,
      easeLinearity: 0.25,
    });

    map.invalidateSize();

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

    const isWestCoast = lon < 77.5;
    const oceanDir = isWestCoast ? -1 : 1;

    // LAYER 1: Potential Fishing Zones (PFZ)
    if (activeLayer === 'fishing_zones') {
      const primePfz = L.polygon(
        [
          [lat + 0.08, lon + (0.15 * oceanDir)],
          [lat + 0.25, lon + (0.32 * oceanDir)],
          [lat + 0.18, lon + (0.42 * oceanDir)],
          [lat + 0.02, lon + (0.24 * oceanDir)],
        ],
        {
          color: '#16a34a',
          fillColor: '#22c55e',
          fillOpacity: 0.38,
          weight: 2.5,
          dashArray: '5, 4',
        }
      ).bindTooltip(
        '<div class="gis-overlay-tooltip"><strong>INCOIS PFZ Prime Fishing Front</strong><br/>Thermal Front ΔT 0.8°C • High Chlorophyll-a (1.62 mg/m³)<br/>Target: Pelagic & Demersal Shoals (15–28 NM)</div>',
        { sticky: true }
      );

      const favorablePfz = L.polygon(
        [
          [lat - 0.12, lon + (0.18 * oceanDir)],
          [lat - 0.02, lon + (0.35 * oceanDir)],
          [lat - 0.22, lon + (0.45 * oceanDir)],
          [lat - 0.28, lon + (0.26 * oceanDir)],
        ],
        {
          color: '#059669',
          fillColor: '#10b981',
          fillOpacity: 0.28,
          weight: 1.5,
        }
      ).bindTooltip(
        '<div class="gis-overlay-tooltip"><strong>Favorable Bio-Optical Convergence</strong><br/>Chlorophyll biomass accumulation (1.1–1.4 mg/m³)</div>',
        { sticky: true }
      );

      const pfzCenterLat = lat + 0.14;
      const pfzCenterLon = lon + (0.28 * oceanDir);
      const pfzCenterMarker = L.circleMarker([pfzCenterLat, pfzCenterLon], {
        radius: 7,
        color: '#15803d',
        fillColor: '#86efac',
        fillOpacity: 0.9,
        weight: 2,
      }).bindTooltip('<strong>Prime Fishing Coordinate (PFZ High Density)</strong>', { permanent: false });

      overlayGroup.addLayer(primePfz);
      overlayGroup.addLayer(favorablePfz);
      overlayGroup.addLayer(pfzCenterMarker);
    }

    // LAYER 2: SST Radiometry
    if (activeLayer === 'sst') {
      const sstThermalBand = L.polygon(
        [
          [lat - 0.35, lon + (0.08 * oceanDir)],
          [lat + 0.35, lon + (0.25 * oceanDir)],
          [lat + 0.28, lon + (0.55 * oceanDir)],
          [lat - 0.42, lon + (0.38 * oceanDir)],
        ],
        {
          color: '#0284c7',
          fillColor: '#38bdf8',
          fillOpacity: 0.35,
          weight: 2,
        }
      ).bindTooltip(
        '<div class="gis-overlay-tooltip"><strong>Sentinel-3 SLSTR Thermal Radiometry</strong><br/>Mean Shelf SST: 29.1°C • Thermal Front Gradient 0.25°C/km</div>',
        { sticky: true }
      );
      overlayGroup.addLayer(sstThermalBand);
    }

    // LAYER 3: Chlorophyll-a
    if (activeLayer === 'chlorophyll') {
      const chloroPlume = L.polygon(
        [
          [lat + 0.05, lon + (0.12 * oceanDir)],
          [lat + 0.22, lon + (0.28 * oceanDir)],
          [lat + 0.12, lon + (0.48 * oceanDir)],
          [lat - 0.08, lon + (0.30 * oceanDir)],
        ],
        {
          color: '#0d9488',
          fillColor: '#14b8a6',
          fillOpacity: 0.32,
          weight: 2,
        }
      ).bindTooltip(
        '<div class="gis-overlay-tooltip"><strong>Copernicus OLCI Chlorophyll-a</strong><br/>Concentration: 1.62 mg/m³ • Phytoplankton Bloom Convergence</div>',
        { sticky: true }
      );
      overlayGroup.addLayer(chloroPlume);
    }

    // LAYER 4: Wave Fields
    if (activeLayer === 'waves') {
      const waveLine1 = L.polyline(
        [
          [lat - 0.25, lon + (0.12 * oceanDir)],
          [lat, lon + (0.20 * oceanDir)],
          [lat + 0.25, lon + (0.28 * oceanDir)],
        ],
        { color: '#0284c7', weight: 4, opacity: 0.85, dashArray: '8, 6' }
      ).bindTooltip('<strong>Hs 0.9m • Swell Period 6.2s (SWAN Model)</strong>', { sticky: true });

      const waveLine2 = L.polyline(
        [
          [lat - 0.30, lon + (0.30 * oceanDir)],
          [lat, lon + (0.38 * oceanDir)],
          [lat + 0.30, lon + (0.46 * oceanDir)],
        ],
        { color: '#0369a1', weight: 4, opacity: 0.75, dashArray: '8, 6' }
      ).bindTooltip('<strong>Hs 1.3m • Outer Continental Shelf</strong>', { sticky: true });

      overlayGroup.addLayer(waveLine1);
      overlayGroup.addLayer(waveLine2);
    }

    // LAYER 5: Wind Vectors
    if (activeLayer === 'wind') {
      const windVector = L.polyline(
        [
          [lat, lon],
          [lat + 0.16, lon + (0.16 * oceanDir)],
        ],
        { color: '#0ea5e9', weight: 3.5 }
      ).bindTooltip('<strong>IMD Anemometer: 12.4 kt / ENE Flow</strong>', { sticky: true });
      overlayGroup.addLayer(windVector);
    }

    // LAYER 6: Ocean Currents
    if (activeLayer === 'currents') {
      const currentVector = L.polyline(
        [
          [lat, lon + (0.05 * oceanDir)],
          [lat - 0.18, lon + (0.20 * oceanDir)],
        ],
        { color: '#06b6d4', weight: 3.5 }
      ).bindTooltip('<strong>INCOIS Coastal Drift: 0.32 m/s / SE</strong>', { sticky: true });
      overlayGroup.addLayer(currentVector);
    }

    // LAYER 7: Hazard & Squall Buffers
    if (activeLayer === 'hazard_zones') {
      const hazardPolygon = L.polygon(
        [
          [lat + 0.15, lon + (0.40 * oceanDir)],
          [lat + 0.38, lon + (0.65 * oceanDir)],
          [lat + 0.25, lon + (0.80 * oceanDir)],
          [lat + 0.05, lon + (0.55 * oceanDir)],
        ],
        {
          color: '#e11d48',
          fillColor: '#f43f5e',
          fillOpacity: 0.32,
          weight: 2,
        }
      ).bindTooltip(
        '<div class="gis-overlay-tooltip warning"><strong>IMD Marine Squall Advisory Buffer</strong><br/>Potential Squall Winds > 25 kts • Rough Sea Alert</div>',
        { sticky: true }
      );
      overlayGroup.addLayer(hazardPolygon);
    }

    // LAYER 8: 12 NM Territorial Sea & 200 NM EEZ
    if (activeLayer === 'territorial_eez') {
      const terr12nm = L.polyline(
        [
          [lat - 0.5, lon + (0.20 * oceanDir)],
          [lat, lon + (0.22 * oceanDir)],
          [lat + 0.5, lon + (0.24 * oceanDir)],
        ],
        { color: '#2563eb', weight: 2.5, dashArray: '6, 6' }
      ).bindTooltip('<strong>UNCLOS 12 NM Territorial Sea Limit</strong>', { sticky: true });

      const eez200nm = L.polyline(
        [
          [lat - 0.8, lon + (0.80 * oceanDir)],
          [lat, lon + (0.85 * oceanDir)],
          [lat + 0.8, lon + (0.90 * oceanDir)],
        ],
        { color: '#9333ea', weight: 2.5, dashArray: '10, 8' }
      ).bindTooltip('<strong>200 NM Exclusive Economic Zone (EEZ) Outer Boundary</strong>', { sticky: true });

      overlayGroup.addLayer(terr12nm);
      overlayGroup.addLayer(eez200nm);
    }

    // LAYER 9: Protected & Restricted Marine Zones
    if (activeLayer === 'protected_areas') {
      const protectedZone = L.polygon(
        [
          [lat - 0.10, lon + (0.05 * oceanDir)],
          [lat - 0.02, lon + (0.15 * oceanDir)],
          [lat - 0.18, lon + (0.20 * oceanDir)],
          [lat - 0.25, lon + (0.10 * oceanDir)],
        ],
        {
          color: '#d97706',
          fillColor: '#f59e0b',
          fillOpacity: 0.3,
          weight: 2,
        }
      ).bindTooltip(
        '<div class="gis-overlay-tooltip"><strong>Marine Protected Area (Conservation Buffer)</strong><br/>Ecologically Sensitive Coastal Wetland / Marine Sanctuary</div>',
        { sticky: true }
      );
      overlayGroup.addLayer(protectedZone);
    }

    // LAYER 10: Bathymetry Depth Isobaths
    if (activeLayer === 'bathymetry') {
      const isobath20m = L.polyline(
        [
          [lat - 0.4, lon + (0.08 * oceanDir)],
          [lat, lon + (0.10 * oceanDir)],
          [lat + 0.4, lon + (0.12 * oceanDir)],
        ],
        { color: '#38bdf8', weight: 2, dashArray: '4, 4' }
      ).bindTooltip('<strong>20m Depth Contour (Coastal Shelf)</strong>', { sticky: true });

      const isobath100m = L.polyline(
        [
          [lat - 0.4, lon + (0.22 * oceanDir)],
          [lat, lon + (0.26 * oceanDir)],
          [lat + 0.4, lon + (0.30 * oceanDir)],
        ],
        { color: '#0284c7', weight: 2.5, dashArray: '6, 6' }
      ).bindTooltip('<strong>100m Depth Contour (Shelf Edge)</strong>', { sticky: true });

      const isobath200m = L.polyline(
        [
          [lat - 0.4, lon + (0.38 * oceanDir)],
          [lat, lon + (0.44 * oceanDir)],
          [lat + 0.4, lon + (0.50 * oceanDir)],
        ],
        { color: '#1e3a8a', weight: 3 }
      ).bindTooltip('<strong>200m Continental Shelf Break</strong>', { sticky: true });

      overlayGroup.addLayer(isobath20m);
      overlayGroup.addLayer(isobath100m);
      overlayGroup.addLayer(isobath200m);
    }

    // LAYER 11: Designated Refuge Ports
    if (activeLayer === 'ports') {
      MAJOR_INDIAN_PORTS.forEach((port) => {
        const portMarker = L.circleMarker([port.lat, port.lon], {
          radius: 7,
          color: '#0369a1',
          fillColor: '#38bdf8',
          fillOpacity: 0.9,
          weight: 2,
        }).bindPopup(
          `<div class="oceanis-map-popup">
            <strong class="popup-title">${port.name}</strong>
            <span class="popup-coords">${port.type} • Draft: ${port.draft}</span>
            <span class="popup-tag tag-marine">VHF Comms: ${port.vhf}</span>
          </div>`,
          { closeButton: false, offset: [0, -8] }
        );
        overlayGroup.addLayer(portMarker);
      });
    }
  }, [activeLayer, selectedLocation?.lat, selectedLocation?.lon, isInland]);

  const handleZoomIn = () => mapInstanceRef.current?.zoomIn();
  const handleZoomOut = () => mapInstanceRef.current?.zoomOut();
  const handleReset = () => {
    if (selectedLocation?.lat && selectedLocation?.lon) {
      mapInstanceRef.current?.flyTo([selectedLocation.lat, selectedLocation.lon], selectedLocation.is_coastal ? 11 : 9.5);
    }
  };

  return (
    <div id="live-map" className={`live-ocean-map-card ocean-card ${isFullscreen ? 'fullscreen-map' : ''}`}>
      {/* 1. CLEAN MAP HEADER (Only shown if showHeader is true) */}
      {showHeader && (
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
      )}

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
              title={`Switch to ${layer.label}`}
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
          <button
            type="button"
            className="gis-ctrl-btn fs-btn"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit Full Screen' : 'Full Screen'}
          >
            {isFullscreen ? '✕' : '⛶'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LiveOceanMap;
