"use client";

// =============================================================================
// SHIELD — AdvisoryReport Component
// Renders the structured advisory from the /predict response:
//   • Tone banner (colour-coded by risk level) with LLM explanation
//   • Risk drivers table
//   • Protective factors table
//   • Recommendation block (structured action list)
// =============================================================================

import clsx from "clsx";
import type { LucideIcon } from "lucide-react";
import {
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Lightbulb,
} from "lucide-react";
import type { AdvisoryReport as AdvisoryReportType } from "@/lib/types";
import InfoTooltip from "@/components/InfoTooltip";

interface Props {
  advisory: AdvisoryReportType;
}

type ToneLevel = AdvisoryReportType["tone_level"];

// Each risk level maps to a colour scheme + a Lucide icon component
const TONE_CONFIG: Record<
  ToneLevel,
  {
    bg: string;
    border: string;
    text: string;
    subtext: string;
    divider: string;
    label: string;
    Icon: LucideIcon;
  }
> = {
  critical: {
    bg: "bg-risk-highBg",
    border: "border-risk-high/30",
    text: "text-risk-high",
    subtext: "text-risk-high/80",
    divider: "border-risk-high/20",
    label: "Critical Risk",
    Icon: AlertCircle,
  },
  elevated: {
    bg: "bg-[rgba(245,158,11,0.08)]",
    border: "border-risk-amber/30",
    text: "text-risk-amber",
    subtext: "text-risk-amber/80",
    divider: "border-risk-amber/20",
    label: "Elevated Risk",
    Icon: AlertTriangle,
  },
  moderate: {
    bg: "bg-[rgba(234,179,8,0.06)]",
    border: "border-yellow-500/30",
    text: "text-yellow-400",
    subtext: "text-yellow-400/80",
    divider: "border-yellow-500/20",
    label: "Moderate Risk",
    Icon: Info,
  },
  low: {
    bg: "bg-risk-lowBg",
    border: "border-risk-low/30",
    text: "text-risk-low",
    subtext: "text-risk-low/80",
    divider: "border-risk-low/20",
    label: "Low Risk",
    Icon: CheckCircle,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function splitSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+(?=[A-Z])/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function splitRecommendation(text: string): string[] {
  const numbered = text.split(/\n+\d+\.\s+/).filter(Boolean);
  if (numbered.length > 1) return numbered.map((s) => s.trim());

  const bulleted = text.split(/\n+[-•]\s+/).filter(Boolean);
  if (bulleted.length > 1) return bulleted.map((s) => s.trim());

  return splitSentences(text);
}

function ensurePeriod(s: string) {
  return s.endsWith(".") || s.endsWith("!") || s.endsWith("?") ? s : s + ".";
}

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
          "font-mono text-xs font-bold shrink-0 tabular-nums",
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
    advisory_source,
  } = advisory;

  const config = TONE_CONFIG[tone_level];
  const { Icon } = config;
  const isGroq = advisory_source === "groq";
  const explanationSentences = isGroq ? splitSentences(tone) : [tone];
  const recommendationPoints = isGroq ? splitRecommendation(recommendation) : [recommendation];

  return (
    <div className="flex flex-col gap-4 animate-fade-in">

      {/* ── Tone / Explanation Banner ───────────────────────────── */}
      <div className={clsx("rounded-lg border overflow-hidden", config.border)}>

        {/* Header row */}
        <div className={clsx("flex items-center gap-2 px-4 py-2.5", config.bg)}>
          <Icon size={13} className={config.text} />
          <p className={clsx("text-xs font-bold uppercase tracking-widest", config.text)}>
            {config.label}
          </p>
        </div>

        {/* Explanation body */}
        <div className={clsx("px-4 py-3 flex flex-col gap-2.5", config.bg)}>
          {explanationSentences.map((sentence, i) => (
            <div
              key={i}
              className={clsx(
                "flex gap-2.5 items-start",
                i > 0 && ["pt-2.5 border-t", config.divider]
              )}
            >
              {isGroq && explanationSentences.length > 1 && (
                <span className={clsx("mt-0.5 shrink-0 text-[10px] font-bold w-4 text-center leading-none", config.text)}>
                  {i + 1}
                </span>
              )}
              <p className={clsx("text-xs leading-relaxed", config.subtext)}>
                {ensurePeriod(sentence)}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Risk Drivers ────────────────────────────────────────── */}
      {risk_drivers.length > 0 && (
        <div className="bg-brand-bg rounded-lg border border-brand-border px-3 py-2">
          <p className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-semibold text-risk-high/70 mb-2">
            <TrendingUp size={11} className="text-risk-high/70" />
            Key Risk Drivers
            <InfoTooltip
              size={11}
              text="Each SHAP value shows how much this feature pushed the default probability up (+) or down (−) from the base value. A larger positive number means this metric is a stronger driver of distress for this SME."
            />
          </p>
          {risk_drivers.map((d) => (
            <FactorRow key={d.label} label={d.label} value={d.shap_value} direction="risk" />
          ))}
        </div>
      )}

      {/* ── Protective Factors ──────────────────────────────────── */}
      {protective_factors.length > 0 && (
        <div className="bg-brand-bg rounded-lg border border-brand-border px-3 py-2">
          <p className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-semibold text-risk-low/70 mb-2">
            <TrendingDown size={11} className="text-risk-low/70" />
            Protective Factors
            <InfoTooltip
              size={11}
              text="These features have negative SHAP values, meaning they reduce the predicted probability of default. The more negative the value, the stronger the protective effect of that metric for this SME."
            />
          </p>
          {protective_factors.map((d) => (
            <FactorRow key={d.label} label={d.label} value={d.shap_value} direction="protective" />
          ))}
        </div>
      )}

      {/* ── Recommendation ──────────────────────────────────────── */}
      <div className="rounded-lg border border-brand-yellow/25 bg-brand-yellow/5 overflow-hidden">

        <div className="flex items-center gap-2 px-4 py-2 border-b border-brand-yellow/20">
          <Lightbulb size={12} className="text-brand-yellow/80" />
          <p className="text-[10px] uppercase tracking-widest font-bold text-brand-yellow/80">
            Recommendation
          </p>
        </div>

        <div className="px-4 py-3 flex flex-col gap-3">
          {recommendationPoints.map((point, i) => (
            <div key={i} className="flex gap-3 items-start">
              <span className="shrink-0 mt-0.5 w-4 h-4 rounded-full bg-brand-yellow/20 border border-brand-yellow/40 flex items-center justify-center text-[9px] font-bold text-brand-yellow leading-none">
                {recommendationPoints.length > 1 ? i + 1 : "→"}
              </span>
              <p className="text-xs text-brand-subtext leading-relaxed">
                {ensurePeriod(point)}
              </p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
