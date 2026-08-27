// =============================================================================
// SHIELD — Frontend constants
// Median defaults and test profiles, mirrored from backend for instant
// offline pre-fill (no API call needed to seed the form).
// =============================================================================

import type { SMEFinancialData } from "./types";

export const MEDIAN_DEFAULTS: SMEFinancialData = {
  roa_a: 0.5598,
  roa_b: 0.5523,
  continuous_interest_rate: 0.7816,
  net_value_per_share_b: 0.1844,
  net_value_per_share_a: 0.1844,
  net_value_per_share_c: 0.1844,
  persistent_eps: 0.2245,
  per_share_net_profit: 0.1797,
  interest_expense_ratio: 0.6307,
  debt_ratio: 0.1114,
  net_worth_assets: 0.8886,
  borrowing_dependency: 0.3726,
  net_profit_paid_in_capital: 0.1785,
  retained_earnings: 0.9377,
  total_income_expense: 0.0023,
  net_income_total_assets: 0.8106,
  net_income_equity: 0.8412,
  liability_to_equity: 0.2788,
  interest_coverage_ratio: 0.5653,
  equity_to_liability: 0.0338,
};

export const PROFILE_HEALTHY: SMEFinancialData = {
  roa_a: 0.58684,
  roa_b: 0.58804,
  continuous_interest_rate: 0.781608,
  net_value_per_share_b: 0.185032,
  net_value_per_share_a: 0.185032,
  net_value_per_share_c: 0.185032,
  persistent_eps: 0.248842,
  per_share_net_profit: 0.204188,
  interest_expense_ratio: 0.630613,
  debt_ratio: 0.165221,
  net_worth_assets: 0.834779,
  borrowing_dependency: 0.369637,
  net_profit_paid_in_capital: 0.202783,
  retained_earnings: 0.94219,
  total_income_expense: 0.002269,
  net_income_total_assets: 0.827921,
  net_income_equity: 0.843384,
  liability_to_equity: 0.283137,
  interest_coverage_ratio: 0.565159,
  equity_to_liability: 0.02168,
};

export const PROFILE_DISTRESSED: SMEFinancialData = {
  roa_a: 0.211023,
  roa_b: 0.221425,
  continuous_interest_rate: 0.780388,
  net_value_per_share_b: 0.069656,
  net_value_per_share_a: 0.069656,
  net_value_per_share_c: 0.069656,
  persistent_eps: 0.079512,
  per_share_net_profit: 0.054304,
  interest_expense_ratio: 0.630536,
  debt_ratio: 0.52541,
  net_worth_assets: 0.47459,
  borrowing_dependency: 0.357056,
  net_profit_paid_in_capital: 0.05713,
  retained_earnings: 0.777637,
  total_income_expense: 0.001996,
  net_income_total_assets: 0.519388,
  net_income_equity: 0.856906,
  liability_to_equity: 0.25928,
  interest_coverage_ratio: 0.565052,
  equity_to_liability: 0.003946,
};

export const FEATURE_LABELS: Record<keyof SMEFinancialData, string> = {
  roa_a: "ROA(A) — Before Interest & % After Tax",
  roa_b: "ROA(B) — Before Interest & Depreciation After Tax",
  continuous_interest_rate: "Continuous Interest Rate (After Tax)",
  net_value_per_share_b: "Net Value Per Share (B)",
  net_value_per_share_a: "Net Value Per Share (A)",
  net_value_per_share_c: "Net Value Per Share (C)",
  persistent_eps: "Persistent EPS in the Last Four Seasons",
  per_share_net_profit: "Per Share Net Profit Before Tax",
  interest_expense_ratio: "Interest Expense Ratio",
  debt_ratio: "Debt Ratio %",
  net_worth_assets: "Net Worth / Assets",
  borrowing_dependency: "Borrowing Dependency",
  net_profit_paid_in_capital: "Net Profit Before Tax / Paid-in Capital",
  retained_earnings: "Retained Earnings to Total Assets",
  total_income_expense: "Total Income / Total Expense",
  net_income_total_assets: "Net Income to Total Assets",
  net_income_equity: "Net Income to Stockholder's Equity",
  liability_to_equity: "Liability to Equity",
  interest_coverage_ratio: "Interest Coverage Ratio (Interest Expense to EBIT)",
  equity_to_liability: "Equity to Liability",
};
