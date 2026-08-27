"use client";

// =============================================================================
// SHIELD — RiskGauge Component
// Recharts RadialBarChart renders the P(default) arc.
// The large numeric display and classification badge sit in the chart centre.
// =============================================================================

import { useMemo } from "react";
import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";
import clsx from "clsx";
import type { PredictionResponse } from "@/lib/types";

interface Props {
  result: PredictionResponse;
}

// Colour stops matching the Streamlit gradient: green → amber → red
function gaugeColor(pct: number): string {
  if (pct >= 70) return "#ef4444"; // risk-high
  if (pct >= 50) return "#f59e0b"; // risk-amber
  if (pct >= 30) return "#eab308"; // yellow-500
  return "#22c55e";                // risk-low
}

export default function RiskGauge({ result }: Props) {
  const { probability_pct, is_high_risk, classification, shap_base_value, shap_features } =
    result;

  const color = useMemo(() => gaugeColor(probability_pct), [probability_pct]);

  // Recharts RadialBar expects a data array; we use a 0-100 domain
  const chartData = [{ value: probability_pct, fill: color }];

  // Top 5 features by absolute SHAP impact
  const top5 = useMemo(
    () => [...shap_features].sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)).slice(0, 5),
    [shap_features]
  );

  return (
    <div className="flex flex-col gap-5 animate-fade-in">

      {/* ---- Gauge ---- */}
      <div className="relative flex items-center justify-center" style={{ height: 240 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="55%"
            innerRadius="70%"
            outerRadius="90%"
            barSize={14}
            data={chartData}
            startAngle={210}
            endAngle={-30}
          >
            {/* Full-range background track */}
            <PolarAngleAxis
              type="number"
              domain={[0, 100]}
              angleAxisId={0}
              tick={false}
            />
            {/* Background arc */}
            <RadialBar
              background={{ fill: "#2a2d36" }}
              dataKey="value"
              angleAxisId={0}
              cornerRadius={6}
              isAnimationActive
              animationDuration={900}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        {/* Centre overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pb-4 pointer-events-none">
          <span
            className="text-5xl font-black leading-none tabular-nums"
            style={{ color }}
          >
            {probability_pct.toFixed(1)}%
          </span>
          <span className="text-xs text-brand-muted mt-1 tracking-widest uppercase">
            P(Default)
          </span>
        </div>
      </div>

      {/* ---- Classification Badge ---- */}
      <div
        className={clsx(
          "flex items-center justify-center gap-2 rounded-lg px-4 py-3 font-bold text-sm",
          is_high_risk
            ? "bg-risk-highBg text-risk-high border border-risk-high/30"
            : "bg-risk-lowBg text-risk-low border border-risk-low/30"
        )}
      >
        <span className="text-base">{is_high_risk ? "⚠️" : "✅"}</span>
        <span>
          {is_high_risk
            ? "Financially Distressed — HIGH RISK"
            : "Financially Healthy — LOW RISK"}
        </span>
      </div>

      {/* ---- Probability Bar ---- */}
      <div>
        <div className="flex justify-between text-xs text-brand-muted mb-1.5">
          <span>Risk Level</span>
          <span className="font-mono" style={{ color }}>{probability_pct.toFixed(2)}%</span>
        </div>
        <div className="h-2 bg-brand-border rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${probability_pct}%`,
              background: `linear-gradient(90deg, #22c55e, #f59e0b, #ef4444)`,
            }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-brand-muted mt-1">
          <span>0%  Low</span>
          <span>50%  Threshold</span>
          <span>High  100%</span>
        </div>
      </div>

      {/* ---- Confidence Breakdown ---- */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-risk-lowBg border border-risk-low/20 rounded-lg px-3 py-3 text-center">
          <p className="text-[10px] uppercase tracking-widest text-risk-low/70 mb-1">Healthy</p>
          <p className="text-2xl font-black text-risk-low tabular-nums">
            {(100 - probability_pct).toFixed(1)}%
          </p>
        </div>
        <div className="bg-risk-highBg border border-risk-high/20 rounded-lg px-3 py-3 text-center">
          <p className="text-[10px] uppercase tracking-widest text-risk-high/70 mb-1">Distressed</p>
          <p className="text-2xl font-black text-risk-high tabular-nums">
            {probability_pct.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* ---- SHAP Base Value ---- */}
      <p className="text-[11px] text-brand-muted text-center">
        SHAP base value:{" "}
        <span className="font-mono text-brand-subtext">{shap_base_value.toFixed(4)}</span>
      </p>

      {/* ---- Top 5 Impact Snapshot ---- */}
      <div>
        <p className="section-label">Top 5 Features by Risk Impact</p>
        <div className="flex flex-col gap-1.5">
          {top5.map((f) => (
            <div
              key={f.label}
              className="flex items-center justify-between gap-2 text-xs
                         bg-brand-bg rounded px-2 py-1.5 border border-brand-border"
            >
              <span className="text-brand-subtext truncate flex-1" title={f.label}>
                {f.label}
              </span>
              <span
                className={clsx(
                  "font-mono font-semibold shrink-0",
                  f.direction === "risk" ? "text-risk-high" : "text-risk-low"
                )}
              >
                {f.shap_value > 0 ? "+" : ""}
                {f.shap_value.toFixed(4)}
              </span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
