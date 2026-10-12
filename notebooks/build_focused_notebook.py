"""Rebuild the self-contained Colab notebook from the tested experiment runner."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)})


def code(text):
    cells.append({"cell_type": "code", "metadata": {}, "source": text.splitlines(True),
                  "execution_count": None, "outputs": []})


md("""# SHIELD — Focused precision and recall improvement

**Question:** can the current financial predictors support **at least 70% precision and 70% recall together**?

This focused round uses **one stratified 80:20 split and 5-fold CV within its training partition**.
It does not repeat the 176-experiment matrix. Nine declared RF/XGBoost candidates compare the strongest
historical settings, no SMOTE, a weighted RF, and two small RF parameter changes.

Information Gain (top 20) and SMOTE are fitted inside each training fold. Each original training company
gets one out-of-fold score from a model that did not train on that company. Thresholds and the candidate
are selected from those scores, then frozen before holdout evaluation.

**Interpretation:** the OOF scores are used for tuning, so selected OOF precision/recall are not an unbiased
final estimate. Your old 80:20 holdout has already been used in many experiments. Further evaluation on it
is explicitly exploratory; new/external companies are needed for a genuinely fresh final assessment.
Changing the seed does not erase previous test reuse. This notebook does not introduce nested CV.

The exported research candidate does not replace the prototype model or alter its risk bands.
""")
md("## 1. Install dependencies\nThe runner records package versions. These modelling versions match the verified local run.")
code("%pip install -q scikit-learn==1.9.0 imbalanced-learn==0.14.2 xgboost==2.0.3 openpyxl matplotlib joblib\n")
md("""## 2. Choose the data and output folder
Use the original Excel file, or a CSV with **all original numeric predictors and original class counts**.
Do not upload the IG-selected or SMOTE-resampled training CSVs. Only `Bankrupt` is the target.
""")
code("""from pathlib import Path
try:
    from google.colab import drive
    drive.mount('/content/drive')
    RAW_PATH = Path('/content/drive/MyDrive/SHIELD_Project/data/bankruptcy_italian_companies_2023.xlsx')
    OUTPUT_BASE = Path('/content/drive/MyDrive/SHIELD_Project/reports/focused_improvement')
except ImportError:
    PROJECT = Path.cwd()
    if PROJECT.name == 'notebooks':
        PROJECT = PROJECT.parent
    RAW_PATH = PROJECT / 'data' / 'bankruptcy_italian_companies_2023.xlsx'
    OUTPUT_BASE = PROJECT / 'reports' / 'focused_improvement'

print('Input:', RAW_PATH)
print('Output:', OUTPUT_BASE)
""")
md("""## 3. Experiment functions
This cell embeds the tested local runner, so the notebook works without uploading any Python helper files.
Fold checkpoints and pipeline caching save time. Their folder is isolated by data, configuration,
package versions and candidate parameters. Changing a setting starts a separate run.
""")
runner = (ROOT / "shield_focused_improvement.py").read_text(encoding="utf-8")
code(runner.split('\nif __name__ == "__main__":')[0])
md("""## 4. Settings and declared candidates
The first stage examines thresholds. The small additional comparisons use the same folds.
Set `include_leaf_variants=False` for seven rather than nine candidates.

**Threshold rule:** if both 70% targets are achievable on training OOF scores, select the threshold
with the highest F2 among those qualifying thresholds. Otherwise select the highest F2 while maintaining
recall of at least 70%, and report that the joint target was not achieved. F2 gives greater weight to recall.
Candidate selection follows the same rule and uses training OOF results only.

Set `evaluate_holdout=False` to inspect training curves without evaluating the historical holdout.
This changes the run fingerprint. Keep settings fixed before reading holdout results.
""")
code("""CONFIG = Config(
    seed=42,
    folds=5,
    test_size=0.20,
    top_k=20,
    smote_neighbors=5,
    target_precision=0.70,
    target_recall=0.70,
    model_jobs=2,
    include_leaf_variants=True,
    evaluate_holdout=True,
)
SPECS = candidate_specs(CONFIG.include_leaf_variants)
display(pd.DataFrame(SPECS))
print(f'{len(SPECS)} candidates x {CONFIG.folds} CV folds = {len(SPECS)*CONFIG.folds} training-fold fits')
print('No hyperparameter grid search. Holdout refits are limited to the frozen choice and RF reference.')
""")
md("## 5. Load and check the original data\nThe financial predictors must remain numeric. No nominal conversion of ratios.")
code("""if not RAW_PATH.exists():
    raise FileNotFoundError(f'Update RAW_PATH to your original data file: {RAW_PATH}')
RAW = pd.read_excel(RAW_PATH) if RAW_PATH.suffix.lower() in ['.xlsx', '.xls'] else pd.read_csv(RAW_PATH)
X_CHECK, Y_CHECK = clean_data(RAW, CONFIG.top_k)
print('Raw shape:', RAW.shape)
print('Predictor shape after removing Company and constants:', X_CHECK.shape)
print('Original target counts:', Y_CHECK.value_counts().sort_index().to_dict())
print('Missing values, infinities, repeated company IDs and duplicate predictors checked.')
""")
md("""## 6. Run the focused round
Every company's OOF score comes from its held-out training fold. IG and SMOTE are never fitted using
that fold. The pipeline is then refitted on the complete training partition for holdout prediction.
Training folds can select different 20-feature sets; the final fitted model has one saved feature list.

