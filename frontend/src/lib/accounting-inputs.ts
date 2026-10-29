export const ACCOUNTING_FIELDS = {
  net_income_to_stockholders_equity: "Net Income to Stockholder's Equity",
  net_income_to_total_assets: "Net Income to Total Assets",
  retained_earnings_to_total_assets: "Retained Earnings to Total Assets",
  debt_ratio_percent: "Debt ratio %",
  net_worth_assets: "Net worth/Assets",
  equity_to_liability: "Equity to Liability",
  liability_to_equity: "Liability to Equity",
};
export type AccountingData = Record<keyof typeof ACCOUNTING_FIELDS, number>;
export interface FinancialDraft { values: Record<keyof AccountingData,string>; }
const keys = Object.keys(ACCOUNTING_FIELDS) as Array<keyof AccountingData>;
export function createFinancialDraft(): FinancialDraft { return {values:Object.fromEntries(keys.map(k=>[k,""])) as FinancialDraft["values"]}; }
export function assessReadiness(draft: FinancialDraft) {
  const missing = keys.filter(k=>!draft.values?.[k]?.trim());
  const invalid = keys.filter(k=>!missing.includes(k) && (!Number.isFinite(Number(draft.values[k])) || Number(draft.values[k])<0 || Number(draft.values[k])>1));
  return {ready:!missing.length&&!invalid.length,provided:keys.length-missing.length-invalid.length,missing,invalid};
}
export function toFinancialData(draft: FinancialDraft): AccountingData {
  if(!assessReadiness(draft).ready)throw new Error('Complete all seven dataset feature values using numbers between 0 and 1.');
  return Object.fromEntries(keys.map(k=>[k,Number(draft.values[k])])) as AccountingData;
}
