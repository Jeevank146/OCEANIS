import React, { useState, useEffect } from 'react';
import './LiveMarineOverview.css';
import { fetchLiveMarineConditions, type MarineConditionData } from '../../services/api';

interface LiveMarineOverviewProps {
  location: string;
  lat?: number;
  lon?: number;
}

export const LiveMarineOverview: React.FC<LiveMarineOverviewProps> = ({ location, lat, lon }) => {
  const [data, setData] = useState<MarineConditionData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

    fetchLiveMarineConditions(location, lat, lon).then((res) => {
      if (isMounted) {
        setData(res);
        setIsLoading(false);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [location, lat, lon]);

  if (!data && isLoading) {
    return (
      <div className="marine-overview-card ocean-card">
        <div className="overview-loading-skeleton">
          <span className="overview-spinner"></span>
          <span>Loading telemetry for {location}...</span>
        </div>
      </div>
    );
  }

  const d = data!;

  return (
    <div id="live-overview" className="marine-overview-card ocean-card">
      {/* Header */}
      <div className="card-header-row">
        <div className="card-header-left">
          <h2 className="card-main-title">🌊 Live Marine Conditions</h2>
          <p className="card-subtitle">
            Latest observations from official sources for <strong>{location.split(',')[0]}</strong>
          </p>
        </div>
        <div className="live-pill-tag">
          <span className="live-dot pulse"></span>
          <span>{d.freshness || 'REAL-TIME'}</span>
        </div>
      </div>

      {/* If location is inland or unavailable */}
      {d.isInland && (
        <div className="inland-alert-banner">
          <span>{d.message || '⚠️ No seashore or marine area found at this location.'}</span>
        </div>
      )}

      {/* 6 Compact Metric Cards */}
      <div className="metric-cards-grid">
        {/* 1. Sea State */}
        <div className="metric-box">
          <div className="metric-box-top">
            <div className="metric-icon-box bg-blue-tint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </div>
            <span className="metric-label">Sea State</span>
          </div>
          <div className="metric-value-row">
            <span className="metric-value-text">{d.seaState}</span>
          </div>
          <span className="metric-support-info">Hydrodynamic limit: {d.isInland ? 'Inland' : 'Normal'}</span>
          <div className="metric-footer-row">
            <span className="metric-source">{d.source ? d.source.split('•')[0] : 'Ocean Model'}</span>
            <span className="metric-time">{d.timestamp}</span>
          </div>
        </div>

        {/* 2. Significant Wave Height */}
        <div className="metric-box">
          <div className="metric-box-top">
            <div className="metric-icon-box bg-cyan-tint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
                <path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
              </svg>
            </div>
            <span className="metric-label">Wave Height</span>
          </div>
          <div className="metric-value-row">
            <span className="metric-value-text">{d.isInland ? 'N/A' : d.waveHeight.toFixed(1)}</span>
            {!d.isInland && <span className="metric-unit-text">{d.waveHeightUnit}</span>}
          </div>
          <span className="metric-support-info">{d.isInland ? 'Inland territory' : 'Significant Height (Hs)'}</span>
          <div className="metric-footer-row">
            <span className="metric-source">Wave Telemetry</span>
            <span className="metric-time">{d.timestamp}</span>
          </div>
        </div>

        {/* 3. Wind Speed */}
        <div className="metric-box">
          <div className="metric-box-top">
            <div className="metric-icon-box bg-teal-tint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
              </svg>
            </div>
            <span className="metric-label">Wind Speed</span>
          </div>
          <div className="metric-value-row">
            <span className="metric-value-text">{d.windSpeed.toFixed(0)}</span>
            <span className="metric-unit-text">{d.windUnit}</span>
          </div>
          <span className="metric-support-info">Direction: {d.windDirection}</span>
          <div className="metric-footer-row">
            <span className="metric-source">Coastal Radar</span>
            <span className="metric-time">{d.timestamp}</span>
          </div>
        </div>

        {/* 4. Sea Surface Temperature */}
        <div className="metric-box">
          <div className="metric-box-top">
            <div className="metric-icon-box bg-amber-tint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
              </svg>
            </div>
            <span className="metric-label">Sea Surface Temp</span>
          </div>
          <div className="metric-value-row">
            <span className="metric-value-text">{d.isInland ? 'N/A' : d.sst.toFixed(1)}</span>
            {!d.isInland && <span className="metric-unit-text">{d.sstUnit}</span>}
          </div>
          <span className="metric-support-info">{d.isInland ? 'Inland region' : 'Thermal Sensor'}</span>
          <div className="metric-footer-row">
            <span className="metric-source">Sentinel-3 SLSTR</span>
            <span className="metric-time">{d.timestamp}</span>
          </div>
        </div>

        {/* 5. Surface Ocean Current */}
        <div className="metric-box">
          <div className="metric-box-top">
            <div className="metric-icon-box bg-sky-tint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
            </div>
            <span className="metric-label">Ocean Current</span>
          </div>
          <div className="metric-value-row">
            <span className="metric-value-text">{d.isInland ? 'N/A' : d.currentSpeed.toFixed(1)}</span>
            {!d.isInland && <span className="metric-unit-text">{d.currentUnit}</span>}
          </div>
          <span className="metric-support-info">{d.isInland ? 'No ocean flow' : `Vector: ${d.currentDirection}`}</span>
          <div className="metric-footer-row">
            <span className="metric-source">HYCOM Array</span>
            <span className="metric-time">{d.timestamp}</span>
          </div>
        </div>

        {/* 6. Visibility */}
        <div className="metric-box">
          <div className="metric-box-top">
            <div className="metric-icon-box bg-purple-tint">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </div>
            <span className="metric-label">Visibility</span>
          </div>
          <div className="metric-value-row">
            <span className="metric-value-text">{d.visibility.toFixed(1)}</span>
            <span className="metric-unit-text">{d.visibilityUnit}</span>
          </div>
          <span className="metric-support-info">Clarity: Optimal</span>
          <div className="metric-footer-row">
            <span className="metric-source">Station Sensor</span>
            <span className="metric-time">{d.timestamp}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
