"""Build the standalone, explained Colab missing-data experiment notebook."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)})


def code(text):
    cells.append({"cell_type": "code", "metadata": {}, "source": text.splitlines(True),
                  "execution_count": None, "outputs": []})


md("""# SHIELD — Missing financial metrics: frozen Random Forest stress test

**Research question:** When an SME provides only 19, 18, 15, or 10 of the 20 required metrics,
how much do the existing model's detection performance and individual risk estimates change?

We load **the existing prototype RF**, preserve all 20 feature columns, and hide observed values with
`NaN`. We compare native RF handling with training-median imputation. **No model is retrained.**
The companies, labels, model and thresholds stay the same; the missing inputs and handling method change.

**Scope:** This measures sensitivity on the historical dataset, not eligibility for financing or deployment
readiness. The historical test split has already been used in development, so results are exploratory.
It does not establish accuracy for Malaysian SMEs, startups, or a different accounting period.
Risk probabilities from SMOTE training are not automatically calibrated real-world default probabilities.
The existing application's completeness gate is unchanged.
""")
md("""## 1. Install the model-compatible environment

Use a **CPU runtime**; a GPU is unnecessary. These core package versions match the saved RF and backend.
Use Python 3.10–3.12 for these pins. If Colab asks you to restart the runtime, restart and continue from
section 2. If section 4 reports a version mismatch, restart the session after installation.

Only load your own trusted `.joblib` artifact: loading it executes Python object deserialization.
""")
code("%pip install -q numpy==1.26.4 pandas==2.2.2 scikit-learn==1.6.1 imbalanced-learn==0.12.4 joblib==1.4.2 matplotlib==3.9.4\n")
md("""## 2. Select the project folder

Open this notebook in Colab. Put the following files in Google Drive, preserving these folder names.
The default folder is `/content/drive/MyDrive/SHIELD_Project`; change it if yours differs.

```text
SHIELD_Project/
  model/SHIELD_BestModel_RF_8020_CV10.joblib
  data/preprocessed_dataset.csv
  data/X_train_processed_8020.csv
  data/y_train_processed_8020.csv
  data/X_test_processed_8020.csv
  data/y_test_processed_8020.csv
```

You do **not** need to upload any helper Python files. The experiment functions are embedded below.
No new split is made for scoring: the source CSV is used to verify the existing split and recover the
original training companies for medians. File or split mismatches stop the experiment.
""")
code("""from pathlib import Path
try:
    from google.colab import drive
    drive.mount('/content/drive')
    PROJECT = Path('/content/drive/MyDrive/SHIELD_Project')
except ImportError:
    PROJECT = Path.cwd()
    if PROJECT.name == 'notebooks':
        PROJECT = PROJECT.parent

OUTPUT_BASE = PROJECT / 'reports' / 'missing_data'
print('Project:', PROJECT)
print('Results:', OUTPUT_BASE)
""")
md("""## 3. Freeze the experiment settings before viewing the results

- **20 single-metric cases:** each metric is missing for all test companies in turn.
- **Random missing inputs:** exactly 1, 2, 5, 10 or 20 values are hidden per company; identities vary
  between companies. Twenty seeded repetitions use identical masks for both handling methods.
- **Grouped proxies:** missing four-season EPS, all four selected share-based measures, or five
  leverage/solvency measures. These are controlled masks, not observed Malaysian missingness patterns.
- **Methods:** native `NaN` routing; median replacement using only verified original training rows.
- **Primary decision cutoff:** 0.60, matching SHIELD's high-risk flag. A fixed 0.50 reference is also
  reported for comparison with historical model evaluation. Neither cutoff is tuned here.
- **Risk tiers:** Low <0.30; Moderate 0.30–<0.60; High 0.60–<0.80; Critical >=0.80.
- **20 missing:** a no-information control, not a proposed supported input case.

Do not declare a missing-data policy acceptable just because it reproduces an already weak baseline.
Record your intended minimum detection performance and maximum false-alarm rate before reviewing results.
Formal policy selection should use development data followed by independent validation.
""")
code("""RANDOM_REPEATS = 20
MISSING_COUNTS = (1, 2, 5, 10, 20)
SEED = 42
BOOTSTRAP_DRAWS = 500
print('Predictions:', 1 + 2 * (20 + 3 + RANDOM_REPEATS * len(MISSING_COUNTS)))
print('No RF fitting, cross-validation search, or threshold optimisation.')
""")
md("""## 4. Load the experiment functions

The full tested runner is included in this cell. It verifies the model's exact feature names/order and
the saved labels. Original train/test membership must reproduce the saved numeric seed-42 stratified
80:20 split. Source values are checked within `1e-8` to allow the source CSV's decimal rounding.

The saved training file contains original rows followed by SMOTE-generated rows. Medians use only
the verified original prefix. SMOTE is never applied to test records or at prediction time.

