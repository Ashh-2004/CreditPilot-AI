import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ApplicationItem, UnderwritingMemoResult, PolicyQueryResult } from '../types';
import { BoomerangCanvas } from '../components/BoomerangCanvas';
import {
  ArrowRight,
  BookOpen,
  FileText,
  Search,
  Copy,
  Check,
  AlertCircle,
  RefreshCw
} from 'lucide-react';

// Helper to format inline markdown bold (**bold**) cleanly
function formatInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-[#191919]">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

// Lightweight, crash-proof markdown renderer for underwriting memos
function MarkdownMemo({ content }: { content: string }) {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = (keyPrefix: number) => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${keyPrefix}`} className="space-y-1.5 my-2.5 pl-4 list-disc marker:text-[#191919]/50 text-xs text-[#191919]/80 leading-relaxed">
          {listItems.map((item, idx) => (
            <li key={idx}>{formatInline(item)}</li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trim();

    // Check if line is a bullet item
    if (line.startsWith('* ') || line.startsWith('- ')) {
      listItems.push(line.slice(2));
      return;
    }

    // Flush any ongoing bullet list
    flushList(idx);

    if (!line) {
      return;
    }

    if (line.startsWith('### ')) {
      elements.push(
        <h4 key={idx} className="font-sans font-semibold text-xs text-[#191919] uppercase tracking-wider mt-4 mb-1.5">
          {line.slice(4)}
        </h4>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h3 key={idx} className="font-serif text-lg text-[#191919] font-medium mt-6 mb-2 pt-2 border-b border-[#E5E5E5] pb-1">
          {line.slice(3)}
        </h3>
      );
    } else if (line.startsWith('# ')) {
      elements.push(
        <h2 key={idx} className="font-serif text-2xl text-[#191919] font-normal mt-4 mb-2">
          {line.slice(2)}
        </h2>
      );
    } else if (line === '---' || line === '***') {
      elements.push(<hr key={idx} className="border-[#E5E5E5] my-4" />);
    } else if (line.startsWith('> ')) {
      elements.push(
        <blockquote key={idx} className="p-3 my-3 border-l-2 border-[#191919] bg-[#F4F3F3] text-[11px] text-[#191919]/70 leading-relaxed font-sans rounded-r">
          {formatInline(line.slice(2))}
        </blockquote>
      );
    } else {
      elements.push(
        <p key={idx} className="text-xs sm:text-sm text-[#191919]/80 leading-relaxed mb-2.5 font-sans">
          {formatInline(line)}
        </p>
      );
    }
  });

  flushList(lines.length);

  return <div className="space-y-1">{elements}</div>;
}

export const AiAnalystView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'memo' | 'policy'>('memo');

  // Application selection for Memo
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);
  const [selectedApp, setSelectedApp] = useState<ApplicationItem | null>(null);

  // Memo generation state
  const [memoLoading, setMemoLoading] = useState(false);
  const [memoError, setMemoError] = useState<string | null>(null);
  const [memoResult, setMemoResult] = useState<UnderwritingMemoResult | null>(null);
  const [copied, setCopied] = useState(false);

  // Policy Research state
  const [policyQuery, setPolicyQuery] = useState('');
  const [policyLoading, setPolicyLoading] = useState(false);
  const [policyResult, setPolicyResult] = useState<PolicyQueryResult | null>(null);

  // Load existing applications
  useEffect(() => {
    api.getPortfolio()
      .then((res) => {
        setApplications(res.applications || []);
        if (res.applications && res.applications.length > 0) {
          setSelectedAppId(res.applications[0].application_id);
          setSelectedApp(res.applications[0]);
        }
      })
      .catch((e) => console.error(e));
  }, []);

  const handleSelectApp = (id: number) => {
    setSelectedAppId(id);
    const found = applications.find((a) => a.application_id === id);
    if (found) setSelectedApp(found);
    setMemoError(null);
    setMemoResult(null);
  };

  const handleGenerateMemo = async () => {
    if (!selectedApp) return;
    setMemoLoading(true);
    setMemoError(null);
    try {
      const res = await api.generateUnderwritingMemo({
        name: selectedApp.full_name,
        annual_income: selectedApp.annual_income,
        credit_score: selectedApp.credit_score,
        employment_type: selectedApp.employment_type,
        existing_loans: 1,
        loan_amount: selectedApp.loan_amount,
        loan_purpose: selectedApp.loan_purpose,
        tenure_months: selectedApp.tenure_months,
        interest_rate: selectedApp.interest_rate,
        approval_probability: selectedApp.approval_probability,
        ml_default_probability: selectedApp.ml_default_probability,
        ml_risk_band: selectedApp.ml_risk_band
      });
      setMemoResult(res);
    } catch (err: any) {
      console.error(err);
      setMemoError(err?.message || 'Failed to synthesize underwriting memorandum. Please check network connection.');
    } finally {
      setMemoLoading(false);
    }
  };

  const handleCopyMemo = () => {
    if (!memoResult?.memorandum) return;
    navigator.clipboard.writeText(memoResult.memorandum);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePolicyQuery = async (queryText?: string) => {
    const q = queryText || policyQuery;
    if (!q.trim()) return;
    setPolicyLoading(true);
    try {
      const res = await api.queryPolicy({ query: q });
      setPolicyResult(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setPolicyLoading(false);
    }
  };

  const QUICK_QUESTIONS = [
    'What is the maximum allowed DTI for salaried borrowers?',
    'What are the eligibility conditions for debt consolidation loans?',
    'When is a co-applicant or guarantor mandatory?',
    'What is the escalation threshold for subprime credit scores below 650?'
  ];

  return (
    <div className="space-y-8 pb-16">
      {/* Editorial Header */}
      <section className="relative overflow-hidden pt-4 pb-6 border-b border-[#E5E5E5]">
        <BoomerangCanvas intensity="subtle" />
        <div className="relative z-10 max-w-4xl">
          <p className="text-xs text-[#191919]/60 font-sans mb-1.5">
            Underwriting intelligence and policy research
          </p>
          <h1 className="font-serif text-4xl sm:text-5xl text-[#191919] tracking-tight leading-[1.1] mb-2.5">
            Intelligence for better underwriting
          </h1>
          <p className="text-xs sm:text-sm text-[#191919]/70 font-sans leading-relaxed max-w-2xl">
            Understand borrower strengths, identify vulnerabilities and review policy-grounded lending insights with generative AI and deterministic RAG policy retrieval.
          </p>
        </div>

        {/* Tab switch */}
        <div className="relative z-10 flex gap-2 mt-5 pt-4 border-t border-[#E5E5E5]">
          <button
            onClick={() => setActiveTab('memo')}
            className={`px-3.5 py-1.5 rounded text-xs font-sans font-medium transition-colors ${
              activeTab === 'memo'
                ? 'bg-[#191919] text-white'
                : 'bg-[#F4F3F3] text-[#191919]/70 hover:text-[#191919] border border-[#E5E5E5]'
            }`}
          >
            Underwriting memorandum
          </button>
          <button
            onClick={() => setActiveTab('policy')}
            className={`px-3.5 py-1.5 rounded text-xs font-sans font-medium transition-colors ${
              activeTab === 'policy'
                ? 'bg-[#191919] text-white'
                : 'bg-[#F4F3F3] text-[#191919]/70 hover:text-[#191919] border border-[#E5E5E5]'
            }`}
          >
            Policy knowledge assistant
          </button>
        </div>
      </section>

      {/* SUB-VIEW 1: UNDERWRITING MEMORANDUM GENERATOR */}
      {activeTab === 'memo' && (
        <section className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Selection Column */}
            <div className="lg:col-span-4 space-y-4">
              <div className="p-5 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="font-serif text-lg text-[#191919]">Borrower profile</h2>
                  <span className="text-[11px] text-[#191919]/50 font-sans tabular-nums">
                    {applications.length} applicants
                  </span>
                </div>

                {/* Primary Action Button (Placed right at the top for immediate access) */}
                <button
                  type="button"
                  onClick={handleGenerateMemo}
                  disabled={memoLoading || !selectedApp}
                  className="w-full py-2.5 px-4 rounded-lg bg-[#191919] text-white text-xs font-sans font-medium hover:bg-[#333333] transition flex items-center justify-center space-x-2 disabled:opacity-50 shadow-sm"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>{memoLoading ? 'Synthesizing memo...' : 'Generate underwriting memo'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                {/* Compact Applicant List */}
                <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1 border border-[#E5E5E5] rounded-lg p-1.5 bg-[#FAFAFA]">
                  {applications.map((app) => (
                    <button
                      key={app.application_id}
                      onClick={() => handleSelectApp(app.application_id)}
                      className={`w-full text-left p-2.5 rounded-md border text-xs font-sans transition-colors ${
                        selectedAppId === app.application_id
                          ? 'border-[#191919] bg-white shadow-xs'
                          : 'border-transparent hover:bg-white/80'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-0.5">
                        <span className="font-medium text-[#191919] truncate mr-2">{app.full_name}</span>
                        <span className="text-[10px] text-[#191919]/50 tabular-nums">#{app.application_id}</span>
                      </div>
                      <div className="flex justify-between text-[11px] text-[#191919]/60">
                        <span className="tabular-nums">₹{(app.loan_amount / 100000).toFixed(1)}L · {app.loan_purpose}</span>
                        <span className="font-serif tabular-nums">CIBIL {app.credit_score}</span>
                      </div>
                    </button>
                  ))}
                </div>

                {/* Selected Applicant Summary */}
                {selectedApp && (
                  <div className="p-3 rounded-lg bg-[#F4F3F3] border border-[#E5E5E5] space-y-2 text-xs font-sans">
                    <div className="flex justify-between items-center pb-1.5 border-b border-[#E5E5E5]">
                      <span className="font-medium text-[#191919]">{selectedApp.full_name}</span>
                      <span className="text-[10px] text-[#191919]/60 capitalize">{selectedApp.employment_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#191919]/60">Annual income</span>
                      <span className="font-medium tabular-nums">₹{(selectedApp.annual_income / 100000).toFixed(1)} Lakh</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#191919]/60">Facility amount</span>
                      <span className="font-medium tabular-nums">₹{(selectedApp.loan_amount / 100000).toFixed(1)} Lakh</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#191919]/60">Default risk probability</span>
                      <span className="font-serif font-medium text-[#191919] tabular-nums">
                        {selectedApp.ml_default_probability ? `${selectedApp.ml_default_probability}%` : 'Low'}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right Memorandum Document Column */}
            <div className="lg:col-span-8">
              {memoLoading ? (
                <div className="p-16 rounded-xl bg-white border border-[#E5E5E5] flex flex-col items-center justify-center space-y-4 min-h-[380px]">
                  <div className="w-7 h-7 border-2 border-[#191919] border-t-transparent rounded-full animate-spin"></div>
                  <div className="text-center space-y-1">
                    <p className="text-sm font-medium font-sans text-[#191919]">
                      Synthesizing underwriting memorandum...
                    </p>
                    <p className="text-xs font-sans text-[#191919]/60 max-w-md">
                      Retrieving institutional credit policies and generating executive commentary. This usually takes 5-10 seconds.
                    </p>
                  </div>
                </div>
              ) : memoError ? (
                <div className="p-10 rounded-xl bg-white border border-red-200 flex flex-col items-center justify-center space-y-4 text-center">
                  <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center text-red-600">
                    <AlertCircle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-serif text-lg text-[#191919]">Memorandum synthesis failed</h3>
                    <p className="text-xs text-[#191919]/60 font-sans mt-1 max-w-sm">
                      {memoError}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleGenerateMemo}
                    className="px-4 py-2 rounded-lg bg-[#191919] text-white text-xs font-sans font-medium hover:bg-[#333333] transition flex items-center space-x-2"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Try again</span>
                  </button>
                </div>
              ) : memoResult ? (
                <div className="p-8 sm:p-10 rounded-xl bg-white border border-[#E5E5E5] shadow-card space-y-6">
                  {/* Memorandum Header */}
                  <div className="border-b border-[#E5E5E5] pb-6 flex items-start justify-between">
                    <div>
                      <p className="text-[11px] font-sans text-[#191919]/50 mb-1">
                        Confidential credit committee memorandum
                      </p>
                      <h2 className="font-serif text-3xl text-[#191919]">
                        {selectedApp?.full_name}
                      </h2>
                      <p className="text-xs text-[#191919]/60 font-sans mt-0.5">
                        Application #{selectedApp?.application_id} · Facility: ₹{selectedApp ? (selectedApp.loan_amount / 100000).toFixed(1) : ''}L {selectedApp?.loan_purpose}
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={handleCopyMemo}
                        className="p-2 rounded-lg border border-[#E5E5E5] bg-[#F4F3F3] text-xs text-[#191919] hover:bg-[#EAEAEA] transition flex items-center space-x-1.5"
                        title="Copy memorandum text"
                      >
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                        <span className="text-[11px] font-medium">{copied ? 'Copied' : 'Copy'}</span>
                      </button>

                      <span className="px-2.5 py-1 rounded bg-[#F4F3F3] border border-[#E5E5E5] text-[11px] font-sans text-[#191919]">
                        Source: {memoResult.source}
                      </span>
                    </div>
                  </div>

                  {/* Formatted Memorandum Content */}
                  <div className="text-[#191919]">
                    <MarkdownMemo content={memoResult.memorandum} />
                  </div>

                  {/* Retrieved Policy Clauses */}
                  {memoResult.retrieved_clauses && memoResult.retrieved_clauses.length > 0 && (
                    <div className="pt-6 border-t border-[#E5E5E5] space-y-2">
                      <p className="text-xs font-sans font-medium text-[#191919]/70">
                        Applicable institutional policy clauses
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {memoResult.retrieved_clauses.map((clause, idx) => (
                          <span
                            key={idx}
                            className="text-[11px] px-2 py-0.5 rounded bg-[#F4F3F3] border border-[#E5E5E5] text-[#191919]/70 font-mono"
                          >
                            {clause}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Mandatory Legal Disclaimer */}
                  <div className="p-3.5 rounded-lg bg-[#F4F3F3] border border-[#E5E5E5] text-[11px] text-[#191919]/60 font-sans">
                    {memoResult.disclaimer}
                  </div>
                </div>
              ) : (
                /* Empty state with prominent primary action button */
                <div className="p-12 sm:p-16 rounded-xl bg-[#F4F3F3] border border-[#E5E5E5] text-center space-y-4 min-h-[360px] flex flex-col items-center justify-center">
                  <div className="w-12 h-12 rounded-full bg-white border border-[#E5E5E5] flex items-center justify-center text-[#191919]/60 shadow-xs">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="font-serif text-2xl text-[#191919]">No memorandum generated yet</h3>
                    <p className="text-xs text-[#191919]/60 font-sans max-w-md mx-auto leading-relaxed">
                      Synthesize an executive underwriting memorandum for {selectedApp?.full_name ? <strong className="text-[#191919]">{selectedApp.full_name}</strong> : 'the selected applicant'} grounded in institutional credit policies and borrower metrics.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={handleGenerateMemo}
                    disabled={memoLoading || !selectedApp}
                    className="mt-2 px-5 py-2.5 rounded-lg bg-[#191919] text-white text-xs font-sans font-medium hover:bg-[#333333] transition inline-flex items-center space-x-2 shadow-sm disabled:opacity-50"
                  >
                    <FileText className="w-4 h-4" />
                    <span>Generate memorandum for {selectedApp ? selectedApp.full_name : 'selected applicant'}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* SUB-VIEW 2: RAG POLICY KNOWLEDGE ASSISTANT */}
      {activeTab === 'policy' && (
        <section className="space-y-8 max-w-4xl mx-auto">
          <div>
            <h2 className="font-serif text-3xl text-[#191919]">Credit policy research</h2>
            <p className="text-xs text-[#191919]/60 font-sans mt-0.5">
              Search institutional credit underwriting policies, DTI caps, LTV rules, and risk escalation clauses
            </p>
          </div>

          {/* Search Box */}
          <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-4">
            <div className="relative">
              <input
                type="text"
                value={policyQuery}
                onChange={(e) => setPolicyQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handlePolicyQuery();
                }}
                placeholder="Ask an underwriting policy question (e.g. What is the maximum DTI for home loans?)"
                className="w-full pl-10 pr-24 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-xs sm:text-sm font-sans focus:outline-none focus:border-[#191919]"
              />
              <Search className="w-4 h-4 text-[#191919]/40 absolute left-3.5 top-3" />
              <button
                type="button"
                onClick={() => handlePolicyQuery()}
                disabled={policyLoading}
                className="absolute right-1.5 top-1.5 px-3 py-1.5 rounded bg-[#191919] text-white text-xs font-sans font-medium hover:bg-[#333333] transition disabled:opacity-50"
              >
                {policyLoading ? 'Searching...' : 'Search'}
              </button>
            </div>

            {/* Quick Question Chips */}
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="text-[11px] font-sans text-[#191919]/50 self-center">Example queries:</span>
              {QUICK_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setPolicyQuery(q);
                    handlePolicyQuery(q);
                  }}
                  className="text-[11px] px-2.5 py-1 rounded bg-[#F4F3F3] hover:bg-[#EAEAEA] text-[#191919]/80 font-sans border border-[#E5E5E5] transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Policy Results */}
          {policyResult && (
            <div className="space-y-6">
              {/* Synthesized Guidance */}
              <div className="p-8 rounded-xl bg-white border border-[#E5E5E5] shadow-card space-y-4">
                <div className="flex items-center space-x-2">
                  <BookOpen className="w-4 h-4 text-[#191919]" />
                  <h3 className="font-serif text-2xl text-[#191919]">Policy guidance synthesis</h3>
                </div>
                <div className="prose prose-sm max-w-none text-[#191919] font-sans whitespace-pre-line text-xs sm:text-sm leading-relaxed">
                  {policyResult.synthesis}
                </div>
              </div>

              {/* Referenced Raw Clauses */}
              <div className="space-y-4">
                <h3 className="font-serif text-xl text-[#191919]">Referenced institutional clauses</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {policyResult.clauses.map((clause) => (
                    <div
                      key={clause.clause_id}
                      className="p-5 rounded-lg bg-[#F4F3F3] border border-[#E5E5E5] space-y-2 text-xs font-sans"
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-[11px] font-medium text-[#191919]">
                          {clause.clause_id}
                        </span>
                        <span className="text-[11px] text-[#191919]/50 font-medium capitalize">
                          {clause.category}
                        </span>
                      </div>
                      <h4 className="font-medium text-sm text-[#191919]">{clause.title}</h4>
                      <p className="text-[#191919]/80 leading-relaxed">{clause.rule_text}</p>
                      <div className="pt-2 border-t border-[#E5E5E5] text-[11px] text-[#191919]/60">
                        <span className="font-medium text-[#191919]">Guidance: </span>
                        {clause.guidance}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-[#F4F3F3] border border-[#E5E5E5] text-[11px] text-[#191919]/60 font-sans">
                {policyResult.disclaimer}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
};
