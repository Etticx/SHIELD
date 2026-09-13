// =============================================================================
// SHIELD — Frontend constants
// Median defaults and test profiles, mirrored from backend for instant
// offline pre-fill (no API call needed to seed the form).
// =============================================================================

import type { SMEFinancialData } from "./types";

export const MEDIAN_DEFAULTS: SMEFinancialData = {
  roa_c: 0.4724507510,
  roa_a: 0.5320553249,
  continuous_interest_rate: 0.7815367064,
  net_value_per_share_b: 0.1732333235,
  net_value_per_share_a: 0.1732333235,
  net_value_per_share_c: 0.1734018794,
  persistent_eps: 0.2115911884,
  per_share_net_profit: 0.1689343463,
  interest_expense_ratio: 0.6306122519,
  debt_ratio: 0.1561205497,
  net_worth_assets: 0.8438794503,
  borrowing_dependency: 0.3774359165,
  net_profit_paid_in_capital: 0.1679541179,
  retained_earnings: 0.9291504440,
  total_income_expense: 0.0022130871,
  net_income_total_assets: 0.7934734606,
  net_income_equity: 0.8399382414,
  liability_to_equity: 0.2819822002,
  interest_coverage_ratio: 0.5651583958,
  equity_to_liability: 0.0232401213,
};

export const PROFILE_HEALTHY: SMEFinancialData = {
  roa_c: 0.5101990755,
  roa_a: 0.5645483124,
  continuous_interest_rate: 0.7811546026,
  net_value_per_share_b: 0.1943670407,
  net_value_per_share_a: 0.1942756119,
  net_value_per_share_c: 0.1943248059,
  persistent_eps: 0.2327743732,
  per_share_net_profit: 0.1884357433,
  interest_expense_ratio: 0.6313819785,
  debt_ratio: 0.1106172146,
  net_worth_assets: 0.8893827854,
  borrowing_dependency: 0.3739696103,
  net_profit_paid_in_capital: 0.1863039832,
  retained_earnings: 0.9361581868,
  total_income_expense: 0.0024427588,
  net_income_total_assets: 0.8111407213,
  net_income_equity: 0.8409864856,
  liability_to_equity: 0.2797485083,
  interest_coverage_ratio: 0.5657041165,
  equity_to_liability: 0.0488247804,
};

export const PROFILE_DISTRESSED: SMEFinancialData = {
  roa_c: 0.4183976458,
  roa_a: 0.4657591781,
  continuous_interest_rate: 0.7811561521,
  net_value_per_share_b: 0.1633479032,
  net_value_per_share_a: 0.1628020119,
  net_value_per_share_c: 0.1630462265,
  persistent_eps: 0.1923470309,
  per_share_net_profit: 0.1519647785,
  interest_expense_ratio: 0.6306522965,
  debt_ratio: 0.1788368463,
  net_worth_assets: 0.8211631537,
  borrowing_dependency: 0.3844244754,
  net_profit_paid_in_capital: 0.1519429839,
  retained_earnings: 0.9067963727,
  total_income_expense: 0.0021013057,
  net_income_total_assets: 0.7413578792,
  net_income_equity: 0.8342608756,
  liability_to_equity: 0.2865768249,
  interest_coverage_ratio: 0.5643454621,
  equity_to_liability: 0.0227042267,
};

