import React, { useState, useEffect } from 'react';
import { User } from './types';
import { api } from './services/api';
import { Navbar, ViewType } from './components/Navbar';
import { AuthModal } from './components/AuthModal';

// Views
import { OverviewView } from './views/OverviewView';
import { ApplicationView } from './views/ApplicationView';
import { RiskAnalysisView } from './views/RiskAnalysisView';
import { PortfolioView } from './views/PortfolioView';
import { EmiCalculatorView } from './views/EmiCalculatorView';
import { AiAnalystView } from './views/AiAnalystView';
import { AiQueryView } from './views/AiQueryView';
import { UserManagementView } from './views/UserManagementView';

export function App() {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem('creditpilot_user') || localStorage.getItem('loansense_user');
      if (!saved || saved === 'undefined' || saved === 'null') return null;
      return JSON.parse(saved);
    } catch {
      return null;
    }
  });

  const [currentView, setCurrentView] = useState<ViewType>('overview');
  const [apiConnected, setApiConnected] = useState(false);

  // Check backend health
  useEffect(() => {
    api.checkHealth()
      .then(() => setApiConnected(true))
      .catch(() => setApiConnected(false));
  }, []);

  const handleLoginSuccess = (loggedInUser: User) => {
    setUser(loggedInUser);
    localStorage.setItem('creditpilot_user', JSON.stringify(loggedInUser));
    setCurrentView('overview');
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('creditpilot_user');
    localStorage.removeItem('loansense_user');
  };

  if (!user) {
    return <AuthModal onSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col text-[#191919] font-sans selection:bg-[#191919] selection:text-white">
      {/* Global Navbar */}
      <Navbar
        user={user}
        currentView={currentView}
        onSelectView={setCurrentView}
        onLogout={handleLogout}
        apiConnected={apiConnected}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {currentView === 'overview' && <OverviewView onNavigate={setCurrentView} />}
        {currentView === 'applications' && <ApplicationView />}
        {currentView === 'risk' && <RiskAnalysisView />}
        {currentView === 'portfolio' && <PortfolioView />}
        {currentView === 'emi' && <EmiCalculatorView />}
        {currentView === 'ai_analyst' && <AiAnalystView />}
        {currentView === 'ai_query' && <AiQueryView />}
        {currentView === 'users' && user.role === 'admin' && <UserManagementView currentUser={user} />}
      </main>

      {/* Editorial Footer */}
      <footer className="border-t border-[#E5E5E5] bg-[#FFFFFF] py-6 text-xs font-sans text-[#191919]/50">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <span className="font-serif font-medium text-[#191919]">CreditPilot AI</span>
            <span>·</span>
            <span>Smarter lending · Stronger decisions</span>
          </div>

          <div className="flex items-center space-x-4 text-[11px] tabular-nums">
            <span>Model 2.0.0</span>
            <span>·</span>
            <span>Dual-engine risk calibration</span>
            <span>·</span>
            <span className="text-[#191919]/70">Advisory governance</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
