# =============================================================================
# SHIELD — FastAPI Backend
# Prediction endpoint: POST /predict
# Startup: loads XGBoost model + SHAP TreeExplainer once, reuses per request.
#
# Advisory engine: dynamically generated via Groq API (openai/gpt-oss-120b)
# when GROQ_API_KEY is set in backend/.env.
# Falls back gracefully to rule-based text if the key is absent or the API
# call fails — the application never crashes due to a Groq error.
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
# Application state
# ---------------------------------------------------------------------------
class AppState:
    model: Any = None
    explainer: Any = None


app_state = AppState()


# ---------------------------------------------------------------------------
# Lifespan
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

    logger.info("Initialising Groq advisory engine …")
    _init_groq()

    logger.info("SHIELD backend ready.")
    yield

    logger.info("SHIELD backend shutting down.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SHIELD API",
    description="SME Health Indicator and Evaluator for Loan Decision — prediction endpoint.",
    version="1.2.0",
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
    """20 normalised financial ratios, all in [0, 1]."""
    roa_a: float = Field(..., ge=0.0, le=1.0)
    roa_b: float = Field(..., ge=0.0, le=1.0)
    continuous_interest_rate: float = Field(..., ge=0.0, le=1.0)
    net_value_per_share_b: float = Field(..., ge=0.0, le=1.0)
    net_value_per_share_a: float = Field(..., ge=0.0, le=1.0)
    net_value_per_share_c: float = Field(..., ge=0.0, le=1.0)
    persistent_eps: float = Field(..., ge=0.0, le=1.0)
    per_share_net_profit: float = Field(..., ge=0.0, le=1.0)
    interest_expense_ratio: float = Field(..., ge=0.0, le=1.0)
    debt_ratio: float = Field(..., ge=0.0, le=1.0)
    net_worth_assets: float = Field(..., ge=0.0, le=1.0)
    borrowing_dependency: float = Field(..., ge=0.0, le=1.0)
    net_profit_paid_in_capital: float = Field(..., ge=0.0, le=1.0)
    retained_earnings: float = Field(..., ge=0.0, le=1.0)
    total_income_expense: float = Field(..., ge=0.0, le=1.0)
    net_income_total_assets: float = Field(..., ge=0.0, le=1.0)
    net_income_equity: float = Field(..., ge=0.0, le=1.0)
    liability_to_equity: float = Field(..., ge=0.0, le=1.0)
    interest_coverage_ratio: float = Field(..., ge=0.0, le=1.0)
    equity_to_liability: float = Field(..., ge=0.0, le=1.0)

    def to_feature_array(self) -> list[float]:
        return [
            self.roa_a, self.roa_b, self.continuous_interest_rate,
            self.net_value_per_share_b, self.net_value_per_share_a,
            self.net_value_per_share_c, self.persistent_eps,
            self.per_share_net_profit, self.interest_expense_ratio,
            self.debt_ratio, self.net_worth_assets, self.borrowing_dependency,
            self.net_profit_paid_in_capital, self.retained_earnings,
            self.total_income_expense, self.net_income_total_assets,
            self.net_income_equity, self.liability_to_equity,
            self.interest_coverage_ratio, self.equity_to_liability,
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
            f"Top risk drivers (SHAP values from the XGBoost model):\n{drivers_text}\n\n"
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
    sv_obj = app_state.explainer(input_df.values)
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
        if prob >= 0.50 else
        "The financial profile supports a favourable loan consideration. Standard monitoring "
        "of the identified risk drivers is recommended throughout the loan tenure."
    )

    return tone, tone_level, recommendation, risk_drivers, protective_factors


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
async def root() -> dict:
    return {"status": "ok", "service": "SHIELD API", "version": "1.2.0"}


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
            "distressed": {k: v for k, v in zip(SMEFinancialData.model_fields.keys(), PROFILE_B_DISTRESSED.values())},
        },
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(data: SMEFinancialData) -> PredictionResponse:
    """Main prediction endpoint — runs XGBoost + SHAP + Groq advisory."""
    if app_state.model is None or app_state.explainer is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Try again shortly.")

    feature_array = data.to_feature_array()
    input_df      = pd.DataFrame([feature_array], columns=FEATURE_NAMES)

    prob_bankrupt = float(app_state.model.predict_proba(input_df)[0][1])
    is_high_risk  = prob_bankrupt >= 0.50

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

    classification = "High Risk" if is_high_risk else "Low Risk"

    final_tone, final_recommendation, advisory_source = await generate_advisory(
        probability=prob_bankrupt,
        classification=classification,
        risk_drivers=risk_drivers,
        protective_factors=protective_factors,
        fallback_recommendation=rule_recommendation,
        fallback_tone=tone,
    )

    return PredictionResponse(
        probability=round(prob_bankrupt, 6),
        probability_pct=round(prob_bankrupt * 100, 2),
        classification=classification,
        is_high_risk=is_high_risk,
        shap_base_value=round(base_val, 6),
        shap_features=shap_features,
        advisory=AdvisoryReport(
            tone=final_tone,
            tone_level=tone_level,
            risk_drivers=risk_drivers,
            protective_factors=protective_factors,
            recommendation=final_recommendation,
            advisory_source=advisory_source,
        ),
    )
