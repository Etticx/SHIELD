"use client";

// =============================================================================
// SHIELD — InputForm Component  (v1.2 — flat list, 2-col grid)
//
// All 20 fields are visible at once in a compact 2-column grid, grouped
// under 4 labelled sections (no tabs — everything scrollable).
//
// Structure:
//   Profile selector
//   CSV upload strip
//   ── Profitability ──────── (5 fields, 2-col grid)
//   ── Per-Share Value ─────── (5 fields, 2-col grid)
//   ── Leverage & Solvency ── (5 fields, 2-col grid)
//   ── Debt Service ──────── (5 fields, 2-col grid)
//   [Evaluate Risk] CTA
// =============================================================================

import { useState, useRef, useCallback, ChangeEvent } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Upload, Download, ChevronDown,
  Pencil, CheckCircle, XCircle, Check, Zap,
  TrendingUp, BarChart2, Scale, Landmark,
} from "lucide-react";
import clsx from "clsx";

import type { SMEFinancialData } from "@/lib/types";
import {
  MEDIAN_DEFAULTS,
  PROFILE_HEALTHY,
  PROFILE_DISTRESSED,
  FEATURE_LABELS,
  FIELD_TOOLTIPS,
} from "@/lib/constants";
import InfoTooltip from "@/components/InfoTooltip";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type ProfileKey = "manual" | "healthy" | "distressed";

interface Props {
  onEvaluate: (data: SMEFinancialData) => void;
  isLoading: boolean;
}

// ---------------------------------------------------------------------------
// Profile config
// ---------------------------------------------------------------------------
const PROFILES: Record<ProfileKey, {
  label: string;
  Icon: LucideIcon;
  iconClass: string;
  values: SMEFinancialData | null;
}> = {
  manual: { label: "Manual Input", Icon: Pencil, iconClass: "text-brand-muted", values: null },
  healthy: { label: "Profile A: Healthy SME", Icon: CheckCircle, iconClass: "text-risk-low", values: PROFILE_HEALTHY },
  distressed: { label: "Profile B: Distressed SME", Icon: XCircle, iconClass: "text-risk-high", values: PROFILE_DISTRESSED },
};

// ---------------------------------------------------------------------------
// Field groups — all 20 fields, split into 4 labelled sections
// ---------------------------------------------------------------------------
const FIELD_GROUPS: Array<{
  label: string;
  Icon: LucideIcon;
  fields: Array<keyof SMEFinancialData>;
}> = [
    {
      label: "Profitability & Earnings",
      Icon: TrendingUp,
      fields: [
        "roa_c",
        "roa_a",
        "persistent_eps",
        "net_profit_paid_in_capital",
        "net_income_total_assets",
      ],
    },
    {
      label: "Per-Share Value",
      Icon: BarChart2,
      fields: [
        "net_value_per_share_a",
        "net_value_per_share_b",
        "net_value_per_share_c",
        "per_share_net_profit",
        "net_income_equity",
      ],
    },
    {
      label: "Leverage & Solvency",
      Icon: Scale,
      fields: [
        "debt_ratio",
        "net_worth_assets",
        "borrowing_dependency",
        "liability_to_equity",
        "equity_to_liability",
      ],
    },
    {
      label: "Debt Service & Interest",
      Icon: Landmark,
      fields: [
        "interest_expense_ratio",
        "continuous_interest_rate",
        "retained_earnings",
        "total_income_expense",
        "interest_coverage_ratio",
      ],
    },
  ];

