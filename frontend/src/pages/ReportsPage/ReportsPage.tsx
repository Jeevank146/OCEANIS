import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './ReportsPage.css';

export const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState<string>('pfz-briefing');
  const [sector, setSector] = useState<string>('Visakhapatnam');
  const [includeProvenance, setIncludeProvenance] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);

  const handleGenerateReport = (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setDownloadSuccess(false);

    setTimeout(() => {
      setIsGenerating(false);
      setDownloadSuccess(true);
    }, 800);
  };

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">Home</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">Reports</span>
          </div>
          <h1 className="page-title">
            Structured Marine Intelligence Report Generator
            <span className="page-title-badge badge-official">Official Format</span>
          </h1>
          <p className="page-subtitle">
            Generate printable operational dossiers, fishing advisories, passage briefings, and multi-agency provenance audits.
          </p>
        </div>
        <div className="page-header-actions">
          <Link to="/analytics" className="btn-page-action secondary">
            <span>View KPIs</span>
          </Link>
          <Link to="/ask-oceanis" className="btn-page-action primary">
            <span>Query Assistant</span>
          </Link>
        </div>
      </header>

      {/* Main Grid */}
      <div className="reports-layout-grid">
        {/* Left Column: Report Configuration Form */}
        <div className="reports-left-col">
          <div className="ocean-card report-config-card">
            <div className="card-top-header">
              <h3>Report Parameters & Configuration</h3>
              <span className="badge-tool">Export Engine</span>
            </div>

            <form onSubmit={handleGenerateReport} className="report-form">
              <div className="form-field">
                <label>Report Template</label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="report-select"
                >
                  <option value="pfz-briefing">Daily Fishery & PFZ Advisory Briefing</option>
                  <option value="hydrographic-bulletin">Coastal Hydrographic & Sea State Bulletin</option>
                  <option value="passage-clearance">Pre-Voyage Passage Clearance & Safety Dossier</option>
                  <option value="cyclone-log">Cyclone & Severe Weather Incident Log</option>
                </select>
              </div>

              <div className="form-field">
                <label>Target Coastal Sector</label>
                <select
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  className="report-select"
                >
                  <option value="Visakhapatnam">Visakhapatnam & North Andhra Coast</option>
                  <option value="Kakinada">Kakinada Spit & Godavari Estuary</option>
                  <option value="Gopalpur">Gopalpur & South Odisha Coast</option>
                  <option value="Paradip">Paradip Roadstead Sector</option>
                  <option value="Chennai">Chennai & Coromandel Coast</option>
                </select>
              </div>

              <div className="form-field checkbox-field">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={includeProvenance}
                    onChange={(e) => setIncludeProvenance(e.target.checked)}
                  />
                  <span>Include cryptographic institutional provenance hashes (INCOIS, IMD, ISRO)</span>
                </label>
              </div>

              <button
                type="submit"
                className="btn-generate-report"
                disabled={isGenerating}
              >
                {isGenerating ? 'Compiling Multi-Agent Dossier...' : 'Generate & Download PDF Report'}
              </button>

              {downloadSuccess && (
                <div className="report-success-box">
                  <span>✓ Report compiled successfully. Ready for maritime dispatch.</span>
                </div>
              )}
            </form>
          </div>
        </div>

        {/* Right Column: Live Dossier Preview */}
        <div className="reports-right-col">
          <div className="ocean-card report-preview-card">
            <div className="card-top-header">
              <h3>Live Document Preview</h3>
              <span className="badge-provenance">CONFIDENTIAL MARITIME BRIEF</span>
            </div>

            <div className="dossier-paper">
              <div className="dossier-header">
                <div className="dossier-brand">
                  <strong>OCEANIS MARINE INTELLIGENCE SYSTEM</strong>
                  <span>Government of India Marine Operations Protocol</span>
                </div>
                <div className="dossier-meta">
                  <span>Date: <strong>06-SEP-2026</strong></span>
                  <span>Ref: <strong>OCN-RPT-8422</strong></span>
                </div>
              </div>

              <hr className="dossier-rule" />

              <h4 className="dossier-title">
                {reportType === 'pfz-briefing' && 'DAILY FISHERY & POTENTIAL FISHING ZONE BRIEFING'}
                {reportType === 'hydrographic-bulletin' && 'COASTAL HYDROGRAPHIC & SEA STATE BULLETIN'}
                {reportType === 'passage-clearance' && 'PRE-VOYAGE PASSAGE CLEARANCE & SAFETY DOSSIER'}
                {reportType === 'cyclone-log' && 'CYCLONE & SEVERE WEATHER INCIDENT LOG'}
              </h4>

              <div className="dossier-section">
                <strong>1. OPERATIONAL SECTOR</strong>
                <p>Location: {sector} • Maritime Zone: 0 - 25 NM Coastal & Shelf Basin</p>
              </div>

              <div className="dossier-section">
                <strong>2. CONSENSUS SAFETY ASSESSMENT</strong>
                <p>Status: <span className="text-success">CLEAR / MODERATE VIGILANCE</span> • Significant Wave Height: 1.4m • Wind: 14 kts ESE</p>
              </div>

              <div className="dossier-section">
                <strong>3. TARGET WAYPOINTS & HYDRODYNAMICS</strong>
                <p>PFZ-82 (17.68°N, 83.42°E): Chlorophyll-a: 0.84 mg/m³ • SST Front: 28.2°C • Distance: 14.5 NM</p>
              </div>

              {includeProvenance && (
                <div className="dossier-section provenance">
                  <strong>4. INSTITUTIONAL DATA PROVENANCE AUDIT</strong>
                  <p>• INCOIS Moored Buoy BD08 (Sync: 17:15 IST) • IMD Doppler Radar Machilipatnam • Copernicus Sentinel-3 OLCI (Pass: 09:42 UTC)</p>
                </div>
              )}

              <div className="dossier-footer">
                <span>Certified by OCEANIS Multi-Agent Orchestrator v2.4</span>
                <span>Page 1 of 1</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
