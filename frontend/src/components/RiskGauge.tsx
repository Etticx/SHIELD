"use client";

// =============================================================================
// SHIELD — RiskGauge Component  (3-band classification, set by backend)
// =============================================================================

import { useMemo } from "react";
import clsx from "clsx";

import type { PredictionResponse } from "@/lib/types";
import InfoTooltip from "@/components/InfoTooltip";

interface Props {
  result: PredictionResponse;
}

// ---------------------------------------------------------------------------
// 3-band helpers — band comes from the backend so cut-points live in one place
// ---------------------------------------------------------------------------
type Tier = "low" | "medium" | "high";

const TIER_OF: Record<PredictionResponse["classification"], Tier> = {
  "Low Risk": "low", "Medium Risk": "medium", "High Risk": "high",
};

function gaugeColor(tier: Tier): string {
  switch (tier) {
    case "high": return "#DC2626";   // red
    case "medium": return "#CA8A04";   // yellow
    case "low": return "#16A34A";   // green
  }
}

const TIER_CONFIG: Record<Tier, {
  label: string;          // banner label
  health: string;         // "Financially Healthy" | "Financially Distressed"
  badgeBg: string;
  badgeText: string;
  badgeBorder: string;
  cardLabel: string;      // left confidence card label
}> = {
  low: {
    label: "LOW RISK",
    health: "Financially Healthy",
    badgeBg: "bg-risk-lowBg",
    badgeText: "text-risk-low",
    badgeBorder: "border-risk-low/30",
    cardLabel: "Healthy",
  },
  medium: {
    label: "MEDIUM RISK",
    health: "Review Advised",
    badgeBg: "bg-risk-moderateBg",
    badgeText: "text-risk-moderate",
    badgeBorder: "border-risk-moderate/30",
    cardLabel: "At Risk",
  },
  high: {
    label: "HIGH RISK",
    health: "Financially Distressed",
    badgeBg: "bg-risk-criticalBg",
    badgeText: "text-risk-critical",
    badgeBorder: "border-risk-critical/30",
    cardLabel: "At Risk",
  },
};

export default function RiskGauge({ result }: Props) {
  const { probability_pct, shap_base_value, classification } = result;

  const tier = TIER_OF[classification] ?? "low";
  const color = useMemo(() => gaugeColor(tier), [tier]);
  const config = TIER_CONFIG[tier];

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
              background: "linear-gradient(90deg, #16A34A, #CA8A04, #DC2626)",
            }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-brand-muted mt-1">
          <span>0% — Low</span>
          <span>19.8% Medium</span>
          <span>50% High</span>
          <span>100%</span>
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
        <span>XGBoost + SHAP</span>
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
