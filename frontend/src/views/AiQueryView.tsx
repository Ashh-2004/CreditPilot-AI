import React, { useState } from 'react';
import { api } from '../services/api';
import { BoomerangCanvas } from '../components/BoomerangCanvas';
import {
  ArrowRight,
  AlertCircle,
  ShieldCheck,
  Code
} from 'lucide-react';

export const AiQueryView: React.FC = () => {
  const [prompt, setPrompt] = useState('Show total loans and average amount grouped by purpose');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    status: string;
    generated_sql: string;
    record_count: number;
    results: any[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const QUICK_QUERIES = [
    'Show total loan amount and count by loan purpose',
    'List all applications with default probability above 25%',
    'Count approved and rejected loans grouped by property area',
    'Find top 5 borrowers with highest loan amounts and their CIBIL score'
  ];

  const handleExecuteQuery = async (queryText?: string) => {
    const q = queryText || prompt;
    if (!q.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await api.queryAssistant(q);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Error processing financial analytics query');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const columns = result?.results && result.results.length > 0 ? Object.keys(result.results[0]) : [];

  return (
    <div className="space-y-12 pb-16">
      {/* Editorial Header */}
      <section className="relative overflow-hidden pt-6 pb-10 border-b border-[#E5E5E5]">
        <BoomerangCanvas intensity="subtle" />
        <div className="relative z-10 max-w-4xl">
          <p className="text-xs text-[#191919]/60 font-sans mb-2">
            Natural language financial analytics
          </p>
          <h1 className="font-serif text-5xl sm:text-6xl text-[#191919] tracking-tight leading-[1.08] mb-4">
            SQL assistant
          </h1>
          <p className="text-base text-[#191919]/70 font-sans leading-relaxed max-w-2xl">
            Query the lending database using plain English with rigorous AST-level security verification, read-only permissions and automated schema safeguards.
          </p>
        </div>
      </section>

      {/* Query Input Section */}
      <section className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-4">
        <div>
          <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
            Natural language query
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleExecuteQuery();
              }}
              placeholder="e.g. Show approved loans grouped by purpose with total disbursed amount"
              className="flex-1 px-4 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-xs sm:text-sm font-sans focus:outline-none focus:border-[#191919]"
            />
            <button
              onClick={() => handleExecuteQuery()}
              disabled={loading}
              className="px-6 py-2.5 rounded-lg bg-[#191919] text-white text-xs font-sans font-medium hover:bg-[#333333] transition flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{loading ? 'Synthesizing SQL...' : 'Run query'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Quick query chips */}
        <div className="flex flex-wrap gap-2 pt-1">
          <span className="text-[11px] font-sans text-[#191919]/50 self-center">Quick queries:</span>
          {QUICK_QUERIES.map((q, idx) => (
            <button
              key={idx}
              onClick={() => {
                setPrompt(q);
                handleExecuteQuery(q);
              }}
              className="text-[11px] px-2.5 py-1 rounded bg-[#F4F3F3] hover:bg-[#EAEAEA] text-[#191919]/80 font-sans border border-[#E5E5E5] transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </section>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-xs font-sans text-red-800 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Workspace */}
      {result && (
        <section className="space-y-6">
          {/* Security & SQL Preview Card */}
          <div className="p-6 rounded-xl bg-[#F4F3F3] border border-[#E5E5E5] space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Code className="w-4 h-4 text-[#191919]" />
                <span className="font-serif text-lg text-[#191919]">Verified SQL execution</span>
              </div>
              <div className="flex items-center space-x-1.5 text-[11px] font-sans text-emerald-800 font-medium bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
                <span>AST guard verified</span>
              </div>
            </div>

            <pre className="p-4 rounded-lg bg-white border border-[#E5E5E5] text-xs font-mono text-[#191919] overflow-x-auto">
              {result.generated_sql}
            </pre>

            <div className="flex items-center justify-between text-[11px] text-[#191919]/60 font-sans pt-1">
              <span>Read-only single statement · Clamped at max 100 rows</span>
              <span className="font-medium text-[#191919] tabular-nums">{result.record_count} records returned</span>
            </div>
          </div>

          {/* Results Table */}
          <div className="space-y-3">
            <h3 className="font-serif text-2xl text-[#191919]">Result records</h3>
            <div className="border border-[#E5E5E5] rounded-xl overflow-hidden bg-white shadow-subtle">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs font-sans">
                  <thead>
                    <tr className="border-b border-[#E5E5E5] bg-[#F4F3F3] text-[#191919]/70 font-medium">
                      {columns.map((col) => (
                        <th key={col} className="py-3 px-4 font-medium capitalize">
                          {col.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E5E5E5]">
                    {result.results.length === 0 ? (
                      <tr>
                        <td colSpan={columns.length || 1} className="py-8 text-center text-[#191919]/50">
                          Query returned zero records.
                        </td>
                      </tr>
                    ) : (
                      result.results.map((row, rowIdx) => (
                        <tr key={rowIdx} className="hover:bg-[#F4F3F3]/60 transition-colors">
                          {columns.map((col) => (
                            <td key={col} className="py-3 px-4 text-[#191919] tabular-nums">
                              {typeof row[col] === 'number'
                                ? row[col].toLocaleString('en-IN', { maximumFractionDigits: 2 })
                                : String(row[col] ?? '—')}
                            </td>
                          ))}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};
