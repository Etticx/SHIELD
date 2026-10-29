"""Build the self-contained, configurable seven-versus-twenty Colab comparison."""
import ast,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
old=json.loads((HERE/'SHIELD_RF_Missing_Features_SMOTE_025.ipynb').read_text(encoding='utf-8'))
codes=[''.join(c['source']) for c in old['cells'] if c['cell_type']=='code']
source=codes[2]
seven=["Net Income to Stockholder's Equity",'Net Income to Total Assets','Retained Earnings to Total Assets',
       'Debt ratio %','Net worth/Assets','Equity to Liability','Liability to Equity']
ranks=dict(zip(seven,[5,7,13,14,16,17,20]))
scores=dict(zip(seven,[.036753,.035144,.032738,.032479,.032132,.031732,.030660]))
start=source.index('RECOVERY_CANDIDATES=')
end=source.index('def make_model(')
source=source[:start]+f'''SEVEN_FEATURES={seven!r}
HISTORICAL_IG_RANKS={ranks!r}
HISTORICAL_IG_SCORES={scores!r}

def scenarios():
    return {{'baseline_20':FEATURES.copy(),'practical_7':SEVEN_FEATURES.copy()}}

'''+source[end:]
source=source.replace('confusion_matrix, ConfusionMatrixDisplay)','confusion_matrix, ConfusionMatrixDisplay, RocCurveDisplay, PrecisionRecallDisplay)')
load=codes[3].replace('shield-rf-feature-removal-v1','shield-rf-seven-vs-twenty-v1')
load=load.replace('SCENARIOS=scenarios()',"if SMOTE_RATIO not in [.25,1.0]: raise ValueError('Choose SMOTE_RATIO=0.25 or 1.0')\nSCENARIOS=scenarios()")
load=load.replace("'feature_selection':'fixed historical 20, no reselection'","'feature_selection':'fixed historical20 versus predefined7; no IG reselection'")
load += '''\nrank_table=pd.DataFrame({'Feature':SEVEN_FEATURES,
    'Historical IG rank':[HISTORICAL_IG_RANKS[f] for f in SEVEN_FEATURES],
    'Historical IG score':[HISTORICAL_IG_SCORES[f] for f in SEVEN_FEATURES]})
rank_table.to_csv(OUT/'seven_feature_historical_ig.csv',index=False)
display(rank_table)
'''
cv=codes[4]
test=codes[5]
anchor="    pd.DataFrame(rows).to_csv(OUT/'results.csv',index=False)"
extra='''    fig,axes=plt.subplots(1,2,figsize=(11,4.5))
    RocCurveDisplay.from_predictions(y_test,scores,ax=axes[0])
    PrecisionRecallDisplay.from_predictions(y_test,scores,ax=axes[1])
    fig.suptitle(f'{name} | test | SMOTE {SMOTE_RATIO}')
    fig.tight_layout()
    fig.savefig(directory/'test_roc_pr.png',dpi=180,bbox_inches='tight')
    fig.savefig(directory/'test_roc_pr.svg',bbox_inches='tight')
    plt.show()
'''
assert test.count(anchor)==1
test=test.replace(anchor,extra+anchor)
comparison=codes[6].replace('Reduced-input RF comparison','Seven versus twenty inputs: RF')
cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s,definitions=False):cells.append(dict(cell_type='code',metadata={'definitions':True} if definitions else {},source=s.splitlines(True),execution_count=None,outputs=[]))
md('''# SHIELD — Random Forest: 7 financial-statement candidates versus 20 inputs

**Question:** does a Random Forest using only seven predefined financial-statement-based feature candidates retain useful bankruptcy detection compared with the historical20-input baseline?

This **one notebook** runs both feature sets using a stratified **80:20 split**, **10-fold ordinary training CV**, **seed42**, fixed RF parameters and **threshold0.5**. Start with **SMOTE0.25**, then change one setting to **1.0** and run again. Ratio-specific settings produce separate output folders.

No imputation, feature reconstruction, new IG selection, GridSearchCV or threshold tuning. The seven candidates were selected for potential accounting availability, not because they performed best on this test set. Historical20 selection and repeated holdout inspection mean all results remain **exploratory**, not independent final validation.

**Important:** the seven are candidate ratios derivable from company accounts. Their exact historical donor definitions and transformations are not yet established. This experiment uses existing dataset columns; it does not validate entering raw SME financial amounts into the prototype or prove validity for Malaysian SMEs. It does not modify the prototype.
''')
md('## 1. Install modelling dependencies\nPinned modelling versions match the verified local comparison environment. If Colab already imported a different version, restart the runtime after installing, then continue from the settings cell.')
code('%pip install -q scikit-learn==1.9.0 imbalanced-learn==0.14.2 pandas numpy matplotlib openpyxl\n')
md('## 2. Settings and data paths\nOnly change SMOTE_RATIO between0.25 and1.0. In Colab, update the Drive path if necessary, then run the remaining cells top to bottom. Use the original unresampled Excel file, not the SMOTE-expanded training files.')
code('''from pathlib import Path
SMOTE_RATIO=0.25           # Second run: change to 1.0
try:
    from google.colab import drive
    drive.mount('/content/drive')
    BASE=Path('/content/drive/MyDrive/SHIELD_Project')
except ImportError:
    BASE=Path.cwd()
    if BASE.name=='notebooks': BASE=BASE.parent
RAW_PATH=BASE/'data'/'bankruptcy_italian_companies_2023.xlsx'
OUTPUT_BASE=BASE/'reports'/'rf_seven_vs_twenty'
print('Data:',RAW_PATH)
print('SMOTE ratio:',SMOTE_RATIO)
''')
md('''## 3. Fixed features, RF and metrics

RF: **200 trees, max_depth10, min_samples_split2, min_samples_leaf1, max_features sqrt, no class weights**. SMOTE: k_neighbors5. Balancing occurs **inside each training fold**, never on validation or test companies. No new scaling is introduced, matching this controlled historical RF setup. Because max_features is sqrt, the absolute number of candidate split features changes with feature count.

The baseline is retrained in the same environment; compare against this fresh baseline rather than assuming historical scores will reproduce exactly. The1.0 arm uses identical RF parameters for isolation, not an automatic reproduction of the original best-tuned1.0 model.

The seven and their historical IG positions are shown after data validation. Historical scores are recorded, not recalculated. Some of these seven encode related leverage/profit information; they are not seven independent signals.
''')
code(source,True)
md('## 4. Validate original data and split once\nCompany and Bankrupt are excluded from predictors. Both feature sets use the identical companies and folds. There must be no unresolved missing values or duplicate full20-input rows. No rows are silently deleted. The output folder records input hash, versions, parameters and scenario membership. Full20 validation is necessary for the paired baseline comparison.')
code(load)
md('## 5. Training cross-validation\n22 fits per ratio:10 folds plus1 full-training refit for each of2 feature sets. Every training company gets exactly one OOF prediction. Mean/SD of fold F1 and pooled OOF metrics are distinct. Completed fold predictions are reused only for matching run settings. If these scores are used to select the final feature set/ratio, they become selection scores.')
code(cv)
md('## 6. Refit and report on the test set\nFor each feature set, refit on all80% training companies and evaluate on the original20% test companies. Metrics retain their familiar names; Bankruptcy=1 is the positive class. A score>=0.5 predicts Bankruptcy. Exported predictions permit later threshold/curve audits; this notebook does not export or deploy a replacement production model.')
code(test)
md('## 7. Compare with the20-feature baseline\nChanges in percentage metrics are percentage points; FP/FN changes are company counts. No automatic winner is chosen from the historical test set. Inspect training OOF alongside holdout results.')
code(comparison)
md('''## Reading the outcome and running the second ratio

- Compare seven against20 **within the same ratio** first. Higher recall means fewer missed bankruptcies; higher precision means fewer false alarms among positive alerts.
- Then change SMOTE_RATIO to1.0 in Section2 and rerun from there. Settings hashes isolate outputs; do not edit only the final display cell.
- On the historical test set with44 bankruptcies, one company corresponds to2.27 percentage points of recall. Small changes do not establish a meaningful winner.
- Removing columns tests a **retrained seven-input model**, not an existing20-input model receiving blank values. Supporting arbitrary missing subsets needs separate evaluation.
- IG is intentionally omitted from this fixed-subset comparison. A later experiment could apply IG inside training folds to a larger accounting-eligible pool.
- Formula verification, correct raw-to-model transformation, actual SME document checks and independent population validation remain separate steps before deployment.

Output files include `results.csv`, `RESULTS.txt`, `test_changes_vs_baseline.csv`, historical IG references, split/fold membership, classification reports, confusion matrices, ROC/precision-recall charts and prediction checkpoints. No datasets or production model files are changed.
''')
for i,c in enumerate(cells):c['id']=f'shield-seven-{i:02d}'
path=HERE/'SHIELD_RF_Seven_vs_Twenty_Features.ipynb'
nb=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python'),colab=dict(name=path.name)),nbformat=4,nbformat_minor=5)
path.write_text(json.dumps(nb,indent=1),encoding='utf-8')
print(path)
