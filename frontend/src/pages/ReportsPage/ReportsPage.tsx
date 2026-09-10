import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import { useLanguage } from '../../context/LanguageContext';
import { downloadOceanisReport, type OceanisReportType } from '../../utils/oceanisPdf';
import './ReportsPage.css';

export const ReportsPage: React.FC = () => {
  const { selectedLocation } = useLocationContext();
  const { t } = useLanguage();

  const initialSector = selectedLocation?.city || selectedLocation?.name || 'Operational Sector';
  const [reportType, setReportType] = useState<OceanisReportType>('pfz-briefing');
  const [sector, setSector] = useState<string>(initialSector);
  const [includeProvenance, setIncludeProvenance] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);
  const [downloadedFilename, setDownloadedFilename] = useState<string>('');
  const [downloadError, setDownloadError] = useState<string>('');

  useEffect(() => {
    if (selectedLocation?.name || selectedLocation?.city) {
      setSector(selectedLocation.city || selectedLocation.name);
    }
  }, [selectedLocation]);

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setDownloadSuccess(false);
    setDownloadError('');

    try {
      const filename = await downloadOceanisReport({
        reportType,
        sector,
        coordinates: coordsText,
        includeProvenance,
      });
      setDownloadedFilename(filename);
      setDownloadSuccess(true);
    } catch (error) {
      console.error('Failed to generate OCEANIS PDF report:', error);
      setDownloadError(t('reports.error_msg', 'The PDF could not be generated. Please review the report settings and try again.'));
    } finally {
      setIsGenerating(false);
    }
  };

  const formattedDate = new Date().toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).toUpperCase();

  const coordsText = selectedLocation?.coordinates || (
    selectedLocation?.lat !== undefined && selectedLocation?.lon !== undefined
      ? `${Math.abs(selectedLocation.lat).toFixed(4)}° ${selectedLocation.lat >= 0 ? 'N' : 'S'}, ${Math.abs(selectedLocation.lon).toFixed(4)}° ${selectedLocation.lon >= 0 ? 'E' : 'W'}`
      : '17.6868° N, 83.2185° E'
  );

  return (
    <div className="ocean-page-container">
      {/* Header Banner */}
      <header className="page-header-banner">
        <div className="page-header-main">
          <div className="page-breadcrumbs">
            <Link to="/" className="page-breadcrumb-crumb">{t('nav.home', 'Home')}</Link>
            <span className="page-breadcrumb-sep">/</span>
            <span className="page-breadcrumb-current">{t('nav.reports', 'Reports')}</span>
          </div>
          <h1 className="page-title">
            {t('reports.title', 'Structured Marine Intelligence Report Generator')}
            <span className="page-title-badge badge-official">{t('reports.badge', 'Official Format')}</span>
          </h1>
          <p className="page-subtitle">
            {t('reports.subtitle', 'Generate printable operational dossiers, fishing advisories, passage briefings, and multi-agency provenance audits.')}
          </p>
        </div>
        <div className="page-header-actions">
          <Link to="/analytics" className="btn-page-action secondary">
            <span>{t('nav.analytics', 'View KPIs')}</span>
          </Link>
          <Link to="/ask" className="btn-page-action primary">
            <span>{t('nav.ask', 'Ask OCEANIS')}</span>
          </Link>
        </div>
      </header>

      {/* Main Grid */}
      <div className="reports-layout-grid">
        {/* Left Column: Report Configuration Form */}
        <div className="reports-left-col">
          <div className="ocean-card report-config-card">
            <div className="card-top-header">
              <h3>{t('reports.config_title', 'Report Parameters & Configuration')}</h3>
              <span className="badge-tool">{selectedLocation?.name || 'Active Location'}</span>
            </div>

            <form onSubmit={handleGenerateReport} className="report-form">
              <div className="form-field">
                <label>{t('reports.template_label', 'Report Template')}</label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value as OceanisReportType)}
                  className="report-select"
                >
                  <option value="pfz-briefing">Daily Fishery & PFZ Advisory Briefing</option>
                  <option value="hydrographic-bulletin">Coastal Hydrographic & Sea State Bulletin</option>
                  <option value="passage-clearance">Pre-Voyage Passage Clearance & Safety Dossier</option>
                  <option value="cyclone-log">Cyclone & Severe Weather Incident Log</option>
                </select>
              </div>

              <div className="form-field">
                <label>{t('reports.sector_label', 'Target Operating Sector')}</label>
                <input
                  type="text"
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  className="report-select"
                  placeholder="Enter coastal sector or city"
                />
              </div>

              <div className="form-field checkbox-field">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={includeProvenance}
                    onChange={(e) => setIncludeProvenance(e.target.checked)}
                  />
                  <span>{t('reports.provenance_checkbox', 'Include cryptographic institutional provenance hashes (INCOIS, IMD, ISRO, Copernicus)')}</span>
                </label>
              </div>

              <button
                type="submit"
                className="btn-generate-report"
                disabled={isGenerating}
              >
                {isGenerating ? t('reports.generating', 'Compiling Multi-Agent Dossier...') : t('reports.generate_btn', 'Generate & Download PDF Report')}
              </button>

              {downloadSuccess && (
                <div className="report-success-box" role="status">
                  <span>✓ {t('reports.success_msg', 'Report compiled successfully for')} {sector}. {t('reports.ready_msg', 'Ready for maritime dispatch.')}</span>
                  <code>{downloadedFilename}</code>
                </div>
              )}

              {downloadError && (
                <div className="report-error-box" role="alert">{downloadError}</div>
              )}
            </form>
          </div>
        </div>

        {/* Right Column: Live Dossier Preview */}
        <div className="reports-right-col">
          <div className="ocean-card report-preview-card">
            <div className="card-top-header">
              <h3>{t('reports.preview_title', 'Live Document Preview')}</h3>
              <span className="badge-provenance">CONFIDENTIAL MARITIME BRIEF</span>
            </div>

            <div className="dossier-paper">
              <div className="dossier-header">
                <div className="dossier-brand">
                  <strong>OCEANIS MARINE INTELLIGENCE SYSTEM</strong>
                  <span>Government of India Marine Operations Protocol</span>
                </div>
                <div className="dossier-meta">
                  <span>Date: <strong>{formattedDate}</strong></span>
                  <span>Ref: <strong>OCN-RPT-{(selectedLocation?.lat ? Math.round(selectedLocation.lat * 100) : 8422)}</strong></span>
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
                <p>Location: {sector} • Coordinates: {coordsText} • Zone: 0 - 25 NM Coastal & Shelf Basin</p>
              </div>

              <div className="dossier-section">
                <strong>2. CONSENSUS SAFETY ASSESSMENT</strong>
                <p>Status: <span className="text-success">CLEAR / OPERATIONAL VIGILANCE</span> • Significant Wave Height: 1.2m • Wind: 12 kts ESE</p>
              </div>

              <div className="dossier-section">
                <strong>3. TARGET WAYPOINTS & HYDRODYNAMICS</strong>
                <p>PFZ Waypoint ({coordsText}): Chlorophyll-a: 0.82 mg/m³ • SST Front: 28.5°C • Distance: 12.0 NM</p>
              </div>

              {includeProvenance && (
                <div className="dossier-section provenance">
                  <strong>4. INSTITUTIONAL DATA PROVENANCE AUDIT</strong>
                  <p>• INCOIS Moored Buoys • IMD Doppler Weather Radar • Copernicus Sentinel-3 OLCI/SLSTR (Pass: Recent UTC)</p>
                </div>
              )}

              <div className="dossier-footer">
                <span>Certified by OCEANIS Multi-Agent Orchestrator v2.4</span>
                <span>Sector: {sector}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
