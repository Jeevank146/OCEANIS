import React from 'react';
import './ControlSidebar.css';

interface ControlSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeSection?: string;
  onNavigateSection?: (sectionId: string) => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: string;
  badge?: string;
  badgeType?: 'live' | 'alert' | 'agent';
}

export const ControlSidebar: React.FC<ControlSidebarProps> = ({
  isOpen,
  onClose,
  activeSection = 'home',
  onNavigateSection,
}) => {
  const navItems: NavItem[] = [
    { id: 'home', label: 'Operational Overview', icon: '⚓' },
    { id: 'live-overview', label: 'Live Marine Conditions', icon: '🌊', badge: 'LIVE', badgeType: 'live' },
    { id: 'live-map', label: 'Live Ocean GIS Map', icon: '🗺️', badge: '10 L', badgeType: 'live' },
    { id: 'safety-alerts', label: 'Safety & Marine Alerts', icon: '⚠️', badge: '2', badgeType: 'alert' },
    { id: 'satellite-eo', label: 'Earth Observation (EO)', icon: '🛰️', badge: 'Sentinel-3', badgeType: 'live' },
    { id: 'agents', label: '6 Domain Agents', icon: '🤖', badge: '6/6', badgeType: 'agent' },
    { id: 'query', label: 'Ask OCEANIS AI', icon: '💬' },
    { id: 'what-if-scenarios', label: 'What-If Simulation', icon: '🧭' },
    { id: 'trusted-sources', label: 'Institutional Sources', icon: '🏛️' },
  ];

  const handleItemClick = (id: string) => {
    if (onNavigateSection) {
      onNavigateSection(id);
    } else {
      const el = document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="control-sidebar-overlay" onClick={onClose} />
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
            <span className="status-box-title">System Status</span>
          </div>
          <div className="status-metric-row">
            <span className="status-label">Domain Agents:</span>
            <span className="status-val positive">6/6 Synchronized</span>
          </div>
          <div className="status-metric-row">
            <span className="status-label">Backend REST APIs:</span>
            <span className="status-val positive">28/28 Operational</span>
          </div>
          <div className="status-metric-row">
            <span className="status-label">Active Sector:</span>
            <span className="status-val">Bay of Bengal (Vizag)</span>
          </div>
        </div>
      </aside>
    </>
  );
};
