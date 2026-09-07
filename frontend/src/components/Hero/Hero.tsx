import React, { useState, useEffect, useRef } from 'react';
import './Hero.css';

import heroFishing from '../../assets/images/hero_coastal_fishing.jpg';
import heroWaves from '../../assets/images/hero_ocean_waves.jpg';
import heroSatellite from '../../assets/images/hero_satellite_earth.jpg';
import heroSafety from '../../assets/images/hero_maritime_safety.jpg';

interface HeroSlide {
  id: number;
  image: string;
  tag: string;
  tagColor: 'cyan' | 'blue' | 'teal' | 'amber';
  headline: string;
  subheadline: string;
  capabilityLabel: string;
  capabilityValue: string;
}

const slides: HeroSlide[] = [
  {
    id: 1,
    image: heroFishing,
    tag: 'INDIAN COASTAL & FISHING INTELLIGENCE',
    tagColor: 'cyan',
    headline: 'Intelligent Oceans. Safer Communities.',
    subheadline: 'An AI-powered marine intelligence and decision support platform integrating ocean observations, weather forecasts, satellite Earth Observation, geospatial analytics, safety guardrails, and multi-agent AI reasoning.',
    capabilityLabel: 'Architecture',
    capabilityValue: '6 Specialized Domain Agents',
  },
  {
    id: 2,
    image: heroWaves,
    tag: 'HYDRODYNAMIC SEA STATE & WAVE DYNAMICS',
    tagColor: 'blue',
    headline: 'Real-Time Ocean Physics & Hydrography',
    subheadline: 'Continuous integration of wave heights, swell periods, and surface wind vectors from official oceanographic observation buoys and hydrodynamic models.',
    capabilityLabel: 'Foundation',
    capabilityValue: 'Evidence-Based Grounded Telemetry',
  },
  {
    id: 3,
    image: heroSatellite,
    tag: 'ORBITAL EARTH OBSERVATION',
    tagColor: 'teal',
    headline: 'Satellite Remote Sensing & Bio-Optics',
    subheadline: 'Multi-spectral satellite telemetry detecting chlorophyll-a biological concentration, thermal sea surface gradients, and oceanographic fronts.',
    capabilityLabel: 'Data Pipeline',
    capabilityValue: 'Multi-Source Intelligence Fusion',
  },
  {
    id: 4,
    image: heroSafety,
    tag: 'MARITIME SAFETY & DISASTER RESILIENCE',
    tagColor: 'amber',
    headline: 'Deterministic Hazard & Refuge Routing',
    subheadline: 'PostGIS spatial geofencing tracking tropical cyclone corridors, storm surge alerts, naval exclusions, and nearest safe harbor refuges.',
    capabilityLabel: 'Reliability',
    capabilityValue: 'Deterministic Safety-First Guardrails',
  },
];

interface HeroProps {
  onAskClick?: () => void;
  onExploreMapClick?: () => void;
}

export const Hero: React.FC<HeroProps> = ({ onAskClick, onExploreMapClick }) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isPaused) {
      timerRef.current = window.setInterval(() => {
        setCurrentSlide((prev) => (prev + 1) % slides.length);
      }, 7000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPaused]);

  const handleNext = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length);
  };

  const handlePrev = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section 
      id="home" 
      className="hero-section"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      aria-label="OCEANIS Hero Carousel"
    >
      {/* Background Slides with Rich Visibility */}
      <div className="hero-carousel-container">
        {slides.map((slide, index) => (
          <div
            key={slide.id}
            className={`hero-slide ${index === currentSlide ? 'active' : ''}`}
            style={{ backgroundImage: `url(${slide.image})` }}
          >
            <div className="hero-overlay-dark"></div>
            <div className="hero-overlay-gradient"></div>
          </div>
        ))}
      </div>

      {/* Foreground Content */}
      <div className="container hero-content-wrapper">
        <div className="hero-content">
          {/* Animated Slide Domain Badge */}
          <div className="hero-badge-row">
            <span className={`badge badge-${slides[currentSlide].tagColor} hero-tag`}>
              <span className="badge-pulse-dot"></span>
              {slides[currentSlide].tag}
            </span>
          </div>

          {/* Main Headline */}
          <h1 className="hero-title">
            {slides[currentSlide].headline}
          </h1>

          {/* Supporting Subtitle */}
          <p className="hero-subtitle">
            {slides[currentSlide].subheadline}
          </p>

          {/* Action CTAs */}
          <div className="hero-cta-group">
            <button 
              type="button" 
              className="btn-hero-primary"
              onClick={onAskClick || (() => scrollToSection('query'))}
              aria-label="Ask OCEANIS AI query"
            >
              <svg className="hero-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <span>Ask OCEANIS</span>
            </button>

            <button 
              type="button" 
              className="btn-hero-secondary"
              onClick={onExploreMapClick || (() => scrollToSection('live-status'))}
              aria-label="Explore Live Status and Map"
            >
              <svg className="hero-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 2 7 12 12 22 7 12 2" />
                <polyline points="2 17 12 22 22 17" />
                <polyline points="2 12 12 17 22 12" />
              </svg>
              <span>Explore Live Map</span>
            </button>
          </div>

          {/* Clean Non-Numeric Capability Badges (No Fabricated Metrics) */}
          <div className="hero-capabilities-strip">
            <div className="capability-pill">
              <span className="capability-dot"></span>
              <span className="capability-text">{slides[currentSlide].capabilityValue}</span>
            </div>
            <div className="capability-pill">
              <span className="capability-dot"></span>
              <span className="capability-text">Multilingual Coastal Voice</span>
            </div>
            <div className="capability-pill">
              <span className="capability-dot"></span>
              <span className="capability-text">Deterministic Safety Overrides</span>
            </div>
          </div>
        </div>

        {/* Carousel Navigation Bar */}
        <div className="hero-carousel-controls">
          <button 
            type="button" 
            className="carousel-arrow prev" 
            onClick={handlePrev}
            aria-label="Previous slide"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>

          <div className="carousel-indicators">
            {slides.map((s, idx) => (
              <button
                key={s.id}
                type="button"
                className={`indicator-dot ${idx === currentSlide ? 'active' : ''}`}
                onClick={() => setCurrentSlide(idx)}
                aria-label={`Go to slide ${idx + 1}`}
              >
                <span className="dot-inner"></span>
              </button>
            ))}
          </div>

          <button 
            type="button" 
            className="carousel-arrow next" 
            onClick={handleNext}
            aria-label="Next slide"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>
      </div>
    </section>
  );
};
