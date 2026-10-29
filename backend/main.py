# =============================================================================
# SHIELD — FastAPI Backend
# Prediction endpoint: POST /ratios-predict
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
from experimental_accounting import calculate_features, run_prediction
from pathlib import Path
from database import init_db, close_db, get_session, Evaluation

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger("shield.api")


class AccountingExperimentRequest(BaseModel):
    net_income: float = Field(allow_inf_nan=False)
    total_assets: float = Field(gt=0, allow_inf_nan=False)
    total_liabilities: float = Field(gt=0, allow_inf_nan=False)
    equity: float = Field(allow_inf_nan=False)
    retained_earnings: float = Field(allow_inf_nan=False)


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
# Lifespan — model: SHIELD_RF_7Features_SMOTE050_8020_CV5_sk161.joblib
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
    logger.info("Loading seven-ratio Random Forest model …")
    app_state.model = joblib.load(Path(__file__).resolve().parent / settings.model_path)

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


# ---------------------------------------------------------------------------
# Log entry response model
# ---------------------------------------------------------------------------

class SevenRatioInputs(BaseModel):
    model_config = {"extra": "forbid"}
    net_income_to_stockholders_equity: float = Field(ge=0, le=1, allow_inf_nan=False)
    net_income_to_total_assets: float = Field(ge=0, le=1, allow_inf_nan=False)
    retained_earnings_to_total_assets: float = Field(ge=0, le=1, allow_inf_nan=False)
    debt_ratio_percent: float = Field(ge=0, le=1, allow_inf_nan=False)
    net_worth_assets: float = Field(ge=0, le=1, allow_inf_nan=False)
    equity_to_liability: float = Field(ge=0, le=1, allow_inf_nan=False)
    liability_to_equity: float = Field(ge=0, le=1, allow_inf_nan=False)

    def as_model_features(self):
        from experimental_accounting import FEATURES
        return dict(zip(FEATURES, self.model_dump().values()))


class AccountingPredictRequest(BaseModel):
    meta: EvaluationMeta
    financials: SevenRatioInputs


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
    labels: list[str],
) -> tuple[str, str, str, list[dict], list[dict]]:
    """Returns (tone, tone_level, recommendation, risk_drivers, protective_factors)."""
    pairs = list(zip(labels, shap_values))

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


@app.post("/ratios-predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: AccountingPredictRequest, _: None = Security(verify_api_key)) -> PredictionResponse:
    """Main prediction endpoint — runs the seven-ratio Random Forest + SHAP + Groq advisory, then persists to DB."""
    if app_state.model is None or app_state.explainer is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Try again shortly.")
    data = request.financials
    meta = request.meta
    try:
        outcome = run_prediction(app_state.model, data.as_model_features())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    input_df = pd.DataFrame([list(outcome['features_sent'].values())], columns=list(outcome['features_sent']))
    feature_array = input_df.iloc[0].tolist()
    labels = [str(name).strip() for name in input_df.columns]
    prob_bankrupt = outcome['bankruptcy_score']
    shap_vals, base_val = _compute_shap(input_df)
    is_high_risk = prob_bankrupt >= 0.60

    shap_features: list[ShapFeature] = []
    for i, (label, sv) in enumerate(zip(labels, shap_vals)):
        shap_features.append(ShapFeature(
            label=label,
            value=round(feature_array[i], 6),
            shap_value=round(float(sv), 6),
            direction="risk" if sv > 0 else "protective",
        ))
    shap_features.sort(key=lambda x: abs(x.shap_value), reverse=True)

    tone, tone_level, rule_recommendation, risk_drivers, protective_factors = (
        _build_rule_based_advisory(shap_vals, prob_bankrupt, labels)
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

@app.post('/experimental/accounting-predict', tags=['Experimental'])
async def accounting_predict(request: AccountingExperimentRequest, _: None = Security(verify_api_key)):
    try:
        features = calculate_features(**request.model_dump())
        result = run_prediction(app_state.model, features)
        result['model'] = 'Random Forest | 7 features | SMOTE 0.5 | 80:20 + CV=5'
        result['balance_difference'] = request.total_assets - request.total_liabilities - request.equity
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        logger.exception('Experimental accounting prediction failed')
        raise HTTPException(status_code=503, detail='Seven-feature model unavailable. Check the backend model file and compatible dependencies.')
