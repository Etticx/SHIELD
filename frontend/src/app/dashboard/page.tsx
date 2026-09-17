"use client";

// =============================================================================
// SHIELD — Personal Analytics Dashboard  (/dashboard)
//
// Shows the logged-in Loan Officer's own pipeline statistics, filtered from
// the shared evaluation log by `log.evaluator === user.username`.
//
// Sections:
//   1. Page Header
//   2. KPI Ribbon (4 cards)
//   3. Analytics Grid — Risk Distribution Donut + Evaluation Volume Bar Chart
//   4. Recent Pipeline — last 5 evaluations (dense table)
// =============================================================================

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useReactToPrint } from "react-to-print";
import AnalyticsReportTemplate from "@/components/AnalyticsReportTemplate";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  RefreshCw,
  Loader2,
  ServerOff,
  ClipboardList,
  DollarSign,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Flame,
  Building2,
  Hash,
  Download,
} from "lucide-react";
import clsx from "clsx";

import { fetchLogs } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { LogEntry } from "@/lib/types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Risk-semantic palette for donut segments
const DONUT_COLORS: Record<string, string> = {
  "Low Risk": "#16A34A",   // green
  "Moderate Risk": "#CA8A04",   // yellow
  "High Risk": "#D97706",   // amber
  "Critical Risk": "#DC2626",   // red
};

const CHARCOAL = "#1A1A1A";
const BORDER = "#E8E4DE";
const MUTED = "#6B6B6B";
const SUBTEXT = "#9A9A9A";

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------
const currencyFmt = new Intl.NumberFormat("en-MY", {
  style: "currency",
  currency: "MYR",
  maximumFractionDigits: 0,
});

function formatDateShort(iso: string): string {
  return new Date(iso).toLocaleDateString("en-MY", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

/** Returns "DD MMM" for bar chart axis labels. */
function formatAxisDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-MY", {
    day: "2-digit",
    month: "short",
  });
}

// ---------------------------------------------------------------------------
// Derived data helpers
// ---------------------------------------------------------------------------

/** Collapse logs into last N active calendar days (days that have ≥1 entry). */
function buildVolumeData(logs: LogEntry[], maxDays = 7) {
  const counts: Record<string, number> = {};
  for (const log of logs) {
    const day = log.evaluated_at.slice(0, 10); // "YYYY-MM-DD"
    counts[day] = (counts[day] ?? 0) + 1;
  }
  // Sort by date desc, take last N active days, then reverse to ascending
  const sorted = Object.entries(counts)
    .sort(([a], [b]) => b.localeCompare(a))
    .slice(0, maxDays)
    .reverse();

  return sorted.map(([date, count]) => ({
    date,
    label: formatAxisDate(date),
    count,
  }));
}

function buildDonutData(logs: LogEntry[]) {
  const counts: Record<string, number> = {
    "Low Risk": 0, "Moderate Risk": 0, "High Risk": 0, "Critical Risk": 0,
  };
  for (const log of logs) counts[log.risk_classification] = (counts[log.risk_classification] ?? 0) + 1;
  return Object.entries(counts)
    .map(([name, value]) => ({ name, value }))
    .filter((d) => d.value > 0);
}

