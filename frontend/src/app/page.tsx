"use client";

// =============================================================================
// SHIELD — Main Dashboard Page
// 3-column layout: InputForm | RiskGauge | ShapChart + AdvisoryReport
// JuneBankEagle silhouette ghosted large in the page background.
// =============================================================================

import { useState, useCallback } from "react";
import Image from "next/image";
import { X } from "lucide-react";

import InputForm from "@/components/InputForm";
import RiskGauge from "@/components/RiskGauge";
import ShapChart from "@/components/ShapChart";
import AdvisoryReport from "@/components/AdvisoryReport";

import { predict } from "@/lib/api";
import type { SMEFinancialData, PredictionResponse } from "@/lib/types";

// ---------------------------------------------------------------------------
// Idle placeholders
// ---------------------------------------------------------------------------
function IdleMiddle() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[320px] text-brand-muted gap-3">
      <div className="h-12 w-12 rounded-full border-2 border-brand-border flex items-center justify-center text-brand-border text-xl">
        ?
      </div>
      <p className="text-sm text-center leading-relaxed">
        Fill in the financial metrics<br />and click{" "}
        <span className="text-brand-yellow font-semibold">Evaluate Risk</span> to begin.
      </p>
    </div>
  );
}

function IdleRight() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[320px] text-brand-muted gap-3">
      <svg
        width="48" height="48" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="1" strokeLinecap="round"
        strokeLinejoin="round" className="text-brand-border"
      >
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M3 9h18M9 21V9" />
      </svg>
      <p className="text-sm text-center leading-relaxed">
        SHAP explanations and the<br />advisory report will appear here.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function DashboardPage() {
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = useCallback(async (data: SMEFinancialData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await predict(data);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-brand-cream">

      {/* ================================================================
          BACKGROUND — JuneBank Eagle silhouette watermark
          Fixed, ghosted, full eagle visible — official feel.
      ================================================================ */}
      <div
        aria-hidden="true"
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          pointerEvents: "none",
          userSelect: "none",
        }}
      >
        <Image
          src="/JuneBankEagle.png"
          alt=""
          width={780}
          height={780}
          priority
          style={{
            opacity: 0.06,
            filter: "grayscale(1) contrast(0.8)",
            pointerEvents: "none",
            userSelect: "none",
            marginTop: "-40px",
          }}
        />
      </div>

      {/* All content above the watermark */}
      <div className="relative flex flex-col min-h-screen" style={{ zIndex: 1 }}>

        {/* ---- ERROR BANNER ---- */}
        {error && (
          <div className="mx-6 mt-4 px-4 py-3 bg-risk-highBg border border-risk-high/30
                          rounded-lg text-risk-high text-sm flex items-center gap-2 animate-fade-in">
            <span className="font-bold">Error</span>
            <span className="text-brand-border">·</span>
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-risk-high/60 hover:text-risk-high transition-colors p-0.5 rounded"
              aria-label="Dismiss"
            >
              <X size={14} />
            </button>
          </div>
        )}

        {/* ---- 3-COLUMN GRID ---- */}
        <main className="flex-1 grid grid-cols-1 xl:grid-cols-[400px_1fr_1fr] gap-5 p-5 items-start">

          {/* LEFT: Input Form */}
          <section className="panel flex flex-col gap-0 overflow-hidden">
            <div className="px-5 pt-5 pb-4 border-b border-brand-border">
              <p className="section-label">Company Financial Inputs</p>
              <h2 className="text-brand-text font-semibold text-base">SME Financial Profile</h2>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4">
              <InputForm onEvaluate={handleEvaluate} isLoading={loading} />
            </div>
          </section>

          {/* MIDDLE: Risk Gauge */}
          <section className="panel px-5 py-5 flex flex-col gap-4">
            <div className="border-b border-brand-border pb-4">
              <p className="section-label">Risk Assessment</p>
              <h2 className="text-brand-text font-semibold text-base">Probability of Default</h2>
            </div>
            {loading ? (
              <div className="flex items-center justify-center min-h-[320px]">
                <div className="flex flex-col items-center gap-3">
                  <div className="h-10 w-10 rounded-full border-2 border-brand-yellow border-t-transparent animate-spin" />
                  <span className="text-brand-muted text-sm">Computing model…</span>
                </div>
              </div>
            ) : result ? (
              <RiskGauge result={result} />
            ) : (
              <IdleMiddle />
            )}
          </section>

          {/* RIGHT: SHAP + Advisory */}
          <section className="panel px-5 py-5 flex flex-col gap-4">
            <div className="border-b border-brand-border pb-4">
              <p className="section-label">Explainability & Advisory</p>
              <h2 className="text-brand-text font-semibold text-base">SHAP Analysis & Report</h2>
            </div>
            {loading ? (
              <div className="flex items-center justify-center min-h-[320px]">
                <div className="flex flex-col items-center gap-3">
                  <div className="h-10 w-10 rounded-full border-2 border-brand-yellow border-t-transparent animate-spin" />
                  <span className="text-brand-muted text-sm">Computing SHAP…</span>
                </div>
              </div>
            ) : result ? (
              <div className="flex flex-col gap-6 animate-fade-in">
                <ShapChart features={result.shap_features} />
                <AdvisoryReport advisory={result.advisory} />
              </div>
            ) : (
              <IdleRight />
            )}
          </section>

        </main>

        {/* ---- FOOTER ---- */}
        <footer className="border-t border-brand-border px-6 py-3 flex items-center justify-between text-brand-muted text-xs">
          <span>SHIELD · Final Year Project · For academic use only</span>
          <span>JuneBank Internal Tools · XGBoost + SHAP</span>
        </footer>

      </div>{/* end z-1 content wrapper */}
    </div>
  );
}
