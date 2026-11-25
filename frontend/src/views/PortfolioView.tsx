import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { PortfolioData, ApplicationItem } from '../types';
import { BoomerangCanvas } from '../components/BoomerangCanvas';
import {
  ArrowRight,
  Search,
  FileSpreadsheet
} from 'lucide-react';

export const PortfolioView: React.FC = () => {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [purpose, setPurpose] = useState('');
  const [status, setStatus] = useState('');
  const [band, setBand] = useState('');
  const [search, setSearch] = useState('');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const fetchPortfolio = async () => {
    setLoading(true);
    try {
      const res = await api.getPortfolio({
        purpose: purpose || undefined,
        status: status || undefined,
        band: band || undefined,
        search: search || undefined
      });
      setData(res);
      setCurrentPage(1);
    } catch (err: any) {
      setError(err.message || 'Failed to load portfolio registry');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, [purpose, status, band]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPortfolio();
  };

  const exportCSV = () => {
    if (!data?.applications) return;
    const headers = [
      'ID',
      'Borrower',
      'Credit Score',
      'Income',
      'Area',
      'Loan Amount',
      'Purpose',
      'Rate',
      'Tenure',
      'Status',
      'ML Default Prob',
      'Risk Band'
    ];
    const rows = data.applications.map((app) => [
      app.application_id,
      `"${app.full_name}"`,
      app.credit_score,
      app.annual_income,
      app.property_area,
      app.loan_amount,
      `"${app.loan_purpose}"`,
      app.interest_rate,
      app.tenure_months,
      app.status,
      app.ml_default_probability,
      app.ml_risk_band
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `creditpilot_portfolio_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const applications = data?.applications || [];
  const totalPages = Math.ceil(applications.length / pageSize) || 1;
  const paginatedApps = applications.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const kpis = data?.kpis;

  return (
    <div className="space-y-12 pb-16">
      {/* Editorial Header */}
      <section className="relative overflow-hidden pt-6 pb-10 border-b border-[#E5E5E5]">
        <BoomerangCanvas intensity="subtle" />
        <div className="relative z-10 max-w-4xl">
          <p className="text-xs text-[#191919]/60 font-sans mb-2">
            Loan portfolio registry
          </p>
          <h1 className="font-serif text-5xl sm:text-6xl text-[#191919] tracking-tight leading-[1.08] mb-4">
            Portfolio registry
          </h1>
          <p className="text-base text-[#191919]/70 font-sans leading-relaxed max-w-2xl">
            Monitor balance sheet exposure, active accounts and delinquency status across diverse lending categories with institutional audit logging.
          </p>
        </div>

        {/* Action button */}
        <div className="relative z-10 mt-6 flex gap-3">
          <button
            onClick={exportCSV}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded bg-[#191919] text-white text-xs font-sans font-medium hover:bg-[#333333] transition-colors"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Export registry (CSV)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </section>

      {/* KPI Overview Grid */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-8 pb-8 border-b border-[#E5E5E5]">
        <div>
          <p className="text-xs font-sans text-[#191919]/60 mb-1.5">Total book exposure</p>
          <p className="font-serif text-3xl sm:text-4xl text-[#191919] tabular-nums">
            ₹{((kpis?.total_disbursed || 0) / 10000000).toFixed(2)} Cr
          </p>
          <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Approved principal total</p>
        </div>

        <div>
          <p className="text-xs font-sans text-[#191919]/60 mb-1.5">Active accounts</p>
          <p className="font-serif text-3xl sm:text-4xl text-[#191919] tabular-nums">{kpis?.approved_count || 0}</p>
          <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Performing facilities</p>
        </div>

        <div>
          <p className="text-xs font-sans text-[#191919]/60 mb-1.5">Average ticket size</p>
          <p className="font-serif text-3xl sm:text-4xl text-[#191919] tabular-nums">
            ₹{((kpis?.avg_ticket_size || 0) / 100000).toFixed(2)} L
          </p>
          <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Per approved facility</p>
        </div>

        <div>
          <p className="text-xs font-sans text-[#191919]/60 mb-1.5">Weighted yield</p>
          <p className="font-serif text-3xl sm:text-4xl text-[#191919] tabular-nums">{kpis?.weighted_interest_rate || 0}%</p>
          <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Annualized rate</p>
        </div>
      </section>

      {/* Filter and Search Bar */}
      <section className="bg-[#F4F3F3] p-4 rounded-xl border border-[#E5E5E5] flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 min-w-[240px] relative">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by borrower name..."
            className="w-full pl-9 pr-4 py-2 rounded border border-[#E5E5E5] bg-white text-xs font-sans focus:outline-none focus:border-[#191919]"
          />
          <Search className="w-3.5 h-3.5 text-[#191919]/40 absolute left-3 top-2.5" />
        </form>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Purpose Filter */}
          <select
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            className="px-3 py-2 rounded border border-[#E5E5E5] bg-white text-xs font-sans focus:outline-none focus:border-[#191919]"
          >
            <option value="">All purposes</option>
            <option value="Home Loan">Home Loan</option>
            <option value="Home Improvement">Home Improvement</option>
            <option value="Personal Loan">Personal Loan</option>
            <option value="Education Loan">Education Loan</option>
            <option value="Business Loan">Business Loan</option>
            <option value="Debt Consolidation">Debt Consolidation</option>
          </select>

          {/* Status Filter */}
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="px-3 py-2 rounded border border-[#E5E5E5] bg-white text-xs font-sans focus:outline-none focus:border-[#191919]"
          >
            <option value="">All statuses</option>
            <option value="approved">Approved</option>
            <option value="pending">Pending</option>
            <option value="review">Under review</option>
            <option value="rejected">Rejected</option>
          </select>

          {/* Risk Band Filter */}
          <select
            value={band}
            onChange={(e) => setBand(e.target.value)}
            className="px-3 py-2 rounded border border-[#E5E5E5] bg-white text-xs font-sans focus:outline-none focus:border-[#191919]"
          >
            <option value="">All risk bands</option>
            <option value="Low">Low risk</option>
            <option value="Medium">Medium risk</option>
            <option value="High">High risk</option>
          </select>

          {(purpose || status || band || search) && (
            <button
              onClick={() => {
                setPurpose('');
                setStatus('');
                setBand('');
                setSearch('');
              }}
              className="text-xs text-[#191919]/60 hover:text-[#191919] font-sans underline"
            >
              Reset
            </button>
          )}
        </div>
      </section>

      {/* Main Table */}
      <section className="space-y-4">
        <div className="border border-[#E5E5E5] rounded-xl overflow-hidden bg-white shadow-subtle">
          <table className="w-full text-left border-collapse text-xs font-sans">
            <thead>
              <tr className="border-b border-[#E5E5E5] bg-[#F4F3F3] text-[#191919]/70 font-medium">
                <th className="py-3 px-4">Application ID</th>
                <th className="py-3 px-4">Borrower name</th>
                <th className="py-3 px-4">CIBIL</th>
                <th className="py-3 px-4">Loan amount</th>
                <th className="py-3 px-4">Purpose</th>
                <th className="py-3 px-4">Rate & tenure</th>
                <th className="py-3 px-4">ML default risk</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E5E5]">
              {paginatedApps.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-xs text-[#191919]/50 font-sans">
                    No loan applications matching the selected criteria.
                  </td>
                </tr>
              ) : (
                paginatedApps.map((app) => (
                  <tr key={app.application_id} className="hover:bg-[#F4F3F3]/60 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-[11px] text-[#191919]/60 tabular-nums">
                      #{app.application_id}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-[#191919]">
                      {app.full_name}
                      <span className="block text-[11px] text-[#191919]/40 font-normal">
                        {app.property_area} · {app.employment_type}
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
                    </td>
                    <td className="py-3.5 px-4 text-[#191919]/80">{app.loan_purpose}</td>
                    <td className="py-3.5 px-4 text-[#191919]/80 tabular-nums">
                      {app.interest_rate}% · {app.tenure_months}m
                    </td>
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
                            : app.status === 'pending' || app.status === 'review'
                            ? 'bg-amber-50 text-amber-800 border border-amber-200'
                            : 'bg-red-50 text-red-800 border border-red-200'
                        }`}
                      >
                        {app.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between text-xs text-[#191919]/60 font-sans px-2">
          <span className="tabular-nums">
            Showing {(currentPage - 1) * pageSize + 1} –{' '}
            {Math.min(currentPage * pageSize, applications.length)} of {applications.length} applications
          </span>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 rounded border border-[#E5E5E5] bg-white hover:bg-[#F4F3F3] disabled:opacity-40"
            >
              Previous
            </button>
            <span className="px-2 font-serif text-sm text-[#191919] tabular-nums">{currentPage} / {totalPages}</span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 rounded border border-[#E5E5E5] bg-white hover:bg-[#F4F3F3] disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
