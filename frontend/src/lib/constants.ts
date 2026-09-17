// =============================================================================
// SHIELD — Frontend constants
// Key order matches model.feature_names_in_ exactly (verified from the saved
// pipeline). Any reordering here will cause a column-mismatch 500 on /predict.
// =============================================================================

import type { SMEFinancialData } from "./types";

// ---------------------------------------------------------------------------
// Median defaults — dataset median values, keyed in training column order.
// ---------------------------------------------------------------------------
export const MEDIAN_DEFAULTS: SMEFinancialData = {
  roa_c_before_interest_and_depreciation_before_interest:     0.4732732879,
  roa_a_before_interest_and_percent_after_tax:                0.5351354922,
  roa_b_before_interest_and_depreciation_after_tax:           0.5240172754,
  continuous_interest_rate_after_tax:                         0.7815414092,
  net_value_per_share_b:                                      0.1739918250,
  net_value_per_share_a:                                      0.1739918250,
  persistent_eps_in_the_last_four_seasons:                    0.2123475466,
  per_share_net_profit_before_tax:                            0.1698745389,
  interest_expense_ratio:                                     0.6306122519,
  debt_ratio_percent:                                         0.1551878295,
  net_worth_assets:                                           0.8448121705,
  borrowing_dependency:                                       0.3774943933,
  net_profit_before_tax_paid_in_capital:                      0.1688788111,
  retained_earnings_to_total_assets:                          0.9299983779,
  net_income_to_total_assets:                                 0.7952664808,
  net_income_to_stockholders_equity:                          0.8400066940,
  liability_to_equity:                                        0.2819903757,
  degree_of_financial_leverage_dfl:                           0.0267911567,
  interest_coverage_ratio:                                    0.5651583958,
  equity_to_liability:                                        0.0233989920,
};

// ---------------------------------------------------------------------------
// Profile A — Healthy SME (Low Default Risk)
// Source: 50th percentile of healthy-class training samples.
// Verified by model: P(default) = 0.00%
// ---------------------------------------------------------------------------
export const PROFILE_HEALTHY: SMEFinancialData = {
  roa_c_before_interest_and_depreciation_before_interest:     0.5037780919,
  roa_a_before_interest_and_percent_after_tax:                0.5604012211,
  roa_b_before_interest_and_depreciation_after_tax:           0.5529203919,
  continuous_interest_rate_after_tax:                         0.7816381852,
  net_value_per_share_b:                                      0.1846951245,
  net_value_per_share_a:                                      0.1846951245,
  persistent_eps_in_the_last_four_seasons:                    0.2249220006,
  per_share_net_profit_before_tax:                            0.1799352263,
  interest_expense_ratio:                                     0.6307060862,
  debt_ratio_percent:                                         0.1094718384,
  net_worth_assets:                                           0.8905281616,
  borrowing_dependency:                                       0.3724733439,
  net_profit_before_tax_paid_in_capital:                      0.1787421763,
  retained_earnings_to_total_assets:                          0.9379042900,
  net_income_to_total_assets:                                 0.8112314879,
  net_income_to_stockholders_equity:                          0.8412064442,
  liability_to_equity:                                        0.2786760063,
  degree_of_financial_leverage_dfl:                           0.0268105994,
  interest_coverage_ratio:                                    0.5652639072,
  equity_to_liability:                                        0.0344557638,
};

// ---------------------------------------------------------------------------
// Profile C — Moderate Risk SME
// Source: Real training row (idx 4915), bankrupt class.
// Verified by model: P(default) = 42.50%  →  Moderate Risk (30–49%)
// ---------------------------------------------------------------------------
export const PROFILE_MODERATE: SMEFinancialData = {
  roa_c_before_interest_and_depreciation_before_interest:     0.2313654756,
  roa_a_before_interest_and_percent_after_tax:                0.1627780201,
  roa_b_before_interest_and_depreciation_after_tax:           0.2067562503,
  continuous_interest_rate_after_tax:                         0.7801268831,
  net_value_per_share_b:                                      0.1350975517,
  net_value_per_share_a:                                      0.1350975517,
  persistent_eps_in_the_last_four_seasons:                    0.1598752009,
  per_share_net_profit_before_tax:                            0.1271371545,
  interest_expense_ratio:                                     0.6305584855,
  debt_ratio_percent:                                         0.2080902137,
  net_worth_assets:                                           0.7919097863,
  borrowing_dependency:                                       0.3831738178,
  net_profit_before_tax_paid_in_capital:                      0.1261217103,
  retained_earnings_to_total_assets:                          0.8277666581,
  net_income_to_total_assets:                                 0.5269117307,
  net_income_to_stockholders_equity:                          0.7984852056,
  liability_to_equity:                                        0.2903251996,
  degree_of_financial_leverage_dfl:                           0.0267721521,
  interest_coverage_ratio:                                    0.5650661185,
  equity_to_liability:                                        0.0164195794,
};

