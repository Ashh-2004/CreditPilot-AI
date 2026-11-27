import React, { useState } from 'react';
import { api } from '../services/api';
import { User } from '../types';
import { CreditPilotLogo } from './CreditPilotLogo';
import { BoomerangCanvas } from './BoomerangCanvas';
import { ArrowRight, Eye, EyeOff, User as UserIcon, Shield } from 'lucide-react';

interface AuthModalProps {
  onSuccess: (user: User) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please enter both username and password.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const user = await api.login(username.trim(), password);
      onSuccess(user);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full bg-[#FFFFFF] flex flex-col justify-between overflow-hidden selection:bg-[#191919] selection:text-white">
      {/* Background Boomerang Canvas */}
      <BoomerangCanvas intensity="medium" />

      {/* Minimal Top Header */}
      <header className="relative z-10 w-full px-8 py-6 flex items-center justify-between border-b border-[#E5E5E5]/60 bg-white/70 backdrop-blur-sm">
        <CreditPilotLogo size="md" />
        <div className="hidden sm:flex items-center space-x-2 text-xs text-[#191919]/60 font-sans">
          <span>Enterprise Underwriting Intelligence</span>
          <span>•</span>
          <span className="text-emerald-700 font-medium">System Online</span>
        </div>
      </header>

      {/* Main Viewport Split / Hero Composition */}
      <main className="relative z-10 flex-1 max-w-7xl mx-auto w-full px-6 py-12 flex flex-col lg:flex-row items-center justify-between gap-16">
        {/* Left Column: Hero Editorial Content */}
        <div className="flex-1 max-w-xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded bg-[#F4F3F3] border border-[#E5E5E5] mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[#191919]"></span>
            <span className="text-xs font-sans font-medium text-[#191919]/70">
              Institutional credit platform
            </span>
          </div>

          <h1 className="font-serif text-5xl sm:text-6xl lg:text-7xl text-[#191919] leading-[1.08] tracking-tight mb-6">
            Smarter lending
            <br />
            <span className="text-[#191919]/60 font-serif">Stronger decisions</span>
          </h1>

          <p className="text-base sm:text-lg text-[#191919]/70 font-sans leading-relaxed mb-8 max-w-lg">
            Intelligent credit risk assessment and explainable underwriting, bringing clarity, precision and institutional governance to every lending decision.
          </p>

          <div className="grid grid-cols-3 gap-6 pt-6 border-t border-[#E5E5E5]">
            <div>
              <p className="font-serif text-2xl text-[#191919] tabular-nums">142+</p>
              <p className="text-xs text-[#191919]/60 font-sans mt-0.5">Risk attributes</p>
            </div>
            <div>
              <p className="font-serif text-2xl text-[#191919] tabular-nums">0.741</p>
              <p className="text-xs text-[#191919]/60 font-sans mt-0.5">ROC-AUC benchmark</p>
            </div>
            <div>
              <p className="font-serif text-2xl text-[#191919] tabular-nums">100%</p>
              <p className="text-xs text-[#191919]/60 font-sans mt-0.5">Human governed</p>
            </div>
          </div>
        </div>

        {/* Right Column: Authentication Panel */}
        <div className="w-full max-w-md">
          <div className="bg-white/95 backdrop-blur-md border border-[#E5E5E5] rounded-xl p-8 sm:p-10 shadow-card transition-all">
            <div className="mb-6 pb-4 border-b border-[#E5E5E5]">
              <div className="flex items-center space-x-2 text-xs font-sans text-[#191919]/60 mb-1">
                <Shield className="w-3.5 h-3.5 text-[#191919]" />
                <span>Authorized Personnel Terminal</span>
              </div>
              <h2 className="font-serif text-2xl text-[#191919]">Sign in to CreditPilot</h2>
              <p className="text-xs text-[#191919]/60 font-sans mt-1">
                Enter your provisioned institutional officer or analyst credentials
              </p>
            </div>

            {/* Error Notifications */}
            {error && (
              <div className="mb-6 p-3.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 font-sans leading-relaxed">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-xs font-sans font-medium text-[#191919]/80 mb-1.5">
                  Username or identifier
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. admin or officer"
                    required
                    className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-[#191919] text-sm font-sans placeholder:text-[#191919]/30 focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919] transition"
                  />
                  <UserIcon className="absolute right-3.5 top-3 w-4 h-4 text-[#191919]/40" />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-sans font-medium text-[#191919]/80">
                    Security password
                  </label>
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    required
                    className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-[#191919] text-sm font-sans placeholder:text-[#191919]/30 focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919] transition"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-3 text-[#191919]/40 hover:text-[#191919] transition"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-[#191919]/70 pt-1">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded border-[#E5E5E5] text-[#191919] focus:ring-0"
                  />
                  <span>Remember terminal</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-4 flex items-center justify-center space-x-2.5 py-3 px-5 rounded-lg bg-[#191919] hover:bg-[#333333] text-white font-sans text-sm font-medium transition shadow-sm disabled:opacity-50"
              >
                <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
                <ArrowRight className="w-4 h-4 text-white" />
              </button>
            </form>

            <div className="mt-6 pt-4 border-t border-[#E5E5E5] text-center">
              <p className="text-[11px] text-[#191919]/55 font-sans leading-relaxed">
                User accounts are provisioned exclusively by system administrators. Contact your administrator if you need access.
              </p>
            </div>
          </div>

          <p className="text-center text-[11px] text-[#191919]/40 font-sans mt-6">
            Institutional access is logged and audited according to banking compliance standards.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full px-8 py-5 border-t border-[#E5E5E5]/60 bg-white/70 backdrop-blur-sm flex flex-col sm:flex-row items-center justify-between text-xs text-[#191919]/50 font-sans gap-2">
        <p>© 2026 CreditPilot AI. All rights reserved.</p>
        <p>Institutional Credit Risk Modeling & Explainable Underwriting Platform</p>
      </footer>
    </div>
  );
};
