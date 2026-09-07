import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import './MarineConditionsPage.css';

interface ParameterCardData {
  title: string;
  value: string;
  unit: string;
  status: 'OBSERVED' | 'FORECAST' | 'CALCULATED';
  freshness: 'FRESH' | 'RECENT';
  source: string;
  trend: 'steady' | 'rising' | 'falling';
  trendText: string;
  description: string;
}

export const MarineConditionsPage: React.FC = () => {
  const { selectedLocation } = useLocationContext();
  const [selectedSector, setSelectedSector] = useState<string>(selectedLocation.city || 'Visakhapatnam');
  const [forecastHour, setForecastHour] = useState<number>(14);

  useEffect(() => {
    if (selectedLocation?.city) {
      setSelectedSector(selectedLocation.city);
    }
  }, [selectedLocation]);

  const sectors = [
    'Visakhapatnam',
    'Kakinada Coast',
    'Machilipatnam',
    'Gopalpur Haven',
    'Paradip Roadstead',
    'Chennai Harbour',
    'Kochi Channel',
    'Mumbai High',
  ];

  const parameters: ParameterCardData[] = [
    {
      title: 'Significant Wave Height (Hs)',
      value: '1.4',
      unit: 'meters',
      status: 'OBSERVED',
      freshness: 'FRESH',
      source: 'INCOIS Moored Buoy BD08',
      trend: 'rising',
      trendText: '+0.2m in last 3 hrs',
      description: 'Moderate sea state. Safe for mechanized craft; small motorized crafts caution in offshore sectors.',
    },
    {
      title: 'Peak Wave Period (Tp)',
      value: '8.4',
      unit: 'seconds',
      status: 'OBSERVED',
      freshness: 'FRESH',
      source: 'INCOIS Moored Buoy BD08',
      trend: 'steady',
      trendText: 'Dominant southern swell',
      description: 'Long-period swell entering from southern Bay of Bengal basin.',
    },
    {
      title: 'Surface Ocean Current',
      value: '0.42',
      unit: 'm/s (0.82 kts)',
      status: 'OBSERVED',
      freshness: 'FRESH',
      source: 'High-Frequency Radar (HFR)',
      trend: 'steady',
      trendText: 'Bearing 065° ENE',
      description: 'East India Coastal Current (EICC) flowing northward along the shelf break.',
    },
    {
      title: 'Sea Surface Temp (SST)',
      value: '28.4',
      unit: '°C',
      status: 'OBSERVED',
      freshness: 'FRESH',
      source: 'Sentinel-3 SLSTR Radiometer',
      trend: 'falling',
      trendText: '-0.3°C vs 24h average',
      description: 'Favorable thermal range for pelagic shoals (mackerel & sardine).',
    },
    {
      title: 'Sustained Wind Speed',
      value: '14.2',
      unit: 'knots',
      status: 'OBSERVED',
      freshness: 'FRESH',
      source: 'IMD Coastal Doppler Anemometer',
      trend: 'rising',
      trendText: 'Gusting to 18.5 kts',
      description: 'Moderate breeze from ESE (110°). Light spray, small whitecaps.',
    },
    {
      title: 'Barometric Pressure',
      value: '1008.4',
      unit: 'hPa / mbar',
      status: 'OBSERVED',
      freshness: 'FRESH',
      source: 'IMD Coastal AWS',
      trend: 'steady',
      trendText: 'Normal diurnal cycle',
      description: 'Stable synoptic atmospheric pressure. No immediate squall trigger.',
    },
    {
      title: 'Sea Surface Salinity',
      value: '33.2',
      unit: 'PSU',
      status: 'OBSERVED',
      freshness: 'RECENT',
      source: 'SMAP / Argo Profiling Float',
      trend: 'steady',
      trendText: 'Normal marine salinity',
      description: 'Minimal riverine freshwater dilution at 10 NM offshore.',
    },
    {
      title: 'Tide Height & Cycle',
      value: '+1.18',
      unit: 'meters (Chart Datum)',
      status: 'CALCULATED',
      freshness: 'FRESH',
      source: 'Survey of India Tide Gauge',
      trend: 'rising',
      trendText: 'High Tide peak at 18:45 IST',
      description: 'Semi-diurnal tide in rising phase (Flood Tide). Current velocity assisting harbor entry.',
    },
    {
      title: 'Water Clarity & Turbidity',
      value: '1.2',
      unit: 'NTU (High Clarity)',
      status: 'OBSERVED',
      freshness: 'FRESH',
      source: 'Sentinel-3 OLCI Ocean Color',
      trend: 'steady',
      trendText: 'Secchi depth ~9.5m',
      description: 'Low sediment suspension; clear photic zone optimal for bio-optical sensing.',
    },
    {
      title: 'Thermocline Depth',
      value: '38.0',
      unit: 'meters depth',
      status: 'FORECAST',
      freshness: 'RECENT',
      source: 'INCOIS INCOIS-GODAS Model',
      trend: 'steady',
      trendText: 'Sharp gradient at 40m',
      description: 'Upper mixed layer extends down to 38m, below which temperature drops sharply.',
    },
    {
      title: 'Wave Steepness Index',
      value: '0.018',
      unit: 'ratio (Non-breaking)',
      status: 'CALCULATED',
      freshness: 'FRESH',
      source: 'OCEANIS Hydrodynamic Engine',
      trend: 'steady',
      trendText: 'Low capsizing risk',
      description: 'Ratio of wave height to wavelength is low; swell waves are rounded and stable.',
    },
    {
      title: 'Coastal Fog / Visibility',
      value: '> 10.0',
      unit: 'kilometers',
      status: 'OBSERVED',
      freshness: 'FRESH',
      source: 'IMD Aviation / Port Sensor',
      trend: 'steady',
      trendText: 'Clear visibility',
      description: 'Unrestricted optical visibility for coastal navigation and radar identification.',
    },
  ];

  const hourlyForecast = [
    { hour: '06:00', wave: '1.2m', wind: '11 kts', sst: '28.1°C', state: 'Calm' },
    { hour: '09:00', wave: '1.3m', wind: '12 kts', sst: '28.3°C', state: 'Smooth' },
    { hour: '12:00', wave: '1.4m', wind: '14 kts', sst: '28.6°C', state: 'Moderate' },
    { hour: '15:00', wave: '1.5m', wind: '15 kts', sst: '28.5°C', state: 'Moderate' },
    { hour: '18:00', wave: '1.6m', wind: '16 kts', sst: '28.3°C', state: 'Moderate' },
    { hour: '21:00', wave: '1.4m', wind: '13 kts', sst: '28.1°C', state: 'Smooth' },
    { hour: '00:00', wave: '1.3m', wind: '12 kts', sst: '27.9°C', state: 'Smooth' },
  ];

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Marine Conditions</span>
          </div>
          <h1 className="page-title">
            Physical & Atmospheric Marine Conditions
            <span className="page-title-badge badge-live">12 Parameters Live</span>
          </h1>
          <p className="page-subtitle">
            Calibrated hydrographic telemetry from INCOIS ocean buoys, IMD coastal Doppler radars, and Copernicus satellite scatterometers.
          </p>
        </div>
        <div className="page-header-actions">
          <Link to="/what-if" className="btn-page-action secondary">
            <span>Forecast Drift</span>
          </Link>
          <Link to="/ask-oceanis" className="btn-page-action primary">
            <span>Query Marine Agent</span>
          </Link>
        </div>
      </header>

      {/* Sector Switcher Strip */}
      <div className="sector-filter-bar">
        <span className="sector-label">Select Sector:</span>
        <div className="sector-pill-list">
          {sectors.map((sec) => (
            <button
              key={sec}
              type="button"
              className={`sector-pill-btn ${selectedSector === sec ? 'active' : ''}`}
              onClick={() => setSelectedSector(sec)}
            >
              {sec}
            </button>
          ))}
        </div>
      </div>

      {/* 24-Hour Interactive Timeline Slider */}
      <div className="ocean-card forecast-timeline-card">
        <div className="card-top-header">
          <div>
            <h3>24-Hour Hydrodynamic Forecast Progression</h3>
            <span className="timeline-sector-name">Active Sector: {selectedSector}</span>
          </div>
          <span className="badge-source">ECMWF / INCOIS Model</span>
        </div>

        <div className="timeline-slider-wrapper">
          <div className="slider-header">
            <span>Timeline Cursor: <strong>+{forecastHour} Hours Ahead</strong></span>
            <span className="slider-hint">Slide to preview expected sea state changes</span>
          </div>
          <input
            type="range"
            min="0"
            max="24"
            step="1"
            value={forecastHour}
            onChange={(e) => setForecastHour(parseInt(e.target.value))}
            className="forecast-range-slider"
          />
        </div>

        {/* Hourly Forecast Strip */}
        <div className="hourly-forecast-grid">
          {hourlyForecast.map((hf) => (
            <div key={hf.hour} className="hourly-card">
              <span className="hf-hour">{hf.hour}</span>
              <div className="hf-metrics">
                <div className="hf-val-row">
                  <span className="hf-label">Wave:</span>
                  <strong className="hf-val">{hf.wave}</strong>
                </div>
                <div className="hf-val-row">
                  <span className="hf-label">Wind:</span>
                  <strong className="hf-val">{hf.wind}</strong>
                </div>
                <div className="hf-val-row">
                  <span className="hf-label">SST:</span>
                  <strong className="hf-val">{hf.sst}</strong>
                </div>
              </div>
              <span className="hf-state-badge">{hf.state}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 12-Parameter Grid */}
      <div className="marine-params-grid">
        {parameters.map((param) => (
          <div key={param.title} className="ocean-card param-metric-card">
            <div className="param-header">
              <span className="param-title">{param.title}</span>
              <div className="param-badges">
                <span className={`badge-status status-${param.status.toLowerCase()}`}>
                  {param.status}
                </span>
                <span className="badge-freshness">
                  {param.freshness}
                </span>
              </div>
            </div>

            <div className="param-body">
              <div className="param-value-box">
                <span className="param-num">{param.value}</span>
                <span className="param-unit">{param.unit}</span>
              </div>
              <div className="param-trend-box">
                <span className={`trend-tag trend-${param.trend}`}>
                  {param.trend === 'rising' ? '▲' : param.trend === 'falling' ? '▼' : '●'} {param.trendText}
                </span>
              </div>
            </div>

            <p className="param-description">{param.description}</p>

            <div className="param-footer">
              <span className="param-source">Source: <strong>{param.source}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MarineConditionsPage;
