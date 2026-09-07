import React, { useState, useEffect } from 'react';
import './SystemStatus.css';

export const SystemStatus: React.FC = () => {
  const [lastSync, setLastSync] = useState<string>('Just now');

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
            <strong>6/6</strong> Agents Online
          </span>
          <span className="status-dot-divider">•</span>
          <span className="system-summary-text">
            <span className="mini-green-dot" />
            <strong>28/28</strong> APIs Online
          </span>
          <span className="status-dot-divider">•</span>
          <span className="system-summary-text">
            <span className="mini-green-dot" />
            <strong>PostgreSQL / PostGIS</strong> Connected
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

        {/* Right: Latency & Heartbeat */}
        <div className="status-meta-group">
          <span className="status-sector-indicator">
            Sector: <strong>Bay of Bengal (Vizag)</strong>
          </span>
          <span className="status-sync-time">
            Last Sync: <strong>{lastSync}</strong>
          </span>
        </div>
      </div>
    </div>
  );
};
