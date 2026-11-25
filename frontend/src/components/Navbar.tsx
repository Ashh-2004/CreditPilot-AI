import React, { useState } from 'react';
import { User, Role } from '../types';
import { CreditPilotLogo } from './CreditPilotLogo';
import {
  LogOut,
  Menu,
  X,
  ArrowRight
} from 'lucide-react';

export type ViewType =
  | 'overview'
  | 'applications'
  | 'risk'
  | 'portfolio'
  | 'emi'
  | 'ai_analyst'
  | 'ai_query'
  | 'users';

interface NavbarProps {
  user: User;
  currentView: ViewType;
  onSelectView: (view: ViewType) => void;
  onLogout: () => void;
  apiConnected: boolean;
}

interface NavItem {
  id: ViewType;
  label: string;
  roles: Role[];
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', roles: ['admin', 'officer', 'viewer'] },
  { id: 'applications', label: 'Applications', roles: ['admin', 'officer'] },
  { id: 'risk', label: 'Risk Intelligence', roles: ['admin', 'officer', 'viewer'] },
  { id: 'portfolio', label: 'Portfolio', roles: ['admin', 'officer', 'viewer'] },
  { id: 'emi', label: 'EMI Calculator', roles: ['admin', 'officer'] },
  { id: 'ai_analyst', label: 'AI Analyst', roles: ['admin', 'officer'] },
  { id: 'ai_query', label: 'SQL Assistant', roles: ['admin', 'officer', 'viewer'] },
  { id: 'users', label: 'User Admin', roles: ['admin'] },
];

export const Navbar: React.FC<NavbarProps> = ({
  user,
  currentView,
  onSelectView,
  onLogout,
  apiConnected
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Filter items by user role
  const accessibleItems = NAV_ITEMS.filter((item) =>
    item.roles.includes(user.role)
  );

  return (
    <header className="sticky top-0 z-50 bg-[#FFFFFF] border-b border-[#E5E5E5] transition-colors">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center space-x-8">
          <button
            onClick={() => onSelectView('overview')}
            className="focus:outline-none"
          >
            <CreditPilotLogo size="md" />
          </button>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-1">
            {accessibleItems.map((item) => {
              const isActive = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectView(item.id)}
                  className={`px-3 py-1.5 rounded text-sm font-sans transition-colors duration-150 ${
                    isActive
                      ? 'text-[#191919] font-medium bg-[#F4F3F3]'
                      : 'text-[#191919]/70 hover:text-[#191919] hover:bg-[#F4F3F3]/60'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User Profile & Right-Hand Controls */}
        <div className="hidden sm:flex items-center space-x-4">
          {/* API Health indicator */}
          <div className="flex items-center space-x-2 px-2.5 py-1 rounded bg-[#F4F3F3] border border-[#E5E5E5] text-xs">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                apiConnected ? 'bg-emerald-600' : 'bg-red-500'
              }`}
            ></span>
            <span className="text-[#191919]/70 text-[11px] font-sans">
              {apiConnected ? 'API connected' : 'Connecting'}
            </span>
          </div>

          {/* User Role Badge */}
          <div className="flex items-center space-x-3 pl-3 border-l border-[#E5E5E5]">
            <div className="flex flex-col items-end text-right">
              <span className="text-xs font-medium text-[#191919] leading-tight">
                {user.username}
              </span>
              <span className="text-[11px] text-[#191919]/50 font-sans capitalize">
                {user.role}
              </span>
            </div>

            <button
              onClick={onLogout}
              className="p-1.5 rounded text-[#191919]/50 hover:text-[#191919] hover:bg-[#F4F3F3] transition"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Mobile Hamburger Button */}
        <div className="lg:hidden flex items-center space-x-2">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded text-[#191919] hover:bg-[#F4F3F3] transition"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-white border-b border-[#E5E5E5] px-6 py-4 space-y-2">
          {accessibleItems.map((item) => {
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectView(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3.5 py-2 rounded text-sm font-sans ${
                  isActive
                    ? 'text-[#191919] font-medium bg-[#F4F3F3]'
                    : 'text-[#191919]/70 hover:text-[#191919] hover:bg-[#F4F3F3]/60'
                }`}
              >
                <span>{item.label}</span>
                {isActive && <ArrowRight className="w-4 h-4 text-[#191919]" />}
              </button>
            );
          })}

          <div className="pt-4 border-t border-[#E5E5E5] flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-[#191919]">{user.username}</p>
              <p className="text-[11px] text-[#191919]/50 capitalize">{user.role}</p>
            </div>
            <button
              onClick={onLogout}
              className="flex items-center space-x-1.5 text-xs text-red-600 font-medium py-1.5 px-3 rounded bg-red-50"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
