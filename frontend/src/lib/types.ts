// =============================================================================
// SHIELD — Shared TypeScript types
// Mirror the Pydantic models in backend/main.py exactly.
// =============================================================================

// ---------------------------------------------------------------------------
// Financial input — 20 features in the exact order of model.feature_names_in_
// Keys are snake_case; order mirrors the RF model's training columns.
// ---------------------------------------------------------------------------
export interface SMEFinancialData {
  roa_c_before_interest_and_depreciation_before_interest: number;
  roa_a_before_interest_and_percent_after_tax:            number;
  roa_b_before_interest_and_depreciation_after_tax:       number;
  continuous_interest_rate_after_tax:                     number;
  net_value_per_share_b:                                  number;
  net_value_per_share_a:                                  number;
  persistent_eps_in_the_last_four_seasons:                number;
  per_share_net_profit_before_tax:                        number;
  interest_expense_ratio:                                 number;
  debt_ratio_percent:                                     number;
  net_worth_assets:                                       number;
  borrowing_dependency:                                   number;
  net_profit_before_tax_paid_in_capital:                  number;
  retained_earnings_to_total_assets:                      number;
  net_income_to_total_assets:                             number;
  net_income_to_stockholders_equity:                      number;
  liability_to_equity:                                    number;
  degree_of_financial_leverage_dfl:                       number;
  interest_coverage_ratio:                                number;
  equity_to_liability:                                    number;
}

// ---------------------------------------------------------------------------
// Evaluation metadata — collected via the identification gate modal
// ---------------------------------------------------------------------------
export interface EvaluationMeta {
  company_name: string;
  ssm_number:   string;
  loan_amount:  number;
  evaluator:    string;   // auto-filled from useAuth()
}

// ---------------------------------------------------------------------------
// Full /predict request payload
// ---------------------------------------------------------------------------
export interface PredictRequest {
  meta:       EvaluationMeta;
  financials: SMEFinancialData;
}

// ---------------------------------------------------------------------------
// Prediction response
// ---------------------------------------------------------------------------
export interface ShapFeature {
  label:      string;
  value:      number;
  shap_value: number;
  direction:  "risk" | "protective";
}

export interface AdvisoryReport {
  tone:               string;
  tone_level:         "critical" | "elevated" | "moderate" | "low";
  risk_drivers:       Array<{ label: string; shap_value: number }>;
  protective_factors: Array<{ label: string; shap_value: number }>;
  recommendation:     string;
  advisory_source:    "groq" | "rule-based" | "rate-limited";
}

export interface PredictionResponse {
  probability:     number;
  probability_pct: number;
  classification:  "Low Risk" | "Moderate Risk" | "High Risk" | "Critical Risk";
  is_high_risk:    boolean;
  shap_base_value: number;
  shap_features:   ShapFeature[];
  advisory:        AdvisoryReport;
}

// ---------------------------------------------------------------------------
// Audit log entry — returned by GET /logs
// ---------------------------------------------------------------------------
export interface LogEntry {
  id:                  number;
  company_name:        string;
  ssm_number:          string;
  loan_amount:         number;
  evaluator:           string;
  evaluated_at:        string;   // ISO-8601
  probability_default: number;
  risk_classification: "Low Risk" | "Moderate Risk" | "High Risk" | "Critical Risk";
  financial_inputs:    SMEFinancialData;
  shap_breakdown:      ShapFeature[];
  advisory_report:     string;
}

// ---------------------------------------------------------------------------
// /features endpoint
// ---------------------------------------------------------------------------
export interface FeatureMeta {
  key:    keyof SMEFinancialData;
  label:  string;
  median: number;
}

export interface FeaturesResponse {
  features: FeatureMeta[];
  profiles: {
    healthy:    SMEFinancialData;
    moderate:   SMEFinancialData;
    critical:   SMEFinancialData;
    distressed: SMEFinancialData;
  };
}
