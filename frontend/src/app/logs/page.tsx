"use client";

// =============================================================================
// SHIELD — Evaluation Logs Page  (/logs)
//
// Each row owns its own contentRef + useReactToPrint hook so the Download PDF
// button can be called without violating React hook rules.
// ReportTemplate is rendered hidden (print-only CSS class) inside each LogRow
// and shown only when the browser print dialog fires.
// =============================================================================

import { useEffect, useState, useCallback, useRef } from "react";
import { useReactToPrint } from "react-to-print";
import {
  RefreshCw, AlertTriangle, CheckCircle,
  Calendar, Building2, Hash, DollarSign,
  User, ChevronDown, ChevronUp, Loader2,
  ClipboardList, ServerOff, Download,
} from "lucide-react";
import clsx from "clsx";

import { fetchLogs } from "@/lib/api";
import type { LogEntry } from "@/lib/types";
import ReportTemplate from "@/components/ReportTemplate";

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
// Log row — owns its own ref + print hook so hooks are not called conditionally
// ---------------------------------------------------------------------------
function LogRow({ entry }: { entry: LogEntry }) {
  const [expanded, setExpanded] = useState(false);
  const { date, time } = formatDate(entry.evaluated_at);

  const reportRef = useRef<HTMLDivElement>(null);

  const handlePrint = useReactToPrint({
    contentRef: reportRef,
    documentTitle: `SHIELD_Report_${entry.company_name.replace(/\s+/g, "_")}_${entry.id}`,
    fonts: [
      {
        family: "Ubuntu",
        source: "https://fonts.gstatic.com/s/ubuntu/v20/4iCs6KVjbNBYlgoKfw72.woff2",
        weight: "700",
      },
      {
        family: "Lato",
        source: "https://fonts.gstatic.com/s/lato/v24/S6uyw4BMUTPHjx4wXiWtFCc.woff2",
        weight: "400",
      },
      {
        family: "Lato",
        source: "https://fonts.gstatic.com/s/lato/v24/S6u9w4BMUTPHh6UVSwiPGQ3q5d0.woff2",
        weight: "700",
      },
    ],
  });

  return (
    <>
      {/*
        ReportTemplate CANNOT be a sibling of <tr> inside <tbody> — the browser
        silently drops nodes that violate table structure, so the ref stays null.
        Instead we portal it outside the table entirely using a <td>-free div
        that lives before the table row fragment. We use a zero-size absolutely
        positioned wrapper so it takes no layout space but IS in the DOM.
        react-to-print reads the ref'd node from there.
      */}
      <tr style={{ display: "none" }}>
        <td>
          <ReportTemplate ref={reportRef} log={entry} />
        </td>
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

            {/* Download PDF */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                handlePrint();
              }}
              className="flex items-center gap-1.5 text-xs font-semibold
                         text-brand-charcoal bg-brand-yellow hover:bg-brand-yellowHover
                         transition-colors duration-150 px-2.5 py-1.5 rounded-lg shadow-sm"
              aria-label="Download PDF report"
              title="Download PDF"
            >
              <Download size={12} />
              PDF
            </button>

            {/* Expand toggle */}
            <button
              className="text-brand-muted hover:text-brand-charcoal transition-colors p-1.5 rounded-lg
                         border border-brand-border hover:border-brand-charcoal/30"
              aria-label={expanded ? "Collapse details" : "Expand details"}
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
// Page
// ---------------------------------------------------------------------------
export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="min-h-screen bg-brand-cream">
      <div className="relative z-10 flex flex-col min-h-screen">

        {/* ── Page header ───────────────────────────────────────────────── */}
        <div className="px-6 pt-6 pb-4 flex items-center justify-between">
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
            className="btn-ghost flex items-center gap-1.5 px-3 py-2 text-sm"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>

        {/* ── Main content ──────────────────────────────────────────────── */}
        <div className="flex-1 px-6 pb-6">

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

          {/* Empty state */}
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

          {/* Table */}
          {!loading && !error && logs.length > 0 && (
            <div className="panel overflow-hidden">

              {/* Table meta bar */}
              <div className="px-4 py-3 border-b border-brand-border flex items-center justify-between">
                <p className="text-xs text-brand-muted">
                  <span className="font-semibold text-brand-charcoal">{logs.length}</span>{" "}
                  evaluation{logs.length !== 1 ? "s" : ""} on record
                </p>
                <div className="flex items-center gap-3 text-[10px] text-brand-muted">
                  <span className="flex items-center gap-1">
                    <AlertTriangle size={9} className="text-risk-high" /> High Risk
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle size={9} className="text-risk-low" /> Low Risk
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left min-w-[800px]">
                  <thead>
                    <tr className="border-b border-brand-border bg-brand-bg/50">
                      {[
                        { Icon: Calendar, label: "Date & Time" },
                        { Icon: Building2, label: "Company" },
                        { Icon: Hash, label: "SSM No." },
                        { Icon: DollarSign, label: "Loan Amount" },
                        { Icon: null, label: "Risk" },
                        { Icon: null, label: "P(Default)" },
                        { Icon: User, label: "Evaluator" },
                        { Icon: null, label: "Actions" },
                      ].map(({ Icon, label }, i) => (
                        <th
                          key={i}
                          className={clsx(
                            "px-4 py-2.5 text-[10px] font-bold uppercase tracking-widest text-brand-muted",
                            (i === 3 || i === 5) && "text-right",
                            i === 7 && "text-right"
                          )}
                        >
                          <span className="flex items-center gap-1.5">
                            {Icon && <Icon size={10} />}
                            {label}
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {logs.map((entry) => (
                      <LogRow key={entry.id} entry={entry} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>

        {/* ── Footer ──────────────────────────────────────────────────────── */}
        <footer className="border-t border-brand-border px-6 py-3 flex items-center
                           justify-between text-brand-muted text-xs">
          <span>SHIELD · Final Year Project · For academic use only</span>
          <span>JuneBank Internal Tools · XGBoost + SHAP</span>
        </footer>

      </div>
    </div>
  );
}
