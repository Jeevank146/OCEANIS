import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Navbar } from '../components/Navbar/Navbar';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { Footer } from '../components/Footer/Footer';
import { LocationChangeModal } from '../components/LocationSelector/LocationChangeModal';
import './MainLayout.css';

export const MainLayout: React.FC = () => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  const isLandingPage = location.pathname === '/';

  return (
    <div className={`oceanis-app ${isLandingPage ? 'landing-mode' : 'operational-mode'}`}>
      {/* 1. Institutional Top Navigation Bar */}
      <Navbar
        onToggleSidebar={!isLandingPage ? () => setSidebarOpen(!sidebarOpen) : undefined}
      />

      {/* 2. Left Vertical Marine Operations Sidebar (Hidden on Landing Page) */}
      {!isLandingPage && (
        <Sidebar
          isMobileOpen={sidebarOpen}
          onCloseMobile={() => setSidebarOpen(false)}
        />
      )}

      {/* 3. Main Route Content Canvas */}
      <div className={`oceanis-layout-wrapper ${isLandingPage ? 'is-landing' : ''}`}>
        <main className={`oceanis-main ${isLandingPage ? 'main-landing' : ''}`}>
          <Outlet />
        </main>

        {/* 4. Institutional Maritime Footer (Render on all pages) */}
        <Footer compact={!isLandingPage} />
      </div>

      {/* 5. Global Location Switcher Modal */}
      <LocationChangeModal />
    </div>
  );
};

export default MainLayout;
