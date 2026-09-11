"use client";

// =============================================================================
// SHIELD — Evaluation Logs Page  (/logs)
//
// v2 additions:
//   • Search bar     — filters by company name or SSM number (case-insensitive)
//   • Risk filter    — All / High Risk / Low Risk dropdown
//   • Evaluator filter — All / per-officer dropdown (dynamic from data)
//   • Column sorting — click any column header to sort asc/desc
//   • Results count  — "Showing X of Y" live feedback
//
// Each row owns its own contentRef + useReactToPrint hook so the Download PDF
// button can be called without violating React hook rules.
// =============================================================================

import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useReactToPrint } from "react-to-print";
import {
  RefreshCw, AlertTriangle, CheckCircle,
  Calendar, Building2, Hash, DollarSign,
  User, ChevronDown, ChevronUp, Loader2,
  ClipboardList, ServerOff, Download,
  Search, X, ChevronsUpDown, ArrowUp, ArrowDown,
  Filter,
} from "lucide-react";
import clsx from "clsx";

import { fetchLogs } from "@/lib/api";
import type { LogEntry } from "@/lib/types";
import ReportTemplate from "@/components/ReportTemplate";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type SortKey = "evaluated_at" | "company_name" | "loan_amount" | "probability_default";
type SortDir = "asc" | "desc";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const currencyFmt = new Intl.NumberFormat("en-MY", {
  style: "currency",
  currency: "MYR",
  maximumFractionDigits: 0,
});

function formatDate(iso: string) {
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString("en-MY", { day: "2-digit", month: "short", year: "numeric" }),
    time: d.toLocaleTimeString("en-MY", { hour: "2-digit", minute: "2-digit", hour12: true }),
  };
}

