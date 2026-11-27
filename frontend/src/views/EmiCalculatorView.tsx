import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { EmiScheduleResult } from '../types';
import { BoomerangCanvas } from '../components/BoomerangCanvas';
import {
  ArrowRight,
  Download,
  Sliders
} from 'lucide-react';

export const EmiCalculatorView: React.FC = () => {
  // Input parameters
  const [principal, setPrincipal] = useState(2500000);
  const [annualRate, setAnnualRate] = useState(8.75);
  const [tenureMonths, setTenureMonths] = useState(180);
  const [monthlyPrepayment, setMonthlyPrepayment] = useState(5000);
  const [lumpSumPrepayment, setLumpSumPrepayment] = useState(100000);
  const [lumpSumMonth, setLumpSumMonth] = useState(24);

  const [_loading, setLoading] = useState(false);
  const [result, setResult] = useState<EmiScheduleResult | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      api.calculateEmi({
        principal: Number(principal),
        annual_rate: Number(annualRate),
        tenure_months: Number(tenureMonths),
        processing_fee_pct: 0.5,
        monthly_prepayment: Number(monthlyPrepayment),
        lump_sum_prepayment: Number(lumpSumPrepayment),
        lump_sum_month: Number(lumpSumMonth)
      })
        .then((res) => setResult(res))
        .catch((e) => console.error(e))
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(timer);
  }, [principal, annualRate, tenureMonths, monthlyPrepayment, lumpSumPrepayment, lumpSumMonth]);

  const downloadScheduleCSV = () => {
    if (!result?.accelerated_schedule) return;
    const headers = [
      'Month',
      'Opening Balance',
      'Interest Component',
      'Principal Component',
      'Total Payment',
      'Closing Balance'
    ];
    const rows = result.accelerated_schedule.map((r) => [
      r.month,
      r.opening_balance.toFixed(2),
      r.interest_component.toFixed(2),
      r.principal_component.toFixed(2),
      r.total_payment.toFixed(2),
      r.closing_balance.toFixed(2)
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `creditpilot_amortization_schedule.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-12 pb-16">
      {/* Editorial Header */}
      <section className="relative overflow-hidden pt-6 pb-10 border-b border-[#E5E5E5]">
        <BoomerangCanvas intensity="subtle" />
        <div className="relative z-10 max-w-4xl">
          <p className="text-xs text-[#191919]/60 font-sans mb-2">
            Structured amortization intelligence
          </p>
          <h1 className="font-serif text-5xl sm:text-6xl text-[#191919] tracking-tight leading-[1.08] mb-4">
            Amortization and prepayments
          </h1>
          <p className="text-base text-[#191919]/70 font-sans leading-relaxed max-w-2xl">
            Model structured repayment schedules and evaluate the balance sheet impact of accelerated monthly and lump-sum prepayments.
          </p>
        </div>

        {/* Action Button */}
        {result && (
          <div className="relative z-10 mt-6 flex gap-3">
            <button
              onClick={downloadScheduleCSV}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded bg-[#191919] text-white text-xs font-sans font-medium hover:bg-[#333333] transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download full schedule (CSV)</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </section>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Controls Column */}
        <div className="lg:col-span-5 space-y-6">
          <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-5">
            <h2 className="font-serif text-2xl text-[#191919]">Loan parameters</h2>

            {/* Principal */}
            <div>
              <div className="flex justify-between text-xs font-sans mb-1.5">
                <span className="text-[#191919]/70">Loan principal</span>
                <span className="font-serif text-base text-[#191919] tabular-nums">
                  ₹{(principal / 100000).toFixed(2)} Lakh
                </span>
              </div>
              <input
                type="range"
                min="100000"
                max="20000000"
                step="50000"
                value={principal}
                onChange={(e) => setPrincipal(Number(e.target.value))}
                className="w-full accent-[#191919]"
              />
              <div className="flex justify-between text-[11px] text-[#191919]/40 font-sans mt-0.5 tabular-nums">
                <span>₹1 Lakh</span>
                <span>₹2 Crore</span>
              </div>
            </div>

            {/* Interest Rate */}
            <div>
              <div className="flex justify-between text-xs font-sans mb-1.5">
                <span className="text-[#191919]/70">Annual interest rate</span>
                <span className="font-serif text-base text-[#191919] tabular-nums">{annualRate}%</span>
              </div>
              <input
                type="range"
                min="4.0"
                max="20.0"
                step="0.25"
                value={annualRate}
                onChange={(e) => setAnnualRate(Number(e.target.value))}
                className="w-full accent-[#191919]"
              />
              <div className="flex justify-between text-[11px] text-[#191919]/40 font-sans mt-0.5 tabular-nums">
                <span>4.0%</span>
                <span>20.0%</span>
              </div>
            </div>

            {/* Tenure */}
            <div>
              <div className="flex justify-between text-xs font-sans mb-1.5">
                <span className="text-[#191919]/70">Tenure</span>
                <span className="font-serif text-base text-[#191919] tabular-nums">
                  {tenureMonths} months ({(tenureMonths / 12).toFixed(1)} yrs)
                </span>
              </div>
              <input
                type="range"
                min="12"
                max="360"
                step="6"
                value={tenureMonths}
                onChange={(e) => setTenureMonths(Number(e.target.value))}
                className="w-full accent-[#191919]"
              />
              <div className="flex justify-between text-[11px] text-[#191919]/40 font-sans mt-0.5 tabular-nums">
                <span>1 year</span>
                <span>30 years</span>
              </div>
            </div>
          </div>

          {/* Prepayment Acceleration Options */}
          <div className="p-6 rounded-xl bg-[#F4F3F3] border border-[#E5E5E5] space-y-5">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-[#191919]" />
              <h2 className="font-serif text-xl text-[#191919]">Prepayment strategy</h2>
            </div>

            {/* Monthly Prepayment */}
            <div>
              <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">
                Extra monthly payment (₹)
              </label>
              <input
                type="number"
                step="1000"
                min="0"
                value={monthlyPrepayment}
                onChange={(e) => setMonthlyPrepayment(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg border border-[#E5E5E5] bg-white text-xs font-sans tabular-nums"
              />
              <span className="text-[11px] text-[#191919]/50 block mt-1">
                Paid alongside regular EMI each month
              </span>
            </div>

            {/* Lump-sum Prepayment */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">
                  Lump-sum payment (₹)
                </label>
                <input
                  type="number"
                  step="25000"
                  min="0"
                  value={lumpSumPrepayment}
                  onChange={(e) => setLumpSumPrepayment(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg border border-[#E5E5E5] bg-white text-xs font-sans tabular-nums"
                />
              </div>
              <div>
                <label className="block text-xs font-sans text-[#191919]/70 mb-1.5">
                  At month #
                </label>
                <input
                  type="number"
                  min="1"
                  max={tenureMonths}
                  value={lumpSumMonth}
                  onChange={(e) => setLumpSumMonth(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg border border-[#E5E5E5] bg-white text-xs font-sans tabular-nums"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Results & Schedule Column */}
        <div className="lg:col-span-7 space-y-6">
          {/* Executive Output Block */}
          <div className="p-8 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-6">
            <div>
              <p className="text-xs text-[#191919]/60 font-sans mb-1.5">
                Regular monthly installment (EMI)
              </p>
              <div className="flex items-baseline space-x-3">
                <span className="font-serif text-5xl sm:text-6xl text-[#191919] tabular-nums">
                  ₹{result ? result.base_emi.toLocaleString('en-IN', { maximumFractionDigits: 0 }) : '—'}
                </span>
                <span className="text-xs text-[#191919]/50 font-sans">/ month</span>
              </div>
            </div>

            {/* Savings Quad */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-6 border-t border-[#E5E5E5]">
              <div>
                <p className="text-xs text-[#191919]/60 font-sans">Total interest</p>
                <p className="font-serif text-2xl text-[#191919] mt-0.5 tabular-nums">
                  ₹{result ? ((result.total_interest) / 100000).toFixed(2) : '—'} L
                </p>
                <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Accelerated plan</p>
              </div>

              <div>
                <p className="text-xs text-[#191919]/60 font-sans">Total payment</p>
                <p className="font-serif text-2xl text-[#191919] mt-0.5 tabular-nums">
                  ₹{result ? ((result.total_payment) / 100000).toFixed(2) : '—'} L
                </p>
                <p className="text-[11px] text-[#191919]/50 font-sans mt-0.5">Principal + interest</p>
              </div>

              <div>
                <p className="text-xs text-emerald-800 font-sans font-medium">Interest saved</p>
                <p className="font-serif text-2xl text-emerald-700 mt-0.5 tabular-nums">
                  ₹{result ? ((result.interest_saved) / 100000).toFixed(2) : '—'} L
                </p>
                <p className="text-[11px] text-emerald-700/60 font-sans mt-0.5">Prepayment benefit</p>
              </div>

              <div>
                <p className="text-xs text-emerald-800 font-sans font-medium">Tenure saved</p>
                <p className="font-serif text-2xl text-emerald-700 mt-0.5 tabular-nums">
                  {result ? result.tenure_months_saved : 0} mos
                </p>
                <p className="text-[11px] text-emerald-700/60 font-sans mt-0.5 tabular-nums">
                  {(Number(result?.tenure_months_saved || 0) / 12).toFixed(1)} years sooner
                </p>
              </div>
            </div>
          </div>

          {/* SVG Comparative Amortization Curve */}
          <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-serif text-xl text-[#191919]">Balance amortization trajectory</h3>
              <div className="flex items-center space-x-4 text-xs font-sans">
                <div className="flex items-center space-x-1.5">
                  <span className="w-3 h-0.5 bg-[#191919]/30 inline-block"></span>
                  <span className="text-[#191919]/60">Baseline schedule</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-3 h-0.5 bg-[#191919] inline-block"></span>
                  <span className="text-[#191919] font-medium">Accelerated schedule</span>
                </div>
              </div>
            </div>

            {/* SVG Visualizer */}
            <div className="h-44 w-full flex items-center justify-center">
              <svg viewBox="0 0 600 150" className="w-full h-full text-[#191919]">
                {/* Baseline Curve */}
                <path
                  d="M 20 20 Q 300 80 580 140"
                  fill="none"
                  stroke="rgba(25, 25, 25, 0.25)"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />
                {/* Accelerated Curve */}
                <path
                  d="M 20 20 Q 240 70 420 140"
                  fill="none"
                  stroke="#191919"
                  strokeWidth="2"
                />
                {/* Axis lines */}
                <line x1="20" y1="140" x2="580" y2="140" stroke="#E5E5E5" strokeWidth="1" />
                <text x="20" y="150" fontSize="10" fill="#999" fontFamily="Inter">Month 0</text>
                <text x="400" y="150" fontSize="10" fill="#15803d" fontFamily="Inter">Debt-free month {result?.actual_tenure_months || tenureMonths}</text>
                <text x="540" y="150" fontSize="10" fill="#999" fontFamily="Inter">Month {tenureMonths}</text>
              </svg>
            </div>
          </div>

          {/* Amortization Schedule Table */}
          <div className="p-6 rounded-xl bg-white border border-[#E5E5E5] shadow-subtle space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-serif text-xl text-[#191919]">Amortization schedule preview</h3>
              <span className="text-xs text-[#191919]/60 font-sans">First 12 installments</span>
            </div>

            <div className="border border-[#E5E5E5] rounded-lg overflow-hidden">
              <table className="w-full text-left border-collapse text-xs font-sans">
                <thead>
                  <tr className="border-b border-[#E5E5E5] bg-[#F4F3F3] text-[#191919]/70 font-medium">
                    <th className="py-2.5 px-3">Month</th>
                    <th className="py-2.5 px-3">Opening</th>
                    <th className="py-2.5 px-3">Principal</th>
                    <th className="py-2.5 px-3">Interest</th>
                    <th className="py-2.5 px-3">Closing</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E5E5]">
                  {(result?.accelerated_schedule || []).slice(0, 12).map((row) => (
                    <tr key={row.month} className="hover:bg-[#F4F3F3]/50 transition-colors">
                      <td className="py-2 px-3 font-medium text-[#191919] tabular-nums">#{row.month}</td>
                      <td className="py-2 px-3 tabular-nums">₹{row.opening_balance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                      <td className="py-2 px-3 text-emerald-700 font-medium tabular-nums">
                        ₹{row.principal_component.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </td>
                      <td className="py-2 px-3 text-[#191919]/70 tabular-nums">
                        ₹{row.interest_component.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </td>
                      <td className="py-2 px-3 font-medium text-[#191919] tabular-nums">
                        ₹{row.closing_balance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
