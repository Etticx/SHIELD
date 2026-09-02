// =============================================================================
// SHIELD — ReportTemplate  (corporate banking edition)
//
// A4 print component. Lives inside a display:none <tr><td> in the logs table
// so it is valid HTML and fully mounts in the DOM (ref is populated).
// react-to-print clones the ref'd div into a sandboxed iframe for printing.
//
// Styling philosophy:
//   • All inline styles — immune to Tailwind purge inside the print iframe.
//   • No web-dashboard colours. Plain black/grey professional palette.
//   • Background image supplies all branding (header logo + footer bar).
// =============================================================================

import { forwardRef } from "react";
import type { LogEntry, ShapFeature } from "@/lib/types";

interface Props {
  log: LogEntry;
}

// ---------------------------------------------------------------------------
// Helpers
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

/**
 * Split advisory text into paragraphs and highlight "Recommendation:" keyword.
 * Returns an array of React nodes — each paragraph is either a plain <p> or
 * a <p> that contains a <strong>Recommendation:</strong> prefix.
 */
function renderAdvisory(text: string): React.ReactNode[] {
  const paragraphs = text
    .split(/\n+/)
    .map((p) => p.trim())
    .filter(Boolean);

  return paragraphs.map((para, i) => {
    const keyword = "Recommendation:";
    const idx = para.indexOf(keyword);

    return (
      <p
        key={i}
        style={{
          fontSize: "10.5px",
          color: "#2D2D2D",
          lineHeight: 1.7,
          margin: i === 0 ? "0" : "7px 0 0 0",
        }}
      >
        {idx !== -1 ? (
          <>
            {para.slice(0, idx)}
            <strong style={{ fontWeight: 700, color: "#000000" }}>{keyword}</strong>
            {para.slice(idx + keyword.length)}
          </>
        ) : (
          para
        )}
      </p>
    );
  });
}

