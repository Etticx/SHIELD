"use client";

// =============================================================================
// SHIELD — InputForm Component  (v1.3 — Random Forest / verified feature order)
//
// Field order and keys match model.feature_names_in_ exactly.
// All 20 fields visible at once in a compact 2-column grid, grouped under
// 4 labelled sections (no tabs — everything scrollable).
// =============================================================================

import { useState, useRef, useCallback, ChangeEvent } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Upload, Download, ChevronDown,
  Pencil, CheckCircle, AlertTriangle, Flame, Check, Zap,
  TrendingUp, BarChart2, Scale, Landmark, Activity,
} from "lucide-react";
import clsx from "clsx";

import type { SMEFinancialData } from "@/lib/types";
import {
  createFinancialDraft, assessReadiness, toFinancialData, parseFinancialCsv,
  AVAILABILITY_LABELS,
} from "@/lib/readiness";
import type { FinancialDraft, ProfileKey, Availability } from "@/lib/readiness";
import {
  PROFILE_HEALTHY,
  PROFILE_MODERATE,
  PROFILE_CRITICAL,
  PROFILE_DISTRESSED,
  FEATURE_LABELS,
  FIELD_TOOLTIPS,
} from "@/lib/constants";
import InfoTooltip from "@/components/InfoTooltip";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Props {
  onEvaluate: (data: SMEFinancialData) => void;
  draft: FinancialDraft;
  onDraftChange: (draft: FinancialDraft) => void;
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
  healthy: { label: "Profile A: Low Risk", Icon: CheckCircle, iconClass: "text-risk-low", values: PROFILE_HEALTHY },
  moderate: { label: "Profile B: Moderate Risk", Icon: Activity, iconClass: "text-risk-moderate", values: PROFILE_MODERATE },
  critical: { label: "Profile C: High Risk", Icon: AlertTriangle, iconClass: "text-risk-high", values: PROFILE_CRITICAL },
  distressed: { label: "Profile D: Critical Risk", Icon: Flame, iconClass: "text-risk-critical", values: PROFILE_DISTRESSED },
};

// ---------------------------------------------------------------------------
// Field groups — 20 keys in training-verified order, split into 4 sections
// ---------------------------------------------------------------------------
const FIELD_GROUPS: Array<{
  label: string;
  Icon: LucideIcon;
  fields: Array<keyof SMEFinancialData>;
}> = [
    {
      label: "Return on Assets",
      Icon: TrendingUp,
      fields: [
        "roa_c_before_interest_and_depreciation_before_interest",
        "roa_a_before_interest_and_percent_after_tax",
        "roa_b_before_interest_and_depreciation_after_tax",
        "net_income_to_total_assets",
        "net_income_to_stockholders_equity",
      ],
    },
    {
      label: "Profitability & Earnings",
      Icon: BarChart2,
      fields: [
        "persistent_eps_in_the_last_four_seasons",
        "per_share_net_profit_before_tax",
        "net_profit_before_tax_paid_in_capital",
        "net_value_per_share_a",
        "net_value_per_share_b",
      ],
    },
    {
      label: "Leverage & Solvency",
      Icon: Scale,
      fields: [
        "debt_ratio_percent",
        "net_worth_assets",
        "borrowing_dependency",
        "degree_of_financial_leverage_dfl",
        "retained_earnings_to_total_assets",
      ],
    },
    {
      label: "Debt Service & Interest",
      Icon: Landmark,
      fields: [
        "interest_expense_ratio",
        "interest_coverage_ratio",
        "continuous_interest_rate_after_tax",
        "liability_to_equity",
        "equity_to_liability",
      ],
    },
  ];

