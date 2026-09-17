# =============================================================================
# SHIELD — FastAPI Backend
# Prediction endpoint: POST /predict
# Startup: loads Random Forest model + SHAP TreeExplainer once, reuses per request.
#
# Advisory engine: dynamically generated via Groq API (openai/gpt-oss-120b)
# when GROQ_API_KEY is set in backend/.env.
# Falls back gracefully to rule-based text if the key is absent or the API
# call fails — the application never crashes due to a Groq error.
#
# Persistence: every evaluation is saved to PostgreSQL when DATABASE_URL is
# set in backend/.env.  Falls back gracefully if DB is unavailable.
# =============================================================================

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
import shap
import joblib

from fastapi import FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

from config import settings
from database import init_db, close_db, get_session, Evaluation

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger("shield.api")

# ---------------------------------------------------------------------------
# Groq async client — initialised once at startup if API key is present.
# AsyncGroq integrates natively with FastAPI's event loop — no thread pool.
# Model: openai/gpt-oss-120b
#   • ~500 t/s on Groq's LPU hardware
#   • Free tier available (no credit card required)
#   • 131k context window, 65k max completion tokens
# ---------------------------------------------------------------------------
_groq_client: Any = None
_GROQ_MODEL   = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "You are a Senior Credit Risk Analyst at JuneBank, a commercial bank operating "
    "under Bank Negara Malaysia (BNM) regulatory guidelines. Your role is to advise "
    "loan officers on SME credit applications based purely on quantitative financial "
    "data and SHAP model explainability output. You communicate in clear, professional "
    "English. You never invent numbers, ratios, or facts beyond what is explicitly "
    "provided in the prompt. You are concise, precise, and actionable."
)


def _init_groq() -> None:
    """Attempt to instantiate the async Groq client at startup."""
    global _groq_client
    if not settings.groq_api_key:
        logger.warning(
            "GROQ_API_KEY not set — advisory engine running in rule-based fallback mode."
        )
        return
    try:
        from groq import AsyncGroq  # type: ignore
        _groq_client = AsyncGroq(api_key=settings.groq_api_key)
        logger.info("Groq async client initialised (%s).", _GROQ_MODEL)
    except Exception as exc:
        logger.warning("Failed to initialise Groq client: %s — using fallback.", exc)
        _groq_client = None


# ---------------------------------------------------------------------------
# Feature registry — exact column names and order from model.feature_names_in_
#
# These were verified by inspecting the saved pipeline:
#   clf.feature_names_in_  (RandomForestClassifier, final pipeline step)
# Order MUST match training exactly — the DataFrame passed to predict_proba
# uses these as column headers.
# ---------------------------------------------------------------------------
FEATURE_NAMES: list[str] = [
    " ROA(C) before interest and depreciation before interest",
    " ROA(A) before interest and % after tax",
    " ROA(B) before interest and depreciation after tax",
    " Continuous interest rate (after tax)",
    " Net Value Per Share (B)",
    " Net Value Per Share (A)",
    " Persistent EPS in the Last Four Seasons",
    " Per Share Net profit before tax",
    " Interest Expense Ratio",
    " Debt ratio %",
    " Net worth/Assets",
    " Borrowing dependency",
    " Net profit before tax/Paid-in capital",
    " Retained Earnings to Total Assets",
    " Net Income to Total Assets",
    " Net Income to Stockholder's Equity",
    " Liability to Equity",
    " Degree of Financial Leverage (DFL)",
    " Interest Coverage Ratio (Interest expense to EBIT)",
    " Equity to Liability",
]

FEATURE_LABELS: list[str] = [
    "ROA(C) — Before Interest & Depreciation Before Interest",
    "ROA(A) — Before Interest & % After Tax",
    "ROA(B) — Before Interest & Depreciation After Tax",
    "Continuous Interest Rate (After Tax)",
    "Net Value Per Share (B)",
    "Net Value Per Share (A)",
    "Persistent EPS in the Last Four Seasons",
    "Per Share Net Profit Before Tax",
    "Interest Expense Ratio",
    "Debt Ratio %",
    "Net Worth / Assets",
    "Borrowing Dependency",
    "Net Profit Before Tax / Paid-in Capital",
    "Retained Earnings to Total Assets",
    "Net Income to Total Assets",
    "Net Income to Stockholder's Equity",
    "Liability to Equity",
    "Degree of Financial Leverage (DFL)",
    "Interest Coverage Ratio (Interest Expense to EBIT)",
    "Equity to Liability",
]