**Default 0.5 and selected cutoffs use `score >= cutoff` throughout**, including tied scores.
SMOTE model scores are uncalibrated: a cutoff of 0.30 does not establish a 30% real-world bankruptcy probability.
""")
code("""RUN = run_focus(RAW, OUTPUT_BASE, CONFIG, source_note=str(RAW_PATH), specs=SPECS)
REPORT_DIR = RUN['output_dir']
print('Frozen choice:', RUN['choice'])
""")
md("""## 7. Training-CV metrics — same headline columns, separate tuning labels
Precision, recall and F scores refer to **Bankrupt (1)**. ROC-AUC and average precision do not change
when only the classification threshold changes. `CV_F1_Mean (%)` is mean fold F1 at the displayed cutoff;
the selected cutoff itself was chosen using the pooled OOF predictions.
""")
code("""HEADLINE_COLUMNS = ['Model', 'Experiment', 'Split', 'CV', 'Accuracy (%)', 'Precision (%)',
                    'Recall (%)', 'F1-Score (%)', 'ROC-AUC (%)', 'Best_Params', 'CV_F1_Mean (%)']
EXTRA_COLUMNS = ['Candidate', 'SMOTE_Ratio', 'Decision_Rule', 'Threshold', 'F2-Score (%)',
                 'Average Precision (%)', 'Both_Targets_Feasible_OOF',
                 'Max_Precision_At_Target_Recall (%)', 'TP', 'FP', 'FN', 'TN', 'Evaluation']
display(RUN['training_results'][HEADLINE_COLUMNS + EXTRA_COLUMNS])
selected_rows = RUN['training_results'].query("Decision_Rule == 'OOF selected'")
print('Any candidate reaches BOTH targets on its training OOF curve:',
      bool(selected_rows['Both_Targets_Feasible_OOF'].any()))
print('These are threshold-selection results, not independent final performance.')
""")
md("""## 8. Visualise the achievable precision–recall combinations
The upper-right area beyond both dashed 70% lines is the joint target region.
If a candidate never enters that region, threshold changes alone cannot achieve both targets on these OOF scores.
This does not prove a permanent limit for the dataset or all possible models.
""")
code("""from IPython.display import Image, display
display(Image(filename=str(REPORT_DIR / 'training_precision_recall.png')))
for candidate in dict.fromkeys(['RF_SMOTE025', RUN['choice']['Candidate']]):
    display(Image(filename=str(REPORT_DIR / f'{candidate}_threshold_curve.png')))
""")
md("""## 9. Frozen-choice holdout report
The classifier and cutoff were chosen before evaluating this split. However, these same companies were
used in previous rounds, so this remains **exploratory historical-holdout evaluation**.
The report also includes approximate 95% Wilson intervals because 44 bankrupt test companies give limited precision.
Intervals describe sampling uncertainty; they do not correct historical selection bias.
""")
code("""if len(RUN['holdout_results']):
    display(RUN['holdout_results'])
    chosen = RUN['holdout_results'].query("Decision_Rule == 'Frozen OOF threshold'").iloc[0]
    both = chosen['Precision (%)'] >= 70 and chosen['Recall (%)'] >= 70
    print('Both targets met on this historical holdout:', both)
    print(f"Frozen result: Precision {chosen['Precision (%)']:.2f}% | Recall {chosen['Recall (%)']:.2f}% | F1 {chosen['F1-Score (%)']:.2f}%")
    print('Do not adjust the threshold again using this holdout result.')
else:
    print('Holdout evaluation disabled by CONFIG; review the saved training curves.')
""")
md("""## 10. Saved files and next decision
`FOCUSED_RESULTS.txt` contains a readable record. CSV/JSON files retain full numerical precision.
The run folder includes the declared settings, package versions, fold membership, OOF predictions,
exact threshold tables, per-fold features and figures. If holdout evaluation is enabled, it also includes
the research pipeline and its fixed 20-feature manifest with the frozen threshold.

If the joint target is absent, report the measured trade-off and decide with your supervisor what precision
and alert workload are acceptable at the required recall. Do not repeat seeds until a favourable result appears.
New data, feature quality and label meaning remain the next avenues; adding many models offers no guarantee.

References:
- [scikit-learn: threshold tuning](https://scikit-learn.org/stable/modules/classification_threshold.html)
- [imbalanced-learn: resampling leakage](https://imbalanced-learn.org/stable/common_pitfalls.html)
""")
code("""print((REPORT_DIR / 'FOCUSED_RESULTS.txt').read_text(encoding='utf-8'))
print('Reports:', REPORT_DIR)
print('The deployed SHIELD model and risk bands have not been changed.')
""")

notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12"},
    "colab": {"provenance": []}, "shield_version": "shield-focused-threshold-v2",
}, "cells": cells}
for i, cell in enumerate(cells):
    cell["id"] = f"focus-{i:02d}"
    if cell["cell_type"] == "code":
        source = ''.join(cell["source"])
        if not source.startswith('%pip'):
            compile(source, f"cell_{i}", "exec")
path = ROOT / "SHIELD_Focused_Improvement.ipynb"
path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + '\n', encoding="utf-8")
print(f"Wrote {path}: {len(cells)} cells; Python cells compile.")
