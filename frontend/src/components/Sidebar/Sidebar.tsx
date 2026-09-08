import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import './Sidebar.css';

interface SidebarProps {
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

interface SidebarNavItem {
  id: string;
  path: string;
  labelKey: string;
  defaultLabel: string;
  icon: React.ReactNode;
  badge?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const location = useLocation();
  const { t } = useLanguage();

  const primaryNavItems: SidebarNavItem[] = [
    {
      id: 'dashboard',
      path: '/dashboard',
      labelKey: 'nav.dashboard',
      defaultLabel: 'Dashboard',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
        </svg>
      ),
    },
    {
      id: 'live-map',
      path: '/maps',
      labelKey: 'nav.maps',
      defaultLabel: 'Live Map',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
          <line x1="8" y1="2" x2="8" y2="18" />
          <line x1="16" y1="6" x2="16" y2="22" />
        </svg>
      ),
      badge: 'GIS',
    },
    {
      id: 'fishing',
      path: '/fishing',
      labelKey: 'nav.fishing',
      defaultLabel: 'Fishing Intelligence',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c2.5 0 4.8-.9 6.5-2.5L22 22l-2.5-3.5C21.1 16.8 22 14.5 22 12c0-5.5-4.5-10-10-10z" />
          <path d="M8 12c1.5-2 4-2 5.5 0" />
        </svg>
      ),
    },
    {
      id: 'marine-conditions',
      path: '/marine-conditions',
      labelKey: 'nav.marine_conditions',
      defaultLabel: 'Marine Conditions',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
          <path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1" />
        </svg>
      ),
    },
    {
      id: 'earth-observation',
      path: '/earth-observation',
      labelKey: 'nav.earth_observation',
      defaultLabel: 'Earth Observation',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="9" />
          <path d="M3.6 9h16.8M3.6 15h16.8" />
        </svg>
      ),
    },
    {
      id: 'geospatial',
      path: '/navigation',
      labelKey: 'nav.navigation',
      defaultLabel: 'Geo-Spatial & Nav',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
        </svg>
      ),
    },
    {
      id: 'disaster-safety',
      path: '/safety',
      labelKey: 'nav.safety',
      defaultLabel: 'Disaster & Safety',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <line x1="12" y1="8" x2="12" y2="12" />
        </svg>
      ),
      badge: 'ALERT',
    },
    {
      id: 'marine-operations',
      path: '/operations',
      labelKey: 'nav.operations',
      defaultLabel: 'Marine Operations',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 18l3.5-3.5L12 19l8-8-3.5-3.5L12 12 7 7 3 18z" />
        </svg>
      ),
    },
    {
      id: 'query',
      path: '/ask',
      labelKey: 'nav.ask',
      defaultLabel: 'Ask OCEANIS',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      ),
      badge: 'AI',
    },
  ];

  const secondaryNavItems: SidebarNavItem[] = [
    {
      id: 'agents',
      path: '/agents',
      labelKey: 'nav.agents',
      defaultLabel: 'Domain Agents',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      ),
    },
    {
      id: 'analytics',
      path: '/analytics',
      labelKey: 'nav.analytics',
      defaultLabel: 'Analytics',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
      ),
    },
    {
      id: 'reports',
      path: '/reports',
      labelKey: 'nav.reports',
      defaultLabel: 'Reports',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
      ),
    },
    {
      id: 'data-sources',
      path: '/data-sources',
      labelKey: 'nav.data_sources',
      defaultLabel: 'Data Sources',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
        </svg>
      ),
    },
    {
      id: 'settings',
      path: '/settings',
      labelKey: 'nav.settings',
      defaultLabel: 'Settings',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      ),
    },
  ];

  const isNavActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="sidebar-mobile-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Main Sidebar Shell */}
      <aside className={`oceanis-sidebar ${isMobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-scroll-container">
          {/* Section: Operational Core Navigation */}
          <div className="sidebar-group">
            <div className="sidebar-group-title">OPERATIONS</div>
            <nav className="sidebar-nav">
              {primaryNavItems.map((item) => (
                <Link
                  key={item.id}
                  to={item.path}
                  className={`sidebar-link ${isNavActive(item.path) ? 'active' : ''}`}
                  onClick={onCloseMobile}
                >
                  <span className="sidebar-icon">{item.icon}</span>
                  <span className="sidebar-label">{t(item.labelKey, item.defaultLabel)}</span>
                  {item.badge && (
                    <span className={`sidebar-badge badge-${item.badge.toLowerCase()}`}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              ))}
            </nav>
          </div>

          <div className="sidebar-divider" />

          {/* Section: System & Analytical Tools */}
          <div className="sidebar-group">
            <div className="sidebar-group-title">INTELLIGENCE & CONFIG</div>
            <nav className="sidebar-nav">
              {secondaryNavItems.map((item) => (
                <Link
                  key={item.id}
                  to={item.path}
                  className={`sidebar-link ${isNavActive(item.path) ? 'active' : ''}`}
                  onClick={onCloseMobile}
                >
                  <span className="sidebar-icon">{item.icon}</span>
                  <span className="sidebar-label">{t(item.labelKey, item.defaultLabel)}</span>
                </Link>
              ))}
            </nav>
          </div>
        </div>

        {/* Sidebar Footer Indicator */}
        <div className="sidebar-footer">
          <div className="engine-status-pill">
            <span className="pulse-indicator-dot" />
            <span className="engine-status-text">6/6 Agents Live</span>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
