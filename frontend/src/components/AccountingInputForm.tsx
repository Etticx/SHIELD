"use client";

import InfoTooltip from "@/components/InfoTooltip";
import { ACCOUNTING_FIELDS, assessReadiness, toFinancialData } from "@/lib/accounting-inputs";
import type { AccountingData, FinancialDraft } from "@/lib/accounting-inputs";

interface Props {
  draft: FinancialDraft;
  onDraftChange: (draft: FinancialDraft) => void;
  onEvaluate: (data: AccountingData) => void;
  isLoading: boolean;
}

const FEATURE_HELP: Record<keyof AccountingData, string> = {
  net_income_to_stockholders_equity:
    "Compares the company's net profit or loss with shareholders' equity (the owners' interest in the company). It describes profitability relative to owners' funds.",
  net_income_to_total_assets:
    "Compares net profit or loss with total assets. It describes how much profit the company generates relative to the assets it holds.",
  retained_earnings_to_total_assets:
    "Compares accumulated profits kept in the business, after distributions, with total assets. Retained earnings can also reflect accumulated losses.",
  debt_ratio_percent:
    "Compares total liabilities with total assets. It describes the extent to which the company's assets are financed by obligations to creditors.",
  net_worth_assets:
    "Compares shareholders' equity with total assets. Equity is the owners' remaining interest after liabilities are deducted from assets.",
  equity_to_liability:
    "Compares shareholders' equity with total liabilities. It describes the amount of owners' funds relative to the company's obligations.",
  liability_to_equity:
    "Compares total liabilities with shareholders' equity. It describes financial leverage: the company's obligations relative to owners' funds.",
};

export default function AccountingInputForm({ draft, onDraftChange, onEvaluate, isLoading }: Props) {
  const readiness = assessReadiness(draft);
  return (
    <form className="p-5 space-y-5" onSubmit={(event) => {
      event.preventDefault();
      if (readiness.ready) onEvaluate(toFinancialData(draft));
    }}>
      <div className="space-y-4">
        {(Object.keys(ACCOUNTING_FIELDS) as Array<keyof AccountingData>).map((key) => (
          <div key={key}>
            <div className="flex items-center justify-between gap-2 text-xs text-brand-muted">
              <label htmlFor={`seven-ratio-${key}`}>{ACCOUNTING_FIELDS[key]}</label>
              <InfoTooltip text={FEATURE_HELP[key]} size={13} />
            </div>
            <input
              id={`seven-ratio-${key}`}
              name={key}
              required type="number" step="any" min="0" max="1"
              value={draft.values[key] ?? ""}
              onChange={(event) => onDraftChange({ values: { ...draft.values, [key]: event.target.value } })}
              className="mt-1 w-full border border-brand-border rounded-lg px-3 py-2 text-sm text-brand-charcoal bg-white"
            />
          </div>
        ))}
      </div>
      {readiness.invalid.length > 0 && (
        <p role="alert" className="text-xs text-red-700">Use numbers between 0 and 1 for all seven feature values.</p>
      )}
      <button type="submit" disabled={!readiness.ready || isLoading} className="w-full rounded-lg bg-brand-yellow py-3 font-bold text-sm disabled:opacity-40">
        {isLoading ? "Evaluating…" : "Evaluate Risk"}
      </button>
    </form>
  );
}
