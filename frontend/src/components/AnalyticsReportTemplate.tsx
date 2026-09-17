// =============================================================================
// SHIELD — AnalyticsReportTemplate
//
// A4 print component for a Loan Officer's personal analytics summary.
// Follows the same design contract as ReportTemplate.tsx:
//   • All inline styles — immune to Tailwind purge inside the print iframe.
//   • JuneBank letterhead background image supplies header + footer branding.
//   • Monochrome / professional palette — no dashboard web colours.
//
// Rendered hidden in the DOM; react-to-print clones it into a print iframe.
// =============================================================================

import { forwardRef } from "react";
import type { LogEntry } from "@/lib/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface AnalyticsReportProps {
  username: string;
  generatedAt: string;          // ISO string
  totalCount: number;
  totalVolume: number;
  highRiskCount: number;
  lowRiskCount: number;
  recentLogs: LogEntry[];
}

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------
const currencyFmt = new Intl.NumberFormat("en-MY", {
  style: "currency",
  currency: "MYR",
  maximumFractionDigits: 0,
});

function formatDateLong(iso: string): string {
  return new Date(iso).toLocaleDateString("en-MY", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

function formatDateShort(iso: string): string {
  return new Date(iso).toLocaleDateString("en-MY", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function pct(count: number, total: number): string {
  if (total === 0) return "0.0%";
  return ((count / total) * 100).toFixed(1) + "%";
}

// ---------------------------------------------------------------------------
// Sub-components (all inline styles)
// ---------------------------------------------------------------------------

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <p
      style={{
        fontFamily: "Ubuntu, sans-serif",
        fontSize: "11px",
        fontWeight: 700,
        color: "#1A1A1A",
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        margin: "0 0 2mm 0",
      }}
    >
      {children}
    </p>
  );
}

function Divider() {
  return (
    <div style={{ height: "1px", background: "#D0D0D0", margin: "3mm 0" }} />
  );
}

function MetaField({
  label,
  value,
  right = false,
  large = false,
}: {
  label: string;
  value: string;
  right?: boolean;
  large?: boolean;
}) {
  return (
    <div>
      <p style={{
        fontSize: "8px",
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        color: "#9A9A9A",
        margin: 0,
      }}>
        {label}
      </p>
      <p style={{
        fontSize: large ? "13px" : "10.5px",
        fontWeight: large ? 700 : 500,
        color: "#1A1A1A",
        margin: "2px 0 0 0",
        textAlign: right ? "right" : "left",
        fontFamily: "monospace",
      }}>
        {value}
      </p>
    </div>
  );
}

// A single KPI tile in the summary grid
function KpiTile({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div style={{
      border: "1px solid #E0E0E0",
      borderRadius: "3px",
      padding: "4mm 5mm",
      background: "#F9F9F9",
    }}>
      <p style={{
        fontSize: "8px",
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.1em",
        color: "#9A9A9A",
        margin: "0 0 3px 0",
      }}>
        {label}
      </p>
      <p style={{
        fontFamily: "monospace",
        fontSize: "18px",
        fontWeight: 700,
        color: "#1A1A1A",
        margin: 0,
        lineHeight: 1.2,
      }}>
        {value}
      </p>
      {sub && (
        <p style={{
          fontSize: "8.5px",
          color: "#6B6B6B",
          margin: "3px 0 0 0",
          lineHeight: 1.4,
        }}>
          {sub}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const AnalyticsReportTemplate = forwardRef<HTMLDivElement, AnalyticsReportProps>(
  function AnalyticsReportTemplate(props, ref) {
    const {
      username,
      generatedAt,
      totalCount,
      totalVolume,
      highRiskCount,
      lowRiskCount,
      recentLogs,
    } = props;

    return (
      <div
        ref={ref}
        aria-hidden="true"
        style={{
          width: "210mm",
          height: "297mm",
          position: "relative",
          background: "#FFFFFF",
          fontFamily: "Lato, sans-serif",
          color: "#1A1A1A",
          boxSizing: "border-box",
        }}
      >

        {/* ── Letterhead background ──────────────────────────────────────── */}
        <img
          src={`${typeof window !== "undefined" ? window.location.origin : "http://localhost:3000"}/JuneBankCorporateLetterhead.png`}
          alt=""
          aria-hidden="true"
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            objectFit: "fill",
            zIndex: 0,
            pointerEvents: "none",
          }}
        />

        {/* ── Content layer ─────────────────────────────────────────────── */}
        <div
          style={{
            position: "relative",
            zIndex: 1,
            paddingTop: "28mm",
            paddingBottom: "22mm",
            paddingLeft: "14mm",
            paddingRight: "14mm",
            boxSizing: "border-box",
            height: "100%",
            display: "flex",
            flexDirection: "column",
          }}
        >

          {/* CONFIDENTIAL stamp */}
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "4mm" }}>
            <span style={{
              fontSize: "8px",
              fontWeight: 600,
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              color: "#9CA3AF",
            }}>
              Confidential
            </span>
          </div>

          {/* Report title — pushed down a touch with extra top margin */}
          <div style={{ textAlign: "center", marginTop: "6mm", marginBottom: "5mm" }}>
            <p style={{
              fontFamily: "Ubuntu, sans-serif",
              fontSize: "17px",
              fontWeight: 700,
              color: "#1A1A1A",
              margin: 0,
              letterSpacing: "0.01em",
            }}>
              Personal Analytics Performance Report
            </p>
          </div>

          {/* Metadata strip */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "0 12mm",
            marginTop: "6mm",
            marginBottom: "4mm",
            background: "#F9F9F9",
            border: "1px solid #E0E0E0",
            borderRadius: "4px",
            padding: "3mm 6mm",
          }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
              <MetaField label="Officer Username" value={username} large />
              <MetaField label="Total Evaluations on Record" value={totalCount.toString()} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "5px", textAlign: "right" }}>
              <MetaField label="Report Generated" value={formatDateLong(generatedAt)} right />
              <MetaField label="System" value="SHIELD · Random Forest Credit Risk Engine" right />
            </div>
          </div>

          <Divider />

          {/* ── Section 1: KPI Summary ────────────────────────────────── */}
          <SectionHeading>Performance Summary</SectionHeading>
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr 1fr",
            gap: "2mm",
            marginBottom: "4mm",
          }}>
            <KpiTile
              label="Total SMEs Evaluated"
              value={totalCount.toString()}
              sub="All-time evaluations"
            />
            <KpiTile
              label="Total Volume Processed"
              value={currencyFmt.format(totalVolume)}
              sub="Cumulative loan amounts"
            />
            <KpiTile
              label="High Risk Rate"
              value={pct(highRiskCount, totalCount)}
              sub={`${highRiskCount} of ${totalCount} evaluations`}
            />
            <KpiTile
              label="Low Risk Rate"
              value={pct(lowRiskCount, totalCount)}
              sub={`${lowRiskCount} of ${totalCount} evaluations`}
            />
          </div>

          <Divider />

          {/* ── Section 2: Risk Distribution ─────────────────────────── */}
          <SectionHeading>Risk Distribution Breakdown</SectionHeading>
          <table style={{
            width: "100%",
            borderCollapse: "collapse",
            marginBottom: "3mm",
            fontSize: "10px",
          }}>
            <thead>
              <tr style={{ background: "#F0F0F0" }}>
                {["Classification", "Count", "Share of Portfolio", "Avg. Loan Amount"].map((h) => (
                  <th key={h} style={{
                    padding: "3mm 4mm",
                    textAlign: "left",
                    fontWeight: 700,
                    fontSize: "8px",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    color: "#555555",
                    borderBottom: "1px solid #D0D0D0",
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                {
                  label: "High Risk",
                  count: highRiskCount,
                  logs: recentLogs.filter((l) => l.risk_classification === "High Risk"),
                  all: props.recentLogs, // used for avg — note: only recent 5 passed, label accordingly
                },
                {
                  label: "Low Risk",
                  count: lowRiskCount,
                  logs: recentLogs.filter((l) => l.risk_classification === "Low Risk"),
                  all: props.recentLogs,
                },
              ].map((row, i) => {
                const avgAmt = row.logs.length > 0
                  ? row.logs.reduce((s, l) => s + l.loan_amount, 0) / row.logs.length
                  : 0;
                return (
                  <tr key={row.label} style={{
                    background: i % 2 === 0 ? "#FFFFFF" : "#FAFAFA",
                    borderBottom: "1px solid #E8E8E8",
                  }}>
                    <td style={{ padding: "3mm 4mm", fontWeight: 600, color: "#1A1A1A" }}>
                      {row.label}
                    </td>
                    <td style={{ padding: "3mm 4mm", fontFamily: "monospace", color: "#1A1A1A" }}>
                      {row.count}
                    </td>
                    <td style={{ padding: "3mm 4mm", fontFamily: "monospace", color: "#1A1A1A" }}>
                      {pct(row.count, totalCount)}
                    </td>
                    <td style={{ padding: "3mm 4mm", fontFamily: "monospace", color: "#6B6B6B" }}>
                      {row.logs.length > 0 ? currencyFmt.format(avgAmt) : "—"}
                      {row.logs.length > 0 && (
                        <span style={{ fontSize: "8px", color: "#9A9A9A" }}> (recent sample)</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <Divider />

          {/* ── Section 3: Recent Pipeline ───────────────────────────── */}
          <SectionHeading>Recent Pipeline (Last 5 Evaluations)</SectionHeading>
          {recentLogs.length === 0 ? (
            <p style={{ fontSize: "10px", color: "#9A9A9A", fontStyle: "italic" }}>
              No evaluations found on record.
            </p>
          ) : (
            <table style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "9.5px",
            }}>
              <thead>
                <tr style={{ background: "#F0F0F0" }}>
                  {["Date", "Company Name", "SSM No.", "Loan Amount", "Classification"].map((h) => (
                    <th key={h} style={{
                      padding: "2.5mm 3mm",
                      textAlign: "left",
                      fontWeight: 700,
                      fontSize: "7.5px",
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      color: "#555555",
                      borderBottom: "1px solid #D0D0D0",
                      whiteSpace: "nowrap",
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recentLogs.map((log, i) => (
                  <tr key={log.id} style={{
                    background: i % 2 === 0 ? "#FFFFFF" : "#FAFAFA",
                    borderBottom: "1px solid #EEEEEE",
                  }}>
                    <td style={{ padding: "2.5mm 3mm", fontFamily: "monospace", color: "#1A1A1A", whiteSpace: "nowrap" }}>
                      {formatDateShort(log.evaluated_at)}
                    </td>
                    <td style={{ padding: "2.5mm 3mm", fontWeight: 600, color: "#1A1A1A" }}>
                      {log.company_name}
                    </td>
                    <td style={{ padding: "2.5mm 3mm", fontFamily: "monospace", color: "#6B6B6B" }}>
                      {log.ssm_number}
                    </td>
                    <td style={{ padding: "2.5mm 3mm", fontFamily: "monospace", color: "#1A1A1A", whiteSpace: "nowrap" }}>
                      {currencyFmt.format(log.loan_amount)}
                    </td>
                    <td style={{ padding: "2.5mm 3mm" }}>
                      <span style={{
                        display: "inline-block",
                        padding: "1px 6px",
                        border: `1px solid ${log.risk_classification === "High Risk" ? "#FCA5A5" : "#86EFAC"}`,
                        borderRadius: "2px",
                        background: log.risk_classification === "High Risk" ? "#FEF2F2" : "#F0FDF4",
                        color: log.risk_classification === "High Risk" ? "#991B1B" : "#166534",
                        fontSize: "8px",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                        whiteSpace: "nowrap",
                      }}>
                        {log.risk_classification}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* ── Disclaimer ────────────────────────────────────────────── */}
          <div style={{ marginTop: "auto", paddingTop: "3mm", borderTop: "1px solid #E0E0E0" }}>
            <p style={{ fontSize: "8px", color: "#9A9A9A", lineHeight: 1.5, margin: 0 }}>
              This report is generated by the SHIELD automated credit risk evaluation system and is
              intended solely for internal JuneBank use. Metrics reflect evaluations associated with
              the named officer account. This document does not constitute a final credit decision,
              performance review, or regulatory filing.
            </p>
          </div>

        </div>{/* end content layer */}
      </div>
    );
  }
);

export default AnalyticsReportTemplate;
