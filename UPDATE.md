# SHIELD — Project Context for AI Assistant

> Hand this document to any AI assistant (Gemini, ChatGPT, etc.) to get accurate,
> context-aware help without re-explaining the project from scratch.

---

## What is SHIELD?

**SHIELD** (SME Health Indicator and Evaluator for Loan Decisions) is a Final Year Project
for a fictitious bank called **JuneBank**. It is a web-based credit risk evaluation tool
that predicts the probability of financial default for Small & Medium Enterprises (SMEs)
using a trained XGBoost model with SHAP explainability.

- **Academic context:** FYP / Degree Project — for demonstration purposes only.
- **Dataset:** Italian bankruptcy dataset (2023), 20 normalised financial ratios as features.
- **Model:** XGBoost binary classifier, trained offline, saved as `model/xgb_shield_model.joblib`.
- **Explainability:** SHAP `TreeExplainer` runs per-request and returns feature-level contributions.

---

## Tech Stack

### Frontend
| Item | Detail |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS v3 |
| Charts | Recharts 2 |
| Icons | Lucide React |
| Fonts | Ubuntu (headings), Lato (body) — Google Fonts |
| Auth | Client-side only, hardcoded demo credentials in `auth.tsx` |
| API calls | Proxied via Next.js rewrites (`/api/*` → FastAPI on port 8000) |

### Backend
| Item | Detail |
|---|---|
| Framework | FastAPI 0.111 |
| Language | Python 3.11+ |
| Model | XGBoost 2.0.3 |
| Explainability | SHAP 0.45.1 |
| Data | pandas 2.2.2, numpy 1.26.4 |
| Server | Uvicorn with standard extras |
| Config | pydantic-settings, reads from `backend/.env` |

---

## Project Structure

```
SHIELD/
├── frontend/                        # Next.js app
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout, fonts, metadata, favicon
│   │   │   ├── page.tsx             # Main dashboard page (3-column grid)
│   │   │   └── globals.css          # Tailwind base + custom CSS variables
│   │   ├── components/
│   │   │   ├── AppShell.tsx         # Auth gate: login → splash → dashboard
│   │   │   ├── LoginPage.tsx        # JuneBank login screen
│   │   │   ├── Navbar.tsx           # Fixed top nav with profile dropdown
│   │   │   ├── SplashScreen.tsx     # Animated splash (plays once after login)
│   │   │   ├── InputForm.tsx        # 20-field form with CSV upload & presets
│   │   │   ├── RiskGauge.tsx        # SVG semicircle gauge + risk breakdown
│   │   │   ├── ShapChart.tsx        # Recharts horizontal SHAP bar chart
│   │   │   └── AdvisoryReport.tsx   # AI advisory tone + drivers + recommendation
│   │   └── lib/
│   │       ├── api.ts               # fetch wrappers for /predict, /features, /health
│   │       ├── auth.tsx             # AuthContext + AuthProvider + useAuth hook
│   │       ├── types.ts             # TypeScript interfaces (mirrors Pydantic models)
│   │       └── constants.ts         # MEDIAN_DEFAULTS, PROFILE_HEALTHY, PROFILE_DISTRESSED, FEATURE_LABELS
│   ├── public/                      # Static assets
│   │   ├── JuneBank.png             # Bank logo (used in Navbar + LoginPage)
│   │   ├── JuneBankEagle.png        # Eagle silhouette (watermark on all pages)
│   │   ├── JuneBankLoading.mp4      # Splash screen video
│   │   ├── favicon.ico
│   │   ├── favicon-16x16.png
│   │   ├── favicon-32x32.png
│   │   ├── apple-touch-icon.png
│   │   ├── android-chrome-192x192.png
│   │   ├── android-chrome-512x512.png
│   │   └── site.webmanifest
│   ├── next.config.mjs              # API rewrite: /api/* → http://localhost:8000/*
│   ├── tailwind.config.ts           # Custom design tokens (brand-*, risk-*)
│   └── package.json
│
├── backend/
│   ├── main.py                      # FastAPI app, all routes, SHAP logic
│   ├── config.py                    # pydantic-settings, reads .env
│   ├── run.py                       # Convenience launcher (python run.py)
│   ├── requirements.txt
│   └── .env                         # model_path, cors_origins, host, port
│
├── model/
│   └── xgb_shield_model.joblib      # Trained XGBoost model (binary classifier)
│
├── data/                            # Raw + processed datasets (not deployed)
├── notebooks/                       # Jupyter notebooks for preprocessing + training
├── reports/                         # Confusion matrix, ROC curve, model comparison PNGs
└── pics/                            # Brand assets + favicon source files
```

---

## Key Design Decisions

### Authentication
- **Client-side only**, no backend auth. Credentials are hardcoded in `frontend/src/lib/auth.tsx`.
- Two demo users: `admin / admin` and `analyst / junebank1`.
- Session persisted in `sessionStorage` (survives refresh, cleared on tab close).
- Splash screen plays once per login, not on refresh — controlled by in-memory `splashPending` flag.

### API Proxy
- Next.js rewrites `/api/*` to `http://localhost:8000/*` (configured in `next.config.mjs`).
- This avoids CORS issues in development. In production, the rewrite target would point to the deployed backend URL.
- Frontend never calls the backend URL directly — always through `/api`.

