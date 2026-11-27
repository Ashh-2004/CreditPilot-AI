import {
  User,
  PortfolioData,
  RiskCalculationResult,
  EmiScheduleResult,
  RiskSummary,
  StressTestResult,
  HomeCreditPrediction,
  UnderwritingMemoResult,
  PolicyQueryResult
} from '../types';

const API_BASE = typeof window !== 'undefined' && window.location.port === '5173'
  ? 'http://localhost:8000'
  : '';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  let token: string | null = null;
  try {
    const saved = localStorage.getItem('creditpilot_user') || localStorage.getItem('loansense_user');
    if (saved && saved !== 'undefined' && saved !== 'null') {
      const u = JSON.parse(saved);
      token = u.token || null;
    }
  } catch {
    // Ignore storage parse error
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {})
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  // Auth
  login: (username: string, password: string) =>
    request<User>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    }),

  register: (username: string, password: string, role: string) =>
    request<{ status: string; message: string; user_id: number; username: string; role: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, role })
    }),

  // Admin User Management (Restricted to administrators)
  getUsers: () =>
    request<{ status: string; users: { user_id: number; username: string; role: import('../types').Role; created_at: string }[] }>('/api/admin/users'),

  createUser: (username: string, password: string, role: string) =>
    request<{ status: string; message: string; user_id: number; username: string; role: string }>('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify({ username, password, role })
    }),

  deleteUser: (userId: number) =>
    request<{ status: string; message: string }>(`/api/admin/users/${userId}`, {
      method: 'DELETE'
    }),

  // Portfolio
  getPortfolio: (params?: { purpose?: string; status?: string; band?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.purpose) q.append('purpose', params.purpose);
    if (params?.status) q.append('status_filter', params.status);
    if (params?.band) q.append('risk_band', params.band);
    if (params?.search) q.append('search', params.search);
    const qs = q.toString();
    return request<PortfolioData>(`/api/portfolio${qs ? `?${qs}` : ''}`);
  },

  // Applications
  calculateRisk: (data: any) =>
    request<RiskCalculationResult>('/api/applications/calculate-risk', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  submitApplication: (data: any) =>
    request<{ status: string; application_id: number; message: string }>('/api/applications', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  // EMI Calculator
  calculateEmi: (params: {
    principal: number;
    annual_rate: number;
    tenure_months: number;
    processing_fee_pct?: number;
    monthly_prepayment?: number;
    lump_sum_prepayment?: number;
    lump_sum_month?: number;
  }) =>
    request<EmiScheduleResult>('/api/emi/calculate', {
      method: 'POST',
      body: JSON.stringify(params)
    }),

  // Risk & Stress Testing
  getRiskSummary: (minDpd: number = 15, maxScore: number = 680) =>
    request<RiskSummary>(`/api/risk/summary?min_dpd=${minDpd}&max_score=${maxScore}`),

  runStressTest: (params: {
    baseline_exposure_cr: number;
    baseline_npa_rate: number;
    rate_shock_bps: number;
    income_shock_pct: number;
  }) =>
    request<StressTestResult>('/api/risk/stress-test', {
      method: 'POST',
      body: JSON.stringify(params)
    }),

  // Home Credit ML
  getHomeCreditEvaluation: () =>
    request<{ evaluation_report: any; calibration_report: any; shap_summary: any }>('/api/home-credit/evaluation'),

  predictHomeCredit: (applicant: any) =>
    request<HomeCreditPrediction>('/api/home-credit/predict', {
      method: 'POST',
      body: JSON.stringify(applicant)
    }),

  // AI & RAG
  queryAssistant: (prompt: string) =>
    request<{ status: string; generated_sql: string; record_count: number; results: any[] }>('/api/ai/query', {
      method: 'POST',
      body: JSON.stringify({ prompt })
    }),

  generateUnderwritingMemo: (applicant: any) =>
    request<UnderwritingMemoResult>('/api/ai/underwrite', {
      method: 'POST',
      body: JSON.stringify(applicant)
    }),

  queryPolicy: (data: { query: string; loan_purpose?: string; credit_score?: number; dti_percent?: number }) =>
    request<PolicyQueryResult>('/api/ai/policy-query', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  // Health
  checkHealth: () => request<{ status: string; service: string; version: string }>('/api/health')
};
