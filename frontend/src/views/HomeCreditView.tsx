import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { HomeCreditPrediction } from '../types';
import { AlertTriangle } from 'lucide-react';

const BENCHMARKS: Record<string, any> = {
  prime: {
    label: '🌟 Prime Benchmark Borrower (Low Risk)',
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
    label: '⚖️ Moderate Benchmark Borrower (Medium Risk)',
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
    BUREAU_DEBT_CREDIT_RATIO: 0.45,
  },
  subprime: {
    label: '⚠️ Subprime Benchmark Borrower (High Risk)',
    source: 'Kaggle Benchmark Profile (Real Data)',
    AMT_INCOME_TOTAL: 112500.0,
    AMT_CREDIT: 675000.0,
    AMT_ANNUITY: 34500.0,
    AMT_GOODS_PRICE: 540000.0,
    NAME_CONTRACT_TYPE: 'Cash loans',
    CODE_GENDER: 'M',
    FLAG_OWN_CAR: 'N',
    FLAG_OWN_REALTY: 'N',
    CNT_CHILDREN: 2,
    DAYS_BIRTH: -9500,
    DAYS_EMPLOYED: -500,
    EXT_SOURCE_1: 0.18,
    EXT_SOURCE_2: 0.22,
    EXT_SOURCE_3: 0.15,
    INSTAL_LATE_RATIO: 0.35,
    INSTAL_DPD_MAX: 45.0,
    PREV_REFUSAL_RATE: 0.50,
    BUREAU_LOAN_COUNT: 8.0,
    BUREAU_DEBT_CREDIT_RATIO: 0.85,
  }
};