// ---------------------------------------------------------------------------
// CSV helpers
// ---------------------------------------------------------------------------
function buildCsvTemplate(): string {
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
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

const CSV_HEADER_TO_KEY: Record<string, keyof SMEFinancialData> = {
  " ROA(C) before interest and depreciation before interest": "roa_c",
  " ROA(A) before interest and % after tax": "roa_a",
  " Continuous interest rate (after tax)": "continuous_interest_rate",
  " Net Value Per Share (B)": "net_value_per_share_b",
  " Net Value Per Share (A)": "net_value_per_share_a",
  " Net Value Per Share (C)": "net_value_per_share_c",
  " Persistent EPS in the Last Four Seasons": "persistent_eps",
  " Per Share Net profit before tax": "per_share_net_profit",
  " Interest Expense Ratio": "interest_expense_ratio",
  " Debt ratio %": "debt_ratio",
  " Net worth/Assets": "net_worth_assets",
  " Borrowing dependency": "borrowing_dependency",
  " Net profit before tax/Paid-in capital": "net_profit_paid_in_capital",
  " Retained Earnings to Total Assets": "retained_earnings",
  " Total income/Total expense": "total_income_expense",
  " Net Income to Total Assets": "net_income_total_assets",
  " Net Income to Stockholder's Equity": "net_income_equity",
  " Liability to Equity": "liability_to_equity",
  " Interest Coverage Ratio (Interest expense to EBIT)": "interest_coverage_ratio",
  " Equity to Liability": "equity_to_liability",
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export default function InputForm({ onEvaluate, isLoading }: Props) {
  const [profile, setProfile] = useState<ProfileKey>("manual");
  const [fields, setFields] = useState<SMEFinancialData>({ ...MEDIAN_DEFAULTS });
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleProfileChange = useCallback((key: ProfileKey) => {
    setProfile(key);
    const preset = PROFILES[key].values;
    setFields(preset ? { ...preset } : { ...MEDIAN_DEFAULTS });
    setUploadMsg(null);
    setUploadError(null);
    if (fileRef.current) fileRef.current.value = "";
  }, []);

  const handleFieldChange = useCallback((key: keyof SMEFinancialData, raw: string) => {
    const num = parseFloat(raw);
    setFields((prev) => ({ ...prev, [key]: isNaN(num) ? 0 : num }));
  }, []);

  const handleFileUpload = useCallback(async (e: ChangeEvent<HTMLInputElement>) => {
    setUploadMsg(null);
    setUploadError(null);
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const lines = text.split(/\r?\n/).filter((l) => l.trim());
      if (lines.length < 2) throw new Error("File has no data rows.");
      const rawHeaders = lines[0].split(",");
      const rawValues = lines[1].split(",");
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
          `Missing ${missing.length} column(s): ${missing.slice(0, 3).join(", ")}` +
          (missing.length > 3 ? ` … (+${missing.length - 3} more)` : "") +
          ". Download the template for required headers."
        );
      }
      setFields(parsed as SMEFinancialData);
      setProfile("manual");
      setUploadMsg(`"${file.name}" loaded — all 20 fields updated.`);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Could not parse file.");
    }
  }, []);

  const handleSubmit = useCallback(() => onEvaluate(fields), [fields, onEvaluate]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="flex flex-col gap-5">

      {/* ── Profile selector ─────────────────────────────────────────────── */}
      <div>
        <p className="section-label">Test Profile</p>
        <div className="relative">
          <button
            type="button"
            onClick={() => setDropdownOpen((v) => !v)}
            className="w-full flex items-center gap-2 bg-brand-bg border border-brand-border
                       rounded-lg px-3 py-2.5 text-sm text-brand-text
                       focus:outline-none focus:ring-1 focus:ring-brand-yellow/60
                       focus:border-brand-yellow/60 transition-colors text-left"
          >
            {(() => {
              const { Icon, iconClass, label } = PROFILES[profile];
              return (
                <>
                  <Icon size={13} className={iconClass} />
                  <span className="flex-1 truncate">{label}</span>
                </>
              );
            })()}
            <ChevronDown
              size={13}
              className={clsx(
                "text-brand-muted transition-transform duration-150 shrink-0",
                dropdownOpen && "rotate-180"
              )}
            />
          </button>

          {dropdownOpen && (
            <div className="absolute z-20 mt-1 w-full bg-brand-panel border border-brand-border
                            rounded-lg shadow-card overflow-hidden">
              {(Object.entries(PROFILES) as [ProfileKey, typeof PROFILES[ProfileKey]][]).map(
                ([key, { label, Icon, iconClass }]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => { handleProfileChange(key); setDropdownOpen(false); }}
                    className={clsx(
                      "w-full flex items-center gap-2 px-3 py-2.5 text-sm text-left",
                      "hover:bg-brand-bg transition-colors",
                      profile === key ? "text-brand-charcoal font-semibold" : "text-brand-subtext"
                    )}
                  >
                    <Icon size={13} className={iconClass} />
                    {label}
                  </button>
                )
              )}
            </div>
          )}
        </div>

        {profile !== "manual" && (
          <p className={clsx(
            "mt-1.5 text-xs px-2 py-1 rounded flex items-center gap-1.5",
            profile === "healthy" ? "text-risk-low bg-risk-lowBg" : "text-risk-high bg-risk-highBg"
          )}>
            <Check size={10} />
            {profile === "healthy"
              ? "Healthy preset — P(default) ≈ 0.007%"
              : "Distressed preset — P(default) ≈ 99.8%"}
          </p>
        )}
      </div>

      {/* ── CSV upload strip ─────────────────────────────────────────────── */}
      <div className="border border-brand-border rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-3 py-2 bg-brand-panel/60
                        border-b border-brand-border">
          <p className="section-label mb-0">Upload SME Data File</p>
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
          className="flex items-center gap-3 px-3 py-3 cursor-pointer
                     hover:bg-brand-panel/40 transition-colors"
        >
          <Upload size={18} className="text-brand-muted shrink-0" />
          <span className="text-xs text-brand-subtext leading-snug">
            Drop a <span className="text-brand-yellow font-medium">.csv</span> or{" "}
            <span className="text-brand-yellow font-medium">click to browse</span>
            <span className="block text-brand-muted text-[0.68rem] mt-0.5">
              First data row populates all 20 fields
            </span>
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
          <p className="mx-3 mb-2 text-xs text-risk-low bg-risk-lowBg px-2 py-1 rounded
                        flex items-center gap-1.5">
            <Check size={10} />{uploadMsg}
          </p>
        )}
        {uploadError && (
          <p className="mx-3 mb-2 text-xs text-risk-high bg-risk-highBg px-2 py-1 rounded">
            {uploadError}
          </p>
        )}
      </div>

      {/* ── All 20 fields — 4 labelled groups, 2-col grid each ───────────── */}
      <div className="flex flex-col gap-5">
        {FIELD_GROUPS.map(({ label, Icon, fields: groupFields }) => (
          <div key={label}>
            {/* Group header */}
            <div className="flex items-center gap-2 mb-2.5 pb-1.5 border-b border-brand-border">
              <Icon size={11} className="text-brand-muted shrink-0" />
              <p className="text-[0.68rem] font-bold uppercase tracking-widest text-brand-muted">
                {label}
              </p>
            </div>

            {/* 2-column field grid */}
            <div className="grid grid-cols-2 gap-x-3 gap-y-3">
              {groupFields.map((key) => {
                const fieldLabel = FEATURE_LABELS[key];
                const tooltipText = FIELD_TOOLTIPS[key];
                return (
                  <div key={key} className="flex flex-col gap-1">
                    <label
                      htmlFor={`field-${key}`}
                      className="text-[0.67rem] leading-tight text-brand-subtext flex items-center gap-1"
                    >
                      <span className="truncate flex-1" title={fieldLabel}>
                        {fieldLabel}
                      </span>
                      <InfoTooltip text={tooltipText} />
                    </label>
                    <input
                      id={`field-${key}`}
                      type="number"
                      step="0.0001"
                      min="0"
                      max="1"
                      value={fields[key]}
                      onChange={(e) => handleFieldChange(key, e.target.value)}
                      className="input-field text-right py-1.5 text-xs"
                    />
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* ── Evaluate CTA ─────────────────────────────────────────────────── */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={isLoading}
        className="btn-primary w-full flex items-center justify-center gap-2 sticky bottom-4"
      >
        {isLoading ? (
          <>
            <span className="h-4 w-4 rounded-full border-2 border-black/30 border-t-black animate-spin" />
            Evaluating…
          </>
        ) : (
          <>
            <Zap size={14} />
            Evaluate Risk
          </>
        )}
      </button>

    </div>
  );
}
