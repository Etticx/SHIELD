"use client";

import { useMemo } from "react";
import clsx from "clsx";
import { AlertTriangle, CheckCircle } from "lucide-react";
import type { PredictionResponse } from "@/lib/types";

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
  const { probability_pct, is_high_risk, shap_base_value, shap_features } = result;
  const color = useMemo(() => gaugeColor(probability_pct), [probability_pct]);

  // ── Gauge geometry ──────────────────────────────────────────────────────────
  // Both track and fill use the EXACT SAME hardcoded path string.
  // The path is a semicircle: from left (20,100) counter-clockwise over the
  // top to right (180,100). Verified by hand:
  //   M 20 100          → move to left tip
  //   A 80 80 0 0 1 180 100  → arc: rx=80 ry=80, x-rot=0,
  //                            large-arc=0, sweep=1 (clockwise in SVG),
  //                            end at right tip (180,100)
  //
  // SVG sweep-flag=1 from (20,100) to (180,100) short arc = UPPER half ✓
  // (The short clockwise arc from left-middle to right-middle goes UPWARD)
  //
  // Path length = π × R = π × 80 ≈ 251.33
  //
  // Fill technique: strokeDasharray="251.33 251.33"
  //   strokeDashoffset = 251.33 × (1 - pct/100)
  //   → offset=251.33 means nothing shown (0%)
  //   → offset=0      means full arc shown (100%)

  const R = 80;
  const CX = 100;
  const CY = 100;
  const STROKE = 16;
  const ARC = Math.PI * R; // ≈ 251.33 — exact semicircle length

  // Single shared path: left tip → clockwise short arc → right tip (upper half)
  const D = `M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`;

  const pct = Math.min(100, Math.max(0, probability_pct));
  const dashOffset = ARC * (1 - pct / 100);

  const top5 = useMemo(
    () =>
      [...shap_features]
        .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
        .slice(0, 5),
    [shap_features]
  );

  return (
    <div className="flex flex-col gap-5 animate-fade-in">

      {/* ── Gauge ──────────────────────────────────────────────────────────── */}
      <div className="flex justify-center">
        {/*
          viewBox: left edge=5, top=15 (arc top = CY-R = 20), width=190, height=120
          Bottom of viewBox = 15+120 = 135, well below CY=100 for text room.
          Arc endpoints sit at y=100; text at y=115 and y=130 are fully visible.
        */}
        <svg viewBox="5 5 190 130" width="240" height="156" aria-label={`Risk gauge: ${pct.toFixed(1)}%`}>
          <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="rgba(0,0,0,0.18)" />
            </filter>
          </defs>

          {/* Track — grey, full semicircle, never changes */}
          <path
            d={D}
            fill="none"
            stroke="#E5E5E5"
            strokeWidth={STROKE}
            strokeLinecap="round"
          />

          {/* Fill — same path, revealed left→right by dashOffset */}
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

          {/* Percentage */}
          <text
            x={CX} y={CY + 18}
            textAnchor="middle"
            fontSize="26"
            fontWeight="900"
            fontFamily="Lato, system-ui, sans-serif"
            fill={color}
          >
            {probability_pct.toFixed(1)}%
          </text>

          {/* Label */}
          <text
            x={CX} y={CY + 34}
            textAnchor="middle"
            fontSize="7.5"
            fontWeight="600"
            fontFamily="Lato, system-ui, sans-serif"
            fill="#888"
            letterSpacing="2"
          >
            P(DEFAULT)
          </text>
        </svg>
      </div>

      {/* ── Classification Badge ───────────────────────────────────────────── */}
      <div className={clsx(
        "flex items-center justify-center gap-2 rounded-lg px-4 py-3 font-bold text-sm",
        is_high_risk
          ? "bg-risk-highBg text-risk-high border border-risk-high/30"
          : "bg-risk-lowBg text-risk-low border border-risk-low/30"
      )}>
        <span className="text-base">{is_high_risk ? <AlertTriangle size={16} /> : <CheckCircle size={16} />}</span>
        <span>{is_high_risk ? "Financially Distressed — HIGH RISK" : "Financially Healthy — LOW RISK"}</span>
      </div>

      {/* ── Probability Bar ────────────────────────────────────────────────── */}
      <div>
        <div className="flex justify-between text-xs text-brand-muted mb-1.5">
          <span>Risk Level</span>
          <span className="font-mono font-semibold" style={{ color }}>{probability_pct.toFixed(2)}%</span>
        </div>
        <div className="h-2.5 rounded-full overflow-hidden"
          style={{ background: "#E8E4DE", boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.10)" }}>
          <div className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${probability_pct}%`,
              background: "linear-gradient(90deg, #16A34A, #D97706, #DC2626)",
            }} />
        </div>
        <div className="flex justify-between text-[10px] text-brand-muted mt-1">
          <span>0% — Low</span>
          <span>50% Threshold</span>
          <span>High — 100%</span>
        </div>
      </div>

      {/* ── Confidence Breakdown ───────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-risk-lowBg border border-risk-low/20 rounded-lg px-3 py-3 text-center">
          <p className="text-[10px] uppercase tracking-widest text-risk-low/70 mb-1">Healthy</p>
          <p className="text-2xl font-black text-risk-low tabular-nums">{(100 - probability_pct).toFixed(1)}%</p>
        </div>
        <div className="bg-risk-highBg border border-risk-high/20 rounded-lg px-3 py-3 text-center">
          <p className="text-[10px] uppercase tracking-widest text-risk-high/70 mb-1">Distressed</p>
          <p className="text-2xl font-black text-risk-high tabular-nums">{probability_pct.toFixed(1)}%</p>
        </div>
      </div>

      {/* ── SHAP Base Value ────────────────────────────────────────────────── */}
      <p className="text-[11px] text-brand-muted text-center">
        SHAP base value:{" "}
        <span className="font-mono text-brand-subtext">{shap_base_value.toFixed(4)}</span>
      </p>

      {/* ── Top 5 Impact Snapshot ──────────────────────────────────────────── */}
      <div>
        <p className="section-label">Top 5 Features by Risk Impact</p>
        <div className="flex flex-col gap-1.5">
          {top5.map((f) => (
            <div key={f.label}
              className="flex items-center justify-between gap-2 text-xs bg-brand-bg rounded px-2 py-1.5 border border-brand-border">
              <span className="text-brand-subtext truncate flex-1" title={f.label}>{f.label}</span>
              <span className={clsx("font-mono font-semibold shrink-0",
                f.direction === "risk" ? "text-risk-high" : "text-risk-low")}>
                {f.shap_value > 0 ? "+" : ""}{f.shap_value.toFixed(4)}
              </span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
