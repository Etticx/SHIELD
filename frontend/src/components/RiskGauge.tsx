"use client";

// =============================================================================
// SHIELD — RiskGauge Component  (v1.1 layout)
//
// Changes from v1.0:
//   • Removed "Top 5 Features" snapshot — now lives in ShapChart for better
//     information architecture (all SHAP data in one place).
//   • Gauge SVG scaled down slightly to fit the narrower half-width column.
//   • Confidence breakdown cards tightened.
//   • SHAP base value retained as a footnote.
// =============================================================================

import { useMemo } from "react";
import clsx from "clsx";
import { AlertTriangle, CheckCircle } from "lucide-react";
import type { PredictionResponse } from "@/lib/types";
import InfoTooltip from "@/components/InfoTooltip";

interface Props {
  result: PredictionResponse;
}

function gaugeColor(pct: number): string {
  if (pct >= 70) return "#DC2626";
  if (pct >= 50) return "#D97706";
  if (pct >= 30) return "#CA8A04";
  return "#16A34A";
}

export default function RiskGauge({ result }: Props) {
  const { probability_pct, is_high_risk, shap_base_value } = result;
  const color = useMemo(() => gaugeColor(probability_pct), [probability_pct]);

  // ── Gauge geometry ─────────────────────────────────────────────────────────
  const R = 80;
  const CX = 100;
  const CY = 100;
  const STROKE = 16;
  const ARC = Math.PI * R;   // ≈ 251.33 — exact semicircle length

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

          {/* Percentage readout — centred inside the arc bowl */}
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

      {/* ── Classification badge ───────────────────────────────────────────── */}
      <div className={clsx(
        "flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 font-bold text-sm",
        is_high_risk
          ? "bg-risk-highBg text-risk-high border border-risk-high/30"
          : "bg-risk-lowBg text-risk-low border border-risk-low/30"
      )}>
        {is_high_risk ? <AlertTriangle size={15} /> : <CheckCircle size={15} />}
        <span>{is_high_risk ? "Financially Distressed — HIGH RISK" : "Financially Healthy — LOW RISK"}</span>
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
              background: "linear-gradient(90deg, #16A34A, #D97706, #DC2626)",
            }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-brand-muted mt-1">
          <span>0% — Low</span>
          <span>50% Threshold</span>
          <span>High — 100%</span>
        </div>
      </div>

      {/* ── Confidence breakdown ───────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-risk-lowBg border border-risk-low/20 rounded-lg px-3 py-2.5 text-center">
          <p className="text-[10px] uppercase tracking-widest text-risk-low/70 mb-0.5">Healthy</p>
          <p className="text-xl font-black text-risk-low tabular-nums">
            {(100 - probability_pct).toFixed(2)}%
          </p>
        </div>
        <div className="bg-risk-highBg border border-risk-high/20 rounded-lg px-3 py-2.5 text-center">
          <p className="text-[10px] uppercase tracking-widest text-risk-high/70 mb-0.5">Distressed</p>
          <p className="text-xl font-black text-risk-high tabular-nums">
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
