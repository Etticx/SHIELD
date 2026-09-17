"use client";

// =============================================================================
// SHIELD — Main Dashboard Page  (v1.4 — persistent workspace)
//
// Workspace state (sessionMeta + result) is persisted to sessionStorage so
// navigating away and back restores exactly where the officer left off.
//
// Empty-state landing page shows ONLY when:
//   - No shield_workspace key exists in sessionStorage (fresh login), OR
//   - Officer explicitly clicks "New Evaluation" (clears the key).
//
// Logout (auth.tsx) removes both shield_auth AND shield_workspace so the
// next login always starts from the empty state.
// =============================================================================

import { useState, useCallback, useEffect, useRef } from "react";
import Image from "next/image";
import {
  Plus, X, Building2, Hash, DollarSign, User,
  BarChart2, FileText, ChevronRight, RefreshCw,
} from "lucide-react";

import InputForm from "@/components/InputForm";
import RiskGauge from "@/components/RiskGauge";
import ShapChart from "@/components/ShapChart";
import AdvisoryReport from "@/components/AdvisoryReport";

import { predict } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  EvaluationMeta,
  SMEFinancialData,
  PredictionResponse,
} from "@/lib/types";

// ---------------------------------------------------------------------------
// sessionStorage helpers
// ---------------------------------------------------------------------------
const WORKSPACE_KEY = "shield_workspace";

interface PersistedWorkspace {
  meta: EvaluationMeta;
  result: PredictionResponse | null;
}

function saveWorkspace(ws: PersistedWorkspace) {
  try { sessionStorage.setItem(WORKSPACE_KEY, JSON.stringify(ws)); } catch { /* quota */ }
}

function loadWorkspace(): PersistedWorkspace | null {
  try {
    const raw = sessionStorage.getItem(WORKSPACE_KEY);
    return raw ? (JSON.parse(raw) as PersistedWorkspace) : null;
  } catch { return null; }
}

function clearWorkspace() {
  sessionStorage.removeItem(WORKSPACE_KEY);
}

// ---------------------------------------------------------------------------
// Idle / Spinner helpers
// ---------------------------------------------------------------------------
function IdleMiddle() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[280px] text-brand-muted gap-3 py-8">
      <div className="h-14 w-14 rounded-full border-2 border-brand-border flex items-center justify-center">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
          className="text-brand-border">
          <path d="M12 2a10 10 0 0 1 10 10" />
          <path d="M12 6a6 6 0 0 1 6 6" />
          <circle cx="12" cy="12" r="2" />
        </svg>
      </div>
      <p className="text-sm text-center leading-relaxed max-w-[160px]">
        Fill in the financial metrics and click{" "}
        <span className="text-brand-yellow font-semibold">Evaluate Risk</span>.
      </p>
    </div>
  );
}

function IdleRight() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[280px] text-brand-muted gap-3 py-8">
      <div className="h-14 w-14 rounded-full border-2 border-brand-border flex items-center justify-center">
        <BarChart2 size={22} className="text-brand-border" strokeWidth={1.5} />
      </div>
      <p className="text-sm text-center leading-relaxed max-w-[180px]">
        SHAP analysis and the AI advisory report will appear here.
      </p>
    </div>
  );
}

