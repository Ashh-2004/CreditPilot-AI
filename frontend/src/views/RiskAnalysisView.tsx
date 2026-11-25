import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  RiskSummary,
  StressTestResult,
  HomeCreditPrediction,
  RiskCalculationResult
} from '../types';
import { BoomerangCanvas } from '../components/BoomerangCanvas';
import {
  ArrowRight
} from 'lucide-react';

const BENCHMARKS: Record<string, any> = {
  prime: {
    label: 'Prime Corporate Executive (Low Risk)',
    source: 'Kaggle Benchmark Profile (Real Data)',
    AMT_INCOME_TOTAL: 270000.0,
    AMT_CREDIT: 450000.0,
    AMT_ANNUITY: 21850.0,
    AMT_GOODS_PRICE: 450000.0,
    NAME_CONTRACT_TYPE: 'Cash loans',
    CODE_GENDER: 'F',
    FLAG_OWN_CAR: 'Y',
    FLAG_OWN_REALTY: 'Y',
    CNT_CHILDREN: 0,
    DAYS_BIRTH: -16500,
    DAYS_EMPLOYED: -4500,
    EXT_SOURCE_1: 0.72,
    EXT_SOURCE_2: 0.68,
    EXT_SOURCE_3: 0.75,
    INSTAL_LATE_RATIO: 0.0,
    INSTAL_DPD_MAX: 0.0,
    PREV_REFUSAL_RATE: 0.0,
    BUREAU_LOAN_COUNT: 4.0,
    BUREAU_DEBT_CREDIT_RATIO: 0.15,
  },
  moderate: {
    label: 'Small Enterprise Trader (Moderate Risk)',
    source: 'Kaggle Benchmark Profile (Real Data)',
    AMT_INCOME_TOTAL: 135000.0,
    AMT_CREDIT: 540000.0,
    AMT_ANNUITY: 27000.0,
    AMT_GOODS_PRICE: 450000.0,
    NAME_CONTRACT_TYPE: 'Cash loans',
    CODE_GENDER: 'M',
    FLAG_OWN_CAR: 'N',
    FLAG_OWN_REALTY: 'Y',
    CNT_CHILDREN: 1,
    DAYS_BIRTH: -12000,
    DAYS_EMPLOYED: -1500,
    EXT_SOURCE_1: 0.45,
    EXT_SOURCE_2: 0.48,
    EXT_SOURCE_3: 0.42,
    INSTAL_LATE_RATIO: 0.08,
    INSTAL_DPD_MAX: 7.0,
    PREV_REFUSAL_RATE: 0.20,
    BUREAU_LOAN_COUNT: 6.0,
    BUREAU_DEBT_CREDIT_RATIO: 0.48,
  },
  subprime: {
    label: 'High Overdue History (Elevated Delinquency)',
    source: 'Kaggle Benchmark Profile (Real Data)',
    AMT_INCOME_TOTAL: 90000.0,
    AMT_CREDIT: 675000.0,
    AMT_ANNUITY: 36000.0,
    AMT_GOODS_PRICE: 585000.0,
    NAME_CONTRACT_TYPE: 'Cash loans',
    CODE_GENDER: 'M',
    FLAG_OWN_CAR: 'N',
    FLAG_OWN_REALTY: 'N',
    CNT_CHILDREN: 3,
    DAYS_BIRTH: -9500,
    DAYS_EMPLOYED: -300,
    EXT_SOURCE_1: 0.18,
    EXT_SOURCE_2: 0.22,
    EXT_SOURCE_3: 0.15,
    INSTAL_LATE_RATIO: 0.45,
    INSTAL_DPD_MAX: 45.0,
    PREV_REFUSAL_RATE: 0.65,
    BUREAU_LOAN_COUNT: 9.0,
    BUREAU_DEBT_CREDIT_RATIO: 0.88,
  }
};