// ---------------------------------------------------------------------------
// Profile D — Critical Risk SME
// Source: Real training row (idx 5585), bankrupt class.
// Verified by model: P(default) = 75.00%  →  Critical Risk (70–100%)
// ---------------------------------------------------------------------------
export const PROFILE_CRITICAL: SMEFinancialData = {
  roa_c_before_interest_and_depreciation_before_interest:     0.5120199887,
  roa_a_before_interest_and_percent_after_tax:                0.5422359131,
  roa_b_before_interest_and_depreciation_after_tax:           0.5531457389,
  continuous_interest_rate_after_tax:                         0.7816009533,
  net_value_per_share_b:                                      0.1869820500,
  net_value_per_share_a:                                      0.1869820500,
  persistent_eps_in_the_last_four_seasons:                    0.2187794559,
  per_share_net_profit_before_tax:                            0.1754886524,
  interest_expense_ratio:                                     0.6318576236,
  debt_ratio_percent:                                         0.0962210375,
  net_worth_assets:                                           0.9037789625,
  borrowing_dependency:                                       0.3729598336,
  net_profit_before_tax_paid_in_capital:                      0.1744981147,
  retained_earnings_to_total_assets:                          0.9425178458,
  net_income_to_total_assets:                                 0.8016045267,
  net_income_to_stockholders_equity:                          0.8404271483,
  liability_to_equity:                                        0.2779817096,
  degree_of_financial_leverage_dfl:                           0.0269848167,
  interest_coverage_ratio:                                    0.5659031109,
  equity_to_liability:                                        0.0395780864,
};

// ---------------------------------------------------------------------------
// Profile B — Distressed SME (High Default Risk)
// Source: 40th percentile of bankrupt-class training samples.
// Verified by model: P(default) = 89.00%
// ---------------------------------------------------------------------------
export const PROFILE_DISTRESSED: SMEFinancialData = {
  roa_c_before_interest_and_depreciation_before_interest:     0.4228234844,
  roa_a_before_interest_and_percent_after_tax:                0.4689850218,
  roa_b_before_interest_and_depreciation_after_tax:           0.4715291797,
  continuous_interest_rate_after_tax:                         0.7812369945,
  net_value_per_share_b:                                      0.1543982211,
  net_value_per_share_a:                                      0.1543982211,
  persistent_eps_in_the_last_four_seasons:                    0.1901531696,
  per_share_net_profit_before_tax:                            0.1483734423,
  interest_expense_ratio:                                     0.6300544748,
  debt_ratio_percent:                                         0.1809170010,
  net_worth_assets:                                           0.8051677310,
  borrowing_dependency:                                       0.3814089300,
  net_profit_before_tax_paid_in_capital:                      0.1488356255,
  retained_earnings_to_total_assets:                          0.9100849445,
  net_income_to_total_assets:                                 0.7518520655,
  net_income_to_stockholders_equity:                          0.8340502626,
  liability_to_equity:                                        0.2850218010,
  degree_of_financial_leverage_dfl:                           0.0266330871,
  interest_coverage_ratio:                                    0.5643908424,
  equity_to_liability:                                        0.0178351829,
};