// ---------------------------------------------------------------------------
// CSV helpers — headers use the dataset's original labels (with leading space)
// so uploaded files map correctly via CSV_HEADER_TO_KEY below.
// ---------------------------------------------------------------------------
function buildCsvTemplate(): string {
  const headers = [
    " ROA(C) before interest and depreciation before interest",
    " ROA(A) before interest and % after tax",
    " ROA(B) before interest and depreciation after tax",
    " Continuous interest rate (after tax)",
    " Net Value Per Share (B)",
    " Net Value Per Share (A)",
    " Persistent EPS in the Last Four Seasons",
    " Per Share Net profit before tax",
    " Interest Expense Ratio",
    " Debt ratio %",
    " Net worth/Assets",
    " Borrowing dependency",
    " Net profit before tax/Paid-in capital",
    " Retained Earnings to Total Assets",
    " Net Income to Total Assets",
    " Net Income to Stockholder's Equity",
    " Liability to Equity",
    " Degree of Financial Leverage (DFL)",
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

// Maps dataset CSV header (with leading space) → Pydantic snake_case key
const CSV_HEADER_TO_KEY: Record<string, keyof SMEFinancialData> = {
  " ROA(C) before interest and depreciation before interest": "roa_c_before_interest_and_depreciation_before_interest",
  " ROA(A) before interest and % after tax": "roa_a_before_interest_and_percent_after_tax",
  " ROA(B) before interest and depreciation after tax": "roa_b_before_interest_and_depreciation_after_tax",
  " Continuous interest rate (after tax)": "continuous_interest_rate_after_tax",
  " Net Value Per Share (B)": "net_value_per_share_b",
  " Net Value Per Share (A)": "net_value_per_share_a",
  " Persistent EPS in the Last Four Seasons": "persistent_eps_in_the_last_four_seasons",
  " Per Share Net profit before tax": "per_share_net_profit_before_tax",
  " Interest Expense Ratio": "interest_expense_ratio",
  " Debt ratio %": "debt_ratio_percent",
  " Net worth/Assets": "net_worth_assets",
  " Borrowing dependency": "borrowing_dependency",
  " Net profit before tax/Paid-in capital": "net_profit_before_tax_paid_in_capital",
  " Retained Earnings to Total Assets": "retained_earnings_to_total_assets",
  " Net Income to Total Assets": "net_income_to_total_assets",
  " Net Income to Stockholder's Equity": "net_income_to_stockholders_equity",
  " Liability to Equity": "liability_to_equity",
  " Degree of Financial Leverage (DFL)": "degree_of_financial_leverage_dfl",
  " Interest Coverage Ratio (Interest expense to EBIT)": "interest_coverage_ratio",
  " Equity to Liability": "equity_to_liability",
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export default function InputForm({ onEvaluate, draft, onDraftChange, isLoading }: Props) {
  const profile = draft.profile;
  const readiness = assessReadiness(draft);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleProfileChange = useCallback((key: ProfileKey) => {
    const preset = PROFILES[key].values;
    onDraftChange(createFinancialDraft(preset ?? undefined, key));
    setUploadMsg(null);
    setUploadError(null);
    if (fileRef.current) fileRef.current.value = "";
  }, [onDraftChange]);

  const handleFieldChange = useCallback((key: keyof SMEFinancialData, raw: string) => {
    onDraftChange({ ...draft, values: { ...draft.values, [key]: raw } });
    setUploadMsg(null);
  }, [draft, onDraftChange]);

  const handleAvailabilityChange = (key: keyof SMEFinancialData, availability: Availability) => {
    onDraftChange({
      ...draft,
      availability: { ...draft.availability, [key]: availability },
      values: { ...draft.values, [key]: "" },
    });
    setUploadMsg(null);
  };

  const handleFileUpload = useCallback(async (e: ChangeEvent<HTMLInputElement>) => {
    setUploadMsg(null);
    setUploadError(null);
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const parsed = parseFinancialCsv(await file.text(), CSV_HEADER_TO_KEY);
      onDraftChange(parsed);
      setUploadMsg(`"${file.name}" loaded — ${assessReadiness(parsed).provided} of 20 metrics provided. Missing fields remain blank.`);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Could not parse file.");
    }
  }, [onDraftChange]);

  const handleSubmit = () => {
    if (readiness.ready && !isLoading) onEvaluate(toFinancialData(draft));
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="flex flex-col gap-5">

      <div className="rounded-lg border border-brand-border px-3 py-3 text-xs text-brand-subtext" aria-live="polite">
        <p className="font-semibold text-brand-charcoal">
          {readiness.ready ? "Ready to evaluate" : "Insufficient Data"}
          <span className="ml-2 font-normal">{readiness.provided} / 20 metrics provided</span>
        </p>
        <p className="mt-1.5 leading-relaxed">
          Provide normalised values supported by financial records. Leave unknown values blank,
          or select why a metric is unavailable. Zero is a valid value when supported by the records.
        </p>
        {!readiness.ready && (
          <details className="mt-2">
            <summary className="cursor-pointer font-medium">View missing or invalid metrics</summary>
            <ul className="mt-2 space-y-1 list-disc pl-4">
              {readiness.missing.map((item) => <li key={item.key}>{item.label} — {item.reason}</li>)}
              {readiness.invalid.map((item) => <li key={item.key}>{item.label} — enter a number between 0 and 1</li>)}
            </ul>
          </details>
        )}
        <p className="mt-2 leading-relaxed">
          For new businesses, mark historical metrics as “Not enough history”. If a share-based metric
          does not apply to the business structure, select “Not applicable”. Request supporting accounts
          or refer the case for another assessment approach.
        </p>
      </div>

      {/* ── Profile selector ─────────────────────────────────────────────── */}
      <div>
        <p className="section-label">Manual Entry / Demo Profiles</p>
        <div className="relative">
          <button
            type="button"
            disabled={isLoading}
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
                    disabled={isLoading}
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
            profile === "healthy" && "text-risk-low      bg-risk-lowBg",
            profile === "moderate" && "text-risk-moderate bg-risk-moderateBg",
            profile === "critical" && "text-risk-high     bg-risk-highBg",
            profile === "distressed" && "text-risk-critical bg-risk-criticalBg",
          )}>
            <Check size={10} />
            Demo inputs loaded. Editing is allowed; results are calculated when you evaluate.
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
              First data row loads available values; blanks stay missing
            </span>
          </span>
          <input
            id="sme-upload"
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            disabled={isLoading}
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
            <div className="flex items-center gap-2 mb-2.5 pb-1.5 border-b border-brand-border">
              <Icon size={11} className="text-brand-muted shrink-0" />
              <p className="text-[0.68rem] font-bold uppercase tracking-widest text-brand-muted">
                {label}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-x-3 gap-y-3">
              {groupFields.map((key) => (
                <div key={key} className="flex flex-col gap-1">
                  <label
                    htmlFor={`field-${key}`}
                    className="text-[0.67rem] leading-tight text-brand-subtext flex items-center gap-1"
                  >
                    <span className="flex-1" title={FEATURE_LABELS[key]}>
                      {FEATURE_LABELS[key]}
                    </span>
                    <InfoTooltip text={FIELD_TOOLTIPS[key]} />
                  </label>
                  <input
                    id={`field-${key}`}
                    type="number"
                    step="0.0001"
                    min="0"
                    max="1"
                    value={draft.values[key]}
                    disabled={isLoading || draft.availability[key] !== "available"}
                    placeholder="Not provided"
                    aria-invalid={readiness.invalid.some((item) => item.key === key)}
                    onChange={(e) => handleFieldChange(key, e.target.value)}
                    className="input-field text-right py-1.5 text-xs"
                  />
                  <select
                    aria-label={`Availability of ${FEATURE_LABELS[key]}`}
                    value={draft.availability[key]}
                    disabled={isLoading}
                    onChange={(e) => handleAvailabilityChange(key, e.target.value as Availability)}
                    className="input-field py-1.5 text-xs"
                  >
                    {Object.entries(AVAILABILITY_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* ── Evaluate CTA ─────────────────────────────────────────────────── */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={isLoading || !readiness.ready}
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
            {readiness.ready ? "Evaluate Risk" : "Complete Required Metrics"}
          </>
        )}
      </button>

    </div>
  );
}
