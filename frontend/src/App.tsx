import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LocationProvider } from './context/LocationContext';
import { LanguageProvider } from './context/LanguageContext';
import { MainLayout } from './layouts/MainLayout';
import { ScrollToTop } from './components/ScrollToTop/ScrollToTop';

// Dedicated Page Workspaces
import { HomePage } from './pages/HomePage/HomePage';
import { DashboardPage } from './pages/DashboardPage/DashboardPage';
import { LiveMapPage } from './pages/LiveMapPage/LiveMapPage';
import { FishingPage } from './pages/FishingPage/FishingPage';
import { MarineConditionsPage } from './pages/MarineConditionsPage/MarineConditionsPage';
import { EarthObservationPage } from './pages/EarthObservationPage/EarthObservationPage';
import { GeospatialPage } from './pages/GeospatialPage/GeospatialPage';
import { DisasterSafetyPage } from './pages/DisasterSafetyPage/DisasterSafetyPage';
import { MarineOperationsPage } from './pages/MarineOperationsPage/MarineOperationsPage';
import { AskOceanisPage } from './pages/AskOceanisPage/AskOceanisPage';
import { DecisionIntelligencePage } from './pages/DecisionIntelligencePage/DecisionIntelligencePage';
import { WhatIfPage } from './pages/WhatIfPage/WhatIfPage';
import { AgentsPage } from './pages/AgentsPage/AgentsPage';
import { DataSourcesPage } from './pages/DataSourcesPage/DataSourcesPage';
import { AnalyticsPage } from './pages/AnalyticsPage/AnalyticsPage';
import { ReportsPage } from './pages/ReportsPage/ReportsPage';
import { SettingsPage } from './pages/SettingsPage/SettingsPage';

import './App.css';

export const App: React.FC = () => {
  return (
    <LanguageProvider>
      <LocationProvider>
        <BrowserRouter>
          {/* Automatic scroll reset on route changes */}
          <ScrollToTop />

          <Routes>
            <Route element={<MainLayout />}>
              {/* 1. Dedicated Full-Screen Landing Page */}
              <Route path="/" element={<HomePage />} />

              {/* 2. Dedicated Marine Intelligence Dashboard */}
              <Route path="/dashboard" element={<DashboardPage />} />

              {/* 3. Live Ocean Intelligence GIS Map */}
              <Route path="/maps" element={<LiveMapPage />} />
              <Route path="/live-map" element={<Navigate to="/maps" replace />} />

              {/* 4. Fishing Intelligence Agent */}
              <Route path="/fishing" element={<FishingPage />} />
              <Route path="/fishing-intelligence" element={<Navigate to="/fishing" replace />} />

              {/* 5. Marine Conditions Agent */}
              <Route path="/marine-conditions" element={<MarineConditionsPage />} />

              {/* 6. Earth Observation Intelligence Agent */}
              <Route path="/earth-observation" element={<EarthObservationPage />} />

              {/* 7. Geo-Spatial & Navigation Intelligence Agent */}
              <Route path="/navigation" element={<GeospatialPage />} />
              <Route path="/geo-spatial" element={<Navigate to="/navigation" replace />} />
              <Route path="/geospatial" element={<Navigate to="/navigation" replace />} />

              {/* 8. Disaster & Safety Intelligence Agent */}
              <Route path="/safety" element={<DisasterSafetyPage />} />
              <Route path="/disaster-safety" element={<Navigate to="/safety" replace />} />
              <Route path="/alerts" element={<Navigate to="/safety" replace />} />

              {/* 9. Marine Operations Intelligence Agent */}
              <Route path="/operations" element={<MarineOperationsPage />} />
              <Route path="/marine-operations" element={<Navigate to="/operations" replace />} />

              {/* 10. Ask OCEANIS Conversational Multi-Agent AI */}
              <Route path="/ask" element={<AskOceanisPage />} />
              <Route path="/ask-oceanis" element={<Navigate to="/ask" replace />} />

              {/* 11. Decision Intelligence Pipeline & Provenance */}
              <Route path="/decision-intelligence" element={<DecisionIntelligencePage />} />

              {/* 12. Predictive What-If Marine Simulation */}
              <Route path="/what-if" element={<WhatIfPage />} />

              {/* 13. Six Domain Intelligence Agents Showcase */}
              <Route path="/agents" element={<AgentsPage />} />

              {/* 14. Trusted Institutional Data Sources */}
              <Route path="/data-sources" element={<DataSourcesPage />} />
              <Route path="/about" element={<Navigate to="/data-sources" replace />} />

              {/* 15. Marine Analytics & Performance KPIs */}
              <Route path="/analytics" element={<AnalyticsPage />} />

              {/* 16. Structured Report Generator */}
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/resources" element={<Navigate to="/reports" replace />} />

              {/* 17. Platform Settings & Operator Profile */}
              <Route path="/settings" element={<SettingsPage />} />

              {/* Fallback to Landing */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </LocationProvider>
    </LanguageProvider>
  );
};

export default App;