MEDIAN_DEFAULTS: dict[str, float] = {
    " ROA(C) before interest and depreciation before interest":    0.4732732879,
    " ROA(A) before interest and % after tax":                     0.5351354922,
    " ROA(B) before interest and depreciation after tax":          0.5240172754,
    " Continuous interest rate (after tax)":                       0.7815414092,
    " Net Value Per Share (B)":                                    0.1739918250,
    " Net Value Per Share (A)":                                    0.1739918250,
    " Persistent EPS in the Last Four Seasons":                    0.2123475466,
    " Per Share Net profit before tax":                            0.1698745389,
    " Interest Expense Ratio":                                     0.6306122519,
    " Debt ratio %":                                               0.1551878295,
    " Net worth/Assets":                                           0.8448121705,
    " Borrowing dependency":                                       0.3774943933,
    " Net profit before tax/Paid-in capital":                      0.1688788111,
    " Retained Earnings to Total Assets":                          0.9299983779,
    " Net Income to Total Assets":                                 0.7952664808,
    " Net Income to Stockholder's Equity":                         0.8400066940,
    " Liability to Equity":                                        0.2819903757,
    " Degree of Financial Leverage (DFL)":                         0.0267911567,
    " Interest Coverage Ratio (Interest expense to EBIT)":         0.5651583958,
    " Equity to Liability":                                        0.0233989920,
}

# Profile A — Healthy SME (Low Default Risk)
# Derived from 50th percentile of healthy-class training samples.
# Verified P(default) = 0.00%
PROFILE_A_HEALTHY: dict[str, float] = {
    " ROA(C) before interest and depreciation before interest":    0.5037780919,
    " ROA(A) before interest and % after tax":                     0.5604012211,
    " ROA(B) before interest and depreciation after tax":          0.5529203919,
    " Continuous interest rate (after tax)":                       0.7816381852,
    " Net Value Per Share (B)":                                    0.1846951245,
    " Net Value Per Share (A)":                                    0.1846951245,
    " Persistent EPS in the Last Four Seasons":                    0.2249220006,
    " Per Share Net profit before tax":                            0.1799352263,
    " Interest Expense Ratio":                                     0.6307060862,
    " Debt ratio %":                                               0.1094718384,
    " Net worth/Assets":                                           0.8905281616,
    " Borrowing dependency":                                       0.3724733439,
    " Net profit before tax/Paid-in capital":                      0.1787421763,
    " Retained Earnings to Total Assets":                          0.9379042900,
    " Net Income to Total Assets":                                 0.8112314879,
    " Net Income to Stockholder's Equity":                         0.8412064442,
    " Liability to Equity":                                        0.2786760063,
    " Degree of Financial Leverage (DFL)":                         0.0268105994,
    " Interest Coverage Ratio (Interest expense to EBIT)":         0.5652639072,
    " Equity to Liability":                                        0.0344557638,
}

# Profile C — Moderate Risk SME
# Real training row (idx 4915) from the bankrupt class.
# Verified P(default) = 42.50%  →  Moderate Risk tier (30–59%)
PROFILE_C_MODERATE: dict[str, float] = {
    " ROA(C) before interest and depreciation before interest":    0.2313654756,
    " ROA(A) before interest and % after tax":                     0.1627780201,
    " ROA(B) before interest and depreciation after tax":          0.2067562503,
    " Continuous interest rate (after tax)":                       0.7801268831,
    " Net Value Per Share (B)":                                    0.1350975517,
    " Net Value Per Share (A)":                                    0.1350975517,
    " Persistent EPS in the Last Four Seasons":                    0.1598752009,
    " Per Share Net profit before tax":                            0.1271371545,
    " Interest Expense Ratio":                                     0.6305584855,
    " Debt ratio %":                                               0.2080902137,
    " Net worth/Assets":                                           0.7919097863,
    " Borrowing dependency":                                       0.3831738178,
    " Net profit before tax/Paid-in capital":                      0.1261217103,
    " Retained Earnings to Total Assets":                          0.8277666581,
    " Net Income to Total Assets":                                 0.5269117307,
    " Net Income to Stockholder's Equity":                         0.7984852056,
    " Liability to Equity":                                        0.2903251996,
    " Degree of Financial Leverage (DFL)":                         0.0267721521,
    " Interest Coverage Ratio (Interest expense to EBIT)":         0.5650661185,
    " Equity to Liability":                                        0.0164195794,
}

