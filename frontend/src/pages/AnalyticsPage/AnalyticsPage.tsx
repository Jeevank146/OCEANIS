import React from 'react';
import { Link } from 'react-router-dom';
import './AnalyticsPage.css';

export const AnalyticsPage: React.FC = () => {

  const intentStats = [
    { name: 'Fishing Suitability & PFZ', pct: 38, count: '14,820', color: '#16A34A' },
    { name: 'Marine Conditions & Wave Height', pct: 24, count: '9,360', color: '#0284C7' },
    { name: 'Disaster, Cyclone & Safety', pct: 18, count: '7,020', color: '#DC2626' },
    { name: 'Geo-Spatial & Boundary Clearance', pct: 12, count: '4,680', color: '#9333EA' },
    { name: 'Marine Operations & Voyage ETA', pct: 8, count: '3,120', color: '#D97706' },
  ];

  const decisionsStats = [
    { label: 'CLEAR (Safe to Venture)', pct: 68, color: '#16A34A' },
    { label: 'CAUTION (Heightened Vigilance)', pct: 26, color: '#D97706' },
    { label: 'PROHIBITED (Dangerous Sea State)', pct: 6, color: '#DC2626' },
  ];

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Analytics</span>
          </div>
          <h1 className="page-title">
            Marine Analytics & Telemetry Performance
            <span className="page-title-badge badge-live">Live Operational KPIs</span>
          </h1>
          <p className="page-subtitle">
            Real-time query volume, multi-agent dispatch statistics, safety decision distribution, and latency benchmarks.
          </p>
        </div>
        <div className="page-header-actions">
          <Link to="/reports" className="btn-page-action secondary">
            <span>Export Analytics</span>
          </Link>
          <Link to="/ask-oceanis" className="btn-page-action primary">
            <span>Query Assistant</span>
          </Link>
        </div>
      </header>

      {/* Top Stat KPI Cards */}
      <div className="analytics-kpi-grid">
        <div className="ocean-card kpi-card">
          <span className="kpi-label">24h Queries Processed</span>
          <strong className="kpi-val">39,000+</strong>
          <span className="kpi-sub text-success">▲ +14% vs yesterday</span>
        </div>

        <div className="ocean-card kpi-card">
          <span className="kpi-label">Mean Multi-Agent Latency</span>
          <strong className="kpi-val">142 ms</strong>
          <span className="kpi-sub text-success">p95 &lt; 280 ms</span>
        </div>

        <div className="ocean-card kpi-card">
          <span className="kpi-label">Daily Spatial Ingests</span>
          <strong className="kpi-val">1.42 M</strong>
          <span className="kpi-sub">Points across 6 sources</span>
        </div>

        <div className="ocean-card kpi-card">
          <span className="kpi-label">Safety Guardrail Adherence</span>
          <strong className="kpi-val">100.0%</strong>
          <span className="kpi-sub text-success">0 Unenforced Overrides</span>
        </div>
      </div>

      {/* Analytics Main Breakdown Grid */}
      <div className="analytics-charts-grid">
        {/* Intent Distribution Card */}
        <div className="ocean-card analytics-chart-card">
          <div className="card-top-header">
            <h3>Query Intent Classification Distribution</h3>
            <span className="badge-source">NLP Intent Router</span>
          </div>
          <div className="bar-breakdown-list">
            {intentStats.map((item) => (
              <div key={item.name} className="chart-bar-item">
                <div className="chart-bar-labels">
                  <span className="bar-name">{item.name}</span>
                  <strong className="bar-val">{item.pct}% ({item.count})</strong>
                </div>
                <div className="chart-bar-track">
                  <div
                    className="chart-bar-fill"
                    style={{ width: `${item.pct}%`, background: item.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Safety Decision Distribution Card */}
        <div className="ocean-card analytics-chart-card">
          <div className="card-top-header">
            <h3>Consensus Safety Decision Distribution</h3>
            <span className="badge-provenance">Guardrail Engine</span>
          </div>
          <div className="decisions-breakdown-list">
            {decisionsStats.map((item) => (
              <div key={item.label} className="decision-bar-item">
                <div className="chart-bar-labels">
                  <span className="bar-name">{item.label}</span>
                  <strong className="bar-val">{item.pct}%</strong>
                </div>
                <div className="chart-bar-track">
                  <div
                    className="chart-bar-fill"
                    style={{ width: `${item.pct}%`, background: item.color }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="language-dist-box">
            <span className="lang-dist-title">Language Ingest Distribution:</span>
            <div className="lang-pills-row">
              <span className="lang-pill">English: <strong>52%</strong></span>
              <span className="lang-pill">Telugu (తెలుగు): <strong>31%</strong></span>
              <span className="lang-pill">Hindi (हिन्दी): <strong>11%</strong></span>
              <span className="lang-pill">Tamil (தமிழ்): <strong>6%</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
