# SHIELD — Project Context for AI Assistant

> Hand this document to any AI assistant (Gemini, ChatGPT, Kiro, etc.) to get accurate,
> context-aware help without re-explaining the project from scratch.
>
> **Current version: v1.0.3**

---

## What is SHIELD?

**SHIELD** (SME Health Indicator and Evaluator for Loan Decisions) is a Final Year Project
for a fictitious bank called **JuneBank**. It is a web-based credit risk evaluation tool
that predicts the probability of financial default for Small & Medium Enterprises (SMEs)
using a trained XGBoost model with SHAP explainability.

- **Academic context:** FYP / Degree Project — for demonstration purposes only.
- **Dataset:** Italian bankruptcy dataset (2023), 20 normalised financial ratios as features.
- **Model:** XGBoost binary classifier, trained offline, saved as `model/xgb_shield_model.joblib`.
- **Explainability:** SHAP `TreeExplainer` runs per-request, returns per-feature contributions.
- **AI Advisory:** Groq API (`openai/gpt-oss-120b`) generates dynamic natural-language credit
  analysis from SHAP values. Falls back to rule-based text if key is missing or API fails.
- **Audit Persistence:** Every evaluation is saved to a PostgreSQL database (via Docker) for
  audit trail purposes. Fully optional — app works without it.

---

## Tech Stack

### Frontend
| Item | Detail |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS v3 with custom design tokens |
| Charts | Recharts 2 |
| Icons | Lucide React (no emojis anywhere in the UI) |
| Fonts | Ubuntu (headings), Lato (body), JetBrains Mono (numbers) — Google Fonts |
| Auth | Client-side only, hardcoded demo credentials in `auth.tsx` |
| API calls | Proxied via Next.js rewrites (`/api/*` → FastAPI on port 8000) |
| State | Workspace state persisted in `sessionStorage` (survives navigation, clears on logout) |

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
| AI Advisory | Groq SDK (`groq>=1.7.0`), model `openai/gpt-oss-120b` |
| Database ORM | SQLAlchemy 2.0.30 async + asyncpg 0.29.0 |

### Infrastructure
| Item | Detail |
|---|---|
| Database | PostgreSQL 15 (Alpine) via Docker Compose |
| Port | 5400 (5432 is reserved by local PostgreSQL install; Windows Hyper-V reserves 5433–5532) |
| Volume | `shield_pgdata` — named Docker volume, data persists across container restarts |

---

## Project Structure