# Profile D — Critical Risk SME
# Real training row (idx 5585) from the bankrupt class.
# Verified P(default) = 75.00%  →  High Risk tier (60–79%)
PROFILE_D_CRITICAL: dict[str, float] = {
    " ROA(C) before interest and depreciation before interest":    0.5120199887,
    " ROA(A) before interest and % after tax":                     0.5422359131,
    " ROA(B) before interest and depreciation after tax":          0.5531457389,
    " Continuous interest rate (after tax)":                       0.7816009533,
    " Net Value Per Share (B)":                                    0.1869820500,
    " Net Value Per Share (A)":                                    0.1869820500,
    " Persistent EPS in the Last Four Seasons":                    0.2187794559,
    " Per Share Net profit before tax":                            0.1754886524,
    " Interest Expense Ratio":                                     0.6318576236,
    " Debt ratio %":                                               0.0962210375,
    " Net worth/Assets":                                           0.9037789625,
    " Borrowing dependency":                                       0.3729598336,
    " Net profit before tax/Paid-in capital":                      0.1744981147,
    " Retained Earnings to Total Assets":                          0.9425178458,
    " Net Income to Total Assets":                                 0.8016045267,
    " Net Income to Stockholder's Equity":                         0.8404271483,
    " Liability to Equity":                                        0.2779817096,
    " Degree of Financial Leverage (DFL)":                         0.0269848167,
    " Interest Coverage Ratio (Interest expense to EBIT)":         0.5659031109,
    " Equity to Liability":                                        0.0395780864,
}

# Profile B — Distressed SME (High Default Risk)
# Derived from 40th percentile of bankrupt-class training samples.
# Verified P(default) = 89.00%
PROFILE_B_DISTRESSED: dict[str, float] = {
    " ROA(C) before interest and depreciation before interest":    0.4228234844,
    " ROA(A) before interest and % after tax":                     0.4689850218,
    " ROA(B) before interest and depreciation after tax":          0.4715291797,
    " Continuous interest rate (after tax)":                       0.7812369945,
    " Net Value Per Share (B)":                                    0.1543982211,
    " Net Value Per Share (A)":                                    0.1543982211,
    " Persistent EPS in the Last Four Seasons":                    0.1901531696,
    " Per Share Net profit before tax":                            0.1483734423,
    " Interest Expense Ratio":                                     0.6300544748,
    " Debt ratio %":                                               0.1809170010,
    " Net worth/Assets":                                           0.8051677310,
    " Borrowing dependency":                                       0.3814089300,
    " Net profit before tax/Paid-in capital":                      0.1488356255,
    " Retained Earnings to Total Assets":                          0.9100849445,
    " Net Income to Total Assets":                                 0.7518520655,
    " Net Income to Stockholder's Equity":                         0.8340502626,
    " Liability to Equity":                                        0.2850218010,
    " Degree of Financial Leverage (DFL)":                         0.0266330871,
    " Interest Coverage Ratio (Interest expense to EBIT)":         0.5643908424,
    " Equity to Liability":                                        0.0178351829,
}


# ---------------------------------------------------------------------------
# Application state
# ---------------------------------------------------------------------------
class AppState:
    model: Any = None
    explainer: Any = None


app_state = AppState()


