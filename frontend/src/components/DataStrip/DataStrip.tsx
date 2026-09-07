import React, { useState, useEffect } from 'react';
import './DataStrip.css';
import { checkDomainConnectivity, type DomainConnectivityStatus } from '../../services/api';

interface StatusCard {
  id: string;
  category: string;
  source: string;
  coverage: string;
  description: string;
  icon: React.ReactNode;
  domainKey: keyof Omit<DomainConnectivityStatus, 'backendOnline'>;
}

const statusCards: StatusCard[] = [
  {
    id: 'weather',
    category: 'Weather & Atmosphere',
    source: 'IMD Coastal Doppler & Global NWP',
    coverage: 'Indian Coastal Grid (Hourly)',
    description: 'Wind vectors, air temperature, barometric pressure gradients, and precipitation tracking.',
    domainKey: 'weather',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
      </svg>
    ),
  },
  {
    id: 'marine',
    category: 'Marine Conditions',
    source: 'INCOIS Wave Buoy & Hydrodynamic Models',
    coverage: 'Bay of Bengal & Arabian Sea',
    description: 'Significant wave heights, swell direction, peak wave periods, and surface sea state currents.',
    domainKey: 'marineConditions',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    id: 'eo',
    category: 'Earth Observation',
    source: 'Copernicus Sentinel-3 & MODIS-Aqua',
    coverage: 'Orbital Multispectral Imagery',
    description: 'Chlorophyll-a density concentration, thermal sea surface fronts, and water bio-optics.',
    domainKey: 'earthObservation',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 3v18M3 12h18" />
      </svg>
    ),
  },
  {
    id: 'safety',
    category: 'Safety & Disaster Alerts',
    source: 'IMD & JTWC Cyclone Advisories',
    coverage: 'Active Maritime Hazards',
    description: 'Tropical cyclone trajectories, gale storm surges, naval exclusion zones, and safe harbors.',
    domainKey: 'safetyAlerts',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
  {
    id: 'geospatial',
    category: 'Geospatial & Navigation',
    source: 'PostGIS 3.5 Spatial Engine & GEBCO',
    coverage: 'Indian EEZ & Coastal Harbors',
    description: 'Spatial bathymetry depth contours, navigation channels, port refuges, and distance computation.',
    domainKey: 'geospatialData',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
      </svg>
    ),
  },
];

export const DataStrip: React.FC = () => {
  const [connectivity, setConnectivity] = useState<DomainConnectivityStatus>({
    weather: false,
    marineConditions: false,
    earthObservation: false,
    safetyAlerts: false,
    geospatialData: false,
    backendOnline: false,
  });
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchStatus = async () => {
      try {
        const result = await checkDomainConnectivity();
        if (isMounted) {
          setConnectivity(result);
          setIsChecking(false);
        }
      } catch {
        if (isMounted) {
          setIsChecking(false);
        }
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <section id="live-status" className="datastrip-section">
      <div className="container">
        <div className="datastrip-panel glass-panel">
          {/* Section Header */}
          <div className="datastrip-header">
            <div className="datastrip-lead">
              <span className="section-tag">DATA INGESTION & SENSOR PIPELINE</span>
              <h2 className="datastrip-title">Marine Intelligence Status</h2>
              <p className="datastrip-desc">
                Multi-source ocean telemetry and satellite feeds powering the OCEANIS decision engine.
              </p>
            </div>
            
            <div className="datastrip-system-pill">
              <span className={`live-dot ${connectivity.backendOnline ? 'pulse' : 'awaiting'}`}></span>
              <span className="system-pill-text">
                {isChecking
                  ? 'CHECKING TELEMETRY...'
                  : connectivity.backendOnline
                  ? 'BACKEND CONNECTED • 28/28 APIS ONLINE'
                  : 'AWAITING LIVE CONNECTION'}
              </span>
            </div>
          </div>

          {/* 5 Domain Status Cards */}
          <div className="datastrip-grid">
            {statusCards.map((card) => {
              const isConnected = connectivity[card.domainKey];
              return (
                <div key={card.id} className={`datastrip-card ${isConnected ? 'connected' : 'awaiting'}`}>
                  <div className="datastrip-card-top">
                    <div className="datastrip-icon">{card.icon}</div>
                    <span className={`status-tag ${isConnected ? 'status-connected' : 'status-awaiting'}`}>
                      <span className={`status-indicator-dot ${isConnected ? 'pulse' : ''}`}></span>
                      {isConnected ? 'Connected' : 'Awaiting connection'}
                    </span>
                  </div>

                  <div className="datastrip-card-body">
                    <h3 className="datastrip-category">{card.category}</h3>
                    <div className="datastrip-source-tag">{card.source}</div>
                    <p className="datastrip-detail">{card.description}</p>
                    <div className="datastrip-coverage">
                      <span className="coverage-label">Coverage:</span> {card.coverage}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};