```
SHIELD/
├── docker-compose.yml               ← PostgreSQL 15 local dev container (port 5400)
├── UPDATE.md                        ← This file — project context for AI assistants
├── SETUP_AND_RUN.txt                ← Full setup guide for running locally
├── app.py                           ← Legacy Streamlit app (v1, still works)
│
├── frontend/                        # Next.js app (main UI)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout: fonts, metadata, favicon, AppShell wrapper
│   │   │   ├── page.tsx             # Dashboard: empty state → gate modal → 3-col workspace
│   │   │   ├── globals.css          # Tailwind base + .panel, .btn-primary, .input-field, .section-label
│   │   │   └── logs/
│   │   │       └── page.tsx         # Audit log table: expandable rows, SHAP preview, risk badges
│   │   ├── components/
│   │   │   ├── AppShell.tsx         # Auth gate: LoginPage → SplashScreen → Navbar + dashboard
│   │   │   ├── LoginPage.tsx        # JuneBank login screen with eagle watermark + help modal
│   │   │   ├── Navbar.tsx           # Fixed top nav (Home/Logs/Dashboard/Contact) + profile dropdown
│   │   │   ├── SplashScreen.tsx     # Video splash (plays once per login session, not on refresh)
│   │   │   ├── InputForm.tsx        # 20-field form: profile selector, CSV upload, 4 grouped sections, sticky CTA
│   │   │   ├── RiskGauge.tsx        # SVG semicircle gauge + classification badge + confidence breakdown
│   │   │   ├── ShapChart.tsx        # Top-5 ranked table + Recharts horizontal bar chart (expand toggle)
│   │   │   └── AdvisoryReport.tsx   # Groq/rule-based advisory: tone banner + risk drivers + recommendation
│   │   └── lib/
│   │       ├── api.ts               # fetch wrappers: predict(), fetchLogs(), fetchFeatures(), healthCheck()
│   │       ├── auth.tsx             # AuthContext, AuthProvider, useAuth — session + workspace cleared on logout
│   │       ├── types.ts             # TypeScript interfaces mirroring all backend Pydantic models
│   │       └── constants.ts         # MEDIAN_DEFAULTS, PROFILE_HEALTHY, PROFILE_DISTRESSED, FEATURE_LABELS
│   ├── public/
│   │   ├── JuneBank.png             # Bank wordmark logo
│   │   ├── JuneBankEagle.png        # Eagle silhouette (ghosted watermark on all pages)
│   │   ├── JuneBankLoading.mp4      # Splash screen video
│   │   ├── favicon.ico / *.png      # Favicon set
│   │   └── site.webmanifest
│   ├── next.config.mjs              # API rewrite: /api/* → http://localhost:8000/*
│   ├── tailwind.config.ts           # Custom design tokens (brand-*, risk-*)
│   ├── postcss.config.mjs
│   ├── tsconfig.json
│   └── package.json                 # lucide-react, recharts, clsx, next, react
│
├── backend/
│   ├── main.py                      # FastAPI app: all routes, SHAP logic, Groq engine, DB persistence
│   ├── database.py                  # SQLAlchemy async engine, Evaluation ORM model, session helpers
│   ├── config.py                    # pydantic-settings: MODEL_PATH, CORS_ORIGINS, HOST, PORT, GROQ_API_KEY, DATABASE_URL
│   ├── run.py                       # Convenience launcher → python run.py
│   ├── requirements.txt             # All Python dependencies
│   ├── .env                         # Local secrets (gitignored — never committed)
│   └── .env.example                 # Template with all keys and descriptions
│
├── model/
│   └── xgb_shield_model.joblib      # Trained XGBoost binary classifier
│
├── data/
│   ├── df_cleaned_original.csv
│   ├── X_train_processed_8020.csv
│   ├── X_test_processed_8020.csv
│   ├── y_train_processed_8020.csv
│   └── y_test_processed_8020.csv
│
├── notebooks/
│   ├── Preprocessing_SHIELD.ipynb
│   ├── preprocessing_shield.py
│   ├── Development_SHIELD.ipynb
│   └── development_shield.py
│
└── pics/                            # Brand assets and favicon sources
    ├── JuneBank.png
    ├── JuneBankEagle.png
    ├── JuneBankBG.png
    └── favicon/
```

---

## Key Design Decisions

### Dashboard Flow — 3 States (v1.3+)
The main `page.tsx` has three distinct UI states:

1. **Empty State** — shown on fresh login or after clicking "New Evaluation". Displays a
   centered landing screen with a single `+ Start New SME Evaluation` CTA.
2. **Gate Modal** — triggered by the CTA. Collects `company_name`, `ssm_number`, and
   `loan_amount`. `evaluator` is auto-filled from `useAuth()`. Validates all fields before
   proceeding.
3. **Workspace** — the full 3-column sticky layout. A `SessionHeader` bar at the top shows
   the active company name, SSM, loan amount, and evaluator, with a yellow `New Evaluation`
   button to reset back to the empty state.

### Workspace Persistence (v1.4)
- `sessionMeta` and `result` are serialised to `sessionStorage` under `shield_workspace`.
- On mount, the page reads this key and rehydrates instantly — navigating to `/logs` and back
  restores the exact state the officer was working in.
- Logout removes both `shield_auth` and `shield_workspace` so the next login starts fresh.
- `New Evaluation` button explicitly calls `clearWorkspace()` before resetting state.
- A `hydrated` flag prevents a flash of the empty state before the key is read.

