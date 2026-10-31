# SME Health Indicator and Evaluator for Loan Decision (SHIELD)

> **Final Year Project · For academic use only**

SHIELD is a credit-risk assessment platform that predicts the probability of SME bankruptcy using a Random Forest model trained on 7 financial ratios (experimental; SMOTE 0.5, 80:20 split, 5-fold CV). SHAP provides full explainability for every prediction.

---

## Architecture

```
SHIELD/
├── backend/                    # FastAPI prediction API
│   ├── main.py                 # Endpoints: GET /health  POST /ratios-predict  GET /logs
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
│   │   │   ├── AccountingInputForm.tsx  # 7-ratio input form
│   │   │   ├── RiskGauge.tsx   # Recharts RadialBar + confidence breakdown
│   │   │   ├── ShapChart.tsx   # Recharts horizontal BarChart (waterfall-style)
│   │   │   └── AdvisoryReport.tsx  # Structured AI advisory text
│   │   └── lib/
│   │       ├── api.ts          # Typed fetch wrappers for /ratios-predict & /logs
│   │       ├── types.ts        # TypeScript interfaces mirroring Pydantic models
│   │       └── accounting-inputs.ts  # 7-ratio fields + readiness checks
│   ├── tailwind.config.ts      # JuneBank colour palette (#FFD100, #0e1117 …)
│   ├── next.config.ts          # Rewrites /api/* → FastAPI (no CORS in dev)
│   └── package.json
│
├── model/
│   └── rf_shield_model.joblib  # Pre-trained Random Forest model
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

---

## API Reference

| Method | Endpoint     | Description                                        |
|--------|--------------|----------------------------------------------------|
| GET    | `/health`    | Returns model/explainer load status                |
| POST   | `/ratios-predict` | Accepts 7 ratios (0–1), returns risk score + SHAP + advisory |
| POST   | `/experimental/accounting-predict` | Accepts 5 raw accounting figures, returns the raw model score |
| GET    | `/logs`      | Past evaluations, newest first                     |

### POST `/ratios-predict` — example request body

```json
{
  "meta": {
    "company_name": "Syarikat ABC Sdn Bhd",
    "ssm_number": "1234567-A",
    "loan_amount": 500000,
    "evaluator": "analyst"
  },
  "financials": {
    "net_income_to_stockholders_equity": 0.84,
    "net_income_to_total_assets": 0.79,
    "retained_earnings_to_total_assets": 0.93,
    "debt_ratio_percent": 0.16,
    "net_worth_assets": 0.84,
    "equity_to_liability": 0.02,
    "liability_to_equity": 0.28
  }
}
```

### POST `/ratios-predict` — example response

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
| ML Model   | Random Forest · SHAP 0.45 · Joblib              |
| Backend    | FastAPI 0.111 · Uvicorn · Pydantic v2           |
| Frontend   | Next.js 14 · React 18 · TypeScript              |
| Styling    | Tailwind CSS 3.4 · JuneBank dark theme          |
| Charts     | Recharts 2.12 (RadialBar + BarChart)            |

