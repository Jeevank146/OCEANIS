import React, { useState, useEffect } from 'react';
import './SafetyAlerts.css';
import { fetchSafetyAlerts, type SafetyAlertItem } from '../../services/api';

interface SafetyAlertsProps {
  location: string;
}

export const SafetyAlerts: React.FC<SafetyAlertsProps> = ({ location }) => {
  const [alerts, setAlerts] = useState<SafetyAlertItem[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<SafetyAlertItem | null>(null);

  useEffect(() => {
    fetchSafetyAlerts(location).then((res) => {
      setAlerts(res);
    });
  }, [location]);

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev) {
      case 'CRITICAL': return 'sev-critical';
      case 'WARNING': return 'sev-warning';
      case 'ADVISORY': return 'sev-advisory';
      default: return 'sev-normal';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Cyclone': return '🌀';
      case 'High Waves': return '🌊';
      case 'Restricted Zone': return '🚫';
      default: return '⚠️';
    }
  };

  return (
    <div id="safety-alerts" className="safety-alerts-card ocean-card">
      {/* Header */}
      <div className="alerts-card-header">
        <div>
          <h2 className="alerts-main-title">Safety & Marine Alerts</h2>
          <p className="alerts-subtitle">Active notices & hazard boundaries</p>
        </div>
        <div className="alerts-count-badge">
          <span className="live-dot pulse" />
          <span>{alerts.length} Active</span>
        </div>
      </div>

      {/* Compact Alert Cards List */}
      <div className="alerts-compact-list">
        {alerts.length === 0 ? (
          <div className="no-alerts-placeholder">
            <span className="no-alerts-icon">🛡️</span>
            <span className="no-alerts-text">No active marine advisories. Conditions normal.</span>
          </div>
        ) : (
          alerts.map((alert) => (
            <div 
              key={alert.id} 
              className={`alert-item-box ${getSeverityBadgeClass(alert.severity)}`}
              onClick={() => setSelectedAlert(selectedAlert?.id === alert.id ? null : alert)}
            >
              <div className="alert-item-lead">
                <span className="alert-item-icon">{getCategoryIcon(alert.category)}</span>
                <div className="alert-item-text-group">
                  <div className="alert-item-title-row">
                    <span className="alert-category-tag">{alert.category.toUpperCase()}</span>
                    <span className={`alert-severity-badge ${getSeverityBadgeClass(alert.severity)}`}>
                      {alert.severity}
                    </span>
                  </div>
                  <h4 className="alert-item-title">{alert.title}</h4>
                  <p className="alert-item-desc">{alert.description}</p>
                </div>
                <span className={`alert-item-arrow ${selectedAlert?.id === alert.id ? 'open' : ''}`}>→</span>
              </div>

              {/* Collapsible Details */}
              {selectedAlert?.id === alert.id && (
                <div className="alert-expanded-details">
                  <div className="alert-meta-line">
                    <span className="alert-meta-k">Location:</span>
                    <span className="alert-meta-v">{alert.location}</span>
                  </div>
                  <div className="alert-meta-line">
                    <span className="alert-meta-k">Issued:</span>
                    <span className="alert-meta-v">{alert.issuedTime} (Valid until {alert.validUntil})</span>
                  </div>
                  <div className="alert-meta-line">
                    <span className="alert-meta-k">Authority:</span>
                    <span className="alert-meta-v highlight">{alert.source}</span>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="alerts-card-footer">
        <span className="alerts-auth-text">Official Authority: <strong>IMD Cyclone Warning Division • INCOIS</strong></span>
      </div>
    </div>
  );
};