**Why keep 20 columns?** Removing one column violates the saved model's schema. Keeping the column with
`NaN` tests absent information. When training did not include missing values, native RF routing uses
the child with more training samples; a successful prediction is not proof of robustness.
""")
runner = (ROOT / 'shield_missing_data.py').read_text(encoding='utf-8')
code(runner.split('\nif __name__ == "__main__":')[0])
md("""## 5. Verify inputs and demonstrate 19 columns versus 19 observed values

The first case below should produce a feature-schema error. The second keeps 20 columns with one `NaN`
and should produce a finite score. This is a technical smoke check on one company, not an accuracy test.
""")
code("""model, X_test, y_test, training_medians, source_rows, input_info = load_inputs(PROJECT)
display(pd.Series(input_info, name='Input verification'))
print('Test labels:', dict(zip(*np.unique(y_test, return_counts=True))))
try:
    score(model, X_test.iloc[[0]].drop(columns=[X_test.columns[0]]))
except ValueError as exc:
    print('19-column input rejected:', str(exc).splitlines()[0])
else:
    raise AssertionError('Unexpected: model accepted a removed feature column.')

example = X_test.iloc[[0]].copy()
complete_score = score(model, example)[0]
example.iloc[0, 0] = np.nan
missing_score = score(model, example)[0]
print(f'First company: complete={complete_score:.3f}; one NaN={missing_score:.3f}')
print('Both methods will now be compared across ALL test companies, not just demo profiles.')
""")
md("""## 6. Run the paired stress test

Default settings perform **247 prediction passes**, not 247 model trainings. Each pass scores the
same test companies. Results are written to a folder identified by model/data hashes, package versions
and settings. Identical inputs/settings reproduce the same folder; changed inputs/settings create a new one.
Each scenario appears at both fixed decision cutoffs in `scenario_metrics.csv`.

The same observed entries are kept for both methods. A recorded zero remains zero. Original input files
and the saved model are never overwritten. The median method is an experimental inference policy for this
existing RF; it is not a newly trained imputation-aware model.
""")
code("""RUN = run_experiment(
    PROJECT, output_base=OUTPUT_BASE, repeats=RANDOM_REPEATS,
    seed=SEED, missing_counts=MISSING_COUNTS, bootstrap_draws=BOOTSTRAP_DRAWS,
)
RESULTS = RUN['results']
OUT = RUN['output_dir']
print((OUT / 'READOUT.txt').read_text())
""")
md("""## 7. Read the complete-input baseline first

- **Recall:** fraction of labelled bankrupt companies detected. False negatives are missed bankrupt firms.
- **Precision:** fraction of flagged companies that are labelled bankrupt.
- **False-positive rate:** fraction of non-bankrupt companies incorrectly flagged.
- **Average precision (AP):** summarises the precision-recall curve; compare against the bankruptcy
  prevalence printed below. This is AP, not trapezoidal PR-AUC.
- **ROC-AUC:** ranking quality; interpret alongside AP for this heavily imbalanced dataset.
- **Brier score:** squared probability error; lower is better. It does not by itself prove calibration.
- **Accuracy:** secondary, because correctly labelling most non-bankrupt firms can hide weak recall.

There are only **44 bankrupt test companies** in the current saved split. One changed detection moves
recall by about **2.27 percentage points**. Bootstrap intervals are conditional on this test set and its
class balance; they do not correct prior test reuse or domain mismatch.
""")
code("""DISPLAY_METRICS = ['threshold', 'accuracy', 'precision', 'recall', 'average_precision',
                   'roc_auc', 'brier', 'false_positive_rate', 'tp', 'fn', 'fp', 'tn']
display(RESULTS[RESULTS.family == 'baseline'][DISPLAY_METRICS].round(4))
print(f'Bankruptcy prevalence / constant-score AP reference: {y_test.mean():.4f}')
display(pd.read_csv(OUT / 'baseline_bootstrap.csv').round(4))
""")
md("""## 8. Which individual missing metric matters most?

Every company has 19 observed metrics in these tests. Rows differ in WHICH metric is absent.
`recall_change_pp` and `average_precision_change_pp` are percentage-point changes from complete inputs.
`newly_missed_bankrupt` counts firms detected by the baseline but missed after masking; recoveries are
reported separately so improvements cannot hide newly missed firms. Tier changes are disagreements with
the complete-input model, not evidence that either tier is correct.
""")
code("""PRIMARY = RESULTS[RESULTS.threshold == 0.60]
SINGLE = PRIMARY[PRIMARY.family == 'single'].copy()
columns = ['scenario', 'method', 'recall', 'recall_change_pp', 'precision',
           'average_precision', 'average_precision_change_pp', 'fn', 'newly_missed_bankrupt',
           'newly_detected_bankrupt', 'tier_change_pct', 'mean_probability_change_pp']
display(SINGLE.sort_values(['recall_change_pp', 'average_precision_change_pp'])[columns].round(4))
""")
md("""## 9. How does performance change as more inputs disappear?

