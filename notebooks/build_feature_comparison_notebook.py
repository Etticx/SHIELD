"""Build a self-contained Colab notebook for all features versus IG top 20."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
cells=[]


def md(text):
    cells.append(dict(cell_type="markdown",metadata={},source=text.splitlines(True)))


def code(text):
    cells.append(dict(cell_type="code",metadata={},source=text.splitlines(True),execution_count=None,outputs=[]))


md("""# SHIELD — All financial predictors versus IG top 20

The original file has **97 columns**: `Company`, `Bankrupt`, and **95 financial predictors**.
`Company` is an identifier and `Bankrupt` is the target: neither is an input feature.
The all-feature arm retains **all 95 financial predictors**, including constant `Net Income Flag`,
and **does not apply IG**. The comparison arm follows the original cleaning and selects top 20 by IG.

Compare the same nine RF/XGBoost candidates using the same stratified **80:20 split**, seed 42,
and **5-fold training CV**. SMOTE is fitted only on training folds. Evaluate default 0.5 cutoffs and
thresholds selected using training out-of-fold predictions. Parameters are fixed; no large grid search.

**Question:** does removing the top-20 restriction improve the precision–recall trade-off,
particularly whether both can reach 70% together? The comparison uses matched companies and folds.
Models, the prototype input fields and risk bands are not changed automatically.

OOF scores are used for threshold/model selection and are therefore tuning scores. The historical
holdout has been examined before, so further results on it remain exploratory.
""")
md("## 1. Dependencies\nThese modelling versions match the verified local environment; versions are recorded per run.")
code("%pip install -q scikit-learn==1.9.0 imbalanced-learn==0.14.2 xgboost==2.0.3 openpyxl matplotlib joblib\n")
md("""## 2. Paths
Use the **original Excel file**. A previously cleaned CSV might already have removed a financial predictor.
Do not use SMOTE-resampled or IG-selected arrays as input.
""")
code("""from pathlib import Path
from IPython.display import Image, display
try:
    from google.colab import drive
    drive.mount('/content/drive')
    RAW_PATH=Path('/content/drive/MyDrive/SHIELD_Project/data/bankruptcy_italian_companies_2023.xlsx')
    OUTPUT_BASE=Path('/content/drive/MyDrive/SHIELD_Project/reports/feature_comparison')
except ImportError:
    PROJECT=Path.cwd()
    if PROJECT.name=='notebooks':
        PROJECT=PROJECT.parent
    RAW_PATH=PROJECT/'data'/'bankruptcy_italian_companies_2023.xlsx'
    OUTPUT_BASE=PROJECT/'reports'/'feature_comparison'

# Default: run both matched arms. Optionally reuse a completed IG run only if its
# data fingerprint, model settings and package versions match exactly.
PRIOR_IG_DIR=None
print('Input:',RAW_PATH)
print('Reports:',OUTPUT_BASE)
""")
md("## 3. Experiment runner\nEmbedded here so no helper Python files need uploading to Colab.")
runner=(ROOT/'shield_focused_improvement.py').read_text(encoding='utf-8').split('\nif __name__ == "__main__":')[0]
code(runner)
md("## 4. Matched comparison functions\nReused IG results must pass strict data/settings/package checks; fold membership is verified explicitly.")
comparison=(ROOT/'shield_feature_comparison.py').read_text(encoding='utf-8').split('\nif __name__ == "__main__":')[0]
comparison=comparison.replace('from shield_focused_improvement import (\n    Config, candidate_specs, clean_data, data_fingerprint, run_focus,\n)\n', '# Experiment functions were defined in the preceding cell.\n')
code(comparison)
md("""## 5. Fixed settings and data checks
Threshold selection first looks for both precision and recall >=70%. If unavailable, it maximizes F2
subject to recall >=70%. This fallback does **not** achieve the joint target.
Every candidate is tested at default 0.5 as well, which lets you compare the feature sets without changing the cutoff.

RF `max_features='sqrt'` or `0.5` naturally considers a different number of inputs when the feature count changes.
The parameter setting remains fixed between arms. No additional scaling is introduced in this comparison.
""")
code("""CONFIG=Config(seed=42,folds=5,test_size=.20,top_k=20,smote_neighbors=5,
              target_precision=.70,target_recall=.70,model_jobs=2,
              include_leaf_variants=True,evaluate_holdout=True)
RAW=pd.read_excel(RAW_PATH) if RAW_PATH.suffix.lower() in ['.xlsx','.xls'] else pd.read_csv(RAW_PATH)
X_ALL,Y=clean_data(RAW,CONFIG.top_k,retain_constants=True)
X_IG,_=clean_data(RAW,CONFIG.top_k)
print('Raw table:',RAW.shape)
print('All-financial-predictor arm:',X_ALL.shape)
print('IG arm inputs before selection:',X_IG.shape)
print('Original class counts:',Y.value_counts().sort_index().to_dict())
print('Retained constants:',[c for c in X_ALL if X_ALL[c].nunique(dropna=False)<=1])
assert 'Company' not in X_ALL and 'Bankrupt' not in X_ALL
display(pd.DataFrame(candidate_specs(CONFIG.include_leaf_variants)))
""")
md("""## 6. Run both arms
There are 45 training-fold fits per arm. Completed fold checkpoints can resume.
Without a prior IG run this is 90 fits plus limited holdout refits.
Feature mode and the data fingerprint isolate checkpoints, preventing top-20 predictions from
being reused as all-feature predictions. Each original training company receives one held-out-fold score.

