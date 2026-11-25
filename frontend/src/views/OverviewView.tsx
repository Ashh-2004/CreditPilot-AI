import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { PortfolioData, ApplicationItem } from '../types';
import { ViewType } from '../components/Navbar';
import { BoomerangCanvas } from '../components/BoomerangCanvas';
import {
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  XCircle
} from 'lucide-react';

interface OverviewViewProps {
  onNavigate: (view: ViewType) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate }) => {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getPortfolio()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load credit intelligence metrics');
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-4">
        <div className="w-5 h-5 border-2 border-[#191919] border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-sans text-[#191919]/50">Loading credit intelligence...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="space-y-6 py-12">
        <div className="p-6 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 space-y-2">
          <p className="font-semibold text-sm">Unable to connect to credit intelligence backend</p>
          <p>{error}</p>
          <p className="text-[#191919]/60 pt-2">Please ensure the backend API server is running on http://localhost:8000.</p>
        </div>
      </div>
    );
  }

  const kpis = data?.kpis;
  const recentApps: ApplicationItem[] = (data?.applications || []).slice(0, 5);

  return (
    <div className="space-y-16 pb-16">
      {/* Editorial Hero Introduction */}
      <section className="relative overflow-hidden pt-8 pb-12 border-b border-[#E5E5E5]">
        <BoomerangCanvas intensity="subtle" />
        <div className="relative z-10 max-w-4xl">
          <p className="text-xs text-[#191919]/60 font-sans mb-2">
            Credit intelligence overview
          </p>
          <h1 className="font-serif text-5xl sm:text-6xl text-[#191919] tracking-tight leading-[1.08] mb-4">
            A clearer view of lending
          </h1>
          <p className="text-base sm:text-lg text-[#191919]/70 font-sans max-w-2xl leading-relaxed">
            Monitor applications, understand portfolio exposure and identify emerging credit risk with dual-engine predictive intelligence.
          </p>
        </div>

        {/* Quick Action Badges */}
        <div className="relative z-10 flex flex-wrap gap-2.5 mt-8">
          <button
            onClick={() => onNavigate('applications')}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded bg-[#191919] text-white text-xs font-medium font-sans hover:bg-[#333333] transition-colors"
          >
            <span>Intake new application</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onNavigate('risk')}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded bg-[#F4F3F3] text-[#191919] border border-[#E5E5E5] text-xs font-medium font-sans hover:bg-[#EAEAEA] transition-colors"
          >
            <span>Risk models & benchmarks</span>
            <ArrowRight className="w-3.5 h-3.5 text-[#191919]/60" />
          </button>
          <button
            onClick={() => onNavigate('ai_analyst')}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded bg-[#F4F3F3] text-[#191919] border border-[#E5E5E5] text-xs font-medium font-sans hover:bg-[#EAEAEA] transition-colors"
          >
            <span>Underwriting memo</span>
            <ArrowRight className="w-3.5 h-3.5 text-[#191919]/60" />
          </button>
        </div>
      </section>

      {/* Editorial Metric Groups */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-8 pb-12 border-b border-[#E5E5E5]">
        <div>
          <p className="text-xs font-sans text-[#191919]/60 mb-1.5">Total volume disbursed</p>
          <p className="font-serif text-3xl sm:text-4xl text-[#191919] tabular-nums">
            ₹{((kpis?.total_disbursed || 0) / 10000000).toFixed(2)} Cr
          </p>
          <p className="text-xs text-[#191919]/50 font-sans mt-1">Institutional book exposure</p>
        </div>

        <div>
          <p className="text-xs font-sans text-[#191919]/60 mb-1.5">Total applications</p>
          <p className="font-serif text-3xl sm:text-4xl text-[#191919] tabular-nums">
            {kpis?.total_applications || 0}
          </p>
          <p className="text-xs text-[#191919]/50 font-sans mt-1">Underwritten profiles</p>
        </div>

        <div>
          <p className="text-xs font-sans text-[#191919]/60 mb-1.5">Approval rate</p>
          <p className="font-serif text-3xl sm:text-4xl text-[#191919] tabular-nums">
            {kpis?.approval_rate || 0}%
          </p>
          <p className="text-xs text-[#191919]/50 font-sans mt-1">{kpis?.approved_count || 0} approved accounts</p>
        </div>

        <div>
          <p className="text-xs font-sans text-[#191919]/60 mb-1.5">Weighted interest rate</p>
          <p className="font-serif text-3xl sm:text-4xl text-[#191919] tabular-nums">
            {kpis?.weighted_interest_rate || 0}%
          </p>
          <p className="text-xs text-[#191919]/50 font-sans mt-1">Average portfolio yield</p>
        </div>
      </section>

      {/* Exposure Breakdown & Status Distribution */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 pb-12 border-b border-[#E5E5E5]">
        {/* Purpose Allocation */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="font-serif text-2xl text-[#191919]">Purpose exposure</h2>
              <p className="text-xs text-[#191919]/60 font-sans mt-0.5">Capital allocation across borrowing purposes</p>
            </div>
            <button
              onClick={() => onNavigate('portfolio')}
              className="text-xs text-[#191919]/70 hover:text-[#191919] font-sans flex items-center space-x-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-4">
            {(data?.charts?.by_purpose || []).map((item) => {
              const maxAmount = Math.max(
                ...(data?.charts?.by_purpose?.map((p) => p.amount) || [1])
              );
              const percentage = Math.round((item.amount / (kpis?.total_disbursed || 1)) * 100);
              return (
                <div key={item.purpose} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-sans">
                    <span className="font-medium text-[#191919]">{item.purpose}</span>
                    <span className="text-[#191919]/60 tabular-nums">
                      ₹{(item.amount / 100000).toFixed(1)} Lakh ({percentage}%)
                    </span>
                  </div>
                  <div className="h-1.5 bg-[#E5E5E5] rounded-sm overflow-hidden">
                    <div
                      className="h-full bg-[#191919] rounded-sm transition-all duration-300"
                      style={{ width: `${Math.min(100, Math.max(5, (item.amount / maxAmount) * 100))}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Underwriting Status Distribution */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="font-serif text-2xl text-[#191919]">Underwriting pipeline</h2>
              <p className="text-xs text-[#191919]/60 font-sans mt-0.5">Application flow and approval statuses</p>
            </div>
            <button
              onClick={() => onNavigate('applications')}
              className="text-xs text-[#191919]/70 hover:text-[#191919] font-sans flex items-center space-x-1"
            >
              <span>Manage</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {(data?.charts?.by_status || []).map((s) => {
              const isApproved = s.status === 'approved';
              const isPending = s.status === 'pending' || s.status === 'review';
              const isRejected = s.status === 'rejected';

              return (
                <div
                  key={s.status}
                  className="p-4 rounded-lg bg-[#F4F3F3] border border-[#E5E5E5] space-y-1"
                >
                  <p className="text-xs font-sans text-[#191919]/60 capitalize">
                    {s.status}
                  </p>
                  <p className="font-serif text-3xl text-[#191919] tabular-nums">{s.count}</p>
                  <div className="pt-2 flex items-center space-x-1.5 text-[11px] font-sans">
                    {isApproved && <CheckCircle2 className="w-3 h-3 text-emerald-700" />}
                    {isPending && <Clock className="w-3 h-3 text-amber-700" />}
                    {isRejected && <XCircle className="w-3 h-3 text-red-700" />}
                    <span className="text-[#191919]/60 tabular-nums">
                      {Math.round((s.count / (kpis?.total_applications || 1)) * 100)}% of total
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6 p-4 rounded-lg border border-[#E5E5E5] bg-white flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded bg-[#191919] text-white flex items-center justify-center">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-medium text-[#191919]">Human underwriting governance</p>
                <p className="text-[11px] text-[#191919]/60">All predictive scores and generated memos require final officer sign-off</p>
              </div>
            </div>
            <button
              onClick={() => onNavigate('applications')}
              className="text-xs font-sans text-[#191919] hover:underline flex items-center space-x-1"
            >
              <span>Review pending</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </section>

      {/* Recent Applications Table */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-serif text-2xl text-[#191919]">Recent applications</h2>
            <p className="text-xs text-[#191919]/60 font-sans mt-0.5">Latest borrower profiles submitted to the credit bureau</p>
          </div>
          <button
            onClick={() => onNavigate('portfolio')}
            className="text-xs text-[#191919] font-medium font-sans flex items-center space-x-1 hover:underline"
          >
            <span>Full portfolio registry</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="border border-[#E5E5E5] rounded-lg overflow-hidden bg-white shadow-subtle">
          <table className="w-full text-left border-collapse text-xs font-sans">
            <thead>
              <tr className="border-b border-[#E5E5E5] bg-[#F4F3F3] text-[#191919]/70 font-medium">
                <th className="py-3 px-4">Borrower</th>
                <th className="py-3 px-4">Credit score</th>
                <th className="py-3 px-4">Loan amount</th>
                <th className="py-3 px-4">Purpose</th>
                <th className="py-3 px-4">ML default risk</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E5E5]">
              {recentApps.map((app) => (
                <tr key={app.application_id} className="hover:bg-[#F4F3F3]/60 transition-colors">
                  <td className="py-3.5 px-4 font-medium text-[#191919]">
                    {app.full_name}
                    <span className="block text-[11px] text-[#191919]/40 font-normal">
                      #{app.application_id} · {app.property_area}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-serif text-sm text-[#191919] tabular-nums">{app.credit_score}</span>
                    <span className="text-[11px] text-[#191919]/50 block">
                      {app.credit_score >= 750 ? 'Prime' : app.credit_score >= 650 ? 'Near-prime' : 'Subprime'}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-medium text-[#191919] tabular-nums">
                    ₹{(app.loan_amount / 100000).toFixed(2)} L
                    <span className="block text-[11px] text-[#191919]/40 font-normal">
                      {app.interest_rate}% · {app.tenure_months}m
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-[#191919]/80">{app.loan_purpose}</td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center space-x-1.5">
                      <span className="font-serif text-sm text-[#191919] tabular-nums">
                        {app.ml_default_probability ? `${app.ml_default_probability}%` : 'N/A'}
                      </span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-sans font-medium ${
                          app.ml_risk_band === 'Low'
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                            : app.ml_risk_band === 'Medium'
                            ? 'bg-amber-50 text-amber-800 border border-amber-200'
                            : 'bg-red-50 text-red-800 border border-red-200'
                        }`}
                      >
                        {app.ml_risk_band || 'Low'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium capitalize ${
                        app.status === 'approved'
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                          : app.status === 'pending'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : 'bg-red-50 text-red-800 border border-red-200'
                      }`}
                    >
                      {app.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => onNavigate('applications')}
                      className="inline-flex items-center space-x-1 text-xs text-[#191919] hover:underline"
                    >
                      <span>Review</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
