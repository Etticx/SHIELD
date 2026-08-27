"use client";

// =============================================================================
// SHIELD — InputForm Component
// Three input modes: Manual | Preset Profile | CSV/XLSX Upload
// All 20 fields are driven by local state; switching modes rewrites state
// atomically so the form is always consistent before submission.
// =============================================================================

import { useState, useRef, useCallback, ChangeEvent } from "react";
import { Upload, Download, ChevronDown } from "lucide-react";
import clsx from "clsx";

import type { SMEFinancialData } from "@/lib/types";
import {
  MEDIAN_DEFAULTS,
  PROFILE_HEALTHY,
  PROFILE_DISTRESSED,
  FEATURE_LABELS,
} from "@/lib/constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type ProfileKey = "manual" | "healthy" | "distressed";

interface Props {
  onEvaluate: (data: SMEFinancialData) => void;
  isLoading: boolean;
}

// Ordered list of field keys (must match SMEFinancialData / FEATURE_LABELS)
const FIELD_KEYS = Object.keys(FEATURE_LABELS) as Array<keyof SMEFinancialData>;

const PROFILES: Record<ProfileKey, { label: string; values: SMEFinancialData | null }> = {
  manual:     { label: "✏️  Manual Input",                    values: null },
  healthy:    { label: "🟢  Profile A: Healthy SME (Low Risk)",   values: PROFILE_HEALTHY },
  distressed: { label: "🔴  Profile B: Distressed SME (High Risk)", values: PROFILE_DISTRESSED },
};

// ---------------------------------------------------------------------------
// CSV template builder (runs client-side)
// ---------------------------------------------------------------------------
function buildCsvTemplate(): string {
  // Exact internal column names with leading spaces (must match backend)
  const headers = [
    " ROA(A) before interest and % after tax",
    " ROA(B) before interest and depreciation after tax",
    " Continuous interest rate (after tax)",
    " Net Value Per Share (B)",
    " Net Value Per Share (A)",
    " Net Value Per Share (C)",
    " Persistent EPS in the Last Four Seasons",
    " Per Share Net profit before tax",
    " Interest Expense Ratio",
    " Debt ratio %",
    " Net worth/Assets",
    " Borrowing dependency",
    " Net profit before tax/Paid-in capital",
    " Retained Earnings to Total Assets",
    " Total income/Total expense",
    " Net Income to Total Assets",
    " Net Income to Stockholder's Equity",
    " Liability to Equity",
    " Interest Coverage Ratio (Interest expense to EBIT)",
    " Equity to Liability",
  ];
  return headers.join(",") + "\n" + headers.map(() => "").join(",");
}