// =============================================================================
// FIELD_TOOLTIPS — plain-English explanation for each of the 20 financial
// ratios shown as hover popovers on the InputForm field labels.
// =============================================================================
export const FIELD_TOOLTIPS: Record<keyof SMEFinancialData, string> = {
  roa_c_before_interest_and_depreciation_before_interest:
    "Return on Assets (C) — measures profitability before both interest and depreciation charges, making it a cash-flow-oriented indicator that strips out non-cash adjustments. Higher values indicate better underlying operational asset efficiency. A low value relative to peers is an early distress signal.",

  roa_a_before_interest_and_percent_after_tax:
    "Return on Assets (A) — measures how much net profit the company generates relative to its total assets, calculated before interest but after a percentage tax adjustment. Higher values indicate better asset utilisation and profitability. A low value is a strong distress signal.",

  roa_b_before_interest_and_depreciation_after_tax:
    "Return on Assets (B) — measures profitability before interest but after depreciation and tax. This variant bridges the gap between the cash-flow-focused ROA(C) and the fully adjusted ROA(A), offering a balanced view of asset profitability net of capital consumption.",

  continuous_interest_rate_after_tax:
    "Continuous Interest Rate (After Tax) — the effective after-tax cost of the company's debt obligations expressed as a continuously compounded rate. A higher normalised value here means the company's interest burden is relatively manageable compared to peers.",

  net_value_per_share_b:
    "Net Value Per Share (B) — book value per share calculated using method B (typically total equity minus intangible assets). Reflects the per-share intrinsic worth of the company. Higher values signal stronger shareholder equity.",

  net_value_per_share_a:
    "Net Value Per Share (A) — book value per share using the standard equity calculation. Higher values indicate more asset backing per share and stronger shareholder equity.",

  persistent_eps_in_the_last_four_seasons:
    "Persistent EPS (Last Four Seasons) — earnings per share averaged across the last four reporting periods. Using four periods removes one-off spikes, making this a reliable long-term profitability indicator. Consistently low values are a warning sign.",

  per_share_net_profit_before_tax:
    "Per Share Net Profit Before Tax — raw pre-tax profit divided by total shares outstanding. Unlike EPS, this is not adjusted for tax, so it better reflects operational profitability. Higher values indicate a more profitable business.",

  interest_expense_ratio:
    "Interest Expense Ratio — the proportion of revenue consumed by interest payments. Lower values here mean interest costs are relatively high. Companies spending a large fraction of revenue on interest are more vulnerable to default.",

  debt_ratio_percent:
    "Debt Ratio % — total liabilities divided by total assets. A core leverage indicator. A lower value means less of the company's assets are financed by debt. High debt ratios significantly increase default probability.",

  net_worth_assets:
    "Net Worth / Assets — the equity-to-assets ratio (inverse of debt ratio). Represents the share of assets owned outright by shareholders. Higher values mean the company is less reliant on external debt and is more financially stable.",

  borrowing_dependency:
    "Borrowing Dependency — measures how dependent the company is on external borrowing to fund its operations, relative to its asset base. Higher dependency implies greater vulnerability to credit tightening or rising interest rates.",

  net_profit_before_tax_paid_in_capital:
    "Net Profit Before Tax / Paid-in Capital — relates operating profitability to the original capital invested by shareholders. A higher ratio indicates the company is generating strong returns on committed equity.",

  retained_earnings_to_total_assets:
    "Retained Earnings to Total Assets — the proportion of total assets internally funded through accumulated profits rather than debt or new equity. High retained earnings relative to assets signal long-term financial resilience.",

  net_income_to_total_assets:
    "Net Income to Total Assets — after-tax net profit as a proportion of total assets. Similar to ROA but uses the bottom-line net income figure. It directly measures overall asset profitability. Higher is healthier.",

  net_income_to_stockholders_equity:
    "Net Income to Stockholder's Equity — equivalent to Return on Equity (ROE). Measures how much profit the company generates for each unit of shareholder equity. Higher values mean shareholders' capital is being used more effectively.",

  liability_to_equity:
    "Liability to Equity — total liabilities divided by total equity (debt-to-equity ratio). Lower values mean the company uses proportionally less debt relative to equity. Very high values indicate heavy financial leverage and elevated default risk.",

  degree_of_financial_leverage_dfl:
    "Degree of Financial Leverage (DFL) — measures how sensitive a company's earnings per share are to changes in operating income, driven by fixed financial costs (interest). A high DFL means small revenue changes cause large swings in profitability, significantly elevating default risk.",

  interest_coverage_ratio:
    "Interest Coverage Ratio (Interest Expense to EBIT) — EBIT divided by interest expense. A higher ratio means the company can more comfortably service its debt. Values below 1.5× are typically considered a credit warning.",

  equity_to_liability:
    "Equity to Liability — the inverse of liability-to-equity. A higher value means equity substantially exceeds liabilities, indicating a conservative capital structure. Low values (close to 0) suggest the company is heavily debt-funded.",
};

export const FEATURE_LABELS: Record<keyof SMEFinancialData, string> = {
  roa_c_before_interest_and_depreciation_before_interest:     "ROA(C) — Before Interest & Depreciation Before Interest",
  roa_a_before_interest_and_percent_after_tax:                "ROA(A) — Before Interest & % After Tax",
  roa_b_before_interest_and_depreciation_after_tax:           "ROA(B) — Before Interest & Depreciation After Tax",
  continuous_interest_rate_after_tax:                         "Continuous Interest Rate (After Tax)",
  net_value_per_share_b:                                      "Net Value Per Share (B)",
  net_value_per_share_a:                                      "Net Value Per Share (A)",
  persistent_eps_in_the_last_four_seasons:                    "Persistent EPS in the Last Four Seasons",
  per_share_net_profit_before_tax:                            "Per Share Net Profit Before Tax",
  interest_expense_ratio:                                     "Interest Expense Ratio",
  debt_ratio_percent:                                         "Debt Ratio %",
  net_worth_assets:                                           "Net Worth / Assets",
  borrowing_dependency:                                       "Borrowing Dependency",
  net_profit_before_tax_paid_in_capital:                      "Net Profit Before Tax / Paid-in Capital",
  retained_earnings_to_total_assets:                          "Retained Earnings to Total Assets",
  net_income_to_total_assets:                                 "Net Income to Total Assets",
  net_income_to_stockholders_equity:                          "Net Income to Stockholder's Equity",
  liability_to_equity:                                        "Liability to Equity",
  degree_of_financial_leverage_dfl:                           "Degree of Financial Leverage (DFL)",
  interest_coverage_ratio:                                    "Interest Coverage Ratio (Interest Expense to EBIT)",
  equity_to_liability:                                        "Equity to Liability",
};