Random masks are independent of the true class, so they are a controlled random-missing experiment.
Real missingness may relate to distress, bookkeeping practices, business age or legal structure.
Twenty masks on the same companies are **not twenty independent datasets**. Their min/max and standard
deviation describe sensitivity to mask choice, not a confidence interval for population accuracy.
Recall can rise simply because more companies are flagged. Check the false-positive rate and AP
alongside recall; the all-missing control makes this failure mode visible.
""")
code("""random_summary = pd.read_csv(OUT / 'random_summary.csv')
display(random_summary[random_summary.threshold == .60][[
    'missing_count', 'method', 'recall_mean', 'recall_min', 'recall_max',
    'average_precision_mean', 'brier_mean', 'false_positive_rate_mean', 'tier_change_pct_mean',
    'mean_probability_change_pp_mean', 'newly_missed_bankrupt_mean',
]].round(4))
plot_results(OUT)
""")
md("""## 10. New-business and missing-record proxies

These grouped cases remove related information together. They do **not** simulate a complete startup
population. A truly undefined share-based metric or nonexistent four-quarter history is different from
an unreported, otherwise meaningful value. Median imputation in this notebook is only a stress-test
comparison and does not establish that imputing structurally undefined ratios is suitable.
""")
code("""display(PRIMARY[PRIMARY.family == 'group'][[
    'scenario', 'missing_count', 'method', 'recall', 'recall_change_pp',
    'precision', 'average_precision', 'fn', 'fp', 'newly_missed_bankrupt',
    'tier_change_pct', 'mean_probability_change_pp',
]].round(4))
""")
md("""## 11. Inspect individual companies and export the evidence

The detailed output uses numeric source-row IDs, not company names. Pick a method/scenario below to see
which risk estimates moved the most. Do not interpret the changed score alone as model accuracy; use the
true label and full-set metrics. The compressed CSV contains all scenario/company predictions and the
exact names of the hidden metrics, so a result can be reproduced and explained.

Outputs: metrics for all scenarios, random-repeat summaries, complete-input predictions, individual
predictions, original-training medians, mask hashes, baseline bootstrap intervals, figures, run metadata,
and a plain-language readout. The ZIP excludes the saved model and original source data.
""")
code("""predictions = pd.read_csv(OUT / 'company_predictions.csv.gz')
inspection = predictions[(predictions.family == 'group') &
                         (predictions.scenario == 'share_based_unavailable') &
                         (predictions.method == 'native_nan')].copy()
inspection['change_pp'] = (inspection.probability - inspection.complete_probability) * 100
display(inspection.loc[inspection.change_pp.abs().sort_values(ascending=False).index].head(15))

import shutil
zip_path = shutil.make_archive(str(OUT.parent / f'SHIELD_missing_data_{RUN["config"]["run_id"]}'),
                               'zip', root_dir=OUT)
print('Results ZIP:', zip_path)
# Download when you are ready in Colab:
# from google.colab import files
# files.download(zip_path)
""")
md("""## 12. What can we conclude, and what comes next?

Write down the baseline first, then the largest single-feature damage, the random-missing trend,
the grouped-pattern damage, and how the two handling methods differ. Report exact missed-bankrupt and
false-alarm counts, not just a high accuracy percentage. A method can preserve recall while sharply
increasing false alarms or shifting risk tiers.

This notebook answers **how the frozen RF reacts**; it does not automatically approve incomplete profiles.
Use the following next steps:

1. Predefine acceptable absolute recall/false-alarm performance and allowable deterioration with your
   supervisor. If the complete-input baseline is inadequate, missing-data tolerance does not fix it.
2. Treat these results as exploratory. Select handling policies using training/development data, then
   validate the frozen policy on genuinely fresh companies; repeated historical test reuse limits claims.
3. If necessary, separately train an imputation-aware or missingness-aware model, fitting preprocessing
   inside training folds. That is a new modelling experiment, not something this notebook does.
4. Validate on representative Malaysian SMEs, including startup/structure-specific patterns. Artificially
   hiding values in mature-company records does not establish startup suitability.
5. Before enabling incomplete inputs, test the full API, SHAP, advisory text and report path. Explanations
   must identify missing/imputed metrics and must not present imputed values as observed financial facts.

**Retain the current Insufficient Data gate until a justified policy has been validated.**

### Technical references

- [RandomForestClassifier 1.6: native missing-value routing](https://scikit-learn.org/1.6/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
- [scikit-learn: leakage and preprocessing using training data only](https://scikit-learn.org/stable/common_pitfalls.html)
- [imbalanced-learn Pipeline: sampling during fit](https://imbalanced-learn.org/stable/references/generated/imblearn.pipeline.Pipeline.html)
- [scikit-learn: average precision](https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.average_precision_score.html)
""")

notebook = {
    "cells": cells,
    "metadata": {"colab": {"name": "SHIELD_Missing_Data_Stress_Test.ipynb", "provenance": []},
                 "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                 "language_info": {"name": "python", "version": "3.12"}},
    "nbformat": 4, "nbformat_minor": 5,
}
for i, cell in enumerate(cells):
    cell["id"] = f"missing-data-{i:02d}"
output = ROOT / 'SHIELD_Missing_Data_Stress_Test.ipynb'
output.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print(f'Wrote {output} ({len(cells)} cells)')
