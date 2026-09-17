"use client";

// =============================================================================
// SHIELD — RiskGauge Component  (v1.2 — 4-tier classification)
// =============================================================================

import { useMemo } from "react";
import clsx from "clsx";
import { AlertTriangle, CheckCircle, Flame, ShieldAlert } from "lucide-react";
import type { PredictionResponse } from "@/lib/types";
import InfoTooltip from "@/components/InfoTooltip";

interface Props {
  result: PredictionResponse;
}

// ---------------------------------------------------------------------------
// 4-tier helpers
// ---------------------------------------------------------------------------
type Tier = "low" | "moderate" | "high" | "critical";

function getTier(pct: number): Tier {
  if (pct >= 80) return "critical";
  if (pct >= 60) return "high";
  if (pct >= 30) return "moderate";
  return "low";
}

function gaugeColor(tier: Tier): string {
  switch (tier) {
    case "critical": return "#DC2626";   // red
    case "high": return "#EA580C";   // orange
    case "moderate": return "#CA8A04";   // yellow
    case "low": return "#16A34A";   // green
  }
}

const TIER_CONFIG: Record<Tier, {
  icon: React.ElementType;
  label: string;          // banner label
  health: string;         // "Financially Healthy" | "Financially Distressed"
  badgeBg: string;
  badgeText: string;
  badgeBorder: string;
  cardLabel: string;      // left confidence card label
}> = {
  low: {
    icon: CheckCircle,
    label: "LOW RISK",
    health: "Financially Healthy",
    badgeBg: "bg-risk-lowBg",
    badgeText: "text-risk-low",
    badgeBorder: "border-risk-low/30",
    cardLabel: "Healthy",
  },
  moderate: {
    icon: ShieldAlert,
    label: "MODERATE RISK",
    health: "Financially Distressed",
    badgeBg: "bg-risk-moderateBg",
    badgeText: "text-risk-moderate",
    badgeBorder: "border-risk-moderate/30",
    cardLabel: "At Risk",
  },
  high: {
    icon: AlertTriangle,
    label: "HIGH RISK",
    health: "Financially Distressed",
    badgeBg: "bg-risk-highBg",
    badgeText: "text-risk-high",
    badgeBorder: "border-risk-high/30",
    cardLabel: "At Risk",
  },
  critical: {
    icon: Flame,
    label: "CRITICAL RISK",
    health: "Financially Distressed",
    badgeBg: "bg-risk-criticalBg",
    badgeText: "text-risk-critical",
    badgeBorder: "border-risk-critical/30",
    cardLabel: "At Risk",
  },
};

export default function RiskGauge({ result }: Props) {
  const { probability_pct, shap_base_value } = result;

  const tier = useMemo(() => getTier(probability_pct), [probability_pct]);
  const color = useMemo(() => gaugeColor(tier), [tier]);
  const config = TIER_CONFIG[tier];
  const Icon = config.icon;

  // ── Gauge geometry ─────────────────────────────────────────────────────────
  const R = 80;
  const CX = 100;
  const CY = 100;
  const STROKE = 16;
  const ARC = Math.PI * R;

  const D = `M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`;
  const pct = Math.min(100, Math.max(0, probability_pct));
  const dashOffset = ARC * (1 - pct / 100);

  return (
    <div className="flex flex-col gap-4 animate-fade-in">

      {/* ── Gauge SVG ──────────────────────────────────────────────────────── */}
      <div className="flex justify-center">
        <svg
          viewBox="5 5 190 105"
          width="210"
          height="105"
          aria-label={`Risk gauge: ${pct.toFixed(2)}%`}
        >
          <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="rgba(0,0,0,0.18)" />
            </filter>
          </defs>

          {/* Track */}
          <path d={D} fill="none" stroke="#E5E5E5" strokeWidth={STROKE} strokeLinecap="round" />

          {/* Fill */}
          <path
            d={D}
            fill="none"
            stroke={color}
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeDasharray={`${ARC} ${ARC}`}
            strokeDashoffset={dashOffset}
            filter="url(#glow)"
          />

          {/* Percentage readout */}
          <text
            x={CX} y={CY - 8}
            textAnchor="middle"
            fontSize="24"
            fontWeight="900"
            fontFamily="Lato, system-ui, sans-serif"
            fill={color}
          >
            {probability_pct.toFixed(2)}%
          </text>

          {/* Sub-label */}
          <text
            x={CX} y={CY + 10}
            textAnchor="middle"
            fontSize="7"
            fontWeight="600"
            fontFamily="Lato, system-ui, sans-serif"
            fill="#888"
            letterSpacing="2"
          >
            P(DEFAULT)
          </text>
        </svg>
      </div>

      {/* ── Classification banner ──────────────────────────────────────────── */}
      <div className={clsx(
        "flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 font-bold text-sm",
        "border",
        config.badgeBg,
        config.badgeText,
        config.badgeBorder,
      )}>
        <Icon size={15} />
        <span>{config.health} — {config.label}</span>
      </div>

      {/* ── Probability bar ────────────────────────────────────────────────── */}
      <div>
        <div className="flex justify-between text-xs text-brand-muted mb-1.5">
          <span>Risk Level</span>
          <span className="font-mono font-semibold" style={{ color }}>
            {probability_pct.toFixed(2)}%
          </span>
        </div>
        <div
          className="h-2 rounded-full overflow-hidden"
          style={{ background: "#E8E4DE", boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.08)" }}
        >
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${probability_pct}%`,
              background: "linear-gradient(90deg, #16A34A, #CA8A04, #D97706, #DC2626)",
            }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-brand-muted mt-1">
          <span>0% — Low</span>
          <span>30% Moderate</span>
          <span>60% High</span>
          <span>80% Critical</span>
        </div>
      </div>

      {/* ── Confidence breakdown ───────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3">
        {/* Left — always green: "Healthy" probability */}
        <div className="bg-risk-lowBg border border-risk-low/20 rounded-lg px-3 py-2.5 text-center">
          <p className="text-[10px] uppercase tracking-widest text-risk-low/70 mb-0.5">Healthy</p>
          <p className="text-xl font-black text-risk-low tabular-nums">
            {(100 - probability_pct).toFixed(2)}%
          </p>
        </div>
        {/* Right — always red: "Distressed" probability */}
        <div className="bg-risk-criticalBg border border-risk-critical/20 rounded-lg px-3 py-2.5 text-center">
          <p className="text-[10px] uppercase tracking-widest text-risk-critical/70 mb-0.5">Distressed</p>
          <p className="text-xl font-black text-risk-critical tabular-nums">
            {probability_pct.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* ── Model metadata ─────────────────────────────────────────────────── */}
      <div className="border-t border-brand-border pt-3 flex items-center justify-between text-[11px] text-brand-muted">
        <span>Random Forest + SHAP</span>
        <span className="flex items-center gap-1.5">
          Base value:{" "}
          <span className="font-mono text-brand-subtext">{shap_base_value.toFixed(4)}</span>
          <InfoTooltip
            size={11}
            text="The SHAP base value is the model's average predicted default probability across the entire training dataset. Each feature's SHAP value is an adjustment from this baseline — positive values push the final probability up, negative values push it down."
          />
        </span>
      </div>

    </div>
  );
}
