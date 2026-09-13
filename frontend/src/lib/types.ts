// =============================================================================
// SHIELD — Shared TypeScript types
// Mirror the Pydantic models in backend/main.py exactly.
// =============================================================================

// ---------------------------------------------------------------------------
// Financial input (20 normalised ratios)
// ---------------------------------------------------------------------------
export interface SMEFinancialData {
  roa_c: number;
  roa_a: number;
  continuous_interest_rate: number;
  net_value_per_share_b: number;
  net_value_per_share_a: number;
  net_value_per_share_c: number;
  persistent_eps: number;
  per_share_net_profit: number;
  interest_expense_ratio: number;
  debt_ratio: number;
  net_worth_assets: number;
  borrowing_dependency: number;
  net_profit_paid_in_capital: number;
  retained_earnings: number;
  total_income_expense: number;
  net_income_total_assets: number;
  net_income_equity: number;
  liability_to_equity: number;
  interest_coverage_ratio: number;
  equity_to_liability: number;
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
  classification:  "High Risk" | "Low Risk";
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
  risk_classification: "High Risk" | "Low Risk";
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
    distressed: SMEFinancialData;
  };
}
