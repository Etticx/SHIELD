# Five accounting inputs to the seven-feature RF: conversion audit

Checked: 28 October 2026. This investigation does not change the website,
backend configuration, production model, or training data.

## Result

The proposed five-field interface is feasible as an accounting calculator.
However, a verified conversion from those calculated ratios into the downloaded
model's training representation has not been found. Do not pass raw ratios to
that model as if they reproduced the experiment's inputs and performance.

The unknown conversion was already present in the source dataset; it was not
created by the seven-feature Colab training code.

## Direct checks performed

1. Downloaded the official UCI archive and compared all 6,819 rows and all
   95 predictors plus the target with the local Excel file.
2. Removed only the local `Company` identifier for comparison; stripped header
   whitespace; mapped `Bankrupt?` to `Bankrupt`; removed the currency suffix from
   three per-share column names. Row order was preserved.
3. Every value matches at absolute tolerance `1e-12`, relative tolerance zero.
   The maximum absolute difference is approximately `9.91e-17`. Labels are
   identical. Despite its local filename, this spreadsheet contains the released
   UCI Taiwanese benchmark values, not a distinct Italian 2023 data sample.
4. The official ZIP contains only `data.csv`. It contains no raw accounting
   amounts, raw feature minima/maxima, or fitted scaler artifact.
5. Inspected `notebooks/preprocessing_shield.py` and the seven-feature experiment
   notebook/builder. They read existing columns, select features, split, and fit
   SMOTE/classifiers. The seven-feature RF route does not fit a raw-ratio scaler.
6. Loaded the user-provided `SHIELD_RF_7Features_SMOTE050_8020_CV5.joblib`.
   Its pipeline is `SMOTE -> RandomForestClassifier`, with seven feature names in
   the order below. It does not contain a raw-accounting conversion step.
7. Its RF has 200 trees, maximum depth 6, minimum split size 2, and seed 42.
   Loading it in the backend environment emits scikit-learn version warnings:
   the estimator was saved with 1.9.0, while the environment has 1.6.1. Runtime
   compatibility is a second task, separate from the input conversion.

Machine-readable comparison and source hashes: `uci_comparison.json`.
Observed released-data ranges: `seven_training_column_ranges.csv`.

## Proposed calculator formulas, in actual model-column order

Let NI = annual net income, A = total assets, L = total liabilities,
E = total shareholders' equity, and RE = retained earnings/accumulated losses.
All five amounts must use consistent entity scope, currency and reporting period.
These are conventional end-balance calculator definitions, not verified exact
historical donor definitions or a recovered input conversion.

| Model column | Conventional candidate formula |
| --- | --- |
| Net Income to Stockholder's Equity | NI / E |
| Net Income to Total Assets | NI / A |
| Retained Earnings to Total Assets | RE / A |
| Debt ratio % | L / A as a fraction; historical percent convention unresolved |
| Net worth/Assets | E / A |
| Equity to Liability | E / L |
| Liability to Equity | L / E |

Annual income versus ending/average balances, equity ownership scope, and
negative-equity/sign conventions must also match the historical definitions.
Missing values must not become zero. Zero denominators are undefined, not zero
ratios. Losses and negative equity must not be silently clamped into [0, 1].

## Why the dataset values are not interchangeable with raw ratios

All seven released columns have observed minimum 0 and maximum 1. Their medians
include approximately 0.841179 for NI/equity, 0.810619 for NI/assets and 0.937672
for RE/assets. These bounds describe the released representation, not known raw
accounting bounds.

For conventionally consistent raw ratios, NI/E = (NI/A) / (E/A), when the
denominators are nonzero and the balance conventions agree. The released columns
do not satisfy that identity: the median absolute residual is approximately
0.075968. This is a diagnostic of representation/definition incompatibility;
it cannot identify a unique historical transformation.

For example, if a raw ratio of 0.10 were mapped using raw bounds [-1, 1], its
min-max value would be 0.55. With raw bounds [-4, 1], it would be 0.82. Both
transformations produce a [0, 1] representation, but different model inputs.
The released column's own bounds of [0, 1] do not tell us which mapping was used.
These numerical bounds are illustrations, not estimates for this dataset.

## Primary-source findings and their limits

- [UCI dataset record](https://archive.ics.uci.edu/dataset/572/taiwanese+bankruptcy+prediction)
  identifies the Taiwan Economic Journal, 1999-2009, 6,819 observations and 95
  predictors. Its variable appendix names the relevant accounting concepts,
  but the checked record and downloaded archive do not supply the seven raw
  normalization parameter pairs.
- [Liang et al., 2016, author-hosted paper](https://isslab.csie.ncu.edu.tw/download/publications/1.pdf),
  section 3.1, describes per-feature min-max normalization. Importantly, that
  paper uses 478 selected companies, including governance variables; it does not
  establish the exact fitted transformation of the 6,819-row UCI release. No
  applicable raw minima/maxima were recovered from this source.

## What completes the requested application flow

Preferred: obtain the original donor preprocessing specification, raw bounds or
fitted transformation for these exact released columns, with matched raw/encoded
examples to verify all seven mappings. Then add that deterministic conversion to
the backend and check inference parity with the notebook in a compatible runtime.

Alternative: obtain labelled data expressed in reproducible raw accounting ratios
and retrain/evaluate a model using the same five-to-seven calculator definitions.
That creates a new experiment; the present model's reported recall and precision
cannot be carried over automatically.

Fitting a new scaler to the already encoded CSV, normalizing the seven numbers
within a single company, using arbitrary bounds, percentile mapping without
validation, or guessing the original bounds does not recover the missing mapping.

The requested separate `/backlog` page should show the five entered amounts,
formula substitutions, seven raw ratios, exact conversion and ordered model
vector, model identity, output and risk-band decision. It should update when
inputs change and clear stale results. Until the conversion is verified, the
trace must mark that step as unresolved rather than invent model-ready values.

## Reproduce the data comparison

From the SHIELD root, using the existing environment with the Excel reader:

```powershell
.\backend\venv\Scripts\python.exe reports\input_transformation_audit\audit_training_representation.py
```

The script reads the cached official `uci_release.zip` if present; otherwise it
fetches the public UCI URL with normal certificate validation. It writes the JSON
audit and seven-column range CSV, and fails if values differ beyond tolerance.
The public dataset is credited to the UCI Taiwanese Bankruptcy Prediction
release (2020), DOI 10.24432/C5004D, licensed CC BY 4.0 on the UCI record.