function Spinner({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[280px] gap-3">
      <div className="h-9 w-9 rounded-full border-2 border-brand-yellow border-t-transparent animate-spin" />
      <span className="text-brand-muted text-sm">{label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Identification Gate Modal
// ---------------------------------------------------------------------------
interface GateModalProps {
  evaluator: string;
  onSubmit: (meta: EvaluationMeta) => void;
  onClose: () => void;
}

function GateModal({ evaluator, onSubmit, onClose }: GateModalProps) {
  const [companyName, setCompanyName] = useState("");
  const [ssmNumber, setSsmNumber] = useState("");
  const [loanAmount, setLoanAmount] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!companyName.trim()) e.companyName = "Company name is required.";
    if (!ssmNumber.trim()) e.ssmNumber = "SSM / Business Reg. No. is required.";
    const amt = parseFloat(loanAmount);
    if (!loanAmount || isNaN(amt) || amt <= 0)
      e.loanAmount = "Enter a valid loan amount greater than 0.";
    return e;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }
    onSubmit({
      company_name: companyName.trim(),
      ssm_number: ssmNumber.trim(),
      loan_amount: parseFloat(loanAmount),
      evaluator,
    });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0,0,0,0.45)", backdropFilter: "blur(4px)" }}
      onClick={onClose}
    >
      <div
        className="bg-brand-panel rounded-2xl shadow-card border border-brand-border
                   w-full max-w-md animate-fade-in overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="h-1 w-full bg-brand-yellow" />
        <div className="px-7 py-6 flex flex-col gap-5">

          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] uppercase tracking-widest text-brand-muted font-semibold mb-1">
                New Evaluation
              </p>
              <h2 className="text-xl font-bold text-brand-charcoal font-heading">Identify the SME</h2>
              <p className="text-sm text-brand-muted mt-0.5">
                This information is saved with every evaluation for audit purposes.
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-brand-muted hover:text-brand-charcoal transition-colors mt-0.5 p-1 rounded"
              aria-label="Close"
            >
              <X size={16} />
            </button>
          </div>

          <div className="h-px bg-brand-border" />

          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-brand-charcoal uppercase tracking-wide flex items-center gap-1.5">
                <Building2 size={11} /> Company Name
              </label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Syarikat Maju Jaya Sdn Bhd"
                className={`input-field ${errors.companyName ? "border-risk-high ring-1 ring-risk-high/40" : ""}`}
              />
              {errors.companyName && <p className="text-xs text-risk-high">{errors.companyName}</p>}
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-brand-charcoal uppercase tracking-wide flex items-center gap-1.5">
                <Hash size={11} /> Business Reg. No. (SSM)
              </label>
              <input
                type="text"
                value={ssmNumber}
                onChange={(e) => setSsmNumber(e.target.value)}
                placeholder="e.g. 1234567-A"
                className={`input-field ${errors.ssmNumber ? "border-risk-high ring-1 ring-risk-high/40" : ""}`}
              />
              {errors.ssmNumber && <p className="text-xs text-risk-high">{errors.ssmNumber}</p>}
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-brand-charcoal uppercase tracking-wide flex items-center gap-1.5">
                <DollarSign size={11} /> Requested Loan Amount (MYR)
              </label>
              <input
                type="number"
                min="1"
                step="1000"
                value={loanAmount}
                onChange={(e) => setLoanAmount(e.target.value)}
                placeholder="e.g. 500000"
                className={`input-field ${errors.loanAmount ? "border-risk-high ring-1 ring-risk-high/40" : ""}`}
              />
              {errors.loanAmount && <p className="text-xs text-risk-high">{errors.loanAmount}</p>}
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-brand-charcoal uppercase tracking-wide flex items-center gap-1.5">
                <User size={11} /> Evaluator
              </label>
              <div className="input-field bg-brand-bg text-brand-muted flex items-center gap-2 cursor-not-allowed select-none">
                <User size={12} className="shrink-0" />
                <span>{evaluator}</span>
              </div>
              <p className="text-[0.67rem] text-brand-subtext">Auto-filled from your session.</p>
            </div>

            <div className="h-px bg-brand-border" />

            <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2">
              Begin Evaluation
              <ChevronRight size={15} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Session Header Bar