// ---------------------------------------------------------------------------
// Risk badge
// ---------------------------------------------------------------------------
function RiskBadge({ classification }: { classification: LogEntry["risk_classification"] }) {
  const isHigh = classification === "High Risk";
  return (
    <span className={clsx(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.68rem] font-semibold border",
      isHigh
        ? "text-risk-high bg-risk-highBg border-risk-high/30"
        : "text-risk-low  bg-risk-lowBg  border-risk-low/30"
    )}>
      {isHigh ? <AlertTriangle size={9} /> : <CheckCircle size={9} />}
      {classification}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Sort icon
// ---------------------------------------------------------------------------
function SortIcon({ col, sortKey, sortDir }: {
  col: SortKey; sortKey: SortKey; sortDir: SortDir;
}) {
  if (col !== sortKey) return <ChevronsUpDown size={10} className="text-brand-border" />;
  return sortDir === "asc"
    ? <ArrowUp size={10} className="text-brand-charcoal" />
    : <ArrowDown size={10} className="text-brand-charcoal" />;
}

// ---------------------------------------------------------------------------
// Detail drawer
// ---------------------------------------------------------------------------
function DetailDrawer({ entry }: { entry: LogEntry }) {
  const topDrivers = entry.shap_breakdown
    .slice()
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, 5);

  return (
    <tr>
      <td colSpan={8} className="px-0 pb-0">
        <div className="mx-4 mb-4 rounded-lg border border-brand-border bg-brand-bg
                        overflow-hidden animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-0 divide-y md:divide-y-0 md:divide-x divide-brand-border">

            {/* Advisory text */}
            <div className="px-4 py-3">
              <p className="text-[10px] uppercase tracking-widest font-bold text-brand-muted mb-2">
                Advisory Summary
              </p>
              <p className="text-xs text-brand-subtext leading-relaxed whitespace-pre-line">
                {entry.advisory_report}
              </p>
            </div>

            {/* Top SHAP drivers */}
            <div className="px-4 py-3">
              <p className="text-[10px] uppercase tracking-widest font-bold text-brand-muted mb-2">
                Top 5 SHAP Drivers
              </p>
              <div className="flex flex-col gap-1.5">
                {topDrivers.map((f) => (
                  <div key={f.label} className="flex items-center justify-between gap-2 text-xs">
                    <span className="text-brand-subtext truncate flex-1" title={f.label}>
                      {f.label}
                    </span>
                    <span className={clsx(
                      "font-mono font-bold shrink-0 tabular-nums",
                      f.direction === "risk" ? "text-risk-high" : "text-risk-low"
                    )}>
                      {f.shap_value > 0 ? "+" : ""}{f.shap_value.toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Log row
// ---------------------------------------------------------------------------
function LogRow({ entry }: { entry: LogEntry }) {
  const [expanded, setExpanded] = useState(false);
  const { date, time } = formatDate(entry.evaluated_at);
  const reportRef = useRef<HTMLDivElement>(null);

  const handlePrint = useReactToPrint({
    contentRef: reportRef,
    documentTitle: `SHIELD_Report_${entry.company_name.replace(/\s+/g, "_")}_${entry.id}`,
    fonts: [
      { family: "Ubuntu", source: "https://fonts.gstatic.com/s/ubuntu/v20/4iCs6KVjbNBYlgoKfw72.woff2", weight: "700" },
      { family: "Lato", source: "https://fonts.gstatic.com/s/lato/v24/S6uyw4BMUTPHjx4wXiWtFCc.woff2", weight: "400" },
      { family: "Lato", source: "https://fonts.gstatic.com/s/lato/v24/S6u9w4BMUTPHh6UVSwiPGQ3q5d0.woff2", weight: "700" },
    ],
  });

  return (
    <>
      <tr style={{ display: "none" }}>
        <td><ReportTemplate ref={reportRef} log={entry} /></td>
      </tr>

      <tr
        className={clsx(
          "border-b border-brand-border/60 hover:bg-brand-bg/60 transition-colors cursor-pointer",
          expanded && "bg-brand-bg/60"
        )}
        onClick={() => setExpanded((v) => !v)}
      >
        {/* Date */}
        <td className="px-4 py-3 whitespace-nowrap">
          <p className="text-xs font-semibold text-brand-charcoal">{date}</p>
          <p className="text-[10px] text-brand-muted">{time}</p>
        </td>

        {/* Company */}
        <td className="px-4 py-3 min-w-[160px]">
          <p className="text-sm font-semibold text-brand-charcoal leading-tight">
            {entry.company_name}
          </p>
        </td>

        {/* SSM */}
        <td className="px-4 py-3 whitespace-nowrap">
          <span className="font-mono text-xs text-brand-subtext">{entry.ssm_number}</span>
        </td>

        {/* Loan Amount */}
        <td className="px-4 py-3 whitespace-nowrap text-right">
          <span className="text-sm font-semibold text-brand-charcoal tabular-nums">
            {currencyFmt.format(entry.loan_amount)}
          </span>
        </td>

        {/* Risk */}
        <td className="px-4 py-3">
          <RiskBadge classification={entry.risk_classification} />
        </td>

        {/* P(Default) */}
        <td className="px-4 py-3 whitespace-nowrap text-right">
          <span className={clsx(
            "font-mono text-sm font-bold tabular-nums",
            entry.risk_classification === "High Risk" ? "text-risk-high" : "text-risk-low"
          )}>
            {(entry.probability_default * 100).toFixed(2)}%
          </span>
        </td>

        {/* Evaluator */}
        <td className="px-4 py-3 whitespace-nowrap">
          <span className="text-xs text-brand-subtext">{entry.evaluator}</span>
        </td>

        {/* Actions */}
        <td className="px-4 py-3 whitespace-nowrap">
          <div className="flex items-center justify-end gap-1">
            <button
              onClick={(e) => { e.stopPropagation(); handlePrint(); }}
              className="flex items-center gap-1.5 text-xs font-semibold
                         text-brand-charcoal bg-brand-yellow hover:bg-brand-yellowHover
                         transition-colors duration-150 px-2.5 py-1.5 rounded-lg shadow-sm"
              title="Download PDF"
            >
              <Download size={12} /> PDF
            </button>
            <button
              className="text-brand-muted hover:text-brand-charcoal transition-colors p-1.5 rounded-lg
                         border border-brand-border hover:border-brand-charcoal/30"
              onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v); }}
            >
              {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
          </div>
        </td>
      </tr>

      {expanded && <DetailDrawer entry={entry} />}
    </>
  );
}

// ---------------------------------------------------------------------------
// Sortable column header
// ---------------------------------------------------------------------------
function ColHeader({
  label, icon: Icon, sortKey, activeKey, activeDir, onSort, align = "left",
}: {
  label: string;
  icon?: React.ElementType;
  sortKey?: SortKey;
  activeKey: SortKey;
  activeDir: SortDir;
  onSort: (k: SortKey) => void;
  align?: "left" | "right";
}) {
  const sortable = !!sortKey;
  return (
    <th
      className={clsx(
        "px-4 py-2.5 text-[10px] font-bold uppercase tracking-widest text-brand-muted",
        "select-none whitespace-nowrap",
        sortable && "cursor-pointer hover:text-brand-charcoal transition-colors",
        align === "right" && "text-right"
      )}
      onClick={sortable ? () => onSort(sortKey!) : undefined}
    >
      <span className={clsx("inline-flex items-center gap-1.5", align === "right" && "justify-end w-full")}>
        {Icon && <Icon size={10} />}
        {label}
        {sortable && (
          <SortIcon col={sortKey!} sortKey={activeKey} sortDir={activeDir} />
        )}
      </span>
    </th>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ── Filter state ──────────────────────────────────────────────────────────
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState<"all" | "High Risk" | "Low Risk">("all");
  const [evaluatorFilter, setEvaluatorFilter] = useState<string>("all");

  // ── Sort state ────────────────────────────────────────────────────────────
  const [sortKey, setSortKey] = useState<SortKey>("evaluated_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  // ── Load ──────────────────────────────────────────────────────────────────
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLogs();
      setLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load logs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // ── Unique evaluators for dropdown ────────────────────────────────────────
  const evaluators = useMemo(
    () => ["all", ...Array.from(new Set(logs.map((l) => l.evaluator))).sort()],
    [logs]
  );

  // ── Sort handler ─────────────────────────────────────────────────────────
  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  // ── Filtered + sorted rows ────────────────────────────────────────────────
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return logs
      .filter((l) => {
        if (riskFilter !== "all" && l.risk_classification !== riskFilter) return false;
        if (evaluatorFilter !== "all" && l.evaluator !== evaluatorFilter) return false;
        if (q && !l.company_name.toLowerCase().includes(q) && !l.ssm_number.toLowerCase().includes(q)) return false;
        return true;
      })
      .sort((a, b) => {
        let av: number | string;
        let bv: number | string;
        switch (sortKey) {
          case "evaluated_at": av = a.evaluated_at; bv = b.evaluated_at; break;
          case "company_name": av = a.company_name; bv = b.company_name; break;
          case "loan_amount": av = a.loan_amount; bv = b.loan_amount; break;
          case "probability_default": av = a.probability_default; bv = b.probability_default; break;
          default: av = a.evaluated_at; bv = b.evaluated_at;
        }
        if (av < bv) return sortDir === "asc" ? -1 : 1;
        if (av > bv) return sortDir === "asc" ? 1 : -1;
        return 0;
      });
  }, [logs, search, riskFilter, evaluatorFilter, sortKey, sortDir]);

  const hasActiveFilters = search !== "" || riskFilter !== "all" || evaluatorFilter !== "all";

  function clearFilters() {
    setSearch("");
    setRiskFilter("all");
    setEvaluatorFilter("all");
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-brand-cream">
      <div className="relative z-10 flex flex-col min-h-screen">

        {/* ── Page header ───────────────────────────────────────────────── */}
        <div className="px-6 pt-6 pb-4 flex items-start justify-between border-b border-brand-border/60">
          <div>
            <p className="section-label">Audit Trail</p>
            <h1 className="text-2xl font-bold text-brand-charcoal font-heading">
              Evaluation Logs
            </h1>
            <p className="text-sm text-brand-muted mt-0.5">
              All past SME evaluations, newest first. Click a row to expand, or download a PDF report.
            </p>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="btn-ghost flex items-center gap-1.5 px-3 py-2 text-sm mt-1 shrink-0"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>

        {/* ── Main content ──────────────────────────────────────────────── */}
        <div className="flex-1 px-6 py-5 flex flex-col gap-4">

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-24 gap-3 text-brand-muted">
              <Loader2 size={22} className="animate-spin" />
              <span className="text-sm">Loading evaluations…</span>
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
              <div className="h-14 w-14 rounded-full bg-risk-highBg border border-risk-high/30
                              flex items-center justify-center">
                <ServerOff size={22} className="text-risk-high" />
              </div>
              <div>
                <p className="text-sm font-semibold text-brand-charcoal mb-1">Could not load logs</p>
                <p className="text-xs text-brand-muted max-w-sm">{error}</p>
                <p className="text-xs text-brand-subtext mt-1">
                  Make sure the backend is running and DATABASE_URL is configured.
                </p>
              </div>
              <button onClick={load} className="btn-ghost text-sm px-4 py-2">Try again</button>
            </div>
          )}

          {/* Empty — no data at all */}
          {!loading && !error && logs.length === 0 && (
            <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
              <div className="h-14 w-14 rounded-full bg-brand-panel border border-brand-border
                              flex items-center justify-center">
                <ClipboardList size={22} className="text-brand-muted" />
              </div>
              <div>
                <p className="text-sm font-semibold text-brand-charcoal mb-1">No evaluations yet</p>
                <p className="text-xs text-brand-muted">
                  Run your first SME evaluation from the dashboard to see it here.
                </p>
              </div>
            </div>
          )}

          {/* Search + filter toolbar + table */}
          {!loading && !error && logs.length > 0 && (
            <>
              {/* ── Toolbar ─────────────────────────────────────────────── */}
              <div className="flex flex-wrap items-center gap-3">

                {/* Search */}
                <div className="relative flex-1 min-w-[200px] max-w-sm">
                  <Search
                    size={13}
                    className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted"
                  />
                  <input
                    type="text"
                    placeholder="Search company or SSM…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="input-field pl-8 pr-8 text-sm h-9"
                  />
                  {search && (
                    <button
                      onClick={() => setSearch("")}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-brand-muted
                                 hover:text-brand-charcoal transition-colors"
                    >
                      <X size={13} />
                    </button>
                  )}
                </div>

                {/* Risk filter */}
                <div className="relative">
                  <Filter
                    size={12}
                    className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted"
                  />
                  <select
                    value={riskFilter}
                    onChange={(e) => setRiskFilter(e.target.value as typeof riskFilter)}
                    className="input-field pl-8 pr-7 text-sm h-9 appearance-none cursor-pointer min-w-[140px]"
                  >
                    <option value="all">All Risk Levels</option>
                    <option value="High Risk">High Risk</option>
                    <option value="Low Risk">Low Risk</option>
                  </select>
                  <ChevronDown
                    size={12}
                    className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-brand-muted"
                  />
                </div>

                {/* Evaluator filter */}
                <div className="relative">
                  <User
                    size={12}
                    className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted"
                  />
                  <select
                    value={evaluatorFilter}
                    onChange={(e) => setEvaluatorFilter(e.target.value)}
                    className="input-field pl-8 pr-7 text-sm h-9 appearance-none cursor-pointer min-w-[150px]"
                  >
                    {evaluators.map((e) => (
                      <option key={e} value={e}>
                        {e === "all" ? "All Evaluators" : e}
                      </option>
                    ))}
                  </select>
                  <ChevronDown
                    size={12}
                    className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-brand-muted"
                  />
                </div>

                {/* Clear filters */}
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="btn-ghost flex items-center gap-1.5 px-3 h-9 text-sm"
                  >
                    <X size={12} />
                    Clear
                  </button>
                )}

                {/* Results count — pushed to right */}
                <div className="ml-auto text-xs text-brand-muted shrink-0">
                  Showing{" "}
                  <span className="font-semibold text-brand-charcoal font-mono">
                    {filtered.length}
                  </span>
                  {filtered.length !== logs.length && (
                    <> of <span className="font-semibold text-brand-charcoal font-mono">{logs.length}</span></>
                  )}{" "}
                  evaluation{filtered.length !== 1 ? "s" : ""}
                </div>
              </div>

              {/* ── Table ───────────────────────────────────────────────── */}
              <div className="panel overflow-hidden">

                {/* No results after filtering */}
                {filtered.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
                    <Search size={22} className="text-brand-muted" />
                    <div>
                      <p className="text-sm font-semibold text-brand-charcoal mb-1">
                        No results match your filters
                      </p>
                      <p className="text-xs text-brand-muted">
                        Try adjusting your search or clearing the filters.
                      </p>
                    </div>
                    <button onClick={clearFilters} className="btn-ghost text-sm px-4 py-2">
                      Clear filters
                    </button>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left min-w-[800px]">
                      <thead>
                        <tr className="border-b border-brand-border bg-brand-bg/50">
                          <ColHeader
                            label="Date & Time" icon={Calendar}
                            sortKey="evaluated_at"
                            activeKey={sortKey} activeDir={sortDir} onSort={handleSort}
                          />
                          <ColHeader
                            label="Company" icon={Building2}
                            sortKey="company_name"
                            activeKey={sortKey} activeDir={sortDir} onSort={handleSort}
                          />
                          <ColHeader
                            label="SSM No." icon={Hash}
                            activeKey={sortKey} activeDir={sortDir} onSort={handleSort}
                          />
                          <ColHeader
                            label="Loan Amount" icon={DollarSign}
                            sortKey="loan_amount"
                            activeKey={sortKey} activeDir={sortDir} onSort={handleSort}
                            align="right"
                          />
                          <ColHeader
                            label="Risk"
                            activeKey={sortKey} activeDir={sortDir} onSort={handleSort}
                          />
                          <ColHeader
                            label="P(Default)"
                            sortKey="probability_default"
                            activeKey={sortKey} activeDir={sortDir} onSort={handleSort}
                            align="right"
                          />
                          <ColHeader
                            label="Evaluator" icon={User}
                            activeKey={sortKey} activeDir={sortDir} onSort={handleSort}
                          />
                          {/* Actions — not sortable */}
                          <th className="px-4 py-2.5 text-[10px] font-bold uppercase tracking-widest
                                         text-brand-muted text-right">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((entry) => (
                          <LogRow key={entry.id} entry={entry} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}

        </div>

        {/* ── Footer ──────────────────────────────────────────────────────── */}
        <footer className="border-t border-brand-border px-6 py-3 flex items-center
                           justify-between text-brand-muted text-xs mt-auto">
          <span>SHIELD · Final Year Project · For academic use only</span>
          <span>JuneBank Internal Tools · XGBoost + SHAP</span>
        </footer>

      </div>
    </div>
  );
}
