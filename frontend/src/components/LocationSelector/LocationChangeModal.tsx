import React from 'react';
import { useLocationContext } from '../../context/LocationContext';
import { LocationSelector } from './LocationSelector';
import './LocationSelector.css';

export const LocationChangeModal: React.FC = () => {
  const { isChangeModalOpen, setIsChangeModalOpen } = useLocationContext();

  if (!isChangeModalOpen) return null;

  return (
    <div className="loc-modal-overlay" onClick={() => setIsChangeModalOpen(false)}>
      <div className="loc-modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="loc-modal-topbar">
          <div className="loc-modal-topbar-title">
            <span>📍 Change Active Coastal Location</span>
          </div>
          <button
            type="button"
            className="loc-modal-close-btn"
            onClick={() => setIsChangeModalOpen(false)}
            aria-label="Close location modal"
          >
            ✕
          </button>
        </div>
        <div className="loc-modal-body">
          <LocationSelector
            mode="modal"
            onProceed={() => setIsChangeModalOpen(false)}
            onCancel={() => setIsChangeModalOpen(false)}
            showMapAction={true}
          />
        </div>
      </div>
    </div>
  );
};

export default LocationChangeModal;