// ---------------------------------------------------------------------------
function SessionHeader({ meta, onReset }: { meta: EvaluationMeta; onReset: () => void }) {
  const fmt = new Intl.NumberFormat("en-MY", {
    style: "currency", currency: "MYR", maximumFractionDigits: 0,
  });
  return (
    <div className="mx-5 mt-4 px-4 py-3 bg-brand-panel border border-brand-border rounded-xl
                    flex flex-wrap items-center gap-x-6 gap-y-2 animate-fade-in">
      <div className="flex items-center gap-2 min-w-0">
        <Building2 size={13} className="text-brand-muted shrink-0" />
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-widest text-brand-muted font-semibold">Company</p>
          <p className="text-sm font-bold text-brand-charcoal truncate">{meta.company_name}</p>
        </div>
      </div>
      <div className="h-7 w-px bg-brand-border hidden sm:block" />
      <div className="flex items-center gap-2">
        <Hash size={13} className="text-brand-muted shrink-0" />
        <div>
          <p className="text-[10px] uppercase tracking-widest text-brand-muted font-semibold">SSM</p>
          <p className="text-sm font-mono text-brand-charcoal">{meta.ssm_number}</p>
        </div>
      </div>
      <div className="h-7 w-px bg-brand-border hidden sm:block" />
      <div className="flex items-center gap-2">
        <DollarSign size={13} className="text-brand-muted shrink-0" />
        <div>
          <p className="text-[10px] uppercase tracking-widest text-brand-muted font-semibold">Loan Amount</p>
          <p className="text-sm font-semibold text-brand-charcoal">{fmt.format(meta.loan_amount)}</p>
        </div>
      </div>
      <div className="h-7 w-px bg-brand-border hidden sm:block" />
      <div className="flex items-center gap-2">
        <User size={13} className="text-brand-muted shrink-0" />
        <div>
          <p className="text-[10px] uppercase tracking-widest text-brand-muted font-semibold">Evaluator</p>
          <p className="text-sm text-brand-charcoal">{meta.evaluator}</p>
        </div>
      </div>
      <button
        onClick={onReset}
        className="ml-auto flex items-center gap-2 text-sm font-bold text-brand-charcoal
                   bg-brand-yellow hover:bg-brand-yellowHover
                   transition-colors duration-150 px-4 py-2 rounded-lg shadow-sm"
      >
        <RefreshCw size={13} />
        New Evaluation
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function DashboardPage() {
  const { user } = useAuth();
  const evaluator = user?.username ?? "unknown";

  const [sessionMeta, setSessionMeta] = useState<EvaluationMeta | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [showGate, setShowGate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prevents flash of empty state before sessionStorage is read
  const [hydrated, setHydrated] = useState(false);

  // Skip the persistence useEffect on the initial mount
  const isFirstRender = useRef(true);

  // ── Rehydrate from sessionStorage on mount ────────────────────────────────
  useEffect(() => {
    const saved = loadWorkspace();
    if (saved) {
      setSessionMeta(saved.meta);
      setResult(saved.result);
    }
    setHydrated(true);
  }, []);

  // ── Persist to sessionStorage whenever meta or result changes ─────────────
  useEffect(() => {
    if (!hydrated) return;
    if (isFirstRender.current) { isFirstRender.current = false; return; }
    if (sessionMeta) {
      saveWorkspace({ meta: sessionMeta, result });
    }
  }, [sessionMeta, result, hydrated]);

  // ── Gate submit ───────────────────────────────────────────────────────────
  const handleGateSubmit = useCallback((meta: EvaluationMeta) => {
    clearWorkspace();
    setSessionMeta(meta);
    setResult(null);
    setShowGate(false);
    setError(null);
  }, []);

  // ── New Evaluation — back to empty state ──────────────────────────────────
  const handleReset = useCallback(() => {
    clearWorkspace();
    setSessionMeta(null);
    setResult(null);
    setError(null);
  }, []);

  // ── Evaluate ──────────────────────────────────────────────────────────────
  const handleEvaluate = useCallback(async (financials: SMEFinancialData) => {
    if (!sessionMeta) return;
    setLoading(true);
    setError(null);
    try {
      const response = await predict({ meta: sessionMeta, financials });
      setResult(response);
      // Persist result immediately so navigation away won't lose it
      saveWorkspace({ meta: sessionMeta, result: response });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }, [sessionMeta]);

  // Don't render until sessionStorage has been read (prevents empty-state flash)
  if (!hydrated) return null;

  const isWorkspaceActive = sessionMeta !== null;

  return (
    <div className="min-h-screen bg-brand-cream">

      {/* Eagle watermark */}
      <div
        aria-hidden="true"
        className="fixed inset-0 z-0 flex items-center justify-center pointer-events-none select-none"
      >
        <Image
          src="/JuneBankEagle.png"
          alt=""
          width={760}
          height={760}
          priority
          style={{ opacity: 0.055, filter: "grayscale(1) contrast(0.8)" }}
        />
      </div>

      {/* Gate modal */}
      {showGate && (
        <GateModal
          evaluator={evaluator}
          onSubmit={handleGateSubmit}
          onClose={() => setShowGate(false)}
        />
      )}

      <div className="relative z-10 flex flex-col min-h-screen">

        {/* Error banner */}
        {error && (
          <div className="mx-5 mt-4 px-4 py-2.5 bg-risk-highBg border border-risk-high/30
                          rounded-lg text-risk-high text-sm flex items-center gap-2 animate-fade-in">
            <span className="font-semibold">Error</span>
            <span className="text-brand-border">·</span>
            <span className="flex-1">{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-risk-high/60 hover:text-risk-high transition-colors p-0.5 rounded"
              aria-label="Dismiss"
            >
              <X size={14} />
            </button>
          </div>
        )}

        {/* Session header */}
        {isWorkspaceActive && sessionMeta && (
          <SessionHeader meta={sessionMeta} onReset={handleReset} />
        )}

        {/* ── EMPTY STATE ─────────────────────────────────────────────────── */}
        {!isWorkspaceActive ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-6 px-4 py-16">
            <div className="text-center flex flex-col items-center gap-3 max-w-sm">
              <div className="h-16 w-16 rounded-2xl bg-brand-panel border border-brand-border
                              flex items-center justify-center shadow-card mb-2">
                <Building2 size={28} className="text-brand-muted" strokeWidth={1.5} />
              </div>
              <h1 className="text-2xl font-bold text-brand-charcoal font-heading">
                SME Risk Evaluation
              </h1>
              <p className="text-sm text-brand-muted leading-relaxed">
                Start a new evaluation to assess an SME&apos;s probability of default
                using the Random Forest model with SHAP explainability and AI advisory.
              </p>
            </div>
            <button
              onClick={() => setShowGate(true)}
              className="btn-primary flex items-center gap-2 px-6 py-3 text-base"
            >
              <Plus size={18} />
              Start New SME Evaluation
            </button>
            <p className="text-xs text-brand-subtext">
              You will be asked to provide the company name, SSM number, and loan amount before proceeding.
            </p>
          </div>

        ) : (
          /* ── WORKSPACE ──────────────────────────────────────────────────── */
          <main className="flex-1 grid grid-cols-1 xl:grid-cols-[400px_1fr_1fr] gap-5 p-5 items-start">

            <section className="panel flex flex-col gap-0 overflow-hidden">
              <div className="px-5 pt-5 pb-4 border-b border-brand-border">
                <p className="section-label">Company Financial Inputs</p>
                <h2 className="text-brand-charcoal font-bold text-base font-heading">SME Financial Profile</h2>
              </div>
              <div className="px-5 py-4">
                <InputForm onEvaluate={handleEvaluate} isLoading={loading} />
              </div>
            </section>

            <section className="panel flex flex-col gap-0 overflow-hidden xl:sticky" style={{ top: "20px" }}>
              <div className="px-5 pt-5 pb-4 border-b border-brand-border">
                <p className="section-label">Risk Assessment</p>
                <h2 className="text-brand-charcoal font-bold text-base font-heading">Probability of Default</h2>
              </div>
              <div className="px-5 py-4">
                {loading ? <Spinner label="Computing model…" />
                  : result ? <RiskGauge result={result} />
                    : <IdleMiddle />}
              </div>
            </section>

            <section className="panel flex flex-col gap-0 overflow-hidden xl:sticky" style={{ top: "20px" }}>
              <div className="px-5 pt-5 pb-4 border-b border-brand-border">
                <p className="section-label">Explainability & Advisory</p>
                <h2 className="text-brand-charcoal font-bold text-base font-heading">SHAP Analysis & Report</h2>
              </div>
              <div className="px-5 py-4">
                {loading ? <Spinner label="Computing SHAP…" />
                  : result ? (
                    <div className="flex flex-col gap-6 animate-fade-in">
                      <ShapChart features={result.shap_features} />
                      <div className="border-t border-brand-border pt-5">
                        <div className="flex items-center gap-2 mb-3">
                          <FileText size={12} className="text-brand-muted" />
                          <p className="section-label mb-0">AI Advisory Report</p>
                        </div>
                        <AdvisoryReport advisory={result.advisory} />
                      </div>
                    </div>
                  ) : <IdleRight />}
              </div>
            </section>

          </main>
        )}

        <footer className="border-t border-brand-border px-6 py-3 flex items-center
                           justify-between text-brand-muted text-xs mt-auto">
          <span>SHIELD · Final Year Project · For academic use only</span>
          <span>JuneBank Internal Tools · Random Forest + SHAP</span>
        </footer>

      </div>
    </div>
  );
}
