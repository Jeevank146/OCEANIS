import React from 'react';
import { useLocationContext } from '../../context/LocationContext';
import { useLanguage } from '../../context/LanguageContext';
import './ControlSidebar.css';

interface ControlSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeSection?: string;
  onSelectSection?: (sectionId: string) => void;
}

interface NavDrawerItem {
  id: string;
  label: string;
  icon: string;
  badge?: string;
  badgeType?: 'primary' | 'warning' | 'success';
}

export const ControlSidebar: React.FC<ControlSidebarProps> = ({
  isOpen,
  onClose,
  activeSection = 'overview',
  onSelectSection,
}) => {
  const { selectedLocation } = useLocationContext();
  const { t } = useLanguage();

  if (!isOpen) return null;

  const navItems: NavDrawerItem[] = [
    { id: 'overview', label: t('nav.dashboard', 'Operations Dashboard'), icon: '📊' },
    { id: 'map', label: t('nav.maps', 'Live GIS Map'), icon: '🗺️', badge: 'LIVE', badgeType: 'primary' },
    { id: 'fishing', label: t('nav.fishing', 'Fishing Intelligence'), icon: '🎣' },
    { id: 'marine', label: t('nav.marine_conditions', 'Marine Conditions'), icon: '🌊' },
    { id: 'satellite', label: t('nav.earth_observation', 'Earth Observation'), icon: '🛰️' },
    { id: 'navigation', label: t('nav.navigation', 'Geo-Spatial & Nav'), icon: '🧭' },
    { id: 'safety', label: t('nav.safety', 'Disaster & Safety'), icon: '🛡️', badge: 'ALERT', badgeType: 'warning' },
    { id: 'operations', label: t('nav.operations', 'Marine Operations'), icon: '⚓' },
    { id: 'agents', label: t('nav.agents', 'Domain Agents'), icon: '🤖' },
    { id: 'reports', label: t('nav.reports', 'Reports Generator'), icon: '📄' },
    { id: 'sources', label: t('nav.data_sources', 'Data Sources'), icon: '🗄️' },
  ];

  const handleItemClick = (id: string) => {
    if (onSelectSection) {
      onSelectSection(id);
    }
    onClose();
  };

  const activeSectorLabel = selectedLocation
    ? (selectedLocation.marine_context || selectedLocation.city || selectedLocation.name)
    : t('nav.loc_not_selected', 'Location Not Selected');

  return (
    <>
      <div
        className="sidebar-backdrop"
        onClick={onClose}
        aria-hidden="true"
      />

      <aside className="control-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <span className="sidebar-brand-title">OCEAN CONTROL</span>
            <span className="sidebar-brand-subtitle">Operational Command Drawer</span>
          </div>
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={onClose}
            aria-label="Close navigation sidebar"
          >
            ✕
          </button>
        </div>

        <nav className="sidebar-nav-list">
          {navItems.map((item) => {
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                onClick={() => handleItemClick(item.id)}
              >
                <span className="sidebar-item-icon">{item.icon}</span>
                <span className="sidebar-item-label">{item.label}</span>
                {item.badge && (
                  <span className={`sidebar-item-badge ${item.badgeType || ''}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-status-box">
          <div className="status-box-header">
            <span className="status-indicator-dot"></span>
            <span className="status-box-title">{t('dash.system_status', 'System Status')}</span>
          </div>
          <div className="status-metric-row">
            <span className="status-label">Domain Agents:</span>
            <span className="status-val positive">6/6 Synchronized</span>
          </div>
          <div className="status-metric-row">
            <span className="status-label">Data Ingestion:</span>
            <span className="status-val positive">Active Feeds</span>
          </div>
          <div className="status-metric-row">
            <span className="status-label">Active Sector:</span>
            <span className="status-val">{activeSectorLabel}</span>
          </div>
        </div>
      </aside>
    </>
  );
};

export default ControlSidebar;