Thresholds and per-arm candidate choices use training OOF predictions. The historical holdout is
evaluated after each arm freezes its choice. It is not used to select the comparison winner.
""")
code("""COMPARISON=run_feature_comparison(RAW,OUTPUT_BASE,CONFIG,prior_ig_dir=PRIOR_IG_DIR,
                                  source_note=str(RAW_PATH))
REPORT_DIR=COMPARISON['output_dir']
print('Training-selected comparison choice:',COMPARISON['choice'])
""")
md("""## 7. Metrics in the existing report layout
Precision, recall, F1 and F2 refer to `Bankrupt (1)`. Tables keep the original headline metrics,
with feature mode, candidate, decision rule and threshold added for traceability.
Selected OOF metrics are tuning results. Mean fold F1 at the selected pooled cutoff is not independent evaluation.
""")
code("""HEADLINE=['Model','Experiment','Split','CV','Accuracy (%)','Precision (%)','Recall (%)',
          'F1-Score (%)','ROC-AUC (%)','Best_Params','CV_F1_Mean (%)']
EXTRA=['Feature_Mode','Feature_Count','Candidate','SMOTE_Ratio','Decision_Rule','Threshold',
       'F2-Score (%)','Both_Targets_Feasible_OOF','Max_Precision_At_Target_Recall (%)',
       'TP','FP','FN','TN','Evaluation']
display(COMPARISON['training_results'][HEADLINE+EXTRA])
print('Any all-feature candidate reaches both 70% targets on its training OOF curve:',
      bool(COMPARISON['full']['training_results'].Both_Targets_Feasible_OOF.any()))
""")
md("""## 8. Matched comparisons
`Change_pp` columns are **percentage-point changes**, All minus IG20.
At a fixed cutoff the comparison isolates the input-feature policy. At selected cutoffs it compares
the complete feature-and-threshold policies. Both use exactly the same held-out training companies.
""")
code("""PAIRED_COLUMNS=['Candidate','Decision_Rule','Precision (%)_IG20','Precision (%)_All',
                'Precision (%)_Change_pp','Recall (%)_IG20','Recall (%)_All','Recall (%)_Change_pp',
                'F1-Score (%)_IG20','F1-Score (%)_All','F2-Score (%)_IG20','F2-Score (%)_All',
                'Max_Precision_At_Target_Recall (%)_IG20','Max_Precision_At_Target_Recall (%)_All']
display(COMPARISON['paired'][PAIRED_COLUMNS])
display(Image(filename=str(REPORT_DIR/'precision_at_70_recall_comparison.png')))
display(Image(filename=str(REPORT_DIR/'matched_precision_recall_curves.png')))
""")
md("""## 9. Exploratory historical holdout
The unchanged reference RF is reported at cutoff 0.5 in each arm. Each arm's training-selected
candidate is also reported at its frozen cutoff. When those selected candidates differ, comparing their
test rows does not isolate feature count alone; the matched candidate-level OOF comparisons do.

These test companies have been examined in previous rounds. Treat the scores as exploratory,
and do not adjust cutoffs using them. New/external evaluation is needed for a fresh final assessment.
""")
code("""if len(COMPARISON['holdout_results']):
    display(COMPARISON['holdout_results'])
else:
    print('Holdout evaluation disabled by CONFIG.')
""")
md("""## 10. Save and interpret
The readable record is `FEATURE_COMPARISON_RESULTS.txt`; CSVs retain full precision and model parameters.
Reload saved score/threshold CSVs with `pd.read_csv(path, float_precision='round_trip')` to preserve
scores that exactly equal the cutoff. The saved JSON records and fold NPZ arrays also preserve precision.
The all-feature arm has its own model manifest with all financial input fields. This research export
does not replace the 20-field prototype: any deployment change requires a separate implementation decision.

If full features help consistently, the top-20 restriction warrants reconsideration.
If they do not, this does not prove a permanent dataset ceiling; it tells us that removing IG alone,
under the tested settings, was insufficient.
""")
code("""print((REPORT_DIR/'FEATURE_COMPARISON_RESULTS.txt').read_text(encoding='utf-8'))
print('Saved comparison:',REPORT_DIR)
print('Production model, frontend fields and risk bands remain unchanged.')
""")

for i,cell in enumerate(cells):
    cell['id']=f'features-{i:02d}'
    if cell['cell_type']=='code':
        source=''.join(cell['source'])
        if not source.startswith('%pip'):
            compile(source,f'cell_{i}','exec')
nb=dict(nbformat=4,nbformat_minor=5,cells=cells,metadata={
    'kernelspec':dict(display_name='Python 3',language='python',name='python3'),
    'language_info':dict(name='python',version='3.12'),
    'colab':dict(provenance=[]),'shield_version':'shield-all-features-v1'})
path=ROOT/'SHIELD_All_Features_Comparison.ipynb'
path.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+'\n',encoding='utf-8')
print(f'Wrote {path}: {len(cells)} cells; Python cells compile.')