### Feature Engineering
- All 20 input features are **pre-normalised floats in [0, 1]** from the preprocessing step.
- The model was trained on specific column names with leading spaces (e.g. `" Debt ratio %"`).
- The frontend uses clean camelCase keys (`debt_ratio`); the backend maps them back to the exact column names before inference.

### SHAP
- `TreeExplainer` is instantiated **once at startup** using the `lifespan` context manager and reused for every request — no re-loading overhead per request.
- Returns all 20 SHAP values per prediction, sorted by absolute value descending.
- The advisory report is generated purely from SHAP values and the predicted probability — no LLM involved.

### Risk Gauge (`RiskGauge.tsx`)
- Pure SVG, no third-party gauge library.
- Fixed 180° semicircle (speedometer style): `M 20 100 A 80 80 0 0 1 180 100`.
- Fill is controlled by `strokeDasharray` + `strokeDashoffset` on the same path — no endpoint angle math.
- Color thresholds: green (<30%), amber (30–50%), orange (50–70%), red (≥70%).

### Design System (Tailwind tokens)
Custom tokens defined in `tailwind.config.ts`:
- `brand-cream` — page background
- `brand-panel` — card/panel background
- `brand-yellow` / `brand-yellowHover` — JuneBank accent color
- `brand-charcoal` — primary text
- `brand-muted` / `brand-subtext` — secondary text
- `risk-high` / `risk-highBg` — red risk colors
- `risk-low` / `risk-lowBg` — green health colors
- `risk-amber` — orange for elevated risk

---

## Backend API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check, returns `{status: "ok"}` |
| GET | `/health` | Model + explainer loaded status |
| GET | `/features` | Feature registry with labels, medians, and preset profiles |
| POST | `/predict` | Main prediction endpoint |

### POST /predict

**Request body** — 20 floats matching `SMEFinancialData`:
```json
{
  "roa_a": 0.586,
  "roa_b": 0.588,
  "continuous_interest_rate": 0.781,
  ... (20 fields total)
}
```

**Response** — `PredictionResponse`:
```json
{
  "probability": 0.884,
  "probability_pct": 88.4,
  "classification": "High Risk",
  "is_high_risk": true,
  "shap_base_value": -3.1234,
  "shap_features": [
    {
      "label": "Debt Ratio %",
      "value": 0.525,
      "shap_value": 1.234,
      "direction": "risk"
    },
    ...
  ],
  "advisory": {
    "tone": "Critical Risk Detected. ...",
    "tone_level": "critical",
    "risk_drivers": [{"label": "...", "shap_value": 1.234}],
    "protective_factors": [{"label": "...", "shap_value": -0.567}],
    "recommendation": "Loan approval should be approached with caution. ..."
  }
}
```

---

## The 20 Input Features

All values normalised to [0, 1] via preprocessing:

| Frontend key | Display label |
|---|---|
| `roa_a` | ROA(A) — Before Interest & % After Tax |
| `roa_b` | ROA(B) — Before Interest & Depreciation After Tax |
| `continuous_interest_rate` | Continuous Interest Rate (After Tax) |
| `net_value_per_share_b` | Net Value Per Share (B) |
| `net_value_per_share_a` | Net Value Per Share (A) |
| `net_value_per_share_c` | Net Value Per Share (C) |
| `persistent_eps` | Persistent EPS in the Last Four Seasons |
| `per_share_net_profit` | Per Share Net Profit Before Tax |
| `interest_expense_ratio` | Interest Expense Ratio |
| `debt_ratio` | Debt Ratio % |
| `net_worth_assets` | Net Worth / Assets |
| `borrowing_dependency` | Borrowing Dependency |
| `net_profit_paid_in_capital` | Net Profit Before Tax / Paid-in Capital |
| `retained_earnings` | Retained Earnings to Total Assets |
| `total_income_expense` | Total Income / Total Expense |
| `net_income_total_assets` | Net Income to Total Assets |
| `net_income_equity` | Net Income to Stockholder's Equity |
| `liability_to_equity` | Liability to Equity |
| `interest_coverage_ratio` | Interest Coverage Ratio (Interest Expense to EBIT) |
| `equity_to_liability` | Equity to Liability |

---

## How to Run Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
# Runs on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

The frontend proxies `/api/*` to `http://localhost:8000` via Next.js rewrites — no manual CORS config needed.

---

## Deployment Plan (intended)

| Part | Target | Notes |
|---|---|---|
| Frontend | Vercel (free) | Set root dir to `frontend`, add `NEXT_PUBLIC_API_URL` env var |
| Backend | Oracle Cloud Free Tier (ARM VM) | 1–2 OCPU + 4–8 GB RAM, always-free, no sleep |

Backend memory at startup: ~350–420 MB (XGBoost + SHAP + pandas loaded into memory).
Minimum recommended RAM: 768 MB. Oracle ARM free tier (up to 24 GB total) is ideal.

---

## What Is NOT Implemented Yet

- Real authentication (currently hardcoded demo credentials)
- `/logs`, `/dashboard`, `/contact` navbar routes (links exist, pages do not)
- Settings page (menu item exists but does nothing)
- Password reset flow (button shows placeholder alert)
- Real database or audit logging
- Rate limiting or API key protection on the backend