// ---------------------------------------------------------------------------
// Custom Tooltip for Bar Chart
// ---------------------------------------------------------------------------
function BarTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="bg-brand-panel border border-brand-border rounded-md px-3 py-2 shadow-panel"
      style={{ fontSize: "0.72rem" }}
    >
      <p className="text-brand-muted font-semibold mb-0.5 uppercase tracking-widest">
        {label}
      </p>
      <p className="font-mono font-bold text-brand-charcoal">
        {payload[0].value}{" "}
        <span className="font-sans font-normal text-brand-muted">
          evaluation{payload[0].value !== 1 ? "s" : ""}
        </span>
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom Tooltip for Donut Chart
// ---------------------------------------------------------------------------
function DonutTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; payload: { pct: number } }>;
}) {
  if (!active || !payload?.length) return null;
  const { name, value, payload: extra } = payload[0];
  return (
    <div
      className="bg-brand-panel border border-brand-border rounded-md px-3 py-2 shadow-panel"
      style={{ fontSize: "0.72rem" }}
    >
      <p className="text-brand-muted font-semibold uppercase tracking-widest mb-0.5">{name}</p>
      <p className="font-mono font-bold text-brand-charcoal">
        {value}{" "}
        <span className="font-sans font-normal text-brand-muted">
          ({extra.pct.toFixed(1)}%)
        </span>
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom Legend for Donut
// ---------------------------------------------------------------------------
function DonutLegend({ data }: { data: Array<{ name: string; value: number; pct: number }> }) {
  return (
    <div className="flex flex-col gap-2 mt-4">
      {data.map((d) => (
        <div key={d.name} className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm shrink-0"
              style={{ backgroundColor: DONUT_COLORS[d.name] ?? MUTED }}
            />
            <span className="text-xs text-brand-muted">{d.name}</span>
          </div>
          <span className="font-mono text-xs font-semibold text-brand-charcoal tabular-nums">
            {d.value}{" "}
            <span className="text-brand-subtext font-normal">({d.pct.toFixed(1)}%)</span>
          </span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------
interface KpiCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  accentBar?: boolean;
}

function KpiCard({ icon, label, value, sub, accentBar }: KpiCardProps) {
  return (
    <div className="relative bg-brand-panel border border-brand-border rounded-md overflow-hidden">
      {accentBar && (
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-brand-yellow" />
      )}
      <div className="px-5 py-4 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <p className="text-[0.68rem] font-bold uppercase tracking-[0.13em] text-brand-muted">
            {label}
          </p>
          <span className="text-brand-subtext">{icon}</span>
        </div>
        <p className="font-mono text-2xl font-bold text-brand-charcoal leading-none tabular-nums">
          {value}
        </p>
        {sub && (
          <p className="text-[0.68rem] text-brand-subtext leading-snug">{sub}</p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Risk badge (table) — 4-tier colour coding
// ---------------------------------------------------------------------------
function RiskBadge({ classification }: { classification: LogEntry["risk_classification"] }) {
  const cfg = {
    "Low Risk": { Icon: ShieldCheck, cls: "text-[#166534] bg-[rgba(22,163,74,0.07)]  border-[rgba(22,163,74,0.25)]" },
    "Moderate Risk": { Icon: ShieldAlert, cls: "text-[#854D0E] bg-[rgba(202,138,4,0.07)]  border-[rgba(202,138,4,0.25)]" },
    "High Risk": { Icon: AlertTriangle, cls: "text-[#92400E] bg-[rgba(217,119,6,0.07)]  border-[rgba(217,119,6,0.25)]" },
    "Critical Risk": { Icon: Flame, cls: "text-[#991B1B] bg-[rgba(220,38,38,0.07)]  border-[rgba(220,38,38,0.25)]" },
  }[classification] ?? { Icon: ShieldCheck, cls: "text-[#166534] bg-[rgba(22,163,74,0.07)] border-[rgba(22,163,74,0.25)]" };

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-[0.65rem] font-bold",
        "border tracking-wide uppercase",
        cfg.cls,
      )}
    >
      <cfg.Icon size={8} />
      {classification}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Section wrapper
// ---------------------------------------------------------------------------
function Section({
  title,
  sub,
  children,
}: {
  title: string;
  sub?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-brand-panel border border-brand-border rounded-md overflow-hidden">
      <div className="px-5 pt-4 pb-3 border-b border-brand-border">
        <h2 className="text-sm font-bold text-brand-charcoal font-heading">{title}</h2>
        {sub && <p className="text-[0.68rem] text-brand-muted mt-0.5">{sub}</p>}
      </div>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty / loading / error states (reusable)
// ---------------------------------------------------------------------------
function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 gap-3 text-center">
      <div className="h-10 w-10 border border-brand-border rounded-md flex items-center justify-center">
        <ClipboardList size={16} className="text-brand-subtext" />
      </div>
      <p className="text-xs text-brand-muted max-w-[200px] leading-relaxed">{message}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function DashboardPage() {
  const { user } = useAuth();
  const [allLogs, setAllLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ── Print ref ─────────────────────────────────────────────────────────────
  const reportRef = useRef<HTMLDivElement>(null);
  const handleDownload = useReactToPrint({
    contentRef: reportRef,
    documentTitle: `SHIELD_Analytics_${user?.username ?? "officer"}_${new Date().toISOString().slice(0, 10)}`,
    pageStyle: `
      @page { size: A4 portrait; margin: 0; }
      @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
      }
    `,
  });

  // ── Fetch ──────────────────────────────────────────────────────────────────
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLogs();
      setAllLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // ── Filter to this officer's logs ─────────────────────────────────────────
  const logs = useMemo(
    () => allLogs.filter((l) => l.evaluator === user?.username),
    [allLogs, user]
  );

  // ── KPI calculations ──────────────────────────────────────────────────────
  const totalCount = logs.length;
  const totalVolume = useMemo(() => logs.reduce((s, l) => s + l.loan_amount, 0), [logs]);
  const highRiskLogs = useMemo(() => logs.filter((l) => l.risk_classification !== "Low Risk"), [logs]);
  const lowRiskLogs = useMemo(() => logs.filter((l) => l.risk_classification === "Low Risk"), [logs]);
  const highRiskPct = totalCount > 0 ? (highRiskLogs.length / totalCount) * 100 : 0;
  const lowRiskPct = totalCount > 0 ? (lowRiskLogs.length / totalCount) * 100 : 0;

  // ── Chart data ────────────────────────────────────────────────────────────
  const donutRaw = useMemo(() => buildDonutData(logs), [logs]);
  const donutData = useMemo(
    () =>
      donutRaw.map((d) => ({
        ...d,
        pct: totalCount > 0 ? (d.value / totalCount) * 100 : 0,
      })),
    [donutRaw, totalCount]
  );
  const volumeData = useMemo(() => buildVolumeData(logs, 7), [logs]);

  // ── Recent 5 ─────────────────────────────────────────────────────────────
  const recentLogs = useMemo(() => logs.slice(0, 5), [logs]);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-brand-cream">
      <div className="relative z-10 flex flex-col min-h-screen">

        {/* ── Page Header ──────────────────────────────────────────────────── */}
        <div className="px-6 pt-6 pb-5 flex items-start justify-between border-b border-brand-border/60">
          <div>
            <p className="section-label">Personal Analytics</p>
            <h1 className="text-2xl font-bold text-brand-charcoal font-heading leading-tight">
              My Analytics Overview
            </h1>
            <p className="text-sm text-brand-muted mt-1">
              Personal pipeline and risk distribution metrics
              {user?.username && (
                <>
                  {" "}for{" "}
                  <span className="font-semibold text-brand-charcoal font-mono">
                    {user.username}
                  </span>
                </>
              )}.
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 mt-1 shrink-0">
            <button
              onClick={load}
              disabled={loading}
              className="btn-ghost flex items-center gap-1.5 px-3 py-2 text-sm"
            >
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
              Refresh
            </button>

            <button
              onClick={() => handleDownload()}
              disabled={loading || totalCount === 0}
              className="btn-primary flex items-center gap-1.5 px-4 py-2 text-sm"
              title={totalCount === 0 ? "No data to export" : "Download your analytics as PDF"}
            >
              <Download size={13} />
              Download Report
            </button>
          </div>
        </div>

        {/* ── Main Body ────────────────────────────────────────────────────── */}
        <div className="flex-1 px-6 py-6 flex flex-col gap-6">

          {/* ── Loading ──────────────────────────────────────────────────── */}
          {loading && (
            <div className="flex items-center justify-center py-32 gap-3 text-brand-muted">
              <Loader2 size={20} className="animate-spin" />
              <span className="text-sm">Loading your pipeline data…</span>
            </div>
          )}

          {/* ── Error ────────────────────────────────────────────────────── */}
          {!loading && error && (
            <div className="flex flex-col items-center justify-center py-32 gap-4 text-center">
              <div className="h-12 w-12 border border-brand-border rounded-md flex items-center justify-center">
                <ServerOff size={18} className="text-brand-muted" />
              </div>
              <div>
                <p className="text-sm font-semibold text-brand-charcoal mb-1">
                  Could not load analytics
                </p>
                <p className="text-xs text-brand-muted max-w-sm">{error}</p>
              </div>
              <button onClick={load} className="btn-ghost text-sm px-4 py-2">
                Try again
              </button>
            </div>
          )}

          {/* ── Content ──────────────────────────────────────────────────── */}
          {!loading && !error && (
            <>
              {/* ── KPI Ribbon ───────────────────────────────────────────── */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">

                <KpiCard
                  accentBar
                  icon={<Building2 size={14} />}
                  label="Total SMEs Evaluated"
                  value={totalCount.toString()}
                  sub={
                    totalCount === 0
                      ? "No evaluations yet"
                      : `${totalCount} evaluation${totalCount !== 1 ? "s" : ""} on record`
                  }
                />

                <KpiCard
                  icon={<DollarSign size={14} />}
                  label="Total Volume Processed"
                  value={
                    totalVolume === 0
                      ? "RM 0"
                      : currencyFmt.format(totalVolume)
                  }
                  sub="Cumulative loan amounts evaluated"
                />

                <KpiCard
                  icon={<AlertTriangle size={14} />}
                  label="Distressed Rate"
                  value={totalCount > 0 ? `${highRiskPct.toFixed(1)}%` : "—"}
                  sub={
                    totalCount > 0
                      ? `${highRiskLogs.length} of ${totalCount} flagged as distressed`
                      : "No data"
                  }
                />

                <KpiCard
                  icon={<ShieldCheck size={14} />}
                  label="Healthy Rate"
                  value={totalCount > 0 ? `${lowRiskPct.toFixed(1)}%` : "—"}
                  sub={
                    totalCount > 0
                      ? `${lowRiskLogs.length} of ${totalCount} classified Low Risk`
                      : "No data"
                  }
                />

              </div>

              {/* ── Analytics Grid ───────────────────────────────────────── */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">

                {/* Left: Risk Distribution Donut */}
                <Section
                  title="Risk Distribution"
                  sub="Breakdown of your evaluations by risk classification"
                >
                  <div className="px-5 py-5">
                    {donutData.length === 0 ? (
                      <EmptyState message="No evaluations to chart yet. Complete your first evaluation to see data here." />
                    ) : (
                      <div className="flex flex-col sm:flex-row items-center gap-6">
                        <div className="w-full sm:w-[200px] h-[200px] shrink-0">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={donutData}
                                cx="50%"
                                cy="50%"
                                innerRadius={58}
                                outerRadius={84}
                                paddingAngle={3}
                                dataKey="value"
                                strokeWidth={0}
                              >
                                {donutData.map((entry) => (
                                  <Cell
                                    key={entry.name}
                                    fill={DONUT_COLORS[entry.name] ?? MUTED}
                                  />
                                ))}
                              </Pie>
                              <Tooltip content={<DonutTooltip />} />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>

                        <div className="flex-1 w-full">
                          {/* Centre stat */}
                          <div className="mb-4 border-b border-brand-border pb-4">
                            <p className="text-[0.68rem] uppercase tracking-widest text-brand-muted font-bold mb-1">
                              Total Evaluated
                            </p>
                            <p className="font-mono text-3xl font-bold text-brand-charcoal tabular-nums">
                              {totalCount}
                            </p>
                          </div>
                          <DonutLegend data={donutData} />
                        </div>
                      </div>
                    )}
                  </div>
                </Section>

                {/* Right: Evaluation Volume Bar Chart */}
                <Section
                  title="Evaluation Volume"
                  sub="Number of evaluations completed per day (last 7 active days)"
                >
                  <div className="px-5 py-5">
                    {volumeData.length === 0 ? (
                      <EmptyState message="No evaluation activity to chart yet." />
                    ) : (
                      <div className="h-[220px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={volumeData}
                            barCategoryGap="30%"
                            margin={{ top: 4, right: 8, left: -20, bottom: 0 }}
                          >
                            <CartesianGrid
                              vertical={false}
                              stroke={BORDER}
                              strokeDasharray="3 3"
                            />
                            <XAxis
                              dataKey="label"
                              tick={{
                                fontSize: 10,
                                fill: SUBTEXT,
                                fontFamily: "'JetBrains Mono', monospace",
                              }}
                              axisLine={{ stroke: BORDER }}
                              tickLine={false}
                            />
                            <YAxis
                              allowDecimals={false}
                              tick={{
                                fontSize: 10,
                                fill: SUBTEXT,
                                fontFamily: "'JetBrains Mono', monospace",
                              }}
                              axisLine={false}
                              tickLine={false}
                            />
                            <Tooltip
                              content={<BarTooltip />}
                              cursor={{ fill: "rgba(26,26,26,0.04)" }}
                            />
                            <Bar
                              dataKey="count"
                              fill={CHARCOAL}
                              radius={[2, 2, 0, 0]}
                              maxBarSize={40}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>
                </Section>

              </div>

              {/* ── Recent Pipeline ──────────────────────────────────────── */}
              <Section
                title="Recent Pipeline"
                sub="Your 5 most recent evaluations"
              >
                {recentLogs.length === 0 ? (
                  <div className="px-5">
                    <EmptyState message="No evaluations found for your account. Run your first SME evaluation to see it here." />
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[640px] text-left">
                      <thead>
                        <tr className="border-b border-brand-border bg-brand-cream/60">
                          {[
                            { label: "Date" },
                            { label: "Company Name" },
                            { label: "SSM No." },
                            { label: "Loan Amount", align: "right" as const },
                            { label: "Risk Classification" },
                          ].map(({ label, align }) => (
                            <th
                              key={label}
                              className={clsx(
                                "px-5 py-2.5 text-[0.65rem] font-bold uppercase",
                                "tracking-[0.12em] text-brand-muted whitespace-nowrap",
                                align === "right" && "text-right"
                              )}
                            >
                              {label}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {recentLogs.map((log, idx) => (
                          <tr
                            key={log.id}
                            className={clsx(
                              "border-b border-brand-border/70",
                              idx === recentLogs.length - 1 && "border-b-0"
                            )}
                          >
                            {/* Date */}
                            <td className="px-5 py-3 whitespace-nowrap">
                              <span className="font-mono text-xs text-brand-charcoal tabular-nums">
                                {formatDateShort(log.evaluated_at)}
                              </span>
                            </td>

                            {/* Company */}
                            <td className="px-5 py-3 min-w-[160px]">
                              <div className="flex items-center gap-2">
                                <Building2
                                  size={11}
                                  className="text-brand-subtext shrink-0"
                                />
                                <span className="text-sm font-semibold text-brand-charcoal leading-tight">
                                  {log.company_name}
                                </span>
                              </div>
                            </td>

                            {/* SSM */}
                            <td className="px-5 py-3 whitespace-nowrap">
                              <div className="flex items-center gap-1.5">
                                <Hash size={10} className="text-brand-subtext shrink-0" />
                                <span className="font-mono text-xs text-brand-muted">
                                  {log.ssm_number}
                                </span>
                              </div>
                            </td>

                            {/* Loan Amount */}
                            <td className="px-5 py-3 whitespace-nowrap text-right">
                              <span className="font-mono text-xs font-semibold text-brand-charcoal tabular-nums">
                                {currencyFmt.format(log.loan_amount)}
                              </span>
                            </td>

                            {/* Risk */}
                            <td className="px-5 py-3 whitespace-nowrap">
                              <RiskBadge classification={log.risk_classification} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Section>

            </>
          )}
        </div>

        {/* ── Footer ───────────────────────────────────────────────────────── */}
        <footer className="border-t border-brand-border px-6 py-3 flex items-center
                           justify-between text-brand-muted text-xs mt-auto">
          <span>SHIELD · Final Year Project · For academic use only</span>
          <span>JuneBank Internal Tools · Random Forest + SHAP</span>
        </footer>

        {/* ── Hidden print template — mounted in DOM for react-to-print ────── */}
        <div style={{ display: "none" }}>
          <AnalyticsReportTemplate
            ref={reportRef}
            username={user?.username ?? ""}
            generatedAt={new Date().toISOString()}
            totalCount={totalCount}
            totalVolume={totalVolume}
            highRiskCount={highRiskLogs.length}
            lowRiskCount={lowRiskLogs.length}
            recentLogs={recentLogs}
          />
        </div>

      </div>
    </div>
  );
}