// =============================================================================
// FIELD_TOOLTIPS — plain-English explanation for each of the 20 financial
// ratios. Shown as hover popovers on the InputForm field labels so that
// loan officers (and examiners) understand what each metric measures.
//
// All values are normalised to [0, 1] before being fed to the model, so
// the "healthy direction" note guides the user on what end of the scale
// is favourable.
// =============================================================================
export const FIELD_TOOLTIPS: Record<keyof SMEFinancialData, string> = {
  roa_c:
    "Return on Assets (C) — measures profitability before both interest and depreciation charges, making it a cash-flow-oriented profitability indicator that strips out non-cash accounting adjustments. Higher values indicate better underlying operational asset efficiency. A low value relative to peers is an early distress signal.",

  roa_a:
    "Return on Assets (A) — measures how much net profit the company generates relative to its total assets, calculated before interest but after applying a percentage tax adjustment. Higher values indicate better asset utilisation and profitability. A low value is a strong distress signal.",

  continuous_interest_rate:
    "Continuous Interest Rate (After Tax) — the effective after-tax cost of the company's debt obligations expressed as a continuously compounded rate. A higher normalised value here means the company's interest burden is relatively manageable compared to peers.",

  net_value_per_share_b:
    "Net Value Per Share (B) — book value per share calculated using method B (typically based on total equity minus intangible assets). Reflects the per-share intrinsic worth of the company. Higher values signal stronger shareholder equity.",

  net_value_per_share_a:
    "Net Value Per Share (A) — book value per share using the standard equity calculation. Alongside (B) and (C), these three variants capture different nuances of per-share equity. Higher values indicate more asset backing per share.",

  net_value_per_share_c:
    "Net Value Per Share (C) — an alternative book value calculation that may adjust for revaluation reserves or retained earnings differently. Together with (A) and (B), it provides a triangulated view of per-share equity health.",

  persistent_eps:
    "Persistent EPS (Last Four Seasons) — earnings per share averaged or smoothed across the last four reporting periods. Using four periods removes one-off spikes, making this a reliable long-term profitability indicator. Consistently low values are a warning sign.",

  per_share_net_profit:
    "Per Share Net Profit Before Tax — the raw pre-tax profit divided by total shares outstanding. Unlike EPS, this is not adjusted for tax, so it better reflects operational profitability. Higher values indicate a more profitable business.",

  interest_expense_ratio:
    "Interest Expense Ratio — the proportion of revenue consumed by interest payments. A higher normalised value in this dataset means interest costs are relatively contained. Companies spending a large fraction of revenue on interest are more vulnerable to default.",

  debt_ratio:
    "Debt Ratio % — total liabilities divided by total assets. This is a core leverage indicator. A lower value means less of the company's assets are financed by debt. High debt ratios significantly increase default probability.",

  net_worth_assets:
    "Net Worth / Assets — the equity-to-assets ratio (the inverse of debt ratio). Represents the share of assets owned outright by shareholders. Higher values mean the company is less reliant on external debt and is more financially stable.",

  borrowing_dependency:
    "Borrowing Dependency — measures how dependent the company is on external borrowing to fund its operations, relative to its asset base. Higher dependency implies greater vulnerability to credit tightening or rising interest rates.",

  net_profit_paid_in_capital:
    "Net Profit Before Tax / Paid-in Capital — relates operating profitability to the original capital invested by shareholders. A higher ratio indicates the company is generating strong returns on the equity that shareholders have committed.",

  retained_earnings:
    "Retained Earnings to Total Assets — the proportion of total assets that have been internally funded through accumulated profits rather than debt or new equity. High retained earnings relative to assets signal long-term financial resilience.",

  total_income_expense:
    "Total Income / Total Expense — the income-to-expense efficiency ratio. A value above 1 means income exceeds expenses. This field is normalised, so values near 0 in this dataset actually represent the typical range — interpret alongside the model's SHAP output.",

  net_income_total_assets:
    "Net Income to Total Assets — after-tax net profit as a proportion of total assets. Similar to ROA but uses the bottom-line net income figure. It directly measures overall asset profitability. Higher is healthier.",

  net_income_equity:
    "Net Income to Stockholder's Equity — equivalent to Return on Equity (ROE). Measures how much profit the company generates for each unit of shareholder equity. Higher values mean shareholders' capital is being used more effectively.",

  liability_to_equity:
    "Liability to Equity — total liabilities divided by total equity (the debt-to-equity ratio). Lower values mean the company uses proportionally less debt relative to equity. Very high values indicate heavy financial leverage and elevated risk.",

  interest_coverage_ratio:
    "Interest Coverage Ratio (Interest Expense to EBIT) — EBIT (earnings before interest and tax) divided by interest expense. A higher ratio means the company can more comfortably service its debt. Values below 1.5x are typically considered a credit warning.",

  equity_to_liability:
    "Equity to Liability — the inverse of liability-to-equity. A higher value means equity substantially exceeds liabilities, indicating a very conservative capital structure. Low values (close to 0) suggest the company is heavily debt-funded.",
};

export const FEATURE_LABELS: Record<keyof SMEFinancialData, string> = {
  roa_c: "ROA(C) — Before Interest & Depreciation Before Interest",
  roa_a: "ROA(A) — Before Interest & % After Tax",
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
