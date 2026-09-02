"use client";

// =============================================================================
// SHIELD — ShapChart Component  (v1.1 layout)
//
// Changes from v1.0:
//   • Absorbed the "Top 5 Impact Snapshot" table from RiskGauge — it now
//     lives here as a compact ranked list above the bar chart, giving a
//     single coherent SHAP section in the right-hand report column.
//   • Added compact/full toggle: compact shows top-5 bar chart (default in
//     the half-width column); full shows all 10 bars.
//   • Bar height reduced to 14px max; chart height is now purely data-driven
//     so it never over-expands in a constrained column.
//   • Y-axis label width reduced to 160px to fit narrower containers.
// =============================================================================

import { useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, Cell, ResponsiveContainer,
} from "recharts";
import clsx from "clsx";
import type { ShapFeature } from "@/lib/types";

interface Props {
  features: ShapFeature[];
  /** Number of bars shown in full mode (default 10). */
  maxDisplay?: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function truncateLabel(label: string, maxLen = 26): string {
  return label.length > maxLen ? label.slice(0, maxLen - 1) + "…" : label;
}

// ---------------------------------------------------------------------------
// Custom tooltip
// ---------------------------------------------------------------------------
function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ShapFeature }>;
}) {
  if (!active || !payload?.length) return null;
  const f = payload[0].payload;
  const isRisk = f.direction === "risk";

  return (
    <div className="bg-brand-panel border border-brand-border rounded-lg px-3 py-2.5
                    shadow-card text-xs max-w-[240px]">
      <p className="text-brand-text font-semibold mb-1 leading-snug">{f.label}</p>
      <div className="flex flex-col gap-0.5 text-brand-subtext">
        <span>
          Feature value:{" "}
          <span className="font-mono text-brand-text">{f.value.toFixed(6)}</span>
        </span>
        <span>
          SHAP:{" "}
          <span className="font-mono font-bold" style={{ color: isRisk ? "#ef4444" : "#22c55e" }}>
            {f.shap_value > 0 ? "+" : ""}{f.shap_value.toFixed(6)}
          </span>
        </span>
        <span className={isRisk ? "text-risk-high" : "text-risk-low"}>
          {isRisk ? "↑ Increases default risk" : "↓ Reduces default risk"}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export default function ShapChart({ features, maxDisplay = 10 }: Props) {
  const [expanded, setExpanded] = useState(false);

  const visibleCount = expanded ? maxDisplay : 5;

  // Top N by absolute SHAP value
  const allSorted = useMemo(
    () =>
      [...features]
        .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
        .slice(0, maxDisplay),
    [features, maxDisplay]
  );

  // Top 5 ranked list (always shown)
  const top5 = allSorted.slice(0, 5);

  // Chart data — reversed so highest impact sits at the bottom (SHAP convention)
  const chartData = useMemo(
    () =>
      allSorted
        .slice(0, visibleCount)
        .map((f) => ({ ...f, shortLabel: truncateLabel(f.label) }))
        .reverse(),
    [allSorted, visibleCount]
  );

  const domain = useMemo(() => {
    const abs = Math.max(...chartData.map((f) => Math.abs(f.shap_value)));
    const pad = abs * 0.18;
    return [-(abs + pad), abs + pad] as [number, number];
  }, [chartData]);

  // 14px bar + 6px gap per row + 24px axis
  const chartHeight = chartData.length * 20 + 24;

  return (
    <div className="flex flex-col gap-4">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <p className="section-label mb-0">SHAP Feature Impact</p>
        <span className="text-[10px] text-brand-muted">
          <span className="text-risk-high font-semibold">Red</span> = risk ·{" "}
          <span className="text-risk-low font-semibold">Green</span> = protective
        </span>
      </div>

      {/* ── Top-5 ranked snapshot ───────────────────────────────────────────
          Compact table: rank | label | signed SHAP | mini bar
      ─────────────────────────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-0 rounded-lg border border-brand-border overflow-hidden">
        {top5.map((f, i) => {
          const isRisk = f.direction === "risk";
          const barWidth = Math.round((Math.abs(f.shap_value) /
            Math.abs(allSorted[0].shap_value)) * 100);

          return (
            <div
              key={f.label}
              className={clsx(
                "flex items-center gap-2 px-3 py-1.5 text-xs",
                "border-b border-brand-border/60 last:border-0",
                i % 2 === 0 ? "bg-brand-panel" : "bg-brand-bg"
              )}
            >
              {/* Rank */}
              <span className="shrink-0 text-[10px] font-bold text-brand-subtext w-4 text-center">
                {i + 1}
              </span>

              {/* Label */}
              <span
                className="flex-1 text-brand-subtext truncate text-[0.68rem]"
                title={f.label}
              >
                {f.label}
              </span>

              {/* Mini bar */}
              <div className="shrink-0 w-14 h-1.5 rounded-full bg-brand-border overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${barWidth}%`,
                    background: isRisk ? "#ef4444" : "#22c55e",
                    opacity: 0.8,
                  }}
                />
              </div>

              {/* SHAP value */}
              <span
                className={clsx(
                  "shrink-0 font-mono text-[0.68rem] font-bold tabular-nums w-14 text-right",
                  isRisk ? "text-risk-high" : "text-risk-low"
                )}
              >
                {f.shap_value > 0 ? "+" : ""}{f.shap_value.toFixed(4)}
              </span>
            </div>
          );
        })}
      </div>

      {/* ── Bar chart ──────────────────────────────────────────────────────── */}
      <div>
        <p className="text-[10px] text-brand-muted mb-2 flex items-center justify-between">
          <span>Top {visibleCount} contributions (chart)</span>
          {maxDisplay > 5 && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="text-brand-yellow hover:text-brand-yellowHover
                         font-semibold transition-colors"
            >
              {expanded ? `Show top 5` : `Show all ${maxDisplay}`}
            </button>
          )}
        </p>

        <ResponsiveContainer width="100%" height={chartHeight}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 0, right: 44, bottom: 0, left: 4 }}
          >
            <CartesianGrid
              horizontal={false}
              strokeDasharray="3 3"
              stroke="#E8E4DE"
            />

            <XAxis
              type="number"
              domain={domain}
              tick={{ fill: "#9ca3af", fontSize: 9, fontFamily: "JetBrains Mono, monospace" }}
              tickLine={false}
              axisLine={{ stroke: "#E8E4DE" }}
              tickFormatter={(v: number) => v.toFixed(2)}
            />

            <YAxis
              type="category"
              dataKey="shortLabel"
              width={160}
              tick={{ fill: "#9ca3af", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />

            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: "rgba(0,0,0,0.03)" }}
            />

            <ReferenceLine x={0} stroke="#D4CFC8" strokeWidth={1.5} />

            <Bar dataKey="shap_value" radius={[0, 3, 3, 0]} maxBarSize={14}>
              {chartData.map((entry, idx) => (
                <Cell
                  key={idx}
                  fill={entry.direction === "risk" ? "#ef4444" : "#22c55e"}
                  fillOpacity={0.82}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}
