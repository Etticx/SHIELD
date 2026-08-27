# =============================================================================
# SHIELD — FastAPI Backend
# Prediction endpoint: POST /predict
# Startup: loads XGBoost model + SHAP TreeExplainer once, reuses per request.
# =============================================================================

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import numpy as np
import pandas as pd
import shap
import joblib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger("shield.api")

# ---------------------------------------------------------------------------
# Feature registry
# The model was trained on these exact column names (note the leading space).
# Order is fixed — the Pydantic model mirrors this sequence.
# ---------------------------------------------------------------------------
FEATURE_NAMES: list[str] = [
    " ROA(A) before interest and % after tax",
    " ROA(B) before interest and depreciation after tax",
    " Continuous interest rate (after tax)",
    " Net Value Per Share (B)",
    " Net Value Per Share (A)",
    " Net Value Per Share (C)",
    " Persistent EPS in the Last Four Seasons",
    " Per Share Net profit before tax",
    " Interest Expense Ratio",
    " Debt ratio %",
    " Net worth/Assets",
    " Borrowing dependency",
    " Net profit before tax/Paid-in capital",
    " Retained Earnings to Total Assets",
    " Total income/Total expense",
    " Net Income to Total Assets",
    " Net Income to Stockholder's Equity",
    " Liability to Equity",
    " Interest Coverage Ratio (Interest expense to EBIT)",
    " Equity to Liability",
]

# Clean human-readable labels (same order — used in the SHAP response)
FEATURE_LABELS: list[str] = [
    "ROA(A) — Before Interest & % After Tax",
    "ROA(B) — Before Interest & Depreciation After Tax",
    "Continuous Interest Rate (After Tax)",
    "Net Value Per Share (B)",
    "Net Value Per Share (A)",
    "Net Value Per Share (C)",
    "Persistent EPS in the Last Four Seasons",
    "Per Share Net Profit Before Tax",
    "Interest Expense Ratio",
    "Debt Ratio %",
    "Net Worth / Assets",
    "Borrowing Dependency",
    "Net Profit Before Tax / Paid-in Capital",
    "Retained Earnings to Total Assets",
    "Total Income / Total Expense",
    "Net Income to Total Assets",
    "Net Income to Stockholder's Equity",
    "Liability to Equity",
    "Interest Coverage Ratio (Interest Expense to EBIT)",
    "Equity to Liability",
]

# Median defaults (for the template endpoint)
MEDIAN_DEFAULTS: dict[str, float] = {
    " ROA(A) before interest and % after tax":                 0.5598,
    " ROA(B) before interest and depreciation after tax":      0.5523,
    " Continuous interest rate (after tax)":                   0.7816,
    " Net Value Per Share (B)":                                0.1844,
    " Net Value Per Share (A)":                                0.1844,
    " Net Value Per Share (C)":                                0.1844,
    " Persistent EPS in the Last Four Seasons":                0.2245,
    " Per Share Net profit before tax":                        0.1797,
    " Interest Expense Ratio":                                 0.6307,
    " Debt ratio %":                                           0.1114,
    " Net worth/Assets":                                       0.8886,
    " Borrowing dependency":                                   0.3726,
    " Net profit before tax/Paid-in capital":                  0.1785,
    " Retained Earnings to Total Assets":                      0.9377,
    " Total income/Total expense":                             0.0023,
    " Net Income to Total Assets":                             0.8106,
    " Net Income to Stockholder's Equity":                     0.8412,
    " Liability to Equity":                                    0.2788,
    " Interest Coverage Ratio (Interest expense to EBIT)":     0.5653,
    " Equity to Liability":                                    0.0338,
}

