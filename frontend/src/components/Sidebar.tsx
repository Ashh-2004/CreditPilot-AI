import React from 'react';
import { Role } from '../types';
import {
  LayoutDashboard,
  FileText,
  Calculator,
  AlertTriangle,
  Globe,
  Sparkles,
  Terminal
} from 'lucide-react';

export type ViewType =
  | 'portfolio'
  | 'application'
  | 'emi'
  | 'risk'
  | 'home_credit'
  | 'ai_analyst'
  | 'ai_query';

interface SidebarProps {
  currentView: ViewType;
  onSelectView: (view: ViewType) => void;
  role: Role;
}

interface NavItem {
  id: ViewType;
  label: string;
  icon: React.ReactNode;
  roles: Role[];
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'portfolio',
    label: 'Loan Portfolio',
    icon: <LayoutDashboard className="w-5 h-5" />,
    roles: ['admin', 'officer', 'viewer'],
  },
  {
    id: 'application',
    label: 'Loan Application',
    icon: <FileText className="w-5 h-5" />,
    roles: ['admin', 'officer'],
    badge: 'Underwriting',
  },
  {
    id: 'emi',
    label: 'EMI Calculator',
    icon: <Calculator className="w-5 h-5" />,
    roles: ['admin', 'officer'],
  },
  {
    id: 'risk',
    label: 'Risk & Stress Testing',
    icon: <AlertTriangle className="w-5 h-5" />,
    roles: ['admin', 'viewer'],
  },
  {
    id: 'home_credit',
    label: 'Home Credit Risk',
    icon: <Globe className="w-5 h-5" />,
    roles: ['admin', 'officer', 'viewer'],
    badge: 'ML 142',
  },
  {
    id: 'ai_analyst',
    label: 'AI Loan Analyst',
    icon: <Sparkles className="w-5 h-5 text-amber-400" />,
    roles: ['admin', 'officer'],
    badge: 'RAG',
  },
  {
    id: 'ai_query',
    label: 'AI SQL Assistant',
    icon: <Terminal className="w-5 h-5" />,
    roles: ['admin', 'officer'],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onSelectView, role }) => {
  const allowedItems = NAV_ITEMS.filter((item) => item.roles.includes(role));

  return (
    <aside className="w-64 border-r border-dark-border bg-dark-surface/50 backdrop-blur flex flex-col justify-between p-4 shrink-0">
      <div className="space-y-6">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-dark-muted px-3">
            Core Modules
          </span>
          <nav className="mt-2 space-y-1">
            {allowedItems.map((item) => {
              const active = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectView(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition group ${
                    active
                      ? 'bg-gradient-to-r from-brand-500/20 to-brand-500/5 text-brand-300 border border-brand-500/30 shadow-sm'
                      : 'text-slate-300 hover:bg-dark-card hover:text-white'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className={active ? 'text-brand-400' : 'text-slate-400 group-hover:text-slate-200'}>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      active ? 'bg-brand-500/20 text-brand-300' : 'bg-dark-card text-dark-muted'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="pt-4 border-t border-dark-border text-xs text-dark-muted px-2">
        <p className="font-semibold text-slate-400">LoanSense AI Platform</p>
        <p className="mt-0.5 text-[11px]">React + FastAPI Architecture</p>
      </div>
    </aside>
  );
};