// ---------------------------------------------------------------------------
// SHAP driver row — plain numbered list, no circular badges
// ---------------------------------------------------------------------------
function ShapRow({ feature, rank }: { feature: ShapFeature; rank: number }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "8px",
        padding: "5px 0",
        borderBottom: "1px solid #E5E5E5",
      }}
    >
      {/* Plain number — "1." style */}
      <span
        style={{
          flexShrink: 0,
          fontSize: "10px",
          fontWeight: 700,
          color: "#1A1A1A",
          width: "14px",
          marginTop: "1px",
        }}
      >
        {rank}.
      </span>

      {/* Label */}
      <span style={{ flex: 1, fontSize: "10px", color: "#1A1A1A", lineHeight: 1.4 }}>
        {feature.label}
      </span>

      {/* SHAP value */}
      <span
        style={{
          flexShrink: 0,
          fontFamily: "monospace",
          fontSize: "10px",
          fontWeight: 700,
          color: "#1A1A1A",
        }}
      >
        {feature.shap_value > 0 ? "+" : ""}
        {feature.shap_value.toFixed(4)}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const ReportTemplate = forwardRef<HTMLDivElement, Props>(function ReportTemplate(
  { log },
  ref
) {
  const isHigh = log.risk_classification === "High Risk";

  const sorted = [...log.shap_breakdown].sort(
    (a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)
  );
  const topRiskDrivers = sorted.filter((f) => f.direction === "risk").slice(0, 3);
  const topProtective = sorted.filter((f) => f.direction === "protective").slice(0, 3);

  return (
    <div
      ref={ref}
      aria-hidden="true"
      style={{
        width: "210mm",
        minHeight: "297mm",
        position: "relative",
        background: "#FFFFFF",
        fontFamily: "Lato, sans-serif",
        color: "#1A1A1A",
        boxSizing: "border-box",
      }}
    >
      {/* ── Letterhead background image ──────────────────────────────────── */}
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

      {/* ── Content layer ────────────────────────────────────────────────── */}
      <div
        style={{
          position: "relative",
          zIndex: 1,
          // Top padding clears the letterhead header graphic
          // Bottom padding clears the gold/black footer bar
          paddingTop: "28mm",
          paddingBottom: "30mm",
          paddingLeft: "14mm",
          paddingRight: "14mm",
          boxSizing: "border-box",
        }}
      >

        {/* ── Top strip: "CONFIDENTIAL" right-aligned ───────────────────── */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "6mm" }}>
          <span
            style={{
              fontSize: "8px",
              fontWeight: 600,
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              color: "#9CA3AF",   /* muted grey */
            }}
          >
            Confidential
          </span>
        </div>

        {/* ── Report title — centred, no border below ───────────────────── */}
        <div style={{ textAlign: "center", marginBottom: "8mm" }}>
          <p
            style={{
              fontFamily: "Ubuntu, sans-serif",
              fontSize: "17px",
              fontWeight: 700,
              color: "#1A1A1A",
              margin: 0,
              letterSpacing: "0.01em",
            }}
          >
            SME Credit Risk Evaluation Report
          </p>
        </div>

        {/* ── Metadata grid ────────────────────────────────────────────── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "0 12mm",
            marginTop: "16mm",   /* pushes grid clear of the letterhead gold/black line */
            marginBottom: "7mm",
            background: "#F9F9F9",
            border: "1px solid #E0E0E0",
            borderRadius: "4px",
            padding: "5mm 6mm",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
            <MetaField label="Evaluation For" value={log.company_name} large />
            <MetaField label="SSM Reg. No." value={log.ssm_number} />
            <MetaField label="Requested Facility" value={currencyFmt.format(log.loan_amount)} />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "5px", textAlign: "right" }}>
            <MetaField label="Date Generated" value={formatDateLong(log.evaluated_at)} right />
            <MetaField label="Evaluator" value={log.evaluator} right />
            <MetaField label="Evaluation ID" value={`#${log.id}`} right />
          </div>
        </div>

        {/* ── Section divider ─────────────────────────────────────────── */}
        <div style={{ height: "1px", background: "#D0D0D0", marginBottom: "6mm" }} />

        {/* ── Executive Risk Advisory ──────────────────────────────────── */}
        <SectionHeading>Executive Risk Advisory</SectionHeading>
        <div style={{ marginBottom: "7mm" }}>
          {renderAdvisory(log.advisory_report)}
        </div>

        {/* ── Section divider ─────────────────────────────────────────── */}
        <div style={{ height: "1px", background: "#D0D0D0", marginBottom: "6mm" }} />

        {/* ── Quantitative Risk Assessment ─────────────────────────────── */}
        <SectionHeading>Quantitative Risk Assessment</SectionHeading>

        {/* Result box — stark corporate, no colour backgrounds */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "12px",
            padding: "6px 16px",
            border: "1.5px solid #1A1A1A",
            borderRadius: "3px",
            background: "#F9F9F9",
            marginBottom: "6mm",
          }}
        >
          <span
            style={{
              fontFamily: "Ubuntu, sans-serif",
              fontSize: "12px",
              fontWeight: 700,
              color: "#1A1A1A",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            {log.risk_classification}
          </span>
          <span style={{ width: "1px", height: "14px", background: "#BBBBBB" }} />
          <span
            style={{
              fontFamily: "monospace",
              fontSize: "12px",
              fontWeight: 700,
              color: "#1A1A1A",
            }}
          >
            P(Default) = {(log.probability_default * 100).toFixed(2)}%
          </span>
        </div>

        {/* SHAP drivers — 2 columns, monochrome */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 10mm" }}>

          <div>
            <p style={shapColHeadStyle}>Top Risk Drivers</p>
            {topRiskDrivers.length > 0
              ? topRiskDrivers.map((f, i) => <ShapRow key={f.label} feature={f} rank={i + 1} />)
              : <p style={emptyStyle}>None identified.</p>}
          </div>

          <div>
            <p style={shapColHeadStyle}>Top Protective Factors</p>
            {topProtective.length > 0
              ? topProtective.map((f, i) => <ShapRow key={f.label} feature={f} rank={i + 1} />)
              : <p style={emptyStyle}>None identified.</p>}
          </div>

        </div>

        {/* ── Disclaimer ───────────────────────────────────────────────── */}
        <div style={{ marginTop: "8mm", paddingTop: "4mm", borderTop: "1px solid #E0E0E0" }}>
          <p style={{ fontSize: "8px", color: "#9A9A9A", lineHeight: 1.5, margin: 0 }}>
            This report is generated by the SHIELD automated credit risk evaluation system and is
            intended solely for internal JuneBank use. The probability of default figure is derived
            from a machine learning model trained on historical data and should be used as one input
            among many in the credit decision process. This document does not constitute a final
            credit decision or regulatory advice.
          </p>
        </div>

      </div>{/* end content layer */}
    </div>
  );
});

export default ReportTemplate;

// ---------------------------------------------------------------------------
// Style constants
// ---------------------------------------------------------------------------
const shapColHeadStyle: React.CSSProperties = {
  fontSize: "9px",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.08em",
  color: "#444444",
  marginBottom: "4px",
};

const emptyStyle: React.CSSProperties = {
  fontSize: "10px",
  color: "#9A9A9A",
  fontStyle: "italic",
};

// ---------------------------------------------------------------------------
// Sub-components
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
        margin: "0 0 4mm 0",
      }}
    >
      {children}
    </p>
  );
}

function MetaField({
  label,
  value,
  large = false,
  right = false,
}: {
  label: string;
  value: string;
  large?: boolean;
  right?: boolean;
}) {
  return (
    <div>
      <p
        style={{
          fontSize: "8px",
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          color: "#9A9A9A",
          margin: 0,
        }}
      >
        {label}
      </p>
      <p
        style={{
          fontSize: large ? "13px" : "10.5px",
          fontWeight: large ? 700 : 500,
          color: "#1A1A1A",
          margin: "2px 0 0 0",
          textAlign: right ? "right" : "left",
        }}
      >
        {value}
      </p>
    </div>
  );
}