# ---------------------------------------------------------------------------
# API Key security dependency
#
# How it works:
#   - FastAPI reads the "X-API-Key" header from every incoming request.
#   - If API_KEY is not set in .env, the check is skipped entirely
#     (backwards-compatible for local dev without a key configured).
#   - If API_KEY is set, the header value must match exactly.
#   - Any mismatch returns 401 Unauthorized — the route never executes.
#   - Declare `key: str = Security(verify_api_key)` on any route to protect it.
# ---------------------------------------------------------------------------
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str | None = Security(_api_key_header)) -> None:
    """Dependency — enforces X-API-Key header when API_KEY is configured."""
    if not settings.api_key:
        # No key configured → open access (development mode)
        return
    if key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include X-API-Key header.",
        )


# ---------------------------------------------------------------------------
# Lifespan — model: SHIELD_BestModel_RF_8020_CV10.joblib
#
# SHAP TreeExplainer notes for RandomForestClassifier:
#   • feature_perturbation defaults to "interventional" for RF, which is
#     correct and avoids the tree_path_dependent approximation used for XGBoost.
#   • check_additivity=False is set to suppress the floating-point sum warning
#     that can appear with large RF ensembles (100+ trees); the SHAP values
#     themselves remain accurate.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading Random Forest model …")
    app_state.model = joblib.load(settings.model_path)

    # The saved .joblib is an imblearn Pipeline whose final step is the
    # RandomForestClassifier.  SHAP's TreeExplainer cannot wrap the full
    # Pipeline object — it must receive the bare classifier.
    # We keep app_state.model as the full pipeline for predict_proba (so the
    # preprocessing steps still run), and store only the classifier in the
    # explainer.  SHAP values are computed on the already-preprocessed input
    # DataFrame, so this is numerically correct.
    from sklearn.pipeline import Pipeline as SKPipeline
    from imblearn.pipeline import Pipeline as ImbPipeline

    if isinstance(app_state.model, (SKPipeline, ImbPipeline)):
        clf = app_state.model[-1]   # last step = the RandomForestClassifier
        logger.info(
            "Pipeline detected — extracting final estimator for SHAP: %s",
            type(clf).__name__,
        )
    else:
        clf = app_state.model

    logger.info("Building SHAP TreeExplainer (RandomForestClassifier) …")
    app_state.explainer = shap.TreeExplainer(
        clf,
        feature_perturbation="interventional",
    )

    logger.info("Initialising Groq advisory engine …")
    _init_groq()

    logger.info("Initialising database …")
    await init_db(settings.database_url)

    logger.info("SHIELD backend ready.")
    yield

    await close_db()
    logger.info("SHIELD backend shutting down.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SHIELD API",
    description="SME Health Indicator and Evaluator for Loan Decision — prediction endpoint.",
    version="1.3.0",
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
    Top 20 financial ratios — order and names match model.feature_names_in_ exactly.
    All values normalised to [0, 1].
    """
    roa_c_before_interest_and_depreciation_before_interest: float = Field(
        ..., ge=0.0, le=1.0,
        description="ROA(C) before interest and depreciation before interest",
    )
    roa_a_before_interest_and_percent_after_tax: float = Field(
        ..., ge=0.0, le=1.0,
        description="ROA(A) before interest and % after tax",
    )
    roa_b_before_interest_and_depreciation_after_tax: float = Field(
        ..., ge=0.0, le=1.0,
        description="ROA(B) before interest and depreciation after tax",
    )
    continuous_interest_rate_after_tax: float = Field(
        ..., ge=0.0, le=1.0,
        description="Continuous interest rate (after tax)",
    )
    net_value_per_share_b: float = Field(
        ..., ge=0.0, le=1.0,
        description="Net Value Per Share (B)",
    )
    net_value_per_share_a: float = Field(
        ..., ge=0.0, le=1.0,
        description="Net Value Per Share (A)",
    )
    persistent_eps_in_the_last_four_seasons: float = Field(
        ..., ge=0.0, le=1.0,
        description="Persistent EPS in the Last Four Seasons",
    )
    per_share_net_profit_before_tax: float = Field(
        ..., ge=0.0, le=1.0,
        description="Per Share Net profit before tax",
    )
    interest_expense_ratio: float = Field(
        ..., ge=0.0, le=1.0,
        description="Interest Expense Ratio",
    )
    debt_ratio_percent: float = Field(
        ..., ge=0.0, le=1.0,
        description="Debt ratio %",
    )
    net_worth_assets: float = Field(
        ..., ge=0.0, le=1.0,
        description="Net worth/Assets",
    )
    borrowing_dependency: float = Field(
        ..., ge=0.0, le=1.0,
        description="Borrowing dependency",
    )
    net_profit_before_tax_paid_in_capital: float = Field(
        ..., ge=0.0, le=1.0,
        description="Net profit before tax/Paid-in capital",
    )
    retained_earnings_to_total_assets: float = Field(
        ..., ge=0.0, le=1.0,
        description="Retained Earnings to Total Assets",
    )
    net_income_to_total_assets: float = Field(
        ..., ge=0.0, le=1.0,
        description="Net Income to Total Assets",
    )
    net_income_to_stockholders_equity: float = Field(
        ..., ge=0.0, le=1.0,
        description="Net Income to Stockholder's Equity",
    )
    liability_to_equity: float = Field(
        ..., ge=0.0, le=1.0,
        description="Liability to Equity",
    )
    degree_of_financial_leverage_dfl: float = Field(
        ..., ge=0.0, le=1.0,
        description="Degree of Financial Leverage (DFL)",
    )
    interest_coverage_ratio: float = Field(
        ..., ge=0.0, le=1.0,
        description="Interest Coverage Ratio (Interest expense to EBIT)",
    )
    equity_to_liability: float = Field(
        ..., ge=0.0, le=1.0,
        description="Equity to Liability",
    )

    def to_feature_array(self) -> list[float]:
        """Return values in the exact column order the RF model was trained on."""
        return [
            self.roa_c_before_interest_and_depreciation_before_interest,
            self.roa_a_before_interest_and_percent_after_tax,
            self.roa_b_before_interest_and_depreciation_after_tax,
            self.continuous_interest_rate_after_tax,
            self.net_value_per_share_b,
            self.net_value_per_share_a,
            self.persistent_eps_in_the_last_four_seasons,
            self.per_share_net_profit_before_tax,
            self.interest_expense_ratio,
            self.debt_ratio_percent,
            self.net_worth_assets,
            self.borrowing_dependency,
            self.net_profit_before_tax_paid_in_capital,
            self.retained_earnings_to_total_assets,
            self.net_income_to_total_assets,
            self.net_income_to_stockholders_equity,
            self.liability_to_equity,
            self.degree_of_financial_leverage_dfl,
            self.interest_coverage_ratio,
            self.equity_to_liability,
        ]


class ShapFeature(BaseModel):
    label: str
    value: float
    shap_value: float
    direction: str   # "risk" | "protective"


class AdvisoryReport(BaseModel):
    tone: str
    tone_level: str              # "critical" | "elevated" | "moderate" | "low"
    risk_drivers: list[dict]
    protective_factors: list[dict]
    recommendation: str
    advisory_source: str = "rule-based"  # "groq" | "rule-based" | "rate-limited"


class PredictionResponse(BaseModel):
    probability: float
    probability_pct: float
    classification: str
    is_high_risk: bool
    shap_base_value: float
    shap_features: list[ShapFeature]
    advisory: AdvisoryReport


PredictionResponse.model_rebuild()


# ---------------------------------------------------------------------------
# Request wrapper — financial data + evaluation metadata
# ---------------------------------------------------------------------------

class EvaluationMeta(BaseModel):
    """Identification fields collected via the frontend gate modal."""
    company_name: str = Field(..., min_length=1, max_length=255)
    ssm_number:   str = Field(..., min_length=1, max_length=100)
    loan_amount:  float = Field(..., gt=0)
    evaluator:    str = Field(..., min_length=1, max_length=100)


class PredictRequest(BaseModel):
    """Full /predict payload — metadata + 20 financial ratios."""
    meta:       EvaluationMeta
    financials: SMEFinancialData


# ---------------------------------------------------------------------------
# Log entry response model
# ---------------------------------------------------------------------------

class LogEntry(BaseModel):
    id:                  int
    company_name:        str
    ssm_number:          str
    loan_amount:         float
    evaluator:           str
    evaluated_at:        str   # ISO-8601 string
    probability_default: float
    risk_classification: str
    financial_inputs:    dict
    shap_breakdown:      list
    advisory_report:     str


# ---------------------------------------------------------------------------
# Groq advisory generator
# ---------------------------------------------------------------------------

async def _groq_chat(user_prompt: str) -> str:
    """Send a single chat completion request to Groq and return the text.
    Raises on any error — callers handle exceptions.
    """
    response = await _groq_client.chat.completions.create(
        model=_GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=800,   # plenty for 3 sentences + 2-sentence recommendation
        top_p=0.9,
    )
    return response.choices[0].message.content.strip()


async def generate_advisory(
    probability: float,
    classification: str,
    risk_drivers: list[dict],
    protective_factors: list[dict],
    fallback_recommendation: str,
    fallback_tone: str,
) -> tuple[str, str, str]:
    """
    Generate dynamic advisory text via Groq.
    Returns (explanation, recommendation, source).
    NEVER raises — falls back silently on any error.
    """
    if _groq_client is None:
        return fallback_tone, fallback_recommendation, "rule-based"

    drivers_text = "\n".join(
        f"  • {d['label']}: SHAP = +{d['shap_value']:.4f} (pushes toward default)"
        for d in risk_drivers
    )
    protective_text = (
        "\n".join(
            f"  • {d['label']}: SHAP = {d['shap_value']:.4f} (reduces default risk)"
            for d in protective_factors
        )
        if protective_factors else "  • None identified."
    )

    try:
        # ── Call 1: Explanation ──────────────────────────────────────────
        explanation_prompt = (
            f"An SME credit application has been assessed with a {probability * 100:.1f}% "
            f"probability of default, classified as {classification}.\n\n"
            f"Top risk drivers (SHAP values from the Random Forest model):\n{drivers_text}\n\n"
            f"Protective factors:\n{protective_text}\n\n"
            f"Write 3 concise sentences explaining WHY these specific metrics drove the "
            f"default probability to {probability * 100:.1f}%. Name each metric explicitly "
            f"and explain its financial significance. Do not use bullet points or headers — "
            f"output flowing prose only."
        )

        explanation = await _groq_chat(explanation_prompt)

        # ── Call 2: Recommendation ───────────────────────────────────────
        recommendation_prompt = (
            f"An SME has a {probability * 100:.1f}% probability of default ({classification}).\n\n"
            f"Top risk drivers:\n{drivers_text}\n\n"
            f"Protective factors:\n{protective_text}\n\n"
            f"As a JuneBank loan officer under BNM guidelines, write 2 sentences providing "
            f"a specific, actionable credit restructuring recommendation directly addressing "
            f"the top risk drivers above. Be concrete — mention specific actions such as "
            f"equity injection, debt rescheduling, covenant conditions, collateral requirements, "
            f"or working capital improvements. Do not use bullet points or headers."
        )

        recommendation = await _groq_chat(recommendation_prompt)

        tone           = explanation   if explanation   else fallback_tone
        recommendation = recommendation if recommendation else fallback_recommendation

        logger.info("Groq advisory generated successfully.")
        return tone, recommendation, "groq"

    except Exception as exc:
        exc_str = str(exc)

        if "429" in exc_str or "rate_limit" in exc_str.lower():
            logger.warning("Groq API rate limit reached.")
            msg = (
                "AI advisory is temporarily unavailable — API rate limit reached. "
                "Please try again in a few minutes. "
                "The risk score and SHAP analysis above remain fully accurate."
            )
            return msg, msg, "rate-limited"

        if "503" in exc_str or "unavailable" in exc_str.lower():
            logger.warning("Groq API temporarily unavailable.")
            msg = (
                "AI advisory is temporarily unavailable — service is experiencing high demand. "
                "Please try again shortly. "
                "The risk score and SHAP analysis above remain fully accurate."
            )
            return msg, msg, "rate-limited"

        logger.error("Groq API error (%s): %s — falling back to rule-based.", type(exc).__name__, exc)
        return fallback_tone, fallback_recommendation, "rule-based"


# ---------------------------------------------------------------------------
# Business logic helpers
# ---------------------------------------------------------------------------

def _compute_shap(input_df: pd.DataFrame) -> tuple[np.ndarray, float]:
    """
    Compute SHAP values for a single-row DataFrame.

    For RandomForestClassifier, TreeExplainer returns a 3-D array
    (n_samples, n_features, n_classes) when called as a callable.
    We extract class-1 (default) values and the corresponding base value.
    check_additivity is disabled to avoid benign floating-point warnings
    from large ensembles; the values themselves remain correct.
    """
    sv_obj = app_state.explainer(input_df.values, check_additivity=False)
    if sv_obj.values.ndim == 3:
        sv       = sv_obj.values[0, :, 1]
        base_val = float(sv_obj.base_values[0, 1])
    else:
        sv       = sv_obj.values[0]
        base_val = float(sv_obj.base_values[0])
    return sv, base_val


def _build_rule_based_advisory(
    shap_values: np.ndarray,
    prob: float,
) -> tuple[str, str, str, list[dict], list[dict]]:
    """Returns (tone, tone_level, recommendation, risk_drivers, protective_factors)."""
    pairs = list(zip(FEATURE_LABELS, shap_values))

    if prob >= 0.80:
        tone       = "Critical Risk Detected. The model indicates a very high likelihood of financial distress."
        tone_level = "critical"
    elif prob >= 0.60:
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
        for l, v in sorted(
            [(l, v) for l, v in pairs if v > 0], key=lambda x: x[1], reverse=True
        )[:3]
    ]
    protective_factors = [
        {"label": l, "shap_value": round(float(v), 6)}
        for l, v in sorted(
            [(l, v) for l, v in pairs if v < 0], key=lambda x: x[1]
        )[:3]
    ]

    recommendation = (
        "Loan approval should be approached with caution. A detailed due-diligence review of "
        "the flagged risk drivers is strongly advised. Consider requesting collateral or "
        "imposing covenant-based conditions before disbursement."
        if prob >= 0.60 else
        "The financial profile supports a favourable loan consideration. Standard monitoring "
        "of the identified risk drivers is recommended throughout the loan tenure."
        if prob < 0.30 else
        "Proceed with conditional approval. Request additional financial disclosures and "
        "consider imposing a reduced credit limit or phased disbursement pending improvement "
        "in the flagged risk indicators."
    )

    return tone, tone_level, recommendation, risk_drivers, protective_factors


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
async def root() -> dict:
    return {"status": "ok", "service": "SHIELD API", "version": "1.3.0"}


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {
        "status": "healthy" if (app_state.model and app_state.explainer) else "degraded",
        "model_loaded": app_state.model is not None,
        "explainer_loaded": app_state.explainer is not None,
        "groq_enabled": _groq_client is not None,
    }


@app.get("/features", tags=["Meta"])
async def get_features() -> dict:
    return {
        "features": [
            {"key": key, "label": label, "median": MEDIAN_DEFAULTS[name]}
            for key, label, name in zip(
                SMEFinancialData.model_fields.keys(), FEATURE_LABELS, FEATURE_NAMES,
            )
        ],
        "profiles": {
            "healthy":    {k: v for k, v in zip(SMEFinancialData.model_fields.keys(), PROFILE_A_HEALTHY.values())},
            "moderate":   {k: v for k, v in zip(SMEFinancialData.model_fields.keys(), PROFILE_C_MODERATE.values())},
            "critical":   {k: v for k, v in zip(SMEFinancialData.model_fields.keys(), PROFILE_D_CRITICAL.values())},
            "distressed": {k: v for k, v in zip(SMEFinancialData.model_fields.keys(), PROFILE_B_DISTRESSED.values())},
        },
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictRequest, _: None = Security(verify_api_key)) -> PredictionResponse:
    """Main prediction endpoint — runs Random Forest + SHAP + Groq advisory, then persists to DB."""
    if app_state.model is None or app_state.explainer is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Try again shortly.")

    data          = request.financials
    meta          = request.meta
    feature_array = data.to_feature_array()
    input_df      = pd.DataFrame([feature_array], columns=FEATURE_NAMES)

    prob_bankrupt = float(app_state.model.predict_proba(input_df)[0][1])
    is_high_risk  = prob_bankrupt >= 0.60

    shap_vals, base_val = _compute_shap(input_df)

    shap_features: list[ShapFeature] = []
    for i, (label, sv) in enumerate(zip(FEATURE_LABELS, shap_vals)):
        shap_features.append(ShapFeature(
            label=label,
            value=round(feature_array[i], 6),
            shap_value=round(float(sv), 6),
            direction="risk" if sv > 0 else "protective",
        ))
    shap_features.sort(key=lambda x: abs(x.shap_value), reverse=True)

    tone, tone_level, rule_recommendation, risk_drivers, protective_factors = (
        _build_rule_based_advisory(shap_vals, prob_bankrupt)
    )

    classification = (
        "Critical Risk" if prob_bankrupt >= 0.80 else
        "High Risk"     if prob_bankrupt >= 0.60 else
        "Moderate Risk" if prob_bankrupt >= 0.30 else
        "Low Risk"
    )

    final_tone, final_recommendation, advisory_source = await generate_advisory(
        probability=prob_bankrupt,
        classification=classification,
        risk_drivers=risk_drivers,
        protective_factors=protective_factors,
        fallback_recommendation=rule_recommendation,
        fallback_tone=tone,
    )

    advisory = AdvisoryReport(
        tone=final_tone,
        tone_level=tone_level,
        risk_drivers=risk_drivers,
        protective_factors=protective_factors,
        recommendation=final_recommendation,
        advisory_source=advisory_source,
    )

    # ── Persist to PostgreSQL (non-blocking, best-effort) ────────────────────
    advisory_text = f"{final_tone}\n\nRecommendation: {final_recommendation}"
    shap_list = [
        {"label": f.label, "value": f.value, "shap_value": f.shap_value, "direction": f.direction}
        for f in shap_features
    ]
    try:
        async with get_session() as session:
            if session is not None:
                record = Evaluation(
                    company_name         = meta.company_name,
                    ssm_number           = meta.ssm_number,
                    loan_amount          = meta.loan_amount,
                    evaluator            = meta.evaluator,
                    evaluated_at         = datetime.now(timezone.utc),
                    probability_default  = round(prob_bankrupt, 6),
                    risk_classification  = classification,
                    financial_inputs     = json.dumps(data.model_dump()),
                    shap_breakdown       = json.dumps(shap_list),
                    advisory_report      = advisory_text,
                )
                session.add(record)
                await session.commit()
                logger.info("Evaluation saved — id=%s company=%s", record.id, meta.company_name)
    except Exception as exc:
        logger.error("Failed to save evaluation to DB: %s", exc)
        # Never let a DB failure block the response

    return PredictionResponse(
        probability=round(prob_bankrupt, 6),
        probability_pct=round(prob_bankrupt * 100, 2),
        classification=classification,
        is_high_risk=is_high_risk,
        shap_base_value=round(base_val, 6),
        shap_features=shap_features,
        advisory=advisory,
    )


@app.get("/logs", response_model=list[LogEntry], tags=["Logs"])
async def get_logs(limit: int = 200, _: None = Security(verify_api_key)) -> list[LogEntry]:
    """Return past evaluations, newest first. Max 200 rows per call."""
    from sqlalchemy import select, desc

    async with get_session() as session:
        if session is None:
            raise HTTPException(
                status_code=503,
                detail="Audit log unavailable — DATABASE_URL not configured.",
            )
        result = await session.execute(
            select(Evaluation)
            .order_by(desc(Evaluation.evaluated_at))
            .limit(limit)
        )
        rows = result.scalars().all()

    return [LogEntry(**row.to_dict()) for row in rows]