# Hardcoded test profiles
PROFILE_A_HEALTHY: dict[str, float] = {
    " ROA(A) before interest and % after tax":                 0.586840,
    " ROA(B) before interest and depreciation after tax":      0.588040,
    " Continuous interest rate (after tax)":                   0.781608,
    " Net Value Per Share (B)":                                0.185032,
    " Net Value Per Share (A)":                                0.185032,
    " Net Value Per Share (C)":                                0.185032,
    " Persistent EPS in the Last Four Seasons":                0.248842,
    " Per Share Net profit before tax":                        0.204188,
    " Interest Expense Ratio":                                 0.630613,
    " Debt ratio %":                                           0.165221,
    " Net worth/Assets":                                       0.834779,
    " Borrowing dependency":                                   0.369637,
    " Net profit before tax/Paid-in capital":                  0.202783,
    " Retained Earnings to Total Assets":                      0.942190,
    " Total income/Total expense":                             0.002269,
    " Net Income to Total Assets":                             0.827921,
    " Net Income to Stockholder's Equity":                     0.843384,
    " Liability to Equity":                                    0.283137,
    " Interest Coverage Ratio (Interest expense to EBIT)":     0.565159,
    " Equity to Liability":                                    0.021680,
}

PROFILE_B_DISTRESSED: dict[str, float] = {
    " ROA(A) before interest and % after tax":                 0.211023,
    " ROA(B) before interest and depreciation after tax":      0.221425,
    " Continuous interest rate (after tax)":                   0.780388,
    " Net Value Per Share (B)":                                0.069656,
    " Net Value Per Share (A)":                                0.069656,
    " Net Value Per Share (C)":                                0.069656,
    " Persistent EPS in the Last Four Seasons":                0.079512,
    " Per Share Net profit before tax":                        0.054304,
    " Interest Expense Ratio":                                 0.630536,
    " Debt ratio %":                                           0.525410,
    " Net worth/Assets":                                       0.474590,
    " Borrowing dependency":                                   0.357056,
    " Net profit before tax/Paid-in capital":                  0.057130,
    " Retained Earnings to Total Assets":                      0.777637,
    " Total income/Total expense":                             0.001996,
    " Net Income to Total Assets":                             0.519388,
    " Net Income to Stockholder's Equity":                     0.856906,
    " Liability to Equity":                                    0.259280,
    " Interest Coverage Ratio (Interest expense to EBIT)":     0.565052,
    " Equity to Liability":                                    0.003946,
}

# ---------------------------------------------------------------------------
# Application state (loaded once at startup via lifespan)
# ---------------------------------------------------------------------------
class AppState:
    model: Any = None
    explainer: Any = None


app_state = AppState()


