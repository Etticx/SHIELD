const { test, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const ts = require("typescript");

// Compile the actual pure input-handling modules for Node's built-in test runner.
const compiled = fs.mkdtempSync(path.join(os.tmpdir(), "shield-readiness-"));
for (const name of ["types", "constants", "readiness"]) {
  const source = fs.readFileSync(path.join(__dirname, "../src/lib", `${name}.ts`), "utf8");
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  });
  fs.writeFileSync(path.join(compiled, `${name}.js`), outputText);
}
after(() => {
  for (const name of ["types", "constants", "readiness"]) fs.unlinkSync(path.join(compiled, `${name}.js`));
  fs.rmdirSync(compiled);
});
const { createFinancialDraft, assessReadiness, toFinancialData, parseFinancialCsv, FINANCIAL_KEYS } = require(path.join(compiled, "readiness.js"));
const { PROFILE_HEALTHY, PROFILE_MODERATE, PROFILE_CRITICAL, PROFILE_DISTRESSED } = require(path.join(compiled, "constants.js"));
const key = FINANCIAL_KEYS[0];
const headerMap = { " ROA(C) before interest and depreciation before interest": key, " Debt ratio %": "debt_ratio_percent" };

test("manual entry has no invented financial values and cannot be evaluated", () => {
  const draft = createFinancialDraft();
  assert.equal(assessReadiness(draft).provided, 0);
  assert.equal(assessReadiness(draft).missing.length, 20);
  assert.throws(() => toFinancialData(draft), /Insufficient Data/);
});

test("zero is a valid observed value; clearing it makes it missing", () => {
  const draft = createFinancialDraft(PROFILE_HEALTHY);
  draft.values[key] = "0";
  assert.equal(toFinancialData(draft)[key], 0);
  draft.values[key] = "";
  assert.equal(assessReadiness(draft).ready, false);
  assert.throws(() => toFinancialData(draft));
});

test("every demo profile goes through the same completeness and conversion gate", () => {
  for (const profile of [PROFILE_HEALTHY, PROFILE_MODERATE, PROFILE_CRITICAL, PROFILE_DISTRESSED]) {
    const draft = createFinancialDraft(profile);
    assert.equal(assessReadiness(draft).ready, true);
    assert.deepEqual(toFinancialData(draft), profile);
  }
});

test("unavailable, inapplicable and short-history metrics block prediction even with a stale number", () => {
  for (const reason of ["unavailable", "not_applicable", "insufficient_history"]) {
    const draft = createFinancialDraft(PROFILE_HEALTHY);
    draft.availability[key] = reason;
    assert.equal(assessReadiness(draft).provided, 19);
    assert.throws(() => toFinancialData(draft));
  }
});

test("out-of-range and malformed input cannot reach the model", () => {
  for (const raw of ["-0.1", "1.1", "NaN", "Infinity", "0.5junk"]) {
    const draft = createFinancialDraft(PROFILE_HEALTHY);
    draft.values[key] = raw;
    assert.equal(assessReadiness(draft).invalid.length, 1);
    assert.throws(() => toFinancialData(draft));
  }
});

test("partial CSVs leave all omitted metrics missing", () => {
  const draft = parseFinancialCsv("Debt ratio %\n0.25", headerMap);
  assert.equal(assessReadiness(draft).provided, 1);
  assert.equal(draft.values[key], "");
  assert.equal(draft.values.debt_ratio_percent, "0.25");
  assert.throws(() => toFinancialData(draft));
});

test("CSV blanks stay missing, but an explicit zero stays available", () => {
  const draft = parseFinancialCsv('"ROA(C) before interest and depreciation before interest",Debt ratio %\n,0', headerMap);
  assert.equal(draft.values[key], "");
  assert.equal(draft.values.debt_ratio_percent, "0");
  assert.equal(assessReadiness(draft).provided, 1);
});

test("duplicate columns and invalid CSV numbers are rejected", () => {
  assert.throws(() => parseFinancialCsv("Debt ratio %,Debt ratio %\n0.2,0.3", headerMap), /Duplicate/);
  for (const raw of ["0.5junk", "2", "-1", "Infinity"]) {
    assert.throws(() => parseFinancialCsv(`Debt ratio %\n${raw}`, headerMap), /between 0 and 1/);
  }
});
