// =============================================================================
// SHIELD — Shared TypeScript types
// Mirror the Pydantic models in backend/main.py exactly.
// =============================================================================

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
  financial_inputs:    Record<string, number>;
  shap_breakdown:      ShapFeature[];
  advisory_report:     string;
}