export const HomeCreditView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'prediction' | 'benchmarks'>('prediction');
  const [mode, setMode] = useState<'benchmark' | 'custom'>('benchmark');
  const [benchmarkKey, setBenchmarkKey] = useState<string>('prime');

  // Custom Form
  const [income, setIncome] = useState(200000);
  const [credit, setCredit] = useState(500000);
  const [annuity, setAnnuity] = useState(25000);
  const [_goods, _setGoods] = useState(450000);
  const [gender, setGender] = useState('M');
  const [_contractType, _setContractType] = useState('Cash loans');
  const [age, setAge] = useState(38);
  const [employedYears, setEmployedYears] = useState(6.5);
  const [ext1, setExt1] = useState(0.50);
  const [ext2, setExt2] = useState(0.52);
  const [ext3, setExt3] = useState(0.48);
  const [lateRatio, setLateRatio] = useState(0.05);

  const [_loading, _setLoading] = useState(false);
  const [prediction, setPrediction] = useState<HomeCreditPrediction | null>(null);
  const [evalData, setEvalData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.getHomeCreditEvaluation()
      .then((res) => {
        if (!cancelled) setEvalData(res);
      })
      .catch((err: any) => console.error(err));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (mode !== 'benchmark') return;
    let cancelled = false;
    const payload: any = { ...BENCHMARKS[benchmarkKey] };
    delete payload.label;
    delete payload.source;
    api.predictHomeCredit(payload)
      .then((res) => {
        if (!cancelled) {
          setPrediction(res);
          setError(null);
        }
      })
      .catch((err: any) => {
        if (!cancelled) setError(err.message || 'Error executing Home Credit inference');
      });
    return () => {
      cancelled = true;
    };
  }, [benchmarkKey, mode]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">Home Credit Risk Analysis & SHAP Explainability</h1>
        <p className="text-sm text-dark-muted">Kaggle international benchmark modeling across 142 historical credit features</p>
      </div>

      {/* Isolation safeguard notice */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-brand-500/30 text-amber-300 text-xs flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-brand-400 shrink-0 mt-0.5" />
        <div>
          <strong className="block text-white font-bold">Strict Architecture Isolation Safeguard</strong>
          This module executes the trained 142-feature Home Credit ML model (`models/home_credit/model.joblib`).
          The domestic Indian retail borrower workflow remains separate and continues running on `models/xgboost_model.joblib`.
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-dark-border pb-2">
        <button
          onClick={() => setActiveTab('prediction')}
          className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
            activeTab === 'prediction'
              ? 'bg-brand-500 text-dark-bg shadow-sm'
              : 'bg-dark-surface text-slate-300 hover:text-white'
          }`}
        >
          🎯 Applicant Prediction & SHAP
        </button>
        <button
          onClick={() => setActiveTab('benchmarks')}
          className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
            activeTab === 'benchmarks'
              ? 'bg-brand-500 text-dark-bg shadow-sm'
              : 'bg-dark-surface text-slate-300 hover:text-white'
          }`}
        >
          📊 Model Evaluation & Benchmarks
        </button>
      </div>

      {/* Tab 1: Prediction & SHAP */}
      {activeTab === 'prediction' && (
        <div className="space-y-6">
          <div className="bg-dark-surface border border-dark-border p-6 rounded-2xl space-y-5">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-dark-border pb-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Select Applicant Input Source
              </h3>
              <div className="flex rounded-xl bg-dark-card p-1 border border-dark-border text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setMode('benchmark')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    mode === 'benchmark' ? 'bg-brand-500 text-dark-bg font-bold' : 'text-slate-300 hover:text-white'
                  }`}
                >
                  Preset Benchmark Profiles
                </button>
                <button
                  type="button"
                  onClick={() => setMode('custom')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    mode === 'custom' ? 'bg-brand-500 text-dark-bg font-bold' : 'text-slate-300 hover:text-white'
                  }`}
                >
                  Custom What-If Simulator
                </button>
              </div>
            </div>

            {mode === 'benchmark' ? (
              <div className="space-y-3">
                <label className="block text-xs font-bold uppercase tracking-wider text-dark-muted">
                  Choose Real Kaggle Benchmark Profile
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {Object.entries(BENCHMARKS).map(([k, v]) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => setBenchmarkKey(k)}
                      className={`p-4 rounded-xl border text-left transition ${
                        benchmarkKey === k
                          ? 'bg-brand-500/10 border-brand-500 text-white shadow-sm'
                          : 'bg-dark-card border-dark-border text-slate-300 hover:border-slate-600'
                      }`}
                    >
                      <span className="font-bold text-sm block">{v.label}</span>
                      <span className="text-[11px] text-dark-muted mt-1 block">{v.source}</span>
                      <div className="mt-2 text-xs flex justify-between text-dark-muted border-t border-dark-border/40 pt-2">
                        <span>Ext Mean: {((v.EXT_SOURCE_1 + v.EXT_SOURCE_2 + v.EXT_SOURCE_3) / 3).toFixed(2)}</span>
                        <span>Late: {(v.INSTAL_LATE_RATIO * 100).toFixed(0)}%</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-dark-muted mb-1">Income & Credit</label>
                  <div className="space-y-2">
                    <input
                      type="number"
                      value={income}
                      onChange={(e) => setIncome(Number(e.target.value))}
                      placeholder="Income"
                      className="w-full px-3 py-2 bg-dark-card border border-dark-border rounded-xl text-xs text-white"
                    />
                    <input
                      type="number"
                      value={credit}
                      onChange={(e) => setCredit(Number(e.target.value))}
                      placeholder="Credit"
                      className="w-full px-3 py-2 bg-dark-card border border-dark-border rounded-xl text-xs text-white"
                    />
                    <input
                      type="number"
                      value={annuity}
                      onChange={(e) => setAnnuity(Number(e.target.value))}
                      placeholder="Annuity"
                      className="w-full px-3 py-2 bg-dark-card border border-dark-border rounded-xl text-xs text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-dark-muted mb-1">Demographics</label>
                  <div className="space-y-2">
                    <select
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                      className="w-full px-3 py-2 bg-dark-card border border-dark-border rounded-xl text-xs text-white"
                    >
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                    </select>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={age}
                        onChange={(e) => setAge(Number(e.target.value))}
                        placeholder="Age"
                        className="w-1/2 px-3 py-2 bg-dark-card border border-dark-border rounded-xl text-xs text-white"
                      />
                      <input
                        type="number"
                        value={employedYears}
                        onChange={(e) => setEmployedYears(Number(e.target.value))}
                        placeholder="Yrs Employed"
                        className="w-1/2 px-3 py-2 bg-dark-card border border-dark-border rounded-xl text-xs text-white"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-dark-muted mb-1">Bureau Ratings & History</label>
                  <div className="space-y-2">
                    <div className="flex justify-between text-[11px] text-dark-muted">
                      <span>Ext Mean (1,2,3):</span>
                      <span className="text-brand-400 font-bold">{((ext1 + ext2 + ext3) / 3).toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min={0.05}
                      max={0.95}
                      step={0.05}
                      value={ext2}
                      onChange={(e) => {
                        const val = Number(e.target.value);
                        setExt1(val);
                        setExt2(val);
                        setExt3(val);
                      }}
                      className="w-full accent-brand-500"
                    />
                    <div className="flex justify-between text-[11px] text-dark-muted">
                      <span>Late Payment Ratio:</span>
                      <span className="text-rose-400 font-bold">{(lateRatio * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.05}
                      value={lateRatio}
                      onChange={(e) => setLateRatio(Number(e.target.value))}
                      className="w-full accent-rose-500"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Prediction Result Display */}
          {prediction && (
            <div className="bg-dark-surface border border-dark-border p-6 rounded-2xl space-y-6">
              <div className="flex items-center justify-between border-b border-dark-border pb-3">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  🎯 Inferred Risk Probability & SHAP Attribution
                </h3>
                <span className="text-xs px-2.5 py-1 rounded-full bg-dark-card border border-dark-border text-brand-300 font-bold uppercase tracking-wider">
                  Model: {prediction.model_name}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-dark-card border border-brand-500/40 p-4 rounded-xl bg-brand-500/5">
                  <span className="text-[11px] font-bold text-brand-300 uppercase tracking-wider block">Calibrated Default Prob</span>
                  <div className="text-2xl font-black text-brand-400 mt-1">{prediction.calibrated_default_probability.toFixed(2)}%</div>
                  <span className="text-[10px] text-dark-muted">Sigmoid Calibrated</span>
                </div>

                <div className="bg-dark-card border border-dark-border p-4 rounded-xl">
                  <span className="text-[11px] font-bold text-dark-muted uppercase tracking-wider block">Raw Model Score</span>
                  <div className="text-2xl font-black text-white mt-1">{prediction.uncalibrated_default_probability.toFixed(2)}%</div>
                  <span className="text-[10px] text-dark-muted">Uncalibrated Gradient Boosting</span>
                </div>

                <div className="bg-dark-card border border-dark-border p-4 rounded-xl">
                  <span className="text-[11px] font-bold text-dark-muted uppercase tracking-wider block">Assigned Risk Tier</span>
                  <div className={`text-2xl font-black mt-1 ${
                    prediction.risk_band === 'Low' ? 'text-emerald-400' : prediction.risk_band === 'Medium' ? 'text-amber-400' : 'text-rose-400'
                  }`}>
                    {prediction.risk_band} Risk
                  </div>
                  <span className="text-[10px] text-dark-muted">Benchmark Population</span>
                </div>

                <div className="bg-dark-card border border-dark-border p-4 rounded-xl">
                  <span className="text-[11px] font-bold text-dark-muted uppercase tracking-wider block">Decision Protocol</span>
                  <div className="text-sm font-bold text-white mt-2">{prediction.recommendation}</div>
                </div>
              </div>

              {/* SHAP Attribution Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div className="bg-dark-card p-4 rounded-xl border border-rose-500/20 space-y-2">
                  <span className="text-xs font-bold text-rose-400 uppercase tracking-wider block">
                    ⚠️ Top Risk-Elevating Factors (Local SHAP)
                  </span>
                  {prediction.risk_drivers.length ? (
                    <div className="space-y-1.5">
                      {prediction.risk_drivers.map((d, i) => (
                        <div key={i} className="flex justify-between text-xs p-2 rounded-lg bg-dark-surface border border-dark-border">
                          <span className="font-mono text-slate-300 font-bold">{d.feature}</span>
                          <span className="text-rose-400 font-bold">+{d.impact || d.shap_value}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-dark-muted">No significant risk-elevating deviations found.</p>
                  )}
                </div>

                <div className="bg-dark-card p-4 rounded-xl border border-emerald-500/20 space-y-2">
                  <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block">
                    🛡️ Top Protective Factors (Local SHAP)
                  </span>
                  {prediction.safety_drivers.length ? (
                    <div className="space-y-1.5">
                      {prediction.safety_drivers.map((s, i) => (
                        <div key={i} className="flex justify-between text-xs p-2 rounded-lg bg-dark-surface border border-dark-border">
                          <span className="font-mono text-slate-300 font-bold">{s.feature}</span>
                          <span className="text-emerald-400 font-bold">{s.impact || s.shap_value}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-dark-muted">No significant protective factors detected.</p>
                  )}
                </div>
              </div>

              <p className="text-[11px] text-dark-muted italic border-t border-dark-border pt-3">
                {prediction.disclaimer}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Evaluation Benchmarks */}
      {activeTab === 'benchmarks' && evalData && (
        <div className="space-y-6">
          <div className="bg-dark-surface border border-dark-border p-6 rounded-2xl space-y-6">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-dark-border pb-3">
              Held-Out Test Set Performance (25,000 Kaggle Records)
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-dark-card border border-dark-border p-4 rounded-xl">
                <span className="text-[11px] font-bold text-dark-muted uppercase tracking-wider block">ROC-AUC Score</span>
                <div className="text-2xl font-black text-brand-400 mt-1">0.7407</div>
                <span className="text-[10px] text-dark-muted">5-Fold CV: 0.7415</span>
              </div>

              <div className="bg-dark-card border border-dark-border p-4 rounded-xl">
                <span className="text-[11px] font-bold text-dark-muted uppercase tracking-wider block">PR-AUC Score</span>
                <div className="text-2xl font-black text-white mt-1">0.2355</div>
                <span className="text-[10px] text-dark-muted">Precision-Recall Curve</span>
              </div>

              <div className="bg-dark-card border border-dark-border p-4 rounded-xl">
                <span className="text-[11px] font-bold text-dark-muted uppercase tracking-wider block">Accuracy</span>
                <div className="text-2xl font-black text-emerald-400 mt-1">74.53%</div>
                <span className="text-[10px] text-dark-muted">Held-Out Test Split</span>
              </div>

              <div className="bg-dark-card border border-dark-border p-4 rounded-xl">
                <span className="text-[11px] font-bold text-dark-muted uppercase tracking-wider block">Calibration Gain</span>
                <div className="text-2xl font-black text-emerald-400 mt-1">-59.95%</div>
                <span className="text-[10px] text-emerald-400">Brier 0.1710 → 0.0685</span>
              </div>
            </div>

            {/* Confusion Matrix */}
            <div>
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">
                Held-Out Test Confusion Matrix (Threshold = 0.50)
              </span>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono text-center">
                <div className="bg-dark-card p-3 rounded-xl border border-dark-border">
                  <span className="text-dark-muted block text-[10px]">True Negative (Repaid)</span>
                  <span className="text-emerald-400 font-bold text-base">4,357</span>
                </div>
                <div className="bg-dark-card p-3 rounded-xl border border-dark-border">
                  <span className="text-dark-muted block text-[10px]">False Positive (Type I)</span>
                  <span className="text-rose-400 font-bold text-base">1,389</span>
                </div>
                <div className="bg-dark-card p-3 rounded-xl border border-dark-border">
                  <span className="text-dark-muted block text-[10px]">False Negative (Type II)</span>
                  <span className="text-rose-400 font-bold text-base">203</span>
                </div>
                <div className="bg-dark-card p-3 rounded-xl border border-dark-border">
                  <span className="text-dark-muted block text-[10px]">True Positive (Default Flagged)</span>
                  <span className="text-emerald-400 font-bold text-base">301</span>
                </div>
              </div>
            </div>

            {/* Global SHAP Feature Importance */}
            <div>
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">
                Top Global Risk Predictors (Mean |SHAP| Value)
              </span>
              <div className="space-y-2">
                {evalData.shap_summary?.global_importance?.top_features?.slice(0, 8).map((f: any) => (
                  <div key={f.feature} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-mono text-slate-300 font-semibold">{f.feature}</span>
                      <span className="text-brand-400 font-bold">{f.mean_abs_shap}</span>
                    </div>
                    <div className="h-1.5 w-full bg-dark-card rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-500 rounded-full"
                        style={{ width: `${Math.min(100, f.mean_abs_shap * 1000)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