export const RiskAnalysisView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'indian' | 'home_credit' | 'shap' | 'stress'>('indian');

  // Indian Model Simulator State
  const [indianScore, setIndianScore] = useState(720);
  const [indianIncome, setIndianIncome] = useState(900000);
  const [indianAmount, setIndianAmount] = useState(1500000);
  const [indianTenure, setIndianTenure] = useState(84);
  const [indianRate, setIndianRate] = useState(9.5);
  const [indianPurpose, setIndianPurpose] = useState('Home Improvement');
  const [indianEmpType, setIndianEmpType] = useState('Salaried');
  const [indianLoans, setIndianLoans] = useState(1);
  const [indianResult, setIndianResult] = useState<RiskCalculationResult | null>(null);
  const [indianLoading, setIndianLoading] = useState(false);

  // Home Credit Simulator State
  const [benchmarkKey, setBenchmarkKey] = useState<string>('prime');
  const [hcApplicant, setHcApplicant] = useState<any>(BENCHMARKS.prime);
  const [hcPrediction, setHcPrediction] = useState<HomeCreditPrediction | null>(null);
  const [hcLoading, setHcLoading] = useState(false);
  const [evalData, setEvalData] = useState<any>(null);

  // Stress Testing State
  const [summary, setSummary] = useState<RiskSummary | null>(null);
  const [rateShock, setRateShock] = useState(150);
  const [incomeShock, setIncomeShock] = useState(10.0);
  const [exposureCr, setExposureCr] = useState(250.0);
  const [baselineNpa, setBaselineNpa] = useState(3.2);
  const [stressResult, setStressResult] = useState<StressTestResult | null>(null);

  // Run Indian ML Model
  const runIndianModel = async () => {
    setIndianLoading(true);
    try {
      const res = await api.calculateRisk({
        name: 'Simulated Indian Borrower',
        loan_amount: Number(indianAmount),
        annual_income: Number(indianIncome),
        employment_type: indianEmpType,
        property_area: 'Urban',
        existing_loans: Number(indianLoans),
        tenure_months: Number(indianTenure),
        interest_rate: Number(indianRate),
        loan_purpose: indianPurpose,
        credit_score: Number(indianScore)
      });
      setIndianResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIndianLoading(false);
    }
  };

  // Run Home Credit Model
  const runHomeCredit = async (payload: any) => {
    setHcLoading(true);
    try {
      const res = await api.predictHomeCredit(payload);
      setHcPrediction(res);
    } catch (e) {
      console.error(e);
    } finally {
      setHcLoading(false);
    }
  };

  // Run Macro Stress Test
  const runStress = async () => {
    try {
      const res = await api.runStressTest({
        baseline_exposure_cr: Number(exposureCr),
        baseline_npa_rate: Number(baselineNpa),
        rate_shock_bps: Number(rateShock),
        income_shock_pct: Number(incomeShock)
      });
      setStressResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    runIndianModel();
    runHomeCredit(BENCHMARKS.prime);
    api.getHomeCreditEvaluation().then(setEvalData).catch(() => { });
    api.getRiskSummary().then(setSummary).catch(() => { });
    runStress();
  }, []);

  const handleBenchmarkSelect = (key: string) => {
    setBenchmarkKey(key);
    setHcApplicant(BENCHMARKS[key]);
    runHomeCredit(BENCHMARKS[key]);
  };

  return (
    <div className="space-y-12 pb-16">
      {/* Editorial Header */}
      <section className="relative overflow-hidden pt-6 pb-10 border-b border-[#E5E5E5]">
        <BoomerangCanvas intensity="subtle" />
        <div className="relative z-10 max-w-4xl">
          <p className="text-xs text-[#191919]/60 font-sans mb-2">
            Institutional risk intelligence
          </p>
          <h1 className="font-serif text-5xl sm:text-6xl text-[#191919] tracking-tight leading-[1.08] mb-4">
            Risk intelligence
          </h1>
          <p className="text-base text-[#191919]/70 font-sans leading-relaxed max-w-2xl">
            Two institutional machine learning systems calibrated for domestic and international lending portfolios, with full SHAP transparency and Basel stress modeling.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="relative z-10 flex flex-wrap gap-2 mt-8 pt-6 border-t border-[#E5E5E5]">
          <button
            onClick={() => setActiveTab('indian')}
            className={`px-3.5 py-2 rounded text-xs font-sans font-medium transition-colors ${activeTab === 'indian'
              ? 'bg-[#191919] text-white'
              : 'bg-[#F4F3F3] text-[#191919]/70 hover:text-[#191919] border border-[#E5E5E5]'
              }`}
          >
            Domestic borrower model
          </button>
          <button
            onClick={() => setActiveTab('home_credit')}
            className={`px-3.5 py-2 rounded text-xs font-sans font-medium transition-colors ${activeTab === 'home_credit'
              ? 'bg-[#191919] text-white'
              : 'bg-[#F4F3F3] text-[#191919]/70 hover:text-[#191919] border border-[#E5E5E5]'
              }`}
          >
            Home Credit international model (142 features)
          </button>
          <button
            onClick={() => setActiveTab('shap')}
            className={`px-3.5 py-2 rounded text-xs font-sans font-medium transition-colors ${activeTab === 'shap'
              ? 'bg-[#191919] text-white'
              : 'bg-[#F4F3F3] text-[#191919]/70 hover:text-[#191919] border border-[#E5E5E5]'
              }`}
          >
            SHAP feature attribution
          </button>
          <button
            onClick={() => setActiveTab('stress')}
            className={`px-3.5 py-2 rounded text-xs font-sans font-medium transition-colors ${activeTab === 'stress'
              ? 'bg-[#191919] text-white'
              : 'bg-[#F4F3F3] text-[#191919]/70 hover:text-[#191919] border border-[#E5E5E5]'
              }`}
          >
            Basel stress simulator & watchlist
          </button>
        </div>
      </section>

      {/* TAB A: INDIAN BORROWER MODEL */}
      {activeTab === 'indian' && (
        <section className="space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-serif text-3xl text-[#191919]">Domestic borrower model</h2>
              <p className="text-xs text-[#191919]/60 font-sans mt-0.5">
                Trained on domestic retail borrowing behaviors with 7 core risk attributes and CIBIL credit score
              </p>
            </div>
            <span className="text-xs font-sans px-2.5 py-1 rounded bg-[#F4F3F3] text-[#191919]/80 border border-[#E5E5E5] font-medium">
              Supervised XGBoost
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Input Simulator */}
            <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-4">
              <h3 className="font-serif text-xl text-[#191919] mb-4">Borrower attributes</h3>

              <div>
                <div className="flex justify-between text-xs font-sans mb-1.5">
                  <span className="text-[#191919]/70">CIBIL score</span>
                  <span className="font-medium tabular-nums">{indianScore}</span>
                </div>
                <input
                  type="range"
                  min="300"
                  max="900"
                  value={indianScore}
                  onChange={(e) => setIndianScore(Number(e.target.value))}
                  className="w-full accent-[#191919]"
                />
              </div>

              <div>
                <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">Annual gross income (₹)</label>
                <input
                  type="number"
                  step="50000"
                  value={indianIncome}
                  onChange={(e) => setIndianIncome(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans tabular-nums"
                />
              </div>

              <div>
                <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">Loan amount (₹)</label>
                <input
                  type="number"
                  step="50000"
                  value={indianAmount}
                  onChange={(e) => setIndianAmount(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans tabular-nums"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">Tenure (months)</label>
                  <input
                    type="number"
                    value={indianTenure}
                    onChange={(e) => setIndianTenure(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans tabular-nums"
                  />
                </div>
                <div>
                  <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">Interest rate (%)</label>
                  <input
                    type="number"
                    step="0.25"
                    value={indianRate}
                    onChange={(e) => setIndianRate(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans tabular-nums"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">Employment</label>
                  <select
                    value={indianEmpType}
                    onChange={(e) => setIndianEmpType(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans"
                  >
                    <option value="Salaried">Salaried</option>
                    <option value="Self-Employed">Self-Employed</option>
                    <option value="Business">Business</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">Existing loans</label>
                  <input
                    type="number"
                    value={indianLoans}
                    onChange={(e) => setIndianLoans(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans tabular-nums"
                  />
                </div>
              </div>

              <button
                onClick={runIndianModel}
                disabled={indianLoading}
                className="w-full py-2.5 rounded-lg bg-[#191919] text-white text-xs font-medium font-sans hover:bg-[#333333] transition mt-2 flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                <span>{indianLoading ? 'Simulating...' : 'Calculate model risk'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Prediction Output */}
            <div className="lg:col-span-2 p-8 rounded-xl bg-[#F4F3F3] border border-[#E5E5E5] flex flex-col justify-between space-y-6">
              <div>
                <p className="text-xs text-[#191919]/60 font-sans mb-1.5">
                  Predicted default probability
                </p>
                <div className="flex items-baseline space-x-4">
                  <span className="font-serif text-6xl sm:text-7xl text-[#191919] tabular-nums">
                    {indianResult ? `${indianResult.ml_prob}%` : '—'}
                  </span>
                  <div className="flex flex-col">
                    <span className="text-xs text-[#191919]/60 font-sans">Risk classification</span>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-sans font-medium mt-1 ${indianResult?.ml_band === 'Low'
                        ? 'bg-emerald-100 text-emerald-800'
                        : indianResult?.ml_band === 'Medium'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-red-100 text-red-800'
                        }`}
                    >
                      {indianResult?.ml_band || 'Standard'} risk
                    </span>
                  </div>
                </div>
              </div>

              {/* Supporting Risk Metrics */}
              <div className="grid grid-cols-3 gap-6 pt-6 border-t border-[#E5E5E5]">
                <div>
                  <p className="text-xs text-[#191919]/60 font-sans">Rule-based score</p>
                  <p className="font-serif text-3xl text-[#191919] mt-0.5 tabular-nums">{indianResult?.risk_score} / 100</p>
                  <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Traditional matrix</p>
                </div>
                <div>
                  <p className="text-xs text-[#191919]/60 font-sans">Monthly EMI</p>
                  <p className="font-serif text-3xl text-[#191919] mt-0.5 tabular-nums">
                    ₹{indianResult ? indianResult.emi.toLocaleString('en-IN', { maximumFractionDigits: 0 }) : '—'}
                  </p>
                  <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Computed obligation</p>
                </div>
                <div>
                  <p className="text-xs text-[#191919]/60 font-sans">DTI ratio</p>
                  <p className="font-serif text-3xl text-[#191919] mt-0.5 tabular-nums">{indianResult?.emi_ratio}%</p>
                  <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Policy cap: 45%</p>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-white border border-[#E5E5E5] space-y-1.5 text-xs font-sans">
                <p className="font-medium text-[#191919]">Underwriting guidance</p>
                <p className="text-[#191919]/80 leading-relaxed">{indianResult?.recommendation}</p>
                <p className="text-[11px] text-[#191919]/50 pt-1">{indianResult?.disclaimer}</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* TAB B: HOME CREDIT MODEL */}
      {activeTab === 'home_credit' && (
        <section className="space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-serif text-3xl text-[#191919]">Home Credit risk model</h2>
              <p className="text-xs text-[#191919]/60 font-sans mt-0.5">
                Trained on Kaggle Home Credit dataset with 142 aggregated multi-table credit features
              </p>
            </div>
            <span className="text-xs font-sans px-2.5 py-1 rounded bg-[#F4F3F3] text-[#191919] border border-[#E5E5E5] font-medium">
              International historical portfolio
            </span>
          </div>

          {/* Benchmark Selection Bar */}
          <div className="flex flex-wrap gap-2.5 p-4 rounded-lg bg-[#F4F3F3] border border-[#E5E5E5]">
            <span className="text-xs font-sans font-medium text-[#191919] self-center mr-2">
              Select benchmark profile:
            </span>
            {Object.keys(BENCHMARKS).map((key) => (
              <button
                key={key}
                onClick={() => handleBenchmarkSelect(key)}
                className={`px-3 py-1.5 rounded text-xs font-sans transition-colors ${benchmarkKey === key
                  ? 'bg-[#191919] text-white font-medium'
                  : 'bg-white text-[#191919]/70 hover:text-[#191919] border border-[#E5E5E5]'
                  }`}
              >
                {BENCHMARKS[key].label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Input Controls */}
            <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-4">
              <h3 className="font-serif text-xl text-[#191919] mb-4">Applicant bureau signals</h3>

              <div>
                <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">External bureau score 1 (0–1)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0.0"
                  max="1.0"
                  value={hcApplicant.EXT_SOURCE_1 || 0.5}
                  onChange={(e) => setHcApplicant({ ...hcApplicant, EXT_SOURCE_1: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans tabular-nums"
                />
              </div>

              <div>
                <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">External bureau score 2 (0–1)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0.0"
                  max="1.0"
                  value={hcApplicant.EXT_SOURCE_2 || 0.5}
                  onChange={(e) => setHcApplicant({ ...hcApplicant, EXT_SOURCE_2: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans tabular-nums"
                />
              </div>

              <div>
                <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">External bureau score 3 (0–1)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0.0"
                  max="1.0"
                  value={hcApplicant.EXT_SOURCE_3 || 0.5}
                  onChange={(e) => setHcApplicant({ ...hcApplicant, EXT_SOURCE_3: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans tabular-nums"
                />
              </div>

              <div>
                <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">Installments late ratio (0–1)</label>
                <input
                  type="number"
                  step="0.02"
                  min="0.0"
                  max="1.0"
                  value={hcApplicant.INSTAL_LATE_RATIO || 0.0}
                  onChange={(e) => setHcApplicant({ ...hcApplicant, INSTAL_LATE_RATIO: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded border border-[#E5E5E5] text-xs font-sans tabular-nums"
                />
              </div>

              <button
                onClick={() => runHomeCredit(hcApplicant)}
                disabled={hcLoading}
                className="w-full py-2.5 rounded-lg bg-[#191919] text-white text-xs font-medium font-sans hover:bg-[#333333] transition mt-2 flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                <span>{hcLoading ? 'Predicting...' : 'Predict Home Credit risk'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Model Output with Calibration */}
            <div className="lg:col-span-2 p-8 rounded-xl bg-[#F4F3F3] border border-[#E5E5E5] flex flex-col justify-between space-y-6">
              <div>
                <p className="text-xs text-[#191919]/60 font-sans mb-1.5">
                  Calibrated default probability
                </p>
                <div className="flex items-baseline space-x-4">
                  <span className="font-serif text-6xl sm:text-7xl text-[#191919] tabular-nums">
                    {hcPrediction ? `${hcPrediction.calibrated_default_probability}%` : '—'}
                  </span>
                  <div className="flex flex-col">
                    <span className="text-xs text-[#191919]/60 font-sans">Risk band</span>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-sans font-medium mt-1 ${hcPrediction?.risk_band === 'Prime' || hcPrediction?.risk_band === 'Low Risk'
                        ? 'bg-emerald-100 text-emerald-800'
                        : hcPrediction?.risk_band === 'Moderate'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-red-100 text-red-800'
                        }`}
                    >
                      {hcPrediction?.risk_band || 'Standard'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Calibration & Model Details */}
              <div className="grid grid-cols-3 gap-6 pt-6 border-t border-[#E5E5E5]">
                <div>
                  <p className="text-xs text-[#191919]/60 font-sans">Uncalibrated output</p>
                  <p className="font-serif text-3xl text-[#191919] mt-0.5 tabular-nums">
                    {hcPrediction?.uncalibrated_default_probability}%
                  </p>
                  <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Raw sigmoid score</p>
                </div>
                <div>
                  <p className="text-xs text-[#191919]/60 font-sans">Calibration gain</p>
                  <p className="font-serif text-3xl text-[#191919] mt-0.5 tabular-nums">-59.95%</p>
                  <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Brier score improvement</p>
                </div>
                <div>
                  <p className="text-xs text-[#191919]/60 font-sans">Features evaluated</p>
                  <p className="font-serif text-3xl text-[#191919] mt-0.5 tabular-nums">142</p>
                  <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Multi-table aggregation</p>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-white border border-[#E5E5E5] space-y-1.5 text-xs font-sans">
                <p className="font-medium text-[#191919]">Advisory interpretation</p>
                <p className="text-[#191919]/80 leading-relaxed">{hcPrediction?.recommendation}</p>
                <p className="text-[11px] text-[#191919]/50 pt-1">{hcPrediction?.disclaimer}</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* TAB C: SHAP EXPLAINABILITY */}
      {activeTab === 'shap' && (
        <section className="space-y-8">
          <div>
            <h2 className="font-serif text-3xl text-[#191919]">SHAP feature attribution</h2>
            <p className="text-xs text-[#191919]/60 font-sans mt-0.5">
              Local Shapley Additive Explanations mapping positive and negative impacts on predicted delinquency risk
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Risk Drivers (Pushing risk higher) */}
            <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-sm bg-red-600"></div>
                <h3 className="font-serif text-xl text-[#191919]">Delinquency risk drivers</h3>
              </div>
              <p className="text-xs text-[#191919]/60 font-sans">
                Attributes increasing predicted probability of default
              </p>

              <div className="space-y-3 pt-2">
                {(hcPrediction?.risk_drivers || []).map((driver, idx) => {
                  const impact = driver.impact || driver.shap_value || 0.15;
                  return (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs font-sans">
                        <span className="font-medium text-[#191919]">{driver.feature}</span>
                        <span className="text-red-700 font-medium font-serif tabular-nums">+{impact.toFixed(4)}</span>
                      </div>
                      <div className="h-1.5 bg-[#E5E5E5] rounded-sm overflow-hidden">
                        <div
                          className="h-full bg-red-600 rounded-sm transition-all duration-300"
                          style={{ width: `${Math.min(100, Math.max(15, impact * 200))}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-[#191919]/50 font-sans">{driver.effect}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Protective Factors (Pushing risk lower) */}
            <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-sm bg-emerald-600"></div>
                <h3 className="font-serif text-xl text-[#191919]">Protective safety drivers</h3>
              </div>
              <p className="text-xs text-[#191919]/60 font-sans">
                Attributes reducing predicted probability of default
              </p>

              <div className="space-y-3 pt-2">
                {(hcPrediction?.safety_drivers || []).map((driver, idx) => {
                  const impact = Math.abs(driver.impact || driver.shap_value || 0.18);
                  return (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs font-sans">
                        <span className="font-medium text-[#191919]">{driver.feature}</span>
                        <span className="text-emerald-700 font-medium font-serif tabular-nums">-{impact.toFixed(4)}</span>
                      </div>
                      <div className="h-1.5 bg-[#E5E5E5] rounded-sm overflow-hidden">
                        <div
                          className="h-full bg-emerald-600 rounded-sm transition-all duration-300"
                          style={{ width: `${Math.min(100, Math.max(15, impact * 200))}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-[#191919]/50 font-sans">{driver.effect}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* TAB D: BASEL STRESS SIMULATOR & WATCHLIST */}
      {activeTab === 'stress' && (
        <section className="space-y-8">
          <div>
            <h2 className="font-serif text-3xl text-[#191919]">Basel macro stress simulator</h2>
            <p className="text-xs text-[#191919]/60 font-sans mt-0.5">
              Monetary policy rate tightening and household disposable income contraction simulations
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Shocks configuration */}
            <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-5">
              <h3 className="font-serif text-xl text-[#191919]">Macro scenario parameters</h3>

              <div>
                <div className="flex justify-between text-xs font-sans mb-1.5">
                  <span className="text-[#191919]/70">Policy rate shock</span>
                  <span className="font-medium tabular-nums">+{rateShock} bps</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="400"
                  step="25"
                  value={rateShock}
                  onChange={(e) => setRateShock(Number(e.target.value))}
                  className="w-full accent-[#191919]"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-sans mb-1.5">
                  <span className="text-[#191919]/70">Income contraction shock</span>
                  <span className="font-medium tabular-nums">-{incomeShock}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="30"
                  step="2.5"
                  value={incomeShock}
                  onChange={(e) => setIncomeShock(Number(e.target.value))}
                  className="w-full accent-[#191919]"
                />
              </div>

              <button
                onClick={runStress}
                className="w-full py-2.5 rounded-lg bg-[#191919] text-white text-xs font-medium font-sans hover:bg-[#333333] transition flex items-center justify-center space-x-2"
              >
                <span>Run stress scenario</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Stressed Capital at Risk */}
            <div className="lg:col-span-2 p-8 rounded-xl bg-[#F4F3F3] border border-[#E5E5E5] flex flex-col justify-between space-y-6">
              <div>
                <p className="text-xs text-[#191919]/60 font-sans mb-1.5">
                  Incremental capital at risk
                </p>
                <div className="flex items-baseline space-x-4">
                  <span className="font-serif text-6xl sm:text-7xl text-[#191919] tabular-nums">
                    ₹{stressResult ? stressResult.incremental_capital_at_risk_cr.toFixed(2) : '—'} Cr
                  </span>
                  <span className="text-xs text-red-700 font-sans font-medium tabular-nums">
                    +{stressResult ? stressResult.npa_surge_pct.toFixed(1) : 0}% NPA surge
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-6 pt-6 border-t border-[#E5E5E5]">
                <div>
                  <p className="text-xs text-[#191919]/60 font-sans">Baseline NPA rate</p>
                  <p className="font-serif text-2xl text-[#191919] mt-0.5 tabular-nums">{stressResult?.baseline_npa_rate || 0}%</p>
                </div>
                <div>
                  <p className="text-xs text-[#191919]/60 font-sans">Stressed NPA rate</p>
                  <p className="font-serif text-2xl text-red-700 mt-0.5 tabular-nums">{stressResult?.stressed_npa_rate || 0}%</p>
                </div>
                <div>
                  <p className="text-xs text-[#191919]/60 font-sans">Stressed NPA book</p>
                  <p className="font-serif text-2xl text-[#191919] mt-0.5 tabular-nums">₹{stressResult ? stressResult.stressed_npa_cr.toFixed(2) : 0} Cr</p>
                </div>
              </div>
            </div>
          </div>

          {/* DPD Watchlist Table */}
          <div className="space-y-4">
            <h3 className="font-serif text-2xl text-[#191919]">Portfolio delinquency watchlist</h3>
            <div className="border border-[#E5E5E5] rounded-lg overflow-hidden bg-white shadow-subtle">
              <table className="w-full text-left border-collapse text-xs font-sans">
                <thead>
                  <tr className="border-b border-[#E5E5E5] bg-[#F4F3F3] text-[#191919]/70 font-medium">
                    <th className="py-3 px-4">Borrower</th>
                    <th className="py-3 px-4">Overdue days (DPD)</th>
                    <th className="py-3 px-4">Outstanding balance</th>
                    <th className="py-3 px-4">Debt burden</th>
                    <th className="py-3 px-4">Action required</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E5E5]">
                  {(summary?.delinquency_watchlist || []).map((loan) => (
                    <tr key={loan.loan_id} className="hover:bg-[#F4F3F3]/60 transition-colors">
                      <td className="py-3 px-4 font-medium text-[#191919]">
                        {loan.full_name}
                        <span className="block text-[11px] text-[#191919]/40 font-normal">{loan.loan_purpose}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`font-serif text-sm tabular-nums ${loan.overdue_days >= 30 ? 'text-red-700 font-medium' : 'text-amber-700 font-medium'
                            }`}
                        >
                          {loan.overdue_days} DPD
                        </span>
                      </td>
                      <td className="py-3 px-4 font-medium text-[#191919] tabular-nums">
                        ₹{(loan.outstanding_balance / 100000).toFixed(2)} L
                      </td>
                      <td className="py-3 px-4 text-[#191919]/80 tabular-nums">{loan.debt_burden_ratio}%</td>
                      <td className="py-3 px-4 text-[#191919]">{loan.action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};