function downloadCsv(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// Map CSV header → SMEFinancialData key (order-based — headers and FIELD_KEYS share index)
const CSV_HEADER_TO_KEY: Record<string, keyof SMEFinancialData> = {
  " ROA(A) before interest and % after tax":                 "roa_a",
  " ROA(B) before interest and depreciation after tax":      "roa_b",
  " Continuous interest rate (after tax)":                   "continuous_interest_rate",
  " Net Value Per Share (B)":                                "net_value_per_share_b",
  " Net Value Per Share (A)":                                "net_value_per_share_a",
  " Net Value Per Share (C)":                                "net_value_per_share_c",
  " Persistent EPS in the Last Four Seasons":                "persistent_eps",
  " Per Share Net profit before tax":                        "per_share_net_profit",
  " Interest Expense Ratio":                                 "interest_expense_ratio",
  " Debt ratio %":                                           "debt_ratio",
  " Net worth/Assets":                                       "net_worth_assets",
  " Borrowing dependency":                                   "borrowing_dependency",
  " Net profit before tax/Paid-in capital":                  "net_profit_paid_in_capital",
  " Retained Earnings to Total Assets":                      "retained_earnings",
  " Total income/Total expense":                             "total_income_expense",
  " Net Income to Total Assets":                             "net_income_total_assets",
  " Net Income to Stockholder's Equity":                     "net_income_equity",
  " Liability to Equity":                                    "liability_to_equity",
  " Interest Coverage Ratio (Interest expense to EBIT)":     "interest_coverage_ratio",
  " Equity to Liability":                                    "equity_to_liability",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function InputForm({ onEvaluate, isLoading }: Props) {
  const [profile, setProfile]   = useState<ProfileKey>("manual");
  const [fields, setFields]     = useState<SMEFinancialData>({ ...MEDIAN_DEFAULTS });
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // ---- Profile switch ----
  const handleProfileChange = useCallback((key: ProfileKey) => {
    setProfile(key);
    const preset = PROFILES[key].values;
    setFields(preset ? { ...preset } : { ...MEDIAN_DEFAULTS });
    setUploadMsg(null);
    setUploadError(null);
    if (fileRef.current) fileRef.current.value = "";
  }, []);

  // ---- Single field edit ----
  const handleFieldChange = useCallback(
    (key: keyof SMEFinancialData, raw: string) => {
      const num = parseFloat(raw);
      setFields((prev) => ({ ...prev, [key]: isNaN(num) ? 0 : num }));
    },
    []
  );

  // ---- CSV upload ----
  const handleFileUpload = useCallback(
    async (e: ChangeEvent<HTMLInputElement>) => {
      setUploadMsg(null);
      setUploadError(null);

      const file = e.target.files?.[0];
      if (!file) return;

      try {
        const text = await file.text();
        const lines = text.split(/\r?\n/).filter((l) => l.trim());
        if (lines.length < 2) throw new Error("File has no data rows.");

        const rawHeaders = lines[0].split(",");
        const rawValues  = lines[1].split(",");

        const parsed: Partial<SMEFinancialData> = {};
        const missing: string[] = [];

        for (const [csvHeader, key] of Object.entries(CSV_HEADER_TO_KEY)) {
          const idx = rawHeaders.indexOf(csvHeader);
          if (idx === -1) { missing.push(csvHeader.trim()); continue; }
          const val = parseFloat(rawValues[idx]);
          if (isNaN(val)) throw new Error(`Non-numeric value for "${csvHeader.trim()}".`);
          parsed[key] = val;
        }

        if (missing.length > 0) {
          throw new Error(
            `Missing ${missing.length} column(s): ${missing.slice(0, 3).join(", ")}${
              missing.length > 3 ? ` … (+${missing.length - 3} more)` : ""
            }. Download the template to see the required headers.`
          );
        }

        setFields(parsed as SMEFinancialData);
        setProfile("manual");
        setUploadMsg(`✔ "${file.name}" loaded — fields updated from row 1.`);
      } catch (err) {
        setUploadError(err instanceof Error ? err.message : "Could not parse file.");
      }
    },
    []
  );

  // ---- Submit ----
  const handleSubmit = useCallback(() => {
    onEvaluate(fields);
  }, [fields, onEvaluate]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="flex flex-col gap-5">

      {/* ---- Profile Selector ---- */}
      <div>
        <label className="section-label block">Select SME Test Profile</label>
        <div className="relative">
          <select
            value={profile}
            onChange={(e) => handleProfileChange(e.target.value as ProfileKey)}
            className="w-full appearance-none bg-brand-bg border border-brand-border
                       rounded-lg px-3 py-2.5 text-sm text-brand-text
                       focus:outline-none focus:ring-1 focus:ring-brand-yellow/60
                       focus:border-brand-yellow/60 transition-colors cursor-pointer"
          >
            {(Object.entries(PROFILES) as [ProfileKey, typeof PROFILES[ProfileKey]][]).map(
              ([key, { label }]) => (
                <option key={key} value={key}>{label}</option>
              )
            )}
          </select>
          <ChevronDown
            size={14}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-muted pointer-events-none"
          />
        </div>

        {/* Profile badge */}
        {profile !== "manual" && (
          <p className={clsx(
            "mt-1.5 text-xs px-2 py-1 rounded",
            profile === "healthy"
              ? "text-risk-low bg-risk-lowBg"
              : "text-risk-high bg-risk-highBg"
          )}>
            {profile === "healthy"
              ? "✔ Healthy preset loaded — P(default) ≈ 0.007%"
              : "✔ Distressed preset loaded — P(default) ≈ 99.8%"}
          </p>
        )}
      </div>

      {/* ---- Upload Section ---- */}
      <div className="border border-brand-border rounded-lg overflow-hidden">
        <div className="bg-brand-panel/60 px-3 py-2 border-b border-brand-border
                        flex items-center justify-between">
          <span className="section-label mb-0">Upload SME Data File</span>
          <button
            type="button"
            onClick={() => downloadCsv(buildCsvTemplate(), "SHIELD_input_template.csv")}
            className="btn-ghost flex items-center gap-1 py-1 px-2 text-xs"
          >
            <Download size={11} />
            Template
          </button>
        </div>

        <label
          htmlFor="sme-upload"
          className="flex flex-col items-center justify-center gap-2 px-4 py-5
                     cursor-pointer hover:bg-brand-panel/30 transition-colors
                     border-2 border-dashed border-transparent hover:border-brand-border
                     mx-2 my-2 rounded-lg"
        >
          <Upload size={20} className="text-brand-muted" />
          <span className="text-xs text-brand-subtext text-center">
            Drop a <span className="text-brand-yellow font-medium">.csv</span> file here,
            or <span className="text-brand-yellow font-medium">click to browse</span>
            <br />
            <span className="text-brand-muted">First data row populates all 20 fields</span>
          </span>
          <input
            id="sme-upload"
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileUpload}
          />
        </label>

        {uploadMsg && (
          <p className="mx-3 mb-2 text-xs text-risk-low bg-risk-lowBg px-2 py-1 rounded">
            {uploadMsg}
          </p>
        )}
        {uploadError && (
          <p className="mx-3 mb-2 text-xs text-risk-high bg-risk-highBg px-2 py-1 rounded">
            {uploadError}
          </p>
        )}
      </div>

      {/* ---- 20 Field Inputs ---- */}
      <div>
        <p className="section-label">Financial Metrics (normalised 0 – 1)</p>
        <div className="flex flex-col gap-2">
          {FIELD_KEYS.map((key) => (
            <div key={key} className="flex flex-col gap-0.5">
              <label
                htmlFor={`field-${key}`}
                className="text-[0.72rem] text-brand-subtext truncate"
                title={FEATURE_LABELS[key]}
              >
                {FEATURE_LABELS[key]}
              </label>
              <input
                id={`field-${key}`}
                type="number"
                step="0.0001"
                min="0"
                max="1"
                value={fields[key]}
                onChange={(e) => handleFieldChange(key, e.target.value)}
                className="input-field text-right"
              />
            </div>
          ))}
        </div>
      </div>

      {/* ---- Submit ---- */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={isLoading}
        className="btn-primary flex items-center justify-center gap-2 sticky bottom-0"
      >
        {isLoading ? (
          <>
            <span className="h-4 w-4 rounded-full border-2 border-black/40
                             border-t-black animate-spin" />
            Evaluating…
          </>
        ) : (
          <>⚡ Evaluate Risk</>
        )}
      </button>

    </div>
  );
}
