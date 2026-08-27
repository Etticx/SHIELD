"use client";

// =============================================================================
// SHIELD — AdvisoryReport Component
// Renders the structured advisory from the /predict response:
//   • Tone banner (colour-coded by risk level)
//   • Risk drivers table
//   • Protective factors table
//   • Recommendation block
// =============================================================================

import clsx from "clsx";
import type { AdvisoryReport as AdvisoryReportType } from "@/lib/types";

interface Props {
  advisory: AdvisoryReportType;
}

type ToneLevel = AdvisoryReportType["tone_level"];

const TONE_STYLES: Record<ToneLevel, { bg: string; border: string; text: string; icon: string }> = {
  critical: {
    bg:     "bg-risk-highBg",
    border: "border-risk-high/30",
    text:   "text-risk-high",
    icon:   "🔴",
  },
  elevated: {
    bg:     "bg-[rgba(245,158,11,0.1)]",
    border: "border-risk-amber/30",
    text:   "text-risk-amber",
    icon:   "🟠",
  },
  moderate: {
    bg:     "bg-[rgba(234,179,8,0.08)]",
    border: "border-yellow-500/30",
    text:   "text-yellow-400",
    icon:   "🟡",
  },
  low: {
    bg:     "bg-risk-lowBg",
    border: "border-risk-low/30",
    text:   "text-risk-low",
    icon:   "🟢",
  },
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FactorRow({
  label,
  value,
  direction,
}: {
  label: string;
  value: number;
  direction: "risk" | "protective";
}) {
  const isRisk = direction === "risk";
  return (
    <div className="flex items-start justify-between gap-3 py-2 border-b border-brand-border/50 last:border-0">
      <span className="text-xs text-brand-subtext leading-snug flex-1">{label}</span>
      <span
        className={clsx(
          "font-mono text-xs font-bold shrink-0",
          isRisk ? "text-risk-high" : "text-risk-low"
        )}
      >
        {value > 0 ? "+" : ""}
        {value.toFixed(4)}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export default function AdvisoryReport({ advisory }: Props) {
  const {
    tone,
    tone_level,
    risk_drivers,
    protective_factors,
    recommendation,
  } = advisory;

  const style = TONE_STYLES[tone_level];

  return (
    <div className="flex flex-col gap-4 animate-fade-in">

      {/* ---- Section Header ---- */}
      <p className="section-label">AI Advisory Report</p>

      {/* ---- Tone Banner ---- */}
      <div
        className={clsx(
          "rounded-lg px-4 py-3 border",
          style.bg,
          style.border
        )}
      >
        <p className={clsx("text-sm font-semibold leading-snug", style.text)}>
          {style.icon} {tone}
        </p>
      </div>

      {/* ---- Risk Drivers ---- */}
      {risk_drivers.length > 0 && (
        <div className="bg-brand-bg rounded-lg border border-brand-border px-3 py-2">
          <p className="text-[10px] uppercase tracking-widest font-semibold text-risk-high/70 mb-2">
            ↑ Key Risk Drivers
          </p>
          {risk_drivers.map((d) => (
            <FactorRow
              key={d.label}
              label={d.label}
              value={d.shap_value}
              direction="risk"
            />
          ))}
        </div>
      )}

      {/* ---- Protective Factors ---- */}
      {protective_factors.length > 0 && (
        <div className="bg-brand-bg rounded-lg border border-brand-border px-3 py-2">
          <p className="text-[10px] uppercase tracking-widest font-semibold text-risk-low/70 mb-2">
            ↓ Protective Factors
          </p>
          {protective_factors.map((d) => (
            <FactorRow
              key={d.label}
              label={d.label}
              value={d.shap_value}
              direction="protective"
            />
          ))}
        </div>
      )}

      {/* ---- Recommendation ---- */}
      <div className="border-l-2 border-brand-yellow/60 pl-3 py-1">
        <p className="text-[10px] uppercase tracking-widest font-semibold text-brand-yellow/70 mb-1.5">
          Recommendation
        </p>
        <p className="text-xs text-brand-subtext leading-relaxed">{recommendation}</p>
      </div>

    </div>
  );
}