### Layout — "Sticky Analytics" (v1.2)
- Normal page scroll — no fixed-viewport tricks.
- **Left column (400px):** InputForm drives page height. 20 fields in a 2-column grid,
  grouped into 4 labelled sections. CTA is `sticky bottom-4`.
- **Middle + right columns:** `position: sticky; top: 20px` — stay in view as the left
  column scrolls. Zero empty whitespace on the right side.

### InputForm — Field Groups
20 fields in 4 labelled sections, each a 2-column grid:
- **Profitability & Earnings** — `roa_a`, `roa_b`, `persistent_eps`, `net_profit_paid_in_capital`, `net_income_total_assets`
- **Per-Share Value** — `net_value_per_share_a/b/c`, `per_share_net_profit`, `net_income_equity`
- **Leverage & Solvency** — `debt_ratio`, `net_worth_assets`, `borrowing_dependency`, `liability_to_equity`, `equity_to_liability`
- **Debt Service & Interest** — `interest_expense_ratio`, `continuous_interest_rate`, `retained_earnings`, `total_income_expense`, `interest_coverage_ratio`

### Audit Persistence Layer
- `backend/database.py` — SQLAlchemy 2.x async engine. `Evaluation` ORM model stores one
  row per `/predict` call.
- **Evaluation columns:** `id`, `company_name`, `ssm_number`, `loan_amount`, `evaluator`,
  `evaluated_at`, `probability_default`, `risk_classification`, `financial_inputs` (JSON),
  `shap_breakdown` (JSON), `advisory_report` (text).
- Tables are created automatically on first backend startup (`CREATE TABLE IF NOT EXISTS`).
- DB failure is **non-blocking** — if PostgreSQL is down, the prediction still returns
  normally, a warning is logged, and the response is not affected.
- `DATABASE_URL` absent → persistence silently disabled, app fully functional.

### POST /predict — Updated Request Shape
The predict endpoint now takes a wrapped payload (not bare financials):
```json
{
  "meta": {
    "company_name": "Syarikat ABC Sdn Bhd",
    "ssm_number":   "1234567-A",
    "loan_amount":  500000,
    "evaluator":    "analyst"
  },
  "financials": {
    "roa_a": 0.586,
    ...20 normalised float fields...
  }
}
```

### GET /logs
- Returns all past evaluations from PostgreSQL, newest first (max 200 rows).
- Returns HTTP 503 if `DATABASE_URL` is not configured.
- Frontend `/logs` page shows: Date/time, Company, SSM, Loan Amount, Risk badge,
  P(Default) %, Evaluator. Each row expands to show the advisory summary and top-5 SHAP
  drivers inline.

### Authentication
- **Client-side only** — no backend auth endpoint.
- Credentials hardcoded in `frontend/src/lib/auth.tsx`.
- Two demo users: `admin / admin` and `analyst / junebank1`.
- `isLoggedIn` persisted in `sessionStorage` (survives refresh, clears on tab close).
- `splashPending` is in-memory only — splash plays once per login action, not on refresh.
- Logout clears both `shield_auth` and `shield_workspace`.

### Groq AI Advisory Engine
- Two sequential Groq API calls per prediction: explanation + recommendation.
- System prompt: "Senior Credit Risk Analyst at JuneBank under BNM regulatory guidelines."
- Model: `openai/gpt-oss-120b` (free plan: 1,000 req/day, 200K tokens/day).
- `temperature=0.3`, `max_tokens=800`, `top_p=0.9`.
- Falls back to rule-based text on any error — app never crashes.
- `advisory_source`: `"groq"` | `"rule-based"` | `"rate-limited"`.
- Frontend splits LLM prose into numbered sentences; recommendation into numbered action steps.

### RiskGauge
- Pure SVG semicircle — no third-party gauge library.
- All percentage values use `toFixed(2)` for consistency with the logs table (e.g. `0.01%`
  not `0.0%`). This fixed a visual mismatch where the gauge showed `0.0%` and the bar
  showed `0.01%` for the same underlying value.
