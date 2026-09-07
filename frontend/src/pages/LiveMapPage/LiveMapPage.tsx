import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import { LiveOceanMap } from '../../components/LiveOceanMap/LiveOceanMap';
import './LiveMapPage.css';

interface SafePort {
  id: string;
  name: string;
  state: string;
  distanceNm: number;
  draftDepth: string;
  berthStatus: 'Available' | 'High Occupancy' | 'Protected Harbor';
  coordinates: string;
  bearing: string;
  vhfChannel: string;
}

export const LiveMapPage: React.FC = () => {
  const { selectedLocation } = useLocationContext();
  const [selectedPort, setSelectedPort] = useState<string>('vizag');
  const [activeTab, setActiveTab] = useState<'layers' | 'ports' | 'vessels'>('layers');

  const safePorts: SafePort[] = [
    {
      id: 'vizag',
      name: 'Visakhapatnam Port (VPT / Outer Harbor)',
      state: 'Andhra Pradesh',
      distanceNm: 4.2,
      draftDepth: '16.5m (Deep Water)',
      berthStatus: 'Protected Harbor',
      coordinates: '17.6868° N, 83.2185° E',
      bearing: '285° WNW',
      vhfChannel: 'Ch 16 / Ch 12 (VTS)',
    },
    {
      id: 'kakinada',
      name: 'Kakinada Deepwater & Anchorage Port',
      state: 'Andhra Pradesh',
      distanceNm: 68.5,
      draftDepth: '14.0m',
      berthStatus: 'Available',
      coordinates: '16.9891° N, 82.2475° E',
      bearing: '215° SSW',
      vhfChannel: 'Ch 16 / Ch 14',
    },
    {
      id: 'gopalpur',
      name: 'Gopalpur Port Haven',
      state: 'Odisha',
      distanceNm: 112.0,
      draftDepth: '12.5m',
      berthStatus: 'Available',
      coordinates: '19.3000° N, 84.9667° E',
      bearing: '035° NNE',
      vhfChannel: 'Ch 16 / Ch 68',
    },
    {
      id: 'paradip',
      name: 'Paradip Port Coastal Sanctuary',
      state: 'Odisha',
      distanceNm: 198.4,
      draftDepth: '17.1m',
      berthStatus: 'High Occupancy',
      coordinates: '20.2644° N, 86.6710° E',
      bearing: '042° NE',
      vhfChannel: 'Ch 16 / Ch 09',
    },
    {
      id: 'chennai',
      name: 'Chennai Harbour Coastal Basin',
      state: 'Tamil Nadu',
      distanceNm: 310.0,
      draftDepth: '15.5m',
      berthStatus: 'Protected Harbor',
      coordinates: '13.0827° N, 80.2707° E',
      bearing: '200° SSW',
      vhfChannel: 'Ch 16 / Ch 11',
    },
  ];

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Maps</span>
          </div>
          <h1 className="page-title">
            Live Ocean Intelligence GIS Map
            <span className="page-title-badge badge-live">Live Multi-Layer</span>
          </h1>
          <p className="page-subtitle">
            Spatial marine decision layer for <strong>{selectedLocation.name}</strong> ({selectedLocation.coordinates}) integrating INCOIS PFZ, Copernicus SST/Chlorophyll, IMD Storm Track, and PostGIS 12NM/200NM Maritime Boundaries.
          </p>
        </div>
        <div className="page-header-actions">
          <Link to="/what-if" className="btn-page-action secondary">
            <span>Simulate Route</span>
          </Link>
          <Link to="/ask-oceanis" className="btn-page-action primary">
            <span>Query GIS Agent</span>
          </Link>
        </div>
      </header>

      {/* Main Workspace: 2-Column GIS Layout */}
      <div className="gis-workspace-grid">
        {/* Left / Center: Expanded Map Canvas */}
        <div className="gis-map-canvas-container">
          <LiveOceanMap />
        </div>

        {/* Right Sidebar: Safe Port Refuge Directory & Hydrographic Details */}
        <div className="gis-sidebar-panel">
          {/* Tab Switcher */}
          <div className="gis-panel-tabs">
            <button
              type="button"
              className={`gis-tab-btn ${activeTab === 'layers' ? 'active' : ''}`}
              onClick={() => setActiveTab('layers')}
            >
              Active Feeds
            </button>
            <button
              type="button"
              className={`gis-tab-btn ${activeTab === 'ports' ? 'active' : ''}`}
              onClick={() => setActiveTab('ports')}
            >
              Refuge Ports
            </button>
            <button
              type="button"
              className={`gis-tab-btn ${activeTab === 'vessels' ? 'active' : ''}`}
              onClick={() => setActiveTab('vessels')}
            >
              Vessel Traffic
            </button>
          </div>

          <div className="gis-tab-content">
            {activeTab === 'layers' && (
              <div className="gis-layers-info">
                <div className="gis-card-header">
                  <h3>Active Spatial Overlays</h3>
                  <span className="badge-count">8 Active</span>
                </div>
                <div className="layer-item-list">
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#16a34a' }} />
                    <div className="layer-info">
                      <strong>Potential Fishing Zones (PFZ)</strong>
                      <p>High chlorophyll-a bio-convergence & thermal boundaries</p>
                    </div>
                    <span className="layer-source">INCOIS</span>
                  </div>
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#0284c7' }} />
                    <div className="layer-info">
                      <strong>Sea Surface Temperature (SST)</strong>
                      <p>Sentinel-3 SLSTR calibrated thermal raster</p>
                    </div>
                    <span className="layer-source">Copernicus</span>
                  </div>
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#e11d48' }} />
                    <div className="layer-info">
                      <strong>Cyclone Storm Surge & Gale Buffer</strong>
                      <p>IMD Doppler Radar & Bay of Bengal track model</p>
                    </div>
                    <span className="layer-source">IMD</span>
                  </div>
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#9333ea' }} />
                    <div className="layer-info">
                      <strong>12 NM Territorial & 200 NM EEZ</strong>
                      <p>UNCLOS maritime limits and naval exclusion corridors</p>
                    </div>
                    <span className="layer-source">PostGIS</span>
                  </div>
                  <div className="layer-item">
                    <span className="layer-dot" style={{ background: '#d97706' }} />
                    <div className="layer-info">
                      <strong>GEBCO Bathymetry & Shoal Contours</strong>
                      <p>High-resolution depth isobaths with shallow warnings</p>
                    </div>
                    <span className="layer-source">GEBCO</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'ports' && (
              <div className="gis-ports-directory">
                <div className="gis-card-header">
                  <h3>Designated Safe Port Havens</h3>
                  <span className="badge-count">{safePorts.length} Ports</span>
                </div>
                <p className="gis-ports-subtitle">
                  Emergency shelter and harbor berths ranked by nautical distance from current position.
                </p>
                <div className="safe-ports-list">
                  {safePorts.map((port) => (
                    <div
                      key={port.id}
                      className={`port-item-card ${selectedPort === port.id ? 'selected' : ''}`}
                      onClick={() => setSelectedPort(port.id)}
                    >
                      <div className="port-header">
                        <strong className="port-name">{port.name}</strong>
                        <span className={`port-status-badge status-${port.berthStatus.toLowerCase().replace(/\s+/g, '-')}`}>
                          {port.berthStatus}
                        </span>
                      </div>
                      <div className="port-meta-grid">
                        <div className="port-metric">
                          <span className="metric-label">Distance:</span>
                          <span className="metric-val">{port.distanceNm} NM</span>
                        </div>
                        <div className="port-metric">
                          <span className="metric-label">Bearing:</span>
                          <span className="metric-val">{port.bearing}</span>
                        </div>
                        <div className="port-metric">
                          <span className="metric-label">Max Draft:</span>
                          <span className="metric-val">{port.draftDepth}</span>
                        </div>
                        <div className="port-metric">
                          <span className="metric-label">VHF Comms:</span>
                          <span className="metric-val">{port.vhfChannel}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'vessels' && (
              <div className="gis-vessel-traffic">
                <div className="gis-card-header">
                  <h3>AIS Vessel Traffic Density</h3>
                  <span className="badge-count">14 In-Range</span>
                </div>
                <div className="vessel-summary-grid">
                  <div className="vessel-stat-box">
                    <span className="stat-num">8</span>
                    <span className="stat-label">Fishing Trawlers</span>
                  </div>
                  <div className="vessel-stat-box">
                    <span className="stat-num">4</span>
                    <span className="stat-label">Cargo / Bulk</span>
                  </div>
                  <div className="vessel-stat-box">
                    <span className="stat-num">2</span>
                    <span className="stat-label">Coast Guard Patrol</span>
                  </div>
                </div>
                <div className="vessel-notices">
                  <div className="vessel-notice-card">
                    <span className="notice-icon">⚓</span>
                    <div className="notice-body">
                      <strong>ICG ICGS Samarth On Patrol</strong>
                      <p>Sector B-4 (15 NM ENE of Visakhapatnam), monitoring safety compliance on VHF Ch 16.</p>
                    </div>
                  </div>
                  <div className="vessel-notice-card warning">
                    <span className="notice-icon">⚠️</span>
                    <div className="notice-body">
                      <strong>High Trawler Density</strong>
                      <p>Kakinada Bank Shoal: 14 small craft operating in close proximity to PFZ waypoint 4.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMapPage;
