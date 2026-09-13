# 🛡️ SHIELD — SME Health Indicator and Evaluator for Loan Decision

> **JuneBank Internal Tools · Final Year Project · For academic use only**

SHIELD is a credit-risk assessment platform that predicts the probability of SME bankruptcy using an XGBoost model trained on 20 key financial ratios. SHAP provides full explainability for every prediction.

---

## Architecture

```
SHIELD/
├── app.py                      # Legacy Streamlit app (v1 — still runnable)
│
├── backend/                    # FastAPI prediction API
│   ├── main.py                 # Endpoints: GET /health  GET /features  POST /predict
│   ├── config.py               # pydantic-settings config (reads .env)
│   ├── run.py                  # Uvicorn launcher
│   ├── requirements.txt        # Pinned Python dependencies
│   └── .env.example            # Copy → .env and fill in values
│
├── frontend/                   # Next.js 14 dashboard (JuneBank theme)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx      # Root layout, Inter font, metadata
│   │   │   ├── page.tsx        # 3-column dashboard page
│   │   │   └── globals.css     # Tailwind base + component classes
│   │   ├── components/
│   │   │   ├── InputForm.tsx   # 20-field form, profile presets, CSV upload
│   │   │   ├── RiskGauge.tsx   # Recharts RadialBar + confidence breakdown
│   │   │   ├── ShapChart.tsx   # Recharts horizontal BarChart (waterfall-style)
│   │   │   └── AdvisoryReport.tsx  # Structured AI advisory text
│   │   └── lib/
│   │       ├── api.ts          # Typed fetch wrappers for /predict & /features
│   │       ├── types.ts        # TypeScript interfaces mirroring Pydantic models
│   │       └── constants.ts    # Median defaults, profiles, feature labels
│   ├── tailwind.config.ts      # JuneBank colour palette (#FFD100, #0e1117 …)
│   ├── next.config.ts          # Rewrites /api/* → FastAPI (no CORS in dev)
│   └── package.json
│
├── model/
│   └── xgb_shield_model.joblib # Pre-trained XGBoost model
│
├── data/                       # Processed train/test CSVs
├── notebooks/                  # EDA & model development notebooks
└── reports/                    # Evaluation charts
```

---

## Quick Start

### 1 · Backend (FastAPI)

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
# Edit .env: set MODEL_PATH, CORS_ORIGINS, PORT as needed

# Start the server
python run.py
# → API running at http://localhost:8000
# → Docs at    http://localhost:8000/docs
```

### 2 · Frontend (Next.js)

```bash
cd frontend

npm install
npm run dev
# → Dashboard at http://localhost:3000
```

### 3 · Legacy Streamlit app (optional)

```bash
# From repo root, with the root venv active:
pip install -r requirements.txt
streamlit run app.py
# → http://localhost:8501
```

---

## API Reference

| Method | Endpoint     | Description                                        |
|--------|--------------|----------------------------------------------------|
| GET    | `/health`    | Returns model/explainer load status                |
| GET    | `/features`  | Returns feature registry + preset profiles         |
| POST   | `/predict`   | Accepts 20 floats, returns risk score + SHAP + advisory |

### POST `/predict` — example request body

```json
{
  "roa_c": 0.4725,
  "roa_a": 0.5321,
  "continuous_interest_rate": 0.7815,
  "net_value_per_share_b": 0.1732,
  "net_value_per_share_a": 0.1732,
  "net_value_per_share_c": 0.1734,
  "persistent_eps": 0.2116,
  "per_share_net_profit": 0.1689,
  "interest_expense_ratio": 0.6306,
  "debt_ratio": 0.1561,
  "net_worth_assets": 0.8439,
  "borrowing_dependency": 0.3774,
  "net_profit_paid_in_capital": 0.1680,
  "retained_earnings": 0.9292,
  "total_income_expense": 0.0022,
  "net_income_total_assets": 0.7935,
  "net_income_equity": 0.8399,
  "liability_to_equity": 0.2820,
  "interest_coverage_ratio": 0.5652,
  "equity_to_liability": 0.0232
}
```

### POST `/predict` — example response

```json
{
  "probability": 0.042,
  "probability_pct": 4.2,
  "classification": "Low Risk",
  "is_high_risk": false,
  "shap_base_value": -1.8234,
  "shap_features": [
    { "label": "Debt Ratio %", "value": 0.1114, "shap_value": -0.312, "direction": "protective" },
    ...
  ],
  "advisory": {
    "tone": "Low Risk. The SME appears financially healthy...",
    "tone_level": "low",
    "risk_drivers": [],
    "protective_factors": [{ "label": "Net Worth / Assets", "shap_value": -0.44 }],
    "recommendation": "The financial profile supports a favourable loan consideration..."
  }
}
```

---

## Tech Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| ML Model   | XGBoost 2.0 · SHAP 0.45 · Joblib               |
| Backend    | FastAPI 0.111 · Uvicorn · Pydantic v2           |
| Frontend   | Next.js 14 · React 18 · TypeScript              |
| Styling    | Tailwind CSS 3.4 · JuneBank dark theme          |
| Charts     | Recharts 2.12 (RadialBar + BarChart)            |
| Legacy UI  | Streamlit 1.35                                  |

---

*SHIELD · XGBoost + SHAP · JuneBank · Academic use only*