- Percentage text positioned inside the arc bowl at `y = CY - 8`.
- Colour thresholds: green < 30%, amber 30–50%, orange 50–70%, red ≥ 70%.

### Icons
- All icons from `lucide-react` — no emojis anywhere in the codebase.

### Design System (Tailwind tokens — `tailwind.config.ts`)
| Token | Value | Use |
|---|---|---|
| `brand-cream` | `#FCFAF8` | Page background |
| `brand-panel` | `#FFFFFF` | Card / panel background |
| `brand-yellow` | `#FFD100` | JuneBank accent, CTA, active states |
| `brand-yellowHover` | (darker shade) | Hover state for yellow buttons |
| `brand-charcoal` | `#1A1A1A` | Primary text |
| `brand-muted` | `#6B6B6B` | Secondary text, labels |
| `brand-subtext` | `#9A9A9A` | Captions, metadata |
| `brand-border` | `#E8E4DE` | All borders |
| `risk-high` | `#DC2626` | Red — distressed |
| `risk-highBg` | `rgba(220,38,38,0.08)` | Red tinted background |
| `risk-low` | `#16A34A` | Green — healthy |
| `risk-lowBg` | `rgba(22,163,74,0.08)` | Green tinted background |
| `risk-amber` | `#D97706` | Orange — elevated risk |

Custom CSS classes in `globals.css`:
- `.panel` — white card with border, rounded-xl, shadow
- `.section-label` — tiny all-caps label above section headings
- `.btn-primary` — solid yellow CTA button
- `.btn-ghost` — bordered secondary button
- `.input-field` — styled number/text input

---

## Backend API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check — `{status: "ok"}` |
| GET | `/health` | Model, explainer, Groq, and DB status |
| GET | `/features` | 20 feature labels, medians, preset profiles |
| POST | `/predict` | XGBoost + SHAP + Groq advisory + DB save |
| GET | `/logs?limit=200` | All past evaluations, newest first |

---

## Environment Variables (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `MODEL_PATH` | Yes | Path to `.joblib` model, relative to `backend/` |
| `CORS_ORIGINS` | Yes | Comma-separated allowed origins |
| `HOST` | Yes | Uvicorn host, default `0.0.0.0` |
| `PORT` | Yes | Uvicorn port, default `8000` |
| `LOG_LEVEL` | Yes | `debug` / `info` / `warning` / `error` |
| `GROQ_API_KEY` | No | Free key from console.groq.com. Absent → rule-based fallback. |
| `DATABASE_URL` | No | `postgresql+asyncpg://shield:shield@localhost:5400/shield_db`. Absent → no persistence. |

---

## How to Run Locally

Three terminals required for the full stack. DB is optional.

```
Terminal 1 — Database (optional):
  cd SHIELD
  docker compose up -d
  docker compose ps       ← wait for STATUS "healthy"

Terminal 2 — Backend:
  cd SHIELD\backend
  venv\Scripts\activate
  python run.py           ← http://localhost:8000

Terminal 3 — Frontend:
  cd SHIELD\frontend
  npm run dev             ← http://localhost:3000
```

Login credentials: `admin / admin` or `analyst / junebank1`

---

## Known Port Notes

- Local PostgreSQL install occupies port **5432** — Docker container uses **5400** instead.
- Windows Hyper-V/WSL reserves ports **5433–5532** — do not use these for Docker mappings.
- If port 5400 is unavailable, edit `docker-compose.yml` and `DATABASE_URL` in `.env` to
  any free port outside the excluded ranges (check with `netsh int ipv4 show excludedportrange protocol=tcp`).

---

## What Is NOT Implemented

- Real authentication (hardcoded credentials in `auth.tsx`)
- `/dashboard` and `/contact` navbar routes — links exist, pages do not
- Settings page — menu item exists, does nothing
- Password reset — shows a placeholder `alert()`
- Rate limiting or API key protection on the backend
- Production deployment (local dev only)
- The `/logs` page requires Docker + DATABASE_URL — shows a 503 error state if unconfigured
