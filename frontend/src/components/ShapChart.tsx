"use client";

// =============================================================================
// SHIELD — ShapChart Component
// Horizontal bar chart showing SHAP contributions for the top N features.
// Risk-increasing bars are red; protective bars are green.
// Uses Recharts BarChart in layout="vertical" (waterfall-style).
// =============================================================================

import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
  ResponsiveContainer,
} from "recharts";
import type { ShapFeature } from "@/lib/types";

interface Props {
  features: ShapFeature[];
  maxDisplay?: number;
}

// Truncate long labels for the Y axis
function truncateLabel(label: string, maxLen = 28): string {
  return label.length > maxLen ? label.slice(0, maxLen - 1) + "…" : label;
}

// Custom tooltip
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
    <div
      className="bg-brand-panel border border-brand-border rounded-lg px-3 py-2.5
                 shadow-panel text-xs max-w-[260px]"
    >
      <p className="text-brand-text font-semibold mb-1 leading-snug">{f.label}</p>
      <div className="flex flex-col gap-0.5 text-brand-subtext">
        <span>
          Feature value:{" "}
          <span className="font-mono text-brand-text">{f.value.toFixed(6)}</span>
        </span>
        <span>
          SHAP contribution:{" "}
          <span
            className="font-mono font-bold"
            style={{ color: isRisk ? "#ef4444" : "#22c55e" }}
          >
            {f.shap_value > 0 ? "+" : ""}
            {f.shap_value.toFixed(6)}
          </span>
        </span>
        <span className={isRisk ? "text-risk-high" : "text-risk-low"}>
          {isRisk ? "↑ Increases default risk" : "↓ Reduces default risk"}
        </span>
      </div>
    </div>
  );
}

export default function ShapChart({ features, maxDisplay = 10 }: Props) {
  // Take top N by absolute SHAP value
  const chartData = useMemo(() => {
    return [...features]
      .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
      .slice(0, maxDisplay)
      .map((f) => ({ ...f, shortLabel: truncateLabel(f.label) }))
      .reverse(); // bottom of chart = highest impact (matches SHAP waterfall convention)
  }, [features, maxDisplay]);

  const domain = useMemo(() => {
    const vals = chartData.map((f) => f.shap_value);
    const abs   = Math.max(...vals.map(Math.abs));
    const pad   = abs * 0.18;
    return [-(abs + pad), abs + pad] as [number, number];
  }, [chartData]);

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <p className="section-label mb-0">SHAP Feature Contributions (Top {maxDisplay})</p>
      </div>
      <p className="text-[11px] text-brand-muted mb-3">
        <span className="text-risk-high font-semibold">Red</span> bars push toward default ·{" "}
        <span className="text-risk-low font-semibold">Green</span> bars push toward health
      </p>

      <ResponsiveContainer width="100%" height={chartData.length * 34 + 32}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 0, right: 48, bottom: 0, left: 8 }}
        >
          <CartesianGrid
            horizontal={false}
            strokeDasharray="3 3"
            stroke="#2a2d36"
          />

          <XAxis
            type="number"
            domain={domain}
            tick={{ fill: "#6b7280", fontSize: 10, fontFamily: "JetBrains Mono, monospace" }}
            tickLine={false}
            axisLine={{ stroke: "#2a2d36" }}
            tickFormatter={(v: number) => v.toFixed(3)}
          />

          <YAxis
            type="category"
            dataKey="shortLabel"
            width={180}
            tick={{ fill: "#9ca3af", fontSize: 10.5 }}
            tickLine={false}
            axisLine={false}
          />

          <Tooltip
            content={<CustomTooltip />}
            cursor={{ fill: "rgba(255,255,255,0.03)" }}
          />

          {/* Zero reference line */}
          <ReferenceLine
            x={0}
            stroke="#3a3d46"
            strokeWidth={1.5}
          />

          <Bar dataKey="shap_value" radius={[0, 3, 3, 0]} maxBarSize={18}>
            {chartData.map((entry, idx) => (
              <Cell
                key={idx}
                fill={entry.direction === "risk" ? "#ef4444" : "#22c55e"}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
