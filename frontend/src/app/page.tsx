"use client";

// =============================================================================
// SHIELD — Main Dashboard Page  (v1.4 — persistent workspace)
//
// Workspace state (sessionMeta + financial draft + result) is persisted to sessionStorage so
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
  ChevronRight, RefreshCw,
} from "lucide-react";

import Modal from "@/components/Modal";
import InputForm from "@/components/AccountingInputForm";
import RiskGauge from "@/components/RiskGauge";
import ShapChart from "@/components/ShapChart";
import AdvisoryReport from "@/components/AdvisoryReport";

import { predictAccounting as predict } from "@/lib/api";
import { createFinancialDraft, assessReadiness } from "@/lib/accounting-inputs";
import type { AccountingData, FinancialDraft } from "@/lib/accounting-inputs";
import { useAuth } from "@/lib/auth";
import type {
  EvaluationMeta,
  PredictionResponse,
} from "@/lib/types";

// ---------------------------------------------------------------------------
// sessionStorage helpers
// ---------------------------------------------------------------------------
const WORKSPACE_KEY = "shield_seven_ratios_workspace_v1";

interface PersistedWorkspace {
  meta: EvaluationMeta;
  result: PredictionResponse | null;
  draft?: FinancialDraft; // Older saved workspaces did not include input values.
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
function IdleMiddle({ draft }: { draft: FinancialDraft }) {
  const readiness = assessReadiness(draft);
  // Ghost gauge: the arc fills with input completeness, never with a risk value.
  const arc = 251;
  const filled = (readiness.provided / 7) * arc;
  return (
    <div className="flex flex-col items-center justify-center min-h-[280px] text-brand-muted gap-3 py-8">
      <svg width="200" height="110" viewBox="0 0 200 110" aria-hidden="true">
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="#E8E4DE" strokeWidth="14" strokeLinecap="round" />
        {filled > 0 && (
          <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="#C9C3BA" strokeWidth="14" strokeLinecap="round"
            strokeDasharray={`${filled} ${arc}`} className="transition-all duration-300" />
        )}
        <text x="100" y="92" textAnchor="middle" className="fill-brand-muted font-mono" fontSize="22">—</text>
      </svg>
      <p className="text-sm font-semibold text-brand-charcoal">
        {readiness.ready ? "Ready to evaluate" : `${readiness.provided} of 7 ratios provided`}
      </p>
      <p className="text-sm text-center leading-relaxed max-w-[260px]">
        {readiness.ready
          ? "Click Evaluate Risk to calculate the assessment. Complete inputs do not verify the underlying records."
          : "Complete the required inputs or request supporting records. No risk score has been calculated yet."}
      </p>
    </div>
  );
}

function IdleRight() {
  const ghostBars = [88, 72, 60, 48, 38, 26, 16];
  return (
    <div className="flex flex-col justify-center min-h-[280px] text-brand-muted gap-4 py-8" >
      <div className="flex flex-col gap-2" aria-hidden="true">
        {ghostBars.map((w, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="h-2.5 w-20 rounded bg-brand-border/70" />
            <div className="h-2.5 rounded bg-brand-border" style={{ width: `${w}%` }} />
          </div>
        ))}
      </div>
      <p className="text-sm leading-relaxed">
        Each ratio&apos;s push toward or away from default, plus the written advisory, will appear here after evaluation.
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
    <Modal
      title="Identify the SME"
      subtitle="This information is saved with every evaluation for audit purposes."
      onClose={onClose}
      dismissOnBackdrop={!companyName && !ssmNumber && !loanAmount}
    >
          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">

            <div className="flex flex-col gap-1.5">
              <label htmlFor="gate-company" className="text-sm font-semibold text-brand-charcoal flex items-center gap-1.5">
                <Building2 size={11} /> Company name
              </label>
              <input
                type="text"
                id="gate-company"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Syarikat Maju Jaya Sdn Bhd"
                className={`input-field ${errors.companyName ? "border-risk-high ring-1 ring-risk-high/40" : ""}`}
              />
              {errors.companyName && <p className="text-xs text-risk-high">{errors.companyName}</p>}
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="gate-ssm" className="text-sm font-semibold text-brand-charcoal flex items-center gap-1.5">
                <Hash size={11} /> Business Reg. No. (SSM)
              </label>
              <input
                type="text"
                id="gate-ssm"
                value={ssmNumber}
                onChange={(e) => setSsmNumber(e.target.value)}
                placeholder="e.g. 1234567-A"
                className={`input-field ${errors.ssmNumber ? "border-risk-high ring-1 ring-risk-high/40" : ""}`}
              />
              {errors.ssmNumber && <p className="text-xs text-risk-high">{errors.ssmNumber}</p>}
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="gate-loan" className="text-sm font-semibold text-brand-charcoal flex items-center gap-1.5">
                <DollarSign size={11} /> Requested loan amount (MYR)
              </label>
              <input
                type="number"
                min="1"
                step="1000"
                id="gate-loan"
                value={loanAmount}
                onChange={(e) => setLoanAmount(e.target.value)}
                placeholder="e.g. 500000"
                className={`input-field ${errors.loanAmount ? "border-risk-high ring-1 ring-risk-high/40" : ""}`}
              />
              {errors.loanAmount && <p className="text-xs text-risk-high">{errors.loanAmount}</p>}
            </div>

            <div className="flex flex-col gap-1.5">
              <p className="text-sm font-semibold text-brand-charcoal flex items-center gap-1.5">
                <User size={11} /> Evaluator
              </p>
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
    </Modal>
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
          <p className="text-xs text-brand-muted">Company</p>
          <p className="text-sm font-bold text-brand-charcoal truncate">{meta.company_name}</p>
        </div>
      </div>
      <div className="h-7 w-px bg-brand-border hidden sm:block" />
      <div className="flex items-center gap-2">
        <Hash size={13} className="text-brand-muted shrink-0" />
        <div>
          <p className="text-xs text-brand-muted">SSM</p>
          <p className="text-sm font-mono text-brand-charcoal">{meta.ssm_number}</p>
        </div>
      </div>
      <div className="h-7 w-px bg-brand-border hidden sm:block" />
      <div className="flex items-center gap-2">
        <DollarSign size={13} className="text-brand-muted shrink-0" />
        <div>
          <p className="text-xs text-brand-muted">Loan amount</p>
          <p className="text-sm font-semibold text-brand-charcoal">{fmt.format(meta.loan_amount)}</p>
        </div>
      </div>
      <div className="h-7 w-px bg-brand-border hidden sm:block" />
      <div className="flex items-center gap-2">
        <User size={13} className="text-brand-muted shrink-0" />
        <div>
          <p className="text-xs text-brand-muted">Evaluator</p>
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
  const [draft, setDraft] = useState<FinancialDraft>(() => createFinancialDraft());
  const [showGate, setShowGate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prevents flash of empty state before sessionStorage is read
  const [hydrated, setHydrated] = useState(false);

  // Skip the persistence useEffect on the initial mount
  const isFirstRender = useRef(true);
  const evaluationVersion = useRef(0);
  const resultsRef = useRef<HTMLDivElement>(null);

  // A response arriving after navigation must not overwrite the saved draft.
  useEffect(() => () => { evaluationVersion.current++; }, []);

  // ── Rehydrate from sessionStorage on mount ────────────────────────────────
  useEffect(() => {
    const saved = loadWorkspace();
    if (saved) {
      setSessionMeta(saved.meta);
      if (saved.draft) {
        setDraft(saved.draft);
        setResult(assessReadiness(saved.draft).ready ? saved.result : null);
      }
    }
    setHydrated(true);
  }, []);

  // ── Persist the matching metadata, inputs and result ──────────────────────
  useEffect(() => {
    if (!hydrated) return;
    if (isFirstRender.current) { isFirstRender.current = false; return; }
    if (sessionMeta) {
      saveWorkspace({ meta: sessionMeta, draft, result });
    }
  }, [sessionMeta, draft, result, hydrated]);

  // ── Gate submit ───────────────────────────────────────────────────────────
  const handleGateSubmit = useCallback((meta: EvaluationMeta) => {
    evaluationVersion.current++;
    clearWorkspace();
    setSessionMeta(meta);
    setDraft(createFinancialDraft());
    setResult(null);
    setLoading(false);
    setShowGate(false);
    setError(null);
  }, []);

  // ── New Evaluation — back to empty state ──────────────────────────────────
  const handleReset = useCallback(() => {
    evaluationVersion.current++;
    clearWorkspace();
    setSessionMeta(null);
    setDraft(createFinancialDraft());
    setResult(null);
    setLoading(false);
    setError(null);
  }, []);

  const handleDraftChange = useCallback((nextDraft: FinancialDraft) => {
    evaluationVersion.current++;
    setDraft(nextDraft);
    setResult(null);
    setError(null);
    setLoading(false);
    if (sessionMeta) saveWorkspace({ meta: sessionMeta, draft: nextDraft, result: null });
  }, [sessionMeta]);

  // ── Evaluate ──────────────────────────────────────────────────────────────
  const handleEvaluate = useCallback(async (financials: AccountingData) => {
    if (!sessionMeta || !assessReadiness(draft).ready || loading) return;
    const version = ++evaluationVersion.current;
    setLoading(true);
    setError(null);
    try {
      const response = await predict({ meta: sessionMeta, financials });
      if (version !== evaluationVersion.current) return;
      setResult(response);
      // Stacked layout puts the score below the form; bring it into view.
      if (window.innerWidth < 1024) resultsRef.current?.scrollIntoView({ behavior: "smooth" });
      // Persist result immediately so navigation away won't lose it
      saveWorkspace({ meta: sessionMeta, draft, result: response });
    } catch (err) {
      if (version === evaluationVersion.current) setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      if (version === evaluationVersion.current) setLoading(false);
    }
  }, [sessionMeta, draft, loading]);

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
              <h1 className="text-2xl font-bold text-brand-charcoal font-heading">
                SME Risk Evaluation
              </h1>
              <p className="text-sm text-brand-muted leading-relaxed">
                Score an SME&apos;s default risk from 7 financial ratios, see which
                ratios drove the score, and get a written advisory for the credit file.
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
          <main className="flex-1 grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-5 p-5 items-start">

            {/* Inputs stay beside the results so officers can tweak a ratio and re-run. */}
            <section className="panel flex flex-col gap-0 overflow-hidden lg:sticky lg:top-5 lg:max-h-[calc(100vh-40px)] lg:overflow-y-auto">
              <div className="px-5 pt-5 pb-4 border-b border-brand-border">
                <p className="section-label">Company Financial Inputs</p>
                <h2 className="text-brand-charcoal font-bold text-base font-heading">SME Financial Profile</h2>
              </div>
              <div className="px-5 py-4">
                <InputForm
                  draft={draft}
                  onDraftChange={handleDraftChange}
                  onEvaluate={handleEvaluate}
                  isLoading={loading}
                />
              </div>
            </section>

            <div ref={resultsRef} className="grid grid-cols-1 xl:grid-cols-2 gap-5 scroll-mt-5">
              <section className="panel flex flex-col gap-0 overflow-hidden">
                <div className="px-5 pt-5 pb-4 border-b border-brand-border">
                  <p className="section-label">Risk Assessment</p>
                  <h2 className="text-brand-charcoal font-bold text-base font-heading">Probability of Default</h2>
                </div>
                <div className="px-5 py-4">
                  {loading ? <Spinner label="Computing model…" />
                    : result ? <RiskGauge result={result} />
                      : <IdleMiddle draft={draft} />}
                </div>
              </section>

              <section className="panel flex flex-col gap-0 overflow-hidden">
                <div className="px-5 pt-5 pb-4 border-b border-brand-border">
                  <p className="section-label">Explainability</p>
                  <h2 className="text-brand-charcoal font-bold text-base font-heading">What Drove the Score</h2>
                </div>
                <div className="px-5 py-4">
                  {loading ? <Spinner label="Computing SHAP…" />
                    : result ? <div className="animate-fade-in"><ShapChart features={result.shap_features} /></div>
                      : <IdleRight />}
                </div>
              </section>

              {result && !loading && (
                <section className="panel flex flex-col gap-0 overflow-hidden xl:col-span-2 animate-fade-in">
                  <div className="px-5 pt-5 pb-4 border-b border-brand-border">
                    <p className="section-label">Advisory</p>
                    <h2 className="text-brand-charcoal font-bold text-base font-heading">AI Advisory Report</h2>
                  </div>
                  <div className="px-5 py-4">
                    <AdvisoryReport advisory={result.advisory} />
                  </div>
                </section>
              )}
            </div>

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
