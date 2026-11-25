import React, { useState } from 'react';
import { api } from '../services/api';
import { RiskCalculationResult, UnderwritingMemoResult } from '../types';
import { BoomerangCanvas } from '../components/BoomerangCanvas';
import {
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  FileText,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export const ApplicationView: React.FC = () => {
  // Section 1: Borrower Information
  const [name, setName] = useState('Pooja Hegde');
  const [propertyArea, setPropertyArea] = useState('Semi-Urban');
  const [age, setAge] = useState(34);

  // Section 2: Employment & Income
  const [annualIncome, setAnnualIncome] = useState(900000);
  const [employmentType, setEmploymentType] = useState('Salaried');

  // Section 3: Loan Requirements
  const [loanAmount, setLoanAmount] = useState(1500000);
  const [interestRate, setInterestRate] = useState(9.5);
  const [tenureMonths, setTenureMonths] = useState(84);
  const [loanPurpose, setLoanPurpose] = useState('Home Improvement');

  // Section 4: Existing Liabilities
  const [creditScore, setCreditScore] = useState(720);
  const [existingLoans, setExistingLoans] = useState(1);

  // Results State
  const [calculating, setCalculating] = useState(false);
  const [riskResult, setRiskResult] = useState<RiskCalculationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // AI Underwriting Memo State
  const [memoLoading, setMemoLoading] = useState(false);
  const [memoResult, setMemoResult] = useState<UnderwritingMemoResult | null>(null);
  const [memoOpen, setMemoOpen] = useState(false);

  // Section 6: Officer Authorization
  const [officerDecision, setOfficerDecision] = useState<string>('approved');
  const [officerNotes, setOfficerNotes] = useState('Verified KYC and bureau score. Income documents verified.');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const handleCalculateRisk = async (e: React.FormEvent) => {
    e.preventDefault();
    setCalculating(true);
    setError(null);
    setSaveSuccess(null);
    try {
      const res = await api.calculateRisk({
        name,
        loan_amount: Number(loanAmount),
        annual_income: Number(annualIncome),
        employment_type: employmentType,
        property_area: propertyArea,
        existing_loans: Number(existingLoans),
        tenure_months: Number(tenureMonths),
        interest_rate: Number(interestRate),
        loan_purpose: loanPurpose,
        credit_score: Number(creditScore),
      });
      setRiskResult(res);
      setOfficerDecision(res.advisory_status);
    } catch (err: any) {
      setError(err.message || 'Error evaluating credit risk');
    } finally {
      setCalculating(false);
    }
  };

  const handleGenerateMemo = async () => {
    setMemoLoading(true);
    try {
      const res = await api.generateUnderwritingMemo({
        name,
        annual_income: Number(annualIncome),
        credit_score: Number(creditScore),
        employment_type: employmentType,
        existing_loans: Number(existingLoans),
        loan_amount: Number(loanAmount),
        loan_purpose: loanPurpose,
        tenure_months: Number(tenureMonths),
        interest_rate: Number(interestRate),
        approval_probability: 80.0,
        ml_default_probability: riskResult?.ml_prob || 12.5,
        ml_risk_band: riskResult?.ml_band || 'Low'
      });
      setMemoResult(res);
      setMemoOpen(true);
    } catch (err: any) {
      setError('Failed to generate underwriting memorandum.');
    } finally {
      setMemoLoading(false);
    }
  };

  const handleSubmitApplication = async () => {
    setSaving(true);
    setError(null);
    setSaveSuccess(null);
    try {
      const res = await api.submitApplication({
        name,
        loan_amount: Number(loanAmount),
        annual_income: Number(annualIncome),
        employment_type: employmentType,
        property_area: propertyArea,
        existing_loans: Number(existingLoans),
        tenure_months: Number(tenureMonths),
        interest_rate: Number(interestRate),
        loan_purpose: loanPurpose,
        credit_score: Number(creditScore),
        officer_decision: officerDecision,
      });
      setSaveSuccess(`Application #${res.application_id} registered successfully to the credit registry.`);
    } catch (err: any) {
      setError(err.message || 'Error submitting application to database.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-12 pb-16">
      {/* Editorial Header */}
      <section className="relative overflow-hidden pt-6 pb-10 border-b border-[#E5E5E5]">
        <BoomerangCanvas intensity="subtle" />
        <div className="relative z-10 max-w-3xl">
          <p className="text-xs text-[#191919]/60 font-sans mb-2">
            Loan underwriting and intake
          </p>
          <h1 className="font-serif text-5xl sm:text-6xl text-[#191919] tracking-tight leading-[1.08] mb-4">
            Loan applications
          </h1>
          <p className="text-base text-[#191919]/70 font-sans leading-relaxed">
            Manage borrower information and review applications throughout the underwriting process with synchronized institutional risk models.
          </p>
        </div>
      </section>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-xs font-sans text-red-800 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {saveSuccess && (
        <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-xs font-sans text-emerald-800 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{saveSuccess}</span>
        </div>
      )}

      <form onSubmit={handleCalculateRisk} className="space-y-12">
        {/* Section 1: Borrower Information */}
        <div className="pb-8 border-b border-[#E5E5E5]">
          <div className="flex items-center space-x-3 mb-6">
            <span className="font-serif text-xl text-[#191919] tabular-nums">01</span>
            <h2 className="font-serif text-2xl text-[#191919]">Borrower information</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Full legal name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              />
            </div>

            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Property area
              </label>
              <select
                value={propertyArea}
                onChange={(e) => setPropertyArea(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              >
                <option value="Urban">Urban</option>
                <option value="Semi-Urban">Semi-Urban</option>
                <option value="Rural">Rural</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Applicant age
              </label>
              <input
                type="number"
                min={18}
                max={75}
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] tabular-nums focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Employment & Income */}
        <div className="pb-8 border-b border-[#E5E5E5]">
          <div className="flex items-center space-x-3 mb-6">
            <span className="font-serif text-xl text-[#191919] tabular-nums">02</span>
            <h2 className="font-serif text-2xl text-[#191919]">Employment & income</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Employment category
              </label>
              <select
                value={employmentType}
                onChange={(e) => setEmploymentType(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              >
                <option value="Salaried">Salaried (Corporate / PSU)</option>
                <option value="Self-Employed">Self-Employed Professional</option>
                <option value="Business">Business Owner / MSME</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Annual gross income (₹)
              </label>
              <input
                type="number"
                step="50000"
                min="100000"
                value={annualIncome}
                onChange={(e) => setAnnualIncome(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] tabular-nums focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Loan Requirements */}
        <div className="pb-8 border-b border-[#E5E5E5]">
          <div className="flex items-center space-x-3 mb-6">
            <span className="font-serif text-xl text-[#191919] tabular-nums">03</span>
            <h2 className="font-serif text-2xl text-[#191919]">Loan requirements</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Loan amount requested (₹)
              </label>
              <input
                type="number"
                step="50000"
                min="50000"
                value={loanAmount}
                onChange={(e) => setLoanAmount(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] tabular-nums focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              />
            </div>

            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Interest rate (%)
              </label>
              <input
                type="number"
                step="0.25"
                min="5"
                max="25"
                value={interestRate}
                onChange={(e) => setInterestRate(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] tabular-nums focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              />
            </div>

            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Tenure (months)
              </label>
              <input
                type="number"
                step="12"
                min="12"
                max="360"
                value={tenureMonths}
                onChange={(e) => setTenureMonths(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] tabular-nums focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              />
            </div>

            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Loan purpose
              </label>
              <select
                value={loanPurpose}
                onChange={(e) => setLoanPurpose(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              >
                <option value="Home Purchase">Home Purchase</option>
                <option value="Home Improvement">Home Improvement</option>
                <option value="Debt Consolidation">Debt Consolidation</option>
                <option value="Education">Education</option>
                <option value="Business Expansion">Business Expansion</option>
                <option value="Personal">Personal</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 4: Existing Liabilities & Bureau */}
        <div className="pb-8 border-b border-[#E5E5E5]">
          <div className="flex items-center space-x-3 mb-6">
            <span className="font-serif text-xl text-[#191919] tabular-nums">04</span>
            <h2 className="font-serif text-2xl text-[#191919]">Bureau & existing liabilities</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                CIBIL credit score
              </label>
              <input
                type="number"
                min="300"
                max="900"
                value={creditScore}
                onChange={(e) => setCreditScore(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] tabular-nums focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              />
              <span className="text-[11px] text-[#191919]/50 block mt-1">
                Score tier: {creditScore >= 750 ? 'Prime' : creditScore >= 680 ? 'Standard' : 'Subprime watch'}
              </span>
            </div>

            <div>
              <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                Existing active loans
              </label>
              <input
                type="number"
                min="0"
                max="15"
                value={existingLoans}
                onChange={(e) => setExistingLoans(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] tabular-nums focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
              />
            </div>
          </div>

          <div className="pt-6">
            <button
              type="submit"
              disabled={calculating}
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-lg bg-[#191919] text-white text-xs font-medium font-sans hover:bg-[#333333] transition-colors disabled:opacity-50"
            >
              <span>{calculating ? 'Running underwriting engine...' : 'Evaluate credit & risk profile'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </form>

      {/* Section 5: Underwriting & Risk Advisory Results */}
      {riskResult && (
        <section className="p-8 rounded-xl bg-[#F4F3F3] border border-[#E5E5E5] space-y-8">
          <div className="flex items-center space-x-3">
            <span className="font-serif text-xl text-[#191919] tabular-nums">05</span>
            <div>
              <h2 className="font-serif text-2xl text-[#191919]">Underwriting advisory output</h2>
              <p className="text-xs text-[#191919]/60 font-sans mt-0.5">
                Predictive default modeling and institutional rule score
              </p>
            </div>
          </div>

          {/* Metric Quad */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 bg-white p-6 rounded-lg border border-[#E5E5E5]">
            <div>
              <p className="text-xs font-sans text-[#191919]/60 mb-1">Calculated EMI</p>
              <p className="font-serif text-2xl sm:text-3xl text-[#191919] tabular-nums">
                ₹{riskResult.emi.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </p>
              <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Per month</p>
            </div>

            <div>
              <p className="text-xs font-sans text-[#191919]/60 mb-1">Debt burden (DTI)</p>
              <p className="font-serif text-2xl sm:text-3xl text-[#191919] tabular-nums">{riskResult.emi_ratio}%</p>
              <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">
                Cap: {riskResult.emi_ratio <= 45 ? 'Compliant' : 'Elevated'}
              </p>
            </div>

            <div>
              <p className="text-xs font-sans text-[#191919]/60 mb-1">Rule-based score</p>
              <p className="font-serif text-2xl sm:text-3xl text-[#191919] tabular-nums">{riskResult.risk_score} / 100</p>
              <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Scorecard threshold: 50</p>
            </div>

            <div>
              <p className="text-xs font-sans text-[#191919]/60 mb-1">ML default risk</p>
              <div className="flex items-center space-x-2">
                <p className="font-serif text-2xl sm:text-3xl text-[#191919] tabular-nums">{riskResult.ml_prob}%</p>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                    riskResult.ml_band === 'Low'
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : riskResult.ml_band === 'Medium'
                      ? 'bg-amber-50 text-amber-800 border border-amber-200'
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}
                >
                  {riskResult.ml_band} risk
                </span>
              </div>
              <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Supervised XGBoost model</p>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-white border border-[#E5E5E5] space-y-1.5 text-xs font-sans">
            <p className="font-medium text-[#191919]">Engine recommendation</p>
            <p className="text-[#191919]/80 leading-relaxed">{riskResult.recommendation}</p>
            <p className="text-[11px] text-[#191919]/50 pt-1">{riskResult.disclaimer}</p>
          </div>

          {/* Underwriting Memo Generator Expander */}
          <div className="border border-[#E5E5E5] rounded-lg bg-white overflow-hidden">
            <div className="p-4 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded bg-[#191919] text-white flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-serif text-lg text-[#191919]">Underwriting memorandum</h3>
                  <p className="text-xs text-[#191919]/60 font-sans mt-0.5">
                    Synthesizes policy guidelines and borrower factors into an executive memo
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={handleGenerateMemo}
                  disabled={memoLoading}
                  className="px-3.5 py-1.5 rounded bg-[#191919] text-white text-xs font-sans font-medium hover:bg-[#333333] transition-colors disabled:opacity-50"
                >
                  {memoLoading ? 'Synthesizing policy...' : memoResult ? 'Re-generate' : 'Generate memo'}
                </button>
                {memoResult && (
                  <button
                    type="button"
                    onClick={() => setMemoOpen(!memoOpen)}
                    className="p-1.5 text-[#191919]/60 hover:text-[#191919]"
                  >
                    {memoOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                )}
              </div>
            </div>

            {memoResult && memoOpen && (
              <div className="p-6 border-t border-[#E5E5E5] bg-[#F4F3F3]/50 space-y-4">
                <div className="prose prose-sm max-w-none text-[#191919] font-sans whitespace-pre-line text-xs leading-relaxed">
                  {memoResult.memorandum}
                </div>
                <div className="pt-3 border-t border-[#E5E5E5] text-[11px] text-[#191919]/50">
                  {memoResult.disclaimer}
                </div>
              </div>
            )}
          </div>

          {/* Section 6: Officer Final Decision & Registry Persistence */}
          <div className="pt-6 border-t border-[#E5E5E5] space-y-4">
            <div className="flex items-center space-x-3 mb-2">
              <span className="font-serif text-xl text-[#191919] tabular-nums">06</span>
              <h2 className="font-serif text-2xl text-[#191919]">Officer authorization & registry save</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-white p-6 rounded-lg border border-[#E5E5E5]">
              <div>
                <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                  Official decision sign-off
                </label>
                <select
                  value={officerDecision}
                  onChange={(e) => setOfficerDecision(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
                >
                  <option value="approved">Approved — Proceed to Sanction Letter</option>
                  <option value="review">Underwriting Review — Request Co-applicant / Collateral</option>
                  <option value="rejected">Rejected — Adverse Credit Profile</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-sans font-medium text-[#191919]/70 mb-1.5">
                  Officer notes & justification
                </label>
                <input
                  type="text"
                  value={officerNotes}
                  onChange={(e) => setOfficerNotes(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E5E5] bg-white text-sm font-sans text-[#191919] focus:outline-none focus:border-[#191919] focus:ring-1 focus:ring-[#191919]"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={handleSubmitApplication}
                disabled={saving}
                className="inline-flex items-center space-x-2 px-6 py-3 rounded-lg bg-[#191919] text-white text-xs font-medium font-sans hover:bg-[#333333] transition-colors disabled:opacity-50"
              >
                <span>{saving ? 'Registering application...' : 'Record decision to registry'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};
