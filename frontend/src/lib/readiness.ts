import { FEATURE_LABELS } from "./constants";
import type { SMEFinancialData } from "./types";

export type ProfileKey = "manual" | "healthy" | "moderate" | "critical" | "distressed";
export type Availability = "available" | "unavailable" | "not_applicable" | "insufficient_history";
export type FinancialKey = keyof SMEFinancialData;

export interface FinancialDraft {
  values: Record<FinancialKey, string>;
  availability: Record<FinancialKey, Availability>;
  profile: ProfileKey;
}

export const FINANCIAL_KEYS = Object.keys(FEATURE_LABELS) as FinancialKey[];
export const AVAILABILITY_LABELS: Record<Availability, string> = {
  available: "Value available",
  unavailable: "Not available",
  not_applicable: "Not applicable",
  insufficient_history: "Not enough history",
};

export function createFinancialDraft(
  financials?: SMEFinancialData,
  profile: ProfileKey = "manual",
): FinancialDraft {
  return {
    values: Object.fromEntries(FINANCIAL_KEYS.map((key) => [
      key, financials ? String(financials[key]) : "",
    ])) as FinancialDraft["values"],
    availability: Object.fromEntries(FINANCIAL_KEYS.map((key) => [key, "available"])) as FinancialDraft["availability"],
    profile,
  };
}

export function assessReadiness(draft: FinancialDraft) {
  const missing: Array<{ key: FinancialKey; label: string; reason: string }> = [];
  const invalid: Array<{ key: FinancialKey; label: string }> = [];
  for (const key of FINANCIAL_KEYS) {
    const availability = draft.availability[key];
    const raw = draft.values[key].trim();
    if (availability !== "available" || raw === "") {
      missing.push({ key, label: FEATURE_LABELS[key], reason: availability === "available" ? "Not provided" : AVAILABILITY_LABELS[availability] });
    } else {
      const value = Number(raw);
      if (!Number.isFinite(value) || value < 0 || value > 1) {
        invalid.push({ key, label: FEATURE_LABELS[key] });
      }
    }
  }
  return {
    ready: missing.length === 0 && invalid.length === 0,
    provided: FINANCIAL_KEYS.length - missing.length - invalid.length,
    missing,
    invalid,
  };
}

/** Only complete, valid inputs can cross the boundary to the prediction API. */
export function toFinancialData(draft: FinancialDraft): SMEFinancialData {
  if (!assessReadiness(draft).ready) throw new Error("Insufficient Data: complete all 20 required metrics before evaluation.");
  return Object.fromEntries(FINANCIAL_KEYS.map((key) => [key, Number(draft.values[key])])) as unknown as SMEFinancialData;
}

/** Partial uploads replace the whole draft; omitted values remain missing. */
export function parseFinancialCsv(
  text: string,
  headerMap: Record<string, FinancialKey>,
): FinancialDraft {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter((line) => line.trim());
  if (lines.length < 2) throw new Error("File has no data rows.");
  const cleanCell = (cell: string) => cell.trim().replace(/^"(.*)"$/, "$1").trim();
  const headers = lines[0].split(",").map(cleanCell);
  const values = lines[1].split(",").map(cleanCell);
  const draft = createFinancialDraft();
  let recognised = 0;
  for (const [header, key] of Object.entries(headerMap)) {
    const matches = headers.flatMap((value, index) => value === header.trim() ? [index] : []);
    if (matches.length > 1) throw new Error(`Duplicate column: "${header.trim()}".`);
    if (matches.length === 0) continue;
    recognised++;
    const raw = values[matches[0]] ?? "";
    if (!raw) continue;
    const value = Number(raw);
    if (!Number.isFinite(value) || value < 0 || value > 1) {
      throw new Error(`"${header.trim()}" must be a normalised number between 0 and 1, or left blank.`);
    }
    draft.values[key] = raw;
  }
  if (recognised === 0) throw new Error("No recognised financial columns. Use the CSV template headers.");
  return draft;
}