# ---------------------------------------------------------------------------
# Lifespan: load heavy assets once, share across all requests
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading XGBoost model …")
    app_state.model = joblib.load(settings.model_path)

    logger.info("Building SHAP TreeExplainer …")
    app_state.explainer = shap.TreeExplainer(
        app_state.model,
        feature_perturbation="tree_path_dependent",
    )

    logger.info("SHIELD backend ready.")
    yield

    # Cleanup (nothing needed for in-memory objects)
    logger.info("SHIELD backend shutting down.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SHIELD API",
    description="SME Health Indicator and Evaluator for Loan Decision — prediction endpoint.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic I/O models
# ---------------------------------------------------------------------------

class SMEFinancialData(BaseModel):
    """
    The 20 normalised financial ratios the model expects.
    All values are floats in the range [0, 1] (post-preprocessing).
    Field aliases use the exact internal column names (with leading space)
    so the frontend can send clean camelCase keys and we remap them here.
    """

    roa_a: float = Field(..., ge=0.0, le=1.0, description="ROA(A) before interest & % after tax")
    roa_b: float = Field(..., ge=0.0, le=1.0, description="ROA(B) before interest & depreciation after tax")
    continuous_interest_rate: float = Field(..., ge=0.0, le=1.0, description="Continuous interest rate (after tax)")
    net_value_per_share_b: float = Field(..., ge=0.0, le=1.0, description="Net Value Per Share (B)")
    net_value_per_share_a: float = Field(..., ge=0.0, le=1.0, description="Net Value Per Share (A)")
    net_value_per_share_c: float = Field(..., ge=0.0, le=1.0, description="Net Value Per Share (C)")
    persistent_eps: float = Field(..., ge=0.0, le=1.0, description="Persistent EPS in the Last Four Seasons")
    per_share_net_profit: float = Field(..., ge=0.0, le=1.0, description="Per Share Net Profit Before Tax")
    interest_expense_ratio: float = Field(..., ge=0.0, le=1.0, description="Interest Expense Ratio")
    debt_ratio: float = Field(..., ge=0.0, le=1.0, description="Debt Ratio %")
    net_worth_assets: float = Field(..., ge=0.0, le=1.0, description="Net Worth / Assets")
    borrowing_dependency: float = Field(..., ge=0.0, le=1.0, description="Borrowing Dependency")
    net_profit_paid_in_capital: float = Field(..., ge=0.0, le=1.0, description="Net Profit Before Tax / Paid-in Capital")
    retained_earnings: float = Field(..., ge=0.0, le=1.0, description="Retained Earnings to Total Assets")
    total_income_expense: float = Field(..., ge=0.0, le=1.0, description="Total Income / Total Expense")
    net_income_total_assets: float = Field(..., ge=0.0, le=1.0, description="Net Income to Total Assets")
    net_income_equity: float = Field(..., ge=0.0, le=1.0, description="Net Income to Stockholder's Equity")
    liability_to_equity: float = Field(..., ge=0.0, le=1.0, description="Liability to Equity")
    interest_coverage_ratio: float = Field(..., ge=0.0, le=1.0, description="Interest Coverage Ratio (Interest Expense to EBIT)")
    equity_to_liability: float = Field(..., ge=0.0, le=1.0, description="Equity to Liability")

    def to_feature_array(self) -> list[float]:
        """Return values in the exact column order the model expects."""
        return [
            self.roa_a,
            self.roa_b,
            self.continuous_interest_rate,
            self.net_value_per_share_b,
            self.net_value_per_share_a,
            self.net_value_per_share_c,
            self.persistent_eps,
            self.per_share_net_profit,
            self.interest_expense_ratio,
            self.debt_ratio,
            self.net_worth_assets,
            self.borrowing_dependency,
            self.net_profit_paid_in_capital,
            self.retained_earnings,
            self.total_income_expense,
            self.net_income_total_assets,
            self.net_income_equity,
            self.liability_to_equity,
            self.interest_coverage_ratio,
            self.equity_to_liability,
        ]


class ShapFeature(BaseModel):
    label: str
    value: float          # raw feature value
    shap_value: float     # contribution to log-odds (positive = risk-increasing)
    direction: str        # "risk" | "protective"


class PredictionResponse(BaseModel):
    probability: float            # P(default) in [0, 1]
    probability_pct: float        # e.g. 73.4
    classification: str           # "High Risk" | "Low Risk"
    is_high_risk: bool
    shap_base_value: float
    shap_features: list[ShapFeature]   # all 20, sorted by |shap_value| desc
    advisory: AdvisoryReport


class AdvisoryReport(BaseModel):
    tone: str
    tone_level: str               # "critical" | "elevated" | "moderate" | "low"
    risk_drivers: list[dict]      # [{label, shap_value}]
    protective_factors: list[dict]
    recommendation: str


# Rebuild so PredictionResponse resolves the forward ref AdvisoryReport
PredictionResponse.model_rebuild()


# ---------------------------------------------------------------------------
# Business logic helpers
# ---------------------------------------------------------------------------

def _compute_shap(input_df: pd.DataFrame) -> tuple[np.ndarray, float]:
    """
    Run SHAP on a single-row DataFrame.
    Returns (shap_values_class1, base_value_class1).
    """
    sv_obj = app_state.explainer(input_df.values)

    if sv_obj.values.ndim == 3:
        sv       = sv_obj.values[0, :, 1]
        base_val = float(sv_obj.base_values[0, 1])
    else:
        sv       = sv_obj.values[0]
        base_val = float(sv_obj.base_values[0])

    return sv, base_val


def _build_advisory(shap_values: np.ndarray, prob: float) -> AdvisoryReport:
    pairs = list(zip(FEATURE_LABELS, shap_values))

    if prob >= 0.70:
        tone       = "Critical Risk Detected. The model indicates a very high likelihood of financial distress."
        tone_level = "critical"
    elif prob >= 0.50:
        tone       = "Elevated Risk Detected. The SME exhibits several financial vulnerabilities."
        tone_level = "elevated"
    elif prob >= 0.30:
        tone       = "Moderate Risk. The SME shows some concerning signals but maintains core financial health."
        tone_level = "moderate"
    else:
        tone       = "Low Risk. The SME appears financially healthy with strong fundamental indicators."
        tone_level = "low"

    risk_drivers = [
        {"label": l, "shap_value": round(float(v), 6)}
        for l, v in sorted([(l, v) for l, v in pairs if v > 0], key=lambda x: x[1], reverse=True)[:3]
    ]
    protective_factors = [
        {"label": l, "shap_value": round(float(v), 6)}
        for l, v in sorted([(l, v) for l, v in pairs if v < 0], key=lambda x: x[1])[:3]
    ]

    if prob >= 0.50:
        recommendation = (
            "Loan approval should be approached with caution. A detailed due-diligence review of "
            "the flagged risk drivers is strongly advised. Consider requesting collateral or "
            "imposing covenant-based conditions before disbursement."
        )
    else:
        recommendation = (
            "The financial profile supports a favourable loan consideration. Standard monitoring "
            "of the identified risk drivers is recommended throughout the loan tenure."
        )

    return AdvisoryReport(
        tone=tone,
        tone_level=tone_level,
        risk_drivers=risk_drivers,
        protective_factors=protective_factors,
        recommendation=recommendation,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
async def root() -> dict:
    return {"status": "ok", "service": "SHIELD API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health() -> dict:
    model_loaded = app_state.model is not None
    explainer_loaded = app_state.explainer is not None
    return {
        "status": "healthy" if (model_loaded and explainer_loaded) else "degraded",
        "model_loaded": model_loaded,
        "explainer_loaded": explainer_loaded,
    }


@app.get("/features", tags=["Meta"])
async def get_features() -> dict:
    """
    Returns the feature registry so the frontend can build the form
    dynamically without hardcoding labels.
    """
    return {
        "features": [
            {
                "key": key,               # camelCase Pydantic field name
                "label": label,           # human-readable display label
                "median": MEDIAN_DEFAULTS[name],
            }
            for key, label, name in zip(
                SMEFinancialData.model_fields.keys(),
                FEATURE_LABELS,
                FEATURE_NAMES,
            )
        ],
        "profiles": {
            "healthy":    {k: v for k, v in zip(SMEFinancialData.model_fields.keys(), PROFILE_A_HEALTHY.values())},
            "distressed": {k: v for k, v in zip(SMEFinancialData.model_fields.keys(), PROFILE_B_DISTRESSED.values())},
        },
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(data: SMEFinancialData) -> PredictionResponse:
    """
    Accepts 20 normalised financial ratios, returns:
    - P(default) probability
    - Risk classification
    - SHAP feature contributions (all 20, sorted by absolute impact)
    - AI Advisory Report
    """
    if app_state.model is None or app_state.explainer is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Try again shortly.")

    # Build DataFrame with exact column names the model expects
    feature_array = data.to_feature_array()
    input_df = pd.DataFrame([feature_array], columns=FEATURE_NAMES)

    # Prediction
    prob_bankrupt = float(app_state.model.predict_proba(input_df)[0][1])
    is_high_risk  = prob_bankrupt >= 0.50

    # SHAP
    shap_vals, base_val = _compute_shap(input_df)

    # Build sorted SHAP feature list (by absolute impact, descending)
    shap_features: list[ShapFeature] = []
    for i, (label, sv) in enumerate(zip(FEATURE_LABELS, shap_vals)):
        shap_features.append(
            ShapFeature(
                label=label,
                value=round(feature_array[i], 6),
                shap_value=round(float(sv), 6),
                direction="risk" if sv > 0 else "protective",
            )
        )
    shap_features.sort(key=lambda x: abs(x.shap_value), reverse=True)

    # Advisory
    advisory = _build_advisory(shap_vals, prob_bankrupt)

    return PredictionResponse(
        probability=round(prob_bankrupt, 6),
        probability_pct=round(prob_bankrupt * 100, 2),
        classification="High Risk" if is_high_risk else "Low Risk",
        is_high_risk=is_high_risk,
        shap_base_value=round(base_val, 6),
        shap_features=shap_features,
        advisory=advisory,
    )
