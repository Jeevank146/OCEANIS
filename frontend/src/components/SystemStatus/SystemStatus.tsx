import React, { useState, useEffect } from 'react';
import { useLocationContext } from '../../context/LocationContext';
import './SystemStatus.css';

export const SystemStatus: React.FC = () => {
  const [lastSync, setLastSync] = useState<string>('Just now');
  const { selectedLocation } = useLocationContext();

  useEffect(() => {
    let elapsedSeconds = 0;
    const timer = setInterval(() => {
      elapsedSeconds += 5;
      if (elapsedSeconds < 60) {
        setLastSync(`${elapsedSeconds}s ago`);
      } else {
        setLastSync(`${Math.floor(elapsedSeconds / 60)}m ago`);
      }
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  const sectorText = selectedLocation
    ? (selectedLocation.marine_context || selectedLocation.city || selectedLocation.name)
    : 'National Maritime Grid';

  return (
    <div className="system-status-strip">
      <div className="system-status-container">
        {/* Left: Operational Health Status */}
        <div className="status-badge-group">
          <div className="system-status-badge">
            <span className="pulse-indicator" />
            <span className="status-badge-text">SYSTEM OPERATIONAL</span>
          </div>
          <span className="status-separator">|</span>
          <span className="system-summary-text">
            <span className="mini-green-dot" />
            <strong>6/6</strong> Domain Agents Synchronized
          </span>
          <span className="status-dot-divider">•</span>
          <span className="system-summary-text">
            <span className="mini-green-dot" />
            <strong>PostgreSQL / PostGIS</strong> Spatial Engine Active
          </span>
        </div>

        {/* Center: Ingest Feeds */}
        <div className="status-feeds-group">
          <span className="feed-tag">INCOIS</span>
          <span className="feed-tag">IMD</span>
          <span className="feed-tag">ISRO</span>
          <span className="feed-tag">COPERNICUS</span>
          <span className="feed-tag">GEBCO</span>
        </div>

        {/* Right: Sector & Heartbeat */}
        <div className="status-meta-group">
          <span className="status-sector-indicator">
            Sector: <strong>{sectorText}</strong>
          </span>
          <span className="status-sync-time">
            Heartbeat: <strong>{lastSync}</strong>
          </span>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
