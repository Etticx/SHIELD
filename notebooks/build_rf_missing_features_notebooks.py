import json
from pathlib import Path
FEATURES=[c.strip() for c in Path('data/X_train_processed_8020.csv').read_text().splitlines()[0].split(',')]
# Exact project names, fixed as a previously chosen deployment input set.
recovery=['Debt ratio %','Net worth/Assets','Equity to Liability','Liability to Equity']
source='''import hashlib, json, importlib.metadata
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    fbeta_score, roc_auc_score, average_precision_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay)
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline

FEATURES=__FEATURES__
RECOVERY_CANDIDATES=__RECOVERY__
SHARE_FIELDS=['Persistent EPS in the Last Four Seasons','Per Share Net profit before tax',
              'Net Value Per Share (A)','Net Value Per Share (B)']

def scenarios():
    result={'baseline_20':FEATURES.copy()}
    for i,f in enumerate(FEATURES):
        if f not in RECOVERY_CANDIDATES:
            result[f'without_feature_{i:02d}']=[c for c in FEATURES if c!=f]
    result['without_share_fields']=[c for c in FEATURES if c not in SHARE_FIELDS]
    return result

def make_model(ratio,small=False):
    return Pipeline([('smote',SMOTE(sampling_strategy=ratio,k_neighbors=5,random_state=42)),
        ('model',RandomForestClassifier(n_estimators=5 if small else 200,max_depth=10,
        min_samples_split=2,min_samples_leaf=1,max_features='sqrt',class_weight=None,
        random_state=42,n_jobs=2))])

def score_metrics(y,score):
    pred=(np.asarray(score)>=.5).astype(int)
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return {'Accuracy (%)':100*accuracy_score(y,pred),
        'Precision (%)':100*precision_score(y,pred,zero_division=0),
        'Recall (%)':100*recall_score(y,pred,zero_division=0),
        'F1-Score (%)':100*f1_score(y,pred,zero_division=0),
        'ROC-AUC (%)':100*roc_auc_score(y,score),
        'F2 (%)':100*fbeta_score(y,pred,beta=2,zero_division=0),
        'PR-AUC (AP) (%)':100*average_precision_score(y,score),
        'TN':int(tn),'FP':int(fp),'FN':int(fn),'TP':int(tp)}

def checked_predictions(path,rows,y):
    with np.load(path,allow_pickle=False) as saved:
        np.testing.assert_array_equal(saved['row_index'],rows)
        np.testing.assert_array_equal(saved['y_true'],np.asarray(y))
        score=saved['y_score'].copy()
    if len(score)!=len(y) or not np.isfinite(score).all():
        raise ValueError('Invalid prediction checkpoint: '+str(path))
    return score
'''.replace('__FEATURES__',repr(FEATURES)).replace('__RECOVERY__',repr(recovery))
load='''raw=pd.read_excel(RAW_PATH) if RAW_PATH.suffix.lower() in ['.xlsx','.xls'] else pd.read_csv(RAW_PATH,float_precision='round_trip')
raw.columns=raw.columns.str.strip()
if raw.columns.duplicated().any(): raise ValueError('Duplicate column names')
if 'Bankrupt' not in raw: raise ValueError('Bankrupt target required')
if 'Company' in raw and raw.Company.duplicated().any(): raise ValueError('Duplicate company IDs: investigate/group before splitting')
if any(f not in raw for f in FEATURES): raise ValueError('Input does not contain all 20 financial features')
X=raw[FEATURES].apply(pd.to_numeric,errors='raise')
y=pd.to_numeric(raw.Bankrupt,errors='raise')
if X.isna().any().any() or y.isna().any() or not np.isfinite(X.to_numpy()).all():
    raise ValueError('Supply complete original data. Scenarios remove columns; no imputation is performed.')
if set(y.unique())!={0,1}: raise ValueError('Target must contain 0=Not Bankrupt and 1=Bankrupt')
y=y.astype(int)
if X.duplicated().any(): raise ValueError('Duplicate full predictor rows: investigate before splitting')
train_idx,test_idx=train_test_split(np.arange(len(y)),test_size=.20,stratify=y,random_state=42)
X_train,y_train=X.iloc[train_idx],y.iloc[train_idx]
X_test,y_test=X.iloc[test_idx],y.iloc[test_idx]
SCENARIOS=scenarios()
versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','imbalanced-learn']}
config={'version':'shield-rf-feature-removal-v1','raw_sha256':hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(),
    'feature_names':FEATURES,'scenarios':SCENARIOS,'smote_ratio':SMOTE_RATIO,
    'seed':42,'test_size':.20,'folds':10,'threshold':.5,'versions':versions,
    'rf':make_model(SMOTE_RATIO).named_steps['model'].get_params(),
    'smote_k_neighbors':5,'scaling':'none','feature_selection':'fixed historical 20, no reselection'}
serialized=json.dumps(config,sort_keys=True,default=str)
RUN_ID=hashlib.sha256(serialized.encode()).hexdigest()[:16]
OUT=OUTPUT_BASE/RUN_ID
OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'run_config.json').exists() and (OUT/'run_config.json').read_text(encoding='utf-8')!=serialized:
    raise ValueError('Checkpoint settings mismatch')
(OUT/'run_config.json').write_text(serialized,encoding='utf-8')
folds=list(StratifiedKFold(n_splits=10,shuffle=True,random_state=42).split(X_train,y_train))
membership=pd.DataFrame({'row_index':np.arange(len(y)),'Bankrupt':y,
    'partition':np.where(np.isin(np.arange(len(y)),train_idx),'training','test'),'validation_fold':-1})
for fold,(_,va) in enumerate(folds,1): membership.loc[train_idx[va],'validation_fold']=fold
membership.to_csv(OUT/'partition_membership.csv',index=False)
manifest=[{'Scenario':name,'Features':len(cols),'Removed':'; '.join(c for c in FEATURES if c not in cols)} for name,cols in SCENARIOS.items()]
pd.DataFrame(manifest).to_csv(OUT/'scenario_manifest.csv',index=False)
print('Original training counts:',y_train.value_counts().sort_index().to_dict())
print('Original test counts:',y_test.value_counts().sort_index().to_dict())
print('Scenarios:',len(SCENARIOS),'| SMOTE ratio:',SMOTE_RATIO,'| Output:',OUT)
display(pd.DataFrame(manifest))
'''
cv='''rows=[]
for name,columns in SCENARIOS.items():
    directory=OUT/name
    directory.mkdir(exist_ok=True)
    oof=np.full(len(y_train),np.nan)
    fold_metrics=[]
    for fold,(tr,va) in enumerate(folds,1):
        checkpoint=directory/f'fold_{fold:02d}.npz'
        if checkpoint.exists():
            scores=checked_predictions(checkpoint,train_idx[va],y_train.iloc[va])
        else:
            pipe=make_model(SMOTE_RATIO)
            pipe.fit(X_train.iloc[tr][columns],y_train.iloc[tr])
            scores=pipe.predict_proba(X_train.iloc[va][columns])[:,1]
            np.savez_compressed(checkpoint,row_index=train_idx[va],y_true=y_train.iloc[va],y_score=scores)
        oof[va]=scores
        fold_metrics.append({'Fold':fold,**score_metrics(y_train.iloc[va],scores)})
        print(name,'fold',fold,'F1:',round(fold_metrics[-1]['F1-Score (%)'],2))
    assert np.isfinite(oof).all()
    pd.DataFrame(fold_metrics).to_csv(directory/'fold_metrics.csv',index=False)
    np.savez_compressed(directory/'training_oof.npz',row_index=train_idx,y_true=y_train,y_score=oof)
    details=next(m for m in manifest if m['Scenario']==name)
    row={**details,'Model':'RandomForest','Experiment':'80-20 + CV=10',
        'Stage':'Training OOF','Split':.20,'CV':10,'SMOTE':SMOTE_RATIO,
        **score_metrics(y_train,oof),
        'CV_F1_Mean (%)':float(np.mean([m['F1-Score (%)'] for m in fold_metrics])),
        'CV_F1_SD (%)':float(np.std([m['F1-Score (%)'] for m in fold_metrics],ddof=1))}
    rows.append(row)
    pd.DataFrame(rows).to_csv(OUT/'results.csv',index=False)
    report=classification_report(y_train,(oof>=.5).astype(int),labels=[0,1],target_names=['Not Bankrupt','Bankrupt'],digits=4,zero_division=0)
    (directory/'training_oof_report.txt').write_text(report,encoding='utf-8')
print('Training CV complete. These scores become selection scores if used to choose a scenario.')
display(pd.DataFrame(rows).round(2))
'''
test='''# Read validated OOF summary so this cell can be rerun without duplicating rows.
rows=pd.read_csv(OUT/'results.csv',float_precision='round_trip').query("Stage == 'Training OOF'").to_dict('records')
for name,columns in SCENARIOS.items():
    directory=OUT/name
    checkpoint=directory/'test_predictions.npz'
    if checkpoint.exists():
        scores=checked_predictions(checkpoint,test_idx,y_test)
    else:
        pipe=make_model(SMOTE_RATIO)
        pipe.fit(X_train[columns],y_train)
        scores=pipe.predict_proba(X_test[columns])[:,1]
        np.savez_compressed(checkpoint,row_index=test_idx,y_true=y_test,y_score=scores)
    reference=next(r for r in rows if r['Scenario']==name and r['Stage']=='Training OOF')
    row={**reference,'Stage':'Test',**score_metrics(y_test,scores)}
    rows.append(row)
    report=f'=== Classification Report: RandomForest | 80-20 + CV=10 | SMOTE={SMOTE_RATIO} | {name} ===\\n'
    report+=classification_report(y_test,(scores>=.5).astype(int),labels=[0,1],target_names=['Not Bankrupt','Bankrupt'],digits=4,zero_division=0)
    report+='\\n'+' | '.join(f'{k}: {row[k]:.2f}' for k in ['Accuracy (%)','Precision (%)','Recall (%)','F1-Score (%)','ROC-AUC (%)'])
    print(report)
    (directory/'test_report.txt').write_text(report,encoding='utf-8')
    fig,ax=plt.subplots(figsize=(5.4,4.5))
    ConfusionMatrixDisplay.from_predictions(y_test,(scores>=.5).astype(int),labels=[0,1],display_labels=['Not Bankrupt','Bankrupt'],ax=ax,cmap='Blues',colorbar=False)
    ax.set_title(f'{name} | SMOTE {SMOTE_RATIO}')
    fig.tight_layout()
    fig.savefig(directory/'test_confusion_matrix.svg',bbox_inches='tight')
    fig.savefig(directory/'test_confusion_matrix.png',dpi=180,bbox_inches='tight')
    plt.show()
    pd.DataFrame(rows).to_csv(OUT/'results.csv',index=False)
results=pd.DataFrame(rows)
(OUT/'RESULTS.txt').write_text('SHIELD: no imputation; retrained reduced-input Random Forests.\\n'+
    '80:20 split, training CV=10, fixed parameters, seed42, threshold0.5.\\n'+
    'Previously inspected holdout; exploratory results.\\n\\n'+results.to_string(index=False),encoding='utf-8')
display(results.round(2))
'''
comparison='''comparison=results[results.Stage=='Test'].copy()
baseline=comparison[comparison.Scenario=='baseline_20'].iloc[0]
for metric in ['Precision (%)','Recall (%)','F1-Score (%)','F2 (%)','FP','FN']:
    comparison['Change '+metric]=comparison[metric]-baseline[metric]
comparison.to_csv(OUT/'test_changes_vs_baseline.csv',index=False)
# Keep original scenario order. Do not automatically pick a winner from the test set.
cols=['Scenario','Features','Removed','Precision (%)','Recall (%)','F1-Score (%)','FP','FN',
    'Change Precision (%)','Change Recall (%)','Change F1-Score (%)']
display(comparison[cols].round(2))
fig,ax=plt.subplots(figsize=(12,8))
comparison.set_index('Scenario')[['Precision (%)','Recall (%)','F1-Score (%)']].plot.barh(ax=ax)
ax.set_xlabel('Score (%)'); ax.set_xlim(0,100)
ax.set_title(f'Reduced-input RF comparison | test | SMOTE {SMOTE_RATIO}')
fig.tight_layout()
fig.savefig(OUT/'test_comparison.svg',bbox_inches='tight')
fig.savefig(OUT/'test_comparison.png',dpi=180,bbox_inches='tight')
plt.show()
print('All outputs:',OUT)
'''
for tag,ratio in [('025',.25),('100',1.)]:
 cells=[]
 def md(s): cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
 def code(s,definitions=False): cells.append(dict(cell_type='code',metadata={'definitions':True} if definitions else {},source=s.splitlines(True),execution_count=None,outputs=[]))
 md(f'''# SHIELD — Reduced-input Random Forest | SMOTE {ratio}

**Question:** when an SME cannot supply a financial input, can a model trained without that input still identify bankruptcy acceptably?

**80:20 stratified split, 10-fold ordinary CV on training companies, seed42, fixed RF settings, SMOTE {ratio}, threshold0.5. No imputation.**

18 scenarios: all20 baseline; remove each of16 features individually; remove all4 share-related features together. Removing EPS individually is already one of the16 scenarios.

The20 inputs are a **fixed historical selection**, not freshly selected IG features. This evaluates the proposed deployment input set. Historical feature selection and repeated holdout inspection limit unbiased performance claims. No IG reselection is performed, because replacing removed fields with newly selected fields would answer a different question.

Four potential recovery fields (Debt ratio, Net worth/Assets, Equity/Liability and Liability/Equity) are excluded from the individual-removal list requested here. Their calculation has **not** been validated. No reconstruction formula is implemented. Both-pair-missing scenarios need separate evaluation before supporting them.

This is **retraining without unavailable inputs**, not passing NaN to the saved prototype model. The prototype is not modified. Random missing fields per company would require a separate strategy/model.

To isolate the effects of feature removal and SMOTE ratio, both notebooks use the same RF settings:200 trees, max_depth10, min_samples_split2, min_samples_leaf1, max_features sqrt, no class weights. This is a controlled comparison, not an exact reproduction of every historical best model. With fewer columns, sqrt naturally changes the number of candidate features at each split.
''')
 code('%pip install -q scikit-learn==1.9.0 imbalanced-learn==0.14.2 pandas numpy matplotlib openpyxl\n')
 md('## 1. Paths\nUse original unresampled data, not X_train_processed (which contains synthetic records). Adjust the Drive path if needed. There are198 fits per notebook (18 scenarios ×10 CV folds +18 final refits); matching completed predictions are reused.')
 code(f'''from pathlib import Path
SMOTE_RATIO={ratio}
try:
    from google.colab import drive
    drive.mount('/content/drive')
    BASE=Path('/content/drive/MyDrive/SHIELD_Project')
except ImportError:
    BASE=Path.cwd()
    if BASE.name=='notebooks': BASE=BASE.parent
RAW_PATH=BASE/'data'/'bankruptcy_italian_companies_2023.xlsx'
OUTPUT_BASE=BASE/'reports'/'rf_missing_features'/'smote_{tag}'
''')
 md('## 2. Fixed inputs, scenarios, model and metrics\nScaling is unchanged from the historical RF + SMOTE setup (none). SMOTE sees only the current training fold. The16 feature labels indicate unconfirmed recovery from the other selected fields, not proof that the SME can never provide them.')
 code(source,True)
 md('## 3. Validate data, split once, record settings\nAll scenarios and both ratio notebooks use the same companies and fold allocation. Input SHA, package versions and settings determine the output folder for safe checkpoint reuse.')
 code(load)
 md('## 4. Training CV\nEach training company is held out exactly once. No parameter tuning, threshold tuning or nested CV. Pooled OOF F1 differs from the mean of10 fold F1 scores. Mean/SD describe folds, not confidence intervals.')
 code(cv)
 md('## 5. Refit and evaluate historical holdout\nThe test set retains its original class distribution. Each scenario fits a separate RF using its available columns. No estimated values are introduced. Reports and confusion matrices are saved for every scenario.')
 code(test)
 md('## 6. Compare with baseline\nChanges are percentage points for percentage metrics; FP/FN changes are company counts. A negative change in FP/FN means fewer errors. No automatic acceptance threshold or test-based winner selection is imposed.')
 code(comparison)
 md('''## How to discuss results
Compare each reduced-input model with **its own fresh baseline in this notebook**. Inspect training OOF and holdout results together. A one-company change among44 bankruptcies is2.27 percentage points of recall; avoid declaring a winner from a small difference.

A model tolerating removal of one field does not prove tolerance when several disappear together. The share-field scenario tests one realistic combination. A startup with short history may differ systematically from the source companies; removing EPS alone does not establish validity for startups.

Agree with your supervisor what detection loss and false-alarm change are acceptable before adopting a reduced model. Independent validation remains needed after exploratory selection.

[SMOTE and leakage](https://imbalanced-learn.org/stable/common_pitfalls.html) · [RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
''')
 for i,c in enumerate(cells): c['id']=f'rf-missing-{i:02d}'
 nb=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python3',language='python',name='python3'),language_info=dict(name='python'),colab=dict(name=f'SHIELD_RF_Missing_Features_SMOTE_{tag}.ipynb')),nbformat=4,nbformat_minor=5)
 path=Path(f'notebooks/SHIELD_RF_Missing_Features_SMOTE_{tag}.ipynb')
 path.write_text(json.dumps(nb,indent=1),encoding='utf-8')
 print(path)
