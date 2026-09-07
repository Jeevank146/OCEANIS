import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useLocationContext } from '../../context/LocationContext';
import './Navbar.css';

interface NavbarProps {
  currentLanguage?: string;
  onSelectLanguage?: (lang: string) => void;
  onToggleSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ 
  currentLanguage = 'en', 
  onSelectLanguage, 
  onToggleSidebar,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { selectedLocation, setIsChangeModalOpen } = useLocationContext();

  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeLang, setActiveLang] = useState('English');
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const languages = [
    { code: 'en', name: 'English', label: 'English' },
    { code: 'te', name: 'Telugu', label: 'తెలుగు' },
    { code: 'hi', name: 'Hindi', label: 'हिन्दी' },
    { code: 'ta', name: 'Tamil', label: 'தமிழ்' },
  ];

  useEffect(() => {
    const matched = languages.find(l => l.code === currentLanguage);
    if (matched) {
      setActiveLang(matched.label);
    }
  }, [currentLanguage]);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLanguageSelect = (lang: { code: string; name: string; label: string }) => {
    setActiveLang(lang.label);
    setLangDropdownOpen(false);
    if (onSelectLanguage) {
      onSelectLanguage(lang.code);
    }
  };

  const navLinks = [
    { path: '/', label: 'Home' },
    { path: '/dashboard', label: 'Explore' },
    { path: '/agents', label: 'Agents' },
    { path: '/maps', label: 'Maps' },
    { path: '/safety', label: 'Alerts' },
    { path: '/reports', label: 'Resources' },
    { path: '/data-sources', label: 'About' },
  ];

  const isNavActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <header className={`navbar-header-light ${isScrolled ? 'scrolled' : ''}`}>
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
        <nav className="navbar-nav desktop-nav">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`nav-link ${isNavActive(link.path) ? 'active' : ''}`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Right: Actions, Location Indicator, Language, Profile & Launch */}
        <div className="navbar-right-group">
          {/* Active Coastal Station Badge */}
          <button 
            type="button" 
            className="navbar-location-pill"
            onClick={() => setIsChangeModalOpen(true)}
            title={`Active Coastal Station: ${selectedLocation.name} (Click to Change Location)`}
            aria-label="Change Active Coastal Location"
          >
            <span className="navbar-loc-pin">📍</span>
            <span className="navbar-loc-name">{selectedLocation.city || selectedLocation.name}</span>
            <span className="navbar-loc-change-tag">Change</span>
          </button>

          {/* Language Selector Dropdown */}
          <div className="lang-selector-wrapper">
            <button 
              type="button" 
              className="lang-selector-btn"
              onClick={() => setLangDropdownOpen(!langDropdownOpen)}
              aria-label="Select language"
            >
              <svg className="lang-globe-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
              <span className="lang-current">{activeLang}</span>
              <svg className={`lang-chevron ${langDropdownOpen ? 'open' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {langDropdownOpen && (
              <div className="lang-dropdown-menu">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    type="button"
                    className={`lang-option ${activeLang === lang.label ? 'active' : ''}`}
                    onClick={() => handleLanguageSelect(lang)}
                  >
                    <span className="lang-option-label">{lang.label}</span>
                    <span className="lang-option-code">{lang.name}</span>
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
              title="Active Marine Advisories & Notices"
              aria-label="Notifications"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
              <span className="notif-badge-dot"></span>
            </button>

            {notificationsOpen && (
              <div className="notif-dropdown-menu">
                <div className="notif-menu-header">
                  <span className="notif-title">Operational Advisories</span>
                  <span className="notif-count">2 Active</span>
                </div>
                <div className="notif-item" onClick={() => { setNotificationsOpen(false); navigate('/safety'); }}>
                  <span className="notif-icon advisory">⚠️</span>
                  <div className="notif-body">
                    <strong className="notif-heading">Moderate Swell Advisory</strong>
                    <p className="notif-desc">Kakinada & Vizag Coastal Sector (Wave: 1.8m)</p>
                    <span className="notif-time">12 min ago • INCOIS</span>
                  </div>
                </div>
                <div className="notif-item" onClick={() => { setNotificationsOpen(false); navigate('/earth-observation'); }}>
                  <span className="notif-icon normal">🛰️</span>
                  <div className="notif-body">
                    <strong className="notif-heading">Sentinel-3 Pass Ingested</strong>
                    <p className="notif-desc">Chlorophyll-a & SST gradients synchronized</p>
                    <span className="notif-time">45 min ago • Copernicus</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Profile / Portal Icon with Operator Title */}
          <Link to="/settings" className="operator-profile-badge" title="Authenticated Maritime Operator">
            <div className="operator-avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <div className="operator-info">
              <span className="operator-name">Cmdr. R. Verma</span>
              <span className="operator-role">Vizag Sector</span>
            </div>
          </Link>

          {/* Primary Action Button */}
          <Link 
            to="/ask" 
            className="btn-launch-header"
          >
            <span>Ask OCEANIS</span>
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
          >
            <span className="hamburger-bar"></span>
            <span className="hamburger-bar"></span>
            <span className="hamburger-bar"></span>
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="mobile-nav-drawer">
          <nav className="mobile-nav-links">
            <Link to="/" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Home Landing</Link>
            <Link to="/dashboard" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Operations Dashboard</Link>
            <Link to="/maps" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Live Ocean GIS Map</Link>
            <Link to="/fishing" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Fishing Intelligence</Link>
            <Link to="/marine-conditions" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Marine Conditions</Link>
            <Link to="/earth-observation" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Earth Observation</Link>
            <Link to="/navigation" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Geo-Spatial & Navigation</Link>
            <Link to="/safety" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Disaster & Safety</Link>
            <Link to="/operations" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Marine Operations</Link>
            <Link to="/decision-intelligence" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Decision Intelligence</Link>
            <Link to="/what-if" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>What-If Simulation</Link>
            <Link to="/agents" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Domain Agents</Link>
            <Link to="/analytics" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Analytics</Link>
            <Link to="/reports" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Reports</Link>
            <Link to="/data-sources" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Data Sources</Link>
            <Link to="/settings" className="mobile-link" onClick={() => setMobileMenuOpen(false)}>Settings</Link>
            <div className="mobile-drawer-footer">
              <Link to="/ask" className="btn-mobile-launch" onClick={() => setMobileMenuOpen(false)}>
                Launch Ask OCEANIS Assistant
              </Link>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
};
