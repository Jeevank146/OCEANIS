import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import { useLanguage } from '../../context/LanguageContext';
import './Navbar.css';

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onToggleSidebar,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { selectedLocation, setIsChangeModalOpen } = useLocationContext();
  const { language, setLanguage, t, languages } = useLanguage();

  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
    setLangDropdownOpen(false);
    setNotificationsOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const closeMenus = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMobileMenuOpen(false);
        setLangDropdownOpen(false);
        setNotificationsOpen(false);
      }
    };
    window.addEventListener('keydown', closeMenus);
    return () => window.removeEventListener('keydown', closeMenus);
  }, []);

  const navLinks = [
    { path: '/', label: t('nav.home', 'Home') },
    { path: '/dashboard', label: t('nav.dashboard', 'Dashboard') },
    { path: '/fishing', label: t('nav.fishing', 'Fishing Intelligence') },
    { path: '/marine-conditions', label: t('nav.marine_conditions', 'Marine Conditions') },
    { path: '/safety', label: t('nav.safety', 'Disaster & Safety') },
    { path: '/maps', label: t('nav.maps', 'Live Map') },
    { path: '/reports', label: t('nav.reports', 'Reports') },
  ];

  const isNavActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const hasLocation = Boolean(selectedLocation && selectedLocation.name && selectedLocation.lat !== undefined);
  const currentLangObj = languages.find((l) => l.code === language) || languages[0];
  const isOperationalPage = location.pathname !== '/';

  const handleOpenLocationSelector = () => {
    if (location.pathname === '/') {
      const el = document.querySelector('.marine-operating-panel');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
        const input = document.querySelector('.marine-search-input') as HTMLInputElement;
        if (input) input.focus();
        return;
      }
    }
    setIsChangeModalOpen(true);
  };

  return (
    <header className={`navbar-header-light ${isScrolled ? 'scrolled' : ''} ${isOperationalPage ? 'is-operational' : 'is-landing'}`}>
      <div className="navbar-container">
        {/* Left: Sidebar Toggle + Brand Logo */}
        <div className="navbar-left-group">
          {onToggleSidebar && (
            <button
              type="button"
              className="btn-sidebar-toggle"
              onClick={onToggleSidebar}
              title="Toggle Navigation Menu"
              aria-label="Toggle navigation menu"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
          )}

          <Link to="/" className="navbar-brand">
            <div className="brand-icon-wrapper">
              <svg className="brand-icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="16" cy="16" r="14" stroke="#00a896" strokeWidth="2" strokeDasharray="3 3" opacity="0.8" />
                <circle cx="16" cy="16" r="8" fill="#0b2137" stroke="#0284c7" strokeWidth="1.5" />
                <path d="M16 4V8M16 24V28M4 16H8M24 16H28" stroke="#00a896" strokeWidth="2" strokeLinecap="round" />
                <circle cx="16" cy="16" r="3" fill="#00d2d3" />
                <path d="M11 21C13.5 19 18.5 19 21 21" stroke="#16a34a" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <span className="brand-beacon-dot"></span>
            </div>
            <div className="brand-text-block">
              <span className="brand-name">OCEANIS</span>
              <span className="brand-tagline">Ocean Intelligence for a Safer Tomorrow</span>
            </div>
          </Link>
        </div>

        {/* Center: Desktop Navigation Links */}
        {!isOperationalPage && (
          <nav className="navbar-nav desktop-nav" aria-label="Primary navigation">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`nav-link ${isNavActive(link.path) ? 'active' : ''}`}
                aria-current={isNavActive(link.path) ? 'page' : undefined}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        )}

        {/* Right: Actions Cluster */}
        <div className="navbar-right-group">
          {/* Dynamic Active Location Pill */}
          {hasLocation && (
            <button
              type="button"
              className="navbar-active-loc-btn"
              onClick={handleOpenLocationSelector}
              title={`Active location: ${selectedLocation.name}. Click to change.`}
            >
              <span className="navbar-loc-pin">📍</span>
              <span className="navbar-loc-name">{selectedLocation.city || selectedLocation.name}</span>
              <span className="navbar-loc-change-tag">{t('nav.change_loc', 'Change')}</span>
            </button>
          )}

          {/* Global Language Selector Dropdown */}
          <div className="lang-selector-wrapper">
            <button
              type="button"
              className="lang-selector-btn"
              onClick={() => setLangDropdownOpen(!langDropdownOpen)}
              aria-label="Select language"
              aria-expanded={langDropdownOpen}
              aria-controls="language-menu"
            >
              <svg className="lang-globe-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
              <span className="lang-current">{currentLangObj.nativeName}</span>
              <svg className={`lang-chevron ${langDropdownOpen ? 'open' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {langDropdownOpen && (
              <div className="lang-dropdown-menu" id="language-menu">
                {languages.map((l) => (
                  <button
                    key={l.code}
                    type="button"
                    className={`lang-option ${language === l.code ? 'active' : ''}`}
                    onClick={() => {
                      setLanguage(l.code);
                      setLangDropdownOpen(false);
                    }}
                  >
                    <span className="lang-option-label">{l.nativeName}</span>
                    <span className="lang-option-code">{l.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Operational Notification Bell */}
          <div className="notif-wrapper">
            <button
              type="button"
              className="navbar-icon-btn"
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              title="Active Marine Advisories and Notices"
              aria-label="Notifications"
              aria-expanded={notificationsOpen}
              aria-controls="notifications-menu"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
              <span className="notif-badge-dot"></span>
            </button>

            {notificationsOpen && (
              <div className="notif-dropdown-menu" id="notifications-menu">
                <div className="notif-menu-header">
                  <span className="notif-title">{t('dash.active_advisories', 'Operational Advisories')}</span>
                  <span className="notif-count">2 Active</span>
                </div>
                <button type="button" className="notif-item" onClick={() => { setNotificationsOpen(false); navigate('/safety'); }}>
                  <span className="notif-icon advisory">⚠️</span>
                  <div className="notif-body">
                    <strong className="notif-heading">Coastal Swell Advisory</strong>
                    <p className="notif-desc">Wave surge monitoring active for inshore shelf waters</p>
                    <span className="notif-time">12 min ago • INCOIS</span>
                  </div>
                </button>
                <button type="button" className="notif-item" onClick={() => { setNotificationsOpen(false); navigate('/earth-observation'); }}>
                  <span className="notif-icon normal">🛰️</span>
                  <div className="notif-body">
                    <strong className="notif-heading">Sentinel-3 Pass Synchronized</strong>
                    <p className="notif-desc">Chlorophyll-a and SST gradients updated</p>
                    <span className="notif-time">45 min ago • Copernicus</span>
                  </div>
                </button>
              </div>
            )}
          </div>

          {/* One location control is enough; avoid repeating the same sector twice. */}
          {!hasLocation && (
            <button
              type="button"
              className="operator-profile-badge operator-profile-empty"
              title="Select an operating area"
              onClick={handleOpenLocationSelector}
            >
              <div className="operator-avatar" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
              </div>
              <span className="operator-name">Select area</span>
            </button>
          )}

          {/* Primary Action Button (Ask OCEANIS CTA) */}
          <Link
            to="/ask"
            className="btn-launch-header"
          >
            <span>{t('nav.ask', 'Ask OCEANIS')}</span>
            <svg className="btn-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </Link>

          {/* Mobile Hamburger Button */}
          <button
            type="button"
            className={`mobile-toggle-btn ${mobileMenuOpen ? 'open' : ''}`}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle mobile menu"
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-navigation"
          >
            <span className="hamburger-bar"></span>
            <span className="hamburger-bar"></span>
            <span className="hamburger-bar"></span>
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="mobile-nav-drawer" id="mobile-navigation">
          <nav className="mobile-nav-links">
            <Link to="/" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.home', 'Home')}</Link>
            <Link to="/dashboard" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.dashboard', 'Dashboard')}</Link>
            <Link to="/fishing" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.fishing', 'Fishing Intelligence')}</Link>
            <Link to="/marine-conditions" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.marine_conditions', 'Marine Conditions')}</Link>
            <Link to="/safety" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.safety', 'Disaster & Safety')}</Link>
            <Link to="/maps" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.maps', 'Live Map')}</Link>
            <Link to="/ask" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.ask', 'Ask OCEANIS')}</Link>
            <Link to="/earth-observation" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.earth_observation', 'Earth Observation')}</Link>
            <Link to="/navigation" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.navigation', 'Geo-Spatial & Nav')}</Link>
            <Link to="/operations" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.operations', 'Marine Operations')}</Link>
            <Link to="/reports" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.reports', 'Reports')}</Link>
            <Link to="/data-sources" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.data_sources', 'Data Sources')}</Link>
            <Link to="/agents" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>{t('nav.agents', 'Domain Agents')}</Link>
          </nav>
        </div>
      )}
    </header>
  );
};

export default Navbar;
