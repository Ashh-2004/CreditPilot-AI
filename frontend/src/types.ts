export type Role = 'admin' | 'officer' | 'viewer';

export interface User {
  username: string;
  role: Role;
  token: string;
}

export interface ApplicationItem {
  application_id: number;
  full_name: string;
  credit_score: number;
  annual_income: number;
  property_area: string;
  employment_type: string;
  loan_amount: number;
  loan_purpose: string;
  interest_rate: number;
  tenure_months: number;
  status: string;
  approval_probability: number;
  ml_default_probability: number;
  ml_risk_band: string;
  applied_date: string;
}

export interface PortfolioKPIs {
  total_applications: number;
  approved_count: number;
  approval_rate: number;
  total_disbursed: number;
  avg_ticket_size: number;
  weighted_interest_rate: number;
}

export interface PortfolioData {
  kpis: PortfolioKPIs;
  charts: {
    by_purpose: { purpose: string; amount: number }[];
    by_status: { status: string; count: number }[];
    by_area: { area: string; count: number }[];
    by_risk_band: { band: string; count: number }[];
  };
  applications: ApplicationItem[];
}

export interface RiskCalculationResult {
  status: string;
  emi: number;
  emi_ratio: number;
  risk_score: number;
  ml_prob: number;
  ml_band: string;
  advisory_status: string;
  recommendation: string;
  disclaimer: string;
}

export interface AmortizationRow {
  month: number;
  opening_balance: number;
  interest_component: number;
  principal_component: number;
  total_payment: number;
  closing_balance: number;
}

export interface EmiScheduleResult {
  base_emi: number;
  processing_fee: number;
  total_interest: number;
  total_payment: number;
  actual_tenure_months: number;
  interest_saved: number;
  tenure_months_saved: number;
  accelerated_schedule: AmortizationRow[];
  baseline_schedule: AmortizationRow[];
}

export interface DelinquentLoan {
  loan_id: string;
  full_name: string;
  loan_purpose: string;
  outstanding_balance: number;
  overdue_days: number;
  credit_score: number;
  debt_burden_ratio: number;
  action: string;
}

export interface RiskSummary {
  kpis: {
    high_risk: number;
    medium_risk: number;
    low_risk: number;
    total_portfolio: number;
    avg_credit_score: number;
  };
  delinquency_watchlist: DelinquentLoan[];
  supervised_models: Record<string, any>;
}

export interface StressTestResult {
  baseline_npa_rate: number;
  stressed_npa_rate: number;
  npa_surge_pct: number;
  baseline_npa_cr: number;
  stressed_npa_cr: number;
  incremental_capital_at_risk_cr: number;
  rate_shock_bps: number;
  income_shock_pct: number;
}

export interface ShapFactor {
  feature: string;
  impact?: number;
  shap_value?: number;
  effect: string;
}

export interface HomeCreditPrediction {
  calibrated_default_probability: number;
  uncalibrated_default_probability: number;
  risk_band: string;
  risk_color: string;
  recommendation: string;
  model_name: string;
  risk_drivers: ShapFactor[];
  safety_drivers: ShapFactor[];
  disclaimer: string;
}

export interface UnderwritingMemoResult {
  status: string;
  source: string;
  memorandum: string;
  disclaimer: string;
  dti_percent: number;
  retrieved_clauses: string[];
}

export interface PolicyClause {
  clause_id: string;
  category: string;
  title: string;
  rule_text: string;
  threshold_condition: string;
  guidance: string;
  applicable_purposes: string[];
}

export interface PolicyQueryResult {
  status: string;
  query: string;
  clauses: PolicyClause[];
  synthesis: string;
  disclaimer: string;
}
