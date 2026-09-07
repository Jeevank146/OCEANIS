import React from 'react';
import './FinalCta.css';
import sunsetBg from '../../assets/images/sunset_ocean_cta.jpg';

interface FinalCtaProps {
  onExploreClick?: () => void;
  onAskClick?: () => void;
}

export const FinalCta: React.FC<FinalCtaProps> = ({ onExploreClick, onAskClick }) => {
  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="final-cta-section">
      <div 
        className="final-cta-bg" 
        style={{ backgroundImage: `url(${sunsetBg})` }}
      >
        <div className="final-cta-overlay"></div>
      </div>

      <div className="container final-cta-container">
        <div className="final-cta-content">
          <span className="final-cta-tag">SUSTAINABLE MARITIME GOVERNANCE</span>
          <h2 className="final-cta-title">Turn Ocean Data into Better Decisions.</h2>
          <p className="final-cta-desc">
            Empowering coastal communities, fishermen, fleet managers, and maritime authorities with deterministic safety rules, satellite Earth observation, and AI decision intelligence.
          </p>

          <div className="final-cta-btn-group">
            <button
              type="button"
              className="btn-cta-primary"
              onClick={onExploreClick || (() => scrollToSection('live-overview'))}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 2 7 12 12 22 7 12 2" />
                <polyline points="2 17 12 22 22 17" />
                <polyline points="2 12 12 17 22 12" />
              </svg>
              <span>Explore Live Intelligence</span>
            </button>

            <button
              type="button"
              className="btn-cta-secondary"
              onClick={onAskClick || (() => scrollToSection('query'))}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <span>Ask OCEANIS</span>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
