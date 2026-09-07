import React, { useState, useEffect } from 'react';
import './DashboardHero.css';

import heroHarbourImg from '../../assets/images/coastal_harbour_port.jpg';
import heroWavesImg from '../../assets/images/hero_ocean_waves.jpg';
import heroFishingImg from '../../assets/images/hero_coastal_fishing.jpg';
import heroVesselImg from '../../assets/images/marine_operations_vessel.jpg';

interface DashboardHeroProps {
  selectedLocation: string;
  onLocationChange: (loc: string) => void;
  onExploreMapClick?: () => void;
  onAskClick?: () => void;
}

const coastalLocations = [
  'Visakhapatnam, Andhra Pradesh',
  'Kakinada, Andhra Pradesh',
  'Chennai, Tamil Nadu',
  'Mangalore, Karnataka',
  'Kochi, Kerala',
  'Paradeep, Odisha',
];

const bgImages = [heroHarbourImg, heroFishingImg, heroWavesImg, heroVesselImg];

export const DashboardHero: React.FC<DashboardHeroProps> = ({
  selectedLocation,
  onLocationChange,
  onExploreMapClick,
  onAskClick,
}) => {
  const [bgIndex, setBgIndex] = useState(0);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>('');
  const [currentDate, setCurrentDate] = useState<string>('');

  useEffect(() => {
    const updateDateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' IST');
      setCurrentDate(now.toLocaleDateString('en-GB', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }));
    };
    updateDateTime();
    const timer = setInterval(updateDateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const slideTimer = setInterval(() => {
      setBgIndex((prev) => (prev + 1) % bgImages.length);
    }, 8000);
    return () => clearInterval(slideTimer);
  }, []);

  const handleSelect = (loc: string) => {
    onLocationChange(loc);
    setDropdownOpen(false);
  };

  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section id="home" className="dashboard-hero-section">
      {/* Background Image Carousel with Smooth Fade & Dark Overlay */}
      <div className="dashboard-hero-bg-wrapper">
        {bgImages.map((img, idx) => (
          <div
            key={idx}
            className={`hero-bg-image ${idx === bgIndex ? 'active' : ''}`}
            style={{ backgroundImage: `url(${img})` }}
          />
        ))}
        <div className="hero-dark-overlay" />
        <div className="hero-gradient-overlay" />
      </div>

      <div className="container hero-inner-container">
        <div className="hero-split-layout">
          {/* Left Column: Hero Content */}
          <div className="hero-text-block">
            <span className="hero-pre-badge">INDIAN COASTAL INTELLIGENCE</span>
            <h1 className="hero-title">Marine Intelligence Dashboard</h1>
            <p className="hero-description">
              Real-time ocean conditions, satellite intelligence, safety alerts and decision support for coastal communities, fishermen, and maritime authorities.
            </p>

            <div className="hero-actions-row">
              <button
                type="button"
                className="btn-hero-primary"
                onClick={onExploreMapClick || (() => scrollToSection('live-map'))}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
                  <line x1="8" y1="2" x2="8" y2="18" />
                  <line x1="16" y1="6" x2="16" y2="22" />
                </svg>
                <span>Explore Live Map</span>
              </button>

              <button
                type="button"
                className="btn-hero-secondary"
                onClick={onAskClick || (() => scrollToSection('query'))}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <span>Ask OCEANIS</span>
              </button>
            </div>

            <div className="hero-quote-row">
              <span className="hero-quote-text">
                "The ocean stirs the heart, inspires the imagination, and brings eternal joy to the soul."
              </span>
            </div>
          </div>

          {/* Right Column: Location & Live Telemetry Card */}
          <div className="hero-location-card">
            <div className="loc-card-header">
              <div className="loc-status-pill">
                <span className="live-dot pulse" />
                <span className="loc-status-label">DATA STATUS: <strong>LIVE</strong></span>
              </div>
              <span className="loc-time-tag">{currentTime || '01:22 PM IST'}</span>
            </div>

            <div className="loc-card-body">
              <label htmlFor="coastal-sector-btn" className="loc-field-label">COASTAL SECTOR / PORT:</label>
              
              <div className="loc-dropdown-wrapper">
                <button
                  id="coastal-sector-btn"
                  type="button"
                  className="loc-select-button"
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  aria-label="Select coastal sector"
                >
                  <svg className="loc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                  <span className="loc-name-text">{selectedLocation}</span>
                  <svg className={`loc-arrow ${dropdownOpen ? 'open' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {dropdownOpen && (
                  <div className="loc-dropdown-list">
                    {coastalLocations.map((loc) => (
                      <button
                        key={loc}
                        type="button"
                        className={`loc-option-item ${selectedLocation === loc ? 'active' : ''}`}
                        onClick={() => handleSelect(loc)}
                      >
                        <span className="loc-option-icon">⚓</span>
                        <span className="loc-option-text">{loc}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="loc-meta-grid">
                <div className="loc-meta-item">
                  <span className="loc-meta-lbl">Date:</span>
                  <span className="loc-meta-val">{currentDate || 'Sat, 06 Sep 2026'}</span>
                </div>
                <div className="loc-meta-item">
                  <span className="loc-meta-lbl">Grid System:</span>
                  <span className="loc-meta-val">EPSG:3857 (Mercator)</span>
                </div>
              </div>
            </div>

            <div className="loc-card-footer">
              <span className="loc-sources-lbl">Active Telemetry Sources:</span>
              <span className="loc-sources-val">INCOIS • IMD • Sentinel-3 • MODIS</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
