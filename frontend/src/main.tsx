import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/components/ThemeProvider';
import Background from '@/components/Background';
import Layout from '@/components/layout/Layout';

// Styles
import './globals.css';
import '@/styles/tokens.css';
import '@/styles/design-system.css';

// Pages
import HomePage from '@/pages/HomePage';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import DashboardPage from '@/pages/DashboardPage';
import AdminPage from '@/pages/AdminPage';
import PharmacistPage from '@/pages/PharmacistPage';
import AnalyticsPage from '@/pages/AnalyticsPage';
import ChatPage from '@/pages/ChatPage';
import RefillAlertsPage from '@/pages/RefillAlertsPage';
import SettingsPage from '@/pages/SettingsPage';
import SymptomPage from '@/pages/SymptomPage';
import VisionPage from '@/pages/VisionPage';
import VoicePage from '@/pages/VoicePage';

function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      {/* Background canvas */}
      <Background />

      {/* Main App routes */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/pharmacist" element={<PharmacistPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/refill-alerts" element={<RefillAlertsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/symptom" element={<SymptomPage />} />
            <Route path="/vision" element={<VisionPage />} />
            <Route path="/voice" element={<VoicePage />} />
          </Routes>
        </Layout>
      </div>
    </ThemeProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
